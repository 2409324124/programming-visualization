# Visual Review Log

This file records UI / HTML / visualization review results. It exists because the primary coding model may not have vision, so visual correctness must be externalized.

Use this for changes touching:

- `examples/*.html`
- `examples/index.html`
- `src/pv/render_*.py`
- `src/pv/*compiler.py` layout or frame output
- `render-code`, `render-visual`, `render-story`, `render-lesson`

## Review protocol

Before marking a UI task complete:

1. Run the unit tests.
2. Regenerate relevant HTML demos.
3. Open the pages locally or via Pages.
4. Send screenshots to `mimo-2.5-pro` or perform explicit human visual review.
5. Record the conclusion here.

Minimum commands for the current demos:

```bash
uv run python -m unittest discover -s tests -v

uv run python -m pv render-code problems/0001_two_sum \
  --case-index 0 \
  --output examples/code_0001_two_sum.case0.html

uv run python -m pv render-visual problems/0001_two_sum \
  --case-index 0 \
  --lesson problems/0001_two_sum/lesson.story.json \
  --output examples/visual_0001_two_sum.case0.html
```

## Review template

```md
## YYYY-MM-DD — <page or task>

Page:
`examples/...html`

Reviewer:
`mimo-2.5-pro` / human

Result:
PASS / NEEDS_FIX / FAIL

Findings:
- P0: ...
- P1: ...
- P2: ...

Fixed:
- ...

Remaining:
- ...

Next:
- ...
```

## 2026-06-27 — render-code viewer polish

Page:
`examples/code_0001_two_sum.case0.html`

Reviewer:
human screenshots + iterative user feedback

Result:
NEEDS_FIX previously; current baseline believed usable after follow-up fixes, but any new UI change still requires a fresh screenshot review.

Findings from recent screenshots:

- Return state must not look like a normal blue execution cursor.
- Return state should use a block-like highlight and a clear `RETURNED HERE` badge.
- The final step should remain on the real return line, not be faked to the bottom of the function.
- Code below an early return may be marked `not executed`, but the code text should remain visually consistent with normal code unless the user explicitly wants it muted.
- `not executed` should be a status badge, not a change to the code font.

Do-not-repeat:

- Do not force Two Sum to highlight `return []` when line 7 returned.
- Do not record module/class definition as learner runtime steps.
- Do not use a full-row strip if the user wants a code-block execution marker.
- Do not let tests replace visual review.

Next visual review should check:

- Is `RETURNED HERE` clearly attached to the return statement?
- Is the code-block highlight block-like rather than a long cursor strip?
- Do skipped lines keep consistent code font/color if that is the current user preference?
- Are controls visible at common zoom levels?

## 2026-06-27 — local LeetCode-style runner

Page:
`http://127.0.0.1:8765/`

Reviewer:
`failure-fix-agent` using real browser (`agent-browser` / Chromium CDP)

Viewport:
1280×577

Result:
PASS

Screenshots:

- Initial: `/tmp/pv_serve_initial.png`
- After Run: `/tmp/pv_serve_result.png`

Findings:

- LeetCode-style runner feel: PASS
- Code input clarity: PASS
- Problem / Case / Run clarity: PASS
- Result status clarity: PASS
- actual / expected clarity: PASS
- Execution Viewer embedding: PASS
- Code viewer readability: PASS
- User flow clarity: PASS
- Layout / overflow: PASS
- Misleading realtime / streaming wording: PASS

Issues:

- P0: none
- P1: none
- P2: none

Recommendation:

Commit with message: `feat: add local LeetCode-style code runner with split-panel UI and execution viewer`

## 2026-06-29 — House Robber render-html demo

Page:
`examples/0198_house_robber.case0.html`

Reviewer:
Codex via `agent-browser` screenshot review

Screenshot:
`/tmp/pv_house_robber_case0_full.png`

Result:
PASS

Findings:

- P0: none
- P1: none
- P2: generic highlight metadata is still shown as raw JSON, inherited from the existing trace renderer.

Fixed:

- Reordered House Robber cases so case 0 demonstrates the full choose/skip DP flow instead of the single-house boundary case.
- Regenerated `trace.case0.json`, `trace.sample.json`, and `examples/0198_house_robber.case0.html`.

Remaining:

- Optional future polish: render highlight metadata as friendly labels instead of raw JSON.

Next:

- Run the full unittest suite before final handoff.

## 2026-06-29 — render-code replay control

Page:
`examples/code_0001_two_sum.case0.html`

Reviewer:
Codex via `agent-browser` DOM verification

Result:
PASS

Findings:

- P0: none
- P1: none
- P2: none

Fixed:

- Play now restarts from the beginning when clicked after execution has reached the final step.

Verification:

- First playback reached `10 / 10`.
- Clicking Play again advanced from the restarted run to `1 / 10`.

Remaining:

- none

Next:

- Run the full unittest suite before final handoff.
