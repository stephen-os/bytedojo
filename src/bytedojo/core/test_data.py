"""
Internal test data loader for bytedojo.

Loads test data from the package's bundled test files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class TestCase:
    """A single test case with input and expected output."""
    input: List[Any]
    expected: Any


@dataclass
class ProblemTestData:
    """Test data for a specific problem."""
    problem_id: int
    title: str
    difficulty: str
    tests: List[TestCase]


class TestDataLoader:
    """Loads test data from internal package data."""

    def __init__(self):
        """Initialize the test data loader."""
        # Get the path to the data directory within the package
        self.data_dir = Path(__file__).parent.parent / "data" / "tests"

    def get_test_data(self, source: str, problem_id: int) -> Optional[ProblemTestData]:
        """
        Load test data for a specific problem.

        Args:
            source: The problem source (e.g., 'leetcode')
            problem_id: The problem ID

        Returns:
            ProblemTestData if found, None otherwise
        """
        test_file = self.data_dir / source / f"{problem_id}.json"

        if not test_file.exists():
            return None

        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            tests = []
            for test in data.get('tests', []):
                tests.append(TestCase(
                    input=test.get('input', []),
                    expected=test.get('expected')
                ))

            return ProblemTestData(
                problem_id=data.get('problem_id', problem_id),
                title=data.get('title', ''),
                difficulty=data.get('difficulty', ''),
                tests=tests
            )

        except (json.JSONDecodeError, KeyError) as e:
            return None

    def list_available_tests(self, source: str) -> List[int]:
        """
        List all available test IDs for a source.

        Args:
            source: The problem source (e.g., 'leetcode')

        Returns:
            List of problem IDs that have test data
        """
        source_dir = self.data_dir / source

        if not source_dir.exists():
            return []

        problem_ids = []
        for file in source_dir.glob("*.json"):
            try:
                problem_id = int(file.stem)
                problem_ids.append(problem_id)
            except ValueError:
                continue

        return sorted(problem_ids)

    def has_test_data(self, source: str, problem_id: int) -> bool:
        """
        Check if test data exists for a problem.

        Args:
            source: The problem source
            problem_id: The problem ID

        Returns:
            True if test data exists
        """
        test_file = self.data_dir / source / f"{problem_id}.json"
        return test_file.exists()
