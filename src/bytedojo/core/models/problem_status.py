"""
ProblemStatus - completion / test outcome status for an attempt.

Used both as the user-facing grade (PASSED/FAILED/SKIPPED) and as the
per-version `dojo test` outcome on Attempt. UNGRADED marks an attempt
that has not been run yet; UNKNOWN is the unrecognized-input fallback.
"""

from enum import Enum


class ProblemStatus(str, Enum):
    """Completion / test outcome status. UNKNOWN is the unrecognized fallback."""
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
