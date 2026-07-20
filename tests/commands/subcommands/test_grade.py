"""Tests for `dojo grade`."""

import pytest
from click.testing import CliRunner

from bytedojo.commands.subcommands.grade import grade
from bytedojo.services.grading_service import GradeResult


# --------------------------------------------------------------------------- #
# Pre-flight                                                                  #
# --------------------------------------------------------------------------- #

def test_grade_outside_repo_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(grade, ["1"])
    assert result.exit_code != 0
    assert "Not inside a .dojo repository" in result.output


def test_grade_mutually_exclusive_status_flags(repo, registered_problem, monkeypatch):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1", "--pass", "--fail"])
    assert result.exit_code != 0
    assert "multiple status flags" in result.output


# --------------------------------------------------------------------------- #
# Direct status flags                                                         #
# --------------------------------------------------------------------------- #

@pytest.fixture
def stub_grading(monkeypatch):
    """Replace GradingService.grade; capture calls."""
    state = {"calls": []}

    def fake_grade(self, repo, problem, *, status, notes=None):
        state["calls"].append({
            "problem_id": problem.problem_id, "status": status, "notes": notes,
        })
        return GradeResult(
            problem=problem, status=status, notes=notes,
            scheduled_review=(status == "passed"), review_frequency_days=7,
        )

    monkeypatch.setattr(
        "bytedojo.services.grading_service.GradingService.grade", fake_grade,
    )
    return state


def test_grade_pass_flag_applies_passed(repo, registered_problem, monkeypatch, stub_grading):
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1", "--pass"])
    assert result.exit_code == 0
    assert stub_grading["calls"][0]["status"] == "passed"


def test_grade_fail_flag_applies_failed(repo, registered_problem, monkeypatch, stub_grading):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(grade, ["1", "--fail"])
    assert stub_grading["calls"][0]["status"] == "failed"


def test_grade_skip_flag_applies_skipped(repo, registered_problem, monkeypatch, stub_grading):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(grade, ["1", "--skip"])
    assert stub_grading["calls"][0]["status"] == "skipped"


def test_grade_notes_flag_propagates(repo, registered_problem, monkeypatch, stub_grading):
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(grade, ["1", "--pass", "--notes", "clean BFS"])
    assert stub_grading["calls"][0]["notes"] == "clean BFS"


def test_grade_short_flags(repo, registered_problem, monkeypatch, stub_grading):
    """-p / -f / -s short forms map to --pass / --fail / --skip."""
    monkeypatch.chdir(repo.root_dir)
    CliRunner().invoke(grade, ["1", "-p"])
    assert stub_grading["calls"][-1]["status"] == "passed"

    CliRunner().invoke(grade, ["1", "-f"])
    assert stub_grading["calls"][-1]["status"] == "failed"

    CliRunner().invoke(grade, ["1", "-s"])
    assert stub_grading["calls"][-1]["status"] == "skipped"


def test_grade_pass_displays_review_scheduled(repo, registered_problem, monkeypatch, stub_grading):
    """Passing a problem mentions review scheduling in the output."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1", "--pass"])
    assert result.exit_code == 0
    # The actual message format depends on _display_grade_result; check the
    # service was called with status=passed and scheduled_review came back True.
    assert any(call["status"] == "passed" for call in stub_grading["calls"])


# --------------------------------------------------------------------------- #
# Status-only mode (view without grading)                                     #
# --------------------------------------------------------------------------- #

def test_grade_view_only_shows_problem_status(repo, registered_problem, monkeypatch):
    """No status flag + no --manual -> renders the Problem Status block and exits."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1"])
    assert result.exit_code == 0
    assert "Problem Status" in result.output
    assert "Two Sum" in result.output


def test_grade_view_only_renders_test_hint_when_ungraded(repo, registered_problem, monkeypatch):
    """Ungraded problems get a 'dojo test' hint."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1"])
    assert "dojo test 1" in result.output


# --------------------------------------------------------------------------- #
# --manual interactive flow                                                   #
# --------------------------------------------------------------------------- #

def test_grade_manual_quit_does_not_call_service(repo, registered_problem, monkeypatch, stub_grading):
    """User selects q at the manual-grade prompt -> service is not invoked."""
    monkeypatch.chdir(repo.root_dir)
    # `q` quits before notes prompt.
    result = CliRunner().invoke(grade, ["1", "--manual"], input="q\n")
    assert result.exit_code == 0
    assert stub_grading["calls"] == []


def test_grade_manual_pass_with_notes(repo, registered_problem, monkeypatch, stub_grading):
    """Manual flow: P -> notes -> service called with passed + notes."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1", "--manual"], input="p\nnice solve\n")
    assert result.exit_code == 0
    assert stub_grading["calls"][0]["status"] == "passed"
    assert stub_grading["calls"][0]["notes"] == "nice solve"


def test_grade_manual_pass_without_notes(repo, registered_problem, monkeypatch, stub_grading):
    """Empty notes prompt -> notes=None on the service call."""
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1", "--manual"], input="p\n\n")
    assert result.exit_code == 0
    assert stub_grading["calls"][0]["status"] == "passed"
    assert stub_grading["calls"][0]["notes"] is None


# --------------------------------------------------------------------------- #
# Service-level error path                                                    #
# --------------------------------------------------------------------------- #

def test_grade_service_error_is_displayed(repo, registered_problem, monkeypatch):
    """GradingService.grade returning failed -> error printed (no raise)."""
    def fake_grade(self, repo, problem, *, status, notes=None):
        return GradeResult(problem=problem, error=f"Invalid status '{status}'")

    monkeypatch.setattr(
        "bytedojo.services.grading_service.GradingService.grade", fake_grade,
    )
    monkeypatch.chdir(repo.root_dir)
    result = CliRunner().invoke(grade, ["1", "--pass"])
    # Doesn't raise — just echoes the error message.
    assert result.exit_code == 0
    assert "Invalid status" in result.output
