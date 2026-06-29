# Agent Handoff

Updated: 2026-06-29

This file is the short, current-state handoff for OpenCode session rollover. Keep it concise. Long history belongs in `docs/agent-session-log.md` if that file is created later.

## Current branch

```text
main
```

## Current status snapshot

Refresh this section before switching windows:

```bash
git status --short --branch
git log --oneline -8 --decorate
```

Latest known stable baseline:

```text
main has render-code and runtime-bound render-visual merged.
0198 House Robber has been added with DP choose/skip trace and render-html demo.
AGENTS.md contains the OpenCode Session Rollover Protocol.
```

## Project invariants

Do not violate these while continuing work:

1. `harness.run_case()` is the only execution/checking path for running solutions.
2. Do not write a second checker/import/execute pipeline.
3. Do not fake trace events.
4. `render-code` is a line-level learner code execution viewer.
5. `render-visual` is official lesson + runtime-bound concept visualization.
6. `render-story` / `render-lesson` are legacy or experimental surfaces.
7. HTML must remain self-contained, with no CDN.
8. UI/HTML changes need visual review, not only unit tests.

## Current phase

Phase 5.x — Runtime-bound visualization and learner code viewer stabilization.

Completed major milestones:

- `render-visual` now binds official lessons to real harness runtime facts.
- `visual_runtime.py` delegates to `harness.run_case()`.
- `render-code` exists for user `solution.py` line-level execution viewing.
- `learner_trace.py` uses `sys.settrace` for target method tracing.
- `learner_runtime.py` wraps harness execution with line-level trace collection.
- `render_learner_html.py` generates the code execution viewer.
- Demo gallery includes runtime-bound and code-viewer demos.
- `0198_house_robber` adds the fifth problem and uses DP choose/skip semantic events.

## Current task

Before starting a new feature, verify the repo state and current UI baseline.

Recommended startup commands:

```bash
git status --short --branch
git log --oneline -8 --decorate
uv run python -m unittest discover -s tests -v
```

If touching HTML / UI / renderer, regenerate demos:

```bash
uv run python -m pv render-code problems/0001_two_sum \
  --case-index 0 \
  --output examples/code_0001_two_sum.case0.html

uv run python -m pv render-visual problems/0001_two_sum \
  --case-index 0 \
  --lesson problems/0001_two_sum/lesson.story.json \
  --output examples/visual_0001_two_sum.case0.html
```

Then inspect or request `mimo-2.5-pro` visual review.

## Known fragile areas

1. `render-code` must show real control flow, including loops jumping back to earlier lines.
2. Do not force final cursor to the bottom if the function returns early.
3. Return events should look different from normal line events.
4. Skipped/not-executed code should not be confused with executed code, but do not alter code semantics.
5. Any UI change that only passes tests may still be visually bad.

## Do-not-repeat mistakes

- Do not reintroduce a second executor outside `harness.run_case()`.
- Do not make `render-visual` depend on authored fake values.
- Do not make `render-code` draw fake algorithm animations.
- Do not decide HTML quality without a screenshot/visual review.
- Do not wait until 300k context to write handoff notes.

## Visual review status

See `docs/visual-review.md` for the latest UI-specific notes.

When updating this file, copy the newest visual conclusion here in one sentence.

Current summary:

```text
House Robber render-html demo passed screenshot review on 2026-06-29; future UI changes still require visual review.
```

## Next action template

Replace this with the exact next instruction before switching sessions:

```text
Next action:
1. Read AGENTS.md, README.md, docs/public-roadmap.md, docs/agent-handoff.md, and docs/visual-review.md.
2. Run git status and latest tests.
3. Continue from roadmap next items: tree adapter + binary tree level-order, or graph/grid Number of Islands.
```
