"""Core harness: load problems, run cases, collect traces, check results."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import uuid
from contextlib import redirect_stderr, redirect_stdout

from pv.errors import (
    CasesInvalid,
    CasesLoadError,
    ClassNotFoundError,
    ImportPolicyError,
    MethodNotFoundError,
    ProblemLoadError,
    ProblemMetaInvalid,
    PVError,
    SolutionImportError,
)
from pv.submission_policy import check_imports
from pv.trace_schema import TraceBuilder
from pv.checkers import check
from pv.adapters import adapt_input, adapt_output


# ── helpers ────────────────────────────────────────────────────────────

def _get_checker_name(problem_meta: dict) -> str:
    return problem_meta.get("checker", {}).get("name", "exact")


def _get_max_events(problem_meta: dict) -> int:
    return problem_meta.get("limits", {}).get("max_events", 10000)


# ── loaders ────────────────────────────────────────────────────────────

def load_problem_meta(problem_dir: str) -> dict:
    """Read and validate ``problem.json`` from *problem_dir*."""
    path = os.path.join(problem_dir, "problem.json")
    if not os.path.isfile(path):
        raise ProblemLoadError(
            detail=f"文件不存在: {path}",
        )
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise ProblemLoadError(
            detail=f"解析失败: {exc}",
        ) from exc

    # ── required-field validation ──────────────────────────────────
    missing: list[str] = []
    if not isinstance(data.get("problem_id"), str):
        missing.append("problem_id (str)")
    entry = data.get("entry")
    if not isinstance(entry, dict):
        missing.append("entry (dict)")
    else:
        if not isinstance(entry.get("class_name"), str):
            missing.append("entry.class_name (str)")
        if not isinstance(entry.get("method_name"), str):
            missing.append("entry.method_name (str)")
    if not isinstance(data.get("pattern_tags"), list):
        missing.append("pattern_tags (list)")
    if not isinstance(data.get("difficulty"), str):
        missing.append("difficulty (str)")

    if missing:
        raise ProblemMetaInvalid(
            detail=f"缺失或类型错误的字段: {', '.join(missing)}",
        )
    return data


def load_cases(problem_dir: str) -> list[dict]:
    """Read and validate ``cases.json`` from *problem_dir*."""
    path = os.path.join(problem_dir, "cases.json")
    if not os.path.isfile(path):
        raise CasesLoadError(
            detail=f"文件不存在: {path}",
        )
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise CasesLoadError(
            detail=f"解析失败: {exc}",
        ) from exc

    if not isinstance(data, list) or len(data) == 0:
        raise CasesInvalid(
            detail="cases.json 必须是非空列表。",
        )

    for i, case in enumerate(data):
        if not isinstance(case, dict):
            raise CasesInvalid(detail=f"cases[{i}] 不是 dict。")
        for field in ("name", "args", "expected"):
            if field not in case:
                raise CasesInvalid(
                    detail=f"cases[{i}] 缺少必要字段 '{field}'。",
                )
    return data


def load_solution(file_path: str):
    """Dynamically import *file_path* as a Python module (isolated)."""
    if not os.path.isfile(file_path):
        raise SolutionImportError(
            detail=f"文件不存在: {file_path}",
        )
    module_name = f"pv_dynamic_{uuid.uuid4().hex[:8]}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:
        raise SolutionImportError(
            detail=f"导入失败: {exc}",
        ) from exc
    return module


# ── execution ──────────────────────────────────────────────────────────

def run_case(
    problem_meta: dict,
    case: dict,
    solution_path: str,
    save_trace: bool = False,
    trace_output_dir: str = "",
    case_index: int = 0,
) -> dict:
    """Execute a single test case and return a result dict."""
    case_name = case["name"]
    expected = case["expected"]
    checker_name = _get_checker_name(problem_meta)
    max_events = _get_max_events(problem_meta)

    # Optionally prepare a trace builder
    trace: TraceBuilder | None = None
    if save_trace:
        trace = TraceBuilder(
            problem_meta=problem_meta,
            case=case,
            max_events=max_events,
        )

    try:
        # 1. Load solution module (fresh each time for state isolation)
        module = load_solution(solution_path)

        # 2. Locate the class
        class_name = problem_meta["entry"]["class_name"]
        cls = getattr(module, class_name, None)
        if cls is None:
            raise ClassNotFoundError(
                detail=f"模块中未找到类 '{class_name}'。",
            )

        # 3. Instantiate (try passing trace if saving; track acceptance)
        trace_supported = False
        if save_trace:
            try:
                instance = cls(trace=trace)
                trace_supported = True
            except TypeError:
                instance = cls()
                trace_supported = False
        else:
            instance = cls()

        # 4. Locate the method
        method_name = problem_meta["entry"]["method_name"]
        method = getattr(instance, method_name, None)
        if method is None:
            raise MethodNotFoundError(
                detail=f"实例上未找到方法 '{method_name}'。",
            )

        # 5. Adapt input
        adapter_config = problem_meta.get("adapter")
        adapted_args = adapt_input(case["args"], adapter_config)

        # 6. Call the method (capture stdout/stderr so learner prints don't leak)
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
            result = method(**adapted_args)
        stdout_str = captured_stdout.getvalue()
        stderr_str = captured_stderr.getvalue()

        # 7. Adapt output
        normalized = adapt_output(result, adapter_config)

        # 8. Check result
        check_result = check(normalized, expected, checker_name=checker_name)
        passed = check_result.passed

        # 9. Finalise trace
        if trace is not None:
            trace.finish("passed" if passed else "wrong_answer", normalized)
            trace_dir = trace_output_dir or "."
            trace_path = os.path.join(trace_dir, f"trace.case{case_index}.json")
            with open(trace_path, "w", encoding="utf-8") as f:
                f.write(trace.to_json())
        else:
            trace_path = None

        # Determine trace_mode
        if trace_supported and trace is not None and trace.step_count > 0:
            trace_mode = "semantic"
        elif save_trace and not trace_supported:
            trace_mode = "validation_only"
        else:
            trace_mode = "none"

        return {
            "case_name": case_name,
            "passed": passed,
            "expected": expected,
            "actual": normalized,
            "message": check_result.message,
            "error": None,
            "trace_path": trace_path,
            "step_count": trace.step_count if trace else 0,
            "truncated": trace._truncated if trace else False,
            "trace_mode": trace_mode,
            "stdout": stdout_str,
            "stderr": stderr_str,
        }

    except PVError as exc:
        # Harness-level user-facing error — use the friendly user_message
        if trace is not None:
            trace.finish("error", None)
            trace_dir = trace_output_dir or "."
            trace_path = os.path.join(trace_dir, f"trace.case{case_index}.json")
            with open(trace_path, "w", encoding="utf-8") as f:
                f.write(trace.to_json())
        else:
            trace_path = None

        return {
            "case_name": case_name,
            "passed": False,
            "expected": expected,
            "actual": None,
            "message": exc.user_message,
            "error": f"{type(exc).__name__}: {exc}",
            "trace_path": trace_path,
            "step_count": trace.step_count if trace else 0,
            "truncated": trace._truncated if trace else False,
            "trace_mode": "none",
            "stdout": "",
            "stderr": "",
        }

    except Exception as exc:
        # 10. Catch-all: do NOT crash the whole run
        if trace is not None:
            trace.finish("error", None)
            trace_dir = trace_output_dir or "."
            trace_path = os.path.join(trace_dir, f"trace.case{case_index}.json")
            with open(trace_path, "w", encoding="utf-8") as f:
                f.write(trace.to_json())
        else:
            trace_path = None

        return {
            "case_name": case_name,
            "passed": False,
            "expected": expected,
            "actual": None,
            "message": f"代码运行时出错：{type(exc).__name__}: {exc}",
            "error": f"{type(exc).__name__}: {exc}",
            "trace_path": trace_path,
            "step_count": trace.step_count if trace else 0,
            "truncated": trace._truncated if trace else False,
            "trace_mode": "none",
            "stdout": "",
            "stderr": "",
        }


def run_all_cases(
    problem_dir: str,
    solution_file: str = "solution.py",
    save_trace: bool = False,
) -> list[dict]:
    """Load problem + cases, run every case, return list of result dicts."""
    problem_meta = load_problem_meta(problem_dir)
    cases = load_cases(problem_dir)
    solution_path = os.path.join(problem_dir, solution_file)

    # Check import policy before running any cases
    policy_result = check_imports(solution_path)
    if not policy_result["ok"]:
        msg = "代码包含不允许的导入：\n" + "\n".join(
            f"  • {v}" for v in policy_result["violations"]
        )
        raise ImportPolicyError(detail=msg, user_message=msg)

    results: list[dict] = []
    for i, case in enumerate(cases):
        result = run_case(
            problem_meta=problem_meta,
            case=case,
            solution_path=solution_path,
            save_trace=save_trace,
            trace_output_dir=problem_dir if save_trace else "",
            case_index=i,
        )
        results.append(result)
    return results
