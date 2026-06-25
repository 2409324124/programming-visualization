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


if __name__ == "__main__":
    unittest.main()
