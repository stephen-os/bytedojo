"""
Test fetcher - loads test case data from individual JSON files.

This module provides functions to fetch test cases from local JSON files.
"""

import json
from typing import Optional, List

from bytedojo.core.models import Case
from bytedojo.core.paths import get_test_file


def _load_test_file(problem_id: int) -> Optional[dict]:
    """Load a single test file by ID."""
    path = get_test_file(problem_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_test_cases(problem_id: int) -> List[Case]:
    """
    Fetch test cases for a problem.

    Args:
        problem_id: The problem number

    Returns:
        List of Case objects
    """
    data = _load_test_file(problem_id)
    if not data:
        return []

    input_output = data.get("input_output", [])
    return [
        Case(input=tc.get("input", ""), output=tc.get("output", ""))
        for tc in input_output
    ]


def is_testable(problem_id: int) -> bool:
    """
    Check if a problem has test cases available.

    Args:
        problem_id: The problem number

    Returns:
        True if test cases exist
    """
    return len(fetch_test_cases(problem_id)) > 0
