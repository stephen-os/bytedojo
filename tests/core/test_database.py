"""Tests for the Database thin data-access layer."""

import sqlite3
from datetime import date, datetime, timedelta

import pytest

from bytedojo.core.database import Database, create_database_schema
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _problem(pid: int = 1, slug: str = "two-sum", title: str = "Two Sum") -> Problem:
    return Problem(
        problem_detail=ProblemDetail(
            id=pid, title=title, slug=slug,
            difficulty=ProblemDifficulty.EASY, description="d",
        ),
        code_snippets=[CodeSnippet(lang=CodeLanguage.PYTHON, code="pass")],
    )


@pytest.fixture
def db_path(tmp_path):
    """A fresh sqlite path with schema applied."""
    path = tmp_path / "db.sqlite"
    create_database_schema(path)
    return path


@pytest.fixture
def seeded_problem_id(db_path) -> int:
    """Insert a Python-language problem and return its row id."""
    with Database(db_path) as db:
        db.register_problem(_problem(), source="leetcode",
                            language="python3", file_path="x")
        # Look up the row id assigned by autoincrement.
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM problems WHERE problem_id = '1'")
        return cursor.fetchone()[0]


# --------------------------------------------------------------------------- #
# create_database_schema                                                      #
# --------------------------------------------------------------------------- #

def test_create_database_schema_creates_all_tables(tmp_path):
    path = tmp_path / "db.sqlite"
    create_database_schema(path)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    for expected in {"problems", "versioned_attempts", "reviews", "config"}:
        assert expected in tables


def test_create_database_schema_seeds_default_config(tmp_path):
    path = tmp_path / "db.sqlite"
    create_database_schema(path)
    with Database(path) as db:
        assert db.get_config("default_language") == "python"
        assert db.get_config("default_source") == "leetcode"
        assert db.get_config("initialized_at") is not None


def test_create_database_schema_problems_table_defaults(tmp_path):
    """problems.status defaults to 'ungraded' (single canonical vocab)."""
    path = tmp_path / "db.sqlite"
    create_database_schema(path)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(problems)")
    cols = {row[1]: row for row in cursor.fetchall()}
    conn.close()
    assert "status" in cols
    # row[4] is the dflt_value column from PRAGMA table_info
    assert "ungraded" in str(cols["status"][4])


# --------------------------------------------------------------------------- #
# Database context manager                                                    #
# --------------------------------------------------------------------------- #

def test_context_manager_opens_and_closes(db_path):
    db = Database(db_path)
    assert db.conn is None
    with db:
        assert db.conn is not None
    assert db.conn is None


def test_context_manager_uses_row_factory(db_path):
    """Rows are sqlite3.Row instances (so dict(row) works in the model from_rows)."""
    with Database(db_path) as db:
        cursor = db.conn.cursor()
        cursor.execute("SELECT 1 AS one, 2 AS two")
        row = cursor.fetchone()
        assert dict(row) == {"one": 1, "two": 2}


# --------------------------------------------------------------------------- #
# Problems table                                                              #
# --------------------------------------------------------------------------- #

def test_register_problem_and_get_problem_roundtrip(db_path):
    with Database(db_path) as db:
        db.register_problem(_problem(), source="leetcode",
                            language="python3", file_path="path/x.py")
        problem = db.get_problem("leetcode", 1, "python3")
    assert problem is not None
    assert problem.title == "Two Sum"
    assert problem.file_path == "path/x.py"


def test_get_problem_missing_returns_none(db_path):
    with Database(db_path) as db:
        assert db.get_problem("leetcode", 999, "python3") is None


def test_is_problem_registered(db_path):
    with Database(db_path) as db:
        assert db.is_problem_registered("leetcode", 1, "python3") is False
        db.register_problem(_problem(), source="leetcode", language="python3")
        assert db.is_problem_registered("leetcode", 1, "python3") is True


def test_register_problem_uses_insert_or_replace(db_path):
    """Re-registering the same (source, pid, lang) overwrites in place."""
    with Database(db_path) as db:
        db.register_problem(_problem(), source="leetcode", language="python3",
                            file_path="a.py")
        db.register_problem(_problem(title="Renamed"), source="leetcode",
                            language="python3", file_path="b.py")
        problem = db.get_problem("leetcode", 1, "python3")
        assert problem.title == "Renamed"
        assert problem.file_path == "b.py"


