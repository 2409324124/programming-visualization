# Existing Projects Survey

This document summarizes project references for `programming-visualization`.

The goal is not to copy an existing project wholesale. The goal is to understand which architectural and product patterns are worth borrowing.

## 1. Summary

Existing resources fall into three broad groups:

1. code execution tracing;
2. data structure and algorithm animation;
3. interview problem learning products.

The strongest conclusion is:

> Do not build a LeetCode clone. Build a trace-first learning engine for LeetCode-style problem patterns.

## 2. Algorithm Visualizer

### What It Is

Algorithm Visualizer is an algorithm visualization platform with a separated architecture: frontend application, algorithm content, and tracer libraries.

### What to Learn

The most important idea is the tracer layer.

Instead of letting the UI inspect arbitrary code directly, algorithm code emits visualization commands through tracer APIs, and the frontend renders those commands.

This maps well to our design:

```text
visual_solution.py
        ↓
trace events
        ↓
renderer
```

### What Not to Copy Blindly

The project is not specifically a LeetCode Hot 100 learning tool. Its UI and content model are more general. Our product should be more focused on `class Solution` execution stories.

## 3. Python Tutor

### What It Is

Python Tutor is the best-known example of code execution visualization. Its important architectural idea is backend execution producing a JSON execution trace, then frontend step-through rendering.

### What to Learn

- execution trace as a first-class artifact;
- step-by-step state playback;
- variable/object visualization;
- frontend/backend separation.

### What to Treat Carefully

Python Tutor-style raw execution tracing can be too low-level for algorithm teaching. This project needs semantic trace events, not just every line and variable change.

Also, license compatibility must be checked before any direct code reuse.

## 4. VisuAlgo

### What It Is

VisuAlgo is a mature algorithm and data-structure teaching site with strong interactive animations.

### What to Learn

- visual language for trees, graphs, heaps, queues, and recursion;
- pacing of educational animations;
- combining animation with explanations and exercises;
- making data structure operations visible.

### What Not to Assume

Do not assume its source code or visual assets can be reused unless a compatible license is confirmed. Treat it primarily as product and pedagogy reference.

## 5. USFCA Data Structure Visualizations

### What It Is

A classic data structure visualization collection with educational animations.

### What to Learn

- linked-list arrow movement;
- tree and heap operation visualization;
- graph traversal visualization;
- clear state transitions for one data structure operation.

### Project Relevance

Useful for visual grammar, especially linked lists, trees, queues, heaps, and graph traversal. Less directly useful for `class Solution` wrappers.

## 6. AlgoMonster and NeetCode

### What They Are

Commercial or productized interview-prep platforms.

### What to Learn

- organizing problems by pattern;
- explaining mental models;
- pacing beginner material;
- mixing written explanations, diagrams, and code;
- productizing interview preparation.

### What Not to Copy

Do not copy problem explanations, examples, images, paid content, UI assets, or platform-specific content.

## 7. Leetcode-Visualizer and Similar Dashboards

### What They Are

Some open-source projects visualize LeetCode progress, category distribution, and difficulty charts.

### What to Learn

- progress dashboards;
- category statistics;
- frontend organization;
- possible future learner analytics.

### Limitation

They do not solve the core problem: visualizing the execution process of a `class Solution`.

## 8. Recursion Tree and DSA Visualizer Projects

### What They Are

Smaller projects that visualize recursion trees, sorting, searching, DP, graph traversal, or data structures.

### What to Learn

- modern frontend patterns;
- recursion tree layout;
- step controls;
- variable panels;
- code highlighting;
- keyboard navigation.

### Limitation

Most are individual demos, not a unified trace schema for many problem families.

## 9. Online Judge Projects

References such as Judge0, DOMjudge, and QingdaoU OnlineJudge show what production online judges need:

- sandboxing;
- resource limits;
- compilation;
- test case execution;
- output comparison;
- special judges/checkers;
- queue/worker systems.

This project should not implement that in v1. It only needs a local educational validator.

## 10. Borrowing Strategy

### Borrow Architecture From

- Algorithm Visualizer: tracer/render split;
- Python Tutor: JSON trace as artifact;
- online judges: case runner and checker concepts.

### Borrow Pedagogy From

- VisuAlgo: animation pacing;
- USFCA: data-structure operation visuals;
- NeetCode / AlgoMonster: pattern-first curriculum organization.

### Borrow UI Ideas From

- modern DSA visualizers;
- recursion tree visualizers;
- progress dashboards.

### Do Not Borrow

- proprietary problem text;
- official editorials;
- paid content;
- platform branding;
- visual assets without permission;
- unlicensed GitHub code.

## 11. Practical Conclusion

The best project shape is:

```text
trace-first engine
+ curated problem packages
+ beginner-readable event messages
+ lightweight renderers
```

The open-source opportunity is not another animation website. It is a reusable educational execution trace layer for classic programming problem patterns.
