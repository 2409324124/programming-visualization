# AGENTS.md

## 接手文档 — 其他 Agent 看这里

如果你是新来的 AI Agent，请按顺序阅读：

1. `AGENTS.md`（本文件）— 项目总纲 + 硬规则
2. `README.md` — 项目定位 + Quickstart
3. `docs/harness-plan.md` — harness 架构设计
4. `docs/trace-schema.md` — trace 事件词汇表
5. `docs/public-roadmap.md` — 已完成 / 下一步

**文件速查表：**

| 文件 | 职责 | 关键点 |
|------|------|--------|
| `src/pv/harness.py` | 核心执行器 | **唯一执行入口**，adapter/checker/import policy/stdout capture 都在这里 |
| `src/pv/trace_schema.py` | TraceBuilder + TraceEvent | 输出结构化 trace JSON |
| `src/pv/learner_trace.py` | sys.settrace 行级追踪 | 只追踪目标方法，不追踪 module/class 定义 |
| `src/pv/learner_runtime.py` | harness + 行级追踪封装 | render-code 的数据源 |
| `src/pv/checkers.py` | CheckResult + 内置 checker | exact / unordered_pairs / linked_list_equal |
| `src/pv/adapters.py` | JSON ↔ 数据结构 | builtin / linked_list（tree 未实现） |
| `src/pv/structures.py` | ListNode / TreeNode | 数据结构定义 |
| `src/pv/errors.py` | 所有自定义异常 | 每个异常都有中文 `user_message` |
| `src/pv/storyboard.py` | **遗留** authored 动画 | 硬编码值，已被 runtime-bound 替代 |
| `src/pv/story_compiler.py` | lesson-script 编译器 | visual_compiler 的基类 |
| `src/pv/visual_runtime.py` | runtime-bound 可视化 | **复用 harness.run_case()**，不重复执行逻辑 |
| `src/pv/visual_binder.py` | lesson ↔ runtime 绑定 | fail-fast 验证一致性 |
| `src/pv/visual_compiler.py` | 编译 bound lesson 为 frames | 输出 runtime-aware 帧 |
| `src/pv/cli.py` | 所有 CLI 子命令 | run / render-* / render-visual / render-code |

**硬规则（必须遵守）：**

1. **零外部 pip 依赖。** 纯 Python stdlib。
2. **绝不重复执行逻辑。** 如果要运行代码，调用 `harness.run_case()`，不要自己写 import/execute/check。`visual_runtime.py` 就是为了修这个问题重写的。
3. **绝不伪造 trace。** 如果 solution 没有 trace hook，`trace_mode` 为 `validation_only`，events 为空。
4. **绝不复制 LeetCode 内容。** 所有题面、用例、explain.md 均为原创。
5. **绝不用 CDN。** 所有 HTML 自包含、可离线打开。
6. **必须跑测试验证。** `uv run python -m unittest discover -s tests -v`。
7. **生成 HTML 后必须确认命令跑通了。** 静态看代码 ≠ 验证。
8. **优先小改，避免大重写。**

**常用命令：**

```bash
uv run python -m pv run problems/0001_two_sum --all
uv run python -m pv render-html trace.json --output out.html
uv run python -m pv render-code problems/0001_two_sum --case-index 0 -o out.html
uv run python -m pv render-visual problems/0001_two_sum --case-index 0 --lesson lesson.story.json -o out.html
uv run python -m pv render-story trace.json --output out.html
uv run python -m unittest discover -s tests -v
```

**当前状态：** 4 道题目，307 测试全通过，3 种渲染器（text / HTML trace viewer / code viewer），runtime-bound 可视化管线已在 main。

## Project Mission

This repository is a learning-first programming visualization project.

The target user is a non-CS / liberal-arts-background developer who finds classic LeetCode-style problems painful to debug, especially:

- two pointers
- sliding window
- linked lists
- recursion
- binary trees
- dynamic programming
- backtracking
- graph traversal

The goal is not to build another competitive programming judge. The goal is to turn each `class Solution` into a visible execution story: every pointer move, comparison, table update, recursion branch, linked-list rewiring, stack push/pop, and graph visit should be understandable at a glance.

## Research-Informed Direction

Before implementation, keep these findings in mind:

1. Existing algorithm visualization projects already exist. Algorithm Visualizer is an interactive online platform that visualizes algorithms from code. VisuAlgo provides mature educational animations for data structures and algorithms. These are references for interaction and pedagogy, not codebases to blindly copy.
2. Recent algorithm-visualization research suggests a robust architecture: decouple execution tracing from rendering. Do not ask an LLM to directly create final animations. Instead: run code or an instrumented tracker, emit structured trace JSON, then render deterministically.
3. Online judge systems generally work by compiling/running submitted code in a resource-limited sandbox, feeding generated or hidden tests, comparing outputs or return values, and reporting verdicts such as Accepted, Wrong Answer, Runtime Error, Time Limit Exceeded, or Memory Limit Exceeded. This project should simulate the educational subset locally, not attempt to reproduce or bypass LeetCode hidden tests.
4. Do not copy LeetCode proprietary problem statements, hidden tests, editorials, or paid content. Use public problem IDs/slugs as references, write original short summaries, and create our own small educational test cases.

