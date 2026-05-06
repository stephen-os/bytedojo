"""
Centralized path constants for bytedojo package.
"""

from pathlib import Path

# Define key paths relative to this file's location
PACKAGE_ROOT = Path(__file__).parent.parent

# Define project-level paths
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

# Define data directory
DATA_DIR = PROJECT_ROOT / "data"

# Define problems directory
PROBLEMS_DIR = DATA_DIR / "problems"

# Define path to problems index file
PROBLEMS_INDEX = PROBLEMS_DIR / "index.json"

# Define tests directory
TESTS_DIR = DATA_DIR / "tests"

def get_problem_file(problem_id: int) -> Path:
    """Get path to individual problem JSON file."""
    return PROBLEMS_DIR / f"{problem_id}.json"

def get_test_file(problem_id: int) -> Path:
    """Get path to individual test JSON file."""
    return TESTS_DIR / f"{problem_id}.json"
