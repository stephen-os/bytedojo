"""
BaseHelperFormatter - abstract base for language-specific helper file formatters.

Helper formatters produce the companion files needed alongside a solution —
TreeNode, ListNode, Node class definitions — derived from the problem's
data_structures field rather than by parsing snippets.

Which structures require a helper file is determined here. Per-language
filename and file content are defined in each subclass.
"""

from abc import ABC, abstractmethod
from typing import Dict

from bytedojo.core.models.data_structure import DataStructure
from bytedojo.core.models.problem import Problem


_HELPER_STRUCTURES = {
    DataStructure.BINARY_TREE,
    DataStructure.LINKED_LIST,
    DataStructure.N_ARY_TREE,
}


class BaseHelperFormatter(ABC):
    """Abstract base for language-specific helper file formatters."""

    @classmethod
    def requires_helper(cls, ds: DataStructure) -> bool:
        """True when a data structure needs a companion file."""
        return ds in _HELPER_STRUCTURES

    @abstractmethod
    def filename(self, ds: DataStructure) -> str:
        """Return the output filename for a given data structure."""
        ...

    @abstractmethod
    def build_file(self, ds: DataStructure) -> str:
        """Return the complete file content for a given data structure."""
        ...

    def files_for(self, problem: Problem) -> Dict[str, str]:
        """Return {filename: content} for every data structure that needs a helper."""
        return {
            self.filename(ds): self.build_file(ds)
            for ds in problem.data_structures
            if self.requires_helper(ds)
        }

    def companion_imports(self, problem: Problem) -> list[str]:
        """Return import/include lines for companion files needed by this problem.

        Default: none. Override in languages where companion files must be
        explicitly referenced in the solution (C++, Python).
        """
        return []
