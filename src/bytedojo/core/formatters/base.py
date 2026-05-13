"""
BaseFormatter - abstract base for language-specific problem formatters.

Each subclass renders a `Problem` into the placement-ready content of
the main solution file for its language and may emit sibling files
(node-class modules, header files) via `extra_files`. Lookup of the
right subclass is centralised in the `core.formatters` package
registry; callers never branch on `CodeLanguage` themselves.
"""

from abc import ABC, abstractmethod
from typing import Dict

from bytedojo.core.models.problem import Problem


class BaseFormatter(ABC):
    """Abstract base for language-specific problem formatters."""

    @abstractmethod
    def format(self, problem: Problem) -> str:
        """
        Format a problem into the main solution-file content.

        Args:
            problem: Problem object

        Returns:
            Complete file content as string
        """
        pass

    def extra_files(self, problem: Problem) -> Dict[str, str]:
        """
        Sibling files to place next to the main solution file.

        Override per-language when the problem needs auxiliary files —
        e.g. a separate `tree_node.py` / `TreeNode.java` / `tree_node.hpp`
        when the starter snippet references a node class. Keys are
        filenames (no directory component); values are the file content.

        Default: no extras.
        """
        return {}
