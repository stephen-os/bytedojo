"""
Tests for paths module.
"""

from pathlib import Path

from bytedojo.core.paths import (
    PACKAGE_ROOT,
    PROJECT_ROOT,
    DATA_DIR,
    TEST_CASES_DIR,
    PROBLEMS_FILE,
    TESTS_FILE,
    UNSUPPORTED_FILE,
)


class TestPaths:
    """Test path constants."""

    def test_paths_are_path_objects(self):
        """All exports should be Path objects."""
        assert isinstance(PACKAGE_ROOT, Path)
        assert isinstance(PROJECT_ROOT, Path)
        assert isinstance(DATA_DIR, Path)
        assert isinstance(TEST_CASES_DIR, Path)
        assert isinstance(PROBLEMS_FILE, Path)
        assert isinstance(TESTS_FILE, Path)
        assert isinstance(UNSUPPORTED_FILE, Path)

    def test_package_root_contains_core(self):
        """Package root should contain the core directory."""
        assert (PACKAGE_ROOT / "core").exists()

    def test_project_root_contains_src(self):
        """Project root should contain src directory."""
        assert (PROJECT_ROOT / "src").exists()

    def test_data_files_exist(self):
        """Data files should exist."""
        assert PROBLEMS_FILE.exists()
        assert TESTS_FILE.exists()

    def test_file_extensions(self):
        """Data files should be JSON."""
        assert PROBLEMS_FILE.suffix == ".json"
        assert TESTS_FILE.suffix == ".json"
        assert UNSUPPORTED_FILE.suffix == ".json"
