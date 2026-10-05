"""Tests for ProblemsRepository."""

from bytedojo.core.repositories import ProblemsRepository

from tests.core.repositories.conftest import make_problem


def _repo(conn) -> ProblemsRepository:
    return ProblemsRepository(conn)


def test_register_and_get_roundtrip(conn):
    repo = _repo(conn)
    repo.register(
        make_problem(), source="leetcode", language="python3", file_path="path/x.py"
    )
    problem = repo.get("leetcode", 1)
    assert problem is not None
    assert problem.title == "Two Sum"
    assert problem.file_path == "path/x.py"


def test_get_missing_returns_none(conn):
    assert _repo(conn).get("leetcode", 999) is None


def test_is_registered(conn):
    repo = _repo(conn)
    assert repo.is_registered("leetcode", 1) is False
    repo.register(make_problem(), source="leetcode", language="python3")
    assert repo.is_registered("leetcode", 1) is True


def test_reregister_updates_metadata_in_place(conn):
    """Re-registering the same (source, pid) refreshes metadata."""
    repo = _repo(conn)
    repo.register(
        make_problem(), source="leetcode", language="python3", file_path="a.py"
    )
    repo.register(
        make_problem(title="Renamed"),
        source="leetcode",
        language="python3",
        file_path="b.py",
    )
    problem = repo.get("leetcode", 1)
    assert problem.title == "Renamed"
    assert problem.file_path == "b.py"


def test_reregister_preserves_row_id_and_status(conn):
    """A new attempt re-register must not orphan reviews (row id stable)
    or wipe the recorded grade."""
    repo = _repo(conn)
    repo.register(make_problem(), source="leetcode", language="python3")
    first = repo.get("leetcode", 1)
    repo.update_status(first.id, "passed")

    repo.register(
        make_problem(), source="leetcode", language="python3", file_path="v2.py"
    )
    again = repo.get("leetcode", 1)
    assert again.id == first.id
    assert again.status.value == "passed"


def test_list_filters_by_language_and_status(conn):
    repo = _repo(conn)
    repo.register(
        make_problem(pid=1, slug="a", title="A"), source="leetcode", language="python3"
    )
    repo.register(
        make_problem(pid=2, slug="b", title="B"), source="leetcode", language="java"
    )
    repo.update_status(repo.get("leetcode", 1).id, "passed")

    assert [p.problem_id for p in repo.list(language="python3")] == [1]
    assert [p.problem_id for p in repo.list(language="java")] == [2]
    assert [p.problem_id for p in repo.list(status="passed")] == [1]
    assert [p.problem_id for p in repo.list()] == [1, 2]


def test_list_orders_by_problem_id(conn):
    repo = _repo(conn)
    for pid in (30, 4, 100):
        repo.register(
            make_problem(pid=pid, slug=f"p{pid}"), source="leetcode", language="python3"
        )
    assert [p.problem_id for p in repo.list()] == [4, 30, 100]


def test_latest_returns_most_recently_fetched(conn):
    """latest() is fetch-order, not problem-id order."""
    repo = _repo(conn)
    repo.register(make_problem(pid=50, slug="x"), source="leetcode", language="python3")
    repo.register(make_problem(pid=3, slug="y"), source="leetcode", language="python3")
    latest = repo.latest()
    assert latest is not None
    assert latest.problem_id == 3


def test_latest_empty_returns_none(conn):
    assert _repo(conn).latest() is None


def test_update_status_stamps_last_graded(conn):
    repo = _repo(conn)
    repo.register(make_problem(), source="leetcode", language="python3")
    row = repo.get("leetcode", 1)
    repo.update_status(row.id, "failed", notes="TLE")
    fresh = repo.get("leetcode", 1)
    assert fresh.status.value == "failed"
    assert fresh.notes == "TLE"
    assert fresh.last_graded is not None


def test_summary_stats_empty(conn):
    assert _repo(conn).summary_stats().total_problems == 0


def test_summary_stats_groups(conn):
    repo = _repo(conn)
    repo.register(make_problem(pid=1, slug="a"), source="leetcode", language="python3")
    repo.register(make_problem(pid=2, slug="b"), source="leetcode", language="java")
    stats = repo.summary_stats()
    assert stats.total_problems == 2
    assert stats.by_language.get("python3") == 1
    assert stats.by_language.get("java") == 1
