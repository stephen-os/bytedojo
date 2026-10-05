"""Tests for the Repository class."""

import pytest

from bytedojo.core.errors import RepoNotFoundError
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.repository import Repository, Session
from bytedojo.core.settings import SettingsManager

# --------------------------------------------------------------------------- #
# open / find / create                                                        #
# --------------------------------------------------------------------------- #


def test_open_returns_none_when_no_dojo(tmp_path):
    """No .dojo directly under `path` -> None (no walking up)."""
    assert Repository.open(tmp_path) is None


def test_open_returns_repository_when_dojo_present(tmp_path):
    (tmp_path / ".dojo").mkdir()
    repo = Repository.open(tmp_path)
    assert repo is not None
    assert repo.root_dir == tmp_path


def test_find_walks_up_to_dojo(tmp_path):
    """find() climbs ancestors until it sees .dojo."""
    (tmp_path / ".dojo").mkdir()
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)

    repo = Repository.find(deep)
    assert repo is not None
    assert repo.root_dir == tmp_path.resolve()


def test_find_returns_none_when_no_ancestor_has_dojo(tmp_path):
    """All the way to the filesystem root with no .dojo -> None."""
    deep = tmp_path / "no" / "dojo" / "here"
    deep.mkdir(parents=True)
    assert Repository.find(deep) is None


def test_create_initialises_dojo_dir_and_db(tmp_path):
    """create() lays down .dojo with db.sqlite, settings.json, .gitignore, README."""
    repo = Repository.create(tmp_path)
    assert repo is not None
    assert repo.dojo_dir.is_dir()
    assert repo.build_dir.is_dir()
    assert repo.db_path.exists()
    assert (repo.dojo_dir / "settings.json").exists()
    assert (repo.dojo_dir / ".gitignore").exists()
    assert (repo.dojo_dir / "README.md").exists()


def test_create_returns_none_when_dojo_exists(tmp_path):
    """Re-running create on an existing repo without force is a no-op."""
    Repository.create(tmp_path)
    again = Repository.create(tmp_path)
    assert again is None


def test_create_force_overrides_existing(tmp_path):
    """force=True re-runs the schema creation even if .dojo is already there."""
    Repository.create(tmp_path)
    forced = Repository.create(tmp_path, force=True)
    assert forced is not None


# --------------------------------------------------------------------------- #
# Path properties                                                             #
# --------------------------------------------------------------------------- #


def test_paths_relative_to_root(tmp_path):
    repo = Repository(root_dir=tmp_path)
    assert repo.dojo_dir == tmp_path / ".dojo"
    assert repo.db_path == tmp_path / ".dojo" / "db.sqlite"
    assert repo.settings_path == tmp_path / ".dojo" / "settings.json"
    assert repo.build_dir == tmp_path / ".dojo" / "build"
    assert repo.problems_dir == tmp_path / "problems"


# --------------------------------------------------------------------------- #
# State predicates                                                            #
# --------------------------------------------------------------------------- #


def test_exists_false_before_create(tmp_path):
    assert Repository(root_dir=tmp_path).exists is False


def test_exists_true_after_create(repo):
    """The `repo` fixture from conftest is already initialised."""
    assert repo.exists is True


def test_is_initialized_requires_both_dojo_and_db(tmp_path):
    """Empty `.dojo` directory without the sqlite file is exists=True but is_initialized=False."""
    bare = Repository(root_dir=tmp_path)
    bare.dojo_dir.mkdir()
    assert bare.exists is True
    assert bare.is_initialized is False


def test_is_initialized_true_after_create(repo):
    assert repo.is_initialized is True


# --------------------------------------------------------------------------- #
# Database access                                                             #
# --------------------------------------------------------------------------- #


def test_session_exposes_all_aggregates(repo):
    """session() yields the four aggregate repositories over one connection."""
    with repo.session() as s:
        assert isinstance(s, Session)
        assert s.problems is not None
        assert s.attempts is not None
        assert s.reviews is not None
        assert s.config is not None
        # They really share the live connection — a write through one
        # aggregate is visible through another in the same session.
        s.config.set("probe", "1")
        assert s.config.get("probe") == "1"


# --------------------------------------------------------------------------- #
# is_problem_registered + register_attempt                                    #
# --------------------------------------------------------------------------- #


