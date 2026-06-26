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
        cleaned = html.replace("http://www.w3.org/2000/svg", "")
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("http://", cleaned)

    def test_cli_writes_file(self):
        from pv.render_story_html import render_story_to_html
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "out.html")
            html = render_story_to_html(self.frames)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 500)

    def test_no_mapzone_innerhtml_clearing(self):
        """The JS should NOT use mapZone.innerHTML = '' (duplicate rendering removed)."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        # Should not contain old map-zone clearing pattern
        self.assertNotIn("mapZone.innerHTML", html)

    def test_uses_keyed_object_nodes(self):
        """JS should use objectNodes dict for keyed DOM reuse (not innerHTML = '' on objects)."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("objectNodes", html,
            "Should use keyed DOM objectNodes for animation")

    def test_uses_transform_translate(self):
        """Object positioning should use JS transform assignment for CSS animation."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn(".transform = 'translate(", html,
            "Should use JS transform assignment for smooth animation")

    def test_has_transform_transition(self):
        """CSS should include transition on transform property."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("transition", html)
        self.assertIn("transform", html)

    def test_no_objdiv_innerhtml_clear(self):
        """JS should NOT use objDiv.innerHTML = '' (destroys transitions)."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertNotIn("objDiv.innerHTML", html,
            "Should not clear innerHTML (breaks CSS transitions)")

    def test_no_http_links(self):
        """HTML must be offline — no CDN or external resource references.
        SVG namespace (w3.org) is allowed."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        # Remove SVG namespace (required for inline SVG, not a CDN)
        cleaned = html.replace("http://www.w3.org/2000/svg", "")
        self.assertNotIn("http://", cleaned)
        self.assertNotIn("https://", cleaned)

    def test_contains_definition_card_css(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("definition_card", html,
            "CSS should include definition_card style")

    def test_contains_rule_card_css(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("rule_card", html,
            "CSS should include rule_card style")

    def test_contains_operation_card_css(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("operation_card", html,
            "CSS should include operation_card style")

    def test_contains_note_card_css(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("note_card", html,
            "CSS should include note_card style")

    def test_still_uses_object_nodes(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("objectNodes", html)

    def test_still_no_objdiv_innerhtml(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertNotIn("objDiv.innerHTML", html)

    def test_still_no_external_links(self):
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        cleaned = html.replace("http://www.w3.org/2000/svg", "")
        self.assertNotIn("http://", cleaned)
        self.assertNotIn("https://", cleaned)

    def test_data_title_uses_title_field(self):
        """JS should set data-title from o.title, not o.text alone."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        # The JS should reference o.title (or o.title || o.text)
        self.assertIn("o.title", html,
            "JS should use o.title for data-title")

    def test_has_pre_line_for_cards(self):
        """Card CSS should include white-space: pre-line for multi-line text."""
        from pv.render_story_html import render_story_to_html
        html = render_story_to_html(self.frames)
        self.assertIn("pre-line", html,
            "Card CSS should include white-space: pre-line")


if __name__ == "__main__":
    unittest.main()
