"""
PythonHelperFormatter - produces companion .py files for node structures
that require a class definition alongside the solution.
"""

from typing import List

from bytedojo.core.formatters.helpers.base_helper_formatter import (
    BaseHelperFormatter,
    node_structures,
)
from bytedojo.core.models.data_structure import DataStructure
from bytedojo.core.models.test_bundle import TestSignature

_IMPORTS = {
    DataStructure.BINARY_TREE: "from tree_node import TreeNode",
    DataStructure.LINKED_LIST: "from list_node import ListNode",
}

_FILENAMES = {
    DataStructure.BINARY_TREE: "tree_node.py",
    DataStructure.LINKED_LIST: "list_node.py",
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
}


class PythonHelperFormatter(BaseHelperFormatter):

    def filename(self, ds: DataStructure) -> str:
        return _FILENAMES[ds]

    def build_file(self, ds: DataStructure) -> str:
        return _TEMPLATES[ds]

    def companion_imports(self, signature: TestSignature) -> List[str]:
        return [_IMPORTS[ds] for ds in node_structures(signature)]
