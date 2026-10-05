"""Tests for AttemptsRepository — flat versioning semantics (§7.1)."""

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.repositories import AttemptsRepository


def _repo(conn) -> AttemptsRepository:
    return AttemptsRepository(conn)


def test_create_starts_at_v1(conn):
    attempt = _repo(conn).create("leetcode", 1, "python3")
    assert attempt.version == 1
    assert attempt.status is ProblemStatus.UNGRADED
    assert attempt.language is CodeLanguage.PYTHON


def test_version_is_flat_across_languages(conn):
    """A later attempt in another language continues the same counter."""
    repo = _repo(conn)
    assert repo.create("leetcode", 1, "python3").version == 1
    assert repo.create("leetcode", 1, "python3").version == 2
    assert repo.create("leetcode", 1, "java").version == 3


def test_version_counter_is_per_problem(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    assert repo.create("leetcode", 2, "python3").version == 1


def test_get_latest_returns_highest_version(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    repo.create("leetcode", 1, "java")
    latest = repo.get("leetcode", 1)
    assert latest.version == 2
    assert latest.language is CodeLanguage.JAVA


def test_get_specific_version(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    repo.create("leetcode", 1, "python3")
    assert repo.get("leetcode", 1, version=1).version == 1


def test_get_missing_returns_none(conn):
    repo = _repo(conn)
    assert repo.get("leetcode", 1) is None
    assert repo.get("leetcode", 1, version=99) is None


def test_list_returns_all_versions_ascending(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    repo.create("leetcode", 1, "java")
    versions = [a.version for a in repo.list("leetcode", 1)]
    assert versions == [1, 2]


def test_update_status_persists(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    assert repo.update_status("leetcode", 1, 1, "passed") is True
    assert repo.get("leetcode", 1, version=1).status is ProblemStatus.PASSED


def test_update_status_returns_false_when_no_row(conn):
    assert _repo(conn).update_status("leetcode", 1, 99, "passed") is False


def test_update_latest_status_grades_only_newest(conn):
    """Grading the latest must leave older versions' outcomes alone."""
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    repo.create("leetcode", 1, "python3")
    repo.update_status("leetcode", 1, 1, "passed")

    assert repo.update_latest_status("leetcode", 1, "failed") is True
    assert repo.get("leetcode", 1, version=1).status is ProblemStatus.PASSED
    assert repo.get("leetcode", 1, version=2).status is ProblemStatus.FAILED


def test_update_latest_status_returns_false_when_no_attempts(conn):
    assert _repo(conn).update_latest_status("leetcode", 99, "passed") is False


def test_increment_run_count(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    repo.increment_run_count("leetcode", 1, 1)
    repo.increment_run_count("leetcode", 1, 1)
    assert repo.get("leetcode", 1, version=1).run_count == 2


def test_increment_run_count_returns_false_when_no_row(conn):
    assert _repo(conn).increment_run_count("leetcode", 1, 99) is False


def test_stats_aggregates_across_versions(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    repo.create("leetcode", 1, "python3")
    repo.create("leetcode", 1, "java")
    repo.update_status("leetcode", 1, 1, "failed")
    repo.update_status("leetcode", 1, 3, "passed")
    repo.increment_run_count("leetcode", 1, 2)

    stats = repo.stats("leetcode", 1)
    assert stats.total_attempts == 3
    assert stats.latest_version == 3
    assert stats.latest_status is ProblemStatus.PASSED
    assert stats.language is CodeLanguage.JAVA  # the latest attempt's language
    assert stats.pass_count == 1
    assert stats.fail_count == 1
    assert stats.total_runs == 1


def test_stats_returns_none_when_no_attempts(conn):
    assert _repo(conn).stats("leetcode", 1) is None


def test_all_stats_keyed_by_problem(conn):
    repo = _repo(conn)
    repo.create("leetcode", 1, "python3")
    repo.create("leetcode", 2, "python3")
    all_stats = repo.all_stats("leetcode")
    assert set(all_stats.keys()) == {1, 2}
    assert all_stats[1].total_attempts == 1
