from dataclasses import dataclass

from bytedojo.core.models.code_language import CodeLanguage


@dataclass
class EntryPoint:
    """Entry point expression for invoking solution in a language."""
    lang: CodeLanguage
    expression: str

    def __post_init__(self):
        if isinstance(self.lang, str):
            self.lang = CodeLanguage.from_string(self.lang)

    def __str__(self):
        return f"{self.lang}: {self.expression}"

    def __repr__(self):
        return f"EntryPoint(lang={self.lang!r}, expression={self.expression!r})"
