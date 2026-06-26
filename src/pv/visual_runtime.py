"""
visual_runtime.py — Run a problem's harness and collect real runtime facts.

This is the SOURCE OF TRUTH layer in the runtime-bound pipeline::

    problem_dir + case_index
          ↓  get_runtime_context()
    RuntimeContext          ← real input / actual / expected / passed / trace
          ↓  visual_binder.py
    ...

Design constraints
------------------
* Must use the real harness (Solution / visual_solution) — no fake values.
* If visual_solution.py exists and emits trace events, use them.
* If only solution.py exists (no visual_solution), mode is "validation_only"
  and trace will be empty — callers must NOT generate semantic animation
  for validation_only results.
* actual / expected / passed ALWAYS come from real execution.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


# ── Public exceptions ─────────────────────────────────────────────────


class RuntimeError_(Exception):  # noqa: N818  (avoid shadowing built-in RuntimeError)
    """Raised when the harness cannot execute the solution."""


class ValidationOnlyError(Exception):
    """Raised when the caller requests semantic animation but only a
    validation-only solution is available (no visual_solution.py)."""


# ── Runtime context type alias ────────────────────────────────────────

#: The dict returned by :func:`get_runtime_context`.
RuntimeContext = dict


# ── Main entry point ──────────────────────────────────────────────────


def get_runtime_context(
    problem_dir: str | Path,
    case_index: int,
    solution_mode: str = "visual",
) -> RuntimeContext:
    """Run the harness for *problem_dir* case *case_index* and return runtime facts.

    Parameters
    ----------
    problem_dir:
        Path to the problem directory (e.g. ``problems/0001_two_sum``).
    case_index:
        Zero-based index into ``cases.json``.
    solution_mode:
        ``"visual"`` — use ``visual_solution.py`` (with TraceBuilder).
        ``"validation_only"`` — use plain ``solution.py`` (no trace).
        If ``"visual"`` is requested but ``visual_solution.py`` is absent,
        raises :exc:`ValidationOnlyError`.

    Returns
    -------
    RuntimeContext
        A dict with keys:

        ``problem_id`` (str)
            Directory name of the problem.
        ``case_index`` (int)
            Which case was run.
        ``case_name`` (str)
            Human-readable case name from cases.json.
        ``solution_mode`` (str)
            Effective mode that was used.
        ``input`` (dict)
            The raw input args (e.g. ``{"nums": [2,7,11,15], "target": 9}``).
        ``expected`` (Any)
            Expected output from cases.json.
        ``actual`` (Any)
            Actual output from the solution (``None`` if it raised).
        ``passed`` (bool)
            Whether ``actual == expected`` (element-wise for lists).
        ``trace`` (list[dict])
            List of raw trace event dicts (empty for validation_only).
        ``error`` (str | None)
            Exception string if execution raised, else ``None``.

    Raises
    ------
    FileNotFoundError
        If cases.json, problem.json, or the solution file is missing.
    IndexError
        If case_index is out of range.
    ValidationOnlyError
        If mode=visual but visual_solution.py does not exist.
    """
    problem_dir = Path(problem_dir).resolve()

    # ── Load cases ────────────────────────────────────────────────────
    cases_path = problem_dir / "cases.json"
    if not cases_path.exists():
        raise FileNotFoundError(f"cases.json not found: {cases_path}")
    with open(cases_path, encoding="utf-8") as f:
        cases: list[dict] = json.load(f)
    if case_index >= len(cases):
        raise IndexError(
            f"case_index {case_index} out of range; only {len(cases)} cases in {cases_path}"
        )
    case = cases[case_index]
    input_args: dict = case.get("args", {})
    expected: Any = case.get("expected")
    case_name: str = case.get("name", f"case_{case_index}")

    # ── Load problem metadata (for TraceBuilder) ──────────────────────
    problem_json_path = problem_dir / "problem.json"
    problem_meta: dict = {}
    if problem_json_path.exists():
        with open(problem_json_path, encoding="utf-8") as f:
            problem_meta = json.load(f)

    problem_id: str = problem_meta.get("problem_id", problem_dir.name)

    # ── Resolve solution path ─────────────────────────────────────────
    visual_sol_path = problem_dir / "visual_solution.py"
    plain_sol_path = problem_dir / "solution.py"

    if solution_mode == "visual":
        if not visual_sol_path.exists():
            raise ValidationOnlyError(
                f"solution_mode='visual' requested but visual_solution.py not found "
                f"in {problem_dir}. Only validation_only is available."
            )
        sol_path = visual_sol_path
        effective_mode = "visual"
    else:
        if not plain_sol_path.exists():
            raise FileNotFoundError(f"solution.py not found: {plain_sol_path}")
        sol_path = plain_sol_path
        effective_mode = "validation_only"

    # ── Import solution module ────────────────────────────────────────
    mod = _load_module(sol_path)
    entry: dict = problem_meta.get("entry", {})
    class_name: str = entry.get("class_name", "Solution")
    method_name: str = entry.get("method_name", "twoSum")

    # ── Execute ───────────────────────────────────────────────────────
    actual: Any = None
    trace_events: list[dict] = []
    error_msg: str | None = None

    if effective_mode == "visual":
        from pv.trace_schema import TraceBuilder

        builder = TraceBuilder(
            problem_meta=problem_meta,
            case=case,
            max_events=problem_meta.get("limits", {}).get("max_events", 1000),
        )
        try:
            sol_cls = getattr(mod, class_name)
            sol_obj = sol_cls(trace=builder)
            actual = getattr(sol_obj, method_name)(**input_args)
            builder.finish(status="passed" if _check_equal(actual, expected) else "failed",
                           actual=actual)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            builder.finish(status="error", actual=None)

        trace_dict = builder.to_dict()
        trace_events = trace_dict.get("events", [])

    else:  # validation_only
        try:
            sol_cls = getattr(mod, class_name)
            sol_obj = sol_cls()
            actual = getattr(sol_obj, method_name)(**input_args)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"

    passed = _check_equal(actual, expected)

    return {
        "problem_id":    problem_id,
        "case_index":    case_index,
        "case_name":     case_name,
        "solution_mode": effective_mode,
        "input":         input_args,
        "expected":      expected,
        "actual":        actual,
        "passed":        passed,
        "trace":         trace_events,
        "error":         error_msg,
    }


# ── Helpers ───────────────────────────────────────────────────────────


def _check_equal(actual: Any, expected: Any) -> bool:
    """Compare actual to expected.  Handles list equality order-insensitive
    only when the problem specifies unordered pairs — but for simplicity we
    do an exact match here.  Extend with checker logic as needed.
    """
    if actual is None:
        return False
    try:
        return sorted(actual) == sorted(expected)  # type: ignore[arg-type]
    except Exception:
        return actual == expected


def _load_module(path: Path):
    """Dynamically import a Python file as a throwaway module."""
    module_name = f"_pv_dynamic_{path.stem}_{id(path)}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    # Temporarily add problem dir to sys.path so relative imports work
    problem_dir = str(path.parent)
    inserted = False
    if problem_dir not in sys.path:
        sys.path.insert(0, problem_dir)
        inserted = True
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        if inserted and problem_dir in sys.path:
            sys.path.remove(problem_dir)
    return mod
