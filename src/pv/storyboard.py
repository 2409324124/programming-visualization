"""Storyboard renderer: converts Two Sum trace JSON into animation frames.

Each frame describes a single visual state with objects (boxes, labels),
arrows (data-flow), and badges (contextual info like the target value).
"""

# ── Layout constants ────────────────────────────────────────────────
STAGE_W = 960
STAGE_H = 520

TARGET_LABEL_X = 60
TARGET_LABEL_Y = 36

ARRAY_BOX_Y = 150
ARRAY_BOX_W = 64
ARRAY_BOX_H = 56
ARRAY_BOX_X_START = 120
ARRAY_BOX_X_GAP = 100

COMPLEMENT_X = 650
COMPLEMENT_Y = 150
COMPLEMENT_W = 110
COMPLEMENT_H = 48

MAP_TITLE_X = 60
MAP_TITLE_Y = 280

MAP_ENTRY_Y = 335
MAP_ENTRY_W = 110
MAP_ENTRY_H = 48
MAP_ENTRY_X_START = 120
MAP_ENTRY_X_GAP = 130

ANSWER_X = 650
ANSWER_Y = 400
ANSWER_W = 150
ANSWER_H = 56

# ── Card layout ───────────────────────────────────────────────────
CARD_X = 600
CARD_Y_START = 50
CARD_GAP = 78
CARD_W = 280
CARD_H = 62


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


