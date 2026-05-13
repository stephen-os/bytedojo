"""Tests for the centralized path constants."""

from pathlib import Path

from bytedojo.core import paths


# --------------------------------------------------------------------------- #
# Constant shape                                                              #
# --------------------------------------------------------------------------- #

def test_package_root_points_at_bytedojo_package():
    """PACKAGE_ROOT resolves to the on-disk bytedojo package dir."""
    assert paths.PACKAGE_ROOT.name == "bytedojo"
    assert paths.PACKAGE_ROOT.is_dir()


def test_project_root_above_package_root():
    """PROJECT_ROOT is two levels above PACKAGE_ROOT (out of src/bytedojo/)."""
    assert paths.PROJECT_ROOT == paths.PACKAGE_ROOT.parent.parent


def test_data_dir_under_project_root():
    assert paths.DATA_DIR == paths.PROJECT_ROOT / "data"


def test_problems_dir_under_data_dir():
    assert paths.PROBLEMS_DIR == paths.DATA_DIR / "problems"


def test_problems_index_under_problems_dir():
    assert paths.PROBLEMS_INDEX == paths.PROBLEMS_DIR / "index.json"


def test_tests_dir_under_data_dir():
    assert paths.TESTS_DIR == paths.DATA_DIR / "tests"


# --------------------------------------------------------------------------- #
# get_problem_file / get_test_file                                            #
# --------------------------------------------------------------------------- #

def test_get_problem_file_format():
    assert paths.get_problem_file(1) == paths.PROBLEMS_DIR / "1.json"
    assert paths.get_problem_file(200) == paths.PROBLEMS_DIR / "200.json"


def test_get_test_file_format():
    assert paths.get_test_file(1) == paths.TESTS_DIR / "1.json"
    assert paths.get_test_file(200) == paths.TESTS_DIR / "200.json"


def test_get_problem_file_returns_path_object():
    """Callers use Path .exists() / .read_text() — ensure we never hand back str."""
    assert isinstance(paths.get_problem_file(1), Path)
    assert isinstance(paths.get_test_file(1), Path)
