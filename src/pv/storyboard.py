"""Storyboard renderer: converts Two Sum trace JSON into animation frames.

Each frame describes a single visual state with objects (boxes, labels),
arrows (data-flow), and badges (contextual info like the target value).
"""

# ── Layout constants ────────────────────────────────────────────────
TARGET_LABEL_X = 80
TARGET_LABEL_Y = 40

ARRAY_BOX_Y = 120
ARRAY_BOX_W = 56
ARRAY_BOX_H = 48
ARRAY_BOX_X_START = 80
ARRAY_BOX_X_GAP = 80

COMPLEMENT_X = 540
COMPLEMENT_Y = 120
COMPLEMENT_W = 72
COMPLEMENT_H = 40

MAP_TITLE_X = 80
MAP_TITLE_Y = 220

MAP_ENTRY_Y = 260
MAP_ENTRY_W = 80
MAP_ENTRY_H = 40
MAP_ENTRY_X_START = 80
MAP_ENTRY_X_GAP = 100

ANSWER_X = 100
ANSWER_Y = 380
ANSWER_W = 120
ANSWER_H = 48


# ── Object factories ────────────────────────────────────────────────

def _target_label(target: int) -> dict:
    return {
        "id": "label_target",
        "type": "label",
        "text": f"target = {target}",
        "x": TARGET_LABEL_X,
        "y": TARGET_LABEL_Y,
        "w": 0,
        "h": 0,
        "state": "normal",
    }


def _array_box(i: int, value: int, state: str = "normal") -> dict:
    return {
        "id": f"arr:{i}",
        "type": "array_box",
        "text": str(value),
        "idx": i,
        "x": ARRAY_BOX_X_START + i * ARRAY_BOX_X_GAP,
        "y": ARRAY_BOX_Y,
        "w": ARRAY_BOX_W,
        "h": ARRAY_BOX_H,
        "state": state,
    }


def _index_label(i: int) -> dict:
    return {
        "id": f"idx_label:{i}",
        "type": "label",
        "text": f"[{i}]",
        "x": ARRAY_BOX_X_START + i * ARRAY_BOX_X_GAP + ARRAY_BOX_W // 2,
        "y": ARRAY_BOX_Y + ARRAY_BOX_H + 4,
        "w": 0,
        "h": 0,
        "state": "normal",
    }


def _complement_box(complement: int, state: str = "normal") -> dict:
    return {
        "id": "comp",
        "type": "complement_box",
        "text": f"need {complement}",
        "x": COMPLEMENT_X,
        "y": COMPLEMENT_Y,
        "w": COMPLEMENT_W,
        "h": COMPLEMENT_H,
        "state": state,
    }


def _map_zone_title() -> dict:
    return {
        "id": "map_zone_title",
        "type": "label",
        "text": "哈希表",
        "x": MAP_TITLE_X,
        "y": MAP_TITLE_Y,
        "w": 0,
        "h": 0,
        "state": "normal",
    }


def _map_empty_label() -> dict:
    return {
        "id": "map_empty",
        "type": "label",
        "text": "(empty)",
        "x": MAP_ENTRY_X_START,
        "y": MAP_ENTRY_Y,
        "w": 0,
        "h": 0,
        "state": "faded",
    }


def _map_entry(key: int, idx: int, slot: int, state: str = "normal") -> dict:
    return {
        "id": f"map:{key}",
        "type": "map_entry",
        "text": f"{key} \u2192 {idx}",
        "x": MAP_ENTRY_X_START + slot * MAP_ENTRY_X_GAP,
        "y": MAP_ENTRY_Y,
        "w": MAP_ENTRY_W,
        "h": MAP_ENTRY_H,
        "state": state,
    }


def _answer_box(text: str = "[0, 1]") -> dict:
    return {
        "id": "answer",
        "type": "answer_box",
        "text": text,
        "x": ANSWER_X,
        "y": ANSWER_Y,
        "w": ANSWER_W,
        "h": ANSWER_H,
        "state": "normal",
    }


# ── Badge helper ────────────────────────────────────────────────────

def _target_badge(target: int) -> dict:
    return {"id": "badge_target", "text": f"target = {target}"}


# ── Main entry point ────────────────────────────────────────────────

