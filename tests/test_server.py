"""test_server.py — Tests for the local interactive runner server module."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from pv.server import (
    render_code_request,
    run_all_fixed_cases_request,
    run_generated_checks_request,
    scan_problems,
    problem_detail,
    _MAIN_PAGE_HTML,
    EXECUTION_TIMEOUT,
    MAX_BODY_BYTES,
    ThreadingHTTPServer,
)


class TestScanProblems(unittest.TestCase):
    """Test problem listing."""

    def test_scan_returns_list(self):
        problems = scan_problems()
        self.assertIsInstance(problems, list)

    def test_two_sum_present(self):
        problems = scan_problems()
        ids = [p["id"] for p in problems]
        self.assertIn("0001_two_sum", ids)

    def test_problem_has_required_fields(self):
        problems = scan_problems()
        for p in problems:
            self.assertIn("id", p)
            self.assertIn("title", p)
            self.assertIn("difficulty", p)
            self.assertIn("tags", p)
            self.assertIn("case_count", p)


class TestProblemDetail(unittest.TestCase):
    """Test problem detail endpoint."""

    def test_two_sum_detail(self):
        detail = problem_detail("0001_two_sum")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["id"], "0001_two_sum")
        self.assertIn("title", detail)
        self.assertIn("cases", detail)
        self.assertIn("default_code", detail)
        self.assertIsInstance(detail["cases"], list)
        self.assertGreater(len(detail["cases"]), 0)
        self.assertIsInstance(detail["default_code"], str)
        self.assertIn("class Solution", detail["default_code"])

    def test_unknown_problem_returns_none(self):
        detail = problem_detail("nonexistent_problem_99999")
        self.assertIsNone(detail)


class TestRenderCodeRequest(unittest.TestCase):
    """Test the render-code API logic (without starting a server)."""

    TWO_SUM_CORRECT = """class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []
"""

    TWO_SUM_BUG = """class Solution:
    def twoSum(self, nums, target):
        return [0, 0]
"""

    TWO_SUM_IMPORT = """import os
class Solution:
    def twoSum(self, nums, target):
        return [0, 1]
"""

    TWO_SUM_SYNTAX = """class Solution
    def twoSum(self, nums, target):
        return [0, 1]
