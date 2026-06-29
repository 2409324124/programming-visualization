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
.ll-diagram{display:flex;align-items:center;gap:0;margin:1rem 0;overflow-x:auto;padding:.5rem 0}
.ll-node{width:48px;height:48px;display:flex;align-items:center;justify-content:center;border:2px solid #90caf9;border-radius:8px;background:#e3f2fd;font-weight:700;font-size:.9rem;position:relative;flex-shrink:0}
.ll-node.hl{background:#ffd54f;border-color:#ff9800;box-shadow:0 0 0 3px #ff9800}
.ll-arrow{width:32px;height:2px;background:#bbb;position:relative;flex-shrink:0}
.ll-arrow::after{content:'';position:absolute;right:-4px;top:-5px;border:6px solid transparent;border-left:8px solid #bbb}
.ll-arrow.hl{background:#ff9800}
.ll-arrow.hl::after{border-left-color:#ff9800}
.ll-label{position:absolute;top:-22px;font-size:.7rem;color:#888;white-space:nowrap;left:50%;transform:translateX(-50%)}
.ll-null{width:48px;height:48px;display:flex;align-items:center;justify-content:center;border:2px dashed #ccc;border-radius:8px;color:#999;font-size:.8rem;flex-shrink:0}
.dp-table{display:flex;gap:4px;flex-wrap:wrap;margin:1rem 0;align-items:flex-end}
.dp-cell{width:52px;min-height:56px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;border:2px solid #e0e0e0;border-radius:6px;background:#fafafa;padding:4px;transition:all .2s}
.dp-cell .dp-idx{font-size:.7rem;color:#999;margin-bottom:2px}
.dp-cell .dp-house{font-size:.68rem;color:#777;margin-bottom:2px}
.dp-cell .dp-val{font-weight:700;font-size:.95rem;color:#333;min-height:20px}
.dp-cell.hl-read{background:#e3f2fd;border-color:#42a5f5;box-shadow:0 0 0 2px #90caf9}
.dp-cell.hl-write{background:#fff3e0;border-color:#ff9800;box-shadow:0 0 0 2px #ffb74d}
.dp-cell.filled{background:#e8f5e9;border-color:#66bb6a}
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


def _render_linked_list_input(key: str, vals: list) -> str:
    """Render a linked list as a horizontal node-edge diagram."""
    parts: list[str] = [f'<div><strong>{_esc(key)}:</strong></div>']
    parts.append('<div class="ll-diagram">')
    for i, v in enumerate(vals):
        if i > 0:
            parts.append('<div class="ll-arrow"></div>')
        parts.append(f'<div class="ll-node" data-ll-idx="{i}">{_esc(v)}</div>')
    # null sentinel
    parts.append('<div class="ll-arrow"></div>')
    parts.append('<div class="ll-null">None</div>')
    parts.append('</div>')
    return "\n".join(parts)


def _render_dp_table(problem: dict, run: dict, events: list[dict]) -> str:
    """Render a DP table visualization for dynamic-programming problems.

    Supports two common educational DP shapes:
    - scalar ``n`` input: renders ``n+1`` cells, used by Climbing Stairs.
    - array ``nums`` input: renders one DP cell per input value, used by
      House Robber.
    """
    inp = run.get("input", {})
    n = inp.get("n")
    nums = inp.get("nums")
    is_n_table = isinstance(n, int) and n >= 0
    is_nums_table = (
        isinstance(nums, list)
        and len(nums) > 0
        and all(isinstance(x, (int, float)) for x in nums)
    )
    if not is_n_table and not is_nums_table:
        return ""
    cell_count = n + 1 if is_n_table else len(nums)

    # Determine final dp state from events (dp_write events)
    filled: dict[int, int | float] = {0: 1, 1: 1} if is_n_table else {}
    for ev in events:
        before = ev.get("before") or {}
        after = ev.get("after") or {}
        # Look for dp_write events that have explicit index info
        if ev.get("event_type") in ("update_dp", "dp_write"):
            idx = after["dp_idx"] if "dp_idx" in after else before.get("dp_idx")
            if "dp" in after:
                val = after["dp"]
            elif "dp_val" in after:
                val = after["dp_val"]
            else:
                val = None
            if isinstance(idx, int) and val is not None:
                filled[idx] = val

    parts: list[str] = ['<div><strong>DP 表:</strong></div>']
    parts.append('<div class="dp-table">')
    for i in range(cell_count):
        val = filled.get(i)
        val_html = _esc(val) if val is not None else ""
        cls = "dp-cell filled" if val is not None else "dp-cell"
        house_html = ""
        if is_nums_table:
            house_html = f'<span class="dp-house">房屋金额 {_esc(nums[i])}</span>'
        parts.append(
            f'<div class="{cls}" data-dp-idx="{i}">'
            f'<span class="dp-idx">{i}</span>'
            f'{house_html}'
            f'<span class="dp-val">{val_html}</span>'
            f'</div>'
        )
    parts.append('</div>')
    return "\n".join(parts)


def _render_input_panel(run: dict, problem: dict | None = None,
                        events: list[dict] | None = None) -> str:
    inp = run.get("input", {})
    if not inp:
        return ""
    is_linked_list = problem is not None and "linked_list" in problem.get("pattern_tags", [])
    is_dp = (problem is not None
             and "dynamic_programming" in problem.get("pattern_tags", []))
    parts: list[str] = ['<section class="input-panel"><h2>输入</h2>']
    for key, val in inp.items():
        if isinstance(val, list) and val and all(isinstance(x, (int, float)) for x in val):
            if is_linked_list:
                parts.append(_render_linked_list_input(key, val))
            else:
                parts.append(f'<div><strong>{_esc(key)}:</strong></div>')
                parts.append('<div class="array-row">')
                for i, v in enumerate(val):
                    parts.append(f'<div class="array-cell" data-idx="{i}">{_esc(v)}</div>')
                parts.append('</div>')
        else:
            parts.append(f'<div><strong>{_esc(key)}:</strong> {_format_val(val)}</div>')
    # DP table visualization
    if is_dp and events is not None:
        parts.append(_render_dp_table(problem, run, events))
    elif is_dp:
        parts.append(_render_dp_table(problem, run, []))
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

    The script runs on page load and highlights array cells, linked-list
    nodes, and DP table cells for the currently hovered step based on
    highlight.indices data embedded in data attributes.

    Supported index prefixes:
    - ``arr:``      → highlights ``.array-cell[data-idx="N"]``
    - ``ll:``       → highlights ``.ll-node[data-ll-idx="N"]``
    - ``dp:table``  → highlights ``.dp-cell[data-dp-idx="N"]``
                       (all but last index → hl-read, last index → hl-write)
    """
    if not events:
        return html_str
    # Collect per-step highlight indices, keyed by target type
    arr_hl: dict[int, list[int]] = {}
    ll_hl: dict[int, list[int]] = {}
    dp_hl: dict[int, list[int]] = {}
    for ev in events:
        step = ev.get("step")
        hl = ev.get("highlight")
        if step and hl and isinstance(hl, dict):
            indices = hl.get("indices", {})
            for obj_key, idx_list in indices.items():
                if not isinstance(idx_list, list):
                    continue
                if obj_key.startswith("arr:"):
                    arr_hl.setdefault(step, []).extend(idx_list)
                elif obj_key.startswith("ll:"):
                    ll_hl.setdefault(step, []).extend(idx_list)
                elif obj_key == "dp:table":
                    dp_hl.setdefault(step, []).extend(idx_list)
    if not arr_hl and not ll_hl and not dp_hl:
        return html_str
    arr_json = json.dumps(arr_hl, ensure_ascii=False)
    ll_json = json.dumps(ll_hl, ensure_ascii=False)
    dp_json = json.dumps(dp_hl, ensure_ascii=False)
    script = f"""\
<script>
(function(){{
  var arrHl={arr_json};
  var llHl={ll_json};
  var dpHl={dp_json};
  var steps=document.querySelectorAll('.step');
  var cells=document.querySelectorAll('.array-cell');
  var nodes=document.querySelectorAll('.ll-node');
  var dpCells=document.querySelectorAll('.dp-cell');
  function clear(){{
    for(var i=0;i<cells.length;i++)cells[i].classList.remove('hl');
    for(var i=0;i<nodes.length;i++)nodes[i].classList.remove('hl');
    for(var i=0;i<dpCells.length;i++)dpCells[i].classList.remove('hl-read','hl-write');
  }}
  for(var i=0;i<steps.length;i++){{
    steps[i].addEventListener('mouseenter',function(){{
      clear();
      var s=parseInt(this.getAttribute('data-step'));
      var aIdxs=arrHl[s];
      if(aIdxs)for(var j=0;j<aIdxs.length;j++){{
        var c=document.querySelector('.array-cell[data-idx="'+aIdxs[j]+'"]');
        if(c)c.classList.add('hl');
      }}
      var lIdxs=llHl[s];
      if(lIdxs)for(var j=0;j<lIdxs.length;j++){{
        var n=document.querySelector('.ll-node[data-ll-idx="'+lIdxs[j]+'"]');
        if(n)n.classList.add('hl');
      }}
      var dIdxs=dpHl[s];
      if(dIdxs){{
        for(var j=0;j<dIdxs.length;j++){{
          var dc=document.querySelector('.dp-cell[data-dp-idx="'+dIdxs[j]+'"]');
          if(dc){{
            if(j<dIdxs.length-1)dc.classList.add('hl-read');
            else dc.classList.add('hl-write');
          }}
        }}
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
        _render_input_panel(run, problem, events),
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
