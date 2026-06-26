"""render_learner_html.py — Render learner code execution as self-contained HTML."""

import html
import json


def render_learner_to_html(runtime: dict) -> str:
    """Generate a self-contained HTML code execution viewer."""

    title = html.escape(runtime.get("problem_id", "Code Viewer"))
    source = runtime.get("source_code", "")
    source_lines = source.split("\n")
    while source_lines and not source_lines[-1].strip():
        source_lines.pop()
    line_trace = runtime.get("line_trace", [])
    passed = runtime.get("passed", False)
    actual = runtime.get("actual")
    expected = runtime.get("expected")
    stdout = runtime.get("stdout", "")
    stderr = runtime.get("stderr", "")
    error = runtime.get("error", "")
    truncated = runtime.get("truncated", False)
    total_steps = runtime.get("total_steps", 0)

    step_linenos = {}
    step_etype = {}
    step_return_val = {}
    for ev in line_trace:
        s = ev.get("step", 0)
        ln = ev.get("lineno", 0)
        if s not in step_linenos:
            step_linenos[s] = []
        if ln not in step_linenos[s]:
            step_linenos[s].append(ln)
        step_etype[s] = ev.get("event_type", "line")
        if ev.get("return_value_summary"):
            step_return_val[s] = ev.get("return_value_summary")

    step_locals = {}
    for ev in line_trace:
        step_locals[ev.get("step", 0)] = ev.get("locals_summary", "")

    return_lineno = 0
    for ev in reversed(line_trace):
        if ev.get("event_type") == "return":
            return_lineno = ev.get("lineno", 0)
            break

    code_html_lines = []
    for i, line in enumerate(source_lines):
        ln = i + 1
        skipped = return_lineno > 0 and ln > return_lineno
        skipped_attr = ' data-skipped="1"' if skipped else ""
        badge = '<span class="event-badge">RETURNED HERE</span>' if ln == return_lineno else ""
        blank = not line.strip()
        skipped_tag = '<span class="skip-badge">not executed</span>' if (skipped and not blank) else ""
        code_html_lines.append(
            '<div class="code-line" data-ln="{}"{}>'.format(ln, skipped_attr)
            + '<span class="ln">{}</span>'.format(ln)
            + '<span class="code-wrap">'
            + '<span class="code">{}</span>'.format(html.escape(line) or "&nbsp;")
            + skipped_tag + badge
            + '</span>'
            + '</div>'
        )

    step_linenos_json = json.dumps(step_linenos, ensure_ascii=False)
    step_locals_json = json.dumps(step_locals, ensure_ascii=False)
    events_json = json.dumps(line_trace, ensure_ascii=False)
    step_etype_json = json.dumps(step_etype, ensure_ascii=False)
    step_retval_json = json.dumps(step_return_val, ensure_ascii=False)
    input_json = json.dumps(runtime.get("input", {}), ensure_ascii=False, indent=2)

    status_class = "passed" if passed else "failed"
    status_text = "PASSED" if passed else ("FAILED" if error else "WRONG ANSWER")

    css = """*{box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#1e1e1e;color:#d4d4d4;margin:0;padding:0;display:flex;flex-direction:column;height:100vh}
.header{background:#252526;padding:.5rem 1rem;display:flex;align-items:center;gap:.8rem;flex-wrap:wrap;border-bottom:1px solid #333;min-height:44px}
.header a{color:#42a5f5;text-decoration:none;font-size:.8rem;flex-shrink:0}
.header h1{font-size:.95rem;margin:0;color:#ccc;flex-shrink:0}
.header .status{font-weight:700;font-size:.8rem;padding:2px 10px;border-radius:4px;flex-shrink:0}
.header .status.passed{background:#1b5e20;color:#a5d6a7}
.header .status.failed{background:#b71c1c;color:#ef9a9a}
.header .meta{font-size:.75rem;color:#888}
.main{display:flex;flex:1;overflow:hidden}
.code-panel{flex:1;overflow-y:auto;background:#1e1e1e;border-right:1px solid #333;font-family:'Cascadia Code','Fira Code',monospace;font-size:.85rem;line-height:1.6}
.code-line{padding:2px .6rem;display:flex;align-items:center}
.code-line .ln{width:36px;text-align:right;color:#555;padding-right:10px;user-select:none;flex-shrink:0;align-self:flex-start;padding-top:4px}
.code-wrap{display:inline-flex;align-items:center;gap:10px;min-height:28px;padding:2px 10px;border-radius:8px;transition:background .15s,border .15s,box-shadow .15s}
.code-wrap .code{white-space:pre}
.code-line.hl-line .code-wrap{background:rgba(66,165,245,.18);border:1px solid rgba(66,165,245,.65);box-shadow:0 0 0 2px rgba(66,165,245,.08)}
.code-line.hl-return .code-wrap{background:rgba(76,175,80,.22);border:1px solid rgba(102,187,106,.85);box-shadow:0 0 0 3px rgba(76,175,80,.12)}
.code-line.hl-exception .code-wrap{background:rgba(244,67,54,.22);border:1px solid rgba(239,83,80,.85);box-shadow:0 0 0 3px rgba(244,67,54,.12)}
.skip-badge{display:inline;margin-left:10px;font-family:inherit;font-size:.7rem;font-style:normal;color:rgba(180,180,180,.65);flex-shrink:0}
.event-badge{display:none;font-size:.68rem;font-weight:800;letter-spacing:.04em;padding:2px 8px;border-radius:999px;white-space:nowrap}
.code-line.hl-return .event-badge{display:inline-block;color:#102a12;background:#66bb6a}
.code-line.hl-exception .event-badge{display:inline-block;color:#2a1010;background:#ef5350}
.side-panel{width:360px;min-width:280px;display:flex;flex-direction:column;background:#252526;overflow-y:auto}
.side-section{padding:.7rem .9rem;border-bottom:1px solid #333}
.side-section h3{margin:0 0 .3rem;font-size:.75rem;color:#888;text-transform:uppercase}
.side-section pre{margin:0;font-size:.78rem;color:#ccc;white-space:pre-wrap;word-break:break-all;max-height:180px;overflow-y:auto}
.locals-display{font-size:.76rem;color:#9ccc65;font-family:monospace;min-height:50px}
.return-info{font-size:.78rem;color:#a5d6a7;line-height:1.5}
#controls{background:#252526;padding:.4rem 1rem;border-top:1px solid #333;display:flex;align-items:center;gap:.5rem;min-height:40px}
#controls button{padding:.35rem .9rem;border:1px solid #555;border-radius:4px;background:#333;color:#ccc;cursor:pointer;font-size:.82rem}
#controls button:hover{background:#444}
#controls button:disabled{opacity:.3;cursor:default}
#step-counter{margin-left:auto;color:#888;font-size:.8rem}"""

    js = """var stepLinenos = {};                          
var stepLocals = {};                            
var stepEvents = {};                             
var stepEtype = {};                              
var stepRetval = {};                             
var totalSteps = {};                             
var currentStep = 0;                             
var playing = false;                             
var timer = null;                                

function highlightStep(step) {{                   
  var lines = document.querySelectorAll('.code-line');
  lines.forEach(function(l) {{ l.classList.remove('hl-line', 'hl-return', 'hl-exception'); }});

  var linenos = stepLinenos[step];               
  var etype = stepEtype[step] || 'line';         
  var cls = etype === 'return' ? 'hl-return' : (etype === 'exception' ? 'hl-exception' : 'hl-line');

  if (linenos) {{                                 
    linenos.forEach(function(ln) {{               
      var line = document.querySelector('.code-line[data-ln="' + ln + '"]');
      if (line) line.classList.add(cls);         
    }});                                         
  }}                                             

  var ev = stepEvents[step - 1];                 
  if (etype === 'return') {{                     
    document.getElementById('event-type-badge').textContent = 'RETURN \\u00b7 line ' + (ev ? ev.lineno : '?');
    document.getElementById('event-type-badge').style.color = '#66bb6a';
  }} else if (etype === 'exception') {{          
    document.getElementById('event-type-badge').textContent = 'EXCEPTION \\u00b7 line ' + (ev ? ev.lineno : '?');
    document.getElementById('event-type-badge').style.color = '#ef5350';
  }} else {{                                     
    document.getElementById('event-type-badge').textContent = 'LINE \\u00b7 line ' + (ev ? ev.lineno : '?');
    document.getElementById('event-type-badge').style.color = '#888';
  }}                                             

  document.getElementById('locals-display').textContent = stepLocals[step] || '\\u2014';
  document.getElementById('step-counter').textContent = step + ' / ' + totalSteps;

  var rs = document.getElementById('return-section');
  var cb = document.getElementById('completed-banner');
  if (etype === 'return' && stepRetval[step]) {{
    rs.style.display = 'block';
    document.getElementById('return-value').textContent = stepRetval[step];
    cb.style.display = 'block';
  }} else {{
    rs.style.display = 'none';
    cb.style.display = 'none';
  }}

  document.getElementById('btn-prev').disabled = (step <= 0);
  document.getElementById('btn-next').disabled = (step >= totalSteps);
}}

document.getElementById('btn-prev').onclick = function() {{ if (currentStep > 0) {{ currentStep--; highlightStep(currentStep); }} }};
document.getElementById('btn-next').onclick = function() {{ if (currentStep < totalSteps) {{ currentStep++; highlightStep(currentStep); }} }};
document.getElementById('btn-play').onclick = function() {{
  if (playing) {{ clearInterval(timer); playing = false; this.textContent = '\\u25B6 Play'; }}
  else {{ playing = true; this.textContent = '\\u23F8 Pause';
    var self = this;
    timer = setInterval(function() {{
      if (currentStep < totalSteps) {{ currentStep++; highlightStep(currentStep); }}
      else {{ clearInterval(timer); playing = false; self.textContent = '\\u25B6 Play'; }}
    }}, 300);
  }}
}};"""

    js = js.format(step_linenos_json, step_locals_json, events_json,
                   step_etype_json, step_retval_json, total_steps)

    out = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>""" + title + """ — Code Execution Viewer</title>
