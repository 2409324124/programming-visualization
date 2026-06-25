"""Pre-flight import check for learner submissions.

This is NOT a security sandbox.  It is an educational guardrail that helps
learners understand which libraries are appropriate for algorithm-practice code.
"""

import ast

STDLIB_ALLOW = {
    "typing", "collections", "math", "functools", "itertools",
    "heapq", "bisect", "random", "string", "re", "enum",
    "dataclasses", "copy", "operator",
}
BLOCKED = {
    "os", "sys", "subprocess", "socket", "shutil", "pathlib",
    "glob", "platform", "ctypes", "signal",
}
UNSUPPORTED = {
    "numpy", "pandas", "torch", "tensorflow", "scipy",
    "sklearn", "matplotlib", "seaborn", "plotly",
}


def check_imports(file_path: str) -> dict:
    """Parse *file_path* with ast, collect all imports, and check against policy.

    Returns a dict:
        {"ok": bool, "violations": [str], "warnings": [str]}
    """
    with open(file_path, encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"ok": False, "violations": [f"语法错误: {e}"], "warnings": []}

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])

    # Deduplicate
    imports = list(set(imports))

    violations: list[str] = []
    warnings: list[str] = []

    for name in imports:
        if name in BLOCKED:
            violations.append(
                f"不允许导入 {name}（系统访问模块）。本工具只运行算法练习代码，"
                f"不需要文件系统、进程或网络操作。"
            )
        elif name in UNSUPPORTED:
            violations.append(
                f"不支持的依赖 {name}。本工具只使用 Python 标准库，"
                f"不安装第三方数据处理库。请用纯 Python 实现算法。"
            )
        elif name not in STDLIB_ALLOW:
            warnings.append(
                f"注意：导入了 {name}，不在已知安全列表内。如果运行时出错请检查。"
            )

    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
    }