def _problem():
    """Build a minimal Problem with the fields register_attempt needs."""
    from bytedojo.core.models.problem import Problem
    from bytedojo.core.models.problem_detail import ProblemDetail

    return Problem(
        problem_detail=ProblemDetail(
            id=1,
            title="Two Sum",
            slug="two-sum",
            difficulty=ProblemDifficulty.EASY,
            description="",
        ),
    )


def test_is_problem_registered_raises_without_init(tmp_path):
    """An uninitialised repo can't answer the registration question."""
    bare = Repository(root_dir=tmp_path)
    with pytest.raises(RepoNotFoundError, match="not initialized"):
        bare.is_problem_registered("leetcode", 1)


def test_is_problem_registered_false_when_no_rows(repo):
    assert repo.is_problem_registered("leetcode", 1) is False


def test_register_attempt_then_is_problem_registered_true(repo):
    repo.register_attempt(_problem(), CodeLanguage.PYTHON)
    assert repo.is_problem_registered("leetcode", 1) is True


def test_register_attempt_returns_attempt_with_v1(repo):
    attempt = repo.register_attempt(_problem(), CodeLanguage.PYTHON)
    assert attempt.version == 1
    assert attempt.problem_id == 1
    assert attempt.language is CodeLanguage.PYTHON


def test_register_attempt_stores_relative_posix_file_path(repo):
    """A committed .dojo must survive a repo move: no absolute paths."""
    repo.register_attempt(_problem(), CodeLanguage.PYTHON)
    with repo.session() as s:
        stored = s.problems.get("leetcode", 1).file_path
    assert stored == "problems/0001-two-sum/v001/solution.py"


def test_register_attempt_twice_bumps_version(repo):
    repo.register_attempt(_problem(), CodeLanguage.PYTHON)
    second = repo.register_attempt(_problem(), CodeLanguage.PYTHON)
    assert second.version == 2


def test_register_attempt_raises_without_init(tmp_path):
    bare = Repository(root_dir=tmp_path)
    with pytest.raises(RepoNotFoundError, match="not initialized"):
        bare.register_attempt(_problem(), CodeLanguage.PYTHON)


# --------------------------------------------------------------------------- #
# get_registered_problems                                                     #
# --------------------------------------------------------------------------- #


def test_get_registered_problems_empty_when_uninitialised(tmp_path):
    """Uninitialised repo gives [] for the listing (no exception)."""
    assert Repository(root_dir=tmp_path).get_registered_problems() == []


def test_get_registered_problems_lists_after_register(repo):
    repo.register_attempt(_problem(), CodeLanguage.PYTHON)
    listed = repo.get_registered_problems()
    assert len(listed) == 1
    assert listed[0].problem_id == 1


# --------------------------------------------------------------------------- #
# attempt_path                                                                #
# --------------------------------------------------------------------------- #


def test_attempt_path_is_flat_by_default(repo):
    """problems/<id>-<slug>/v<NNN>/solution.<ext> — no language segment."""
    p = _problem()
    path = repo.attempt_path(p, CodeLanguage.PYTHON, version=1)
    assert path == (repo.problems_dir / "0001-two-sum" / "v001" / "solution.py")


def test_attempt_path_honours_organize_by_language(repo):
    """The opt-in setting reintroduces the <language>/ segment."""
    manager = SettingsManager(repo.dojo_dir)
    settings = manager.load()
    settings.organize_by_language = True
    manager.save(settings)

    path = repo.attempt_path(_problem(), CodeLanguage.PYTHON, version=1)
    assert path == (
        repo.problems_dir / "0001-two-sum" / "python3" / "v001" / "solution.py"
    )


def test_attempt_path_zero_pads_version(repo):
    p = _problem()
    path = repo.attempt_path(p, CodeLanguage.JAVA, version=15)
    assert "v015" in path.parts


# --------------------------------------------------------------------------- #
# place_problem                                                               #
# --------------------------------------------------------------------------- #


def test_place_problem_writes_file_and_creates_parents(repo):
    target = repo.root_dir / "nested" / "deep" / "solution.py"
    repo.place_problem(target, "print('hi')\n")
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "print('hi')\n"


def test_place_problem_skips_write_when_content_empty(repo):
    """Empty content -> directory created, no file written."""
    target = repo.root_dir / "nested" / "empty.py"
    repo.place_problem(target, "")
    assert target.parent.is_dir()
    assert not target.exists()
