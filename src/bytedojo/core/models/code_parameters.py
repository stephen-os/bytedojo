from dataclasses import dataclass, field
from typing import List

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.parameter import Parameter


@dataclass
class CodeParameters:
    """Structured parameters for code generation in a specific language."""
    lang: CodeLanguage
    input_params: List[Parameter] = field(default_factory=list)
    output_type: str = ""

    def __post_init__(self):
        if isinstance(self.lang, str):
            self.lang = CodeLanguage.from_string(self.lang)

    def __str__(self):
        params = ", ".join(str(p) for p in self.input_params)
        return f"{self.lang}: ({params}) -> {self.output_type}"

    def __repr__(self):
        return (f"CodeParameters(lang={self.lang!r}, input_params={self.input_params!r}, "
                f"output_type={self.output_type!r})")
