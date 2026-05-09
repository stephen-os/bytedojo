from dataclasses import dataclass

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_parameters import CodeParameters
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.entry_point import EntryPoint


@dataclass
class ProblemCode:
    """Per-language code package: starter snippet, parameters, entry point, and test snippet."""
    lang: CodeLanguage
    problem_code: CodeSnippet
    problem_parameters: CodeParameters
    entry_point: EntryPoint
    test_code: CodeSnippet

    def __post_init__(self):
        if isinstance(self.lang, str):
            self.lang = CodeLanguage.from_string(self.lang)

    def __str__(self):
        return f"ProblemCode({self.lang})"

    def __repr__(self):
        return (f"ProblemCode(lang={self.lang!r}, problem_code={self.problem_code!r}, "
                f"problem_parameters={self.problem_parameters!r}, entry_point={self.entry_point!r}, "
                f"test_code={self.test_code!r})")
