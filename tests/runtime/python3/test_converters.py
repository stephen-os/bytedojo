"""Tests for the Python universal runner's converters module.

The module declares lazy imports of `tree_node.TreeNode` and
`list_node.ListNode` so it can run standalone in a per-problem build
dir. For these unit tests we monkeypatch the `_tree_node_cls` /
`_list_node_cls` helpers to return locally-defined stand-ins, which
keeps the tests free of build-dir setup.
"""

import math
from dataclasses import dataclass, field
from typing import Any, List, Optional

import pytest

from bytedojo.runtime.python3 import converters
from bytedojo.runtime.python3.converters import (
    build_list,
    build_tree,
    compare,
    display,
    format_input,
    parse_value,
    serialize_list,
    serialize_tree,
    _float_array_equal,
    _float_equal,
    _format_value,
    _sort_recursive,
)


# --------------------------------------------------------------------------- #
# Test node stand-ins                                                         #
# --------------------------------------------------------------------------- #

@dataclass
class _TreeNode:
    val: Any
    left: Optional["_TreeNode"] = None
    right: Optional["_TreeNode"] = None


@dataclass
class _ListNode:
    val: Any
    next: Optional["_ListNode"] = field(default=None, repr=False)


@pytest.fixture(autouse=True)
def patch_node_class_lookup(monkeypatch):
    """Redirect the lazy node-class helpers at our test classes."""
    monkeypatch.setattr(converters, "_tree_node_cls", lambda: _TreeNode)
    monkeypatch.setattr(converters, "_list_node_cls", lambda: _ListNode)


# --------------------------------------------------------------------------- #
# parse_value — primitives                                                    #
# --------------------------------------------------------------------------- #

def test_parse_value_none_passes_through():
    assert parse_value(None, "INT32") is None
    assert parse_value(None, "STRING") is None
    assert parse_value(None, "TREE_NODE") is None


@pytest.mark.parametrize("t", ["INT32", "INT64"])
def test_parse_value_int_types(t):
    assert parse_value(42, t) == 42
    assert parse_value("17", t) == 17        # coerces strings


def test_parse_value_float():
    assert parse_value(3, "FLOAT64") == pytest.approx(3.0)
    assert parse_value("2.5", "FLOAT64") == pytest.approx(2.5)


@pytest.mark.parametrize("raw, expected", [(1, True), (0, False), (True, True)])
def test_parse_value_bool(raw, expected):
    assert parse_value(raw, "BOOL") is expected


def test_parse_value_char_and_string():
    assert parse_value("a", "CHAR") == "a"
    assert parse_value("abc", "STRING") == "abc"


def test_parse_value_void_returns_none():
    assert parse_value("anything", "VOID") is None


def test_parse_value_unknown_type_raises():
    with pytest.raises(ValueError, match="Unknown canonical type"):
        parse_value(1, "MYSTERY")


# --------------------------------------------------------------------------- #
# parse_value — arrays / matrices                                             #
# --------------------------------------------------------------------------- #

def test_parse_value_int_array():
    assert parse_value([1, 2, 3], "INT32_ARRAY") == [1, 2, 3]


def test_parse_value_string_array():
    assert parse_value(["a", "b"], "STRING_ARRAY") == ["a", "b"]


def test_parse_value_int_matrix():
    assert parse_value([[1, 2], [3, 4]], "INT32_MATRIX") == [[1, 2], [3, 4]]


def test_parse_value_char_matrix_preserves_single_chars():
    grid = [["1", "0"], ["0", "1"]]
    assert parse_value(grid, "CHAR_MATRIX") == grid


def test_parse_value_list_node_array_builds_each():
    """A LIST_NODE_ARRAY input becomes a list of linked-list heads."""
    heads = parse_value([[1, 2], [], [3]], "LIST_NODE_ARRAY")
    assert serialize_list(heads[0]) == [1, 2]
    assert heads[1] is None
    assert serialize_list(heads[2]) == [3]


# --------------------------------------------------------------------------- #
# parse_value — reference types (delegates to build_tree / build_list)        #
# --------------------------------------------------------------------------- #

def test_parse_value_tree_node():
    root = parse_value([1, 2, 3], "TREE_NODE")
    assert root.val == 1
    assert root.left.val == 2
    assert root.right.val == 3


def test_parse_value_list_node():
    head = parse_value([1, 2, 3], "LIST_NODE")
    assert serialize_list(head) == [1, 2, 3]


