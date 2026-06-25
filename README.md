# Programming Visualization

一个面向非科班 / 文科背景 / 自学开发者的 **LeetCode-style 编程可视化学习器**。

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
git clone git@github.com:2409324124/programming-visualization.git
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
```

> 如果不使用 uv，可以用标准 venv：`python3 -m venv .venv && source .venv/bin/activate && pip install -e .`，之后不需要 `uv run` 前缀。

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

## Suggested First 10 Problems

```text
1. Two Sum                         hash map
2. Container With Most Water        two pointers
3. 3Sum                             sorting + two pointers + duplicate skip
4. Reverse Linked List              pointer rewiring
5. Linked List Cycle                fast / slow pointers
6. Climbing Stairs                  1-D DP
7. House Robber                     DP choose / skip
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

This project is an independent educational tool for visualizing common programming interview problem patterns. It is not affiliated with, endorsed by, or sponsored by LeetCode. All lesson summaries, examples, test cases, explanations, traces, and visual assets in this repository are original unless otherwise stated.
