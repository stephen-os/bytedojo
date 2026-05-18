"""
Base comment formatter for formatting comments in different languages.
"""

from abc import ABC, abstractmethod

class BaseCommentFormatter(ABC):
    @abstractmethod
    def format_single_line(self, text: str) -> str:
        """
        Format a single-line comment.
        """
        pass

    @abstractmethod
    def format_multi_line(self, text: str) -> str:
        """
        Format a multi-line comment.
        """
        pass
    