<style>
""" + css + """
</style>
</head>
<body>
<div class="header">
  <a href="index.html">← Demo Gallery</a>
  <h1>""" + title + """</h1>
  <span class="status """ + status_class + """">""" + status_text + """</span>
  <span class="meta">actual=""" + html.escape(str(actual)) + """ · expected=""" + html.escape(str(expected)) + """</span>
  <span id="event-type-badge" style="color:#888">—</span>
</div>

<div class="main">
  <div class="code-panel" id="code-panel">
    """ + "".join(code_html_lines) + """
  </div>

  <div class="side-panel">
    <div class="side-section">
      <h3>Input</h3>
      <pre>""" + html.escape(input_json) + """</pre>
    </div>
    <div class="side-section">
      <h3>Locals</h3>
      <div class="locals-display" id="locals-display">—</div>
    </div>
    <div class="side-section" id="return-section" style="display:none">
      <h3>Return Value</h3>
      <div class="return-info">
        <div>Function returned here.</div>
        <div style="color:#aaa;font-size:.75rem;margin:.2rem 0">Code below this return was not executed.</div>
        <pre style="color:#66bb6a;font-size:.82rem;margin-top:.3rem" id="return-value"></pre>
      </div>
    </div>
    <div class="side-section" id="completed-banner" style="display:none">
      <div style="color:#66bb6a;font-weight:700;font-size:.85rem">Execution completed</div>
    </div>
    """ + _stdout_section(stdout) + """
    """ + _stderr_section(stderr) + """
    """ + _error_section(error, truncated) + """
  </div>
</div>

<div id="controls">
  <button id="btn-prev">← Prev</button>
  <button id="btn-play">▶ Play</button>
  <button id="btn-next">Next →</button>
  <span id="step-counter">0 / """ + str(total_steps) + """</span>
</div>

<script>
""" + js + """
</script>
</body>
</html>"""
    return out


def _stdout_section(stdout: str) -> str:
    if not stdout:
        return ""
    return '<div class="side-section"><h3>stdout</h3><pre>' + html.escape(stdout) + '</pre></div>'


def _stderr_section(stderr: str) -> str:
    if not stderr:
        return ""
    return '<div class="side-section"><h3>stderr</h3><pre style="color:#ef9a9a">' + html.escape(stderr) + '</pre></div>'


def _error_section(error: str, truncated: bool) -> str:
    parts = []
    if error:
        parts.append('<div class="side-section"><h3>Error</h3><pre style="color:#ef9a9a">' + html.escape(error) + '</pre></div>')
    if truncated:
        parts.append('<div class="side-section"><h3>Truncated</h3><pre style="color:#ff9800">Execution exceeded step limit.</pre></div>')
    return "".join(parts)
