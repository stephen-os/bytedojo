"""
CodeSnippet - a starter-code snippet for a problem in a specific language.

LeetCode provides a `codeSnippets` array with one entry per supported
language. We coerce the language string into a `CodeLanguage` in
`__post_init__` so callers receive a typed value regardless of whether
the snippet was constructed from raw JSON or in-process.
"""

from dataclasses import dataclass

from bytedojo.core.models.code_language import CodeLanguage


@dataclass
class CodeSnippet:
    """Starter code for a problem in a specific language."""
    lang: CodeLanguage
    code: str

    def __post_init__(self):
        if isinstance(self.lang, str):
            self.lang = CodeLanguage.from_string(self.lang)

    def __str__(self):
        return self.code
