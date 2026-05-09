from dataclasses import dataclass


@dataclass
class Parameter:
    """A parameter with name and type string."""
    name: str
    type_str: str

    def __str__(self):
        return f"{self.name}: {self.type_str}"

    def __repr__(self):
        return f"Parameter(name={self.name!r}, type_str={self.type_str!r})"
