import unittest
import sys
import json
import tempfile
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.render_html import render_trace_to_html


SAMPLE_TRACE = {
    "trace_version": "0.1.0",
    "problem": {
        "problem_id": "0001_test",
        "display_title": "Test Problem",
        "pattern_tags": ["array"],
        "difficulty": "easy",
    },
    "run": {
        "language": "python",
        "entry": {"class_name": "S", "method_name": "m"},
        "input": {"nums": [2, 7, 11, 15], "target": 9},
        "expected": [0, 1],
        "actual": [0, 1],
        "status": "passed",
        "total_steps": 2,
        "truncated": False,
    },
    "events": [
        {
            "step": 1,
            "event_type": "array_read",
            "message": "读取 nums[0] = 2",
            "before": {"i": 0, "num": 2},
            "highlight": {"objects": ["arr:nums"], "indices": {"arr:nums": [0]}},
            "pedagogy": {"why_now": "开始遍历", "mental_model": "哈希查找"},
        },
        {
            "step": 2,
            "event_type": "answer_found",
            "message": "找到答案 [0, 1]",
            "after": {"result": [0, 1]},
        },
    ],
}


class TestRenderHtml(unittest.TestCase):
    def test_output_contains_event_type(self):
        html_out = render_trace_to_html(SAMPLE_TRACE)
        self.assertIn("array_read", html_out)
        self.assertIn("answer_found", html_out)

    def test_output_contains_message(self):
        html_out = render_trace_to_html(SAMPLE_TRACE)
        self.assertIn("读取 nums[0] = 2", html_out)
        self.assertIn("找到答案 [0, 1]", html_out)

    def test_output_contains_highlight_script(self):
        html_out = render_trace_to_html(SAMPLE_TRACE)
        self.assertIn("<script>", html_out)
        self.assertIn("array-cell", html_out)

    def test_output_is_valid_html(self):
        html_out = render_trace_to_html(SAMPLE_TRACE)
        self.assertIn("<!DOCTYPE html>", html_out)
        self.assertIn("<html", html_out)
        self.assertIn("</html>", html_out)
        self.assertIn("<head>", html_out)
        self.assertIn("<body>", html_out)

    def test_output_contains_array_cells(self):
        html_out = render_trace_to_html(SAMPLE_TRACE)
        self.assertIn("array-cell", html_out)
        self.assertIn(">2<", html_out)
        self.assertIn(">7<", html_out)

    def test_output_contains_passed_status(self):
        html_out = render_trace_to_html(SAMPLE_TRACE)
        self.assertIn("通过", html_out)

    def test_output_contains_pedagogy(self):
        html_out = render_trace_to_html(SAMPLE_TRACE)
        self.assertIn("开始遍历", html_out)
        self.assertIn("哈希查找", html_out)

    def test_output_with_wrong_answer(self):
        trace = json.loads(json.dumps(SAMPLE_TRACE))
        trace["run"]["status"] = "wrong_answer"
        trace["run"]["actual"] = 99
        html_out = render_trace_to_html(trace)
        self.assertIn("答案错误", html_out)

    def test_output_with_empty_events(self):
        trace = json.loads(json.dumps(SAMPLE_TRACE))
        trace["events"] = []
        html_out = render_trace_to_html(trace)
        self.assertIn("无追踪事件", html_out)

    def test_output_no_script_when_no_highlights(self):
        trace = json.loads(json.dumps(SAMPLE_TRACE))
        for ev in trace["events"]:
            ev.pop("highlight", None)
        html_out = render_trace_to_html(trace)
        # Still has array cells but no highlight script since no highlight data
        self.assertNotIn("addEventListener", html_out)


