"""
visual_binder.py — Bind a lesson script to real runtime facts.

This is the BINDING layer in the runtime-bound pipeline::

    lesson.story.json + RuntimeContext
          ↓  bind_lesson()
    BoundLesson         ← runtime values injected, trace_refs verified
          ↓  visual_compiler.py
    positioned frames

Design constraints
------------------
* FAIL FAST: any mismatch between lesson claims and runtime facts raises
  :exc:`BindingError` immediately.  No silent fallback.
* Input object values in the lesson MUST match the real runtime input.
* trace_ref annotations MUST resolve to actual events in the trace.
* Values of variables (var:current, var:need, etc.) are DERIVED from
  runtime facts, not copied from the lesson script.
* The binder does NOT generate frames itself — it only enriches the
  lesson dict with runtime-verified data.
"""
from __future__ import annotations

from typing import Any


# ── Public exceptions ─────────────────────────────────────────────────


class BindingError(Exception):
    """Raised when a lesson claim is inconsistent with runtime facts."""


# ── Type alias ────────────────────────────────────────────────────────

BoundLesson = dict  # lesson dict with "_runtime" and resolved values injected


# ── Main entry point ──────────────────────────────────────────────────


def bind_lesson(lesson: dict, runtime_ctx: dict) -> BoundLesson:
    """Bind *lesson* to *runtime_ctx* and return an enriched lesson dict.

    Checks performed
    ----------------
    1. ``input_array`` objects: lesson ``value`` (if set) must match
       the corresponding runtime input array value-by-value.
    2. ``input_value`` objects: same for scalar inputs.
    3. ``variable`` objects with an explicit ``value`` field: compared against
       the runtime-computed value (via ``_expected_value``) if provided.
    4. Every action ``trace_ref`` (if present) must resolve to at least one
       matching event in the runtime trace.

    Parameters
    ----------
    lesson:
        Parsed ``lesson.story.json`` dict (already validated by
        ``validate_lesson``).
    runtime_ctx:
        The ``RuntimeContext`` returned by
        :func:`~pv.visual_runtime.get_runtime_context`.

    Returns
    -------
    BoundLesson
        A copy of *lesson* with ``_runtime`` metadata injected and all
        ``input_*`` object values overridden with runtime facts.

    Raises
    ------
    BindingError
        If any consistency check fails.
    ValueError
        If runtime_ctx is missing required keys.
    """
    _require_keys(runtime_ctx, ("input", "expected", "actual", "passed", "trace"))

    runtime_input: dict = runtime_ctx["input"]
    trace_events: list[dict] = runtime_ctx["trace"]

    # ── Build resolved-objects list ───────────────────────────────────
    bound_objects: list[dict] = []
    for obj in lesson.get("objects", []):
        bound_obj = dict(obj)  # shallow copy
        obj_id: str = obj.get("id", "")
        obj_type: str = obj.get("type", "")

        if obj_type == "input_array":
            # Derive which input param this corresponds to
            param = _infer_input_param(obj_id, runtime_input)
            if param is not None:
                runtime_val = runtime_input[param]
                # If lesson hardcodes a value, verify it matches
                if "value" in obj:
                    _assert_values_match(
                        lesson_val=obj["value"],
                        runtime_val=runtime_val,
                        context=f"object '{obj_id}' value vs runtime input '{param}'",
                    )
                # Always override with runtime value
                bound_obj["value"] = runtime_val

        elif obj_type == "input_value":
            param = _infer_input_param(obj_id, runtime_input)
            if param is not None:
                runtime_val = runtime_input[param]
                if "value" in obj:
                    _assert_values_match(
                        lesson_val=obj["value"],
                        runtime_val=runtime_val,
                        context=f"object '{obj_id}' value vs runtime input '{param}'",
                    )
                bound_obj["value"] = runtime_val

        elif obj_type == "variable" and "value" in obj:
            # Optional: lesson explicitly asserts what the computed value should be.
            # We check this against the _expected_value hint if provided.
            # (Computed values like var:need are checked in the compiler.)
            expected_val = obj.get("_expected_value")
            if expected_val is not None:
                _assert_values_match(
                    lesson_val=obj["value"],
                    runtime_val=expected_val,
                    context=f"variable object '{obj_id}' explicit value",
                )

        bound_objects.append(bound_obj)

    # ── Validate trace_refs in all frames ─────────────────────────────
    bound_frames: list[dict] = []
    for frame in lesson.get("frames", []):
        bound_frame = dict(frame)
        bound_actions: list[dict] = []

        for action in frame.get("actions", []):
            bound_action = dict(action)
            trace_ref: dict | None = action.get("trace_ref")
            if trace_ref:
                _verify_trace_ref(
                    trace_ref=trace_ref,
                    trace_events=trace_events,
                    context=f"frame '{frame.get('id', '?')}' action '{action.get('action', '?')}'",
                )
            bound_actions.append(bound_action)

        bound_frame["actions"] = bound_actions
        bound_frames.append(bound_frame)

    # ── Assemble bound lesson ─────────────────────────────────────────
    bound: BoundLesson = dict(lesson)
    bound["objects"] = bound_objects
    bound["frames"] = bound_frames
    bound["_runtime"] = {
        "bound":         True,
        "problem_id":    runtime_ctx.get("problem_id", ""),
        "case_index":    runtime_ctx.get("case_index", 0),
        "case_name":     runtime_ctx.get("case_name", ""),
        "solution_mode": runtime_ctx.get("solution_mode", "visual"),
        "input":         runtime_ctx["input"],
        "expected":      runtime_ctx["expected"],
        "actual":        runtime_ctx["actual"],
        "passed":        runtime_ctx["passed"],
        "trace_length":  len(trace_events),
        "error":         runtime_ctx.get("error"),
    }
    return bound


