"""
Formatters for solution files.

Language-specific solution formatters plus a registry so callers
(FetchService) can look up the right formatter for a CodeLanguage
without branching on the enum themselves. Stubs are synthesised from
the test bundle's signature (§11); the problem supplies the prose.
"""

from typing import Dict, Optional

from bytedojo.core.formatters.solutions.base_solution_formatter import (
    BaseSolutionFormatter,
)
from bytedojo.core.formatters.solutions.python_solution_formatter import (
    PythonSolutionFormatter,
)
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.test_bundle import TestBundle

_REGISTRY: dict[CodeLanguage, type[BaseSolutionFormatter]] = {
    CodeLanguage.PYTHON: PythonSolutionFormatter,
}


def get_formatter(language: CodeLanguage) -> Optional[BaseSolutionFormatter]:
    """Return a formatter instance for `language`, or None if unsupported."""
    cls = _REGISTRY.get(language)
    return cls() if cls else None


def format_problem(problem: Problem, bundle: TestBundle, language: CodeLanguage) -> str:
    """Render a problem to its placement-ready solution-file content."""
    formatter = get_formatter(language)
    if formatter is None:
        return ""
    return formatter.format(problem, bundle)


def extra_files_for(bundle: TestBundle, language: CodeLanguage) -> Dict[str, str]:
    """Sibling files to place alongside the main solution file."""
    formatter = get_formatter(language)
    if formatter is None:
        return {}
    return formatter.extra_files(bundle)


__all__ = [
    "BaseSolutionFormatter",
    "PythonSolutionFormatter",
    "get_formatter",
    "format_problem",
    "extra_files_for",
]
