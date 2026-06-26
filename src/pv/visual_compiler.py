"""
visual_compiler.py — Compile a bound lesson into runtime-aware visual frames.

This is the COMPILATION layer in the runtime-bound pipeline::

    BoundLesson (from visual_binder.py)
          ↓  compile_visual(bound_lesson)
    frames[]   ← positioned + runtime-aware
          ↓  render_story_html.render_story_to_html()
    HTML animation

Key differences from story_compiler.py
---------------------------------------
* All initial values come from ``bound_lesson["_runtime"]["input"]``,
  never from lesson-hardcoded defaults.
* Each frame includes a ``runtime_meta`` dict with actual/expected/passed.
* The first frame includes the full runtime summary badge.
* Derive actions compute values using runtime input facts, not lesson constants.

If the runtime result is a failure (passed=False) or an error occurred,
the animation still renders but the banner prominently shows the failure.
"""
from __future__ import annotations

import copy
from typing import Any

# Reuse layout constants and most action handlers from story_compiler
from pv.story_compiler import (
    STAGE_W, STAGE_H,
    _ARR_X0, _ARR_Y0, _ARR_BOX_W, _ARR_BOX_H, _ARR_BOX_GAP,
    _IVAL_Y, _IVAL_W, _IVAL_H,
    _VAR_X0, _VAR_Y0, _VAR_W, _VAR_H, _VAR_GAP,
    _RULE_X, _RULE_Y0, _RULE_W, _RULE_H, _RULE_GAP,
    _DEF_X, _DEF_Y, _DEF_W, _DEF_H, _DEF_LABEL_Y,
    _ENTRY_X0, _ENTRY_Y, _ENTRY_W, _ENTRY_H, _ENTRY_GAP,
    _ANSWER_X, _ANSWER_Y, _ANSWER_W, _ANSWER_H,
    _mk_label,
)
from pv.story_compiler import _Compiler as _BaseCompiler


# ── Runtime-aware compiler ────────────────────────────────────────────


