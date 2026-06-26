"""
Type definitions and validation for lesson.story.json (Lesson Script format).

A lesson script is the Layer 2 input to the story animation pipeline::

    lesson.story.json          ← authored by a teacher / LLM
          ↓  story_compiler.py
    frames[]                   ← positioned frames (auto-layout by object type)
          ↓  render_story_html.py
    HTML animation

Unlike ``trace.sample.json`` (which records *execution* events), a lesson
script records *teaching intentions*: what objects exist, what concepts
matter, and what sequence of actions makes them visible to the learner.

Object types
------------
input_array   – the input array (e.g. nums = [2, 7, 11, 15])
input_value   – a scalar input (e.g. target = 9)
variable      – an algorithm intermediate variable (current, need, i)
definition    – a data structure definition / container (seen hash map)
rule          – a formula or rule (seen[number] = index)
operation     – a single computed result
data_structure – a concrete data structure instance
container     – a named container that can hold other objects
map_entry     – one entry inside a hash map (2 → 0)
array_item    – one element of an array
pointer       – a named pointer / cursor (left, right)
answer        – the final return value
note          – a teaching annotation

Action types
------------
appear        – object fades / slides in
disappear     – object fades out
move          – object moves to a new position
transform     – object morphs into another type
copy          – value is copied from one object to another
group         – multiple objects coalesce into a group
ungroup       – group splits back into individuals
connect       – a relationship arrow is drawn between two objects
disconnect    – a relationship arrow is removed
highlight     – an object (or part of it) is highlighted
derive        – a new value is computed from existing objects via a rule
insert_into   – an object enters a container
compare       – an object is compared against a container (hit / miss)
choose        – one option is selected among candidates (backtracking)
return        – the answer object appears with its final value
apply_rule    – a rule card is visually activated / pulsed
"""
from __future__ import annotations

# ── Object types ──────────────────────────────────────────────────────

OBJECT_TYPES: frozenset[str] = frozenset(
    {
        "input_array",
        "input_value",
        "variable",
        "definition",
        "rule",
        "operation",
        "data_structure",
        "container",
        "map_entry",
        "array_item",
        "pointer",
        "answer",
        "note",
    }
)

# ── Action types ──────────────────────────────────────────────────────

ACTION_TYPES: frozenset[str] = frozenset(
    {
        "appear",
        "disappear",
        "move",
        "transform",
        "copy",
        "group",
        "ungroup",
        "connect",
        "disconnect",
        "highlight",
        "derive",
        "insert_into",
        "compare",
        "choose",
        "return",
        "apply_rule",
    }
)

# ── Per-action reference fields ───────────────────────────────────────
# Maps action type → tuple of field names whose values are object-id references.
# Fields not listed here are not reference-checked.
# Notes:
#   * "to" in transform/connect may be a runtime-created map_entry id → skipped
#     by _check_ref when the value starts with "map_entry:".
#   * "object" in insert_into may also be a runtime map_entry id.
_ACTION_REF_FIELDS: dict[str, tuple[str, ...]] = {
    "appear":      ("object",),
    "disappear":   ("object",),
    "highlight":   ("object",),
    "copy":        ("from", "to"),
    "derive":      ("rule", "result"),
    "compare":     ("object", "against"),
    "transform":   ("from",),        # "to" is runtime-created (map_entry:)
    "apply_rule":  ("rule",),
    "insert_into": ("object", "container"),
    "connect":     ("from",),        # "to" may be runtime-created (map_entry:)
    "return":      ("object",),
    # Declared-but-unimplemented actions:
    "move":        ("object",),
    "group":       (),
    "ungroup":     (),
    "disconnect":  (),
    "choose":      (),
}


# ── Reference checker ────────────────────────────────────────────────


def _check_ref(ref: str, obj_ids: set[str], context: str) -> str | None:
    """Return an error string if *ref* cannot be resolved, else ``None``.

    Rules
    -----
    * Empty / missing references are silently skipped.
    * References starting with ``map_entry:`` are runtime-created by the
      compiler (``transform`` action) and cannot be statically validated.
    * Array-element references like ``"input:nums[0]"`` are valid when the
      base object ``"input:nums"`` is declared.
    * All other references must match a declared object id.
    """
    if not ref:
        return None
    # Runtime-created object – cannot validate statically
    if ref.startswith("map_entry:"):
        return None
    # Array-element reference: "input:nums[0]" → check base "input:nums"
    if "[" in ref and ref.endswith("]"):
        base = ref.split("[")[0]
        if base not in obj_ids:
            return (
                f"{context}: base object '{base}' not declared"
                f" (in array reference '{ref}')"
            )
        return None
    # Plain reference: must be a declared object id
    if ref not in obj_ids:
        return f"{context}: '{ref}' not declared in objects"
    return None


# ── Validation ────────────────────────────────────────────────────────


def validate_lesson(lesson: dict) -> list[str]:
    """Return a list of validation error strings, or ``[]`` if the lesson is valid.

    Checks performed
    ----------------
    1. Required top-level fields present.
    2. Every object has an ``id`` and a known ``type``; no duplicate ids.
    3. Every frame has an ``id``; no duplicate frame ids.
    4. Every action uses a known action type.
    5. Object-reference fields in each action resolve to declared object ids
       (with special handling for array-element refs and runtime map_entry ids).

    Parameters
    ----------
    lesson:
        A parsed ``lesson.story.json`` document (plain ``dict``).

    Returns
    -------
    list[str]
        Human-readable error strings. Empty list means valid.
    """
    errors: list[str] = []

    for required in ("lesson_id", "problem_id", "title", "objects", "frames"):
        if required not in lesson:
            errors.append(f"missing required field: '{required}'")

    # Validate objects
    obj_ids: set[str] = set()
    for obj in lesson.get("objects", []):
        obj_id = obj.get("id")
        if not obj_id:
            errors.append(f"object missing 'id': {obj!r}")
            continue
        if obj_id in obj_ids:
            errors.append(f"duplicate object id: {obj_id!r}")
        obj_ids.add(obj_id)

        obj_type = obj.get("type")
        if obj_type not in OBJECT_TYPES:
            errors.append(
                f"unknown object type {obj_type!r} for object {obj_id!r}"
                f" (expected one of {sorted(OBJECT_TYPES)})"
            )

    # Validate frames and their actions
    frame_ids: set[str] = set()
    for frame in lesson.get("frames", []):
        frame_id = frame.get("id")
        if not frame_id:
            errors.append(f"frame missing 'id': {frame!r}")
            continue
        if frame_id in frame_ids:
            errors.append(f"duplicate frame id: {frame_id!r}")
        frame_ids.add(frame_id)

        for action in frame.get("actions", []):
            act = action.get("action")
            if act not in ACTION_TYPES:
                errors.append(
                    f"unknown action {act!r} in frame {frame_id!r}"
                    f" (expected one of {sorted(ACTION_TYPES)})"
                )
                continue  # skip reference checks for unknown action

            # Check object-reference fields declared for this action type
            for field in _ACTION_REF_FIELDS.get(act, ()):
                ref = action.get(field, "")
                err = _check_ref(
                    ref, obj_ids,
                    context=f"frame '{frame_id}' action '{act}' field '{field}'",
                )
                if err:
                    errors.append(err)

    return errors
