"""server.py — Local LeetCode-style interactive code runner.

Zero external dependencies.  Python stdlib only.

Start:
    python -m pv serve --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import html as _html_mod
import json
import multiprocessing
import os
import sys
import tempfile
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

EXECUTION_TIMEOUT = 10
MAX_BODY_BYTES = 512 * 1024


class RequestBodyTooLarge(Exception):
    """Raised when a local API request body exceeds the configured limit."""


# ── helpers ────────────────────────────────────────────────────────────


def _project_root() -> Path:
    """Return the project root directory (parent of src/)."""
    return Path(__file__).resolve().parents[2]


def _scan_problems(project_root: Path) -> list[dict]:
    """Scan problems/ for available problem directories with valid problem.json."""
    problems_dir = project_root / "problems"
    results: list[dict] = []
    if not problems_dir.is_dir():
        return results
    for entry in sorted(problems_dir.iterdir()):
        if not entry.is_dir():
            continue
        problem_json = entry / "problem.json"
        if not problem_json.is_file():
            continue
        try:
            meta = json.loads(problem_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        problem_id = meta.get("problem_id", entry.name)
        title = meta.get("display_title") or problem_id
        case_count = _case_count(entry)
        results.append({
            "id": problem_id,
            "title": title,
            "difficulty": meta.get("difficulty", ""),
            "tags": meta.get("pattern_tags", []),
            "case_count": case_count,
        })
    return results


def _case_count(problem_dir: Path) -> int:
    cases_file = problem_dir / "cases.json"
    if not cases_file.is_file():
        return 0
    try:
        cases = json.loads(cases_file.read_text(encoding="utf-8"))
        if isinstance(cases, list):
            return len(cases)
    except (json.JSONDecodeError, OSError):
        pass
    return 0


def _problem_detail(project_root: Path, problem_id: str) -> dict | None:
    problem_dir = project_root / "problems" / problem_id
    if not problem_dir.is_dir():
        return None
    problem_json = problem_dir / "problem.json"
    if not problem_json.is_file():
        return None
    try:
        meta = json.loads(problem_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    cases_file = problem_dir / "cases.json"
    cases: list[dict] = []
    if cases_file.is_file():
        try:
            raw = json.loads(cases_file.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                for ci, c in enumerate(raw):
                    cases.append({
                        "index": ci,
                        "name": c.get("name", f"case {ci}"),
                        "notes": c.get("notes", ""),
                    })
        except (json.JSONDecodeError, OSError):
            pass
    solution_path = problem_dir / "solution.py"
    default_code = ""
    if solution_path.is_file():
        default_code = solution_path.read_text(encoding="utf-8")
    return {
        "id": meta.get("problem_id", problem_id),
        "title": meta.get("display_title") or problem_id,
        "difficulty": meta.get("difficulty", ""),
        "tags": meta.get("pattern_tags", []),
        "entry": meta.get("entry", {}),
        "cases": cases,
        "default_code": default_code,
    }


# ── code execution with timeout ────────────────────────────────────────


def _exec_subprocess(queue: multiprocessing.Queue, project_root_str: str,
                     problem_dir_str: str, solution_path_str: str,
                     case_index: int) -> None:
    """Target for multiprocessing.Process — runs the real execution."""
    try:
        src_dir = os.path.join(project_root_str, "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html

        runtime = get_learner_runtime(problem_dir_str, solution_path_str, case_index)
        html_str = render_learner_to_html(runtime)
        queue.put({"ok": True, "runtime": runtime, "html": html_str})
    except Exception as exc:
        queue.put({
            "ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "runtime": None,
            "html": None,
        })


def _render_code_request(project_root: Path, payload: dict) -> dict:
    """Execute user code and return runtime context + rendered HTML.

    Returns a dict suitable for JSON response.
    """
    problem_id = str(payload.get("problem_id", ""))
    # Validate problem_id: no path traversal
    if ".." in problem_id or "/" in problem_id or "\\" in problem_id:
        return {"ok": False, "error": "非法的题目 ID。"}
    try:
        case_index = int(payload.get("case_index", 0))
    except (ValueError, TypeError):
        return {"ok": False, "error": "无效的用例索引。"}
    code = payload.get("code", "")

    problem_dir = project_root / "problems" / problem_id
    if not problem_dir.is_dir():
        return {"ok": False, "error": f"题目未找到 (not found): {problem_id}"}

    if not code.strip():
        return {"ok": False, "error": "代码不能为空。"}

    # Check import policy
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False,
                                     encoding="utf-8") as tmp:
        tmp.write(code)
        temp_path = tmp.name

    try:
        from pv.submission_policy import check_imports
        policy = check_imports(temp_path)
        if not policy["ok"]:
            return {"ok": False, "error": "; ".join(policy["violations"])}
    finally:
        os.unlink(temp_path)

    # Write code to temp file for execution
    tmpdir = tempfile.mkdtemp(prefix="pv_runner_")
    solution_path = os.path.join(tmpdir, "solution.py")
    with open(solution_path, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        ctx = multiprocessing.get_context("spawn")
        queue: multiprocessing.Queue = ctx.Queue()
        proc = ctx.Process(
            target=_exec_subprocess,
            args=(queue, str(project_root), str(problem_dir),
                  solution_path, case_index),
        )
        proc.start()
        proc.join(EXECUTION_TIMEOUT)

        if proc.is_alive():
            proc.terminate()
            proc.join(2)
            if proc.is_alive():
                proc.kill()
                proc.join(1)
            return {"ok": False, "error": f"执行超时（{EXECUTION_TIMEOUT} 秒）。"}

        try:
            result = queue.get(timeout=2)
        except Exception:
            return {"ok": False, "error": "执行结果获取失败。"}

        # Check for subprocess-level errors
        if not result.get("ok"):
            return {"ok": False, "error": result.get("error", "未知执行错误。")}

        # Clean up runtime data that shouldn't go over the wire verbatim
        if result.get("runtime"):
            # Keep only summary fields; full trace is in the HTML already
            rt = result["runtime"]
            result["runtime"] = {
                "problem_id": rt.get("problem_id"),
                "case_index": rt.get("case_index"),
                "case_name": rt.get("case_name"),
                "input": rt.get("input"),
                "expected": rt.get("expected"),
                "actual": rt.get("actual"),
                "passed": rt.get("passed"),
                "stdout": rt.get("stdout"),
                "stderr": rt.get("stderr"),
                "error": rt.get("error"),
                "total_steps": rt.get("total_steps"),
                "truncated": rt.get("truncated"),
            }
        return result
    finally:
        # Clean up temp files
        try:
            os.unlink(solution_path)
            os.rmdir(tmpdir)
        except OSError:
            pass


# ── in-process helper (for testing without starting a server) ──────────

def render_code_request(payload: dict, project_root: Path | str | None = None) -> dict:
    """Public API: execute user code and return runtime + HTML.

    This is the same function the server uses, exposed for testing.
    """
    if project_root is None:
        project_root = _project_root()
    else:
        project_root = Path(project_root)
    return _render_code_request(project_root, payload)


def scan_problems(project_root: Path | str | None = None) -> list[dict]:
    """Public API: list available problems."""
    if project_root is None:
        project_root = _project_root()
    else:
        project_root = Path(project_root)
    return _scan_problems(project_root)


def problem_detail(problem_id: str, project_root: Path | str | None = None) -> dict | None:
    """Public API: get problem details including case list and default code."""
    if project_root is None:
        project_root = _project_root()
    else:
        project_root = Path(project_root)
    return _problem_detail(project_root, problem_id)


# ── HTTP server ────────────────────────────────────────────────────────


_MAIN_PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Programming Visualization — Local Runner</title>
<style>
*{box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#1e1e1e;color:#d4d4d4;margin:0;padding:0;height:100vh;display:flex;flex-direction:column}
#app{display:flex;flex:1;overflow:hidden}
.left{width:420px;min-width:340px;display:flex;flex-direction:column;background:#252526;border-right:1px solid #333;padding:1rem;gap:.7rem;overflow-y:auto}
.left h2{font-size:.95rem;margin:0;color:#ccc}
.left label{font-size:.75rem;color:#888;margin-bottom:-.4rem}
select,button{padding:.4rem .7rem;border:1px solid #555;border-radius:4px;background:#333;color:#ccc;font-size:.82rem;cursor:pointer}
select:hover,button:hover{background:#444}
button.primary{background:#0d47a1;border-color:#1565c0;color:#fff;font-weight:700}
button.primary:hover{background:#1565c0}
button.primary:disabled{opacity:.4;cursor:default}
#code-input{flex:1;min-height:200px;background:#1e1e1e;color:#d4d4d4;border:1px solid #555;border-radius:4px;padding:.6rem;font-family:'Cascadia Code','Fira Code',monospace;font-size:.82rem;resize:vertical;tab-size:4}
#status-bar{display:flex;align-items:center;gap:.6rem;min-height:28px}
#status-bar .tag{font-weight:700;font-size:.75rem;padding:2px 10px;border-radius:4px}
.tag.passed{background:#1b5e20;color:#a5d6a7}
.tag.failed{background:#b71c1c;color:#ef9a9a}
.tag.error{background:#e65100;color:#ffe0b2}
.tag.running{background:#0d47a1;color:#90caf9}
#error-msg{font-size:.75rem;color:#ef9a9a;word-break:break-all}
.right{flex:1;display:flex;flex-direction:column;overflow:hidden}
.right-header{background:#252526;padding:.5rem 1rem;border-bottom:1px solid #333;display:flex;align-items:center;gap:.8rem;min-height:36px}
.right-header h3{font-size:.85rem;margin:0;color:#ccc}
#actual-expected{font-size:.75rem;color:#888}
#viewer-frame{flex:1;border:none;width:100%}
#empty-state{flex:1;display:flex;align-items:center;justify-content:center;color:#666;font-size:.9rem}
#empty-state p{text-align:center;line-height:1.6}
</style>
</head>
<body>
<div id="app">
<div class="left">
  <h2>Programming Visualization</h2>
  <label>Problem</label>
  <select id="problem-select"></select>
  <label>Case</label>
  <select id="case-select"></select>
  <label>Code</label>
  <textarea id="code-input" spellcheck="false"></textarea>
  <div id="status-bar">
    <button class="primary" id="run-btn" onclick="runCode()">▶ Run</button>
    <span id="status-tag"></span>
  </div>
  <div id="error-msg"></div>
</div>
<div class="right">
  <div class="right-header">
    <h3>Execution Viewer</h3>
    <span id="actual-expected"></span>
  </div>
  <div id="empty-state"><p>Select a problem, edit your code, then click <strong>Run</strong> to see the execution trace.</p></div>
  <iframe id="viewer-frame" style="display:none"></iframe>
</div>
</div>
<script>
var problems = [];
var runRequestSeq = 0;

function clearResult(reason) {
  var tag = document.getElementById('status-tag');
  var err = document.getElementById('error-msg');
  var frame = document.getElementById('viewer-frame');
  var empty = document.getElementById('empty-state');
  var ae = document.getElementById('actual-expected');
  var btn = document.getElementById('run-btn');

  tag.className = '';
  tag.textContent = '';
  err.textContent = '';
  ae.textContent = '';
  frame.style.display = 'none';
  frame.srcdoc = '';
  empty.style.display = 'flex';
  empty.innerHTML = '<p>Selection changed. Click Run to execute this case.</p>';
  if (reason === 'selection') {
    runRequestSeq += 1;
    btn.disabled = false;
  }
}

async function loadProblems() {
  try {
    var resp = await fetch('/api/problems');
    problems = await resp.json();
    var sel = document.getElementById('problem-select');
    sel.innerHTML = '';
    problems.forEach(function(p) {
      var opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.title + ' (' + p.difficulty + ')';
      sel.appendChild(opt);
    });
    if (problems.length > 0) {
      sel.value = problems[0].id;
      onProblemChange();
    }
  } catch(e) { console.error(e); }
}

async function onProblemChange() {
  clearResult('selection');
  var pid = document.getElementById('problem-select').value;
  try {
    var resp = await fetch('/api/problem/' + pid);
    var detail = await resp.json();
    if (document.getElementById('problem-select').value !== pid) { return; }
    if (detail.error) { console.error(detail.error); return; }
    var cs = document.getElementById('case-select');
    cs.innerHTML = '';
    detail.cases.forEach(function(c) {
      var opt = document.createElement('option');
      opt.value = c.index;
      opt.textContent = c.name;
      cs.appendChild(opt);
    });
    cs.value = '0';
    if (detail.default_code) {
      document.getElementById('code-input').value = detail.default_code;
    }
  } catch(e) { console.error(e); }
}

document.getElementById('problem-select').onchange = onProblemChange;
document.getElementById('case-select').onchange = function() {
  clearResult('selection');
};

async function runCode() {
  var btn = document.getElementById('run-btn');
  var tag = document.getElementById('status-tag');
  var err = document.getElementById('error-msg');
  var frame = document.getElementById('viewer-frame');
  var empty = document.getElementById('empty-state');
  var ae = document.getElementById('actual-expected');
  var runProblemId = document.getElementById('problem-select').value;
  var runCaseIndex = parseInt(document.getElementById('case-select').value, 10);
  if (isNaN(runCaseIndex)) { runCaseIndex = 0; }
  var requestSeq = ++runRequestSeq;

  err.textContent = '';
  tag.className = 'tag running';
  tag.textContent = 'Running...';
  btn.disabled = true;
  ae.textContent = '';

  try {
    var resp = await fetch('/api/render-code', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        problem_id: runProblemId,
        case_index: runCaseIndex,
        code: document.getElementById('code-input').value
      })
    });
    var data = await resp.json();
    var selectedCaseIndex = parseInt(document.getElementById('case-select').value, 10);
    if (isNaN(selectedCaseIndex)) { selectedCaseIndex = 0; }
    if (requestSeq !== runRequestSeq ||
        document.getElementById('problem-select').value !== runProblemId ||
        selectedCaseIndex !== runCaseIndex) {
      return;
    }
    if (!data.ok) {
      tag.className = 'tag error';
      tag.textContent = 'ERROR';
      err.textContent = data.error || 'Unknown error';
      btn.disabled = false;
      return;
    }
    var rt = data.runtime;
    if (rt) {
      if (rt.error) {
        tag.className = 'tag error';
        tag.textContent = 'ERROR';
        err.textContent = rt.error;
      } else if (rt.passed) {
        tag.className = 'tag passed';
        tag.textContent = 'PASSED';
      } else {
        tag.className = 'tag failed';
        tag.textContent = 'FAILED';
      }
      ae.textContent = 'actual=' + JSON.stringify(rt.actual) + '  expected=' + JSON.stringify(rt.expected);
    }
    if (data.html) {
      frame.style.display = 'block';
      empty.style.display = 'none';
      frame.srcdoc = data.html;
    }
  } catch(e) {
    var selectedCaseIndex = parseInt(document.getElementById('case-select').value, 10);
    if (isNaN(selectedCaseIndex)) { selectedCaseIndex = 0; }
    if (requestSeq !== runRequestSeq ||
        document.getElementById('problem-select').value !== runProblemId ||
        selectedCaseIndex !== runCaseIndex) {
      return;
    }
    tag.className = 'tag error';
    tag.textContent = 'ERROR';
    err.textContent = 'Network or server error: ' + e.message;
  }
  btn.disabled = false;
}

loadProblems();
</script>
</body>
</html>"""


