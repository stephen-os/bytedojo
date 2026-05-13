"""Tests for the ReviewStats dataclass."""

from bytedojo.core.models.review_stats import ReviewStats


def test_construct_with_fields():
    s = ReviewStats(due_today=2, due_this_week=5, total_in_review=12)
    assert s.due_today == 2
    assert s.due_this_week == 5
    assert s.total_in_review == 12


def test_empty_factory_zeros_all_counts():
    s = ReviewStats.empty()
    assert s.due_today == 0
    assert s.due_this_week == 0
    assert s.total_in_review == 0
