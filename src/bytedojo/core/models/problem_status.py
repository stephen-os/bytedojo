from enum import Enum

class ProblemStatus(str, Enum):
    """Problem completion status."""
    UNKNOWN = "unknown"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNGRADED = "ungraded"

    @classmethod
    def _missing_(cls, value):
        """Return UNKNOWN for unrecognized status values."""
        return cls.UNKNOWN

    @classmethod
    def from_string(cls, value: str) -> "ProblemStatus":
        """Parse status from string."""
        if not value:
            return cls.UNKNOWN
        return cls(value.lower())
    
    @classmethod
    def all(cls) -> list["ProblemStatus"]:
        """Return all statuses except UNKNOWN."""
        return [s for s in cls if s != cls.UNKNOWN]
    
    def __str__(self):
        return self.value.capitalize()
    
    def __repr__(self):
        return f"ProblemStatus.{self.name}"
