"""CLI for programming-visualization: run problems, render traces."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from pv.harness import load_problem_meta, load_cases, run_case, run_all_cases
from pv.submission_policy import check_imports
from pv.errors import ImportPolicyError, PVError


# ── helpers ────────────────────────────────────────────────────────────


def _format_args(args: dict) -> str:
    """Format case args dict as a readable string, e.g. 'nums=[2,7,11,15], target=9'."""
    parts = []
    for k, v in args.items():
        parts.append(f"{k}={v!r}")
    return ", ".join(parts)


def _format_value(value: Any) -> str:
    """Format a result value for display."""
    if value is None:
        return "None"
    return repr(value)


def _dot_leader(label: str, status: str, width: int = 60) -> str:
    """Build a line like 'Case 0: basic example .............. PASSED'."""
    # Ensure label doesn't exceed width
    if len(label) >= width:
        return f"{label} {status}"
    dots = "." * (width - len(label))
    return f"{label} {dots} {status}"


# ── subcommand: run ────────────────────────────────────────────────────


def cmd_run(args: argparse.Namespace) -> None:
    """Execute the 'run' subcommand."""
    problem_dir = args.problem_path
    solution_file = args.solution
    save_trace = args.save_trace

    # Validate problem directory exists
    if not os.path.isdir(problem_dir):
        print(f"错误: 题目目录不存在: {problem_dir}", file=sys.stderr)
        sys.exit(1)

    # Load problem metadata
    try:
        meta = load_problem_meta(problem_dir)
    except PVError as exc:
        print(f"错误: {exc.user_message}", file=sys.stderr)
        if exc.detail:
            print(f"  详情: {exc.detail}", file=sys.stderr)
        sys.exit(1)

    problem_id = meta.get("problem_id", os.path.basename(problem_dir))
    title = meta.get("display_title") or meta.get("title") or problem_id
    tags = meta.get("pattern_tags", [])
    difficulty = meta.get("difficulty", "unknown")

    # Determine which cases to run
    use_single_case = args.case is not None

    if use_single_case:
        # Load cases to validate index
        try:
            cases = load_cases(problem_dir)
        except PVError as exc:
            print(f"错误: {exc.user_message}", file=sys.stderr)
            if exc.detail:
                print(f"  详情: {exc.detail}", file=sys.stderr)
            sys.exit(1)

        case_index = args.case
        if case_index < 0 or case_index >= len(cases):
            print(
                f"错误: 用例索引 {case_index} 超出范围（共 {len(cases)} 个用例，有效范围 0-{len(cases)-1}）",
                file=sys.stderr,
            )
            sys.exit(1)

        selected_cases = [(case_index, cases[case_index])]
    else:
        # --all (default): run all cases
        try:
            cases = load_cases(problem_dir)
        except PVError as exc:
            print(f"错误: {exc.user_message}", file=sys.stderr)
            if exc.detail:
                print(f"  详情: {exc.detail}", file=sys.stderr)
            sys.exit(1)
        selected_cases = list(enumerate(cases))

    # Print header
    print("=" * 60)
    print(f"Problem: {title} ({problem_id})")
    print(f"Tags: {', '.join(tags)}")
    print(f"Difficulty: {difficulty}")
    print("=" * 60)
    print()

    # Run cases and collect results
    results: list[dict] = []
    saved_trace_paths: list[str] = []

    # Check import policy before running cases
    solution_path = os.path.join(problem_dir, solution_file)
    policy_result = check_imports(solution_path)
    if not policy_result["ok"]:
        msg = "代码包含不允许的导入：\n" + "\n".join(
            f"  • {v}" for v in policy_result["violations"]
        )
        print(f"错误: {msg}", file=sys.stderr)
        sys.exit(1)
    if policy_result.get("warnings"):
        for w in policy_result["warnings"]:
            print(f"警告: {w}", file=sys.stderr)

    for case_index, case in selected_cases:
        try:
            result = run_case(
                problem_meta=meta,
                case=case,
                solution_path=os.path.join(problem_dir, solution_file),
                save_trace=save_trace,
                trace_output_dir=problem_dir if save_trace else "",
                case_index=case_index,
            )
        except PVError as exc:
            # Harness-level error (e.g. solution import failure)
            result = {
                "case_name": case.get("name", f"case {case_index}"),
                "passed": False,
                "expected": case.get("expected"),
                "actual": None,
                "message": exc.user_message,
                "error": str(exc),
                "trace_path": None,
                "step_count": 0,
                "truncated": False,
                "trace_mode": "none",
                "stdout": "",
                "stderr": "",
            }

        results.append(result)

        # Format and print per-case output
        status_str = "PASSED" if result["passed"] else "FAILED"
        label = f"Case {case_index}: {result['case_name']}"
        print(_dot_leader(label, status_str))

        # Input
        args_str = _format_args(case.get("args", {}))
        print(f"  输入: {args_str}")

        # Expected
        print(f"  预期: {_format_value(result['expected'])}")

        # Actual
        print(f"  实际: {_format_value(result['actual'])}")

        # Error detail (if any)
        if result["error"]:
            error_detail = result.get("message", result["error"])
            print(f"  错误: {error_detail}")

        # Step count (事件数) — only when no error
        if not result["error"] and result.get("step_count"):
            print(f"  事件数: {result['step_count']}")

        # Trace availability
        trace_mode = result.get("trace_mode", "none")
        if trace_mode == "validation_only" and save_trace:
            print("  trace: validation only（代码无追踪钩子，只记录输入输出）")

        # Print warning if code used print() instead of return
        stdout_val = result.get("stdout", "")
        if stdout_val:
            truncated = stdout_val[:200] + "..." if len(stdout_val) > 200 else stdout_val
            print(f"  ⚠ 代码有 print 输出（{truncated}），但判题只看 return 值。如果答案不对，请检查是否忘了 return。")

        print()

        # Track saved trace paths
        if result.get("trace_path"):
            saved_trace_paths.append(result["trace_path"])

    # Summary
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    print("=" * 60)
    print(f"结果: {passed_count}/{total_count} 通过")
    print("=" * 60)

    # Show saved trace file paths (prefer relative to cwd for readability)
    if save_trace and saved_trace_paths:
        print()
        print("追踪文件已保存到:")
        cwd = os.getcwd()
        for path in saved_trace_paths:
            try:
                display_path = os.path.relpath(path, cwd)
            except ValueError:
                display_path = path
            print(f"  {display_path}")

    # Exit with non-zero if any case failed
    if passed_count < total_count:
        sys.exit(1)


# ── subcommand: render-text ────────────────────────────────────────────


def cmd_render_text(args: argparse.Namespace) -> None:
    """Execute the 'render-text' subcommand."""
    trace_path = args.trace_json_path

    if not os.path.isfile(trace_path):
        print(f"错误: trace 文件不存在: {trace_path}", file=sys.stderr)
        sys.exit(1)

    # Read the trace JSON
    try:
        with open(trace_path, encoding="utf-8") as f:
            trace_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"错误: 无法读取 trace 文件: {exc}", file=sys.stderr)
        sys.exit(1)

    # Import render_trace_to_text (may not exist yet)
    try:
        from pv.render_text import render_trace_to_text
    except ImportError:
        print(
            "错误: pv.render_text 模块尚未实现，无法渲染文本。",
            file=sys.stderr,
        )
        sys.exit(1)

    # Render and print
    output = render_trace_to_text(trace_data)
    print(output)


# ── subcommand: render-html ────────────────────────────────────────────


def cmd_render_html(args: argparse.Namespace) -> None:
    """Execute the 'render-html' subcommand."""
    trace_path = args.trace_json_path

    if not os.path.isfile(trace_path):
        print(f"错误: trace 文件不存在: {trace_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(trace_path, encoding="utf-8") as f:
            trace_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"错误: 无法读取 trace 文件: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        from pv.render_html import render_trace_to_html
    except ImportError:
        print("错误: pv.render_html 模块尚未实现。", file=sys.stderr)
        sys.exit(1)

    html_output = render_trace_to_html(trace_data)

    output_path = args.output
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"HTML 已写入: {output_path}")
    else:
        print(html_output)


# ── subcommand: render-story ───────────────────────────────────────────


def cmd_render_story(args: argparse.Namespace) -> None:
    """Execute the 'render-story' subcommand."""
    trace_path = args.trace_json_path
    
    if not os.path.isfile(trace_path):
        print(f"错误: trace 文件不存在: {trace_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(trace_path, encoding="utf-8") as f:
            trace_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"错误: 无法读取 trace 文件: {exc}", file=sys.stderr)
        sys.exit(1)
    
    try:
        from pv.storyboard import build_storyboard
        from pv.render_story_html import render_story_to_html
    except ImportError as e:
        print(f"错误: storyboard 模块尚未实现: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        frames = build_storyboard(trace_data)
    except (ValueError, NotImplementedError) as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    title = trace_data.get("problem", {}).get("display_title", "Storyboard")
    html_output = render_story_to_html(frames, title=f"{title} — 执行动画")
    
    output_path = args.output
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"HTML 已写入: {output_path}")
    else:
        print(html_output)


# ── subcommand: render-lesson ──────────────────────────────────────────


def cmd_render_lesson(args: argparse.Namespace) -> None:
    """Execute the 'render-lesson' subcommand.

    Compiles a ``lesson.story.json`` through the lesson-script pipeline::

        lesson.story.json
              ↓  story_compiler.compile_lesson()
        frames[]
              ↓  render_story_html.render_story_to_html()
        HTML animation

    This is the recommended path going forward.  Unlike ``render-story``,
    it does **not** depend on a trace file.
    """
    lesson_path = args.lesson_json_path

    if not os.path.isfile(lesson_path):
        print(f"错误: lesson 文件不存在: {lesson_path}", file=sys.stderr)
        sys.exit(1)

    try:
        from pv.story_compiler import compile_lesson_file
        from pv.render_story_html import render_story_to_html
    except ImportError as exc:
        print(f"错误: story_compiler 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        frames, title = compile_lesson_file(lesson_path)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"错误: 无法编译 lesson 文件: {exc}", file=sys.stderr)
        sys.exit(1)

    html_output = render_story_to_html(frames, title=f"{title} — 概念动画")

    output_path = args.output
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"HTML 已写入: {output_path}")
    else:
        print(html_output)


# ── main ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(prog="pv", description="编程可视化学习器")
    subparsers = parser.add_subparsers(dest="command")

    # run subcommand
    run_parser = subparsers.add_parser("run", help="运行题目")
    run_parser.add_argument("problem_path", help="题目目录路径")
    group = run_parser.add_mutually_exclusive_group()
    group.add_argument("--case", type=int, help="只运行指定索引的用例")
    group.add_argument("--all", action="store_true", help="运行所有用例")
    run_parser.add_argument(
        "--solution",
        default="solution.py",
        help="使用的解法文件（默认 solution.py）",
    )
    run_parser.add_argument(
        "--save-trace",
        action="store_true",
        help="保存 trace JSON 文件",
    )

    # render-text subcommand
    render_parser = subparsers.add_parser("render-text", help="渲染 trace JSON 为文本")
    render_parser.add_argument("trace_json_path", help="trace JSON 文件路径")

    # render-html subcommand
    render_html_parser = subparsers.add_parser("render-html", help="渲染 trace JSON 为 HTML")
    render_html_parser.add_argument("trace_json_path", help="trace JSON 文件路径")
    render_html_parser.add_argument("--output", "-o", help="输出 HTML 文件路径（不指定则打印到 stdout）")

    # render-story subcommand
    render_story_parser = subparsers.add_parser("render-story", help="渲染 trace JSON 为故事动画 HTML（旧路径，依赖 trace）")
    render_story_parser.add_argument("trace_json_path", help="trace JSON 文件路径")
    render_story_parser.add_argument("--output", "-o", help="输出 HTML 文件路径（不指定则打印到 stdout）")

    # render-lesson subcommand
    render_lesson_parser = subparsers.add_parser(
        "render-lesson",
        help="编译 lesson.story.json 为概念动画 HTML（新路径，教学脚本驱动）",
    )
    render_lesson_parser.add_argument("lesson_json_path", help="lesson.story.json 文件路径")
    render_lesson_parser.add_argument("--output", "-o", help="输出 HTML 文件路径（不指定则打印到 stdout）")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "render-text":
        cmd_render_text(args)
    elif args.command == "render-html":
        cmd_render_html(args)
    elif args.command == "render-story":
        cmd_render_story(args)
    elif args.command == "render-lesson":
        cmd_render_lesson(args)
    else:
        parser.print_help()
