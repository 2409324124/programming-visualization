# MVP Problems

The first curriculum should cover the most painful mental models for non-CS learners.

Do not implement 100 problems first. Implement 10 representative problems that prove the trace schema can handle the major patterns.

## Recommended Learning Order

```text
1. Two Sum
2. Container With Most Water
3. 3Sum
4. Reverse Linked List
5. Linked List Cycle
6. Climbing Stairs
7. House Robber
8. Binary Tree Level Order Traversal
9. Permutations
10. Number of Islands
```

This order starts with arrays and maps, then pointer movement, linked-list rewiring, DP state meaning, tree queues, backtracking, and graph/grid traversal.

## 1. Two Sum

### Pattern

Array + hash map.

### What to Visualize

- current index `i`;
- current value `num`;
- complement `target - num`;
- hash map before and after update;
- final answer indices.

### Core Events

- `array_read`
- `hash_map_get`
- `hash_map_put`
- `answer_found`
- `return`

### Beginner Pain Points

- Why not use two nested loops?
- Why store value to index?
- Why usually check complement before inserting current value?
- Is the map storing numbers or positions?

### MVP Renderer Need

Array cells + hash-map panel + explanation timeline.

## 2. Container With Most Water

### Pattern

Two pointers + greedy reasoning.

### What to Visualize

- left pointer;
- right pointer;
- current width;
- current height limit;
- current area;
- best area so far;
- reason for moving the shorter side.

### Core Events

- `pointer_init`
- `comparison_reason`
- `best_update`
- `pointer_move`

### Beginner Pain Points

- Why move the shorter side?
- Why does shrinking width not necessarily lose the answer?
- Why not try all pairs?

### MVP Renderer Need

Array bars + left/right pointer labels + area/best panel.

## 3. 3Sum

### Pattern

Sorting + anchor index + two pointers + duplicate skipping.

### What to Visualize

- sorted array;
- anchor `i`;
- left/right pointers;
- current triple;
- current sum;
- duplicate skips;
- collected answers.

### Core Events

- `array_sort`
- `anchor_set`
- `pointer_move`
- `comparison_reason`
- `duplicate_skip`
- `answer_found`

### Beginner Pain Points

- Why sort first?
- Why does two-pointer search work after sorting?
- Why are there multiple duplicate-skip positions?
- Why is anchor de-dup different from inner pointer de-dup?

### MVP Renderer Need

Sorted array + anchor/left/right labels + answer list panel.

## 4. Reverse Linked List

### Pattern

Linked-list pointer rewiring.

### What to Visualize

- `prev`;
- `curr`;
- saved `next_temp`;
- original `curr.next` edge;
- new reversed edge;
- head update at the end.

### Core Events

- `pointer_follow`
- `link_cut`
- `link_set`
- `cursor_move`
- `head_update`

### Beginner Pain Points

- Why save `next` before changing `curr.next`?
- Why does changing an arrow not copy nodes?
- Why does `prev` become the new head?
- Why does the old head eventually point to `None`?

### MVP Renderer Need

Node boxes + arrow edges + pointer labels.

## 5. Linked List Cycle

### Pattern

Fast/slow pointers.

### What to Visualize

- slow pointer movement by 1;
- fast pointer movement by 2;
- null checks;
- meeting check;
- cycle construction note if a case uses `pos` metadata.

### Core Events

- `pointer_init`
- `pointer_move`
- `meeting_check`
- `return`

### Beginner Pain Points

- Why does fast eventually meet slow if there is a cycle?
- Why must we check `fast` and `fast.next`?
- Why is `pos` not a real method parameter in some serialized examples?

### MVP Renderer Need

Linked-list graph + slow/fast labels + step counter.

## 6. Climbing Stairs

### Pattern

1-D DP / recurrence.

### What to Visualize

- state meaning: `dp[i]` = ways to reach step `i`;
- base cases;
- transition `dp[i] = dp[i - 1] + dp[i - 2]`;
- optional rolling variables.

### Core Events

- `dp_init`
- `dp_read`
- `transition_considered`
- `dp_write`
- `rolling_update`
- `return`

### Beginner Pain Points

- What does `dp[i]` mean?
- Why does the recurrence add two previous states?
- Why can it be optimized to two variables?

### MVP Renderer Need

DP table + highlighted read cells + write cell.

## 7. House Robber

### Pattern

1-D DP with choose/skip transition.

### What to Visualize

- house values;
- `rob_this = nums[i] + dp[i - 2]`;
- `skip_this = dp[i - 1]`;
- chosen max;
- full table or rolling variables.

### Core Events

- `dp_init`
- `dp_read`
- `transition_considered`
- `dp_write`
- `best_update`
- `return`

### Beginner Pain Points

- `dp[i]` does not mean "must rob house i".
- Why compare rob vs skip?
- Why does robbing current house look back two steps?

### MVP Renderer Need

House row + DP row + decision panel.

## 8. Binary Tree Level Order Traversal

### Pattern

Tree + queue + BFS levels.

### What to Visualize

- tree nodes;
- queue contents;
- current level boundary;
- visited node;
- children enqueued;
- output list per level.

### Core Events

- `queue_layer_start`
- `dequeue`
- `tree_visit`
- `child_enqueue`
- `queue_layer_end`

### Beginner Pain Points

- Why use a queue?
- Why save current queue length before processing a level?
- Why is this different from DFS?

### MVP Renderer Need

Tree view + queue panel + level output panel.

## 9. Permutations

### Pattern

Backtracking.

### What to Visualize

- recursion tree;
- current `path`;
- `used[]` flags;
- choose;
- recurse;
- emit solution;
- unchoose/backtrack.

### Core Events

- `choose`
- `call`
- `solution_emit`
- `unchoose`
- `backtrack`
- `return`

### Beginner Pain Points

- Why undo after recursion?
- Why `path` changes over time?
- Why `used[]` is necessary?
- Why recursion explores a tree of choices?

### MVP Renderer Need

Path panel + used flags + simple recursion tree or call stack.

## 10. Number of Islands

### Pattern

Grid traversal + connected components.

### What to Visualize

- grid cells;
- land/water/visited state;
- current island/component;
- DFS stack or BFS queue;
- neighbor checks;
- island count.

### Core Events

- `component_start`
- `discover`
- `mark_visited`
- `frontier_add`
- `frontier_remove`
- `neighbor_check`
- `component_end`

### Beginner Pain Points

- What is a connected component?
- When should a cell become visited?
- Why are we not finding all paths?
- How do DFS and BFS differ here?

### MVP Renderer Need

Grid view + stack/queue panel + island counter.

## MVP Completion Definition

The 10-problem MVP is complete when every problem has:

- `solution.py`;
- `visual_solution.py`;
- `cases.json`;
- `lesson.md` or `explain.md`;
- `trace.sample.json`;
- at least one renderer that shows the key state transitions;
- tests that assert key event types appear in the trace.
