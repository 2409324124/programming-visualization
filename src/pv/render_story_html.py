"""Render storyboard frames into a self-contained HTML animation page."""

from __future__ import annotations

import json


CSS = """\
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#f0f2f5;margin:0;padding:2rem;display:flex;justify-content:center}
#app{width:1000px;max-width:calc(100vw - 48px)}
#app h1{font-size:1.3rem;margin-bottom:1rem;color:#333}
#stage{position:relative;width:960px;height:520px;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.06)}
#arrows{position:absolute;inset:0;z-index:1;pointer-events:none}
#zones{position:absolute;inset:0;z-index:0}
.zone{position:absolute;border:1px dashed #e0e0e0;border-radius:8px;background:rgba(245,245,245,.6)}
.zone-title{position:absolute;top:-22px;left:8px;font-size:.75rem;color:#999;font-weight:600}
.zone-map{left:50px;top:270px;width:400px;height:90px}
.zone-result{left:600px;top:380px;width:260px;height:70px}
#objects{position:absolute;inset:0;z-index:2}
.st-obj{position:absolute;left:0;top:0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-weight:600;font-size:.95rem;transition:transform .42s ease,opacity .26s ease,background .26s ease,border-color .26s ease,color .26s ease,box-shadow .26s ease;white-space:nowrap}
.st-normal{background:#f5f5f5;border:2px solid #d0d0d0;color:#333}
.st-active{background:#e3f2fd;border:2px solid #42a5f5;color:#1565c0;font-weight:700;box-shadow:0 0 0 3px rgba(66,165,245,.25)}
.st-visited{background:#eee;border:2px dashed #bbb;color:#999}
.st-new{background:#fff3e0;border:2px solid #ff9800;color:#e65100;box-shadow:0 0 0 3px rgba(255,152,0,.2)}
.st-matched{background:#e8f5e9;border:2px solid #66bb6a;color:#2e7d32;font-weight:700;box-shadow:0 0 0 3px rgba(102,187,106,.25)}
.st-faded{opacity:0.18;pointer-events:none}
.st-definition_card{border:2px solid #42a5f5;background:linear-gradient(135deg,#e3f2fd,#bbdefb);color:#0d47a1;border-radius:12px;font-size:.88rem;flex-direction:column;align-items:flex-start;padding:8px 12px;text-align:left;white-space:pre-line}
.st-definition_card::before{content:'📖 ' attr(data-title);font-weight:700;font-size:.75rem;color:#1565c0;display:block;margin-bottom:4px}
.st-rule_card{border:2px solid #ab47bc;background:linear-gradient(135deg,#f3e5f5,#e1bee7);color:#4a148c;border-radius:12px;font-size:.85rem;font-family:monospace;font-weight:600;flex-direction:column;align-items:flex-start;padding:6px 12px;text-align:left;white-space:pre-line}
.st-rule_card::before{content:'📐 ' attr(data-title);font-weight:700;font-size:.72rem;color:#7b1fa2;display:block;margin-bottom:4px}
.st-operation_card{border:2px solid #ff9800;background:linear-gradient(135deg,#fff3e0,#ffe0b2);color:#e65100;border-radius:10px;font-size:.82rem;font-weight:600;flex-direction:column;align-items:flex-start;padding:6px 12px;text-align:left;white-space:pre-line}
.st-operation_card::before{content:'▶ ' attr(data-title);font-weight:700;font-size:.72rem;color:#e65100;display:block;margin-bottom:4px}
.st-note_card{border:1px dashed #bbb;background:#f9f9f9;color:#888;border-radius:8px;font-size:.78rem;flex-direction:column;align-items:flex-start;padding:4px 10px;text-align:left;white-space:pre-line}
.st-note_card::before{content:'📝 ' attr(data-title);font-weight:600;font-size:.7rem;color:#aaa;display:block;margin-bottom:3px}
.st-label{background:transparent;border:none;color:#666;font-weight:400;font-size:.85rem}
.st-definition{border:2px dashed #42a5f5;background:rgba(227,242,253,0.35);color:#0d47a1;border-radius:10px;font-size:.82rem;align-items:flex-start;padding:8px 12px;text-align:left;white-space:pre-line}
.st-definition::before{content:'📦 ' attr(data-title);font-weight:700;font-size:.73rem;color:#1565c0;display:block;margin-bottom:4px}
.st-variable_box{border:2px solid #26a69a;background:linear-gradient(135deg,#e0f2f1,#b2dfdb);color:#00695c;border-radius:8px;font-size:.9rem;font-weight:600}
.st-idx{position:absolute;bottom:-20px;font-size:.7rem;color:#999;text-align:center;left:0;right:0}
#caption-area{margin-top:1rem;padding:0 .4rem}
#frame-title{font-size:1.05rem;margin:0 0 .3rem;color:#333}
#frame-caption{margin:0;color:#666;font-size:.92rem;line-height:1.5}
#controls{margin-top:1.2rem;display:flex;align-items:center;gap:.6rem}
#controls button{padding:.5rem 1.2rem;border:1px solid #d0d0d0;border-radius:6px;background:#fff;cursor:pointer;font-size:.9rem;transition:background .15s}
#controls button:hover{background:#f0f0f0}
#controls button:disabled{opacity:.4;cursor:default;background:#fff}
#counter{margin-left:auto;color:#999;font-size:.85rem}
/* Runtime-bound banner ────────────────────────────────────────────── */
#runtime-banner{display:flex;align-items:center;gap:1rem;margin-bottom:1rem;padding:.55rem 1rem;border-radius:8px;font-size:.82rem;font-weight:600;flex-wrap:wrap}
#runtime-banner.rb-passed{background:#e8f5e9;border:1.5px solid #66bb6a;color:#2e7d32}
#runtime-banner.rb-failed{background:#fce4ec;border:1.5px solid #e57373;color:#b71c1c}
#runtime-banner.rb-error{background:#fff8e1;border:1.5px solid #ffca28;color:#e65100}
.rb-label{opacity:.7;font-weight:400}
.rb-chip{background:rgba(0,0,0,.08);border-radius:4px;padding:1px 6px;font-family:monospace;font-size:.8rem}
"""


