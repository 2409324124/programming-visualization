# Product Plan: Programming Visualization

## 1. Product Positioning

`programming-visualization` is an open-source learning tool for visualizing LeetCode-style interview problems.

The primary learner is not a competitive programmer. The primary learner is a self-taught, non-CS, or liberal-arts-background developer who can read Python syntax, but struggles to understand what actually happens during classic algorithm execution.

The core promise is:

> Turn a `class Solution` into an understandable execution story.

The project should help learners see:

- how pointers move;
- how a hash map changes;
- how linked-list arrows are cut and reconnected;
- how a queue or stack changes over time;
- how a DP table is filled;
- how recursion expands and returns;
- how backtracking chooses, recurses, and undoes choices;
- how BFS/DFS explores a graph or grid.

## 2. What Makes This Project Different

The market already has many resources for picking problems, reading solutions, and watching fixed animations. The missing piece is a reusable execution trace layer for LeetCode-style `class Solution` code.

This project should not compete by being another problem list or editorial site. It should compete by making execution state visible and explainable.

## 3. Non-Goals

This project is not:

- a LeetCode mirror;
- a scraping project;
- a replacement for LeetCode submissions;
- a production online judge;
- a hidden-test system;
- a leaderboard or competitive platform;
- a generic browser-based arbitrary-code sandbox in v1.

## 4. Core Architecture

The recommended architecture is:

```text
clean reference solution
        ↓
trace-enabled solution / wrapper
        ↓
structured trace JSON
        ↓
text / HTML / SVG / React renderer
```

The key design principle is to separate **execution truth** from **visual presentation**.

Execution truth should come from deterministic Python code and trace events. Visual explanations, UI panels, and optional LLM-generated wording should sit on top of that fact layer.

## 5. Product Modes

### 5.1 Reference Lesson Mode

The first mode should visualize curated reference solutions.

This is the MVP mode. It avoids the hard problem of supporting arbitrary learner code and lets the project focus on pedagogy.

### 5.2 Local Educational Judge Mode

The second mode should run small, visible local test cases.

It should report:

- expected output;
- actual output;
- pass/fail;
- trace events;
- final state;
- common-mistake warning if available.

Unlike LeetCode, failures should be visible and explainable, not hidden.

### 5.3 Learner Submission Mode

This should come later. Initially it can only check outputs. Full visualization of arbitrary learner code is not required for v1.

## 6. MVP Scope

The MVP should be a Python-first local tool.

Required features:

- load a problem folder;
- run a configured `Solution` method;
- load small local cases from JSON;
- compare output with expected output or a custom checker;
- collect deterministic trace events;
- print a readable text playback;
- save trace JSON.

Optional v1.1 feature:

- export a simple static HTML/SVG playback.

Out of scope for MVP:

- React frontend;
- user accounts;
- cloud sandbox;
- online judge queue;
- scraping problem statements;
- supporting every possible user solution style.

## 7. Suggested User Flow

```bash
python -m pv run problems/0001_two_sum --case 0
```

Output should show:

```text
Problem: Two Sum / Hash complement lookup
Case: basic small array
Status: passed

Step 1: Read nums[0] = 2
Step 2: Need complement 7, but it is not in seen map
Step 3: Store 2 -> index 0 in seen map
Step 4: Read nums[1] = 7
Step 5: Need complement 2, found it at index 0
Step 6: Return [0, 1]

Trace saved to: problems/0001_two_sum/trace.case0.json
```

## 8. Educational Design Principles

Every visualization step should answer three questions:

1. What changed?
2. Why did it change?
3. What should a beginner notice?

Avoid messages like:

```text
Apply complement lookup in O(n).
```

Prefer messages like:

```text
Current value is 7. To reach target 9, we need a previous value 2. The map says 2 was seen at index 0.
```

## 9. Development Phases

### Phase 0: Documentation and Schema

- write `docs/trace-schema.md`;
- define object IDs and event vocabulary;
- define problem folder contract;
- define local case format.

### Phase 1: CLI MVP

- implement `src/pv/trace_schema.py`;
- implement `src/pv/harness.py`;
- implement `src/pv/render_text.py`;
- implement `problems/0001_two_sum` end to end.

### Phase 2: Four Core Mental Models

Add one representative problem for each:

- hash map: Two Sum;
- two pointers: Container With Most Water;
- linked list: Reverse Linked List;
- dynamic programming: Climbing Stairs or House Robber.

### Phase 3: Static HTML/SVG Renderer

Add visual rendering for:

- arrays;
- hash maps;
- pointers;
- linked-list arrows;
- DP table cells;
- event timeline.

### Phase 4: 10-Problem MVP Curriculum

Complete the 10 selected problems in `docs/mvp-problems.md`.

### Phase 5: Interactive Frontend

Only after the trace schema stabilizes:

- React app;
- timeline slider;
- step controls;
- code highlighting;
- state inspector;
- optional React Flow for linked lists, trees, and graphs.

## 10. Product Success Criteria

The MVP is successful when a learner can open a small example, step through it, and say:

> I finally understand what moved, what changed, and why.

Engineering success means:

- trace JSON is deterministic;
- renderer output is reproducible;
- each problem has original lesson content;
- local tests pass;
- common mistakes are documented;
- the project does not depend on copied LeetCode content.