## Core Product Idea

For each classic problem, provide three layers:

```text
clean Solution code
        ↓
trace-enabled Solution / wrapper
        ↓
visual explanation: timeline + state panels + plain-language notes
```

A user should be able to run something like:

```bash
python -m pv run problems/0001_two_sum --case 0
```

and get:

1. whether the solution returns the expected result on the local case;
2. a structured execution trace;
3. a human-readable visualization, initially text/HTML, later interactive web UI.

## Non-Goals

- Do not scrape LeetCode hidden tests.
- Do not implement a full online judge in v1.
- Do not build a huge frontend before trace schemas are stable.
- Do not optimize for competitive-programming speed first.
- Do not make visualizations only understandable to CS majors.

## Repository Structure

Prefer this structure as the project grows:

```text
programming-visualization/
├── AGENTS.md
├── README.md
├── docs/
│   ├── product-plan.md
│   ├── trace-schema.md
│   └── leetcode-hot-100-roadmap.md
├── examples/
│   └── trace-samples/
├── problems/
│   ├── 0001_two_sum/
│   │   ├── solution.py
│   │   ├── visual_solution.py
│   │   ├── cases.json
│   │   ├── explain.md
│   │   └── trace.sample.json
│   └── ...
└── src/
    └── pv/
        ├── harness.py
        ├── trace_schema.py
        ├── adapters.py
        ├── render_text.py
        ├── render_html.py
        └── structures.py
```

## Trace-First Architecture

Always build trace data before building animation.

A trace is a list of small events. Each event should answer:

- What changed?
- Why did it change?
- Which code line or algorithm step caused it?
- What should a beginner notice?

Example trace event shape:

```json
{
  "step": 7,
  "event": "move_pointer",
  "problem": "0011_container_with_most_water",
  "state": {
    "left": 2,
    "right": 8,
    "best_area": 49
  },
  "highlight": [2, 8],
  "message": "Right height is smaller, so move the right pointer inward."
}
```

## Standard Event Types

Use a small shared event vocabulary first:

### Arrays and Hash Maps

- `read_index`
- `compare_values`
- `write_map`
- `found_answer`
- `skip_duplicate`

### Two Pointers and Sliding Window

- `move_left`
- `move_right`
- `expand_window`
- `shrink_window`
- `update_best`

### Linked Lists

- `visit_node`
- `save_next`
- `rewire_next`
- `move_cursor`
- `detect_cycle`

### Stack / Queue / Heap

- `push`
- `pop`
- `peek`
- `enqueue`
- `dequeue`
- `heap_push`
- `heap_pop`

### Trees and Graphs

- `enter_node`
- `exit_node`
- `visit_neighbor`
- `mark_seen`
- `bfs_level_start`
- `dfs_backtrack`

### Dynamic Programming

- `init_dp`
- `read_dp`
- `update_dp`
- `choose_transition`
- `final_answer`

### Backtracking

- `choose`
- `recurse`
- `undo_choose`
- `prune`
- `emit_solution`

## LeetCode-Style Adapter Design

Most Python LeetCode solutions look like this:

```python
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        ...
```

The local harness should:

1. import `Solution` from `solution.py` or `visual_solution.py`;
2. locate the configured method name, such as `twoSum`;
3. load arguments from `cases.json`;
4. convert special structures, for example list arrays to linked lists or binary trees;
5. call the method;
6. normalize the returned value;
7. compare with local expected output;
8. save the trace.

For problems with multiple valid answers, do not compare raw equality only. Add a local checker function.

## Problem Package Contract

Every problem folder should include:

### `solution.py`

Clean solution, close to what someone would write on LeetCode.

### `visual_solution.py`

Trace-enabled version. It can be slightly more verbose than the clean solution. Clarity beats cleverness.

### `cases.json`

Small educational cases, not massive hidden tests.

Recommended format:

```json
[
  {
    "name": "basic example",
    "args": {"nums": [2, 7, 11, 15], "target": 9},
    "expected": [0, 1],
    "notes": "The answer appears after one hash-map lookup."
  }
]
```

### `explain.md`

Plain-language explanation for a non-CS learner:

- What is the mental model?
- What are the moving parts?
- What usually goes wrong?
- What should the visualization show?

### `trace.sample.json`

