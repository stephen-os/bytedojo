from abc import ABC, abstractmethod
from bytedojo.core.leetcode.models import Problem


class BaseFormatter(ABC):
    """Base formatter for problem files."""
    
    @abstractmethod
    def format(self, problem: Problem) -> str:
        """
        Format a problem into file content.
        
        Args:
            problem: Problem object
            
        Returns:
            Complete file content as string
        """
        pass