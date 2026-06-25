import unittest
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.trace_schema import TraceBuilder, TraceEvent


class TestTraceSchema(unittest.TestCase):
    def setUp(self):
        self.meta = {"problem_id": "test", "display_title": "Test"}
        self.case = {"name": "case0", "args": {"x": 1}, "expected": 2}

    def test_create_trace_builder(self):
        tb = TraceBuilder(self.meta, self.case)
        self.assertEqual(tb.step_count, 0)
        self.assertFalse(tb._finished)

    def test_add_event_increments_step(self):
        tb = TraceBuilder(self.meta, self.case)
        tb.event("test_event", "msg1")
        self.assertEqual(tb.step_count, 1)
        tb.event("test_event", "msg2")
        tb.event("test_event", "msg3")
        self.assertEqual(tb.step_count, 3)

    def test_to_dict_contains_envelope(self):
        tb = TraceBuilder(self.meta, self.case)
        tb.event("test_event", "hello")
        tb.finish("passed", 42)
        d = tb.to_dict()
        self.assertIn("trace_version", d)
        self.assertIn("problem", d)
        self.assertIn("run", d)
        self.assertIn("events", d)
        self.assertEqual(len(d["events"]), 1)

    def test_finish_sets_status(self):
        tb = TraceBuilder(self.meta, self.case)
        tb.finish("passed", [0, 1])
        self.assertTrue(tb._finished)
        d = tb.to_dict()
        self.assertEqual(d["run"]["status"], "passed")
        self.assertEqual(d["run"]["actual"], [0, 1])

    def test_max_events_truncates(self):
        tb = TraceBuilder(self.meta, self.case, max_events=3)
        for i in range(5):
            tb.event("test", f"msg{i}")
        self.assertEqual(tb.step_count, 3)
        self.assertTrue(tb._truncated)
        d = tb.to_dict()
        self.assertTrue(d["run"]["truncated"])

    def test_event_after_finish_ignored(self):
        tb = TraceBuilder(self.meta, self.case)
        tb.event("t1", "m1")
        tb.finish("passed", 1)
        tb.event("t2", "m2")
        self.assertEqual(tb.step_count, 1)

    def test_to_json_serializable(self):
        tb = TraceBuilder(self.meta, self.case)
        tb.event("array_read", "读取 nums[0] = 2",
                 before={"i": 0}, after={"i": 1},
                 pedagogy={"why_now": "遍历数组"})
        tb.finish("passed", [0, 1])
        s = tb.to_json()
        d = json.loads(s)
        self.assertEqual(len(d["events"]), 1)
        self.assertEqual(d["events"][0]["event_type"], "array_read")

    def test_step_property(self):
        tb = TraceBuilder(self.meta, self.case)
        self.assertEqual(tb.step_count, 0)
        tb.event("t1", "m1")
        self.assertEqual(tb.step_count, 1)


if __name__ == "__main__":
    unittest.main()
