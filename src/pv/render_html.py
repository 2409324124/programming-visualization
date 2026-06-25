"""Render a trace dict as a self-contained static HTML page."""

from __future__ import annotations

import html
import json


CSS = """\
body{font-family:system-ui,-apple-system,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;background:#fafafa}
header{margin-bottom:2rem;padding-bottom:1rem;border-bottom:2px solid #e0e0e0}
header h1{margin:0 0 .3rem;font-size:1.5rem}
header .meta{color:#666;font-size:.9rem}
h2{margin:1.5rem 0 .5rem;font-size:1.1rem;color:#444}
.input-panel{margin-bottom:1.5rem}
.array-row{display:flex;gap:4px;flex-wrap:wrap;margin:.5rem 0}
.array-cell{width:40px;height:40px;display:flex;align-items:center;justify-content:center;border-radius:6px;font-weight:600;font-size:.9rem;background:#e8e8e8;color:#333;transition:background .2s}
.array-cell.hl{background:#ffd54f;color:#333;box-shadow:0 0 0 2px #ff9800}
.step{border-left:3px solid #e0e0e0;padding:.6rem 1rem;margin:.8rem 0;background:#fff;border-radius:0 6px 6px 0;transition:border-color .2s}
.step:hover{border-color:#90caf9}
.step-header{font-weight:600;color:#1565c0;margin-bottom:.2rem}
.step-message{margin-bottom:.4rem}
.state-grid{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin:.4rem 0}
.state-col{background:#f5f5f5;padding:.4rem .6rem;border-radius:4px;font-size:.85rem}
.state-col h4{margin:0 0 .2rem;font-size:.8rem;color:#888;text-transform:uppercase}
.state-kv{display:flex;gap:.3rem;flex-wrap:wrap}
.state-kv span{background:#fff;padding:1px 6px;border-radius:3px;border:1px solid #e0e0e0}
.pedagogy{margin:.3rem 0;padding:.3rem .6rem;border-radius:4px;font-size:.85rem}
.pedagogy.why{background:#e3f2fd;color:#0d47a1}
.pedagogy.model{background:#e8f5e9;color:#1b5e20}
.highlight-tag{display:inline-block;background:#fff3e0;color:#e65100;padding:1px 6px;border-radius:3px;font-size:.8rem;margin-right:4px}
footer{margin-top:2rem;padding:1rem;border-top:2px solid #e0e0e0;text-align:center}
footer .status{font-size:1.1rem;font-weight:700}
footer .status.passed{color:#2e7d32}
footer .status.failed{color:#c62828}
"""

TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _esc(text: str) -> str:
    return html.escape(str(text))


def _format_val(v) -> str:
    if isinstance(v, (list, dict)):
        return _esc(json.dumps(v, ensure_ascii=False))
    return _esc(repr(v))


def _render_header(problem: dict) -> str:
    title = _esc(problem.get("display_title", "Unknown"))
    pid = _esc(problem.get("problem_id", "unknown"))
    tags = ", ".join(problem.get("pattern_tags", []))
    diff = _esc(problem.get("difficulty", "?").upper())
    return f"""\
<header>
  <h1>{title} <small>({pid})</small></h1>
  <div class="meta">标签: {_esc(tags)} &middot; 难度: {diff}</div>
</header>"""


def _render_input_panel(run: dict) -> str:
    inp = run.get("input", {})
    if not inp:
        return ""
    parts: list[str] = ['<section class="input-panel"><h2>输入</h2>']
    for key, val in inp.items():
        if isinstance(val, list) and val and all(isinstance(x, (int, float)) for x in val):
            parts.append(f'<div><strong>{_esc(key)}:</strong></div>')
            parts.append('<div class="array-row">')
            for i, v in enumerate(val):
                parts.append(f'<div class="array-cell" data-idx="{i}">{_esc(v)}</div>')
            parts.append('</div>')
        else:
            parts.append(f'<div><strong>{_esc(key)}:</strong> {_format_val(val)}</div>')
    parts.append('</section>')
    return "\n".join(parts)


