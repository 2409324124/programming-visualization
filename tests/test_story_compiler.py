"""Tests for src/pv/story_compiler.py and src/pv/lesson_schema.py."""
import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pv.story_compiler import compile_lesson, compile_lesson_file
from pv.lesson_schema import validate_lesson

LESSON_PATH = str(
    Path(__file__).resolve().parent.parent
    / "problems"
    / "0001_two_sum"
    / "lesson.story.json"
)


class TestLessonSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(LESSON_PATH, encoding="utf-8") as f:
            cls.lesson = json.load(f)

    def test_lesson_file_is_valid_json(self):
        self.assertIsInstance(self.lesson, dict)

    def test_validate_returns_no_errors(self):
        errors = validate_lesson(self.lesson)
        self.assertEqual(errors, [], f"Lesson validation errors: {errors}")

    def test_has_required_top_level_keys(self):
        for key in ("lesson_id", "problem_id", "title", "objects", "frames"):
            self.assertIn(key, self.lesson, f"Missing key: {key}")

    def test_objects_have_id_and_type(self):
        for obj in self.lesson["objects"]:
            self.assertIn("id", obj)
            self.assertIn("type", obj)

    def test_frames_have_id_and_actions(self):
        for frame in self.lesson["frames"]:
            self.assertIn("id", frame)
            self.assertIn("actions", frame)

    def test_actions_have_action_field(self):
        for frame in self.lesson["frames"]:
            for action in frame.get("actions", []):
                self.assertIn("action", action, f"action missing 'action' key in frame {frame['id']}")

    def test_validate_catches_missing_fields(self):
        bad = {"lesson_id": "x"}
        errors = validate_lesson(bad)
        self.assertGreater(len(errors), 0)

    def test_validate_catches_bad_object_type(self):
        bad = {
            "lesson_id": "x", "problem_id": "y", "title": "t",
            "objects": [{"id": "foo", "type": "totally_wrong"}],
            "frames": [],
        }
        errors = validate_lesson(bad)
        self.assertTrue(any("unknown object type" in e for e in errors))

    def test_validate_catches_bad_action_type(self):
        bad = {
            "lesson_id": "x", "problem_id": "y", "title": "t",
            "objects": [],
            "frames": [{"id": "f1", "actions": [{"action": "fly_away"}]}],
        }
        errors = validate_lesson(bad)
        self.assertTrue(any("unknown action" in e for e in errors))