def test_list_problems_filters(db_path):
    with Database(db_path) as db:
        db.register_problem(_problem(pid=1, slug="a", title="A"),
                            source="leetcode", language="python3")
        db.register_problem(_problem(pid=2, slug="b", title="B"),
                            source="leetcode", language="java")

        py_only = db.list_problems(language="python3")
        java_only = db.list_problems(language="java")

    assert [p.problem_id for p in py_only] == [1]
    assert [p.problem_id for p in java_only] == [2]


# --------------------------------------------------------------------------- #
# Attempts                                                                    #
# --------------------------------------------------------------------------- #

def test_create_attempt_starts_at_v1(db_path):
    with Database(db_path) as db:
        attempt = db.create_attempt("leetcode", 1, "python3")
    assert attempt.version == 1
    assert attempt.status is ProblemStatus.UNGRADED


def test_create_attempt_increments_per_problem_language(db_path):
    with Database(db_path) as db:
        a1 = db.create_attempt("leetcode", 1, "python3")
        a2 = db.create_attempt("leetcode", 1, "python3")
        java_a1 = db.create_attempt("leetcode", 1, "java")
    assert a1.version == 1
    assert a2.version == 2
    assert java_a1.version == 1   # different language, separate counter


def test_get_attempt_latest_returns_highest_version(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 1, "python3")
        latest = db.get_attempt("leetcode", 1, "python3")
    assert latest is not None
    assert latest.version == 2


def test_get_attempt_specific_version(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 1, "python3")
        v1 = db.get_attempt("leetcode", 1, "python3", version=1)
    assert v1.version == 1


def test_get_attempt_missing_returns_none(db_path):
    with Database(db_path) as db:
        assert db.get_attempt("leetcode", 1, "python3") is None
        assert db.get_attempt("leetcode", 1, "python3", version=99) is None


def test_list_attempts_with_language_filter(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 1, "java")

        py = db.list_attempts("leetcode", 1, "python3")
        java = db.list_attempts("leetcode", 1, "java")
        all_ = db.list_attempts("leetcode", 1)

    assert len(py) == 2
    assert len(java) == 1
    assert len(all_) == 3


