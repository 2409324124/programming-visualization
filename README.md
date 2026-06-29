# Programming Visualization

[![CI](https://github.com/2409324124/programming-visualization/actions/workflows/ci.yml/badge.svg)](https://github.com/2409324124/programming-visualization/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一个面向非科班 / 文科背景 / 自学开发者的 **LeetCode-style 编程可视化学习器**。

[→ 在线 Demo Gallery](https://2409324124.github.io/programming-visualization/examples/)

- [Two Sum Story Animation](https://2409324124.github.io/programming-visualization/examples/story_0001_two_sum.case0.html)

> 本地查看：打开 `examples/index.html`。

## Viewer Paths

| Command | Purpose | Example |
|---------|---------|---------|
| `serve` | 本地交互式代码运行器 | `pv serve --host 127.0.0.1 --port 8765` |
| `render-code` | 用户代码执行过程 | `pv render-code problems/0001_two_sum --case-index 0` |
| `render-visual` | 官方概念可视化 | `pv render-visual problems/0001_two_sum --case-index 0` |
| `render-html` | trace viewer | `pv render-html trace.json` |
| `render-story` | legacy storyboard | `pv render-story trace.json` |

目标不是复制 LeetCode，也不是再做一个题解站，而是把经典 `class Solution` 的执行过程变成可理解的可视化故事：

- 双指针如何移动；
- 滑动窗口如何扩张和收缩；
- 哈希表如何记录状态；
- 链表箭头如何断开和重连；
- 递归栈如何展开和返回；
- 回溯如何 choose / recurse / unchoose；
- DP 表格如何一步步更新；
- 图和网格搜索如何标记 visited。

## Quickstart

**依赖：** Python 3.10+。推荐使用 [uv](https://docs.astral.sh/uv/) 管理环境（零运行时依赖）。

```bash
# 1. 克隆并进入项目
git clone https://github.com/2409324124/programming-visualization.git
cd programming-visualization

# 2. 创建虚拟环境并安装项目（可编辑模式）
uv venv
uv pip install -e .

# 3. 运行测试
uv run python -m unittest discover -s tests -v

# 4. 运行第一个题目
uv run python -m pv run problems/0001_two_sum --all

# 5. 使用可视化版本并保存 trace
uv run python -m pv run problems/0001_two_sum --solution visual_solution.py --save-trace --all

# 6. 渲染保存的 trace 为文本
uv run python -m pv render-text problems/0001_two_sum/trace.sample.json

# 7. 渲染为 HTML（支持 DP table、链表、数组可视化）
uv run python -m pv render-html problems/0070_climbing_stairs/trace.sample.json --output examples/0070_climbing_stairs.case0.html

# 8. 生成故事动画 (Two Sum)
uv run python -m pv render-story problems/0001_two_sum/trace.sample.json --output examples/story_0001_two_sum.case0.html

# 9. 查看自己代码的执行过程
uv run python -m pv render-code problems/0001_two_sum --case-index 0 --output examples/code_0001_two_sum.case0.html

# 10. 启动本地交互式 LeetCode-style 运行器
uv run python -m pv serve --host 127.0.0.1 --port 8765
# 打开 http://127.0.0.1:8765/，粘贴 class Solution，选择用例，点击 Run。
```

> 如果不使用 uv，可以用标准 venv：`python3 -m venv .venv && source .venv/bin/activate && pip install -e .`，之后不需要 `uv run` 前缀。

## Local Interactive Runner

启动一个本地 LeetCode-style 交互页面，在浏览器中编写代码、运行、查看行级执行过程：

```bash
uv run python -m pv serve --host 127.0.0.1 --port 8765
```

打开 `http://127.0.0.1:8765/`，即可：

- 选择题目标签和用例
- 在 textarea 中编写或修改 `class Solution`
- 点击 Run → 运行完成后显示 PASSED/FAILED/ERROR 和代码执行回放

> 仅限受信任的本地开发环境使用。不要暴露到公网。

## Implemented Problems

| ID | Problem | Pattern | Trace Events |
|----|---------|---------|--------------|
| `0001` | Two Sum | array, hash_map | array_read, hash_map_get, hash_map_put, answer_found |
| `0011` | Container With Most Water | two_pointers, greedy | pointer_init, area_compute, best_update, comparison_reason, pointer_move |
| `0206` | Reverse Linked List | linked_list | pointer_init, save_next, link_set, cursor_move |
| `0070` | Climbing Stairs | dynamic_programming | dp_init, dp_read, transition_considered, dp_write |
| `0198` | House Robber | dynamic_programming | dp_init, dp_read, choose_transition, dp_write |

## Visualization Types

| Type | Description | Supported |
|------|-------------|-----------|
| Array + Hash Map | Cell grid with highlighted indices | ✅ |
| Two Pointers | Pointer labels + comparison reasoning | ✅ |
| Linked List Node-Edge | Node boxes + arrow edges + prev/curr/next labels | ✅ |
| DP Table | Cell grid with read (blue) and write (orange) highlights | ✅ |
| Vectorized / NumPy | Operation graph trace | 🔮 design doc only |

> The story animation renderer (`render-story`) turns selected curated traces into spatial animations with moving objects, arrows, and color-coded states. Currently supports Two Sum.
>
> ⚠️ The current story demo is experimental. The long-term direction is lesson-script-driven concept visualization, not trace-driven animation. See [docs/story-vision-realignment.md](docs/story-vision-realignment.md).

## Learner Mode

This project supports two execution modes:

- **Reference Visualization** (`visual_solution.py`): Full semantic trace with step-by-step events. Best for learning the algorithm.
- **Learner Validation** (your own `solution.py`): Runs your code, validates output, reports pass/fail. No fake trace events.

> Learner submissions are checked for disallowed imports (e.g. `os`, `numpy`).
> See [learner-submissions.md](docs/learner-submissions.md) for details.

NumPy is currently not supported. A future `--trace-numpy` mode is described in
[vectorized-trace.md](docs/vectorized-trace.md).

## Core Idea

```text
clean reference solution
        ↓
trace-enabled solution / wrapper
        ↓
structured trace JSON
        ↓
text / HTML / SVG / React visualization
```

先做确定性的 trace，再做渲染器。不要一开始就做完整在线判题平台，也不要让 LLM 直接生成最终动画事实。

## MVP Scope

第一阶段只做：

- Python-first；
- 题目白名单；
- 本地教育型验证器；
- 原创小测试用例；
- trace JSON；
- 文本播放器；
- 后续再加 HTML/SVG 和 React 交互。

## Docs

- [Product Plan](docs/product-plan.md)
- [Harness Plan](docs/harness-plan.md)
- [Trace Schema](docs/trace-schema.md)
- [MVP Problems](docs/mvp-problems.md)
- [Existing Projects Survey](docs/existing-projects-survey.md)
- [Online Judge Notes](docs/online-judge-notes.md)
- [Legal and Licensing Notes](docs/legal-notes.md)
- [Learner Submissions](docs/learner-submissions.md)
- [Vectorized Trace Design](docs/vectorized-trace.md)
- [Public Roadmap](docs/public-roadmap.md)
- [Story Vision Realignment](docs/story-vision-realignment.md)
- [Storyboard Schema](docs/storyboard-schema.md)

## Suggested First 10 Problems

```text
1. Two Sum                         hash map
2. Container With Most Water        two pointers
3. 3Sum                             sorting + two pointers + duplicate skip
4. Reverse Linked List              pointer rewiring
5. Linked List Cycle                fast / slow pointers
6. Climbing Stairs                  1-D DP
7. House Robber                     DP choose / skip ✅
8. Binary Tree Level Order          queue + tree levels
9. Permutations                     backtracking
10. Number of Islands               grid DFS/BFS
```

## Repository Direction

Expected future structure:

```text
programming-visualization/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── docs/
│   ├── harness-plan.md
│   └── ...
├── examples/
│   ├── index.html
│   └── *.html
├── problems/
│   └── 0001_two_sum/
│       ├── problem.json
│       ├── solution.py
│       ├── visual_solution.py
│       ├── cases.json
│       ├── explain.md
│       └── trace.sample.json
├── src/
│   └── pv/
│       ├── harness.py
│       ├── trace_schema.py
│       ├── checkers.py
│       ├── adapters.py
│       ├── structures.py
│       ├── errors.py
│       ├── render_text.py
│       └── cli.py
└── tests/
```

## Non-Affiliation Notice

This project is an independent educational tool for visualizing common programming interview problem patterns.
It is not affiliated with, endorsed by, or sponsored by LeetCode.
All problem summaries, examples, test cases, explanations, traces, and visual assets in this repository are original content.
This project does not copy LeetCode problem statements, official editorials, hidden tests, or paid content.