def _render_step(ev: dict) -> str:
    step = ev.get("step", "?")
    etype = _esc(ev.get("event_type", "?"))
    msg = _esc(ev.get("message", ""))
    lines: list[str] = [
        f'<div class="step" data-step="{step}">',
        f'  <div class="step-header">Step {step} &middot; {etype}</div>',
        f'  <div class="step-message">{msg}</div>',
    ]
    # before / after grid
    before = ev.get("before")
    after = ev.get("after")
    if before or after:
        lines.append('  <div class="state-grid">')
        lines.append('    <div class="state-col"><h4>before</h4><div class="state-kv">')
        if before and isinstance(before, dict):
            for k, v in before.items():
                lines.append(f'<span>{_esc(k)}={_format_val(v)}</span>')
        lines.append('    </div></div>')
        lines.append('    <div class="state-col"><h4>after</h4><div class="state-kv">')
        if after and isinstance(after, dict):
            for k, v in after.items():
                lines.append(f'<span>{_esc(k)}={_format_val(v)}</span>')
        lines.append('    </div></div>')
        lines.append('  </div>')
    # highlight
    hl = ev.get("highlight")
    if hl:
        lines.append(f'  <div><span class="highlight-tag">高亮: {_format_val(hl)}</span></div>')
    # pedagogy
    ped = ev.get("pedagogy")
    if ped and isinstance(ped, dict):
        if "why_now" in ped:
            lines.append(f'  <div class="pedagogy why">💡 {_esc(ped["why_now"])}</div>')
        if "mental_model" in ped:
            lines.append(f'  <div class="pedagogy model">🧠 {_esc(ped["mental_model"])}</div>')
    lines.append('</div>')
    return "\n".join(lines)


def _render_footer(run: dict) -> str:
    status = run.get("status", "unknown")
    status_cn = {"passed": "通过 ✓", "wrong_answer": "答案错误 ✗", "error": "运行错误 ✗"}.get(status, status)
    css_class = "passed" if status == "passed" else "failed"
    actual = _format_val(run.get("actual"))
    expected = _format_val(run.get("expected"))
    lines = [
        '<footer>',
        f'  <div class="status {css_class}">结果: {_esc(status_cn)}</div>',
        f'  <div>实际: {actual} &middot; 预期: {expected}</div>',
    ]
    if run.get("truncated"):
        lines.append('  <div>⚠ 事件被截断（超过上限）</div>')
    lines.append('</footer>')
    return "\n".join(lines)


def _apply_highlights(html_str: str, events: list[dict]) -> str:
    """Post-process the HTML to add highlight classes using a <script> block.

    The script runs on page load and highlights array cells for the currently
    hovered step based on highlight.indices data embedded in data attributes.
    """
    if not events:
        return html_str
    # Embed highlight data as JSON for the JS to consume
    hl_map: dict[int, list[int]] = {}
    for ev in events:
        step = ev.get("step")
        hl = ev.get("highlight")
        if step and hl and isinstance(hl, dict):
            indices = hl.get("indices", {})
            for obj_key, idx_list in indices.items():
                if obj_key.startswith("arr:") and isinstance(idx_list, list):
                    hl_map.setdefault(step, []).extend(idx_list)
    if not hl_map:
        return html_str
    hl_json = json.dumps(hl_map, ensure_ascii=False)
    script = f"""\
<script>
(function(){{
  var hl={hl_json};
  var steps=document.querySelectorAll('.step');
  var cells=document.querySelectorAll('.array-cell');
  function clear(){{
    for(var i=0;i<cells.length;i++)cells[i].classList.remove('hl');
  }}
  for(var i=0;i<steps.length;i++){{
    steps[i].addEventListener('mouseenter',function(){{
      clear();
      var s=parseInt(this.getAttribute('data-step'));
      var idxs=hl[s];
      if(idxs)for(var j=0;j<idxs.length;j++){{
        var c=document.querySelector('.array-cell[data-idx="'+idxs[j]+'"]');
        if(c)c.classList.add('hl');
      }}
    }});
    steps[i].addEventListener('mouseleave',clear);
  }}
}})();
</script>"""
    return html_str.replace("</body>", script + "\n</body>")


def render_trace_to_html(trace_dict: dict) -> str:
    """Convert a trace dict to a self-contained HTML page.

    Parameters
    ----------
    trace_dict : dict
        A trace envelope as produced by ``TraceBuilder.to_dict()``.

    Returns
    -------
    str
        Complete HTML document as a string.
    """
    problem = trace_dict.get("problem", {})
    run = trace_dict.get("run", {})
    events = trace_dict.get("events", [])

    title = _esc(problem.get("display_title", "Program Trace"))
    body_parts: list[str] = [
        _render_header(problem),
        _render_input_panel(run),
        '<section class="timeline"><h2>执行过程</h2>',
    ]
    if not events:
        body_parts.append('<p>（无追踪事件）</p>')
    else:
        for ev in events:
            body_parts.append(_render_step(ev))
    body_parts.append('</section>')
    body_parts.append(_render_footer(run))

    html_str = TEMPLATE.format(css=CSS, title=title, body="\n".join(body_parts))
    html_str = _apply_highlights(html_str, events)
    return html_str
