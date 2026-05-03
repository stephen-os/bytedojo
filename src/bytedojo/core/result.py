"""
Result type for operations that can succeed or fail with a message.
"""

from dataclasses import dataclass

@dataclass
class Result:
    """Result of an operation."""
    success: bool
    message: str
