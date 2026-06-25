import unittest
import sys
import json
import tempfile
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


TWO_SUM_TRACE_PATH = str(Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum" / "trace.sample.json")


class TestRenderStoryHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pv.storyboard import build_storyboard
        with open(TWO_SUM_TRACE_PATH) as f:
            trace = json.load(f)
        cls.frames = build_storyboard(trace)

    def test_output_is_valid_html(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames, "Test")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("</html>", html)

    def test_contains_controls(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("btn-prev", html)
        self.assertIn("btn-play", html)
        self.assertIn("btn-next", html)

    def test_contains_frames_data(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("FRAMES", html)

    def test_contains_stage(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("stage", html)

    def test_contains_caption(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("caption", html)

    def test_contains_story_object_css(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("st-obj", html)

    def test_no_cdn_links(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)

    def test_cli_writes_file(self):
        from pv.render_story_html import render_story_to_html
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "out.html")
            html = render_story_to_html(self.frames)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 500)


if __name__ == "__main__":
    unittest.main()
