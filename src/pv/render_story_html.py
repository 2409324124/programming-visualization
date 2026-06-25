"""Render storyboard frames into a self-contained HTML animation page."""

from __future__ import annotations

import json


CSS = """\
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#f0f2f5;margin:0;padding:2rem;display:flex;justify-content:center}
#app{max-width:800px;width:100%}
#app h1{font-size:1.3rem;margin-bottom:1rem;color:#333}
#stage{position:relative;background:#fff;border-radius:12px;padding:1.5rem;min-height:360px;box-shadow:0 2px 12px rgba(0,0,0,.06)}
#arrows{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none}
#objects{position:relative;z-index:1}
.st-obj{position:absolute;display:flex;align-items:center;justify-content:center;border-radius:8px;font-weight:600;font-size:.95rem;transition:opacity .26s ease,transform .26s ease,border-color .26s ease,background .26s ease}
.st-normal{background:#f5f5f5;border:2px solid #d0d0d0;color:#333}
.st-active{background:#e3f2fd;border:2px solid #42a5f5;color:#1565c0;font-weight:700}
.st-visited{background:#eee;border:2px dashed #bbb;color:#999}
.st-new{background:#fff3e0;border:2px solid #ff9800;color:#e65100}
.st-matched{background:#e8f5e9;border:2px solid #66bb6a;color:#2e7d32;font-weight:700}
.st-faded{opacity:0.25}
.st-label{border:none;background:transparent;color:#666;font-weight:400;font-size:.85rem}
.st-badge{border:none;background:#f5f5f5;color:#555;font-size:.8rem;padding:4px 10px}
.st-idx{position:absolute;bottom:-20px;font-size:.7rem;color:#999;text-align:center;left:0;right:0}
#map-zone{margin-top:1rem;padding:.8rem 1rem;background:#fafafa;border:1px solid #e0e0e0;border-radius:8px;min-height:60px}
#map-zone h3{margin:0 0 .4rem;font-size:.9rem;color:#555}
.map-entry{display:inline-block;margin:2px 4px;padding:3px 10px;border-radius:4px;font-size:.82rem;background:#fff;border:1px solid #e0e0e0}
.map-empty{color:#bbb;font-size:.85rem}
#caption-area{margin-top:1rem;padding:0 .2rem}
#frame-title{font-size:1.05rem;margin:0 0 .3rem;color:#333}
#frame-caption{margin:0;color:#666;font-size:.92rem;line-height:1.5}
#controls{margin-top:1.2rem;display:flex;align-items:center;gap:.6rem}
#controls button{padding:.5rem 1.2rem;border:1px solid #d0d0d0;border-radius:6px;background:#fff;cursor:pointer;font-size:.9rem;transition:background .15s}
#controls button:hover{background:#f0f0f0}
#controls button:disabled{opacity:.4;cursor:default;background:#fff}
#counter{margin-left:auto;color:#999;font-size:.85rem}
"""