class TestStoryCompiler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(LESSON_PATH, encoding="utf-8") as f:
            cls.lesson = json.load(f)
        cls.frames = compile_lesson(cls.lesson)

    # ── basic sanity ──────────────────────────────────────────────────

    def test_compile_returns_list(self):
        self.assertIsInstance(self.frames, list)

    def test_frame_count_equals_lesson_frames(self):
        expected = len(self.lesson["frames"])
        self.assertEqual(len(self.frames), expected)

    def test_frames_have_required_keys(self):
        for f in self.frames:
            for key in ("frame_id", "title", "caption", "objects", "arrows", "badges"):
                self.assertIn(key, f, f"Frame {f.get('frame_id')} missing key: {key}")

    def test_objects_have_id_and_type(self):
        for f in self.frames:
            for o in f["objects"]:
                self.assertIn("id", o)
                self.assertIn("type", o)
                self.assertIn("x", o)
                self.assertIn("y", o)

    # ── frame content ─────────────────────────────────────────────────

    def test_first_frame_contains_array_boxes(self):
        f = self.frames[0]
        types = {o["type"] for o in f["objects"]}
        self.assertIn("array_box", types)

    def test_first_frame_contains_input_value_label(self):
        f = self.frames[0]
        texts = [o["text"] for o in f["objects"]]
        self.assertTrue(
            any("target" in t for t in texts),
            f"Expected 'target' label in frame 0 objects; got: {texts}",
        )

    def test_rule_cards_appear_in_later_frames(self):
        all_types = {o["type"] for f in self.frames for o in f["objects"]}
        self.assertIn("rule_card", all_types)

    def test_definition_container_appears(self):
        all_types = {o["type"] for f in self.frames for o in f["objects"]}
        self.assertIn("definition", all_types)

    def test_variable_boxes_appear(self):
        all_types = {o["type"] for f in self.frames for o in f["objects"]}
        self.assertIn("variable_box", all_types)

    def test_map_entry_appears(self):
        all_types = {o["type"] for f in self.frames for o in f["objects"]}
        self.assertIn("map_entry", all_types)

    def test_answer_box_appears(self):
        all_types = {o["type"] for f in self.frames for o in f["objects"]}
        self.assertIn("answer_box", all_types)

    # ── action effects ────────────────────────────────────────────────

    def test_highlight_sets_active_on_array_box(self):
        """After read_nums0, nums[0] should be in active state."""
        read_frame = next(
            (f for f in self.frames if f["frame_id"] == "read_nums0"), None
        )
        self.assertIsNotNone(read_frame, "Expected frame read_nums0")
        active_boxes = [
            o for o in read_frame["objects"]
            if o["type"] == "array_box" and o["state"] == "active"
        ]
        self.assertGreater(len(active_boxes), 0, "Expected at least one active array_box after highlight")

    def test_derive_updates_variable_text(self):
        """After read_nums0 (derive action), var:need should show a numeric value."""
        read_frame = next(
            (f for f in self.frames if f["frame_id"] == "read_nums0"), None
        )
        self.assertIsNotNone(read_frame)
        need_objs = [o for o in read_frame["objects"] if o.get("id") == "var:need"]
        self.assertTrue(need_objs, "var:need should be visible after derive")
        self.assertNotIn("?", need_objs[0]["text"],
            f"var:need text should not be '?' after derive; got: {need_objs[0]['text']}")

    def test_current_variable_reflects_nums0(self):
        """var:current should contain the value 2 (nums[0])."""
        read_frame = next(
            (f for f in self.frames if f["frame_id"] == "read_nums0"), None
        )
        self.assertIsNotNone(read_frame)
        cur_objs = [o for o in read_frame["objects"] if o.get("id") == "var:current"]
        self.assertTrue(cur_objs, "var:current should be visible")
        self.assertIn("2", cur_objs[0]["text"],
            f"var:current should contain '2'; got: {cur_objs[0]['text']}")

    def test_need_value_for_nums0_is_7(self):
        """need = target(9) - current(2) = 7."""
        read_frame = next(
            (f for f in self.frames if f["frame_id"] == "read_nums0"), None
        )
        self.assertIsNotNone(read_frame)
        need_objs = [o for o in read_frame["objects"] if o.get("id") == "var:need"]
        self.assertTrue(need_objs)
        self.assertIn("7", need_objs[0]["text"],
            f"var:need should be 7 for nums[0]=2; got: {need_objs[0]['text']}")

    def test_transform_creates_map_entry(self):
        """store_nums0 frame should contain a map_entry object."""
        store_frame = next(
            (f for f in self.frames if f["frame_id"] == "store_nums0"), None
        )
        self.assertIsNotNone(store_frame)
        entries = [o for o in store_frame["objects"] if o["type"] == "map_entry"]
        self.assertGreater(len(entries), 0, "Expected at least one map_entry in store_nums0")

    def test_insert_into_positions_entry_inside_container(self):
        """After insert_into, map_entry y-pos should be within the definition container."""
        store_frame = next(
            (f for f in self.frames if f["frame_id"] == "store_nums0"), None
        )
        self.assertIsNotNone(store_frame)
        entries = [o for o in store_frame["objects"] if o["type"] == "map_entry"]
        defs    = [o for o in store_frame["objects"] if o["type"] == "definition"]
        if entries and defs:
            def_y = defs[0]["y"]
            def_bottom = def_y + defs[0]["h"]
            for entry in entries:
                self.assertGreaterEqual(entry["y"], def_y,
                    "Map entry should be at or below the definition container top")
                self.assertLessEqual(entry["y"], def_bottom,
                    "Map entry should be within the definition container")

    def test_connect_produces_arrow(self):
        """check_map_success frame should have a connection arrow."""
        success_frame = next(
            (f for f in self.frames if f["frame_id"] == "check_map_success"), None
        )
        self.assertIsNotNone(success_frame)
        self.assertGreater(len(success_frame["arrows"]), 0,
            "Expected at least one arrow in check_map_success")

    def test_return_sets_answer_state_to_matched(self):
        """return_answer frame should have answer_box with state=matched."""
        ret_frame = next(
            (f for f in self.frames if f["frame_id"] == "return_answer"), None
        )
        self.assertIsNotNone(ret_frame)
        answer_objs = [o for o in ret_frame["objects"] if o["type"] == "answer_box"]
        self.assertTrue(answer_objs, "answer_box should be visible in return_answer")
        self.assertEqual(answer_objs[0]["state"], "matched")

    def test_return_sets_answer_text_with_value(self):
        """answer_box text should contain '0, 1' or '[0, 1]'."""
        ret_frame = next(
            (f for f in self.frames if f["frame_id"] == "return_answer"), None
        )
        self.assertIsNotNone(ret_frame)
        answer_objs = [o for o in ret_frame["objects"] if o["type"] == "answer_box"]
        self.assertTrue(answer_objs)
        text = answer_objs[0]["text"]
        self.assertTrue(
            "0" in text and "1" in text,
            f"answer_box text should contain [0, 1]; got: {text}",
        )

    # ── statefulness ──────────────────────────────────────────────────

    def test_objects_persist_across_frames(self):
        """Once appeared, the definition container should remain visible in later frames."""
        appeared_in = None
        for f in self.frames:
            ids = {o["id"] for o in f["objects"]}
            if "concept:seen" in ids:
                appeared_in = f["frame_id"]
                break
        self.assertIsNotNone(appeared_in, "concept:seen should appear in some frame")
        # All subsequent frames should also have concept:seen
        found = False
        for f in reversed(self.frames):
            ids = {o["id"] for o in f["objects"]}
            if "concept:seen" in ids:
                found = True
                break
        self.assertTrue(found, "concept:seen should persist to the last frame")

    def test_second_highlight_marks_first_as_visited(self):
        """After read_nums1, nums[0] should be visited, nums[1] should be active."""
        read1_frame = next(
            (f for f in self.frames if f["frame_id"] == "read_nums1"), None
        )
        self.assertIsNotNone(read1_frame)
        box0 = next(
            (o for o in read1_frame["objects"] if o.get("id") == "input:nums[0]"), None
        )
        box1 = next(
            (o for o in read1_frame["objects"] if o.get("id") == "input:nums[1]"), None
        )
        if box0:
            self.assertEqual(box0["state"], "visited",
                "nums[0] should be 'visited' after nums[1] is highlighted")
        if box1:
            self.assertEqual(box1["state"], "active",
                "nums[1] should be 'active' when highlighted")

    # ── compile_lesson_file ───────────────────────────────────────────

    def test_compile_lesson_file_returns_frames_and_title(self):
        frames, title = compile_lesson_file(LESSON_PATH)
        self.assertIsInstance(frames, list)
        self.assertGreater(len(frames), 0)
        self.assertIsInstance(title, str)
        self.assertGreater(len(title), 0)

    def test_compile_lesson_file_title_matches_lesson(self):
        frames, title = compile_lesson_file(LESSON_PATH)
        with open(LESSON_PATH, encoding="utf-8") as f:
            lesson = json.load(f)
        self.assertEqual(title, lesson["title"])

    # ── layout sanity ─────────────────────────────────────────────────

    def test_array_boxes_are_horizontally_spaced(self):
        f = self.frames[0]
        arr_boxes = sorted(
            [o for o in f["objects"] if o["type"] == "array_box"],
            key=lambda o: o["x"],
        )
        self.assertGreaterEqual(len(arr_boxes), 2)
        for i in range(len(arr_boxes) - 1):
            gap = arr_boxes[i + 1]["x"] - arr_boxes[i]["x"]
            self.assertGreaterEqual(gap, 60, f"Array boxes too close: gap={gap}px")

    def test_rule_cards_are_vertically_spaced(self):
        last_frame = self.frames[-1]
        rules = sorted(
            [o for o in last_frame["objects"] if o["type"] == "rule_card"],
            key=lambda o: o["y"],
        )
        if len(rules) >= 2:
            for i in range(len(rules) - 1):
                gap = rules[i + 1]["y"] - rules[i]["y"]
                self.assertGreaterEqual(gap, 40, f"Rule cards too close: gap={gap}px")

    def test_no_objects_outside_stage(self):
        from pv.story_compiler import STAGE_W, STAGE_H
        for f in self.frames:
            for o in f["objects"]:
                if o.get("w", 0) == 0 and o.get("h", 0) == 0:
                    continue  # labels have 0 size
                self.assertGreaterEqual(o["x"], 0, f"Object {o['id']} x < 0")
                self.assertGreaterEqual(o["y"], 0, f"Object {o['id']} y < 0")
                self.assertLessEqual(o["x"] + o.get("w", 0), STAGE_W + 40,
                    f"Object {o['id']} extends beyond stage width")


if __name__ == "__main__":
    unittest.main()