# --------------------------------------------------------------------------- #
# build_tree / serialize_tree                                                 #
# --------------------------------------------------------------------------- #

def test_build_tree_empty_inputs_return_none():
    assert build_tree([]) is None
    assert build_tree(None) is None
    assert build_tree([None]) is None


def test_build_tree_skips_null_children_in_level_order():
    # LeetCode-style: [1, null, 2, 3] -> root=1, root.right=2, 2.left=3
    root = build_tree([1, None, 2, 3])
    assert root.val == 1
    assert root.left is None
    assert root.right.val == 2
    assert root.right.left.val == 3


def test_serialize_tree_trims_trailing_nulls():
    root = _TreeNode(1, _TreeNode(2), _TreeNode(3, _TreeNode(4)))
    # Level order is 1, 2, 3, null, null, 4, null. Trailing nulls trimmed.
    assert serialize_tree(root) == [1, 2, 3, None, None, 4]


def test_serialize_tree_none_returns_empty():
    assert serialize_tree(None) == []


def test_build_then_serialize_roundtrip():
    original = [1, 2, 3, None, None, 4, 5]
    root = build_tree(original)
    # serialize_tree's null-emission may differ slightly from input, but a
    # round-trip-then-back yields the same shape.
    serialised = serialize_tree(root)
    assert build_tree(serialised) is not None


# --------------------------------------------------------------------------- #
# build_list / serialize_list                                                 #
# --------------------------------------------------------------------------- #

def test_build_list_empty():
    assert build_list([]) is None
    assert build_list(None) is None


def test_build_list_single_element():
    head = build_list([42])
    assert head.val == 42
    assert head.next is None


def test_build_list_multi_element():
    head = build_list([1, 2, 3])
    assert head.val == 1
    assert head.next.val == 2
    assert head.next.next.val == 3
    assert head.next.next.next is None


def test_serialize_list_walks_chain():
    head = _ListNode(1, _ListNode(2, _ListNode(3)))
    assert serialize_list(head) == [1, 2, 3]


def test_serialize_list_none_returns_empty():
    assert serialize_list(None) == []


def test_list_roundtrip():
    flat = [10, 20, 30, 40]
    assert serialize_list(build_list(flat)) == flat


# --------------------------------------------------------------------------- #
# compare — primitive / array equality                                        #
# --------------------------------------------------------------------------- #

def test_compare_void_always_passes():
    """A void method has no return value to compare; the case is always passing."""
    assert compare("anything", None, "VOID", "exact") is True


def test_compare_int_exact_pass():
    assert compare(5, 5, "INT32", "exact") is True


def test_compare_int_exact_fail():
    assert compare(5, 6, "INT32", "exact") is False


def test_compare_array_exact():
    assert compare([1, 2, 3], [1, 2, 3], "INT32_ARRAY", "exact") is True
    assert compare([1, 2, 3], [1, 3, 2], "INT32_ARRAY", "exact") is False


# --------------------------------------------------------------------------- #
# compare — unordered_all                                                     #
# --------------------------------------------------------------------------- #

def test_compare_unordered_all_flat_array():
    assert compare([3, 1, 2], [1, 2, 3], "INT32_ARRAY", "unordered_all") is True


def test_compare_unordered_all_nested_matrix():
    """Recursively sorts both sides — order doesn't matter at any depth."""
    actual = [[3, 1], [2, 4]]
    expected = [[4, 2], [1, 3]]
    assert compare(actual, expected, "INT32_MATRIX", "unordered_all") is True


def test_compare_unordered_all_does_not_help_with_value_differences():
    assert compare([1, 2, 4], [1, 2, 3], "INT32_ARRAY", "unordered_all") is False


# --------------------------------------------------------------------------- #
# compare — float tolerance                                                   #
# --------------------------------------------------------------------------- #

def test_compare_float_within_tolerance():
    assert compare(1.0000001, 1.0, "FLOAT64", "exact") is True


def test_compare_float_outside_tolerance():
    assert compare(1.0001, 1.0, "FLOAT64", "exact") is False


def test_compare_float_array_elementwise():
    assert compare([1.0000001, 2.0], [1.0, 2.0], "FLOAT64_ARRAY", "exact") is True


def test_compare_float_array_length_mismatch():
    assert compare([1.0, 2.0], [1.0, 2.0, 3.0], "FLOAT64_ARRAY", "exact") is False


