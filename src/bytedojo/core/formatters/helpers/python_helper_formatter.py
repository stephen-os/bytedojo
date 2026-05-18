"""
PythonHelperFormatter - produces companion .py files for data structures
that require a class definition alongside the solution.
"""

from bytedojo.core.formatters.helpers.base_helper_formatter import BaseHelperFormatter
from bytedojo.core.models.data_structure import DataStructure


_FILENAMES = {
    DataStructure.BINARY_TREE: "tree_node.py",
    DataStructure.LINKED_LIST: "list_node.py",
    DataStructure.N_ARY_TREE:  "node.py",
}

_TEMPLATES = {
    DataStructure.BINARY_TREE: (
        "class TreeNode:\n"
        "    def __init__(self, val=0, left=None, right=None):\n"
        "        self.val = val\n"
        "        self.left = left\n"
        "        self.right = right\n"
    ),
    DataStructure.LINKED_LIST: (
        "class ListNode:\n"
        "    def __init__(self, val=0, next=None):\n"
        "        self.val = val\n"
        "        self.next = next\n"
    ),
    DataStructure.N_ARY_TREE: (
        "class Node:\n"
        "    def __init__(self, val=None, children=None):\n"
        "        self.val = val\n"
        "        self.children = children if children is not None else []\n"
    ),
}


class PythonHelperFormatter(BaseHelperFormatter):

    def filename(self, ds: DataStructure) -> str:
        return _FILENAMES[ds]

    def build_file(self, ds: DataStructure) -> str:
        return _TEMPLATES[ds]
