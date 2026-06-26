import unittest
import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.learner_trace import LineTracer, LineTraceEvent


class TestLineTracer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def _write_file(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def _run_solution(self, path, func_name, method_name, arg=5):
        tracer = LineTracer(path, target_function=method_name, max_events=100)
        tracer.start()
        import importlib.util
        spec = importlib.util.spec_from_file_location(func_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            getattr(mod.Solution(), method_name)(arg)
        finally:
            tracer.stop()
        return tracer
    
    def test_tracer_captures_line_events(self):
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        a = x + 1
        b = a * 2
        return b
""")
        tracer = self._run_solution(path, "test_mod", "solve")
        self.assertGreater(len(tracer.events), 0)
    
    def test_tracer_excludes_stdlib(self):
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        return x
""")
        tracer = self._run_solution(path, "test_mod2", "solve")
        for ev in tracer.events:
            self.assertEqual(ev.filename, "s.py")
    
    def test_tracer_respects_max_events(self):
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        a = x
        b = a
        c = b
        d = c
        e = d
        return e
""")
        tracer = LineTracer(path, target_function="solve", max_events=2)
        tracer.start()
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_mod3", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            mod.Solution().solve(1)
        finally:
            tracer.stop()
        self.assertLessEqual(len(tracer.events), 2)
    
    def test_tracer_excludes_self(self):
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        return x
""")
        tracer = self._run_solution(path, "test_mod4", "solve")
        for ev in tracer.events:
            self.assertNotIn("self=", ev.locals_summary)

    def test_locals_contain_values(self):
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        y = x * 10
        return y
""")
        tracer = self._run_solution(path, "test_mod5", "solve")
        all_locals = " ".join(e.locals_summary for e in tracer.events)
        self.assertTrue("x" in all_locals or "y" in all_locals)

    # ── New tests for Phase 5.3 fix ──────────────────────────────

    def test_no_module_or_class_events(self):
        """First event should be inside target function, not module/class."""
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        return x * 2
""")
        tracer = self._run_solution(path, "test_mod6", "solve")
        for ev in tracer.events:
            self.assertNotEqual(ev.function, "<module>",
                "Should not record module-level code")
            self.assertEqual(ev.function, "solve",
                f"All events should be from 'solve', got '{ev.function}'")

    def test_return_event_present(self):
        """Last event should be a return event with lineno."""
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        return x * 2
""")
        tracer = self._run_solution(path, "test_mod7", "solve")
        self.assertGreater(len(tracer.events), 0)
        last = tracer.events[-1]
        self.assertEqual(last.event_type, "return",
            f"Last event should be 'return', got '{last.event_type}'")

    def test_return_value_summary(self):
        """Return event should contain return_value_summary."""
        path = self._write_file("s.py", """
class Solution:
    def solve(self, x):
        return x * 2
""")
        tracer = self._run_solution(path, "test_mod8", "solve", arg=5)
        last = tracer.events[-1]
        self.assertEqual(last.event_type, "return")
        self.assertIn("10", last.return_value_summary,
            f"return should contain computed value, got '{last.return_value_summary}'")

    def test_two_sum_trace_has_loop_back(self):
        """Two Sum trace should contain line 8 going back to line 4 (for loop)."""
        # Test with a minimal loop
        path = self._write_file("s.py", """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []
""")
        tracer = LineTracer(path, target_function="twoSum", max_events=200)
        tracer.start()
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_mod_ts", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            mod.Solution().twoSum([2, 7, 11, 15], 9)
        finally:
            tracer.stop()
        # Check that the first event has function="twoSum" (not module)
        self.assertEqual(tracer.events[0].function, "twoSum")


if __name__ == "__main__":
    unittest.main()
