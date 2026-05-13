"""
Formatters for LeetCode problems.

Base formatter and language-specific implementations, plus a small
registry so callers (FetchService) can look up the right formatter for
a CodeLanguage without branching on the enum themselves.

For unsupported languages (anything without a registered formatter)
format_problem() falls back to the raw starter snippet so the user
still gets a placeable file — just without the description header /
imports / runnable main() the formatted version provides.
"""

from typing import Dict, Optional

from bytedojo.core.formatters.base import BaseFormatter
from bytedojo.core.formatters.cpp import CppFormatter
from bytedojo.core.formatters.java import JavaFormatter
from bytedojo.core.formatters.python import PythonFormatter
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem


_REGISTRY: dict[CodeLanguage, type[BaseFormatter]] = {
    CodeLanguage.PYTHON: PythonFormatter,
    CodeLanguage.JAVA:   JavaFormatter,
    CodeLanguage.CPP:    CppFormatter,
}


def get_formatter(language: CodeLanguage) -> Optional[BaseFormatter]:
    """Return a formatter instance for `language`, or None if unsupported."""
    cls = _REGISTRY.get(language)
    return cls() if cls else None


def format_problem(problem: Problem, language: CodeLanguage) -> str:
    """
    Render a problem to its placement-ready solution-file content for `language`.

    Uses the registered formatter when one exists; otherwise falls back
    to the raw starter snippet from the problem JSON (so Rust / Go / JS
    placements still produce a usable file).
    """
    formatter = get_formatter(language)
    if formatter is not None:
        return formatter.format(problem)
    return problem.get_snippet(language) or ""


def extra_files_for(problem: Problem, language: CodeLanguage) -> Dict[str, str]:
    """
    Sibling files to place alongside the main solution file.

    Returns `{filename: content}` — currently used to emit per-language
    node-class files (e.g. `tree_node.py` / `TreeNode.java` /
    `tree_node.hpp`) that the user's solution imports/includes. Empty
    when the problem doesn't need them or the language has no formatter.
    """
    formatter = get_formatter(language)
    if formatter is None:
        return {}
    return formatter.extra_files(problem)


__all__ = [
    'BaseFormatter',
    'PythonFormatter',
    'JavaFormatter',
    'CppFormatter',
    'get_formatter',
    'format_problem',
    'extra_files_for',
]
