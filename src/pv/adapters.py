"""Convert between JSON-serializable case data and Python algorithm objects.

Phase 1: only ``kind: "builtin"`` (pass-through) is supported.
Other kinds raise ``AdapterError``.  Linked-list and tree helpers are
provided as stubs for Phase 2.
"""

from __future__ import annotations

from pv.errors import AdapterError


# ── public API ────────────────────────────────────────────────────────

def adapt_input(args: dict, adapter_config: dict | None) -> dict:
    """Convert ``cases.json`` args from JSON structures to Python objects.

    If *adapter_config* is ``None`` or has no ``"input"`` key, return
    *args* unchanged.  Otherwise, for each key in ``adapter_config["input"]``,
    deserialize the value according to the configured *kind*.
    """
    if not adapter_config or "input" not in adapter_config:
        return args

    result = dict(args)
    for key, spec in adapter_config["input"].items():
        if key in result:
            kind = spec.get("kind", "builtin") if isinstance(spec, dict) else "builtin"
            result[key] = _deserialize(result[key], kind)
    return result


def adapt_output(value, adapter_config: dict | None):
    """Serialize a Python return value back to JSON-comparable form.

    If *adapter_config* is ``None`` or has no ``"output"`` key, return
    *value* unchanged.  Otherwise, serialize according to the output spec.
    """
    if not adapter_config or "output" not in adapter_config:
        return value

    spec = adapter_config["output"]
    kind = spec.get("kind", "builtin") if isinstance(spec, dict) else "builtin"
    return _serialize(value, kind)


# ── internal helpers ──────────────────────────────────────────────────

def _deserialize(raw, kind: str):
    if kind == "builtin":
        return raw
    raise AdapterError(
        f"Unknown input kind: {kind}",
        user_message=f"不支持的输入类型 {kind}。当前支持：builtin。",
    )


def _serialize(value, kind: str):
    if kind == "builtin":
        return value
    raise AdapterError(
        f"Unknown output kind: {kind}",
        user_message=f"不支持的输出类型 {kind}。当前支持：builtin。",
    )


# ── Phase 2 stubs (linked list & tree) ───────────────────────────────

def _build_linked_list(values: list):
    """Build a singly linked list from a list of values.  Returns the head ``ListNode``."""
    from pv.structures import ListNode

    if not values:
        return None
    head = ListNode(values[0])
    curr = head
    for v in values[1:]:
        curr.next = ListNode(v)
        curr = curr.next
    return head


def _list_from_linked_list(head) -> list:
    """Convert a linked list to a plain list of values."""
    result: list = []
    while head:
        result.append(head.val)
        head = head.next
    return result


def _build_tree(values: list):
    """Build a binary tree from a level-order list.  Returns the root ``TreeNode``."""
    # Stub – will implement in Phase 2
    from pv.structures import TreeNode  # noqa: F401

    return None  # placeholder


def _list_from_tree(root) -> list:
    """Convert a binary tree to a level-order list."""
    return []  # placeholder
