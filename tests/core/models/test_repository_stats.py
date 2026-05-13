"""Tests for the RepositoryStats dataclass."""

from bytedojo.core.models.repository_stats import RepositoryStats


def test_construct_minimal_defaults_breakdowns_to_empty_dicts():
    s = RepositoryStats(total_problems=42)
    assert s.total_problems == 42
    assert s.by_difficulty == {}
    assert s.by_source == {}
    assert s.by_language == {}


def test_construct_with_breakdowns():
    s = RepositoryStats(
        total_problems=10,
        by_difficulty={"Easy": 6, "Medium": 3, "Hard": 1},
        by_source={"leetcode": 10},
        by_language={"python3": 7, "cpp": 3},
    )
    assert s.by_difficulty["Easy"] == 6
    assert s.by_language["python3"] == 7


def test_empty_factory_zeros_everything():
    s = RepositoryStats.empty()
    assert s.total_problems == 0
    assert s.by_difficulty == {}
    assert s.by_source == {}
    assert s.by_language == {}


def test_default_factory_dicts_are_independent_per_instance():
    a = RepositoryStats(total_problems=1)
    b = RepositoryStats(total_problems=1)
    a.by_difficulty["Easy"] = 1
    assert b.by_difficulty == {}