def test_update_attempt_status_persists(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        changed = db.update_attempt_status("leetcode", 1, "python3", 1, "passed")
        assert changed is True
        attempt = db.get_attempt("leetcode", 1, "python3", 1)
    assert attempt.status is ProblemStatus.PASSED


def test_update_attempt_status_returns_false_when_no_row(db_path):
    with Database(db_path) as db:
        assert db.update_attempt_status("leetcode", 1, "python3", 99, "passed") is False


def test_increment_run_count(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        db.increment_run_count("leetcode", 1, "python3", 1)
        db.increment_run_count("leetcode", 1, "python3", 1)
        attempt = db.get_attempt("leetcode", 1, "python3", 1)
    assert attempt.run_count == 2


def test_increment_run_count_returns_false_when_no_row(db_path):
    with Database(db_path) as db:
        assert db.increment_run_count("leetcode", 1, "python3", 99) is False


# --------------------------------------------------------------------------- #
# Attempt stats                                                               #
# --------------------------------------------------------------------------- #

def test_get_attempt_stats_groups_by_language(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 1, "java")
        db.update_attempt_status("leetcode", 1, "python3", 2, "passed")
        db.update_attempt_status("leetcode", 1, "python3", 1, "failed")

        stats = db.get_attempt_stats("leetcode", 1)

    assert "python3" in stats
    assert "java" in stats
    py = stats["python3"]
    assert py.total_attempts == 2
    assert py.latest_version == 2
    assert py.pass_count == 1
    assert py.fail_count == 1
    assert py.latest_status is ProblemStatus.PASSED


def test_get_attempt_stats_filtered_by_language(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 1, "java")
        py_only = db.get_attempt_stats("leetcode", 1, "python3")
    assert set(py_only.keys()) == {"python3"}


def test_get_all_attempt_stats(db_path):
    with Database(db_path) as db:
        db.create_attempt("leetcode", 1, "python3")
        db.create_attempt("leetcode", 2, "python3")
        all_stats = db.get_all_attempt_stats("leetcode")
    assert set(all_stats.keys()) == {1, 2}


# --------------------------------------------------------------------------- #
# Reviews                                                                     #
# --------------------------------------------------------------------------- #

def test_schedule_review_creates_row_with_repetitions_one(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=5)
        review = db.get_review(seeded_problem_id)
    assert review is not None
    assert review.interval_days == 5
    assert review.repetitions == 1  # fresh insert seeds reps=1
    assert review.next_review_date == date.today() + timedelta(days=5)


def test_schedule_review_existing_row_increments_repetitions(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=3)
        db.schedule_review(seeded_problem_id, days_from_now=7)
        review = db.get_review(seeded_problem_id)
    assert review.interval_days == 7
    assert review.repetitions == 2


def test_get_review_returns_none_when_no_track(db_path, seeded_problem_id):
    with Database(db_path) as db:
        assert db.get_review(seeded_problem_id) is None


def test_upsert_review_overwrites_state(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=3)
        db.upsert_review(
            seeded_problem_id, interval_days=14, ease_factor=2.65, repetitions=4,
        )
        review = db.get_review(seeded_problem_id)
    assert review.interval_days == 14
    assert review.ease_factor == pytest.approx(2.65)
    assert review.repetitions == 4


def test_upsert_review_inserts_when_no_row(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.upsert_review(
            seeded_problem_id, interval_days=4, ease_factor=2.5, repetitions=0,
        )
        review = db.get_review(seeded_problem_id)
    assert review is not None
    assert review.interval_days == 4


def test_snooze_review_pushes_date(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=1)
        changed = db.snooze_review(seeded_problem_id, days=5)
        review = db.get_review(seeded_problem_id)
    assert changed is True
    assert review.next_review_date == date.today() + timedelta(days=5)


def test_snooze_review_returns_false_when_no_row(db_path, seeded_problem_id):
    with Database(db_path) as db:
        assert db.snooze_review(seeded_problem_id, days=5) is False


def test_delete_review(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=1)
        deleted = db.delete_review(seeded_problem_id)
        assert deleted is True
        assert db.get_review(seeded_problem_id) is None


def test_delete_review_returns_false_when_no_row(db_path, seeded_problem_id):
    with Database(db_path) as db:
        assert db.delete_review(seeded_problem_id) is False


def test_get_due_reviews_today_only(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=0)
        due = db.get_due_reviews(include_future=False)
    assert len(due) == 1


def test_get_due_reviews_excludes_future(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=10)
        today = db.get_due_reviews(include_future=False)
        future = db.get_due_reviews(include_future=True)
    assert today == []
    assert len(future) == 1


def test_get_review_stats_counts_today_week_total(db_path, seeded_problem_id):
    with Database(db_path) as db:
        db.schedule_review(seeded_problem_id, days_from_now=0)
        stats = db.get_review_stats()
    assert stats.due_today == 1
    assert stats.due_this_week == 1
    assert stats.total_in_review == 1


# --------------------------------------------------------------------------- #
# Repository summary stats                                                    #
# --------------------------------------------------------------------------- #

def test_get_summary_stats_empty(db_path):
    with Database(db_path) as db:
        stats = db.get_summary_stats()
    assert stats.total_problems == 0


def test_get_summary_stats_groups(db_path):
    with Database(db_path) as db:
        db.register_problem(_problem(pid=1, slug="a"), source="leetcode",
                            language="python3")
        db.register_problem(_problem(pid=2, slug="b"), source="leetcode",
                            language="java")
        stats = db.get_summary_stats()
    assert stats.total_problems == 2
    assert stats.by_language.get("python3") == 1
    assert stats.by_language.get("java") == 1


# --------------------------------------------------------------------------- #
# Config                                                                      #
# --------------------------------------------------------------------------- #

def test_config_get_with_default(db_path):
    with Database(db_path) as db:
        assert db.get_config("nonexistent", default="fallback") == "fallback"
        assert db.get_config("nonexistent") is None


def test_config_set_get_roundtrip(db_path):
    with Database(db_path) as db:
        db.set_config("review_frequency_days", "14")
        assert db.get_config("review_frequency_days") == "14"


def test_config_set_overwrites_existing(db_path):
    with Database(db_path) as db:
        db.set_config("k", "1")
        db.set_config("k", "2")
        assert db.get_config("k") == "2"


def test_get_all_config_includes_seeded_defaults(db_path):
    with Database(db_path) as db:
        cfg = db.get_all_config()
    assert cfg.get("default_language") == "python"
    assert cfg.get("default_source") == "leetcode"
    assert "initialized_at" in cfg
