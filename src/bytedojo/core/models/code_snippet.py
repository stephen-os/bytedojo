from dataclasses import dataclass

from bytedojo.core.models.code_language import CodeLanguage


@dataclass
class CodeSnippet:
    """Code snippet in a specific language."""
    lang: CodeLanguage
    code: str

    def __post_init__(self):
        if isinstance(self.lang, str):
            self.lang = CodeLanguage.from_string(self.lang)

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"CodeSnippet(lang={self.lang!r}, code={self.code!r})"