# ── Helpers ───────────────────────────────────────────────────────────


def _require_keys(d: dict, keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in d]
    if missing:
        raise ValueError(f"runtime_ctx is missing required keys: {missing}")


def _infer_input_param(obj_id: str, runtime_input: dict) -> str | None:
    """Try to match an object id like 'input:nums' or 'input:target' to a
    runtime input parameter name.

    Rules
    -----
    * Strip ``input:`` prefix from obj_id.
    * If the remainder is a key in runtime_input, return it.
    * Otherwise return None (unknown input object — skip binding check).
    """
    if obj_id.startswith("input:"):
        param = obj_id[len("input:"):]
        if param in runtime_input:
            return param
    return None


def _assert_values_match(lesson_val: Any, runtime_val: Any, context: str) -> None:
    """Raise BindingError if lesson_val does not match runtime_val."""
    try:
        match = lesson_val == runtime_val
    except Exception:
        match = False
    if not match:
        raise BindingError(
            f"Lesson value mismatch at {context}:\n"
            f"  lesson says: {lesson_val!r}\n"
            f"  runtime has: {runtime_val!r}\n"
            "Fix lesson.story.json to match the actual case input, "
            "or update the case."
        )


def _verify_trace_ref(trace_ref: dict, trace_events: list[dict], context: str) -> None:
    """Raise BindingError if no trace event matches trace_ref.

    A trace event matches if every key in *trace_ref* is present in the
    event and the values are equal.  For example::

        trace_ref = {"event_type": "array_read", "step": 1}
        event     = {"step": 1, "event_type": "array_read", "message": "..."}
        → match

    Only ``event_type``, ``step``, and ``index`` keys are checked.
    """
    if not trace_ref:
        return
    if not trace_events:
        raise BindingError(
            f"trace_ref present at {context} but runtime trace is empty. "
            "Either the solution did not emit trace events, or the wrong "
            "solution_mode was used (need 'visual', not 'validation_only')."
        )
    # Check each declared key in trace_ref
    event_type = trace_ref.get("event_type")
    step       = trace_ref.get("step")      # 1-based step number
    index      = trace_ref.get("index")

    for event in trace_events:
        if event_type is not None and event.get("event_type") != event_type:
            continue
        if step is not None and event.get("step") != step:
            continue
        if index is not None:
            # Check if 'before' dict contains i == index
            before = event.get("before") or {}
            if before.get("i") != index:
                continue
        return  # Found a matching event

    raise BindingError(
        f"trace_ref {trace_ref!r} at {context} did not match any event "
        f"in the runtime trace ({len(trace_events)} events).\n"
        "Lesson script is out of sync with the actual runtime execution."
    )
