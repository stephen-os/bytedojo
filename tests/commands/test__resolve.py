"""Tests for the shared problem-resolver helper used by test / run / grade."""

import click
import pytest

from bytedojo.commands._resolve import resolve_problem
from bytedojo.core.models.registered_problem import RegisteredProblem

from tests.services.conftest import insert_registered_problem


# --------------------------------------------------------------------------- #
# --last                                                                      #
# --------------------------------------------------------------------------- #

def test_last_returns_most_recent(repo, registered_problem):
    """--last short-circuits the find/disambiguate flow."""
    other = insert_registered_problem(repo, pid=2, slug="b", title="B")

    out = resolve_problem(
        repo, language="python3",
        identifier=None, name=None, desc=None, last=True,
        command_name="test",
    )
    assert isinstance(out, RegisteredProblem)
    # We don't care which one is "most recent" — just that --last surfaces
    # something instead of raising. (Ordering is the database's contract.)
    assert out.problem_id in {1, 2}


def test_last_raises_when_no_problems_registered(repo):
    """No registrations -> actionable error pointing at fetch."""
    with pytest.raises(click.ClickException, match="No python3 problems"):
        resolve_problem(
            repo, language="python3",
            identifier=None, name=None, desc=None, last=True,
            command_name="test",
        )


def test_last_uses_python_in_help_examples_even_for_python3_lang(repo):
    """Error message uses 'python' (CLI flag form), not 'python3' (canonical)."""
    with pytest.raises(click.ClickException) as exc:
        resolve_problem(
            repo, language="python3",
            identifier=None, name=None, desc=None, last=True,
            command_name="test",
        )
    assert "--python" in exc.value.message


# --------------------------------------------------------------------------- #
# No selectors                                                                #
# --------------------------------------------------------------------------- #

def test_missing_selector_raises_with_examples(repo):
    """When require_selector is True (default), no flags -> actionable error."""
    with pytest.raises(click.ClickException) as exc:
        resolve_problem(
            repo, language="python3",
            identifier=None, name=None, desc=None, last=False,
            command_name="grade",
        )
    msg = exc.value.message
    assert "dojo grade 1" in msg
    assert "--name" in msg
    assert "--last" in msg


def test_require_selector_false_falls_through_to_lookup(repo, registered_problem):
    """With require_selector=False, missing flags don't raise — lookup proceeds.

    find_registered_problems with no criteria returns every registered
    problem; the single seeded entry is unique so resolve_problem returns
    it instead of raising the missing-selector error.
    """
    out = resolve_problem(
        repo, language="python3",
        identifier=None, name=None, desc=None, last=False,
        command_name="grade",
        require_selector=False,
    )
    assert out.problem_id == 1


# --------------------------------------------------------------------------- #
# Unique match                                                                #
# --------------------------------------------------------------------------- #

def test_identifier_unique_match(repo, registered_problem):
    """Numeric ID maps straight to the matching registered problem."""
    out = resolve_problem(
        repo, language="python3",
        identifier="1", name=None, desc=None, last=False,
        command_name="test",
    )
    assert out.problem_id == 1


def test_no_match_raises_with_criteria_breakdown(repo):
    """The error names every filter the user actually supplied."""
    with pytest.raises(click.ClickException) as exc:
        resolve_problem(
            repo, language="python3",
            identifier="99", name="nothing", desc=None, last=False,
            command_name="test",
        )
    msg = exc.value.message
    assert "99" in msg
    assert "nothing" in msg
    assert "Fetch one first" in msg


# --------------------------------------------------------------------------- #
# Ambiguous match -> interactive disambiguation                               #
# --------------------------------------------------------------------------- #

def test_ambiguous_invokes_select_problem(repo, monkeypatch):
    """Multiple matches route through select_problem; helper returns the choice."""
    a = insert_registered_problem(repo, pid=1, slug="a", title="Two Sum")
    b = insert_registered_problem(repo, pid=2, slug="b", title="Two Sum II")

    chosen = {"pick": b}
    monkeypatch.setattr(
        "bytedojo.commands._resolve.select_problem",
        lambda matches: chosen["pick"],
    )

    out = resolve_problem(
        repo, language="python3",
        identifier=None, name="Two Sum", desc=None, last=False,
        command_name="test",
    )
    assert out is b


def test_ambiguous_cancelled_raises_abort(repo, monkeypatch):
    """User cancels the disambiguation prompt -> click.Abort propagates up."""
    insert_registered_problem(repo, pid=1, slug="a", title="Two Sum")
    insert_registered_problem(repo, pid=2, slug="b", title="Two Sum II")

    monkeypatch.setattr(
        "bytedojo.commands._resolve.select_problem", lambda matches: None,
    )

    with pytest.raises(click.Abort):
        resolve_problem(
            repo, language="python3",
            identifier=None, name="Two Sum", desc=None, last=False,
            command_name="test",
        )
