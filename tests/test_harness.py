import unittest
import sys
import os
import tempfile
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.harness import load_problem_meta, load_cases, load_solution, run_case, run_all_cases
from pv.errors import (
    ProblemLoadError, CasesLoadError, ProblemMetaInvalid, CasesInvalid,
    SolutionImportError, ClassNotFoundError, MethodNotFoundError, CaseExecutionError
)


class TestHarnessLoaders(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_file(self, filename, content):
        path = os.path.join(self.tmpdir, filename)
        with open(path, 'w') as f:
            if isinstance(content, (dict, list)):
                json.dump(content, f)
            else:
                f.write(content)
        return path

    def test_load_problem_meta_valid(self):
        self._write_file("problem.json", {
            "problem_id": "0001_test",
            "display_title": "Test",
            "pattern_tags": ["array"],
            "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        meta = load_problem_meta(self.tmpdir)
        self.assertEqual(meta["problem_id"], "0001_test")

    def test_load_problem_meta_missing_file(self):
        with self.assertRaises(ProblemLoadError):
            load_problem_meta(self.tmpdir)

    def test_load_problem_meta_missing_fields(self):
        self._write_file("problem.json", {"problem_id": "test"})
        with self.assertRaises(ProblemMetaInvalid):
            load_problem_meta(self.tmpdir)

    def test_load_cases_valid(self):
        self._write_file("cases.json", [
            {"name": "case0", "args": {"x": 1}, "expected": 2}
        ])
        cases = load_cases(self.tmpdir)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["name"], "case0")

    def test_load_cases_missing_file(self):
        with self.assertRaises(CasesLoadError):
            load_cases(self.tmpdir)

    def test_load_cases_not_list(self):
        self._write_file("cases.json", {"not": "a list"})
        with self.assertRaises(CasesInvalid):
            load_cases(self.tmpdir)

    def test_load_cases_missing_fields(self):
        self._write_file("cases.json", [{"name": "c1"}])
        with self.assertRaises(CasesInvalid):
            load_cases(self.tmpdir)

    def test_load_solution_valid(self):
        path = self._write_file("solution.py", """
class Solution:
    def solve(self, x):
        return x * 2
""")
        mod = load_solution(path)
        self.assertTrue(hasattr(mod, "Solution"))

    def test_load_solution_missing_file(self):
        with self.assertRaises(SolutionImportError):
            load_solution(os.path.join(self.tmpdir, "nonexistent.py"))

    def test_load_solution_syntax_error(self):
        path = self._write_file("broken.py", "class Solution: invalid syntax !!!")
        with self.assertRaises(SolutionImportError):
            load_solution(path)


class TestHarnessRunCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_file(self, filename, content):
        path = os.path.join(self.tmpdir, filename)
        with open(path, 'w') as f:
            if isinstance(content, (dict, list)):
                json.dump(content, f)
            else:
                f.write(content)
        return path

    def test_run_case_pass(self):
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        sol_path = self._write_file("solution.py", """
class Solution:
    def solve(self, x):
        return x * 2
""")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "test_case", "args": {"x": 21}, "expected": 42}
        result = run_case(meta, case, sol_path, save_trace=False)
        self.assertTrue(result["passed"])
        self.assertEqual(result["actual"], 42)

    def test_run_case_wrong_answer(self):
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        sol_path = self._write_file("solution.py", """
class Solution:
    def solve(self, x):
        return x + 1
""")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "test_case", "args": {"x": 1}, "expected": 42}
        result = run_case(meta, case, sol_path, save_trace=False)
        self.assertFalse(result["passed"])

    def test_run_case_exception_recovery(self):
        """Method throws an exception but harness continues without crashing."""
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        sol_path = self._write_file("solution.py", """
class Solution:
    def solve(self, x):
        raise ValueError("intentional error")
""")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "error_case", "args": {"x": 1}, "expected": 2}
        result = run_case(meta, case, sol_path, save_trace=False)
        self.assertFalse(result["passed"])
        self.assertIsNotNone(result["error"])
        self.assertIn("ValueError", result["message"])

    def test_class_not_found(self):
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "WrongName", "method_name": "solve"}
        })
        sol_path = self._write_file("solution.py", "class Solution:\n    def solve(self, x): return x\n")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "c", "args": {"x": 1}, "expected": 1}
        result = run_case(meta, case, sol_path, save_trace=False)
        self.assertFalse(result["passed"])
        self.assertIn("找不到指定的类", result["message"])
        self.assertIn("ClassNotFoundError", result["error"])

    def test_method_not_found(self):
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "nonexistent"}
        })
        sol_path = self._write_file("solution.py", "class Solution:\n    def solve(self, x): return x\n")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "c", "args": {"x": 1}, "expected": 1}
        result = run_case(meta, case, sol_path, save_trace=False)
        self.assertFalse(result["passed"])
        self.assertIn("找不到指定的方法", result["message"])
        self.assertIn("MethodNotFoundError", result["error"])

    def test_state_no_leak(self):
        """Each case creates a fresh module and instance, no state leakage."""
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        # Solution with a counter that would leak if state persists
        sol_path = self._write_file("solution.py", """
class Solution:
    def solve(self, x):
        return x
""")
        meta = load_problem_meta(self.tmpdir)
        case1 = {"name": "c1", "args": {"x": 1}, "expected": 1}
        case2 = {"name": "c2", "args": {"x": 2}, "expected": 2}
        r1 = run_case(meta, case1, sol_path, save_trace=False)
        r2 = run_case(meta, case2, sol_path, save_trace=False)
        self.assertTrue(r1["passed"])
        self.assertTrue(r2["passed"])
        self.assertEqual(r1["actual"], 1)
        self.assertEqual(r2["actual"], 2)

    def test_trace_saved_with_save_trace(self):
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        # Solution that accepts trace
        sol_path = self._write_file("solution.py", """
class Solution:
    def __init__(self, trace=None):
        self.trace = trace
    def solve(self, x):
        if self.trace:
            self.trace.event("test", "testing")
        return x * 2
""")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "tc", "args": {"x": 5}, "expected": 10}
        result = run_case(meta, case, sol_path, save_trace=True, trace_output_dir=self.tmpdir)
        self.assertTrue(result["passed"])
        self.assertIsNotNone(result["trace_path"])
        self.assertTrue(os.path.exists(result["trace_path"]))
        # Verify the saved trace
        with open(result["trace_path"]) as f:
            trace_data = json.load(f)
        self.assertEqual(trace_data["run"]["status"], "passed")
        self.assertEqual(len(trace_data["events"]), 1)

    def test_trace_on_wrong_answer(self):
        """Trace is saved even when answer is wrong."""
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        sol_path = self._write_file("solution.py", """
class Solution:
    def __init__(self, trace=None):
        self.trace = trace
    def solve(self, x):
        if self.trace:
            self.trace.event("test", "wrong path")
        return x + 1
""")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "tc", "args": {"x": 1}, "expected": 100}
        result = run_case(meta, case, sol_path, save_trace=True, trace_output_dir=self.tmpdir)
        self.assertFalse(result["passed"])
        self.assertIsNotNone(result["trace_path"])
        with open(result["trace_path"]) as f:
            trace_data = json.load(f)
        self.assertEqual(trace_data["run"]["status"], "wrong_answer")