class _RuntimeCompiler(_BaseCompiler):
    """Extends _BaseCompiler to use runtime input values and carry metadata.

    Key overrides
    -------------
    * ``__init__``: populates ``_rt`` (runtime values dict) from
      ``_runtime.input`` instead of relying on lesson object ``value`` fields.
    * ``_appear``: for ``input_array`` objects, uses the runtime-injected
      ``value`` from the bound object (already overridden by binder).
    * ``_derive``: uses runtime ``target`` and runtime-tracked ``current``
      (set by the ``copy`` action).
    * ``_compile_frame``: adds ``runtime_meta`` to each frame.
    """

    def __init__(self, bound_lesson: dict) -> None:
        super().__init__(bound_lesson)
        self._rt_meta: dict = bound_lesson.get("_runtime", {})
        rt_input: dict = self._rt_meta.get("input", {})

        # Seed runtime values — these are the AUTHORITATIVE source
        self._rt.update({
            "input": rt_input,
            "target": rt_input.get("target"),
            "nums":   rt_input.get("nums"),
            # current / need are set dynamically as actions run
        })

    # ── Frame compilation ─────────────────────────────────────────────

    def _compile_frame(self, lf: dict) -> dict:
        self._arrows = []
        for action in lf.get("actions", []):
            self._apply(action)
        frame = {
            "frame_id":    lf["id"],
            "title":       lf.get("goal", ""),
            "caption":     lf.get("caption", lf.get("goal", "")),
            "objects":     copy.deepcopy(list(self._visible.values())),
            "arrows":      copy.deepcopy(self._arrows),
            "badges":      [],
            "runtime_meta": {
                "bound":       self._rt_meta.get("bound", False),
                "case_index":  self._rt_meta.get("case_index", 0),
                "case_name":   self._rt_meta.get("case_name", ""),
                "actual":      self._rt_meta.get("actual"),
                "expected":    self._rt_meta.get("expected"),
                "passed":      self._rt_meta.get("passed", False),
                "error":       self._rt_meta.get("error"),
            },
        }
        return frame

    # ── Override _appear to use runtime values ────────────────────────

    def _appear(self, action: dict) -> None:
        """Appear an object.  For input objects, use runtime-injected value."""
        obj_id = action["object"]
        obj_def = self._defs.get(obj_id, {})
        obj_type = obj_def.get("type", "variable")

        # For input_array: use bound value (already set by binder)
        if obj_type == "input_array":
            rt_nums = self._rt.get("nums")
            if rt_nums is not None:
                # Override the 'value' in obj_def with runtime data
                obj_def = dict(obj_def)
                obj_def["value"] = rt_nums
                self._defs[obj_id] = obj_def

        # For input_value: use runtime target
        elif obj_type == "input_value":
            param = obj_id.replace("input:", "")
            rt_val = self._rt["input"].get(param)
            if rt_val is not None:
                obj_def = dict(obj_def)
                obj_def["value"] = rt_val
                self._defs[obj_id] = obj_def

        # Delegate to parent after injecting runtime values
        super()._appear(action)

    # ── Override _derive to use runtime values ────────────────────────

    def _derive(self, action: dict) -> None:
        """Apply a rule to derive a value — using RUNTIME facts, not lesson constants.

        Currently supports the 'need = target - current' pattern.
        The formula is evaluated using runtime target and the current value
        set by the most recent 'copy' action.
        """
        rule_id    = action.get("rule", "")
        result_id  = action.get("result", "")
        rule_def   = self._defs.get(rule_id, {})
        rule_text  = rule_def.get("formula", rule_def.get("text", ""))

        # Evaluate using runtime values
        rt_target  = self._rt.get("target")
        rt_current = self._rt.get("current_value")

        computed: Any = "?"
        if rt_target is not None and rt_current is not None:
            # "need = target - current" pattern
            if "target" in rule_text and "current" in rule_text:
                try:
                    computed = rt_target - rt_current
                except TypeError:
                    pass

        # Update visible result object with runtime-derived value
        if result_id in self._visible:
            name = result_id.split(":")[-1] if ":" in result_id else result_id
            self._visible[result_id]["text"] = f"{name} = {computed}"
            self._visible[result_id]["state"] = "active"
        else:
            # Object not yet visible — store for when it appears
            self._rt[f"derived:{result_id}"] = computed

        # Store derived value in runtime dict for later reference
        self._rt[f"derived:{result_id}"] = computed

        # Pulse the rule card
        if rule_id in self._visible:
            self._visible[rule_id]["state"] = "active"

    # ── Override _copy to track current value from runtime ────────────

    def _copy(self, action: dict) -> None:
        """Copy value — reads actual runtime value for array elements."""
        src_ref = action.get("from", "")
        dst_id  = action.get("to", "")

        # Resolve source value from runtime
        rt_value: Any = None
        if "[" in src_ref and src_ref.endswith("]"):
            # Array element reference: "input:nums[0]"
            base, idx_s = src_ref.split("[", 1)
            idx = int(idx_s.rstrip("]"))
            rt_nums = self._rt.get("nums")
            if rt_nums is not None and idx < len(rt_nums):
                rt_value = rt_nums[idx]
                self._rt["current_value"] = rt_value
                self._rt["current_index"] = idx
        elif src_ref in self._rt.get("input", {}):
            rt_value = self._rt["input"][src_ref]

        # Update destination object text with runtime value
        if dst_id in self._visible and rt_value is not None:
            name = dst_id.split(":")[-1] if ":" in dst_id else dst_id
            self._visible[dst_id]["text"] = f"{name} = {rt_value}"
            self._visible[dst_id]["state"] = "active"

        # Fall back to parent's copy logic for layout / appearance
        # (Parent reads from self._rt["current_value"])
        super()._copy(action)


# ── Public API ────────────────────────────────────────────────────────


def compile_visual(bound_lesson: dict) -> list[dict]:
    """Compile a bound lesson into runtime-aware animation frames.

    Parameters
    ----------
    bound_lesson:
        Output of :func:`~pv.visual_binder.bind_lesson` — a lesson dict with
        ``_runtime`` metadata injected and input values overridden.

    Returns
    -------
    list[dict]
        Positioned frames, each with a ``runtime_meta`` key containing
        ``actual``, ``expected``, ``passed``, etc.

    Raises
    ------
    KeyError
        If ``_runtime`` key is missing (lesson was not bound first).
    """
    if "_runtime" not in bound_lesson:
        raise KeyError(
            "bound_lesson is missing '_runtime' key. "
            "Call visual_binder.bind_lesson() before compile_visual()."
        )
    return _RuntimeCompiler(bound_lesson).compile()