"""

    def test_correct_code_returns_ok_true(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        self.assertTrue(result["ok"], f"Expected ok=true, got: {result.get('error', '')}")

    def test_correct_code_passed_true(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        self.assertTrue(result["ok"])
        rt = result.get("runtime", {})
        self.assertTrue(rt.get("passed"), f"Expected passed=true, got runtime={rt}")

    def test_correct_code_has_actual(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        rt = result.get("runtime", {})
        self.assertEqual(rt.get("actual"), [0, 1])

    def test_correct_code_has_expected(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        rt = result.get("runtime", {})
        self.assertEqual(rt.get("expected"), [0, 1])

    def test_correct_code_returns_html(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        self.assertIn("html", result)
        self.assertIsInstance(result["html"], str)
        self.assertGreater(len(result["html"]), 500)

    def test_bug_code_ok_true_but_passed_false(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_BUG,
        })
        self.assertTrue(result["ok"])
        rt = result.get("runtime", {})
        self.assertFalse(rt.get("passed"), f"Bug code should fail, got: {rt}")

    def test_bug_code_still_returns_html(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_BUG,
        })
        self.assertIn("html", result)
        self.assertIsInstance(result["html"], str)

    def test_disallowed_import_rejected(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_IMPORT,
        })
        self.assertFalse(result["ok"])
        self.assertIn("os", result.get("error", ""))

    def test_syntax_error_handled(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_SYNTAX,
        })
        self.assertFalse(result["ok"])

    def test_empty_code_returns_error(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": "",
        })
        self.assertFalse(result["ok"])

    def test_unknown_problem_returns_error(self):
        result = render_code_request({
            "problem_id": "nonexistent_99999",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        self.assertFalse(result["ok"])
        self.assertIn("not found", result.get("error", "").lower())

    def test_html_self_contained_no_cdn(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        html_str = result.get("html", "")
        self.assertNotIn("http://", html_str)
        self.assertNotIn("https://", html_str)
        self.assertNotIn("cdn.", html_str.lower())

    def test_html_contains_passed_status(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        self.assertIn("PASSED", result.get("html", ""))

    def test_html_contains_actual_value(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        self.assertIn("[0, 1]", result.get("html", ""))

    def test_case_1_different_input(self):
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 1,
            "code": self.TWO_SUM_CORRECT,
        })
        rt = result.get("runtime", {})
        self.assertTrue(rt.get("passed"), f"Case 1 should pass, got: {rt}")
        self.assertEqual(rt.get("actual"), [1, 2])

    def test_no_temp_files_left_in_problems(self):
        """Ensure user code is NOT written into the problems/ directory."""
        from pv.server import _project_root
        problems_dir = _project_root() / "problems"
        before = set(os.listdir(str(problems_dir)))
        render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": self.TWO_SUM_CORRECT,
        })
        after = set(os.listdir(str(problems_dir)))
        new_items = after - before
        self.assertEqual(len(new_items), 0,
                         f"New items in problems dir: {new_items}")


class TestRunnerTrustLayer(unittest.TestCase):
    """Test runner validation summaries without starting a server."""

    TWO_SUM_CORRECT = TestRenderCodeRequest.TWO_SUM_CORRECT
    TWO_SUM_BUG = TestRenderCodeRequest.TWO_SUM_BUG

    def test_all_fixed_cases_summary_passes(self):
        result = run_all_fixed_cases_request({
            "problem_id": "0001_two_sum",
            "code": self.TWO_SUM_CORRECT,
        })

        self.assertTrue(result["ok"], result.get("error"))
        summary = result["summary"]
        self.assertTrue(summary["passed"])
        self.assertEqual(summary["passed_count"], 4)
        self.assertEqual(summary["total_count"], 4)
        self.assertIsNone(summary["first_failure"])

    def test_all_fixed_cases_reports_first_failure(self):
        result = run_all_fixed_cases_request({
            "problem_id": "0001_two_sum",
            "code": self.TWO_SUM_BUG,
        })

        self.assertTrue(result["ok"], result.get("error"))
        summary = result["summary"]
        self.assertFalse(summary["passed"])
        failure = summary["first_failure"]
        self.assertIsNotNone(failure)
        self.assertEqual(failure["source"], "fixed")
        self.assertIn("input", failure)
        self.assertIn("expected", failure)
        self.assertIn("actual", failure)
        self.assertIn("error", failure)

    def test_generated_checks_summary_passes(self):
        result = run_generated_checks_request({
            "problem_id": "0001_two_sum",
            "code": self.TWO_SUM_CORRECT,
            "generated": 20,
            "seed": 0,
        })

        self.assertTrue(result["ok"], result.get("error"))
        summary = result["summary"]
        self.assertTrue(summary["passed"])
        self.assertEqual(summary["fixed"]["passed"], 4)
        self.assertEqual(summary["fixed"]["total"], 4)
        self.assertEqual(summary["generated"]["passed"], 20)
        self.assertEqual(summary["generated"]["total"], 20)
        self.assertIsNone(summary["first_failure"])

    def test_generated_checks_reports_first_failure(self):
        result = run_generated_checks_request({
            "problem_id": "0001_two_sum",
            "code": self.TWO_SUM_BUG,
            "generated": 20,
            "seed": 0,
        })

        self.assertTrue(result["ok"], result.get("error"))
        summary = result["summary"]
        self.assertFalse(summary["passed"])
        failure = summary["first_failure"]
        self.assertIsNotNone(failure)
        self.assertIn(failure["source"], {"fixed", "generated"})
        self.assertIn("input", failure)
        self.assertIn("expected", failure)
        self.assertIn("actual", failure)
        self.assertIn("message", failure)


class TestMainPageHTML(unittest.TestCase):
    """Validate the main page HTML."""

    def test_html_is_non_empty(self):
        self.assertIsInstance(_MAIN_PAGE_HTML, str)
        self.assertGreater(len(_MAIN_PAGE_HTML), 500)

    def test_no_cdn_links(self):
        self.assertNotIn("http://", _MAIN_PAGE_HTML)
        self.assertNotIn("https://", _MAIN_PAGE_HTML)
        self.assertNotIn("cdn.", _MAIN_PAGE_HTML.lower())

    def test_contains_doctype(self):
        self.assertIn("<!DOCTYPE html>", _MAIN_PAGE_HTML)

    def test_contains_code_input(self):
        self.assertIn("code-input", _MAIN_PAGE_HTML)

    def test_contains_run_button(self):
        self.assertIn("run-btn", _MAIN_PAGE_HTML)

    def test_contains_viewer_frame(self):
        self.assertIn("viewer-frame", _MAIN_PAGE_HTML)

    def test_does_not_claim_realtime_streaming(self):
        self.assertNotIn("实时", _MAIN_PAGE_HTML)
        self.assertNotIn("streaming", _MAIN_PAGE_HTML.lower())

    def test_page_has_clear_result_helper(self):
        self.assertIn("function clearResult(reason)", _MAIN_PAGE_HTML)
        self.assertIn("frame.srcdoc = ''", _MAIN_PAGE_HTML)
        self.assertIn("Selection changed. Click Run to execute this case.", _MAIN_PAGE_HTML)

    def test_problem_change_clears_stale_result(self):
        self.assertIn("async function onProblemChange() {\n  clearResult('selection')", _MAIN_PAGE_HTML)

    def test_case_change_clears_stale_result(self):
        self.assertIn("document.getElementById('case-select').onchange = function() {\n  clearResult('selection')", _MAIN_PAGE_HTML)

    def test_run_code_reads_problem_and_case_from_dom(self):
        self.assertIn("var runProblemId = document.getElementById('problem-select').value", _MAIN_PAGE_HTML)
        self.assertIn("var runCaseIndex = parseInt(document.getElementById('case-select').value, 10)", _MAIN_PAGE_HTML)
        self.assertIn("problem_id: runProblemId", _MAIN_PAGE_HTML)
        self.assertIn("case_index: runCaseIndex", _MAIN_PAGE_HTML)

    def test_run_code_has_stale_response_guard(self):
        self.assertIn("var runRequestSeq = 0", _MAIN_PAGE_HTML)
        self.assertIn("var requestSeq = ++runRequestSeq", _MAIN_PAGE_HTML)
        self.assertIn("if (requestSeq !== runRequestSeq ||", _MAIN_PAGE_HTML)
        self.assertIn("return;", _MAIN_PAGE_HTML)

    def test_contains_runner_trust_buttons(self):
        self.assertIn("Run All Fixed Cases", _MAIN_PAGE_HTML)
        self.assertIn("Run Generated Checks", _MAIN_PAGE_HTML)
        self.assertIn("run-all-btn", _MAIN_PAGE_HTML)
        self.assertIn("run-generated-btn", _MAIN_PAGE_HTML)

    def test_contains_case_preview_area(self):
        self.assertIn("case-preview", _MAIN_PAGE_HTML)
        self.assertIn("case-preview-name", _MAIN_PAGE_HTML)
        self.assertIn("case-preview-input", _MAIN_PAGE_HTML)
        self.assertIn("case-preview-expected", _MAIN_PAGE_HTML)
        self.assertIn("case-preview-notes", _MAIN_PAGE_HTML)

    def test_selection_change_refreshes_case_preview(self):
        self.assertIn("updateCasePreview()", _MAIN_PAGE_HTML)
        self.assertIn("detail.cases = detail.cases || []", _MAIN_PAGE_HTML)
        self.assertIn("document.getElementById('case-select').onchange = function() {\n  clearResult('selection')\n  updateCasePreview()", _MAIN_PAGE_HTML)

    def test_contains_validation_summary_area(self):
        self.assertIn("validation-summary", _MAIN_PAGE_HTML)
        self.assertIn("function renderValidationSummary", _MAIN_PAGE_HTML)

    def test_execution_viewer_has_stable_shell(self):
        self.assertIn('class="viewer-shell"', _MAIN_PAGE_HTML)
        self.assertIn(".right{flex:1;display:flex;flex-direction:column;overflow:hidden;min-height:0;min-width:0}", _MAIN_PAGE_HTML)
        self.assertIn(".viewer-shell{flex:1 1 auto;min-height:0;display:flex;overflow:hidden}", _MAIN_PAGE_HTML)
        self.assertIn("#viewer-frame{flex:1 1 auto;border:none;width:100%;height:100%;min-height:0;display:block}", _MAIN_PAGE_HTML)

    def test_single_run_restores_execution_viewer(self):
        self.assertIn("frame.style.display = 'block';", _MAIN_PAGE_HTML)
        self.assertIn("empty.style.display = 'none';", _MAIN_PAGE_HTML)
        self.assertIn("frame.srcdoc = data.html;", _MAIN_PAGE_HTML)

    def test_batch_validation_is_summary_only(self):
        self.assertIn("Validation summary is shown in the left panel.", _MAIN_PAGE_HTML)
        self.assertIn("frame.style.display = 'none';", _MAIN_PAGE_HTML)
        self.assertIn("frame.srcdoc = '';", _MAIN_PAGE_HTML)


class TestTimeoutConfig(unittest.TestCase):
    """Verify timeout and request size constants exist."""

    def test_timeout_is_positive(self):
        self.assertGreater(EXECUTION_TIMEOUT, 0)

    def test_timeout_reasonable(self):
        self.assertLessEqual(EXECUTION_TIMEOUT, 60)

    def test_body_limit_is_positive(self):
        self.assertGreater(MAX_BODY_BYTES, 0)

    def test_body_limit_is_reasonable(self):
        self.assertLessEqual(MAX_BODY_BYTES, 1024 * 1024)


class TestServerImplementation(unittest.TestCase):
    """Implementation guardrails for the local server."""

    def test_threading_http_server_imported(self):
        self.assertEqual(ThreadingHTTPServer.__name__, "ThreadingHTTPServer")

    def test_server_source_uses_threading_http_server(self):
        source = Path(__file__).resolve().parents[1] / "src" / "pv" / "server.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn("ThreadingHTTPServer((host, port), handler)", text)
        self.assertNotIn("server = HTTPServer(", text)

    def test_server_source_has_body_limit_check(self):
        source = Path(__file__).resolve().parents[1] / "src" / "pv" / "server.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn("MAX_BODY_BYTES", text)
        self.assertIn("RequestBodyTooLarge", text)


class TestRenderCodeErrors(unittest.TestCase):
    """Additional error path tests."""

    def test_code_that_throws_exception(self):
        code = """class Solution:
    def twoSum(self, nums, target):
        raise RuntimeError("boom")
"""
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": code,
        })
        self.assertTrue(result["ok"])
        rt = result.get("runtime", {})
        self.assertFalse(rt.get("passed", True))
        self.assertIsNotNone(rt.get("error"))

    def test_code_with_print_no_return(self):
        code = """class Solution:
    def twoSum(self, nums, target):
        print("hello")
"""
        result = render_code_request({
            "problem_id": "0001_two_sum",
            "case_index": 0,
            "code": code,
        })
        self.assertTrue(result["ok"])
        rt = result.get("runtime", {})
        self.assertFalse(rt.get("passed", True))


class TestCLIServe(unittest.TestCase):
    """Test CLI serve --help exists and doesn't crash."""

    def test_serve_help(self):
        import subprocess
        import sys
        project_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "pv", "serve", "--help"],
            capture_output=True, text=True,
            cwd=str(project_root),
            env={**os.environ, "PYTHONPATH": str(project_root / "src")},
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn("--host", result.stdout)
        self.assertIn("--port", result.stdout)


if __name__ == "__main__":
    unittest.main()
