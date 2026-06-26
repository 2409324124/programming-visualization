"""Tests for src/pv/visual_runtime.py.

Requirements covered
--------------------
* get_runtime_context returns correct input/expected/actual/passed/trace
* actual [0, 1] is present
* trace events are real (not empty)
* validation_only mode returns empty trace
* ValidationOnlyError when visual_solution.py absent and mode='visual'
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.visual_runtime import get_runtime_context, ValidationOnlyError

PROBLEM_DIR = str(
    Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum"
)


class TestGetRuntimeContext(unittest.TestCase):
    """Unit tests for get_runtime_context()."""

    def _ctx(self, case_index: int = 0, mode: str = "visual") -> dict:
        return get_runtime_context(PROBLEM_DIR, case_index, solution_mode=mode)

    # ── basic structure ────────────────────────────────────────────────

    def test_returns_all_required_keys(self):
        ctx = self._ctx()
        for key in ("problem_id", "case_index", "case_name", "solution_mode",
                    "input", "expected", "actual", "passed", "trace", "error"):
            self.assertIn(key, ctx, f"Missing key: {key}")

    def test_problem_id(self):
        ctx = self._ctx()
        self.assertEqual(ctx["problem_id"], "0001_two_sum")

    def test_case_index(self):
        ctx = self._ctx(0)
        self.assertEqual(ctx["case_index"], 0)

    # ── case 0 correctness ─────────────────────────────────────────────

    def test_input_is_real_case_data(self):
        ctx = self._ctx(0)
        self.assertEqual(ctx["input"]["nums"], [2, 7, 11, 15])
        self.assertEqual(ctx["input"]["target"], 9)

    def test_expected_is_0_1(self):
        ctx = self._ctx(0)
        self.assertEqual(ctx["expected"], [0, 1])

    def test_actual_is_0_1(self):
        """Requirement: actual [0, 1] comes from real execution."""
        ctx = self._ctx(0)
        self.assertEqual(sorted(ctx["actual"]), [0, 1])

    def test_passed_is_true_for_case_0(self):
        """Requirement: passed=True for case 0."""
        ctx = self._ctx(0)
        self.assertTrue(ctx["passed"])

    def test_error_is_none_for_correct_solution(self):
        ctx = self._ctx(0)
        self.assertIsNone(ctx["error"])

    # ── trace ──────────────────────────────────────────────────────────

    def test_trace_is_non_empty(self):
        """Requirement: trace events come from real harness execution."""
        ctx = self._ctx(0)
        self.assertGreater(len(ctx["trace"]), 0)

    def test_trace_contains_array_read_events(self):
        ctx = self._ctx(0)
        types = {e["event_type"] for e in ctx["trace"]}
        self.assertIn("array_read", types)

    def test_trace_contains_hash_map_events(self):
        ctx = self._ctx(0)
        types = {e["event_type"] for e in ctx["trace"]}
        self.assertTrue(types & {"hash_map_get", "hash_map_put", "answer_found"})

    def test_trace_events_have_required_fields(self):
        ctx = self._ctx(0)
        for event in ctx["trace"]:
            for field in ("step", "event_type", "message"):
                self.assertIn(field, event, f"Trace event missing '{field}': {event}")

    def test_trace_array_read_step1_has_index_0(self):
        """array_read at step 1 should read nums[0]."""
        ctx = self._ctx(0)
        step1 = next((e for e in ctx["trace"] if e["step"] == 1), None)
        self.assertIsNotNone(step1)
        self.assertEqual(step1["event_type"], "array_read")
        before = step1.get("before") or {}
        self.assertEqual(before.get("i"), 0)
        self.assertEqual(before.get("num"), 2)

    # ── other cases ────────────────────────────────────────────────────

    def test_case_1_different_input(self):
        ctx = self._ctx(1)
        self.assertEqual(ctx["input"]["nums"], [3, 2, 4])
        self.assertEqual(ctx["input"]["target"], 6)
        self.assertTrue(ctx["passed"])

    # ── validation_only mode ───────────────────────────────────────────

    def test_validation_only_mode_no_trace(self):
        """Requirement: validation_only solution must not generate fake trace."""
        ctx = get_runtime_context(PROBLEM_DIR, 0, solution_mode="validation_only")
        self.assertEqual(ctx["trace"], [])
        self.assertEqual(ctx["solution_mode"], "validation_only")

    def test_validation_only_still_gives_actual_result(self):
        ctx = get_runtime_context(PROBLEM_DIR, 0, solution_mode="validation_only")
        self.assertEqual(sorted(ctx["actual"]), [0, 1])
        self.assertTrue(ctx["passed"])

    # ── error cases ────────────────────────────────────────────────────

    def test_raises_file_not_found_for_bad_dir(self):
        with self.assertRaises((FileNotFoundError, Exception)):
            get_runtime_context("/nonexistent/path", 0)

    def test_raises_index_error_for_out_of_range_case(self):
        with self.assertRaises(IndexError):
            get_runtime_context(PROBLEM_DIR, 999)

    def test_raises_validation_only_error_when_visual_missing(self):
        """Requirement: if visual_solution.py absent and mode='visual', raise ValidationOnlyError."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create a minimal problem directory WITHOUT visual_solution.py
            import shutil
            shutil.copy(os.path.join(PROBLEM_DIR, "cases.json"), tmp)
            shutil.copy(os.path.join(PROBLEM_DIR, "problem.json"), tmp)
            shutil.copy(os.path.join(PROBLEM_DIR, "solution.py"), tmp)
            with self.assertRaises(ValidationOnlyError):
                get_runtime_context(tmp, 0, solution_mode="visual")


if __name__ == "__main__":
    unittest.main()
