import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.render_text import render_trace_to_text


class TestRenderText(unittest.TestCase):
    def setUp(self):
        self.sample_trace = {
            "trace_version": "0.1.0",
            "problem": {"problem_id": "test", "display_title": "Test Problem"},
            "run": {
                "language": "python",
                "entry": {"class_name": "S", "method_name": "m"},
                "input": {"x": 1},
                "expected": 2,
                "actual": 2,
                "status": "passed",
                "total_steps": 2,
                "truncated": False
            },
            "events": [
                {
                    "step": 1,
                    "event_type": "array_read",
                    "message": "读取 nums[0] = 2",
                    "before": {"i": 0},
                    "pedagogy": {"why_now": "开始遍历"}
                },
                {
                    "step": 2,
                    "event_type": "answer_found",
                    "message": "找到答案",
                    "after": {"result": [0, 1]},
                    "pedagogy": {"mental_model": "哈希查找"}
                }
            ]
        }

    def test_render_basic_trace(self):
        output = render_trace_to_text(self.sample_trace)
        self.assertIn("Test Problem", output)
        self.assertIn("Step 1", output)
        self.assertIn("Step 2", output)
        self.assertIn("array_read", output)
        self.assertIn("找到答案", output)
        self.assertIn("通过", output)

    def test_render_includes_result(self):
        output = render_trace_to_text(self.sample_trace)
        self.assertIn("通过", output)
        self.assertIn("2", output)

    def test_render_empty_events(self):
        trace = dict(self.sample_trace)
        trace["events"] = []
        output = render_trace_to_text(trace)
        self.assertIn("无追踪事件", output)

    def test_render_truncated_warning(self):
        trace = dict(self.sample_trace)
        trace["run"] = dict(trace["run"])
        trace["run"]["truncated"] = True
        output = render_trace_to_text(trace)
        self.assertIn("截断", output)

    def test_render_wrong_answer_status(self):
        trace = dict(self.sample_trace)
        trace["run"] = dict(trace["run"])
        trace["run"]["status"] = "wrong_answer"
        trace["run"]["actual"] = 99
        output = render_trace_to_text(trace)
        self.assertIn("答案错误", output)
        self.assertIn("99", output)

    def test_render_missing_optional_fields(self):
        trace = dict(self.sample_trace)
        trace["events"] = [{"step": 1, "event_type": "test", "message": "hi"}]
        output = render_trace_to_text(trace)
        self.assertIn("hi", output)


if __name__ == "__main__":
    unittest.main()
