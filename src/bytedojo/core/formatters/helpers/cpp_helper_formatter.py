"""
CppHelperFormatter - produces companion .hpp header files for data structures
that require a struct or class definition alongside the solution.
"""

from bytedojo.core.formatters.helpers.base_helper_formatter import BaseHelperFormatter
from bytedojo.core.models.data_structure import DataStructure


_FILENAMES = {
    DataStructure.BINARY_TREE: "tree_node.hpp",
    DataStructure.LINKED_LIST: "list_node.hpp",
    DataStructure.N_ARY_TREE:  "node.hpp",
}

_TEMPLATES = {
    DataStructure.BINARY_TREE: (
        "#ifndef TREE_NODE_HPP_\n"
        "#define TREE_NODE_HPP_\n\n"
        "struct TreeNode {\n"
        "    int val;\n"
        "    TreeNode *left;\n"
        "    TreeNode *right;\n"
        "    TreeNode() : val(0), left(nullptr), right(nullptr) {}\n"
        "    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}\n"
        "    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}\n"
        "};\n\n"
        "#endif  // TREE_NODE_HPP_\n"
    ),
    DataStructure.LINKED_LIST: (
        "#ifndef LIST_NODE_HPP_\n"
        "#define LIST_NODE_HPP_\n\n"
        "struct ListNode {\n"
        "    int val;\n"
        "    ListNode *next;\n"
        "    ListNode() : val(0), next(nullptr) {}\n"
        "    ListNode(int x) : val(x), next(nullptr) {}\n"
        "    ListNode(int x, ListNode *next) : val(x), next(next) {}\n"
        "};\n\n"
        "#endif  // LIST_NODE_HPP_\n"
    ),
    DataStructure.N_ARY_TREE: (
        "#ifndef NODE_HPP_\n"
        "#define NODE_HPP_\n\n"
        "#include <vector>\n\n"
        "class Node {\n"
        "public:\n"
        "    int val;\n"
        "    std::vector<Node*> children;\n"
        "    Node() {}\n"
        "    Node(int val) : val(val) {}\n"
        "    Node(int val, std::vector<Node*> children) : val(val), children(children) {}\n"
        "};\n\n"
        "#endif  // NODE_HPP_\n"
    ),
}


class CppHelperFormatter(BaseHelperFormatter):

    def filename(self, ds: DataStructure) -> str:
        return _FILENAMES[ds]

    def build_file(self, ds: DataStructure) -> str:
        return _TEMPLATES[ds]
