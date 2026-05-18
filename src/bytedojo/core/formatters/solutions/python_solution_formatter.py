"""
Python formatter for LeetCode solution files.
"""

import re
from typing import List, Dict

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.formatters.comments.python_comment_formatter import PythonCommentFormatter
from bytedojo.core.formatters.helpers.python_helper_formatter import PythonHelperFormatter
from bytedojo.core.formatters.solutions.base_solution_formatter import BaseSolutionFormatter
from bytedojo.core.logger import get_logger


_PYTHON_BASELINE_IMPORTS: tuple = (
    "from collections import Counter, defaultdict, deque",
    "from functools import lru_cache",
    "from heapq import heappop, heappush",
    "from math import inf",
    "from typing import Dict, List, Optional, Set, Tuple",
)


class PythonSolutionFormatter(BaseSolutionFormatter):
    """Formats LeetCode problems as Python solution files."""

    def __init__(self):
        self.logger = get_logger()
        self.comment_formatter = PythonCommentFormatter()
        self._helper = PythonHelperFormatter()

    def extra_files(self, problem: Problem) -> Dict[str, str]:
        return self._helper.files_for(problem)

    def format_imports(self, _problem: Problem) -> str:
        """Baseline stdlib imports."""
        return "\n".join(_PYTHON_BASELINE_IMPORTS)

    def format_solution(self, problem: Problem) -> str:
        """Extract and clean the starter class body from the LeetCode snippet."""
        return self._get_class_body(problem)

    def format_main_block(self, _problem: Problem) -> str:
        """Return a minimal `if __name__ == "__main__":` entry point."""
        return 'if __name__ == "__main__":\n    pass\n'

    # ========================================================================
    # Code Extraction and Processing
    # ========================================================================

    def _get_class_body(self, problem: Problem) -> str:
        """Extract the starter class body, stripping top-level imports."""
        code = problem.get_snippet(CodeLanguage.PYTHON)
        if not code:
            self.logger.warning(
                f"No Python3 snippet for problem #{problem.problem_detail.id}"
            )
            return "# No Python template available"

        code = self._ensure_pass_in_methods(code)
        code = self._strip_top_level_imports(code)
        return code.strip("\n") + "\n"

    def _strip_top_level_imports(self, code: str) -> str:
        """Remove any `import`/`from ... import` lines at top level."""
        out = []
        for line in code.split("\n"):
            stripped = line.lstrip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                continue
            out.append(line)
        return "\n".join(out)

    def _ensure_pass_in_methods(self, code: str) -> str:
        """Insert `pass` into empty method bodies so the snippet parses."""
        lines = code.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]
            result.append(line)

            stripped = line.strip()
            if stripped.startswith('#'):
                i += 1
                continue

            if 'def ' in line and line.strip().endswith(':'):
                if self._is_empty_method(lines, i):
                    current_indent = len(line) - len(line.lstrip())
                    result.append(' ' * (current_indent + 4) + 'pass')

            i += 1

        return '\n'.join(result)

    def _is_empty_method(self, lines: List[str], method_line_idx: int) -> bool:
        """Check if a method definition is empty."""
        if method_line_idx + 1 >= len(lines):
            return True

        next_line = lines[method_line_idx + 1]
        next_stripped = next_line.strip()

        if next_stripped.startswith('#'):
            return False

        current_indent = len(lines[method_line_idx]) - len(lines[method_line_idx].lstrip())
        next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else current_indent

        return next_indent <= current_indent or not next_line.strip()
