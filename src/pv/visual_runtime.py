"""
visual_runtime.py — Run a problem through the real harness and collect runtime facts.

This is the SOURCE OF TRUTH layer in the runtime-bound pipeline::

    problem_dir + case_index
          ↓  get_runtime_context()
    RuntimeContext          ← real input / actual / expected / passed / trace
          ↓  visual_binder.py
    ...

Design constraints
------------------
* Must use the real harness (harness.run_case) — no fake values, no duplicate import logic.
* Inherits: adapter, checker, import policy, stdout capture, trace_mode, UUID isolation.
* If visual_solution.py exists and emits trace events, use them (trace_mode=semantic).
* If only solution.py exists, trace_mode is validation_only — trace empty.
* actual / expected / passed ALWAYS come from real execution via the real checker.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any


# ── Public exceptions ─────────────────────────────────────────────────


class RuntimeError_(Exception):
    """Raised when the harness cannot execute the solution."""


class ValidationOnlyError(Exception):
    """Raised when visual_solution.py is absent but visual mode requested."""


# ── Runtime context type alias ────────────────────────────────────────

RuntimeContext = dict


# ── Main entry point ──────────────────────────────────────────────────


def get_runtime_context(
    problem_dir: str | Path,
    case_index: int,
    solution_mode: str = "visual",
) -> RuntimeContext:
    """Run the harness and return runtime facts.

    Delegates to ``harness.run_case``, inheriting all harness features:
    adapter, checker, import policy, stdout capture, trace_mode, UUID isolation.

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
        Dict with keys: problem_id, case_index, case_name, solution_mode,
        input, expected, actual, passed, trace, error, trace_mode.
    """
    from pv.harness import load_problem_meta, load_cases, run_case

    problem_dir = Path(problem_dir).resolve()

    # Load problem metadata and cases (harness validates both)
    meta = load_problem_meta(str(problem_dir))
    cases = load_cases(str(problem_dir))

    if case_index >= len(cases):
        raise IndexError(
            f"case_index {case_index} out of range; only {len(cases)} cases"
        )
    case = cases[case_index]
    input_args: dict = case.get("args", {})
    expected: Any = case.get("expected")
    case_name: str = case.get("name", f"case_{case_index}")
    problem_id: str = meta.get("problem_id", problem_dir.name)

    # Resolve solution path
    visual_sol = problem_dir / "visual_solution.py"
    plain_sol = problem_dir / "solution.py"

    if solution_mode == "visual":
        if not visual_sol.exists():
            raise ValidationOnlyError(
                f"solution_mode='visual' requested but visual_solution.py not found "
                f"in {problem_dir}. Only validation_only is available."
            )
        sol_path = str(visual_sol)
    else:
        if not plain_sol.exists():
            raise FileNotFoundError(f"solution.py not found: {plain_sol}")
        sol_path = str(plain_sol)

    # Run through the real harness (inherits adapter, checker, import policy, …)
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_case(
            problem_meta=meta,
            case=case,
            solution_path=sol_path,
            save_trace=True,
            trace_output_dir=tmpdir,
            case_index=case_index,
        )

        # Read trace if saved
        trace_events: list[dict] = []
        trace_path = result.get("trace_path")
        if trace_path and Path(trace_path).exists():
            with open(trace_path, encoding="utf-8") as f:
                trace_dict = json.load(f)
            trace_events = trace_dict.get("events", [])

    return {
        "problem_id":    problem_id,
        "case_index":    case_index,
        "case_name":     case_name,
        "solution_mode": result.get("trace_mode", solution_mode),
        "input":         input_args,
        "expected":      expected,
        "actual":        result.get("actual"),
        "passed":        result.get("passed", False),
        "trace":         trace_events,
        "error":         result.get("error"),
    }
