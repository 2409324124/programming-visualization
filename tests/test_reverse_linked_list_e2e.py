import unittest
import sys
import json
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.harness import load_problem_meta, load_cases, run_all_cases


PROBLEM_DIR = str(Path(__file__).resolve().parent.parent / "problems" / "0206_reverse_linked_list")


class TestReverseLinkedListE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = load_problem_meta(PROBLEM_DIR)
        cls.cases = load_cases(PROBLEM_DIR)

    def test_problem_meta_valid(self):
        self.assertEqual(self.meta["problem_id"], "0206_reverse_linked_list")
        self.assertEqual(self.meta["entry"]["class_name"], "Solution")
        self.assertEqual(self.meta["entry"]["method_name"], "reverseList")
        self.assertIn("linked_list", self.meta["pattern_tags"])

    def test_cases_valid(self):
        self.assertGreaterEqual(len(self.cases), 4)
        for case in self.cases:
            self.assertIn("name", case)
            self.assertIn("args", case)
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
        """Run visual_solution with trace and verify key event types appear."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            from pv.harness import run_case
            meta = load_problem_meta(PROBLEM_DIR)
            case = load_cases(PROBLEM_DIR)[0]
            result = run_case(meta, case,
                            os.path.join(PROBLEM_DIR, "visual_solution.py"),
                            save_trace=True, trace_output_dir=tmpdir)
            self.assertTrue(result["passed"])
            self.assertIsNotNone(result["trace_path"])
            with open(result["trace_path"]) as f:
                trace = json.load(f)
            event_types = [e["event_type"] for e in trace["events"]]
            self.assertIn("pointer_init", event_types)
            self.assertIn("save_next", event_types)
            self.assertIn("link_set", event_types)
            self.assertIn("cursor_move", event_types)
            self.assertIn("return", event_types)

    def test_visual_solution_trace_deterministic(self):
        """Same case run twice produces identical trace events (ignoring timestamps)."""
        import tempfile
        from pv.harness import run_case

        def get_events():
            with tempfile.TemporaryDirectory() as tmpdir:
                meta = load_problem_meta(PROBLEM_DIR)
                case = load_cases(PROBLEM_DIR)[0]
                result = run_case(meta, case,
                                os.path.join(PROBLEM_DIR, "visual_solution.py"),
                                save_trace=True, trace_output_dir=tmpdir)
                with open(result["trace_path"]) as f:
                    trace = json.load(f)
                return trace["events"]

        events1 = get_events()
        events2 = get_events()
        self.assertEqual(len(events1), len(events2))
        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1["event_type"], e2["event_type"])
            self.assertEqual(e1["step"], e2["step"])
            self.assertEqual(e1["message"], e2["message"])

    def test_wrong_solution_fails(self):
        """A deliberately wrong solution should fail."""
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(os.path.join(PROBLEM_DIR, "problem.json"), tmpdir)
            shutil.copy(os.path.join(PROBLEM_DIR, "cases.json"), tmpdir)
            with open(os.path.join(tmpdir, "solution.py"), 'w') as f:
                f.write("""
class Solution:
    def reverseList(self, head):
        return head  # always wrong — returns unchanged list
""")
            results = run_all_cases(tmpdir)
            self.assertTrue(any(not r["passed"] for r in results),
                           "Wrong solution should have at least one failure")


if __name__ == "__main__":
    unittest.main()
