"""Tests for render-visual CLI command (integration tests).

Requirements covered
--------------------
1. render-visual truly runs Two Sum case 0
2. runtime context contains input/expected/actual/passed/trace
3. actual [0, 1] appears in generated HTML
4. expected [0, 1] appears in generated HTML
5. passed true appears in generated HTML
6. lesson with wrong nums[0]=999 → BindingError (binder reports error)
7. lesson with wrong variable value → BindingError
8. lesson with bad trace_ref → BindingError
9. validation_only solution → no semantic trace (empty trace list)
10. old 216 tests still pass (verified by running all tests together)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.visual_runtime import get_runtime_context
from pv.visual_binder import bind_lesson, BindingError
from pv.visual_compiler import compile_visual
from pv.render_story_html import render_visual_to_html, _build_runtime_banner

PROBLEM_DIR = str(
    Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum"
)
LESSON_PATH = str(
    Path(__file__).resolve().parent.parent
    / "problems" / "0001_two_sum" / "lesson.story.json"
)
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


def _full_pipeline(lesson_override: dict | None = None, case_index: int = 0) -> str:
    """Run the full render-visual pipeline and return the generated HTML."""
    rt_ctx = get_runtime_context(PROBLEM_DIR, case_index)
    lesson = lesson_override
    if lesson is None:
        with open(LESSON_PATH, encoding="utf-8") as f:
            lesson = json.load(f)
    bound  = bind_lesson(lesson, rt_ctx)
    frames = compile_visual(bound)
    return render_visual_to_html(frames, title=lesson.get("title", "Test"))


class TestRenderVisualPipeline(unittest.TestCase):
    """Integration tests for the full render-visual pipeline."""

    @classmethod
    def setUpClass(cls):
        """Run the pipeline once and cache the HTML output."""
        cls.html = _full_pipeline()
        cls.rt_ctx = get_runtime_context(PROBLEM_DIR, 0)

    # ── Requirement 1: truly runs Two Sum case 0 ─────────────────────

    def test_runtime_was_executed(self):
        """Requirement 1: render-visual really runs the harness, not just reads lesson."""
        self.assertGreater(len(self.rt_ctx["trace"]), 0,
                           "Harness must produce trace events")
        self.assertEqual(self.rt_ctx["input"]["nums"], [2, 7, 11, 15])
        self.assertEqual(self.rt_ctx["input"]["target"], 9)

    # ── Requirement 2: runtime context structure ──────────────────────

    def test_runtime_context_has_all_required_keys(self):
        """Requirement 2: runtime_context has input/expected/actual/passed/trace."""
        for key in ("input", "expected", "actual", "passed", "trace"):
            self.assertIn(key, self.rt_ctx)

    # ── Requirement 3: actual [0, 1] in HTML ─────────────────────────

    def test_actual_0_1_in_html(self):
        """Requirement 3: actual [0, 1] appears in the HTML."""
        self.assertIn("Actual: [0, 1]", self.html,
                      "HTML must show actual result from runtime")

    # ── Requirement 4: expected [0, 1] in HTML ───────────────────────

    def test_expected_0_1_in_html(self):
        """Requirement 4: expected [0, 1] appears in the HTML."""
        self.assertIn("Expected: [0, 1]", self.html,
                      "HTML must show expected result")

    # ── Requirement 5: passed true in HTML ───────────────────────────

    def test_passed_shown_in_html(self):
        """Requirement 5: passed status appears in HTML."""
        self.assertIn("Passed", self.html,
                      "HTML must display Passed status")

    def test_runtime_bound_label_in_html(self):
        """HTML must contain 'Runtime-bound visualization' label."""
        self.assertIn("Runtime-bound visualization", self.html)

    def test_case_0_shown_in_html(self):
        """HTML banner must show Case 0."""
        self.assertIn("Case 0", self.html)

    # ── Requirement 6: wrong nums → BindingError ─────────────────────

    def test_binding_error_on_wrong_nums_value(self):
        """Requirement 6: lesson with nums[0]=999 → BindingError."""
        rt_ctx = get_runtime_context(PROBLEM_DIR, 0)
        with open(LESSON_PATH) as f:
            lesson = json.load(f)
        for obj in lesson["objects"]:
            if obj["id"] == "input:nums":
                obj["value"] = [999, 7, 11, 15]
        with self.assertRaises(BindingError) as ctx:
            bind_lesson(lesson, rt_ctx)
        self.assertIn("999", str(ctx.exception))

    # ── Requirement 7: wrong variable value → BindingError ───────────

    def test_binding_error_on_wrong_variable_value(self):
        """Requirement 7: variable with _expected_value=7 but value=999 → BindingError."""
        rt_ctx = get_runtime_context(PROBLEM_DIR, 0)
        with open(LESSON_PATH) as f:
            lesson = json.load(f)
        lesson["objects"].append({
            "id": "var:need",
            "type": "variable",
            "value": 999,
            "_expected_value": 7,
        })
        with self.assertRaises(BindingError):
            bind_lesson(lesson, rt_ctx)

    # ── Requirement 8: bad trace_ref → BindingError ──────────────────

    def test_binding_error_on_bad_trace_ref(self):
        """Requirement 8: trace_ref for non-existent event type → BindingError."""
        rt_ctx = get_runtime_context(PROBLEM_DIR, 0)
        with open(LESSON_PATH) as f:
            lesson = json.load(f)
        lesson["frames"][0]["actions"].append({
            "action": "appear",
            "object": "input:nums",
            "trace_ref": {"event_type": "totally_fake_event_zzz"},
        })
        with self.assertRaises(BindingError) as ctx:
            bind_lesson(lesson, rt_ctx)
        self.assertIn("totally_fake_event_zzz", str(ctx.exception))

    # ── Requirement 9: validation_only → no semantic trace ───────────

    def test_validation_only_has_empty_trace(self):
        """Requirement 9: validation_only solution must not generate semantic trace."""
        ctx = get_runtime_context(PROBLEM_DIR, 0, solution_mode="validation_only")
        self.assertEqual(ctx["trace"], [],
                         "validation_only mode must not produce trace events")
        self.assertEqual(ctx["solution_mode"], "validation_only")

    def test_validation_only_still_passes(self):
        """validation_only may still pass/fail — just without trace."""
        ctx = get_runtime_context(PROBLEM_DIR, 0, solution_mode="validation_only")
        self.assertEqual(sorted(ctx["actual"]), [0, 1])
        self.assertTrue(ctx["passed"])

    # ── HTML structure ────────────────────────────────────────────────

    def test_html_is_valid_document(self):
        self.assertIn("<!DOCTYPE html>", self.html)
        self.assertIn("</html>", self.html)

    def test_html_has_frames_data(self):
        self.assertIn("FRAMES", self.html)

    def test_html_no_external_cdn_links(self):
        self.assertNotIn("<link rel", self.html)
        self.assertNotIn('src="http', self.html)

    def test_html_has_runtime_banner_css(self):
        self.assertIn("runtime-banner", self.html)

    # ── Frame metadata ────────────────────────────────────────────────

    def test_compiled_frames_have_runtime_meta(self):
        rt_ctx = get_runtime_context(PROBLEM_DIR, 0)
        with open(LESSON_PATH) as f:
            lesson = json.load(f)
        bound  = bind_lesson(lesson, rt_ctx)
        frames = compile_visual(bound)
        self.assertGreater(len(frames), 0)
        for f in frames:
            self.assertIn("runtime_meta", f, f"Frame missing runtime_meta: {f.get('frame_id')}")
            rt = f["runtime_meta"]
            self.assertTrue(rt.get("bound"))
            self.assertEqual(sorted(rt["actual"]), [0, 1])
            self.assertEqual(rt["expected"], [0, 1])
            self.assertTrue(rt["passed"])

    # ── Failure case: banner turns red ───────────────────────────────

    def test_banner_shows_failed_state_when_actual_wrong(self):
        """If actual != expected, banner should show rb-failed class."""
        rt_meta = {
            "bound":      True,
            "actual":     [1, 0],
            "expected":   [0, 1],
            "passed":     False,
            "case_index": 0,
            "case_name":  "test",
            "error":      None,
        }
        banner = _build_runtime_banner(rt_meta)
        self.assertIn("rb-failed", banner)
        self.assertIn("Failed", banner)

    def test_banner_shows_passed_state_when_actual_correct(self):
        rt_meta = {
            "bound":      True,
            "actual":     [0, 1],
            "expected":   [0, 1],
            "passed":     True,
            "case_index": 0,
            "case_name":  "test",
            "error":      None,
        }
        banner = _build_runtime_banner(rt_meta)
        self.assertIn("rb-passed", banner)
        self.assertIn("Passed", banner)

    def test_banner_shows_error_state_when_error_present(self):
        rt_meta = {
            "bound":      False,
            "actual":     None,
            "expected":   [0, 1],
            "passed":     False,
            "case_index": 0,
            "case_name":  "",
            "error":      "TypeError: something went wrong",
        }
        banner = _build_runtime_banner(rt_meta)
        self.assertIn("rb-error", banner)

    # ── CLI subprocess integration ────────────────────────────────────

    def test_cli_render_visual_produces_html_file(self):
        """End-to-end: cli render-visual writes a valid HTML file."""
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "out.html")
            result = subprocess.run(
                [
                    sys.executable, "-m", "pv",
                    "render-visual", PROBLEM_DIR,
                    "--case-index", "0",
                    "--lesson", LESSON_PATH,
                    "--output", out_path,
                ],
                capture_output=True, text=True,
                cwd=PROJECT_ROOT,
                env={**os.environ, "PYTHONPATH": os.path.join(PROJECT_ROOT, "src")},
            )
            self.assertEqual(result.returncode, 0,
                             f"CLI exited {result.returncode}: {result.stderr}")
            self.assertTrue(os.path.exists(out_path))
            with open(out_path, encoding="utf-8") as f:
                html = f.read()
            self.assertIn("Runtime-bound visualization", html)
            self.assertIn("Actual: [0, 1]", html)
            self.assertIn("Expected: [0, 1]", html)
            self.assertIn("Passed", html)

    def test_cli_render_visual_outputs_step_log(self):
        """CLI should print the step log (run complete / bind complete)."""
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "out.html")
            result = subprocess.run(
                [
                    sys.executable, "-m", "pv",
                    "render-visual", PROBLEM_DIR,
                    "--case-index", "0",
                    "--lesson", LESSON_PATH,
                    "--output", out_path,
                ],
                capture_output=True, text=True,
                cwd=PROJECT_ROOT,
                env={**os.environ, "PYTHONPATH": os.path.join(PROJECT_ROOT, "src")},
            )
            combined = result.stdout + result.stderr
            self.assertIn("PASSED", combined)
            self.assertIn("一致", combined)  # "绑定完成: lesson 与 runtime 一致"

    def test_cli_render_lesson_still_works(self):
        """Backward compat: render-lesson (authored-only) must still function."""
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "lesson_out.html")
            result = subprocess.run(
                [
                    sys.executable, "-m", "pv",
                    "render-lesson", LESSON_PATH,
                    "--output", out_path,
                ],
                capture_output=True, text=True,
                cwd=PROJECT_ROOT,
                env={**os.environ, "PYTHONPATH": os.path.join(PROJECT_ROOT, "src")},
            )
            self.assertEqual(result.returncode, 0,
                             f"render-lesson failed: {result.stderr}")
            self.assertTrue(os.path.exists(out_path))


if __name__ == "__main__":
    unittest.main()
