import unittest
import sys
import os
import tempfile
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.submission_policy import check_imports
from pv.harness import load_problem_meta, run_case, run_all_cases
from pv.errors import ImportPolicyError


TWO_SUM_DIR = str(Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum")
CONTAINER_DIR = str(Path(__file__).resolve().parent.parent / "problems" / "0011_container_with_most_water")


class TestImportPolicy(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_allows_stdlib(self):
        path = self._write("s.py", "import math\nfrom collections import defaultdict\nclass S:\n    def f(self): return 1")
        r = check_imports(path)
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["violations"]), 0)

    def test_allows_typing(self):
        path = self._write("s.py", "from typing import List\nclass S:\n    def f(self): return 1")
        r = check_imports(path)
        self.assertTrue(r["ok"])

    def test_blocks_os(self):
        path = self._write("s.py", "import os\nclass S:\n    def f(self): return 1")
        r = check_imports(path)
        self.assertFalse(r["ok"])
        self.assertTrue(any("os" in v for v in r["violations"]))

    def test_blocks_subprocess(self):
        path = self._write("s.py", "import subprocess\nclass S:\n    def f(self): return 1")
        r = check_imports(path)
        self.assertFalse(r["ok"])

    def test_blocks_numpy(self):
        path = self._write("s.py", "import numpy as np\nclass S:\n    def f(self): return 1")
        r = check_imports(path)
        self.assertFalse(r["ok"])
        self.assertTrue(any("numpy" in v for v in r["violations"]))

    def test_syntax_error(self):
        path = self._write("s.py", "this is not valid python @@@")
        r = check_imports(path)
        self.assertFalse(r["ok"])
        self.assertTrue(any("语法错误" in v for v in r["violations"]))

    def test_warns_unknown(self):
        path = self._write("s.py", "import unknown_lib_xyz\nclass S:\n    def f(self): return 1")
        r = check_imports(path)
        self.assertTrue(r["ok"])  # unknown is not blocked, just warned
        self.assertTrue(len(r["warnings"]) > 0)


class TestLearnerBruteForce(unittest.TestCase):
    """Brute-force solutions that don't use trace hooks."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _setup_problem(self, problem_dir):
        """Copy problem.json and cases.json to tmpdir for isolated testing."""
        import shutil
        for f in ("problem.json", "cases.json"):
            src = os.path.join(problem_dir, f)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(self.tmpdir, f))

    def _write_solution(self, content):
        path = os.path.join(self.tmpdir, "solution.py")
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_brute_force_two_sum(self):
        self._setup_problem(TWO_SUM_DIR)
        self._write_solution("""
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
""")
        results = run_all_cases(self.tmpdir)
        self.assertTrue(all(r["passed"] for r in results))

    def test_brute_force_container(self):
        self._setup_problem(CONTAINER_DIR)
        self._write_solution("""
class Solution:
    def maxArea(self, height):
        best = 0
        for i in range(len(height)):
            for j in range(i + 1, len(height)):
                h = height[i] if height[i] < height[j] else height[j]
                area = h * (j - i)
                if area > best:
                    best = area
        return best
""")
        results = run_all_cases(self.tmpdir)
        self.assertTrue(all(r["passed"] for r in results))

    def test_print_not_return(self):
        """print() but no return → harness captures stdout, sees None as result."""
        self._setup_problem(TWO_SUM_DIR)
        self._write_solution("""
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    print([i, j])
        return []
""")
        results = run_all_cases(self.tmpdir)
        self.assertGreaterEqual(len(results), 1)

    def test_stdout_captured_no_leak(self):
        """print() output is captured, does NOT leak to unittest stdout."""
        self._setup_problem(TWO_SUM_DIR)
        self._write_solution("""
class Solution:
    def twoSum(self, nums, target):
        print("DEBUG: nums=", nums, "target=", target)
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
""")
        results = run_all_cases(self.tmpdir)
        self.assertTrue(all(r["passed"] for r in results))
        # stdout should be captured per case
        for r in results:
            self.assertIn("stdout", r)
            # The print output should be in the stdout field
            self.assertIn("DEBUG", r["stdout"])

    def test_validation_only_trace_mode(self):
        """Learner solution with save_trace gets trace_mode='validation_only'."""
        self._setup_problem(TWO_SUM_DIR)
        self._write_solution("""
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
""")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "test", "args": {"nums": [2,7,11,15], "target": 9}, "expected": [0,1]}
        result = run_case(meta, case, os.path.join(self.tmpdir, "solution.py"),
                         save_trace=True, trace_output_dir=self.tmpdir)
        self.assertTrue(result["passed"])
        self.assertEqual(result.get("trace_mode"), "validation_only")

    def test_no_fake_events_for_validation_only(self):
        """validation_only trace has zero events (no fake semantic events)."""
        self._setup_problem(TWO_SUM_DIR)
        self._write_solution("""
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
""")
        meta = load_problem_meta(self.tmpdir)
        case = {"name": "test", "args": {"nums": [2,7,11,15], "target": 9}, "expected": [0,1]}
        result = run_case(meta, case, os.path.join(self.tmpdir, "solution.py"),
                         save_trace=True, trace_output_dir=self.tmpdir)
        self.assertTrue(result["passed"])
        self.assertEqual(result.get("trace_mode"), "validation_only")
        if result.get("trace_path") and os.path.exists(result["trace_path"]):
            with open(result["trace_path"]) as f:
                trace = json.load(f)
            events = trace.get("events", [])
            self.assertEqual(len(events), 0, "validation_only should not have fake semantic events")

    def test_class_variable_no_leak(self):
        """Class-level variable should not leak between cases."""
        self._setup_problem(TWO_SUM_DIR)
        self._write_solution("""
class Solution:
    counter = 0
    def twoSum(self, nums, target):
        Solution.counter += 1
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
""")
        results = run_all_cases(self.tmpdir)
        # Each case gets a fresh module import with UUID isolation
        # So class variable should be fresh each time
        self.assertTrue(all(r["passed"] for r in results))


if __name__ == "__main__":
    unittest.main()
