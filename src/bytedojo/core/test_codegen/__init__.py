"""
Test runner code generation.

Per-language code generators that take a Problem (with canonical types
and test cases) and produce a complete, compilable test runner file. Used
by FetchService to write the runner alongside the user's solution and by
TestService to execute it.

Public surface:

    from bytedojo.core.test_codegen import generate_runner, supports_codegen

    src = generate_runner(problem, CodeLanguage.JAVA)
    # → str of Main.java content with all test cases baked in
"""

from typing import Optional

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.test_codegen import cpp as _cpp
from bytedojo.core.test_codegen import java as _java


# Languages we can codegen test runners for. Python remains on the dynamic
# harness (core/harness.py) until we unify everything.
_SUPPORTED = {
    CodeLanguage.JAVA: _java.generate_runner,
    CodeLanguage.CPP:  _cpp.generate_runner,
}

_SUPPORTED_FROM_SOURCE = {
    CodeLanguage.JAVA: _java.generate_runner_for_source,
    CodeLanguage.CPP:  _cpp.generate_runner_for_source,
}


def supports_codegen(language: CodeLanguage) -> bool:
    """Whether this language has a registered test-runner generator."""
    return language in _SUPPORTED


def generate_runner(problem: Problem, language: CodeLanguage) -> Optional[str]:
    """
    Generate a test runner using the problem's starter snippet as the embedded
    Solution class. Useful for fetch-time pre-generation.

    Returns None for languages without a registered generator.
    """
    fn = _SUPPORTED.get(language)
    return fn(problem) if fn else None


def generate_runner_for_source(
    problem: Problem,
    language: CodeLanguage,
    method_name: str,
    user_source: str,
) -> Optional[str]:
    """
    Generate a test runner that embeds the user's *actual* source file
    (rather than the problem's starter snippet). Used by TestService at
    test time so the runner picks up whatever the user has edited.
    """
    fn = _SUPPORTED_FROM_SOURCE.get(language)
    return fn(problem, method_name, user_source) if fn else None


__all__ = [
    "generate_runner",
    "generate_runner_for_source",
    "supports_codegen",
]
