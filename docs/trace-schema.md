# Trace Schema

## 1. Design Goal

The trace schema is the core of this project.

It should describe algorithm execution in a way that is:

- deterministic;
- easy to diff;
- independent from any one renderer;
- understandable to a beginner;
- expressive enough for common LeetCode-style patterns.

The schema should not be a raw Python VM event dump. It should record semantic events: pointer moves, hash-map updates, DP writes, recursion calls, queue operations, linked-list edge rewires, and similar teaching moments.

## 2. Architecture Principle

Use this pipeline:

```text
execution / instrumentation
        ↓
semantic trace events
        ↓
renderer-specific projection
        ↓
text / HTML / SVG / React / Manim
```

Do not let the renderer define the trace format. Renderers are consumers, not the source of truth.

## 3. Top-Level Trace Envelope

Recommended shape:

```json
{
  "trace_version": "0.1.0",
  "problem": {
    "id": "0001_two_sum",
    "display_title": "Two Sum",
    "pattern_tags": ["array", "hash_map"]
  },
  "run": {
    "language": "python",
    "entry": {
      "class_name": "Solution",
      "method_name": "twoSum"
    },
    "input": {
      "nums": [2, 7, 11, 15],
      "target": 9
    },
    "expected": [0, 1],
    "actual": [0, 1],
    "status": "passed"
  },
  "objects": {
    "arr:nums": {
      "kind": "array",
      "value": [2, 7, 11, 15]
    },
    "map:seen": {
      "kind": "hash_map",
      "entries": {}
    }
  },
  "events": []
}
```

## 4. Event Shape

Recommended event shape:

```json
{
  "step": 7,
  "event_type": "hash_map_put",
  "phase": "execute",
  "line": {
    "original": 5,
    "generated": 14,
    "function": "twoSum"
  },
  "reference": {
    "object_ids": ["arr:nums", "map:seen"],
    "frame_id": "frame:twoSum:0"
  },
  "before": {
    "map:seen": {}
  },
  "after": {
    "map:seen": {"2": 0}
  },
  "state_patch": [
    {"op": "set", "target": "map:seen", "key": "2", "value": 0}
  ],
  "highlight": {
    "objects": ["arr:nums", "map:seen"],
    "indices": {"arr:nums": [0]},
    "variables": {"i": 0, "num": 2, "complement": 7}
  },
  "message": "把当前值 2 记录到哈希表里，后面才能快速查补数。",
  "subgoal": "建立已见元素表",
  "pedagogy": {
    "why_now": "当前还没找到补数，所以先记住它。",
    "common_mistake": "先存后查和先查后存在不同题里并不总是等价。"
  }
}
```

## 5. Required vs Optional Fields

### Required Fields

Every event should contain:

- `step`
- `event_type`
- `message`

### Strongly Recommended Fields

Most events should contain:

- `highlight`
- `before`
- `after`
- `reference`
- `line`
- `pedagogy`

### Optional Fields

Use when helpful:

- `state_patch`
- `subgoal`
- `invariant`
- `common_mistake`
- `pattern_name`
- `complexity_note`
- `debug_note`

## 6. Object Model

Every visual object should have a stable ID.

Suggested ID forms:

```text
arr:nums
map:seen
node:3
edge:3->4
tree:root
grid:cell:2:1
frame:dfs:5
dp:table
queue:bfs
stack:call
pointer:left
pointer:right
```

The renderer should not need to know which problem created the object. It should only need to know object kind and event semantics.

## 7. Event Vocabulary

Keep the vocabulary small and stable. Prefer reusable event types over one-off problem-specific names.

### 7.1 Arrays and Hash Maps

- `array_read`
- `array_write`
- `swap`
- `hash_map_get`
- `hash_map_put`
- `hash_map_delete`
- `answer_found`
- `return`

### 7.2 Two Pointers and Sliding Window