JS = """\
(function() {
  var current = 0;
  var total = FRAMES.length;
  var objDiv = document.getElementById('objects');
  var svg = document.getElementById('arrows');
  var mapZone = document.getElementById('map-zone');
  var titleEl = document.getElementById('frame-title');
  var captionEl = document.getElementById('frame-caption');
  var counterEl = document.getElementById('counter');
  var prevBtn = document.getElementById('btn-prev');
  var nextBtn = document.getElementById('btn-next');
  var playBtn = document.getElementById('btn-play');
  var playing = false;
  var timer = null;
  var SVG_NS = 'http' + '://www.w3.org/2000/svg';

  // Create arrowhead marker
  var defs = document.createElementNS(SVG_NS, 'defs');
  var marker = document.createElementNS(SVG_NS, 'marker');
  marker.setAttribute('id', 'arrowhead');
  marker.setAttribute('markerWidth', '6');
  marker.setAttribute('markerHeight', '6');
  marker.setAttribute('refX', '5');
  marker.setAttribute('refY', '3');
  marker.setAttribute('orient', 'auto');
  var mpath = document.createElementNS(SVG_NS, 'path');
  mpath.setAttribute('d', 'M0,0 L6,3 L0,6 Z');
  mpath.setAttribute('fill', '#90caf9');
  marker.appendChild(mpath);
  defs.appendChild(marker);
  svg.appendChild(defs);

  function render(idx) {
    var f = FRAMES[idx];
    titleEl.textContent = f.title || '';
    captionEl.textContent = f.caption || '';

    // Clear & render objects
    objDiv.innerHTML = '';
    var objs = f.objects || [];
    for (var i = 0; i < objs.length; i++) {
      var o = objs[i];
      var div = document.createElement('div');
      div.className = 'st-obj st-' + (o.state || 'normal');
      div.style.left = (o.x || 0) + 'px';
      div.style.top = (o.y || 0) + 'px';
      div.style.width = (o.w || 56) + 'px';
      div.style.height = (o.h || 48) + 'px';
      div.textContent = o.text || '';
      objDiv.appendChild(div);

      // Index label for array boxes
      if (o.type === 'array_box' && o.idx !== undefined) {
        var lbl = document.createElement('div');
        lbl.className = 'st-obj st-label';
        lbl.style.position = 'absolute';
        lbl.style.left = o.x + 'px';
        lbl.style.top = (o.y + (o.h || 48)) + 'px';
        lbl.style.width = (o.w || 56) + 'px';
        lbl.style.border = 'none';
        lbl.style.background = 'transparent';
        var sp = document.createElement('span');
        sp.className = 'st-idx';
        sp.textContent = '[' + o.idx + ']';
        lbl.appendChild(sp);
        objDiv.appendChild(lbl);
      }
    }

    // Clear & render arrows
    // Preserve the <defs> element
    while (svg.childNodes.length > 1) {
      svg.removeChild(svg.lastChild);
    }
    var arrows = f.arrows || [];
    for (var j = 0; j < arrows.length; j++) {
      var a = arrows[j];
      var fromObj = null, toObj = null;
      for (var k = 0; k < objs.length; k++) {
        if (objs[k].id === a.from) fromObj = objs[k];
        if (objs[k].id === a.to) toObj = objs[k];
      }
      if (fromObj && toObj) {
        var x1 = (fromObj.x || 0) + (fromObj.w || 56) / 2;
        var y1 = (fromObj.y || 0) + (fromObj.h || 48) / 2;
        var x2 = (toObj.x || 0) + (toObj.w || 56) / 2;
        var y2 = (toObj.y || 0) + (toObj.h || 48) / 2;
        var line = document.createElementNS(SVG_NS, 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', a.color || '#90caf9');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('marker-end', 'url(#arrowhead)');
        svg.appendChild(line);
      }
    }

    // Map zone
    mapZone.innerHTML = '<h3>Hash Map</h3>';
    var mapEntries = [];
    for (var m = 0; m < objs.length; m++) {
      if (objs[m].type === 'map_entry') mapEntries.push(objs[m]);
    }
    if (mapEntries.length === 0) {
      var emptySpan = document.createElement('span');
      emptySpan.className = 'map-empty';
      emptySpan.textContent = '(empty)';
      mapZone.appendChild(emptySpan);
    } else {
      for (var n = 0; n < mapEntries.length; n++) {
        var me = mapEntries[n];
        var entry = document.createElement('span');
        entry.className = 'map-entry';
        if (me.state) entry.className += ' st-' + me.state;
        entry.textContent = me.text || '';
        mapZone.appendChild(entry);
      }
    }

    // Counter & buttons
    counterEl.textContent = (idx + 1) + ' / ' + total;
    prevBtn.disabled = (idx === 0);
    nextBtn.disabled = (idx === total - 1);
  }

  prevBtn.onclick = function() {
    if (current > 0) render(--current);
  };
  nextBtn.onclick = function() {
    if (current < total - 1) render(++current);
  };
  playBtn.onclick = function() {
    if (playing) {
      clearInterval(timer);
      playing = false;
      playBtn.textContent = '\\u25b6 \\u64ad\\u653e';
    } else {
      playing = true;
      playBtn.textContent = '\\u23f8 \\u6682\\u505c';
      timer = setInterval(function() {
        if (current < total - 1) render(++current);
        else { clearInterval(timer); playing = false; playBtn.textContent = '\\u25b6 \\u64ad\\u653e'; }
      }, 1800);
    }
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

    <div id="stage">
      <svg id="arrows"></svg>
      <div id="objects"></div>
      <div id="map-zone">
        <h3>Hash Map</h3>
      </div>
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
            - ``w``, ``h`` (int, optional): size (default 56×48)
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
    )