A saved sample trace for demos and regression checks.

## Educational Style Guide

Use the user's pain points as design constraints:

- Avoid pretending the idea is obvious.
- Explain pointer movement as physical movement.
- Explain DP as filling a memory table, not magic recurrence.
- Explain linked list rewiring as changing arrows.
- Show incorrect intermediate intuitions when useful.
- Prefer small input examples that fit on one screen.
- Every frame should have a beginner-friendly sentence.

Good message:

```text
We have seen value 2 before. Because current value is 7 and target is 9, 2 + 7 completes the answer.
```

Bad message:

```text
Apply complement lookup in O(n).
```

## Hot 100 Roadmap

Use LeetCode Hot 100 / classic interview problems as the initial curriculum reference, but keep our content original.

Suggested implementation order:

1. `0001_two_sum` — hash map trace, easiest MVP.
2. `0011_container_with_most_water` — two pointers.
3. `0015_three_sum` — sorting, duplicate skipping, two pointers.
4. `0206_reverse_linked_list` — pointer rewiring.
5. `0141_linked_list_cycle` — fast/slow pointer.
6. `0070_climbing_stairs` — tiny DP table.
7. `0198_house_robber` — DP state transition.
8. `0102_binary_tree_level_order_traversal` — queue + levels.
9. `0046_permutations` — backtracking choose/undo.
10. `0200_number_of_islands` — grid DFS/BFS.

After these 10, expand by pattern rather than by LeetCode order.

## Pattern Buckets

The project should organize problems by mental model:

```text
array-hashmap
    Two Sum, Group Anagrams, Longest Consecutive Sequence

two-pointers
    Container With Most Water, 3Sum, Trapping Rain Water

sliding-window
    Longest Substring Without Repeating Characters, Minimum Window Substring

linked-list
    Reverse Linked List, Merge Two Lists, Linked List Cycle, LRU Cache

stack
    Valid Parentheses, Min Stack, Daily Temperatures, Largest Rectangle

tree
    Max Depth, Invert Tree, Level Order, Diameter, Lowest Common Ancestor

graph-grid
    Number of Islands, Rotting Oranges, Course Schedule

backtracking
    Permutations, Subsets, Combination Sum, Word Search

dynamic-programming
    Climbing Stairs, House Robber, Coin Change, LIS, Edit Distance
```

## MVP Plan

### Phase 0: Trace Schema

Create:

- `src/pv/trace_schema.py`
- `src/pv/harness.py`
- `src/pv/render_text.py`

The first renderer can be plain text. A beautiful frontend is not required yet.

### Phase 1: First Visual Problem

Implement `0001_two_sum` end to end.

Success means:

```bash
python -m pv run problems/0001_two_sum --case 0
```

prints a step-by-step explanation and writes trace JSON.

### Phase 2: First Four Mental Models

Implement one problem each for:

- hash map
- two pointers
- linked list
- DP

Do not implement 100 problems before the workflow is comfortable.

### Phase 3: HTML Renderer

Create a simple static HTML renderer:

- array cells
- highlighted indices
- variable panel
- event timeline
- explanation sentence

Use simple HTML/SVG before using heavy frameworks.

### Phase 4: Interactive Frontend

Only after trace format stabilizes, consider:

- React
- SVG / Canvas
- React Flow for linked lists, trees, and graphs
- Manim export for videos

## Implementation Rules for Agents

When working in this repository:

1. Do not download or install packages unless the user explicitly asks.
2. Prefer standard-library Python for the first MVP.
3. Do not scrape LeetCode.
4. Do not include proprietary LeetCode statements or hidden tests.
5. Keep problem explanations original.
6. Build trace JSON before UI.
7. Keep traces deterministic and easy to diff.
8. Add small local examples instead of huge random tests.
9. For every new problem, include clean solution, visual solution, cases, explanation, and sample trace.
10. Treat visualization as pedagogy, not decoration.

## Local Judge Philosophy

This project should have a local educational judge, not a production judge.

Minimum local judge behavior:

- run configured cases;
- compare outputs;
- support custom checker functions;
- report wrong answers clearly;
- show the final trace even when the answer is wrong;
- never hide the failing case from the learner.

This is deliberately different from LeetCode. Hidden tests are good for ranking; visible tests and traces are better for learning.

## Definition of Done for a Visual Problem

A problem is done only when:

- `solution.py` passes local cases;
- `visual_solution.py` passes local cases;
- trace output is deterministic;
- every trace step has a beginner-readable message;
- `explain.md` describes common mistakes;
- the example is small enough to inspect visually;
- the renderer can show the important state transitions.

## First Commit Recommendation

After adding this file, the next practical commit should be:

```text
Add project agent guidance for LeetCode-style visualization
```
