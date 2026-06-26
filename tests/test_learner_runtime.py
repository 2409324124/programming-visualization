import unittest
import sys
import os
import tempfile
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.learner_runtime import get_learner_runtime

TWO_SUM_DIR = str(Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum")


class TestLearnerRuntime(unittest.TestCase):
    def test_render_code_runs_two_sum(self):
        sol_path = os.path.join(TWO_SUM_DIR, "solution.py")
        runtime = get_learner_runtime(TWO_SUM_DIR, sol_path, 0)
        self.assertTrue(runtime["passed"])
        self.assertEqual(runtime["actual"], [0, 1])
        self.assertEqual(runtime["trace_mode"], "line_level")
    
    def test_line_trace_has_events(self):
        sol_path = os.path.join(TWO_SUM_DIR, "solution.py")
        runtime = get_learner_runtime(TWO_SUM_DIR, sol_path, 0)
        self.assertGreater(len(runtime["line_trace"]), 0,
            "Line trace should have events from real execution")
    
    def test_source_code_present(self):
        sol_path = os.path.join(TWO_SUM_DIR, "solution.py")
        runtime = get_learner_runtime(TWO_SUM_DIR, sol_path, 0)
        self.assertIn("class Solution", runtime["source_code"])
    
    def test_passed_is_true_for_correct_solution(self):
        sol_path = os.path.join(TWO_SUM_DIR, "solution.py")
        runtime = get_learner_runtime(TWO_SUM_DIR, sol_path, 0)
        self.assertTrue(runtime["passed"])
    
    def test_input_present(self):
        sol_path = os.path.join(TWO_SUM_DIR, "solution.py")
        runtime = get_learner_runtime(TWO_SUM_DIR, sol_path, 0)
        self.assertIn("nums", runtime["input"])
        self.assertEqual(runtime["input"]["target"], 9)
    
    def test_print_no_return_shows_stdout_and_fails(self):
        """Code that prints but doesn't return proper answer."""
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(os.path.join(TWO_SUM_DIR, "problem.json"), tmpdir)
            shutil.copy(os.path.join(TWO_SUM_DIR, "cases.json"), tmpdir)
            wrong_path = os.path.join(tmpdir, "solution.py")
            with open(wrong_path, 'w') as f:
                f.write("""
class Solution:
    def twoSum(self, nums, target):
        print("DEBUG hello")
        return []  # wrong
""")
            runtime = get_learner_runtime(tmpdir, wrong_path, 0)
            self.assertFalse(runtime["passed"])
            self.assertIn("DEBUG", runtime["stdout"])
    
    def test_error_code_shows_error(self):
        """Code that throws an exception shows error in runtime."""
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy(os.path.join(TWO_SUM_DIR, "problem.json"), tmpdir)
            shutil.copy(os.path.join(TWO_SUM_DIR, "cases.json"), tmpdir)
            bad_path = os.path.join(tmpdir, "solution.py")
            with open(bad_path, 'w') as f:
                f.write("""
class Solution:
    def twoSum(self, nums, target):
        raise ValueError("intentional test error")
""")
            runtime = get_learner_runtime(tmpdir, bad_path, 0)
            self.assertFalse(runtime["passed"])
            self.assertIsNotNone(runtime["error"])
            self.assertIn("ValueError", runtime["error"])


if __name__ == "__main__":
    unittest.main()
