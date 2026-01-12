"""
Test data storage for bytedojo.

Stores problem metadata and test cases as JSON for the code runner.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from bytedojo.core.logger import get_logger


@dataclass
class TestData:
    """Test data for a single problem."""
    problem_id: int
    source: str
    title: str
    difficulty: str
    class_name: str
    method_name: str
    params: List[Dict[str, str]]  # [{"name": "nums", "type": "List[int]"}, ...]
    return_type: str
    helpers_needed: Dict[str, bool]  # {"listnode": False, "treenode": False}
    test_cases: str  # Raw test cases from LeetCode
    file_path: str  # Path to the solution file

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestData":
        """Create from dictionary."""
        return cls(**data)


class TestStore:
    """Manages test data storage in .dojo/tests directory."""

    def __init__(self, dojo_path: Path):
        """
        Initialize test store.

        Args:
            dojo_path: Path to .dojo directory
        """
        self.dojo_path = dojo_path
        self.tests_dir = dojo_path / "tests"
        self.logger = get_logger()

    def _get_test_file_path(self, source: str, problem_id: int) -> Path:
        """Get path to test JSON file for a problem."""
        return self.tests_dir / source / f"{problem_id}.json"

    def save(self, test_data: TestData) -> Path:
        """
        Save test data to JSON file.

        Args:
            test_data: TestData object to save

        Returns:
            Path to saved JSON file
        """
        file_path = self._get_test_file_path(test_data.source, test_data.problem_id)

        # Create directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(test_data.to_dict(), f, indent=2)

        self.logger.debug(f"Saved test data for problem #{test_data.problem_id} to {file_path}")
        return file_path

    def load(self, source: str, problem_id: int) -> Optional[TestData]:
        """
        Load test data from JSON file.

        Args:
            source: Problem source (e.g., 'leetcode')
            problem_id: Problem ID

        Returns:
            TestData object or None if not found
        """
        file_path = self._get_test_file_path(source, problem_id)

        if not file_path.exists():
            self.logger.debug(f"Test data not found for problem #{problem_id}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TestData.from_dict(data)
        except Exception as e:
            self.logger.error(f"Error loading test data for problem #{problem_id}: {e}")
            return None

    def exists(self, source: str, problem_id: int) -> bool:
        """Check if test data exists for a problem."""
        return self._get_test_file_path(source, problem_id).exists()

    def list_tests(self, source: Optional[str] = None) -> List[TestData]:
        """
        List all stored test data.

        Args:
            source: Filter by source (optional)

        Returns:
            List of TestData objects
        """
        tests = []

        # Return empty list if tests directory doesn't exist
        if not self.tests_dir.exists():
            return tests

        if source:
            source_dir = self.tests_dir / source
            if source_dir.exists():
                for file_path in source_dir.glob("*.json"):
                    test_data = self._load_file(file_path)
                    if test_data:
                        tests.append(test_data)
        else:
            for source_dir in self.tests_dir.iterdir():
                if source_dir.is_dir():
                    for file_path in source_dir.glob("*.json"):
                        test_data = self._load_file(file_path)
                        if test_data:
                            tests.append(test_data)

        return sorted(tests, key=lambda t: t.problem_id)

    def _load_file(self, file_path: Path) -> Optional[TestData]:
        """Load TestData from a file path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TestData.from_dict(data)
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return None

    def get_last(self, source: Optional[str] = None) -> Optional[TestData]:
        """
        Get the most recently added test data.

        Args:
            source: Filter by source (optional)

        Returns:
            Most recent TestData or None
        """
        # Return None if tests directory doesn't exist
        if not self.tests_dir.exists():
            return None

        if source:
            source_dir = self.tests_dir / source
            if not source_dir.exists():
                return None
            files = list(source_dir.glob("*.json"))
        else:
            files = list(self.tests_dir.rglob("*.json"))

        if not files:
            return None

        # Sort by modification time (most recent first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        return self._load_file(files[0])

    def delete(self, source: str, problem_id: int) -> bool:
        """
        Delete test data for a problem.

        Args:
            source: Problem source
            problem_id: Problem ID

        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_test_file_path(source, problem_id)

        if file_path.exists():
            file_path.unlink()
            self.logger.debug(f"Deleted test data for problem #{problem_id}")
            return True

        return False
