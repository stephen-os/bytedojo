"""Tests for the interactive grade presenter (view/grade + batch browser)."""

import click
import pytest

from bytedojo.commands.ui import grade_browser
from bytedojo.core.models.problem_status import ProblemStatus

from tests.conftest import insert_registered_problem


@pytest.fixture
def scripted_prompt(monkeypatch):
    """Feed click.prompt a scripted sequence of answers."""
    answers = []

    def fake_prompt(*args, **kwargs):
        if not answers:
            raise AssertionError("prompt called more times than scripted")
        return answers.pop(0)

    monkeypatch.setattr(click, "prompt", fake_prompt)
    return answers


def _unstyled(capsys) -> str:
    return click.unstyle(capsys.readouterr().out)


# --------------------------------------------------------------------------- #
# view_and_grade_problem                                                      #
# --------------------------------------------------------------------------- #


def test_view_only_renders_status_card(repo, registered_problem, capsys):
    done = grade_browser.view_and_grade_problem(repo, registered_problem)
    assert done is True
    out = _unstyled(capsys)
    assert "Problem Status" in out
    assert "Two Sum" in out
    assert "UNGRADED" in out


def test_direct_status_applies_grade(repo, registered_problem, capsys):
    grade_browser.view_and_grade_problem(repo, registered_problem, status="passed")
    assert "MARKED AS PASSED" in _unstyled(capsys)
    with repo.session() as s:
        assert s.problems.get("leetcode", 1).status is ProblemStatus.PASSED


def test_manual_prompt_applies_choice_and_notes(
    repo, registered_problem, scripted_prompt, capsys
):
    scripted_prompt.extend(["f", "took too long"])

    done = grade_browser.view_and_grade_problem(repo, registered_problem, manual=True)

    assert done is True
    out = _unstyled(capsys)
    assert "MARKED AS FAILED" in out
    with repo.session() as s:
        fresh = s.problems.get("leetcode", 1)
    assert fresh.status is ProblemStatus.FAILED
    assert fresh.notes == "took too long"


def test_manual_prompt_quit_cancels_without_grading(
    repo, registered_problem, scripted_prompt, capsys
):
    scripted_prompt.append("q")

    done = grade_browser.view_and_grade_problem(repo, registered_problem, manual=True)

    assert done is False
    assert "Cancelled" in _unstyled(capsys)
    with repo.session() as s:
        assert s.problems.get("leetcode", 1).status is ProblemStatus.UNGRADED


def test_manual_prompt_retries_on_invalid_choice(
    repo, registered_problem, scripted_prompt
):
    scripted_prompt.extend(["banana", "s", ""])  # invalid, then skip, no notes

    grade_browser.view_and_grade_problem(repo, registered_problem, manual=True)

    with repo.session() as s:
        assert s.problems.get("leetcode", 1).status is ProblemStatus.SKIPPED


def test_invalid_grade_status_renders_service_error(repo, registered_problem, capsys):
    grade_browser.view_and_grade_problem(repo, registered_problem, status="bogus")
    assert "Invalid status" in _unstyled(capsys)


# --------------------------------------------------------------------------- #
# browse_problems                                                             #
# --------------------------------------------------------------------------- #


def test_browse_empty_list_prints_hint(repo, capsys):
    grade_browser.browse_problems(repo, [])
    out = _unstyled(capsys)
    assert "No problems found" in out
    assert "dojo fetch" in out


def _seed_many(repo, count):
    return [
        insert_registered_problem(repo, pid=i, slug=f"p{i}", title=f"Problem {i}")
        for i in range(1, count + 1)
    ]


def test_browse_paginates_forward_and_back(repo, scripted_prompt, capsys):
    problems = _seed_many(repo, 15)
    scripted_prompt.extend(["n", "p", "q"])

    grade_browser.browse_problems(repo, problems, per_page=10)

    out = _unstyled(capsys)
    assert "(page 1/2)" in out
    assert "(page 2/2)" in out
    assert "Showing 11-15 of 15" in out


def test_browse_clamps_navigation_at_edges(repo, scripted_prompt, capsys):
    problems = _seed_many(repo, 3)
    scripted_prompt.extend(["p", "n", "q"])

    grade_browser.browse_problems(repo, problems, per_page=10)

    out = _unstyled(capsys)
    assert "Already on first page." in out
    assert "Already on last page." in out


def test_browse_selection_opens_manual_grade_flow(repo, scripted_prompt, capsys):
    problems = _seed_many(repo, 2)
    # select #2, grade it passed (no notes), press Enter, quit
    scripted_prompt.extend(["2", "p", "", "", "q"])

    grade_browser.browse_problems(repo, problems, per_page=10)

    with repo.session() as s:
        assert s.problems.get("leetcode", 2).status is ProblemStatus.PASSED
    assert "MARKED AS PASSED" in _unstyled(capsys)


def test_browse_rejects_out_of_range_selection(repo, scripted_prompt, capsys):
    problems = _seed_many(repo, 2)
    scripted_prompt.extend(["9", "q"])

    grade_browser.browse_problems(repo, problems, per_page=10)

    assert "Invalid selection" in _unstyled(capsys)


def test_browse_rejects_garbage_input(repo, scripted_prompt, capsys):
    problems = _seed_many(repo, 2)
    scripted_prompt.extend(["??", "q"])

    grade_browser.browse_problems(repo, problems, per_page=10)

    assert "Invalid input" in _unstyled(capsys)
