"""
Type conversion + comparison + display for the ByteDojo Python runner.

Standalone module — no bytedojo imports. Copied into the per-problem
build directory by TestService and consumed by runner.py.

The canonical type vocabulary mirrors src/bytedojo/core/models/canonical_type.py
but is duplicated here so this file can run as a standalone script in
the build dir with no package dependencies.
"""

from collections import deque
from typing import Any, Dict, List, Optional


# ----------------------------------------------------------------------------
# LeetCode reference types — TreeNode / ListNode definitions live in their
# own sibling modules (tree_node.py / list_node.py) placed by `dojo fetch`
# whenever the problem needs them. The user's solution.py imports them the
# same way we do, so node-class customizations carry across both sides.
#
# Lazy-import only fires when a case actually uses TREE_NODE / LIST_NODE;
# primitive-only problems never resolve the node modules.
# ----------------------------------------------------------------------------

def _tree_node_cls():
    """Pull TreeNode from the sibling tree_node module. Raises if missing."""
    from tree_node import TreeNode  # noqa: WPS433 — intentional lazy import
    return TreeNode


def _list_node_cls():
    """Pull ListNode from the sibling list_node module. Raises if missing."""
    from list_node import ListNode  # noqa: WPS433 — intentional lazy import
    return ListNode


# ----------------------------------------------------------------------------
# Parsing JSON values into native Python / reference types
# ----------------------------------------------------------------------------

def parse_value(value: Any, canonical_type: str) -> Any:
    """Convert a JSON-loaded value into the canonical type's native shape."""
    if value is None:
        return None

    t = canonical_type

    if t in ("INT32", "INT64"):
        return int(value)
    if t == "FLOAT64":
        return float(value)
    if t == "BOOL":
        return bool(value)
    if t in ("CHAR", "STRING"):
        return str(value)
    if t == "VOID":
        return None

    if t.endswith("_ARRAY"):
        element_type = t[:-len("_ARRAY")]
        # LIST_NODE_ARRAY is an array of linked-list heads
        if element_type == "LIST_NODE":
            return [build_list(x) for x in value]
        return [parse_value(x, element_type) for x in value]

    if t.endswith("_MATRIX"):
        element_type = t[:-len("_MATRIX")]
        return [[parse_value(x, element_type) for x in row] for row in value]

    if t == "TREE_NODE":
        return build_tree(value)
    if t == "LIST_NODE":
        return build_list(value)

    raise ValueError(f"Unknown canonical type: {t}")


def build_tree(level_order: Optional[List[Any]]) -> Any:
    """Build a binary tree from level-order encoding using the user's TreeNode."""
    if not level_order:
        return None
    if level_order[0] is None:
        return None

    TreeNode = _tree_node_cls()
    root = TreeNode(level_order[0])
    queue = deque([root])
    i = 1
    n = len(level_order)
    while queue and i < n:
        node = queue.popleft()
        if i < n:
            v = level_order[i]
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
            i += 1
        if i < n:
            v = level_order[i]
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
            i += 1
    return root


def build_list(flat: Optional[List[Any]]) -> Any:
    """Build a linked list from a flat value list using the user's ListNode."""
    if not flat:
        return None
    ListNode = _list_node_cls()
    head = ListNode(flat[0])
    cur = head
    for v in flat[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


# ----------------------------------------------------------------------------
# Serialization (output → comparable shape)
# ----------------------------------------------------------------------------

def serialize_tree(root) -> List[Any]:
    """Serialize a tree to level-order with trailing nulls trimmed."""
    if root is None:
        return []
    out: List[Any] = []
    queue: deque = deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        # Append both children even if null — they get trimmed below
        queue.append(node.left if node.left is not None else None)
        queue.append(node.right if node.right is not None else None)
    while out and out[-1] is None:
        out.pop()
    return out


def serialize_list(head) -> List[Any]:
    """Walk a linked list into a flat value list."""
    out: List[Any] = []
    while head is not None:
        out.append(head.val)
        head = head.next
    return out


# ----------------------------------------------------------------------------
# Comparison
# ----------------------------------------------------------------------------

_FLOAT_EPS = 1e-5


def compare(actual: Any, expected: Any, return_type: str, comparison: str) -> bool:
    """Compare actual vs expected per canonical type + comparison mode."""
    if return_type == "VOID":
        # Function returned None by spec — always passes the return check.
        return True

    if return_type == "TREE_NODE":
        return serialize_tree(actual) == serialize_tree(expected)
    if return_type == "LIST_NODE":
        return serialize_list(actual) == serialize_list(expected)
    if return_type == "LIST_NODE_ARRAY":
        a = [serialize_list(x) for x in (actual or [])]
        e = [serialize_list(x) for x in (expected or [])]
        return a == e

    if return_type == "FLOAT64":
        return _float_equal(actual, expected)
    if return_type == "FLOAT64_ARRAY":
        return _float_array_equal(actual, expected)

    if comparison == "unordered_all":
        actual = _sort_recursive(actual)
        expected = _sort_recursive(expected)

    return actual == expected


def _float_equal(a: Any, b: Any, eps: float = _FLOAT_EPS) -> bool:
    """Absolute-tolerance float equality. NaN==NaN passes for our purposes."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # NaN check: NaN != NaN, so if both are not-equal-to-themselves we treat them as equal.
    if a != a and b != b:
        return True
    try:
        return abs(float(a) - float(b)) <= eps
    except (TypeError, ValueError):
        return False


def _float_array_equal(a: Any, b: Any) -> bool:
    """Element-wise float equality with tolerance."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    return all(_float_equal(x, y) for x, y in zip(a, b))


def _sort_recursive(value: Any) -> Any:
    """Recursively sort nested lists so order-insensitive compares work."""
    if isinstance(value, list):
        return sorted((_sort_recursive(x) for x in value), key=_sort_key)
    return value


def _sort_key(value: Any):
    """Comparable key for sorting heterogeneous values (incl. None and lists)."""
    if value is None:
        return (0,)
    if isinstance(value, list):
        return (1, tuple(_sort_key(x) for x in value))
    return (2, value)


# ----------------------------------------------------------------------------
# Display (for failure output)
# ----------------------------------------------------------------------------

def format_input(input_dict: Dict[str, Any]) -> str:
    """Render an input dict as `name = value, name = value` for CLI display."""
    return ", ".join(f"{k} = {_format_value(v)}" for k, v in input_dict.items())


def _format_value(value: Any) -> str:
    """Compact display formatter for an arbitrary JSON-shaped value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    return repr(value)


def display(value: Any, return_type: str) -> str:
    """Render a return value for the test result envelope."""
    if return_type == "VOID":
        return "None"
    if value is None:
        return "null"
    if return_type == "TREE_NODE":
        return repr(serialize_tree(value))
    if return_type == "LIST_NODE":
        return repr(serialize_list(value))
    if return_type == "LIST_NODE_ARRAY":
        return repr([serialize_list(x) for x in (value or [])])
    return repr(value)