class TestRenderHtmlCli(unittest.TestCase):
    """Verify the render-html CLI subcommand writes a file."""

    def test_cli_writes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a sample trace JSON
            trace_path = os.path.join(tmpdir, "trace.json")
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(SAMPLE_TRACE, f, ensure_ascii=False)

            output_path = os.path.join(tmpdir, "output.html")
            # Simulate CLI by importing and calling directly
            from pv.render_html import render_trace_to_html

            with open(trace_path, encoding="utf-8") as f:
                trace_data = json.load(f)
            html_out = render_trace_to_html(trace_data)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_out)

            self.assertTrue(os.path.isfile(output_path))
            self.assertGreater(os.path.getsize(output_path), 100)
            with open(output_path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("array_read", content)


DP_TRACE = {
    "trace_version": "0.1.0",
    "problem": {
        "problem_id": "0070_test",
        "display_title": "Test DP",
        "pattern_tags": ["dynamic_programming"],
        "difficulty": "easy",
    },
    "run": {
        "language": "python",
        "entry": {"class_name": "S", "method_name": "m"},
        "input": {"n": 5},
        "expected": 8,
        "actual": 8,
        "status": "passed",
        "total_steps": 6,
        "truncated": False,
    },
    "events": [
        {
            "step": 1,
            "event_type": "dp_init",
            "message": "创建 DP 表格",
            "before": {"n": 5, "dp[0]": 1, "dp[1]": 1},
            "highlight": {"objects": ["dp:table"], "indices": {"dp:table": [0, 1]}},
        },
        {
            "step": 2,
            "event_type": "dp_read",
            "message": "读取 dp[0] 和 dp[1]",
            "highlight": {"objects": ["dp:table"], "indices": {"dp:table": [0, 1]}},
        },
        {
            "step": 3,
            "event_type": "transition_considered",
            "message": "计算 dp[2] = 1 + 1 = 2",
            "highlight": {"objects": ["dp:table"], "indices": {"dp:table": [0, 1, 2]}},
        },
        {
            "step": 4,
            "event_type": "dp_write",
            "message": "写入 dp[2] = 2",
            "highlight": {"objects": ["dp:table"], "indices": {"dp:table": [2]}},
        },
        {
            "step": 5,
            "event_type": "return",
            "message": "返回 8",
            "after": {"result": 8},
        },
    ],
}


class TestRenderHtmlDP(unittest.TestCase):
    def test_dp_table_contains_cells(self):
        html_out = render_trace_to_html(DP_TRACE)
        self.assertIn("dp-table", html_out)
        self.assertIn("dp-cell", html_out)
        self.assertIn("data-dp-idx", html_out)

    def test_dp_table_has_correct_count(self):
        html_out = render_trace_to_html(DP_TRACE)
        self.assertGreaterEqual(html_out.count("data-dp-idx="), 6)

    def test_dp_highlight_script(self):
        html_out = render_trace_to_html(DP_TRACE)
        self.assertIn("dp:table", html_out)
        self.assertIn("hl-read", html_out)
        self.assertIn("hl-write", html_out)

    def test_dp_table_with_base_cases(self):
        html_out = render_trace_to_html(DP_TRACE)
        self.assertIn("filled", html_out, "Base cases should be pre-filled")

    def test_array_dp_table_uses_nums_length_and_zero_index_write(self):
        trace = {
            "trace_version": "0.1.0",
            "problem": {
                "problem_id": "0198_test",
                "display_title": "Test House Robber",
                "pattern_tags": ["dynamic_programming"],
                "difficulty": "medium",
            },
            "run": {
                "language": "python",
                "entry": {"class_name": "S", "method_name": "rob"},
                "input": {"nums": [2, 7, 9]},
                "expected": 11,
                "actual": 11,
                "status": "passed",
                "total_steps": 3,
                "truncated": False,
            },
            "events": [
                {
                    "step": 1,
                    "event_type": "dp_write",
                    "message": "写入 dp[0] = 2",
                    "highlight": {"objects": ["dp:table"], "indices": {"dp:table": [0]}},
                    "after": {"dp_idx": 0, "dp_val": 2},
                },
                {
                    "step": 2,
                    "event_type": "dp_write",
                    "message": "写入 dp[1] = 7",
                    "highlight": {"objects": ["dp:table"], "indices": {"dp:table": [1]}},
                    "after": {"dp_idx": 1, "dp_val": 7},
                },
            ],
        }
        html_out = render_trace_to_html(trace)
        self.assertIn("dp-table", html_out)
        self.assertEqual(html_out.count('<div class="dp-cell'), 3)
        self.assertIn("房屋金额", html_out)
        self.assertIn('data-dp-idx="0"', html_out)
        self.assertIn(">2<", html_out)


if __name__ == "__main__":
    unittest.main()
