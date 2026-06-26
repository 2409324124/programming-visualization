"""Tests for src/pv/visual_binder.py.

Requirements covered
--------------------
* bind_lesson returns BoundLesson with _runtime metadata
* input_array objects get values from runtime, not lesson
* BindingError on wrong nums[0] value (lesson says 999, runtime says 2)
* BindingError on wrong input value (e.g. nums=[999,...])
* BindingError on trace_ref referencing absent event type
* BindingError when trace is empty but trace_ref present
* Valid trace_ref passes binding
* map_entry: refs are not binding-checked (runtime-generated)
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.visual_binder import bind_lesson, BindingError
from pv.visual_runtime import get_runtime_context

PROBLEM_DIR = str(
    Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum"
)
LESSON_PATH = str(
    Path(__file__).resolve().parent.parent
    / "problems" / "0001_two_sum" / "lesson.story.json"
)


def _load_lesson() -> dict:
    with open(LESSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_runtime(case_index: int = 0) -> dict:
    return get_runtime_context(PROBLEM_DIR, case_index)


class TestBindLesson(unittest.TestCase):
    """Unit tests for bind_lesson()."""

    def test_returns_bound_lesson_with_runtime_key(self):
        lesson  = _load_lesson()
        runtime = _load_runtime()
        bound   = bind_lesson(lesson, runtime)
        self.assertIn("_runtime", bound)

    def test_runtime_metadata_present(self):
        bound = bind_lesson(_load_lesson(), _load_runtime())
        rt = bound["_runtime"]
        for key in ("bound", "actual", "expected", "passed", "trace_length"):
            self.assertIn(key, rt, f"Missing _runtime key: {key}")

    def test_bound_is_true(self):
        bound = bind_lesson(_load_lesson(), _load_runtime())
        self.assertTrue(bound["_runtime"]["bound"])

    def test_actual_is_0_1(self):
        """Requirement: actual [0, 1] present in bound lesson runtime metadata."""
        bound = bind_lesson(_load_lesson(), _load_runtime())
        self.assertEqual(sorted(bound["_runtime"]["actual"]), [0, 1])

    def test_expected_is_0_1(self):
        """Requirement: expected [0, 1] present."""
        bound = bind_lesson(_load_lesson(), _load_runtime())
        self.assertEqual(bound["_runtime"]["expected"], [0, 1])

    def test_passed_is_true(self):
        """Requirement: passed=True present."""
        bound = bind_lesson(_load_lesson(), _load_runtime())
        self.assertTrue(bound["_runtime"]["passed"])

    def test_trace_length_nonzero(self):
        bound = bind_lesson(_load_lesson(), _load_runtime())
        self.assertGreater(bound["_runtime"]["trace_length"], 0)

    # ── input object binding ───────────────────────────────────────────

    def test_input_nums_value_comes_from_runtime(self):
        """Requirement: input:nums value in bound lesson matches runtime case data.

        The binder OVERRIDES input object values with runtime data and VALIDATES
        consistency.  So if the lesson already has the correct value (no mismatch),
        the bound lesson's value equals the runtime input.
        """
        lesson = _load_lesson()
        # Do not alter the lesson — it matches case 0 already.
        bound = bind_lesson(lesson, _load_runtime())
        for obj in bound["objects"]:
            if obj["id"] == "input:nums":
                self.assertEqual(obj["value"], [2, 7, 11, 15],
                                 "input:nums must equal the runtime case data")
                return
        self.fail("input:nums not found in bound objects")

    # ── BindingError: wrong nums value (test req. 6) ──────────────────

    def test_binding_error_when_nums_value_wrong(self):
        """Requirement 6: lesson has nums[0]=999, runtime has 2 → BindingError."""
        lesson = _load_lesson()
        # Set a wrong hardcoded value that does NOT match runtime [2,7,11,15]
        for obj in lesson["objects"]:
            if obj["id"] == "input:nums":
                obj["value"] = [999, 7, 11, 15]  # mismatch on first element
        runtime = _load_runtime()

        with self.assertRaises(BindingError) as ctx:
            bind_lesson(lesson, runtime)
        msg = str(ctx.exception)
        self.assertIn("999", msg)

    def test_binding_error_when_full_nums_array_wrong(self):
        """If entire nums array is wrong, BindingError with helpful message."""
        lesson = _load_lesson()
        for obj in lesson["objects"]:
            if obj["id"] == "input:nums":
                obj["value"] = [1, 2, 3]  # completely different
        with self.assertRaises(BindingError):
            bind_lesson(lesson, _load_runtime())

    # ── BindingError: computed variable wrong value (test req. 7) ────

    def test_binding_error_when_variable_explicit_value_wrong(self):
        """Requirement 7: if a variable has an explicit value that mismatches
        the _expected_value hint, BindingError is raised."""
        lesson = _load_lesson()
        # Add a variable object with explicit wrong value and _expected_value hint
        lesson["objects"].append({
            "id": "var:need",
            "type": "variable",
            "value": 999,           # wrong! runtime would compute 7
            "_expected_value": 7,   # binder checks this
        })
        # Binder checks variable.value vs _expected_value
        with self.assertRaises(BindingError) as ctx:
            bind_lesson(lesson, _load_runtime())
        msg = str(ctx.exception)
        self.assertIn("999", msg)

    # ── BindingError: bad trace_ref ───────────────────────────────────

    def test_binding_error_on_unknown_trace_ref_event_type(self):
        """Requirement 8: trace_ref referencing absent event type → BindingError."""
        lesson = _load_lesson()
        # Inject a trace_ref with a non-existent event type
        if lesson["frames"]:
            lesson["frames"][0]["actions"].append({
                "action": "appear",
                "object": "input:nums",
                "trace_ref": {"event_type": "nonexistent_event_xyz"},
            })
        with self.assertRaises(BindingError) as ctx:
            bind_lesson(lesson, _load_runtime())
        msg = str(ctx.exception)
        self.assertIn("nonexistent_event_xyz", msg)

    def test_binding_error_when_trace_empty_but_ref_present(self):
        """trace_ref present but trace is empty → BindingError."""
        lesson = _load_lesson()
        if lesson["frames"]:
            lesson["frames"][0]["actions"].append({
                "action": "appear",
                "object": "input:nums",
                "trace_ref": {"event_type": "array_read"},
            })
        runtime = dict(_load_runtime())
        runtime["trace"] = []  # empty trace
        with self.assertRaises(BindingError) as ctx:
            bind_lesson(lesson, runtime)
        self.assertIn("empty", str(ctx.exception))

    # ── Valid trace_ref passes ─────────────────────────────────────────

    def test_valid_trace_ref_array_read_passes(self):
        """A trace_ref matching a real array_read event should NOT raise."""
        lesson = _load_lesson()
        if lesson["frames"]:
            lesson["frames"][0]["actions"].append({
                "action": "appear",
                "object": "input:nums",
                "trace_ref": {"event_type": "array_read"},
            })
        # Should not raise
        bound = bind_lesson(lesson, _load_runtime())
        self.assertIn("_runtime", bound)

    def test_valid_trace_ref_with_step_passes(self):
        """trace_ref with matching step number passes."""
        lesson = _load_lesson()
        if lesson["frames"]:
            lesson["frames"][0]["actions"].append({
                "action": "appear",
                "object": "input:nums",
                "trace_ref": {"event_type": "array_read", "step": 1},
            })
        bind_lesson(lesson, _load_runtime())  # no exception

    # ── requires runtime keys ──────────────────────────────────────────

    def test_raises_value_error_on_missing_runtime_keys(self):
        """If runtime_ctx lacks required keys, ValueError is raised."""
        lesson = _load_lesson()
        with self.assertRaises(ValueError):
            bind_lesson(lesson, {"input": {}})  # missing expected/actual/passed/trace

    # ── case 1 binding works too ──────────────────────────────────────

    def test_case_1_binding(self):
        """Case 1 has nums=[3,2,4].  Binding with the same lesson (no hardcoded value
        mismatch) should succeed and the bound input:nums value should be [3,2,4]."""
        runtime = _load_runtime(1)
        lesson  = _load_lesson()
        # Remove any hardcoded 'value' from input:nums so binder just injects runtime value
        for obj in lesson["objects"]:
            if obj["id"] == "input:nums" and "value" in obj:
                del obj["value"]
        bound = bind_lesson(lesson, runtime)
        for obj in bound["objects"]:
            if obj["id"] == "input:nums":
                self.assertEqual(obj["value"], [3, 2, 4])
                return
        # If input:nums not in objects list, binding still succeeded
        self.assertIn("_runtime", bound)

    def test_all_original_lesson_fields_preserved(self):
        """Binding should not drop lesson metadata fields."""
        lesson = _load_lesson()
        bound  = bind_lesson(lesson, _load_runtime())
        for key in ("lesson_id", "title", "problem_id", "frames"):
            self.assertIn(key, bound, f"Missing key after binding: {key}")


if __name__ == "__main__":
    unittest.main()
