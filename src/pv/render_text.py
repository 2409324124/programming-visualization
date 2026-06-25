"""Render a trace dict as human-readable Chinese text for non-CS learners."""

from __future__ import annotations


_STATUS_CN = {
    "passed": "通过",
    "wrong_answer": "答案错误",
    "running": "运行中",
    "error": "运行错误",
}


def _format_value(v) -> str:
    """Format a value for display, handling common types."""
    if isinstance(v, str):
        return v
    return repr(v)


def _render_header(problem: dict) -> list[str]:
    title = problem.get("display_title", "Unknown")
    pid = problem.get("problem_id", "unknown")
    bar = "═" * 35
    return [
        bar,
        f"Problem: {title} ({pid})",
        bar,
        "",
    ]


def _render_input_summary(run: dict) -> list[str]:
    """Show the input that was used for this run."""
    lines: list[str] = []
    inp = run.get("input")
    if inp:
        parts = [f"{k}={_format_value(v)}" for k, v in inp.items()]
        lines.append(f"输入: {', '.join(parts)}")
        lines.append("")
    return lines


def _render_event(ev: dict) -> list[str]:
    """Render a single trace event."""
    lines: list[str] = []
    step = ev.get("step", "?")
    etype = ev.get("event_type", "unknown")
    lines.append(f"Step {step} | {etype}")

    msg = ev.get("message")
    if msg:
        lines.append(f"  {msg}")

    # Before state
    before = ev.get("before")
    if before and isinstance(before, dict):
        for k, v in before.items():
            lines.append(f"  ⚲ {k}: {_format_value(v)}")

    # After state
    after = ev.get("after")
    if after and isinstance(after, dict):
        for k, v in after.items():
            lines.append(f"  ⚲ {k} → {_format_value(v)}")

    # Highlight info
    highlight = ev.get("highlight")
    if highlight is not None:
        lines.append(f"  ⚲ 高亮: {_format_value(highlight)}")

    # Pedagogy notes
    ped = ev.get("pedagogy")
    if ped and isinstance(ped, dict):
        if "why_now" in ped:
            lines.append(f"  💡 {ped['why_now']}")
        if "mental_model" in ped:
            lines.append(f"  🧠 {ped['mental_model']}")

    lines.append("")
    return lines


def _render_footer(run: dict) -> list[str]:
    """Render the result summary footer."""
    bar = "─" * 31
    lines: list[str] = [bar]

    status = run.get("status", "unknown")
    status_cn = _STATUS_CN.get(status, status)
    lines.append(f"结果: {status_cn}")

    actual = run.get("actual")
    expected = run.get("expected")
    lines.append(f"实际输出: {_format_value(actual)}")
    lines.append(f"预期输出: {_format_value(expected)}")

    if run.get("truncated"):
        lines.append("⚠ 事件被截断（超过上限）")

    lines.append(bar)
    return lines


def render_trace_to_text(trace_dict: dict) -> str:
    """Convert a trace dict to human-readable text.

    Parameters
    ----------
    trace_dict : dict
        A trace envelope as produced by ``TraceBuilder.to_dict()``.

    Returns
    -------
    str
        Multi-line Chinese text suitable for terminal or plain-text display.
    """
    parts: list[str] = []

    # ── Header ──────────────────────────────────────────────────────
    problem = trace_dict.get("problem", {})
    parts.extend(_render_header(problem))

    # ── Input summary ───────────────────────────────────────────────
    run = trace_dict.get("run", {})
    parts.extend(_render_input_summary(run))

    # ── Events ──────────────────────────────────────────────────────
    events = trace_dict.get("events", [])
    if not events:
        parts.append("（无追踪事件）")
        parts.append("")
    else:
        for ev in events:
            parts.extend(_render_event(ev))

    # ── Footer ──────────────────────────────────────────────────────
    parts.extend(_render_footer(run))

    return "\n".join(parts)
