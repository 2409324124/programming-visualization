# Agent Session Log

Append longer historical notes here when a session ends. Keep `docs/agent-handoff.md` short and current; move older context into this file.

## Format

````md
## YYYY-MM-DD — <short title>

Branch:
`main` / `<branch>`

Context:
- ...

Completed:
- ...

Tests:
```bash
...
```

Visual review:
- ...

Follow-up:
- ...
````

## 2026-06-27 — Rollover protocol added

Branch:
`main`

Context:
- OpenCode does not support reliable context-window compression.
- The user wants to switch sessions before the context reaches around 300k.
- The project now externalizes current state through repo documents instead of relying on model memory.

Completed:
- Added an OpenCode Session Rollover Protocol section to `AGENTS.md`.
- Added `docs/agent-handoff.md` as the short current-state handoff file.
- Added `docs/visual-review.md` as the UI/HTML visual review record.
- Added this append-only `docs/agent-session-log.md` for older handoff history.

Follow-up:
- Before each future window switch, update `docs/agent-handoff.md` with exact status and next action.
- When UI changes, update `docs/visual-review.md` after screenshot review.
