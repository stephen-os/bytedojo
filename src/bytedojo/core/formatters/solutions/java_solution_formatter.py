"""
Java formatter for LeetCode solution files.
"""

from typing import Dict

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.formatters.comments.java_comment_formatter import JavaCommentFormatter
from bytedojo.core.formatters.helpers.java_helper_formatter import JavaHelperFormatter
from bytedojo.core.formatters.solutions.base_solution_formatter import BaseSolutionFormatter
from bytedojo.core.logger import get_logger


_JAVA_BASELINE_IMPORTS: tuple = (
    "import java.util.*;",
)


class JavaSolutionFormatter(BaseSolutionFormatter):
    """Formats LeetCode problems as Java solution files."""

    def __init__(self):
        self.logger = get_logger()
        self.comment_formatter = JavaCommentFormatter()
        self._helper = JavaHelperFormatter()

    def extra_files(self, problem: Problem) -> Dict[str, str]:
        return self._helper.files_for(problem)

    def format_imports(self, _problem: Problem) -> str:
        """Baseline `java.util.*` import block."""
        return "\n".join(_JAVA_BASELINE_IMPORTS)

    def format_solution(self, problem: Problem) -> str:
        """Extract the solution class from the LeetCode snippet."""
        return self._get_java_code(problem)

    def format_main_block(self, _problem: Problem) -> str:
        """Return a minimal `class Main` entry point."""
        return (
            "class Main {\n"
            "    public static void main(String[] args) {\n"
            "    }\n"
            "}\n"
        )

    # ========================================================================
    # Code Extraction and Processing
    # ========================================================================

    def _get_java_code(self, problem: Problem) -> str:
        """Return the raw Java snippet."""
        code = problem.get_snippet(CodeLanguage.JAVA)
        if not code:
            self.logger.warning(
                f"No Java snippet for problem #{problem.problem_detail.id}"
            )
            return "// No Java template available"
        return code
