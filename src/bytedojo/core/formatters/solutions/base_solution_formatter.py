"""
BaseSolutionFormatter - abstract base for language-specific problem formatters.

Each subclass renders a `Problem` into the placement-ready content of
the main solution file for its language and may emit sibling files
(node-class modules, header files) via `extra_files`. Lookup of the
right subclass is centralised in the `core.formatters` package
registry; callers never branch on `CodeLanguage` themselves.
"""

from abc import ABC, abstractmethod
from typing import Dict

from bytedojo.core.models.problem import Problem
from bytedojo.core.formatters.comments.base_comment_formatter import BaseCommentFormatter


class BaseSolutionFormatter(ABC):
    """Abstract base for language-specific problem formatters."""

    comment_formatter: BaseCommentFormatter

    def format(self, problem: Problem) -> str:
        """Assemble the complete solution file for `problem`.

        Section order is fixed across all languages: header, description,
        imports, solution, test. Subclasses fill in the three language-
        specific sections via the abstract methods below.
        """
        def _section(title: str) -> str:
            return self.comment_formatter.format_single_line(f"--- {title} ---")

        return "".join([
            self.format_header(problem),
            self.format_description(problem),
            "\n\n",
            self.format_imports(problem),
            "\n\n",
            _section("solution"),
            "\n\n",
            self.format_solution(problem),
            "\n\n",
            _section("main"),
            "\n\n",
            self.format_main_block(problem),
            "\n",
        ])

    @abstractmethod
    def format_imports(self, problem: Problem) -> str:
        """Return the imports / includes block for this language."""
        ...

    @abstractmethod
    def format_solution(self, problem: Problem) -> str:
        """Return the starter solution code for this language."""
        ...

    @abstractmethod
    def format_main_block(self, problem: Problem) -> str:
        """Return the runnable entry-point block for this language."""
        ...

    def extra_files(self, _problem: Problem) -> Dict[str, str]:
        """Return sibling files to place alongside the solution file.

        Default: none. Override when the language emits node-class modules
        (e.g. tree_node.py, TreeNode.java, tree_node.hpp).
        """
        return {}

    def format_header(self, problem: Problem) -> str:
        """Format problem metadata as a top-of-file comment block."""
        detail = problem.problem_detail

        def format_tags(tags):
            return ", ".join(tag.value.replace('-', ' ').title() for tag in tags)

        header = "\n".join([
            f"LeetCode Problem #{detail.id}: {detail.title}",
            f"Difficulty: {detail.difficulty}",
            f"Tags: {format_tags(detail.tags)}",
        ])
        return self.comment_formatter.format_multi_line(header) + "\n\n"

    def format_description(self, problem: Problem) -> str:
        """Format the problem description, examples, and constraints as comments."""
        detail = problem.problem_detail

        description = "\n".join([
            "--- description ---",
            "",
            detail.description,
            "",
            "\n".join([f"Example #{example.example_num}:\n{example.example_text}\n" for example in problem.examples]),
            "\n".join(problem.constraints),
        ])

        return self.comment_formatter.format_single_line(description)
