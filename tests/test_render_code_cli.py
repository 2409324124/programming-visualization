import unittest
import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


TWO_SUM_DIR = str(Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum")


class TestRenderCodeHtml(unittest.TestCase):
    def setUp(self):
        self.sol_path = os.path.join(TWO_SUM_DIR, "solution.py")
    
    def test_html_contains_code_text(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("class Solution", html)
    
    def test_html_contains_lineno_data(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("data-ln=", html)
    
    def test_html_contains_locals_panel(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("locals-display", html)
    
    def test_html_contains_passed_status(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("PASSED", html)
    
    def test_html_contains_actual_and_expected(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("[0, 1]", html)
    
    def test_html_no_external_links(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)
    
    def test_html_dark_theme(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("#1e1e1e", html, "Should use dark theme background")
    
    def test_cli_writes_file(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
            html = render_learner_to_html(runtime)
            out = os.path.join(tmpdir, "out.html")
            with open(out, 'w', encoding="utf-8") as f:
                f.write(html)
            self.assertTrue(os.path.isfile(out))
            self.assertGreater(os.path.getsize(out), 500)

    def test_html_contains_return_section(self):
        """HTML should have return value section for return events."""
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("return-section", html)
        self.assertIn("Return Value", html)

    def test_html_contains_completed_banner(self):
        """HTML should show Execution completed banner."""
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("Execution completed", html)

    def test_html_no_class_definition_locals(self):
        """HTML should NOT contain module/class-level trace events.
        The line_trace JSON embedded in the page should not start with
        function='<module>' or step 1 at line 1 of the class definition.
        """
        from pv.learner_runtime import get_learner_runtime
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        # Check that line_trace events in runtime are all inside twoSum
        for ev in runtime.get("line_trace", []):
            self.assertNotEqual(ev.get("function"), "<module>",
                "Should not contain module-level trace events")

    def test_html_contains_return_badge(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("RETURNED HERE", html)

    def test_html_contains_hl_return_class(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("hl-return", html)
        self.assertIn("hl-line", html)

    def test_html_contains_not_executed(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("not executed", html)

    def test_html_contains_return_text(self):
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("Function returned here", html)

    def test_play_restarts_after_completion(self):
        """Clicking Play at the final step should replay from the beginning."""
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
        runtime = get_learner_runtime(TWO_SUM_DIR, self.sol_path, 0)
        html = render_learner_to_html(runtime)
        self.assertIn("if (currentStep >= totalSteps)", html)
        self.assertIn("currentStep = 0", html)
        self.assertIn("highlightStep(currentStep)", html)


if __name__ == "__main__":
    unittest.main()
