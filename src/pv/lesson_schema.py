"""
Type definitions and validation for lesson.story.json (Lesson Script format).

A lesson script is the Layer 2 input to the story animation pipeline::

    lesson.story.json          ← authored by a teacher / LLM
          ↓  story_compiler.py
    frames[]                   ← semantic frames, no pixel coords
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


# ── Validation ────────────────────────────────────────────────────────


def validate_lesson(lesson: dict) -> list[str]:
    """Return a list of validation error strings, or ``[]`` if the lesson is valid.

    This is a lightweight structural check. It does **not** type-check values
    or resolve object references across frames.

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

    # Validate frames
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

    return errors
