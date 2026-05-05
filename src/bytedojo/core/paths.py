"""
Centralized path constants for bytedojo package.

All package-level paths should be defined here to avoid
scattered Path(__file__).parent chains throughout the codebase.
"""

from pathlib import Path

# Package root (src/bytedojo)
PACKAGE_ROOT = Path(__file__).parent.parent

# Project root (contains src/, data/, tests/)
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
TEST_CASES_DIR = DATA_DIR / "test_cases"

# Data files
PROBLEMS_FILE = TEST_CASES_DIR / "problems.json"
TESTS_FILE = TEST_CASES_DIR / "tests.json"
UNSUPPORTED_FILE = TEST_CASES_DIR / "unsupported_tests.json"
