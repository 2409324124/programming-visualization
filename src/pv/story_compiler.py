"""
Story compiler: converts lesson.story.json into animation frames.

Pipeline (Layer 2 → Layer 3)::

    lesson.story.json
          ↓  compile_lesson(lesson) → [frame, ...]
    frames[]
          ↓  render_story_to_html(frames)
    HTML animation

Each output frame is compatible with ``render_story_html.render_story_to_html``::

    {
        "frame_id": str,
        "title":    str,   # from lesson frame "goal"
        "caption":  str,   # from lesson frame "caption"
        "objects":  [...], # visual objects with x/y/w/h/state/type/text
        "arrows":   [...], # SVG arrows between objects
        "badges":   [],
    }

Design principles
-----------------
* The compiler is *stateful*: each frame builds on top of the previous
  frame's visible object set.  Appearing objects stay visible until an
  explicit ``disappear`` action removes them.
* Positions are computed by the built-in layout engine based on object
  type, never hard-coded per-problem.
* The ``from`` key in JSON actions is read as-is (it is not a Python
  keyword in a dict context).
"""
from __future__ import annotations

import copy
import json
from typing import Any

# ── Stage dimensions ──────────────────────────────────────────────────
STAGE_W = 960
STAGE_H = 520

# ── Zone layout (auto-positions by object type) ───────────────────────

# Input array zone – top-left
_ARR_X0 = 80
_ARR_Y0 = 55
_ARR_BOX_W = 64
_ARR_BOX_H = 54
_ARR_BOX_GAP = 88          # center-to-center horizontal spacing

# Input value zone – top, right of the array
_IVAL_Y = 55
_IVAL_W = 130
_IVAL_H = 48

# Variable zone – center-left, below inputs
_VAR_X0 = 80
_VAR_Y0 = 185
_VAR_W = 120
_VAR_H = 48
_VAR_GAP = 150             # horizontal spacing between variable boxes

# Rules zone – right panel
_RULE_X = 615
_RULE_Y0 = 55
_RULE_W = 295
_RULE_H = 58
_RULE_GAP = 75             # vertical spacing between rule cards

# Definition container zone – bottom-left
_DEF_X = 80
_DEF_Y = 298
_DEF_W = 430
_DEF_H = 100
_DEF_LABEL_Y = _DEF_Y - 26  # zone label above the box

# Map entry zone – inside definition container
_ENTRY_X0 = _DEF_X + 18
_ENTRY_Y = _DEF_Y + 28
_ENTRY_W = 110
_ENTRY_H = 46
_ENTRY_GAP = 128           # horizontal spacing between entries

# Answer zone – bottom-right
_ANSWER_X = 685
_ANSWER_Y = 420
_ANSWER_W = 170
_ANSWER_H = 56


# ── Internal compiler ─────────────────────────────────────────────────