- `pointer_init`
- `pointer_move`
- `window_expand`
- `window_shrink`
- `best_update`
- `duplicate_skip`
- `comparison_reason`

### 7.3 Linked Lists

- `node_create`
- `pointer_follow`
- `link_cut`
- `link_set`
- `head_update`
- `cursor_move`
- `meeting_check`

### 7.4 Stack / Queue / Heap

- `push`
- `pop`
- `peek`
- `enqueue`
- `dequeue`
- `heap_push`
- `heap_pop`

### 7.5 Trees

- `tree_visit`
- `edge_traverse`
- `queue_layer_start`
- `queue_layer_end`
- `child_enqueue`

### 7.6 Graphs and Grids

- `component_start`
- `discover`
- `mark_visited`
- `frontier_add`
- `frontier_remove`
- `neighbor_check`
- `component_end`

### 7.7 Dynamic Programming

- `dp_init`
- `dp_read`
- `dp_write`
- `transition_considered`
- `rolling_update`
- `best_update`

### 7.8 Recursion and Backtracking

- `call`
- `return`
- `choose`
- `recurse`
- `unchoose`
- `prune`
- `backtrack`
- `solution_emit`

## 8. Teaching Metadata

Teaching fields are first-class data, not decorations.

Recommended `pedagogy` fields:

```json
{
  "why_now": "Why this step happens now.",
  "mental_model": "The beginner-friendly metaphor.",
  "common_mistake": "What learners often misunderstand here.",
  "invariant": "What remains true after this step.",
  "pattern_name": "Hash complement lookup"
}
```

## 9. Checkpoints and Patches

For short traces, `before` and `after` snapshots are enough.

For longer traces, add:

- periodic checkpoints;
- lightweight `state_patch` operations;
- event-level highlights.

This lets the renderer jump to any step without replaying thousands of events.

## 10. Verified Event Vocabulary

The following event types are confirmed working across the first two problems
(0001_two_sum, 0011_container_with_most_water).  Every event listed here has
a corresponding trace event in at least one committed `trace.sample.json`.

| event_type           | problem(s)                      | section  | description                         |
|----------------------|---------------------------------|----------|-------------------------------------|
| `array_read`         | two_sum                         | 7.1      | 读取数组元素，记录 index + value    |
| `hash_map_get`       | two_sum                         | 7.1      | 在哈希表中查找补数                  |
| `hash_map_put`       | two_sum                         | 7.1      | 将当前值存入哈希表                  |
| `answer_found`       | two_sum                         | 7.1      | 找到最终答案                        |
| `pointer_init`       | container_with_most_water       | 7.2      | 初始化左右指针                      |
| `area_compute`       | container_with_most_water       | 7.2*     | 计算当前面积（width × min_height）  |
| `best_update`        | container_with_most_water       | 7.2      | 更新最佳记录                        |
| `comparison_reason`  | container_with_most_water       | 7.2      | 说明为什么移动某一侧指针            |
| `pointer_move`       | container_with_most_water       | 7.2      | 指针实际移动到新位置                |
| `return`             | two_sum, container_with_most_water | 7.1   | 返回最终结果                        |

> `area_compute` is a custom event specific to container-type problems.  It
> belongs to the two-pointers family but is not listed in the original draft
> vocabulary; it is included here as a verified extension.

New event types can be added when a new problem requires them.  After a
problem is committed with its `trace.sample.json`, append the new event
type(s) to this table.

## 11. Renderer Contract

A renderer should be able to consume trace JSON and produce one of:

- text playback;
- static HTML;
- SVG diagrams;
- interactive React state;
- Manim script in the future.

The same trace should be usable by multiple renderers.

## 12. Versioning

Use semantic trace versions:

```text
0.1.0  first MVP schema
0.2.0  add linked-list and tree object conventions
0.3.0  add renderer hints
1.0.0  stable public format
```

Breaking changes should be documented in `docs/trace-schema.md` and tested against saved `trace.sample.json` files.
