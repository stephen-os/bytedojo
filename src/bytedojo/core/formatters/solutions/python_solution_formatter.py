"""
Python formatter — synthesises a solution stub from the bundle signature.

No LeetCode snippet is involved (§11): the `class Solution` stub is
built from the bundle's method name + typed signature, mapping the
type vocabulary to PEP-484 annotations.
"""

from typing import Dict

from bytedojo.core.formatters.comments.python_comment_formatter import (
    PythonCommentFormatter,
)
from bytedojo.core.formatters.helpers.python_helper_formatter import (
    PythonHelperFormatter,
)
from bytedojo.core.formatters.solutions.base_solution_formatter import (
    BaseSolutionFormatter,
)
from bytedojo.core.models.data_structure import DataStructure
from bytedojo.core.models.primitive import Primitive
from bytedojo.core.models.signature import Signature
from bytedojo.core.models.test_bundle import TestBundle

_PYTHON_BASELINE_IMPORTS: tuple = (
    "from collections import Counter, defaultdict, deque",
    "from functools import lru_cache",
    "from heapq import heappop, heappush",
    "from math import inf",
    "from typing import Dict, List, Optional, Set, Tuple",
)

_PRIMITIVE_ANNOTATIONS = {
    Primitive.INT32: "int",
    Primitive.INT64: "int",
    Primitive.FLOAT64: "float",
    Primitive.BOOL: "bool",
    Primitive.CHAR: "str",
    Primitive.STRING: "str",
    Primitive.VOID: "None",
}

_NODE_ANNOTATIONS = {
    DataStructure.BINARY_TREE: "Optional[TreeNode]",
    DataStructure.LINKED_LIST: "Optional[ListNode]",
}


def annotation(sig: Signature) -> str:
    """PEP-484 annotation for a type-vocabulary signature."""
    if sig.base is DataStructure.ARRAY:
        return f"List[{_base_annotation(sig.element)}]"
    if sig.base is DataStructure.MATRIX:
        return f"List[List[{_base_annotation(sig.element)}]]"
    return _base_annotation(sig.base)


def _base_annotation(base) -> str:
    if base in _NODE_ANNOTATIONS:
        return _NODE_ANNOTATIONS[base]
    if base in _PRIMITIVE_ANNOTATIONS:
        return _PRIMITIVE_ANNOTATIONS[base]
    return "object"


class PythonSolutionFormatter(BaseSolutionFormatter):
    """Synthesises Python solution files from bundle signatures."""

    def __init__(self):
        self.comment_formatter = PythonCommentFormatter()
        self._helper = PythonHelperFormatter()

    def extra_files(self, bundle: TestBundle) -> Dict[str, str]:
        return self._helper.files_for(bundle.signature)

    def format_imports(self, bundle: TestBundle) -> str:
        """Baseline stdlib imports plus companion imports for node types."""
        companions = self._helper.companion_imports(bundle.signature)
        companion_block = ("\n" + "\n".join(companions)) if companions else ""
        return "\n".join(_PYTHON_BASELINE_IMPORTS) + companion_block

    def format_solution(self, bundle: TestBundle) -> str:
        """Synthesise `class Solution` with a typed method stub."""
        params = ", ".join(
            ["self"]
            + [f"{p.name}: {annotation(p.type)}" for p in bundle.signature.params]
        )
        returns = annotation(bundle.signature.returns)
        return (
            f"class Solution:\n"
            f"    def {bundle.method}({params}) -> {returns}:\n"
            f"        pass\n"
        )

    def format_main_block(self, _bundle: TestBundle) -> str:
        """Return a minimal `if __name__ == "__main__":` entry point."""
        return 'if __name__ == "__main__":\n    pass\n'
