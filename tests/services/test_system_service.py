"""Tests for SystemService."""

import sys

from bytedojo.services.system_service import SystemReport, SystemService


# --------------------------------------------------------------------------- #
# SystemReport properties                                                     #
# --------------------------------------------------------------------------- #

def _toolchain_status(found: bool):
    """Build a minimal ToolchainStatus stand-in for the property tests."""
    from bytedojo.core.models.code_language import CodeLanguage
    from bytedojo.core.toolchains.base import ToolchainStatus
    return ToolchainStatus(language=CodeLanguage.PYTHON, found=found)


def test_report_ready_count():
    report = SystemReport(
        bytedojo_version="1.0",
        python_version="3.12.0",
        python_executable="/p",
        platform_name="x",
        platform_id="x",
        toolchains=[_toolchain_status(True), _toolchain_status(False), _toolchain_status(True)],
    )
    assert report.ready_count == 2
    assert report.total_count == 3
    assert report.all_ready is False


def test_report_all_ready_when_every_toolchain_found():
    report = SystemReport(
        bytedojo_version="1.0", python_version="3.12.0",
        python_executable="/p", platform_name="x", platform_id="x",
        toolchains=[_toolchain_status(True), _toolchain_status(True)],
    )
    assert report.all_ready is True


def test_report_all_ready_false_when_no_toolchains():
    """Empty list -> not 'all ready'; nothing to be ready about."""
    report = SystemReport(
        bytedojo_version="1.0", python_version="3.12.0",
        python_executable="/p", platform_name="x", platform_id="x",
    )
    assert report.total_count == 0
    assert report.all_ready is False


# --------------------------------------------------------------------------- #
# SystemService.check                                                         #
# --------------------------------------------------------------------------- #

def test_check_returns_python_metadata():
    report = SystemService().check()
    info = sys.version_info
    assert report.python_version == f"{info.major}.{info.minor}.{info.micro}"
    assert report.python_executable == sys.executable
    assert report.platform_id == sys.platform


def test_check_probes_all_registered_toolchains():
    """One ToolchainStatus per registered toolchain (currently 3)."""
    report = SystemService().check()
    assert report.total_count == 3


def test_check_records_repository_path_inside_repo(repo, monkeypatch):
    """When cwd is inside a .dojo repo, repository_path is populated."""
    monkeypatch.chdir(repo.root_dir)
    report = SystemService().check()
    assert report.repository_path == repo.root_dir


def test_check_records_no_repository_path_outside_repo(tmp_path, monkeypatch):
    """No .dojo above cwd -> repository_path is None."""
    monkeypatch.chdir(tmp_path)
    report = SystemService().check()
    assert report.repository_path is None
