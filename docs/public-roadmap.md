# Public Roadmap

## Completed

| Feature | Status | Example |
|---------|--------|---------|
| array + hash map trace | ✅ | 0001 Two Sum |
| two pointers trace | ✅ | 0011 Container With Most Water |
| linked list node-edge trace | ✅ | 0206 Reverse Linked List |
| DP table trace | ✅ | 0070 Climbing Stairs |
| learner submission import policy | ✅ | `submission_policy.py` |
| text renderer | ✅ | `render_text.py` |
| HTML renderer (array, linked list, DP table) | ✅ | `render_html.py` |
| CI (GitHub Actions) | ✅ | `.github/workflows/ci.yml` |

## Next Steps

| Priority | Task | Notes |
|----------|------|-------|
| next | 0198 House Robber | DP choose/skip transition |
| next | tree adapter + binary tree level-order | TreeNode adapter + queue events |
| next | graph/grid: Number of Islands | grid DFS/BFS with component tracing |
| later | backtracking: Permutations | choose/recurse/unchoose events |

## Future

| Area | Status | Notes |
|------|--------|-------|
| vectorized trace adapter | design doc | `docs/vectorized-trace.md` |
| interactive React frontend | not started | after trace format stable |
| Manim video export | not started | optional |
