"""
C++ formatter for LeetCode solution files.
"""

from typing import Dict, Tuple

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.formatters.comments.cpp_comment_formatter import CppCommentFormatter
from bytedojo.core.formatters.helpers.cpp_helper_formatter import CppHelperFormatter
from bytedojo.core.formatters.solutions.base_solution_formatter import BaseSolutionFormatter
from bytedojo.core.logger import get_logger


_CPP_BASELINE_INCLUDES: Tuple[str, ...] = (
    "#include <algorithm>",
    "#include <climits>",
    "#include <cmath>",
    "#include <cstdint>",
    "#include <deque>",
    "#include <functional>",
    "#include <iostream>",
    "#include <map>",
    "#include <queue>",
    "#include <set>",
    "#include <stack>",
    "#include <string>",
    "#include <unordered_map>",
    "#include <unordered_set>",
    "#include <utility>",
    "#include <vector>",
)


class CppSolutionFormatter(BaseSolutionFormatter):
    """Formats LeetCode problems as C++ solution files."""

    def __init__(self):
        self.logger = get_logger()
        self.comment_formatter = CppCommentFormatter()
        self._helper = CppHelperFormatter()

    def extra_files(self, problem: Problem) -> Dict[str, str]:
        return self._helper.files_for(problem)

    def format_imports(self, _problem: Problem) -> str:
        """Baseline stdlib includes."""
        return "\n".join(_CPP_BASELINE_INCLUDES) + "\n\nusing namespace std;"

    def format_solution(self, problem: Problem) -> str:
        """Extract the class body from the LeetCode snippet."""
        return self._get_cpp_code(problem)

    def format_main_block(self, _problem: Problem) -> str:
        """Return a minimal `int main()` entry point."""
        return "int main() {\n    return 0;\n}\n"

    # ========================================================================
    # Code Extraction and Processing
    # ========================================================================

    def _get_cpp_code(self, problem: Problem) -> str:
        """Extract the class body, stripping includes and `using` directives."""
        code = problem.get_snippet(CodeLanguage.CPP)
        if not code:
            self.logger.warning(
                f"No C++ snippet for problem #{problem.problem_detail.id}"
            )
            return "// No C++ template available"

        return self._strip_top_level_directives(code)

    def _strip_top_level_directives(self, code: str) -> str:
        """Drop top-level `#include ...` and `using ...;` lines from the snippet."""
        out = []
        for line in code.split("\n"):
            stripped = line.lstrip()
            if stripped.startswith("#include"):
                continue
            if stripped.startswith("using ") and stripped.rstrip().endswith(";"):
                continue
            out.append(line)
        return "\n".join(out).lstrip("\n")
