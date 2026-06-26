"""learner_runtime.py — Run user code through harness with line-level tracing."""

from pathlib import Path
from typing import Any


def get_learner_runtime(
    problem_dir: str | Path,
    solution_path: str | Path,
    case_index: int = 0,
    max_trace_events: int = 1000,
) -> dict:
    """Run user solution with line-level tracing and return runtime context.
    
    Delegates to harness.run_case for actual/expected/passed/stdout.
    Uses sys.settrace via LineTracer for line-level execution tracing.
    
    Returns dict with: problem_id, case_index, input, expected, actual,
    passed, stdout, stderr, error, trace_mode, line_trace, truncated.
    """
    from pv.harness import load_problem_meta, load_cases, run_case
    from pv.learner_trace import LineTracer
    
    problem_dir = Path(problem_dir).resolve()
    solution_path = Path(solution_path).resolve()
    
    meta = load_problem_meta(str(problem_dir))
    cases = load_cases(str(problem_dir))
    
    if case_index >= len(cases):
        raise IndexError(f"case_index {case_index} out of range")
    
    case = cases[case_index]
    problem_id = meta.get("problem_id", problem_dir.name)
    
    method_name = meta["entry"]["method_name"]
    
    # Run with line-level tracing (only inside the target method)
    tracer = LineTracer(str(solution_path), target_function=method_name, max_events=max_trace_events)
    tracer.start()
    
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_case(
                problem_meta=meta,
                case=case,
                solution_path=str(solution_path),
                save_trace=False,
                trace_output_dir=tmpdir,
                case_index=case_index,
            )
    finally:
        tracer.stop()
    
    trace_data = tracer.to_dict()
    
    return {
        "problem_id":       problem_id,
        "case_index":       case_index,
        "case_name":        case.get("name", f"case_{case_index}"),
        "solution_path":    str(solution_path),
        "input":            case.get("args", {}),
        "expected":         case.get("expected"),
        "actual":           result.get("actual"),
        "passed":           result.get("passed", False),
        "stdout":           result.get("stdout", ""),
        "stderr":           result.get("stderr", ""),
        "error":            result.get("error"),
        "trace_mode":       "line_level",
        "line_trace":       trace_data.get("events", []),
        "total_steps":      trace_data.get("total_steps", 0),
        "truncated":        trace_data.get("truncated", False),
        "source_code":      _read_source(str(solution_path)),
    }


def _read_source(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "# source not available"
