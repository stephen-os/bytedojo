
from dataclasses import dataclass

@dataclass
class TestCase:
    """A test case with input and expected output as strings."""
    __test__ = False
    input: str
    output: str