"""
Tests for paths module.
"""

from pathlib import Path

from bytedojo.core.paths import (
    PACKAGE_ROOT,
    PROJECT_ROOT,
    DATA_DIR,
    PROBLEMS_DIR,
    TESTS_DIR,
    PROBLEMS_INDEX,
    get_problem_file,
    get_test_file,
)


class TestPaths:
    """Test path constants."""

    def test_paths_are_path_objects(self):
        """All exports should be Path objects."""
        assert isinstance(PACKAGE_ROOT, Path)
        assert isinstance(PROJECT_ROOT, Path)
        assert isinstance(DATA_DIR, Path)
        assert isinstance(PROBLEMS_DIR, Path)
        assert isinstance(TESTS_DIR, Path)
        assert isinstance(PROBLEMS_INDEX, Path)

    def test_package_root_contains_core(self):
        """Package root should contain the core directory."""
        assert (PACKAGE_ROOT / "core").exists()

    def test_project_root_contains_src(self):
        """Project root should contain src directory."""
        assert (PROJECT_ROOT / "src").exists()

    def test_individual_data_dirs_exist(self):
        """Individual data directories should exist."""
        assert PROBLEMS_DIR.exists()
        assert TESTS_DIR.exists()

    def test_problems_index_exists(self):
        """Problems index should exist."""
        assert PROBLEMS_INDEX.exists()
        assert PROBLEMS_INDEX.suffix == ".json"

    def test_get_problem_file(self):
        """get_problem_file should return correct path."""
        path = get_problem_file(1)
        assert path.suffix == ".json"
        assert path.name == "1.json"
        assert path.parent == PROBLEMS_DIR

    def test_get_test_file(self):
        """get_test_file should return correct path."""
        path = get_test_file(1)
        assert path.suffix == ".json"
        assert path.name == "1.json"
        assert path.parent == TESTS_DIR
