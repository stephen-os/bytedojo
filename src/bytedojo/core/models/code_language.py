from enum import Enum


class CodeLanguage(str, Enum):
    """Programming languages supported by ByteDojo. Values match LeetCode JSON keys."""
    UNKNOWN = "unknown"
    PYTHON = "python3"
    JAVA = "java"
    CPP = "cpp"
    RUST = "rust"
    GO = "golang"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"

    @classmethod
    def _missing_(cls, value):
        """Return UNKNOWN for unrecognized language values."""
        return cls.UNKNOWN

    @classmethod
    def from_string(cls, value: str) -> "CodeLanguage":
        """Parse language from string, returns UNKNOWN if unknown."""
        if not value:
            return cls.UNKNOWN
        return cls(value.lower())

    @classmethod
    def default(cls) -> "CodeLanguage":
        """Get default language python3."""
        return cls.PYTHON

    @property
    def extension(self) -> str:
        """Get file extension for this language."""
        extensions = {
            CodeLanguage.PYTHON: ".py",
            CodeLanguage.JAVA: ".java",
            CodeLanguage.CPP: ".cpp",
            CodeLanguage.RUST: ".rs",
            CodeLanguage.GO: ".go",
            CodeLanguage.JAVASCRIPT: ".js",
            CodeLanguage.TYPESCRIPT: ".ts",
        }
        return extensions.get(self, "")

    def __str__(self):
        display_names = {
            CodeLanguage.PYTHON: "Python",
            CodeLanguage.CPP: "C++",
            CodeLanguage.GO: "Go",
            CodeLanguage.JAVASCRIPT: "JavaScript",
            CodeLanguage.TYPESCRIPT: "TypeScript",
        }
        return display_names.get(self, self.value.capitalize())

    def __repr__(self):
        return f"CodeLanguage.{self.name}"