JS = """\
(function() {
  var current = 0;
  var total = FRAMES.length;
  var stage = document.getElementById('stage');
  var objDiv = document.getElementById('objects');
  var svg = document.getElementById('arrows');
  var titleEl = document.getElementById('frame-title');
  var captionEl = document.getElementById('frame-caption');
  var counterEl = document.getElementById('counter');
  var prevBtn = document.getElementById('btn-prev');
  var nextBtn = document.getElementById('btn-next');
  var playBtn = document.getElementById('btn-play');
  var playing = false;
  var timer = null;
  var SVG_NS = 'http://www.w3.org/2000/svg';
  var objectNodes = {};

  // Arrowhead marker
  (function(){
    var defs = document.createElementNS(SVG_NS, 'defs');
    var m = document.createElementNS(SVG_NS, 'marker');
    m.setAttribute('id', 'arrowhead');
    m.setAttribute('markerWidth','6'); m.setAttribute('markerHeight','6');
    m.setAttribute('refX','5'); m.setAttribute('refY','3');
    m.setAttribute('orient','auto');
    var p = document.createElementNS(SVG_NS, 'path');
    p.setAttribute('d','M0,0 L6,3 L0,6 Z'); p.setAttribute('fill','#90caf9');
    m.appendChild(p); defs.appendChild(m); svg.appendChild(defs);
  })();

  function render(idx) {
    var f = FRAMES[idx];
    titleEl.textContent = f.title || '';
    captionEl.textContent = f.caption || '';

    var objs = f.objects || [];
    var seen = {};

    // Build/update objects
    for (var i = 0; i < objs.length; i++) {
      var o = objs[i];
      seen[o.id] = true;
      var node = objectNodes[o.id];
      var created = false;

      if (!node) {
        node = document.createElement('div');
        node.style.position = 'absolute';
        node.style.left = '0';
        node.style.top = '0';
        node.style.width = (o.w || 64) + 'px';
        node.style.height = (o.h || 48) + 'px';
        objectNodes[o.id] = node;
        objDiv.appendChild(node);
        created = true;
      }

      // Update class
      node.className = 'st-obj st-' + (o.state || 'normal');
      // Set data-title for cards and containers (used by CSS ::before)
      if (['definition_card','rule_card','operation_card','note_card','definition'].indexOf(o.type) >= 0) {
          node.setAttribute('data-title', o.title || o.text || '');
      }
      // Update transform (smooth CSS transition)
      node.style.transform = 'translate(' + (o.x || 0) + 'px,' + (o.y || 0) + 'px)';
      node.style.width = (o.w || 64) + 'px';
      node.style.height = (o.h || 48) + 'px';
      node.textContent = o.text || '';

      // Index label for array boxes
      if (o.type === 'array_box' && o.idx !== undefined) {
        var labelId = o.id + '_idx';
        var lbl = objectNodes[labelId];
        if (!lbl) {
          lbl = document.createElement('div');
          lbl.style.position = 'absolute';
          lbl.style.left = '0';
          lbl.style.top = '0';
          lbl.style.border = 'none';
          lbl.style.background = 'transparent';
          lbl.style.color = '#999';
          lbl.style.fontSize = '.7rem';
          lbl.style.textAlign = 'center';
          objectNodes[labelId] = lbl;
          objDiv.appendChild(lbl);
        }
        seen[labelId] = true;
        lbl.style.transform = 'translate(' + (o.x || 0) + 'px,' + ((o.y || 0) + (o.h || 48)) + 'px)';
        lbl.style.width = (o.w || 64) + 'px';
        lbl.textContent = '[' + o.idx + ']';
      }
    }

    // Remove objects no longer in frame
    for (var key in objectNodes) {
      if (!seen[key]) {
        var old = objectNodes[key];
        old.style.opacity = '0';
        setTimeout(function(n){ return function(){ if(n.parentNode)n.parentNode.removeChild(n); }; }(old), 300);
        delete objectNodes[key];
      }
    }

    // Arrows
    while (svg.childNodes.length > 1) { svg.removeChild(svg.lastChild); }
    var arrows = f.arrows || [];
    for (var j = 0; j < arrows.length; j++) {
      var a = arrows[j];
      var fromObj = null, toObj = null;
      for (var k = 0; k < objs.length; k++) {
        if (objs[k].id === a.from) fromObj = objs[k];
        if (objs[k].id === a.to) toObj = objs[k];
      }
      if (fromObj && toObj) {
        var x1 = (fromObj.x || 0) + (fromObj.w || 64) / 2;
        var y1 = (fromObj.y || 0) + (fromObj.h || 48) / 2;
        var x2 = (toObj.x || 0) + (toObj.w || 64) / 2;
        var y2 = (toObj.y || 0) + (toObj.h || 48) / 2;
        var line = document.createElementNS(SVG_NS, 'line');
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        var color = a.color || (a.label === 'match' ? '#66bb6a' : '#90caf9');
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', '2.5');
        line.setAttribute('marker-end', 'url(#arrowhead)');
        svg.appendChild(line);
      }
    }

    counterEl.textContent = (idx + 1) + ' / ' + total;
    prevBtn.disabled = (idx === 0);
    nextBtn.disabled = (idx === total - 1);
  }

  // Controls
  prevBtn.onclick = function(){ if(current>0)render(--current); };
  nextBtn.onclick = function(){ if(current<total-1)render(++current); };
  playBtn.onclick = function(){
    if(playing){ clearInterval(timer); playing=false; playBtn.textContent='\\u25b6 \\u64ad\\u653e'; }
    else{ playing=true; playBtn.textContent='\\u23f8 \\u6682\\u505c';
      timer=setInterval(function(){ if(current<total-1)render(++current); else{clearInterval(timer);playing=false;playBtn.textContent='\\u25b6 \\u64ad\\u653e';} },1800); }
  };
  render(0);
})();
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
  <div id="app">
    <h1>{title}</h1>
{runtime_banner}
    <div id="stage">
      <svg id="arrows"></svg>
      <div id="zones">
        <div class="zone zone-map"><div class="zone-title">Hash Map</div></div>
      </div>
      <div id="objects"></div>
    </div>

    <div id="caption-area">
      <h3 id="frame-title"></h3>
      <p id="frame-caption"></p>
    </div>

    <div id="controls">
      <button id="btn-prev">\u2190 \u4e0a\u4e00\u6b65</button>
      <button id="btn-play">\u25b6 \u64ad\u653e</button>
      <button id="btn-next">\u4e0b\u4e00\u6b65 \u2192</button>
      <span id="counter">1 / N</span>
    </div>
  </div>

  <script>
    const FRAMES = {frames_json};
{js}
  </script>
</body>
</html>"""


