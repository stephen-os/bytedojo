"""Tests for PickService."""

import random
from typing import List

import pytest

from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.services.pick_service import PickResult, PickScope, PickService


# --------------------------------------------------------------------------- #
# PickScope                                                                   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("scope, label", [
    (PickScope.UNSOLVED, "unsolved"),
    (PickScope.SOLVED,   "registered"),
    (PickScope.ALL,      "all"),
])
def test_scope_display_label(scope, label):
    """SOLVED renders as 'registered' to match user-facing language."""
    assert scope.display_label == label


# --------------------------------------------------------------------------- #
# PickResult                                                                  #
# --------------------------------------------------------------------------- #

def test_pick_result_has_pick_true_when_picked_set():
    pd = ProblemDetail(id=1, title="t", slug="s",
                       difficulty=ProblemDifficulty.EASY, description="")
    assert PickResult(picked=pd, candidates=[pd]).has_pick is True


def test_pick_result_has_pick_false_when_none():
    assert PickResult(picked=None).has_pick is False


def test_pick_result_pool_size_matches_candidates():
    pd = ProblemDetail(id=1, title="t", slug="s",
                       difficulty=ProblemDifficulty.EASY, description="")
    assert PickResult(candidates=[pd, pd, pd]).pool_size == 3


# --------------------------------------------------------------------------- #
# pick — scope filtering                                                      #
# --------------------------------------------------------------------------- #

def _details(*ids) -> List[ProblemDetail]:
    return [
        ProblemDetail(id=i, title=f"t{i}", slug=f"s{i}",
                      difficulty=ProblemDifficulty.EASY, description="")
        for i in ids
    ]


@pytest.fixture
def stub_query(monkeypatch):
    """Replace problem_service.query_problems so tests don't hit the index."""
    state = {"problems": []}

    def fake_query(**kwargs):
        return list(state["problems"])

    monkeypatch.setattr(
        "bytedojo.services.pick_service.problem_service.query_problems",
        fake_query,
    )
    return state


def test_pick_unsolved_excludes_registered(repo, stub_query, registered_problem):
    """Default UNSOLVED scope drops problems already in the repo's DB."""
    stub_query["problems"] = _details(1, 2, 3)
    # registered_problem has pid=1 — it should not be picked under UNSOLVED.
    random.seed(0)
    result = PickService().pick(repo)

    assert result.scope is PickScope.UNSOLVED
    assert result.total_count == 3
    assert result.registered_count == 1
    assert {p.id for p in result.candidates} == {2, 3}
    assert result.picked.id in {2, 3}


def test_pick_solved_only_picks_registered(repo, stub_query, registered_problem):
    stub_query["problems"] = _details(1, 2, 3)
    result = PickService().pick(repo, scope=PickScope.SOLVED)

    assert result.scope is PickScope.SOLVED
    assert {p.id for p in result.candidates} == {1}
    assert result.picked.id == 1


def test_pick_all_ignores_registration(repo, stub_query, registered_problem):
    stub_query["problems"] = _details(1, 2, 3)
    result = PickService().pick(repo, scope=PickScope.ALL)

    assert result.scope is PickScope.ALL
    assert {p.id for p in result.candidates} == {1, 2, 3}


# --------------------------------------------------------------------------- #
# pick — empty pool                                                           #
# --------------------------------------------------------------------------- #

def test_pick_returns_none_when_no_candidates(repo, stub_query):
    """Empty pool -> picked is None, has_pick False, no exception."""
    stub_query["problems"] = []
    result = PickService().pick(repo)
    assert result.picked is None
    assert result.has_pick is False
    assert result.pool_size == 0


def test_pick_unsolved_returns_none_when_all_registered(
    repo, stub_query, registered_problem,
):
    """Only one problem, already registered -> nothing left under UNSOLVED."""
    stub_query["problems"] = _details(1)
    result = PickService().pick(repo)
    assert result.picked is None
    assert result.candidates == []


# --------------------------------------------------------------------------- #
# pick — filter passthrough                                                   #
# --------------------------------------------------------------------------- #

def test_pick_forwards_difficulty_and_tags_to_query(repo, monkeypatch):
    captured = {}

    def spy(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        "bytedojo.services.pick_service.problem_service.query_problems", spy,
    )

    PickService().pick(
        repo,
        difficulty=ProblemDifficulty.MEDIUM,
        tags=[ProblemTag.ARRAY, ProblemTag.HASH_TABLE],
    )

    assert captured["difficulty"] is ProblemDifficulty.MEDIUM
    assert captured["tags"] == [ProblemTag.ARRAY, ProblemTag.HASH_TABLE]
