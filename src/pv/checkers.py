"""Output checkers for comparing actual vs expected results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from pv.errors import CheckerError
except ImportError:
    from .errors import CheckerError


@dataclass
class CheckResult:
    passed: bool
    expected: Any
    actual: Any
    normalized_expected: Any
    normalized_actual: Any
    message: str


def _check_exact(actual: Any, expected: Any) -> CheckResult:
    passed = actual == expected
    if passed:
        message = "输出与预期完全一致。"
    else:
        message = f"输出与预期不符。预期 {expected}，实际得到 {actual}。"
    return CheckResult(
        passed=passed,
        expected=expected,
        actual=actual,
        normalized_expected=expected,
        normalized_actual=actual,
        message=message,
    )


def _normalize_pairs(value: Any) -> list[list]:
    """Sort each pair internally, then sort the outer list.

    Handles two cases:
    - Flat list like [0, 1]: treated as a single pair → [[0, 1]]
    - Nested list like [[0,1],[2,3]]: each inner list is a pair
    """
    if not value:
        return []
    # Detect flat list: first element is not a list/tuple
    if not isinstance(value[0], (list, tuple)):
        pairs = [sorted(value)]
    else:
        pairs = [sorted(pair) for pair in value]
    pairs.sort()
    return pairs


def _check_unordered_pairs(actual: Any, expected: Any) -> CheckResult:
    norm_expected = _normalize_pairs(expected)
    norm_actual = _normalize_pairs(actual)
    passed = norm_actual == norm_expected
    if passed:
        message = "输出顺序不影响结果，索引对一致。"
    else:
        message = (
            f"输出与预期不符。预期索引对 {expected}，实际得到索引对 {actual}。"
        )
    return CheckResult(
        passed=passed,
        expected=expected,
        actual=actual,
        normalized_expected=norm_expected,
        normalized_actual=norm_actual,
        message=message,
    )


def _check_linked_list_equal(actual: Any, expected: Any) -> CheckResult:
    """Compare two linked lists by their value sequences.

    Both *actual* and *expected* are already normalised to plain lists by the
    adapter before reaching the checker, so this is a list-vs-list comparison
    with a friendly message.
    """
    passed = actual == expected
    if passed:
        message = "链表逐节点值完全一致。"
    else:
        message = f"链表不匹配。预期 {expected}，实际得到 {actual}。"
    return CheckResult(
        passed=passed,
        expected=expected,
        actual=actual,
        normalized_expected=expected,
        normalized_actual=actual,
        message=message,
    )


_CHECKERS: dict[str, Any] = {
    "exact": _check_exact,
    "unordered_pairs": _check_unordered_pairs,
    "linked_list_equal": _check_linked_list_equal,
}


def check(
    actual: Any,
    expected: Any,
    checker_name: str = "exact",
    context: dict | None = None,
) -> CheckResult:
    """Main entry point. Route to the appropriate checker function."""
    if checker_name not in _CHECKERS:
        raise CheckerError(
            f"Unknown checker: {checker_name!r}. "
            f"Available checkers: {sorted(_CHECKERS)}"
        )
    return _CHECKERS[checker_name](actual, expected)