def build_storyboard(trace_data: dict) -> list[dict]:
    """Convert a Two Sum trace dict into storyboard frames.

    Raises ValueError with a user-friendly message if the trace is not from
    ``0001_two_sum``.
    """

    problem_id = trace_data["problem"]["problem_id"]
    if problem_id != "0001_two_sum":
        raise ValueError("storyboard renderer currently supports only 0001_two_sum")

    nums: list[int] = trace_data["run"]["input"]["nums"]
    target: int = trace_data["run"]["input"]["target"]
    events: list[dict] = trace_data["events"]
    result: list[int] = trace_data["run"].get("actual") or trace_data["run"].get("expected", [0, 1])

    n = len(nums)
    badge = _target_badge(target)
    all_index_labels = [_index_label(i) for i in range(n)]

    # Shorthand: array boxes with per-index state overrides
    def _arr_boxes(overrides: dict[int, str] | None = None) -> list[dict]:
        overrides = overrides or {}
        return [_array_box(i, nums[i], overrides.get(i, "normal")) for i in range(n)]

    frames: list[dict] = []

    # ── Frame 0: input_appear ───────────────────────────────────────
    frames.append(
        {
            "frame_id": "input_appear",
            "step": 0,
            "title": "输入数组",
            "caption": (
                f"先把输入数组变成可以观察的对象。"
                f"target = {target}，需要找到两个数和为 {target} 的下标。"
            ),
            "objects": [_target_label(target)] + _arr_boxes() + all_index_labels,
            "arrows": [],
            "badges": [badge],
        }
    )

    # ── Frame 1: read_nums0 ────────────────────────────────────────
    # step=1, array_read: read nums[0]
    e1_before = events[0].get("before") or {}
    i0 = e1_before.get("i", 0)
    num0 = e1_before.get("num", nums[0])
    complement0 = target - num0

    frames.append(
        {
            "frame_id": "read_nums0",
            "step": 1,
            "title": "读取 nums[0]",
            "caption": (
                f"当前读取 nums[{i0}] = {num0}。"
                f"要满足 target = {target}，需要补数 = {complement0}。"
            ),
            "objects": (
                [_target_label(target)]
                + _arr_boxes({0: "active"})
                + all_index_labels
                + [_complement_box(complement0)]
            ),
            "arrows": [],
            "badges": [badge],
        }
    )

    # ── Frame 2: check_complement_7 ────────────────────────────────
    # step=2, hash_map_get: complement not found (map empty)
    frames.append(
        {
            "frame_id": "check_complement_7",
            "step": 2,
            "title": "检查哈希表",
            "caption": f"补数 {complement0} 不在哈希表中（表为空）。所以不能匹配。",
            "objects": (
                [_target_label(target)]
                + _arr_boxes({0: "visited"})
                + all_index_labels
                + [_complement_box(complement0, "faded")]
                + [_map_zone_title(), _map_empty_label()]
            ),
            "arrows": [],
            "badges": [badge],
        }
    )

    # ── Frame 3: store_2_in_map ────────────────────────────────────
    # step=3, hash_map_put: store num0 → index 0
    frames.append(
        {
            "frame_id": "store_2_in_map",
            "step": 3,
            "title": f"记录 {num0} 到哈希表",
            "caption": (
                f"把 {num0} \u2192 索引 0 记录下来，"
                f"以后遇到 {complement0} 就能快速找到。"
            ),
            "objects": (
                [_target_label(target)]
                + _arr_boxes({0: "visited"})
                + all_index_labels
                + [_map_zone_title(), _map_entry(num0, 0, 0, "new")]
            ),
            "arrows": [{"id": "arrow:0", "from": f"arr:{i0}", "to": f"map:{num0}", "label": "store"}],
            "badges": [badge],
        }
    )

    # ── Frame 4: read_nums1 ────────────────────────────────────────
    # step=4, array_read: read nums[1]
    e4_before = events[3].get("before") or {}
    i1 = e4_before.get("i", 1)
    num1 = e4_before.get("num", nums[1])
    complement1 = target - num1

    frames.append(
        {
            "frame_id": "read_nums1",
            "step": 4,
            "title": f"读取 nums[{i1}]",
            "caption": (
                f"当前读取 nums[{i1}] = {num1}。"
                f"要满足 target = {target}，需要补数 = {complement1}。"
            ),
            "objects": (
                [_target_label(target)]
                + _arr_boxes({0: "visited", 1: "active"})
                + all_index_labels
                + [_complement_box(complement1)]
                + [_map_zone_title(), _map_entry(num0, 0, 0)]
            ),
            "arrows": [],
            "badges": [badge],
        }
    )

    # ── Frame 5: check_complement_2_found ──────────────────────────
    # step=5, hash_map_get: complement found!
    frames.append(
        {
            "frame_id": "check_complement_2_found",
            "step": 5,
            "title": "哈希表匹配成功！",
            "caption": (
                f"补数 {complement1} 在哈希表中（索引 0），"
                f"与当前的 {num1}（索引 1）配对成功。"
            ),
            "objects": (
                [_target_label(target)]
                + _arr_boxes({0: "matched", 1: "matched"})
                + all_index_labels
                + [_map_zone_title(), _map_entry(num0, 0, 0, "matched")]
            ),
            "arrows": [{"id": "arrow:1", "from": f"arr:{i1}", "to": f"map:{num0}", "label": "match"}],
            "badges": [badge],
        }
    )

    # ── Frame 6: answer ────────────────────────────────────────────
    # step=6, answer_found
    r0, r1 = result[0], result[1]
    frames.append(
        {
            "frame_id": "answer",
            "step": 6,
            "title": "返回答案",
            "caption": (
                f"返回 [{r0}, {r1}]，"
                f"即 nums[{r0}] + nums[{r1}] = {nums[r0]} + {nums[r1]} = {target}。"
            ),
            "objects": (
                [_target_label(target)]
                + _arr_boxes({0: "matched", 1: "matched"})
                + all_index_labels
                + [_map_zone_title(), _map_entry(num0, 0, 0, "matched")]
                + [_answer_box(f"[{r0}, {r1}]")]
            ),
            "arrows": [],
            "badges": [badge],
        }
    )

    return frames
