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


if __name__ == "__main__":
    unittest.main()
