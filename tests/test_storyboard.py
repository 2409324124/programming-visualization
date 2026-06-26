import unittest
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.storyboard import build_storyboard


TWO_SUM_TRACE_PATH = str(Path(__file__).resolve().parent.parent / "problems" / "0001_two_sum" / "trace.sample.json")


class TestStoryboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TWO_SUM_TRACE_PATH) as f:
            cls.trace = json.load(f)

    def test_build_non_empty_frames(self):
        frames = build_storyboard(self.trace)
        self.assertGreater(len(frames), 0)

    def test_frames_contain_array_box(self):
        frames = build_storyboard(self.trace)
        all_objects = [o for f in frames for o in f.get("objects", [])]
        types = {o["type"] for o in all_objects}
        self.assertIn("array_box", types)

    def test_frames_contain_complement_box(self):
        frames = build_storyboard(self.trace)
        all_objects = [o for f in frames for o in f.get("objects", [])]
        types = {o["type"] for o in all_objects}
        self.assertIn("complement_box", types)

    def test_frames_contain_map_entry(self):
        frames = build_storyboard(self.trace)
        all_objects = [o for f in frames for o in f.get("objects", [])]
        types = {o["type"] for o in all_objects}
        self.assertIn("map_entry", types)

    def test_frames_contain_answer_box(self):
        frames = build_storyboard(self.trace)
        all_objects = [o for f in frames for o in f.get("objects", [])]
        types = {o["type"] for o in all_objects}
        self.assertIn("answer_box", types)

    def test_object_ids_stable(self):
        frames = build_storyboard(self.trace)
        all_ids = [o["id"] for f in frames for o in f.get("objects", [])]
        self.assertIn("arr:0", all_ids)
        self.assertIn("arr:1", all_ids)

    def test_unsupported_problem_raises(self):
        other = dict(self.trace)
        other["problem"] = dict(other["problem"])
        other["problem"]["problem_id"] = "9999_unknown"
        with self.assertRaises((ValueError, NotImplementedError)):
            build_storyboard(other)

    def test_map_entry_has_stable_id_across_frames(self):
        """map:2 should appear in multiple frames with same id (for keyed DOM animation)."""
        frames = build_storyboard(self.trace)
        map_ids = set()
        for f in frames:
            for o in f.get("objects", []):
                if o.get("id", "").startswith("map:"):
                    map_ids.add(o["id"])
        self.assertIn("map:2", map_ids)

    def test_map_entry_position_changes_for_motion(self):
        """map:2 should be at different positions in different frames (enables translation animation)."""
        frames = build_storyboard(self.trace)
        positions = []
        for f in frames:
            for o in f.get("objects", []):
                if o.get("id") == "map:2":
                    positions.append((o.get("x"), o.get("y")))
        # Should have at least 2 different positions
        self.assertGreaterEqual(len(set(positions)), 2,
            "map:2 should move between frames for translation animation")

    def test_array_boxes_are_spaced_apart(self):
        """Array boxes should have at least 90px gap between them."""
        frames = build_storyboard(self.trace)
        f = frames[0]
        arr_boxes = sorted([o for o in f["objects"] if o["type"] == "array_box"], key=lambda o: o["x"])
        self.assertGreaterEqual(len(arr_boxes), 4)
        for i in range(len(arr_boxes) - 1):
            gap = arr_boxes[i+1]["x"] - arr_boxes[i]["x"]
            self.assertGreaterEqual(gap, 90, f"Gap between arr boxes should be >= 90, got {gap}")

    def test_answer_box_not_overlapping_array(self):
        """Answer box should be below array boxes on y-axis."""
        frames = build_storyboard(self.trace)
        last_frame = frames[-1]
        arr_boxes = [o for o in last_frame["objects"] if o["type"] == "array_box"]
        answer_boxes = [o for o in last_frame["objects"] if o["type"] == "answer_box"]
        if answer_boxes and arr_boxes:
            self.assertGreater(answer_boxes[0]["y"], arr_boxes[0]["y"] + 30,
                "Answer box should be below array boxes")

    def test_frame_count(self):
        frames = build_storyboard(self.trace)
        self.assertGreaterEqual(len(frames), 7)

    def test_frame_count_min_10(self):
        frames = build_storyboard(self.trace)
        self.assertGreaterEqual(len(frames), 10, "Should have at least 10 frames with concept cards")

    def test_contains_definition_card(self):
        frames = build_storyboard(self.trace)
        all_types = {o["type"] for f in frames for o in f.get("objects", [])}
        self.assertIn("definition_card", all_types)

    def test_contains_rule_card(self):
        frames = build_storyboard(self.trace)
        all_types = {o["type"] for f in frames for o in f.get("objects", [])}
        self.assertIn("rule_card", all_types)

    def test_contains_operation_card(self):
        frames = build_storyboard(self.trace)
        all_types = {o["type"] for f in frames for o in f.get("objects", [])}
        self.assertIn("operation_card", all_types)

    def test_contains_note_about_index(self):
        """A note should mention that the answer returns indices, not values."""
        frames = build_storyboard(self.trace)
        all_texts = [o.get("text", "") for f in frames for o in f.get("objects", [])]
        # Check for note mentioning "下标" or "index"
        found = any("index" in t.lower() or "下标" in t for t in all_texts)
        self.assertTrue(found, "Should have a note about returning indices")

    def test_contains_need_rule(self):
        """A rule card should mention need = target - current."""
        frames = build_storyboard(self.trace)
        found = any("need" in o.get("text", "").lower() and "current" in o.get("text", "").lower()
                   for f in frames for o in f.get("objects", []))
        self.assertTrue(found, "Should have a rule about need = target - current")

    def test_contains_seen_rule(self):
        """A rule card should mention seen[number] = index."""
        frames = build_storyboard(self.trace)
        found = any("seen[" in o.get("text", "") and "index" in o.get("text", "").lower()
                   for f in frames for o in f.get("objects", []))
        self.assertTrue(found, "Should have a rule about seen[number] = index")

    def test_map_entry_still_has_motion(self):
        """map:2 should still have different positions (animation preserved)."""
        frames = build_storyboard(self.trace)
        positions = []
        for f in frames:
            for o in f.get("objects", []):
                if o.get("id") == "map:2":
                    positions.append((o.get("x"), o.get("y")))
        self.assertGreaterEqual(len(set(positions)), 2,
            "map:2 should move between frames")

    def test_match_frame_contains_correct_complement_lookup(self):
        """Success frame should look up seen[complement], NOT seen[current value]."""
        frames = build_storyboard(self.trace)
        all_texts = [o.get("text", "") for f in frames for o in f.get("objects", [])]
        self.assertTrue(any("查找 seen[2]" in t for t in all_texts),
            "Success frame should contain '查找 seen[2]' (complement), not 'seen[7]'")

    def test_match_frame_excludes_wrong_lookup(self):
        """Success/match frame should NOT contain lookup by current value (7).
        But the earlier fail frame (Frame 6) correctly shows '查找 seen[7]' failing.
        """
        frames = build_storyboard(self.trace)
        # Check only the success frame (frame_id = "check_map_success")
        for f in frames:
            if f.get("frame_id") == "check_map_success":
                for o in f.get("objects", []):
                    txt = o.get("text", "")
                    self.assertNotIn("查找 seen[7]", txt,
                        f"Success frame should not contain '查找 seen[7]' — got: {txt}")

    def test_definition_card_has_title_and_text(self):
        """definition_card objects should have both 'title' and 'text' fields."""
        frames = build_storyboard(self.trace)
        for f in frames:
            for o in f.get("objects", []):
                if o["type"] == "definition_card":
                    self.assertIn("title", o, f"definition_card missing title: {o.get('id')}")
                    self.assertIn("text", o, f"definition_card missing text: {o.get('id')}")

    def test_hashmap_definition_contains_body(self):
        """Hash map definition card text should contain key Chinese terms."""
        frames = build_storyboard(self.trace)
        for f in frames:
            for o in f.get("objects", []):
                if o["type"] == "definition_card" and "哈希" in o.get("title", ""):
                    body = o.get("text", "")
                    self.assertIn("保存", body)
                    self.assertIn("数字", body)
                    self.assertIn("下标", body)
                    return
        self.fail("No hash map definition card found with expected body text")


if __name__ == "__main__":
    unittest.main()