def render_story_to_html(frames: list[dict], title: str = "Storyboard Demo") -> str:
    """Convert storyboard frames to a self-contained HTML animation page.

    Backward-compatible entry point for authored-only (lesson/storyboard) mode.
    Frames are displayed without a runtime banner.

    Parameters
    ----------
    frames : list[dict]
        Each frame is a dict with keys:

        - ``title`` (str): frame heading
        - ``caption`` (str): explanatory text
        - ``objects`` (list[dict]): visual objects, each with:
            - ``id`` (str): unique identifier (used for arrows)
            - ``text`` (str): display label
            - ``x``, ``y`` (int): absolute position in stage
            - ``w``, ``h`` (int, optional): size (default 64×48)
            - ``state`` (str, optional): one of normal/active/visited/new/matched/faded
            - ``type`` (str, optional): ``'array_box'`` for indexed boxes,
              ``'map_entry'`` for hash-map entries
            - ``idx`` (int, optional): array index label (when type=array_box)
        - ``arrows`` (list[dict], optional): arrow connections, each with:
            - ``from`` (str): source object id
            - ``to`` (str): target object id
            - ``color`` (str, optional): stroke color (default ``#90caf9``)

    title : str
        Page title.

    Returns
    -------
    str
        Complete self-contained HTML document.
    """
    frames_json = json.dumps(frames, ensure_ascii=False, indent=2)
    return TEMPLATE.format(
        title=title,
        css=CSS,
        frames_json=frames_json,
        js=JS,
        runtime_banner="",   # no banner for authored-only mode
    )