class _ServerHandler(BaseHTTPRequestHandler):
    """Request handler for the local runner server."""

    server_project_root: Path = _project_root()

    def _json_response(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html_response(self, html_str: str, status: int = 200) -> None:
        body = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("无效的 Content-Length。") from exc
        if length > MAX_BODY_BYTES:
            raise RequestBodyTooLarge(
                f"请求体过大，最大允许 {MAX_BODY_BYTES} bytes。"
            )
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("请求 JSON 解析失败。") from exc

    def do_GET(self) -> None:
        path = self.path.rstrip("/") or "/"

        if path == "/":
            self._html_response(_MAIN_PAGE_HTML)
        elif path == "/api/problems":
            problems = _scan_problems(self.server_project_root)
            self._json_response(problems)
        elif path.startswith("/api/problem/"):
            problem_id = path[len("/api/problem/"):]
            detail = _problem_detail(self.server_project_root, problem_id)
            if detail is None:
                self._json_response({"error": f"Problem not found: {problem_id}"}, 404)
            else:
                self._json_response(detail)
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        if self.path == "/api/render-code":
            try:
                payload = self._read_body()
            except RequestBodyTooLarge as exc:
                self._json_response({"ok": False, "error": str(exc)}, 413)
                return
            except ValueError as exc:
                self._json_response({"ok": False, "error": str(exc)}, 400)
                return
            result = _render_code_request(self.server_project_root, payload)
            self._json_response(result)
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:
        if self.server and getattr(self.server, "quiet", False):
            return
        super().log_message(fmt, *args)


def run_server(host: str = "127.0.0.1", port: int = 8765,
               project_root: Path | str | None = None,
               quiet: bool = False) -> None:
    """Start the local LeetCode-style runner HTTP server.

    Args:
        host: Bind address.  Default 127.0.0.1 (localhost only).
        port: Port number.
        project_root: Project root path.  Defaults to auto-detect.
        quiet: Suppress access logs.
    """
    if project_root is None:
        project_root = _project_root()
    else:
        project_root = Path(project_root)

    handler = type("BoundHandler", (_ServerHandler,), {"server_project_root": project_root})

    server = ThreadingHTTPServer((host, port), handler)
    server.quiet = quiet

    print(f"Programming Visualization Local Runner")
    print(f"Listening on http://{host}:{port}/")
    print(f"Project root: {project_root}")
    print(f"Press Ctrl+C to stop.")
    print()
    print("This is for trusted local development only.")
    print("Do not expose this server to the public internet.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
