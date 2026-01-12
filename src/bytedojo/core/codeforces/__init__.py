"""
Codeforces integration for ByteDojo.

This package contains all Codeforces-specific functionality:
- Fetching problems from Codeforces API
- Formatting problems into language-specific files
"""

from bytedojo.core.codeforces.client import CodeforcesClient
from bytedojo.core.codeforces.models import Problem, ProblemSummary
from bytedojo.core.codeforces.formatters.python import PythonFormatter

__all__ = [
    'CodeforcesClient',
    'Problem',
    'ProblemSummary',
    'PythonFormatter',
]
