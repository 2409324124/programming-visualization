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


# ── subcommand: render-visual ────────────────────────────────────────


def cmd_render_visual(args: argparse.Namespace) -> None:
    """Execute the 'render-visual' subcommand.

    Pipeline::

        problem_dir + case_index
              ↓  visual_runtime.get_runtime_context()
        RuntimeContext
              ↓  visual_binder.bind_lesson()
        BoundLesson
              ↓  visual_compiler.compile_visual()
        frames[]
              ↓  render_story_html.render_visual_to_html()
        HTML

    All values in the generated HTML come from the real harness execution.
    """
    problem_dir = args.problem_dir
    case_index  = int(args.case_index)
    lesson_path = args.lesson
    output_path = args.output

    if not os.path.isdir(problem_dir):
        print(f"错误: 题目目录不存在: {problem_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(lesson_path):
        print(f"错误: lesson 文件不存在: {lesson_path}", file=sys.stderr)
        sys.exit(1)

    # Step 1: run harness
    try:
        from pv.visual_runtime import get_runtime_context, ValidationOnlyError
    except ImportError as exc:
        print(f"错误: visual_runtime 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        rt_ctx = get_runtime_context(
            problem_dir=problem_dir,
            case_index=case_index,
            solution_mode="visual",
        )
    except ValidationOnlyError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        print("该题目没有 visual_solution.py，无法生成语义动画。"
              "使用 render-lesson 查看 authored demo。", file=sys.stderr)
        sys.exit(1)
    except (FileNotFoundError, IndexError) as exc:
        print(f"错误: 运行 harness 失败: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"错误: 未预期异常: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\u8fd0行完成: case {case_index} / "
          f"{'PASSED' if rt_ctx['passed'] else 'FAILED'} / "
          f"actual={rt_ctx['actual']} / trace events={len(rt_ctx['trace'])}")

    # Step 2: load and validate lesson
    try:
        from pv.lesson_schema import validate_lesson
        from pv.story_compiler import compile_lesson_file as _unused  # noqa: F401
    except ImportError as exc:
        print(f"错误: lesson_schema 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    with open(lesson_path, encoding="utf-8") as fh:
        lesson_dict = json.load(fh)

    errors = validate_lesson(lesson_dict)
    if errors:
        print(f"错误: lesson 文件校验失败:", file=sys.stderr)
        for e in errors:
            print(f"  • {e}", file=sys.stderr)
        sys.exit(1)

    # Step 3: bind lesson to runtime
    try:
        from pv.visual_binder import bind_lesson, BindingError
    except ImportError as exc:
        print(f"错误: visual_binder 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        bound = bind_lesson(lesson_dict, rt_ctx)
    except BindingError as exc:
        print(f"错误: lesson 与运行时不一致 (BindingError):", file=sys.stderr)
        print(f"  {exc}", file=sys.stderr)
        sys.exit(1)

    print("绑定完成: lesson 与 runtime 一致")

    # Step 4: compile visual frames
    try:
        from pv.visual_compiler import compile_visual
    except ImportError as exc:
        print(f"错误: visual_compiler 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    frames = compile_visual(bound)
    print(f"编译完成: {len(frames)} 帧")

    # Step 5: render HTML
    try:
        from pv.render_story_html import render_visual_to_html
    except ImportError as exc:
        print(f"错误: render_story_html 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    title = lesson_dict.get("title", "Runtime-bound Visualization")
    html_output = render_visual_to_html(frames, title=title)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"HTML 已写入: {output_path}")
    else:
        print(html_output)


def cmd_render_code(args: argparse.Namespace) -> None:
    problem_dir = args.problem_path
    if not os.path.isdir(problem_dir):
        print(f"错误: 题目目录不存在: {problem_dir}", file=sys.stderr)
        sys.exit(1)
    
    solution_path = args.solution or os.path.join(problem_dir, "solution.py")
    if not os.path.isfile(solution_path):
        print(f"错误: solution 文件不存在: {solution_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        from pv.learner_runtime import get_learner_runtime
        from pv.render_learner_html import render_learner_to_html
    except ImportError as e:
        print(f"错误: 模块未实现: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        runtime = get_learner_runtime(problem_dir, solution_path, args.case_index)
    except Exception as e:
        print(f"错误: 运行失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    html = render_learner_to_html(runtime)
    
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML 已写入: {args.output}")
    else:
        print(html)


def cmd_serve(args: argparse.Namespace) -> None:
    """Execute the 'serve' subcommand — start local interactive runner."""
    try:
        from pv.server import run_server
    except ImportError as exc:
        print(f"错误: server 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    host = args.host
    port = int(args.port)

    if host == "0.0.0.0":
        print("⚠ 警告: 监听 0.0.0.0 会暴露给局域网。", file=sys.stderr)
        print("   仅用于受信任的本地开发环境。", file=sys.stderr)
        print()

    project_root = args.project_root
    if project_root:
        print(f"使用指定的项目根目录: {project_root}")
    run_server(host=host, port=port, project_root=project_root)


def cmd_validate_problem(args: argparse.Namespace) -> None:
    """Execute oracle-based generated validation for a problem."""
    try:
        from pv.problem_validation import ProblemValidationError, validate_problem
    except ImportError as exc:
        print(f"错误: problem_validation 模块加载失败: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        result = validate_problem(
            problem_dir=args.problem_path,
            generated_count=args.generated,
            seed=args.seed,
            solution_file=args.solution,
        )
    except (ProblemValidationError, ImportPolicyError, PVError) as exc:
        print(f"错误: {exc.user_message}", file=sys.stderr)
        if exc.detail:
            print(f"  详情: {exc.detail}", file=sys.stderr)
        sys.exit(1)

    problem_id = result["problem_id"]
    fixed = result["fixed"]
    generated = result["generated"]
    total_passed = fixed["passed"] + generated["passed"]
    total_count = fixed["total"] + generated["total"]

    print(f"Problem: {problem_id}")
    print(f"fixed: {fixed['passed']}/{fixed['total']} passed")
    print(f"generated: {generated['passed']}/{generated['total']} passed")
    print(f"total: {total_passed}/{total_count} passed")

    if not result["passed"]:
        failure = result["first_failure"]
        case = failure["case"]
        run_result = failure["result"]
        print()
        print(
            f"first failure: {failure['source']} case {failure['index']} "
            f"({case.get('name', 'unnamed')})"
        )
        print(f"input: {_format_args(case.get('args', {}))}")
        print(f"expected: {_format_value(run_result.get('expected'))}")
        print(f"actual: {_format_value(run_result.get('actual'))}")
        if run_result.get("message"):
            print(f"message: {run_result['message']}")
        if run_result.get("error"):
            print(f"error: {run_result['error']}")
        sys.exit(1)


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
        help="编译 lesson.story.json 为概念动画 HTML（authored-only / experimental）",
    )
    render_lesson_parser.add_argument("lesson_json_path", help="lesson.story.json 文件路径")
    render_lesson_parser.add_argument("--output", "-o", help="输出 HTML 文件路径（不指定则打印到 stdout）")

    # render-code subcommand
    render_code_parser = subparsers.add_parser("render-code", help="渲染用户代码执行过程为 HTML")
    render_code_parser.add_argument("problem_path", help="题目目录路径")
    render_code_parser.add_argument("--solution", help="用户 solution.py 路径（默认使用 problem_dir/solution.py）")
    render_code_parser.add_argument("--case-index", type=int, default=0, help="用例索引（默认 0）")
    render_code_parser.add_argument("--output", "-o", help="输出 HTML 文件路径")

    # serve subcommand
    serve_parser = subparsers.add_parser(
        "serve",
        help="启动本地 LeetCode-style 交互运行器",
    )
    serve_parser.add_argument("--host", default="127.0.0.1",
                              help="监听地址（默认 127.0.0.1）")
    serve_parser.add_argument("--port", default=8765, type=int,
                              help="监听端口（默认 8765）")
    serve_parser.add_argument("--project-root", default=None,
                              help="项目根目录（默认自动检测）")

    # validate-problem subcommand
    validate_parser = subparsers.add_parser(
        "validate-problem",
        help="运行固定用例 + oracle 生成用例验证题目",
    )
    validate_parser.add_argument("problem_path", help="题目目录路径")
    validate_parser.add_argument("--generated", default=100, type=int,
                                 help="生成用例数量（默认 100）")
    validate_parser.add_argument("--seed", default=0, type=int,
                                 help="随机种子（默认 0）")
    validate_parser.add_argument("--solution", default="solution.py",
                                 help="使用的解法文件（默认 solution.py）")

    # render-visual subcommand (new primary path)
    render_visual_parser = subparsers.add_parser(
        "render-visual",
        help="主入口：真实运行 harness + 绑定 lesson 生成可视化 HTML",
    )
    render_visual_parser.add_argument("problem_dir", help="题目目录（如 problems/0001_two_sum）")
    render_visual_parser.add_argument("--case-index", default=0, type=int,
                                      dest="case_index", help="用例索引（默认 0）")
    render_visual_parser.add_argument("--lesson", required=True,
                                      help="lesson.story.json 文件路径")
    render_visual_parser.add_argument("--output", "-o",
                                      help="输出 HTML 文件路径（不指定则打印到 stdout）")

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
    elif args.command == "render-visual":
        cmd_render_visual(args)
    elif args.command == "render-code":
        cmd_render_code(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "validate-problem":
        cmd_validate_problem(args)
    else:
        parser.print_help()