def _ghost_map_entry(key: int, idx: int, x: int, y: int, state: str = "faded") -> dict:
    """A map entry placed at an arbitrary position (e.g. over an array box).

    Using the same ``id`` as a normal ``_map_entry`` lets the HTML renderer
    animate the element from the ghost position to the real map position via
    CSS transitions on keyed DOM nodes.
    """
    return {
        "id": f"map:{key}",
        "type": "map_entry",
        "text": f"{key} \u2192 {idx}",
        "x": x,
        "y": y,
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


def _definition_card(card_id: str, title: str, body: str, slot: int, state: str = "normal") -> dict:
    return {
        "id": card_id,
        "type": "definition_card",
        "title": title,
        "text": body,
        "x": CARD_X,
        "y": CARD_Y_START + slot * CARD_GAP,
        "w": CARD_W,
        "h": CARD_H,
        "state": state,
    }


def _rule_card(card_id: str, text: str, slot: int, state: str = "normal") -> dict:
    return {
        "id": card_id,
        "type": "rule_card",
        "title": "规则",
        "text": text,
        "x": CARD_X,
        "y": CARD_Y_START + slot * CARD_GAP,
        "w": int(CARD_W * 0.85),
        "h": CARD_H - 6,
        "state": state,
    }


def _operation_card(text: str, slot: int, state: str = "active") -> dict:
    return {
        "id": "op_card",
        "type": "operation_card",
        "title": "操作",
        "text": text,
        "x": CARD_X,
        "y": CARD_Y_START + slot * CARD_GAP,
        "w": int(CARD_W * 0.9),
        "h": CARD_H - 6,
        "state": state,
    }


def _note_card(text: str, slot: int) -> dict:
    return {
        "id": "note_card",
        "type": "note_card",
        "title": "注意",
        "text": text,
        "x": CARD_X + 30,
        "y": CARD_Y_START + slot * CARD_GAP + 6,
        "w": CARD_W - 30,
        "h": CARD_H - 12,
        "state": "faded",
    }


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

    # ── Frame 0: input_appear ─────────────────────────────────────────
    frames.append({
        "frame_id": "input_appear",
        "step": 0,
        "title": "输入数组",
        "caption": f"nums = {nums}，target = {target}。先把输入变成可以观察的对象。",
        "objects": ([_target_label(target)] + _arr_boxes() + all_index_labels),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 1: goal_definition ─────────────────────────────────────
    frames.append({
        "frame_id": "goal_definition",
        "step": 0,
        "title": "目标定义",
        "caption": f"找到两个数，使它们的和等于 {target}。",
        "objects": (
            [_target_label(target)] + _arr_boxes() + all_index_labels
            + [_definition_card("card_goal", "目标", f"找到两个数\n使它们的和 = {target}", 0, "active")]
        ),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 2: return_definition ───────────────────────────────────
    frames.append({
        "frame_id": "return_definition",
        "step": 0,
        "title": "返回值是什么",
        "caption": "返回的是两个数的下标，不是数字本身。",
        "objects": (
            [_target_label(target)] + _arr_boxes() + all_index_labels
            + [_definition_card("card_goal", "目标", f"找到两个数\n使它们的和 = {target}", 0)]
            + [_note_card("answer = [index_a, index_b]", 1)]
        ),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 3: hashmap_definition ──────────────────────────────────
    frames.append({
        "frame_id": "hashmap_definition",
        "step": 0,
        "title": "哈希表定义",
        "caption": "哈希表保存已经见过的数字，以及它出现的下标。",
        "objects": (
            [_target_label(target)] + _arr_boxes() + all_index_labels
            + [_map_zone_title(), _map_empty_label()]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1, "new")]
        ),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 4: complement_rule ─────────────────────────────────────
    frames.append({
        "frame_id": "complement_rule",
        "step": 0,
        "title": "补数规则",
        "caption": f"如果 current + need = {target}，那么 need 就是我们要找的另一个数。",
        "objects": (
            [_target_label(target)] + _arr_boxes() + all_index_labels
            + [_map_zone_title(), _map_empty_label()]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1)]
            + [_rule_card("card_rule_need", f"need = {target} - current", 2, "new")]
        ),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 5: read_nums0 ──────────────────────────────────────────
    e0 = events[0]
    i0 = e0["before"].get("i", 0)
    num0 = nums[i0]
    complement0 = target - num0
    frames.append({
        "frame_id": "read_nums0",
        "step": 1,
        "title": f"读取 nums[{i0}] = {num0}",
        "caption": f"当前读取 nums[{i0}] = {num0}。需要补数 = {complement0}。",
        "objects": (
            [_target_label(target)] + _arr_boxes({0: "active"}) + all_index_labels
            + [_complement_box(complement0)]
            + [_map_zone_title(), _map_empty_label()]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1)]
            + [_rule_card("card_rule_need", f"need = {target} - current", 2)]
            + [_operation_card(f"current = {num0}\nneed = {target} - {num0} = {complement0}", 3)]
        ),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 6: check_map_fail ──────────────────────────────────────
    frames.append({
        "frame_id": "check_map_fail",
        "step": 2,
        "title": "查询哈希表",
        "caption": f"查找 seen[{complement0}]，{complement0} 不存在。还不能返回答案。",
        "objects": (
            [_target_label(target)] + _arr_boxes({0: "visited"}) + all_index_labels
            + [_map_zone_title(), _map_empty_label()]
            + [_ghost_map_entry(num0, 0, ARRAY_BOX_X_START, ARRAY_BOX_Y, "faded")]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1)]
            + [_rule_card("card_rule_need", f"need = {target} - current", 2)]
            + [_operation_card(f"查找 seen[{complement0}]\n{complement0} 不存在 ✗", 3)]
        ),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 7: store_2_in_map ──────────────────────────────────────
    frames.append({
        "frame_id": "store_2_in_map",
        "step": 3,
        "title": f"记录 {num0} 到哈希表",
        "caption": f"执行 seen[{num0}] = {i0}。{num0} 从数组区移动到哈希表。",
        "objects": (
            [_target_label(target)] + _arr_boxes({0: "visited"}) + all_index_labels
            + [_map_zone_title(), _map_entry(num0, i0, 0, "new")]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1)]
            + [_rule_card("card_rule_need", f"need = {target} - current", 2)]
            + [_operation_card(f"seen[{num0}] = {i0}  ✓", 3)]
        ),
        "arrows": [{"id": "arrow:store", "from": f"arr:{i0}", "to": f"map:{num0}", "label": "store"}],
        "badges": [badge],
    })

    # ── Frame 8: read_nums1 ──────────────────────────────────────────
    e3 = events[3]
    i1 = e3["before"].get("i", 1)
    num1 = nums[i1]
    complement1 = target - num1
    frames.append({
        "frame_id": "read_nums1",
        "step": 4,
        "title": f"读取 nums[{i1}] = {num1}",
        "caption": f"当前读取 nums[{i1}] = {num1}。需要补数 = {complement1}。",
        "objects": (
            [_target_label(target)] + _arr_boxes({0: "visited", 1: "active"}) + all_index_labels
            + [_complement_box(complement1)]
            + [_map_zone_title(), _map_entry(num0, 0, 0)]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1)]
            + [_rule_card("card_rule_need", f"need = {target} - current", 2)]
            + [_operation_card(f"current = {num1}\nneed = {target} - {num1} = {complement1}", 3, "active")]
        ),
        "arrows": [],
        "badges": [badge],
    })

    # ── Frame 9: check_map_success ───────────────────────────────────
    frames.append({
        "frame_id": "check_map_success",
        "step": 5,
        "title": "哈希表匹配成功！",
        "caption": f"查找 seen[{complement1}]，找到了！{complement1} 在索引 0。",
        "objects": (
            [_target_label(target)] + _arr_boxes({0: "matched", 1: "matched"}) + all_index_labels
            + [_map_zone_title(), _map_entry(num0, 0, 0, "matched")]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1)]
            + [_rule_card("card_rule_need", f"need = {target} - current", 2)]
            + [_operation_card(f"查找 seen[{complement1}]\n找到了 ✓\n{num0} + {num1} = {target}", 3, "matched")]
        ),
        "arrows": [{"id": "arrow:match", "from": f"arr:{i1}", "to": f"map:{num0}", "label": "match", "color": "#66bb6a"}],
        "badges": [badge],
    })

    # ── Frame 10: answer ─────────────────────────────────────────────
    frames.append({
        "frame_id": "answer",
        "step": 6,
        "title": "返回答案",
        "caption": f"返回 [{result[0]}, {result[1]}]。nums[0] + nums[1] = {nums[0]} + {nums[1]} = {target}。",
        "objects": (
            [_target_label(target)] + _arr_boxes({0: "matched", 1: "matched"}) + all_index_labels
            + [_map_zone_title(), _map_entry(num0, 0, 0, "matched")]
            + [_answer_box(f"[{result[0]}, {result[1]}]")]
            + [_definition_card("card_hash", "哈希表", "保存见过的数字\n和它的下标", 0)]
            + [_rule_card("card_rule_seen", "seen[number] = index", 1)]
            + [_rule_card("card_rule_need", f"need = {target} - current", 2)]
            + [_note_card(f"返回的是下标 [{result[0]}, {result[1]}]\n因为 nums[0]+nums[1]={target}", 3)]
        ),
        "arrows": [],
        "badges": [badge],
    })

    return frames