class TestHarnessRunAllCases(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_file(self, filename, content):
        path = os.path.join(self.tmpdir, filename)
        with open(path, 'w') as f:
            if isinstance(content, (dict, list)):
                json.dump(content, f)
            else:
                f.write(content)
        return path

    def test_run_all_cases(self):
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        self._write_file("solution.py", """
class Solution:
    def solve(self, x):
        return x * 2
""")
        self._write_file("cases.json", [
            {"name": "c1", "args": {"x": 1}, "expected": 2},
            {"name": "c2", "args": {"x": 5}, "expected": 10},
            {"name": "c3", "args": {"x": 0}, "expected": 0},
        ])
        results = run_all_cases(self.tmpdir)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r["passed"] for r in results))

    def test_run_all_cases_with_trace(self):
        self._write_file("problem.json", {
            "problem_id": "test", "display_title": "Test",
            "pattern_tags": ["array"], "difficulty": "easy",
            "entry": {"class_name": "Solution", "method_name": "solve"}
        })
        self._write_file("solution.py", """
class Solution:
    def __init__(self, trace=None):
        self.trace = trace
    def solve(self, x):
        if self.trace:
            self.trace.event("test", "t")
        return x
""")
        self._write_file("cases.json", [
            {"name": "c1", "args": {"x": 1}, "expected": 1},
        ])
        results = run_all_cases(self.tmpdir, save_trace=True)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["passed"])
        self.assertIsNotNone(results[0]["trace_path"])


if __name__ == "__main__":
    unittest.main()
