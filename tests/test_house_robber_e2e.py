import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.harness import load_cases, load_problem_meta, run_all_cases, run_case


PROBLEM_DIR = str(
    Path(__file__).resolve().parent.parent / "problems" / "0198_house_robber"
)


class TestHouseRobberE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = load_problem_meta(PROBLEM_DIR)
        cls.cases = load_cases(PROBLEM_DIR)

    def test_problem_meta_valid(self):
        self.assertEqual(self.meta["problem_id"], "0198_house_robber")
        self.assertEqual(self.meta["entry"]["class_name"], "Solution")
        self.assertEqual(self.meta["entry"]["method_name"], "rob")
        self.assertIn("dynamic_programming", self.meta["pattern_tags"])

    def test_cases_valid(self):
        self.assertGreaterEqual(len(self.cases), 4)
        for case in self.cases:
            self.assertIn("name", case)
            self.assertIn("args", case)
            self.assertIn("nums", case["args"])
            self.assertIn("expected", case)

    def test_solution_passes_all_cases(self):
        results = run_all_cases(PROBLEM_DIR, solution_file="solution.py")
        self.assertEqual(len(results), len(self.cases))
        for r in results:
            self.assertTrue(r["passed"], f"Case '{r['case_name']}' failed: {r['message']}")

    def test_visual_solution_passes_all_cases(self):
        results = run_all_cases(PROBLEM_DIR, solution_file="visual_solution.py")
        self.assertEqual(len(results), len(self.cases))
        for r in results:
            self.assertTrue(r["passed"], f"Case '{r['case_name']}' failed: {r['message']}")

    def test_visual_solution_trace_has_expected_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_case(
                self.meta,
                self.cases[2],
                os.path.join(PROBLEM_DIR, "visual_solution.py"),
                save_trace=True,
                trace_output_dir=tmpdir,
            )
            self.assertTrue(result["passed"])
            self.assertIsNotNone(result["trace_path"])
            with open(result["trace_path"], encoding="utf-8") as f:
                trace = json.load(f)
            event_types = [e["event_type"] for e in trace["events"]]
            self.assertIn("dp_init", event_types)
            self.assertIn("dp_read", event_types)
            self.assertIn("choose_transition", event_types)
            self.assertIn("dp_write", event_types)
            self.assertIn("return", event_types)

    def test_visual_solution_trace_deterministic(self):
        def get_events():
            with tempfile.TemporaryDirectory() as tmpdir:
                result = run_case(
                    self.meta,
                    self.cases[2],
                    os.path.join(PROBLEM_DIR, "visual_solution.py"),
                    save_trace=True,
                    trace_output_dir=tmpdir,
                )
                with open(result["trace_path"], encoding="utf-8") as f:
                    return json.load(f)["events"]

        events1 = get_events()
        events2 = get_events()
        self.assertEqual(len(events1), len(events2))
        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1["event_type"], e2["event_type"])
            self.assertEqual(e1["step"], e2["step"])
            self.assertEqual(e1["message"], e2["message"])

    def test_wrong_solution_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(os.path.join(PROBLEM_DIR, "problem.json"), tmpdir)
            shutil.copy(os.path.join(PROBLEM_DIR, "cases.json"), tmpdir)
            with open(os.path.join(tmpdir, "solution.py"), "w", encoding="utf-8") as f:
                f.write(
                    """
class Solution:
    def rob(self, nums):
        return sum(nums)
"""
                )
            results = run_all_cases(tmpdir)
            self.assertTrue(
                any(not r["passed"] for r in results),
                "Wrong solution should have at least one failure",
            )


if __name__ == "__main__":
    unittest.main()