class _Compiler:
    """Stateful lesson-to-frames compiler.

    Usage::

        compiler = _Compiler(lesson_dict)
        frames = compiler.compile()
    """

    def __init__(self, lesson: dict) -> None:
        self._lesson = lesson
        # id → lesson object definition
        self._defs: dict[str, dict] = {
            o["id"]: o for o in lesson.get("objects", [])
        }
        # Currently visible objects: id → visual dict (mutated in place)
        self._visible: dict[str, dict] = {}
        # Arrows for the current frame
        self._arrows: list[dict] = []
        # Auto-layout slot counters
        self._rule_slot = 0
        self._var_slot = 0
        self._entry_slot = 0
        # map_entry id → its slot index (for final position after insert_into)
        self._entry_slots: dict[str, int] = {}
        # Runtime values computed during actions (current_value, derived results)
        self._rt: dict[str, Any] = {}

    # ── Public API ────────────────────────────────────────────────────

    def compile(self) -> list[dict]:
        """Compile all frames in order and return the frame list."""
        return [self._compile_frame(lf) for lf in self._lesson.get("frames", [])]

    # ── Frame compilation ─────────────────────────────────────────────

    def _compile_frame(self, lf: dict) -> dict:
        self._arrows = []
        for action in lf.get("actions", []):
            self._apply(action)
        return {
            "frame_id": lf["id"],
            "title":    lf.get("goal", ""),
            "caption":  lf.get("caption", lf.get("goal", "")),
            # Deep-copy so later mutations don't bleed into earlier frames.
            "objects":  copy.deepcopy(list(self._visible.values())),
            "arrows":   copy.deepcopy(self._arrows),
            "badges":   [],
        }

    # ── Action dispatch ───────────────────────────────────────────────

    def _apply(self, action: dict) -> None:
        act = action.get("action", "")
        {
            "appear":      self._appear,
            "disappear":   self._disappear,
            "highlight":   self._highlight,
            "copy":        self._copy,
            "derive":      self._derive,
            "compare":     self._compare,
            "transform":   self._transform,
            "apply_rule":  self._apply_rule,
            "insert_into": self._insert_into,
            "connect":     self._connect,
            "return":      self._do_return,
        }.get(act, lambda _: None)(action)

    # ── appear ────────────────────────────────────────────────────────

    def _appear(self, action: dict) -> None:
        obj_id = action["object"]
        obj_def = self._defs.get(obj_id, {})
        obj_type = obj_def.get("type", "variable")

        handler = {
            "input_array": self._appear_input_array,
            "input_value": self._appear_input_value,
            "definition":  self._appear_definition,
            "rule":        self._appear_rule,
            "variable":    self._appear_variable,
            "answer":      self._appear_answer,
        }.get(obj_type)

        if handler:
            handler(obj_id, obj_def)

    def _appear_input_array(self, obj_id: str, obj_def: dict) -> None:
        values: list = obj_def.get("value", [])
        label: str = obj_def.get("label", "")
        # Header label
        self._visible[f"{obj_id}:label"] = _mk_label(
            f"{obj_id}:label",
            label,
            _ARR_X0,
            _ARR_Y0 - 22,
        )
        # Individual array boxes
        for i, v in enumerate(values):
            box_id = f"{obj_id}[{i}]"
            self._visible[box_id] = {
                "id":    box_id,
                "type":  "array_box",
                "text":  str(v),
                "idx":   i,
                "x":     _ARR_X0 + i * _ARR_BOX_GAP,
                "y":     _ARR_Y0,
                "w":     _ARR_BOX_W,
                "h":     _ARR_BOX_H,
                "state": "normal",
            }

    def _appear_input_value(self, obj_id: str, obj_def: dict) -> None:
        label = obj_def.get("label", obj_id)
        value = obj_def.get("value", "")
        # Place to the right of the input array
        nums_def = self._defs.get("input:nums", {})
        arr_len = len(nums_def.get("value", []))
        x = _ARR_X0 + arr_len * _ARR_BOX_GAP + 24
        self._visible[obj_id] = {
            "id":    obj_id,
            "type":  "label",
            "text":  f"{label} = {value}",
            "x":     x,
            "y":     _IVAL_Y + (_ARR_BOX_H - _IVAL_H) // 2,
            "w":     _IVAL_W,
            "h":     _IVAL_H,
            "state": "normal",
        }

    def _appear_definition(self, obj_id: str, obj_def: dict) -> None:
        label = obj_def.get("label", obj_id)
        body  = obj_def.get("body", "")
        # Zone label above the container
        self._visible[f"{obj_id}:label"] = _mk_label(
            f"{obj_id}:label",
            label,
            _DEF_X + 8,
            _DEF_LABEL_Y,
        )
        # Container box
        self._visible[obj_id] = {
            "id":    obj_id,
            "type":  "definition",
            "title": label,
            "text":  body,
            "x":     _DEF_X,
            "y":     _DEF_Y,
            "w":     _DEF_W,
            "h":     _DEF_H,
            "state": "normal",
        }

    def _appear_rule(self, obj_id: str, obj_def: dict) -> None:
        slot = self._rule_slot
        self._rule_slot += 1
        formula = obj_def.get("formula", obj_def.get("label", obj_id))
        self._visible[obj_id] = {
            "id":    obj_id,
            "type":  "rule_card",
            "title": "规则",
            "text":  formula,
            "x":     _RULE_X,
            "y":     _RULE_Y0 + slot * _RULE_GAP,
            "w":     _RULE_W,
            "h":     _RULE_H,
            "state": "new",
        }

    def _appear_variable(self, obj_id: str, obj_def: dict) -> None:
        slot = self._var_slot
        self._var_slot += 1
        label = obj_def.get("label", obj_id.split(":")[-1])
        self._visible[obj_id] = {
            "id":    obj_id,
            "type":  "variable_box",
            "text":  f"{label} = ?",
            "x":     _VAR_X0 + slot * _VAR_GAP,
            "y":     _VAR_Y0,
            "w":     _VAR_W,
            "h":     _VAR_H,
            "state": "faded",
        }

    def _appear_answer(self, obj_id: str, obj_def: dict) -> None:
        label = obj_def.get("label", "return ?")
        self._visible[obj_id] = {
            "id":    obj_id,
            "type":  "answer_box",
            "text":  label,
            "x":     _ANSWER_X,
            "y":     _ANSWER_Y,
            "w":     _ANSWER_W,
            "h":     _ANSWER_H,
            "state": "faded",
        }

    # ── disappear ─────────────────────────────────────────────────────

    def _disappear(self, action: dict) -> None:
        self._visible.pop(action.get("object", ""), None)

    # ── highlight ─────────────────────────────────────────────────────

    def _highlight(self, action: dict) -> None:
        obj_id = action["object"]
        idx    = action.get("index")
        obj_def = self._defs.get(obj_id, {})

        if obj_def.get("type") == "input_array":
            values = obj_def.get("value", [])
            for i, v in enumerate(values):
                box_id = f"{obj_id}[{i}]"
                if box_id not in self._visible:
                    continue
                if i == idx:
                    self._visible[box_id]["state"] = "active"
                    self._rt["current_value"] = v
                    self._rt["current_index"] = i
                else:
                    cur = self._visible[box_id].get("state", "normal")
                    if cur == "active":
                        self._visible[box_id]["state"] = "visited"
        elif obj_id in self._visible:
            self._visible[obj_id]["state"] = "active"

    # ── copy ──────────────────────────────────────────────────────────

    def _copy(self, action: dict) -> None:
        from_id = action.get("from", "")
        to_id   = action.get("to", "")
        value   = self._resolve_value(from_id)

        if to_id in self._visible:
            obj_def = self._defs.get(to_id, {})
            label = obj_def.get("label", to_id.split(":")[-1])
            self._visible[to_id]["text"]  = f"{label} = {value}"
            self._visible[to_id]["state"] = "active"
        self._rt[to_id] = value

    def _resolve_value(self, ref: str) -> Any:
        """Resolve an object reference to its runtime value."""
        # Array element reference: "input:nums[0]"
        if "[" in ref and ref.endswith("]"):
            arr_id, rest = ref.split("[", 1)
            idx = int(rest.rstrip("]"))
            arr_def = self._defs.get(arr_id, {})
            values = arr_def.get("value", [])
            if 0 <= idx < len(values):
                return values[idx]
        # Scalar input object
        obj_def = self._defs.get(ref, {})
        if "value" in obj_def:
            return obj_def["value"]
        # Runtime computed value
        if ref in self._rt:
            return self._rt[ref]
        return "?"

    # ── derive ────────────────────────────────────────────────────────

    def _derive(self, action: dict) -> None:
        rule_id   = action.get("rule", "")
        result_id = action.get("result", "")
        rule_def  = self._defs.get(rule_id, {})

        # Pulse the rule card
        if rule_id in self._visible:
            self._visible[rule_id]["state"] = "active"

        derived = self._eval_rule(rule_def)

        if result_id in self._visible:
            res_def = self._defs.get(result_id, {})
            label   = res_def.get("label", result_id.split(":")[-1])
            self._visible[result_id]["text"]  = f"{label} = {derived}"
            self._visible[result_id]["state"] = "active"
        self._rt[result_id] = derived

    def _eval_rule(self, rule_def: dict) -> Any:
        """Evaluate a rule formula against current runtime values."""
        formula = rule_def.get("formula", "")
        # Pattern: "need = target - current"
        if "target" in formula and "current" in formula and "-" in formula:
            target_def = self._defs.get("input:target", {})
            target  = target_def.get("value", 0)
            current = self._rt.get("var:current", self._rt.get("current_value", 0))
            return target - current
        return "?"

    # ── compare ───────────────────────────────────────────────────────

    def _compare(self, action: dict) -> None:
        obj_id     = action.get("object", "")
        against_id = action.get("against", "")
        result     = action.get("result", "miss")

        is_hit = result == "hit"
        color  = "#66bb6a" if is_hit else "#90caf9"

        if obj_id in self._visible:
            self._visible[obj_id]["state"] = "matched" if is_hit else "active"
        if against_id in self._visible:
            self._visible[against_id]["state"] = "active"

        if obj_id in self._visible and against_id in self._visible:
            self._arrows.append({
                "id":    f"arrow:cmp:{obj_id}",
                "from":  obj_id,
                "to":    against_id,
                "label": "lookup",
                "color": color,
            })

    # ── transform ─────────────────────────────────────────────────────

    def _transform(self, action: dict) -> None:
        from_id = action.get("from", "")
        to_id   = action.get("to", "")

        # Source position (for entry animation start)
        src = self._visible.get(from_id)
        src_x = src["x"] if src else _ENTRY_X0
        src_y = src["y"] if src else _ENTRY_Y

        if to_id.startswith("map_entry:"):
            suffix = to_id[len("map_entry:"):]
            # "2_to_0" → key=2, val=0
            if "_to_" in suffix:
                key, val = suffix.split("_to_", 1)
            else:
                key, val = suffix, "?"

            slot = self._entry_slot
            self._entry_slot += 1
            self._entry_slots[to_id] = slot

            # Start at source position; insert_into moves it to container
            self._visible[to_id] = {
                "id":    to_id,
                "type":  "map_entry",
                "text":  f"{key} \u2192 {val}",
                "x":     src_x,
                "y":     src_y,
                "w":     _ENTRY_W,
                "h":     _ENTRY_H,
                "state": "new",
            }
            self._rt["last_entry_id"] = to_id

    # ── apply_rule ────────────────────────────────────────────────────

    def _apply_rule(self, action: dict) -> None:
        rule_id = action.get("rule", "")
        if rule_id in self._visible:
            self._visible[rule_id]["state"] = "active"

    # ── insert_into ───────────────────────────────────────────────────

    def _insert_into(self, action: dict) -> None:
        obj_id       = action.get("object", "")
        container_id = action.get("container", "")

        if obj_id in self._visible:
            slot = self._entry_slots.get(obj_id, 0)
            self._visible[obj_id]["x"]     = _ENTRY_X0 + slot * _ENTRY_GAP
            self._visible[obj_id]["y"]     = _ENTRY_Y
            self._visible[obj_id]["state"] = "new"

    # ── connect ───────────────────────────────────────────────────────

    def _connect(self, action: dict) -> None:
        from_id = action.get("from", "")
        to_id   = action.get("to", "")

        if from_id in self._visible:
            self._visible[from_id]["state"] = "matched"
        if to_id in self._visible:
            self._visible[to_id]["state"] = "matched"

        # Also mark the active array box as matched
        for vis in self._visible.values():
            if vis.get("state") == "active" and vis.get("type") == "array_box":
                vis["state"] = "matched"

        if from_id in self._visible and to_id in self._visible:
            self._arrows.append({
                "id":    f"arrow:conn:{from_id}:{to_id}",
                "from":  from_id,
                "to":    to_id,
                "label": "match",
                "color": "#66bb6a",
            })

    # ── return ────────────────────────────────────────────────────────

    def _do_return(self, action: dict) -> None:
        obj_id = action.get("object", "")
        value  = action.get("value")
        if obj_id in self._visible:
            self._visible[obj_id]["text"]  = (
                f"return {value}" if value is not None else "return ?"
            )
            self._visible[obj_id]["state"] = "matched"


# ── Helpers ───────────────────────────────────────────────────────────


def _mk_label(obj_id: str, text: str, x: int, y: int) -> dict:
    return {
        "id":    obj_id,
        "type":  "label",
        "text":  text,
        "x":     x,
        "y":     y,
        "w":     0,
        "h":     0,
        "state": "normal",
    }


# ── Public API ────────────────────────────────────────────────────────


def compile_lesson(lesson: dict) -> list[dict]:
    """Compile a lesson script into animation frames.

    Parameters
    ----------
    lesson:
        A parsed ``lesson.story.json`` document (plain Python ``dict``).

    Returns
    -------
    list[dict]
        Animation frames compatible with
        ``render_story_html.render_story_to_html()``.
    """
    return _Compiler(lesson).compile()


def compile_lesson_file(path: str) -> tuple[list[dict], str]:
    """Load ``lesson.story.json`` from *path* and compile it.

    Returns
    -------
    (frames, title)
        ``frames`` is a list of frame dicts; ``title`` is the lesson title
        string for the HTML page heading.
    """
    with open(path, encoding="utf-8") as fh:
        lesson = json.load(fh)
    frames = compile_lesson(lesson)
    title = lesson.get("title", "Story")
    return frames, title