def render_visual_to_html(frames: list[dict], title: str = "Runtime-bound Visualization") -> str:
    """Render runtime-bound frames into a self-contained HTML animation page.

    Unlike :func:`render_story_to_html`, this function expects frames that
    contain a ``runtime_meta`` key (produced by
    :func:`~pv.visual_compiler.compile_visual`).  A banner is injected into
    the page showing::

        Runtime-bound visualization  |  Case N  |  Passed: true  |  Actual: [0,1]  |  Expected: [0,1]

    If ``passed`` is ``False`` the banner turns red.  If an execution error
    occurred the banner turns amber and shows the error message.

    Parameters
    ----------
    frames:
        Frames from :func:`~pv.visual_compiler.compile_visual`.
    title:
        Page title.

    Returns
    -------
    str
        Complete self-contained HTML document with runtime banner.
    """
    # Extract runtime metadata from the first frame that has it
    rt_meta: dict = {}
    for f in frames:
        if f.get("runtime_meta"):
            rt_meta = f["runtime_meta"]
            break

    banner_html = _build_runtime_banner(rt_meta)
    frames_json = json.dumps(frames, ensure_ascii=False, indent=2)
    return TEMPLATE.format(
        title=title,
        css=CSS,
        frames_json=frames_json,
        js=JS,
        runtime_banner=banner_html,
    )


def _build_runtime_banner(rt_meta: dict) -> str:
    """Build the HTML for the runtime status banner."""
    if not rt_meta:
        return ""

    passed: bool  = rt_meta.get("passed", False)
    actual        = rt_meta.get("actual")
    expected      = rt_meta.get("expected")
    case_index    = rt_meta.get("case_index", 0)
    case_name     = rt_meta.get("case_name", "")
    error_msg     = rt_meta.get("error")

    if error_msg:
        css_class = "rb-error"
        status_text = "\u26a0\ufe0f Error"
    elif passed:
        css_class = "rb-passed"
        status_text = "\u2705 Passed"
    else:
        css_class = "rb-failed"
        status_text = "\u274c Failed"

    case_label = f"Case {case_index}"
    if case_name:
        # truncate long names
        short = case_name[:40] + "\u2026" if len(case_name) > 40 else case_name
        case_label += f" \u2014 {short}"

    actual_str   = _fmt_val(actual)
    expected_str = _fmt_val(expected)

    chips = [
        ("Runtime-bound visualization", False),
        (case_label, True),
        (status_text, False),
        (f"Actual: {actual_str}", True),
        (f"Expected: {expected_str}", True),
    ]
    if error_msg:
        short_err = error_msg[:80] + "\u2026" if len(error_msg) > 80 else error_msg
        chips.append((f"Error: {short_err}", True))

    items = ""
    for text, is_chip in chips:
        if is_chip:
            items += f'<span class="rb-chip">{_esc(text)}</span>\n    '
        else:
            items += f'<span>{_esc(text)}</span>\n    '

    return f'\n    <div id="runtime-banner" class="{css_class}">\n    {items.strip()}\n    </div>'


def _fmt_val(v) -> str:
    if v is None:
        return "None"
    return str(v)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
