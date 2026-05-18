"""
Formatters for LeetCode solution files.

Language-specific solution formatters plus a registry so callers
(FetchService) can look up the right formatter for a CodeLanguage
without branching on the enum themselves.

For unsupported languages (anything without a registered formatter)
format_problem() falls back to the raw starter snippet so the user
still gets a placeable file.
"""

from typing import Dict, Optional

from bytedojo.core.formatters.solutions.base_solution_formatter import BaseSolutionFormatter
from bytedojo.core.formatters.solutions.cpp_solution_formatter import CppSolutionFormatter
from bytedojo.core.formatters.solutions.java_solution_formatter import JavaSolutionFormatter
from bytedojo.core.formatters.solutions.python_solution_formatter import PythonSolutionFormatter
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem


_REGISTRY: dict[CodeLanguage, type[BaseSolutionFormatter]] = {
    CodeLanguage.PYTHON: PythonSolutionFormatter,
    CodeLanguage.JAVA:   JavaSolutionFormatter,
    CodeLanguage.CPP:    CppSolutionFormatter,
}


def get_formatter(language: CodeLanguage) -> Optional[BaseSolutionFormatter]:
    """Return a formatter instance for `language`, or None if unsupported."""
    cls = _REGISTRY.get(language)
    return cls() if cls else None


def format_problem(problem: Problem, language: CodeLanguage) -> str:
    """Render a problem to its placement-ready solution-file content for `language`."""
    formatter = get_formatter(language)
    if formatter is not None:
        return formatter.format(problem)
    return problem.get_snippet(language) or ""


def extra_files_for(problem: Problem, language: CodeLanguage) -> Dict[str, str]:
    """Sibling files to place alongside the main solution file."""
    formatter = get_formatter(language)
    if formatter is None:
        return {}
    return formatter.extra_files(problem)


__all__ = [
    'BaseSolutionFormatter',
    'PythonSolutionFormatter',
    'JavaSolutionFormatter',
    'CppSolutionFormatter',
    'get_formatter',
    'format_problem',
    'extra_files_for',
]
