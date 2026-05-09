from enum import Enum

class ProblemDifficulty(str, Enum):
    """Problem difficulty levels."""
    NONE = "None"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

    @classmethod
    def _missing_(cls, value):
        """Return NONE for unrecognized difficulty values."""
        return cls.NONE

    @classmethod
    def from_string(cls, value: str) -> "ProblemDifficulty":
        """Parse difficulty from string."""
        if not value:
            return cls.NONE
        return cls(value.capitalize())
    
    @classmethod
    def all(cls) -> list["ProblemDifficulty"]:
        """Return all difficulties except NONE."""
        return [d for d in cls if d != cls.NONE]
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return f"ProblemDifficulty.{self.name}"