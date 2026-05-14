"""Tests for `dojo support`."""

from pathlib import Path

from click.testing import CliRunner

from bytedojo.commands.subcommands.support import support
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains.base import ToolchainStatus
from bytedojo.services.system_service import SystemReport


def _report(*, all_ready: bool = True, with_repo: bool = False) -> SystemReport:
    statuses = [
        ToolchainStatus(
            language=CodeLanguage.PYTHON,
            found=True, version="3.12.0",
            paths={"python": "/usr/bin/python3"},
        ),
        ToolchainStatus(
            language=CodeLanguage.JAVA,
            found=all_ready, version="OpenJDK 21" if all_ready else None,
            paths={"javac": "/usr/bin/javac", "java": "/usr/bin/java"} if all_ready else {},
            missing=[] if all_ready else ["javac", "java"],
            install_hint=None if all_ready else "apt install default-jdk",
        ),
    ]
    return SystemReport(
        bytedojo_version="0.1.0",
        python_version="3.12.0",
        python_executable="/usr/bin/python3",
        platform_name="Linux 6.6",
        platform_id="linux",
        repository_path=Path("/home/x/repo") if with_repo else None,
        toolchains=statuses,
    )


def test_support_invokes_system_service(monkeypatch):
    """The command runs SystemService().check() exactly once."""
    calls = {"n": 0}

    def fake_check(self):
        calls["n"] += 1
        return _report()

    monkeypatch.setattr(
        "bytedojo.services.system_service.SystemService.check", fake_check,
    )
    result = CliRunner().invoke(support, [])
    assert result.exit_code == 0
    assert calls["n"] == 1


def test_support_renders_environment_block(monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.system_service.SystemService.check",
        lambda self: _report(with_repo=True),
    )
    result = CliRunner().invoke(support, [])
    assert result.exit_code == 0
    assert "BYTEDOJO SUPPORT" in result.output
    assert "Environment" in result.output
    assert "0.1.0" in result.output       # bytedojo version
    assert "3.12.0" in result.output      # python version
    assert "Linux 6.6" in result.output   # platform name
    # Path renders differently on Windows vs POSIX — check the tail segment.
    assert "repo" in result.output


def test_support_says_not_in_repo_when_repo_path_missing(monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.system_service.SystemService.check",
        lambda self: _report(with_repo=False),
    )
    result = CliRunner().invoke(support, [])
    assert "not in a .dojo repository" in result.output


def test_support_marks_ready_toolchains_ok(monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.system_service.SystemService.check",
        lambda self: _report(all_ready=True),
    )
    result = CliRunner().invoke(support, [])
    assert "[OK]" in result.output
    assert "python3" in result.output


def test_support_marks_missing_toolchains_no_and_shows_install_hint(monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.system_service.SystemService.check",
        lambda self: _report(all_ready=False),
    )
    result = CliRunner().invoke(support, [])
    assert "[NO]" in result.output
    assert "javac" in result.output
    assert "apt install default-jdk" in result.output


def test_support_summary_line_all_ready_vs_partial(monkeypatch):
    monkeypatch.setattr(
        "bytedojo.services.system_service.SystemService.check",
        lambda self: _report(all_ready=True),
    )
    ready = CliRunner().invoke(support, [])
    assert "All 2 toolchains ready" in ready.output

    monkeypatch.setattr(
        "bytedojo.services.system_service.SystemService.check",
        lambda self: _report(all_ready=False),
    )
    partial = CliRunner().invoke(support, [])
    assert "1 of 2 toolchains ready" in partial.output
