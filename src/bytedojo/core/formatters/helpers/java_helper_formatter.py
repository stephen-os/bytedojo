"""
JavaHelperFormatter - produces companion .java files for data structures
that require a class definition alongside the solution.
"""

from bytedojo.core.formatters.helpers.base_helper_formatter import BaseHelperFormatter
from bytedojo.core.models.data_structure import DataStructure


_FILENAMES = {
    DataStructure.BINARY_TREE: "TreeNode.java",
    DataStructure.LINKED_LIST: "ListNode.java",
    DataStructure.N_ARY_TREE:  "Node.java",
}

_TEMPLATES = {
    DataStructure.BINARY_TREE: (
        "public class TreeNode {\n"
        "    int val;\n"
        "    TreeNode left;\n"
        "    TreeNode right;\n"
        "    TreeNode() {}\n"
        "    TreeNode(int val) { this.val = val; }\n"
        "    TreeNode(int val, TreeNode left, TreeNode right) {\n"
        "        this.val = val;\n"
        "        this.left = left;\n"
        "        this.right = right;\n"
        "    }\n"
        "}\n"
    ),
    DataStructure.LINKED_LIST: (
        "public class ListNode {\n"
        "    int val;\n"
        "    ListNode next;\n"
        "    ListNode() {}\n"
        "    ListNode(int val) { this.val = val; }\n"
        "    ListNode(int val, ListNode next) { this.val = val; this.next = next; }\n"
        "}\n"
    ),
    DataStructure.N_ARY_TREE: (
        "import java.util.List;\n\n"
        "public class Node {\n"
        "    public int val;\n"
        "    public List<Node> children;\n"
        "    public Node() {}\n"
        "    public Node(int val) { this.val = val; }\n"
        "    public Node(int val, List<Node> children) {\n"
        "        this.val = val;\n"
        "        this.children = children;\n"
        "    }\n"
        "}\n"
    ),
}


class JavaHelperFormatter(BaseHelperFormatter):

    def filename(self, ds: DataStructure) -> str:
        return _FILENAMES[ds]

    def build_file(self, ds: DataStructure) -> str:
        return _TEMPLATES[ds]
