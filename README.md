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
├── docs/
├── problems/
│   └── 0001_two_sum/
│       ├── solution.py
│       ├── visual_solution.py
│       ├── cases.json
│       ├── explain.md
│       └── trace.sample.json
├── src/
│   └── pv/
│       ├── harness.py
│       ├── trace_schema.py
│       ├── render_text.py
│       └── render_html.py
├── examples/
└── tests/
```

## Non-Affiliation Notice

This project is an independent educational tool for visualizing common programming interview problem patterns. It is not affiliated with, endorsed by, or sponsored by LeetCode. All lesson summaries, examples, test cases, explanations, traces, and visual assets in this repository are original unless otherwise stated.