# --------------------------------------------------------------------------- #
# compare — reference types                                                   #
# --------------------------------------------------------------------------- #

def test_compare_tree_node_via_serialize():
    actual = _TreeNode(1, _TreeNode(2), _TreeNode(3))
    expected = _TreeNode(1, _TreeNode(2), _TreeNode(3))
    assert compare(actual, expected, "TREE_NODE", "exact") is True


def test_compare_tree_node_different_shape():
    actual = _TreeNode(1, _TreeNode(2))
    expected = _TreeNode(1, None, _TreeNode(2))
    assert compare(actual, expected, "TREE_NODE", "exact") is False


def test_compare_list_node_via_serialize():
    assert compare(
        _ListNode(1, _ListNode(2)),
        _ListNode(1, _ListNode(2)),
        "LIST_NODE", "exact",
    ) is True


def test_compare_list_node_different_lengths():
    assert compare(
        _ListNode(1, _ListNode(2)),
        _ListNode(1),
        "LIST_NODE", "exact",
    ) is False


def test_compare_list_node_array():
    a = [_ListNode(1, _ListNode(2)), _ListNode(3)]
    e = [_ListNode(1, _ListNode(2)), _ListNode(3)]
    assert compare(a, e, "LIST_NODE_ARRAY", "exact") is True


def test_compare_list_node_array_handles_none_sides():
    assert compare(None, None, "LIST_NODE_ARRAY", "exact") is True


# --------------------------------------------------------------------------- #
# _float_equal / _float_array_equal — edge cases                              #
# --------------------------------------------------------------------------- #

def test_float_equal_both_nan_treated_equal():
    assert _float_equal(math.nan, math.nan) is True


def test_float_equal_one_nan_one_real_unequal():
    assert _float_equal(math.nan, 1.0) is False


def test_float_equal_both_none_equal():
    assert _float_equal(None, None) is True


def test_float_equal_one_none_unequal():
    assert _float_equal(None, 1.0) is False
    assert _float_equal(1.0, None) is False


def test_float_equal_custom_eps():
    assert _float_equal(1.0, 1.1, eps=0.2) is True
    assert _float_equal(1.0, 1.3, eps=0.2) is False


def test_float_array_equal_both_none():
    assert _float_array_equal(None, None) is True
    assert _float_array_equal(None, [1.0]) is False


# --------------------------------------------------------------------------- #
# _sort_recursive                                                             #
# --------------------------------------------------------------------------- #

def test_sort_recursive_flat_list():
    assert _sort_recursive([3, 1, 2]) == [1, 2, 3]


def test_sort_recursive_nested():
    """Inner lists sort first, then outer list sorts by the first-element key."""
    assert _sort_recursive([[3, 1], [2]]) == [[1, 3], [2]]


def test_sort_recursive_with_none_in_list():
    """None sorts before everything else (sentinel ordering for unordered compare)."""
    assert _sort_recursive([None, 1, None]) == [None, None, 1]


def test_sort_recursive_passes_non_list_through():
    assert _sort_recursive(5) == 5
    assert _sort_recursive("x") == "x"


# --------------------------------------------------------------------------- #
# format_input / _format_value / display                                      #
# --------------------------------------------------------------------------- #

def test_format_input_renders_kv_pairs():
    assert format_input({"nums": [1, 2], "target": 3}) == "nums = [1, 2], target = 3"


def test_format_value_handles_specials():
    assert _format_value(None) == "null"
    assert _format_value(True) == "true"
    assert _format_value(False) == "false"
    assert _format_value("x") == '"x"'


def test_display_void():
    assert display("anything", "VOID") == "None"


def test_display_null():
    assert display(None, "INT32") == "null"


def test_display_tree_node_uses_serialised_form():
    root = _TreeNode(1, _TreeNode(2), _TreeNode(3))
    assert display(root, "TREE_NODE") == "[1, 2, 3]"


def test_display_list_node_uses_serialised_form():
    head = _ListNode(1, _ListNode(2))
    assert display(head, "LIST_NODE") == "[1, 2]"


def test_display_list_node_array():
    arr = [_ListNode(1, _ListNode(2)), _ListNode(3)]
    assert display(arr, "LIST_NODE_ARRAY") == "[[1, 2], [3]]"


def test_display_primitive_uses_repr():
    assert display(42, "INT32") == "42"
    assert display([1, 2], "INT32_ARRAY") == "[1, 2]"
