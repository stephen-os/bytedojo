"""
Shared pytest fixtures for the bytedojo test suite.

- `_initialise_logger` (session, autouse): sets up the global logger so
  `get_logger()` works for direct-import tests. Production callers always
  go through main()'s explicit setup_logger; this fills the gap for tests.

- `repo` (function): builds a fresh, fully-initialised Repository at
  tmp_path. Each test gets its own sqlite DB + .dojo / problems / build
  directories, so service- and command-level tests can exercise real DB
  writes and file placement without mocks.

- `registered_problem` + `insert_registered_problem` / `make_problem`:
  helpers for seeding the repo's DB with a Problem so command / service
  tests can exercise lookup, grading, review-scheduling, etc. against
  real rows.

- `stub_corpus`: redirects the corpus gateway at a tmp data directory so
  tests control exactly which problems / bundles are "bundled" without
  touching the real package data.
"""

import json

import pytest

from bytedojo.core import corpus
from bytedojo.core.logger import setup_logger
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository


@pytest.fixture(scope="session", autouse=True)
def _initialise_logger():
    setup_logger(debug=False)


@pytest.fixture
def repo(tmp_path) -> Repository:
    """Fresh Repository at tmp_path — real sqlite, real filesystem layout."""
    return Repository.create(tmp_path)


# --------------------------------------------------------------------------- #
# Corpus stubbing — shared across services + commands tests                   #
# --------------------------------------------------------------------------- #


class CorpusStub:
    """Writable stand-in for the bundled corpus, rooted at a tmp dir."""

    def __init__(self, root):
        self.root = root
        self._entries: dict[str, dict] = {}
        self._flush()

    def _flush(self) -> None:
        (self.root / "index.json").write_text(
            json.dumps(self._entries), encoding="utf-8"
        )
        corpus._catalog.cache_clear()

    def add_entry(
        self,
        pid: int,
        *,
        title: str = "",
        slug: str = "",
        difficulty: str = "",
        tags: list | None = None,
    ) -> None:
        """Add a catalog entry (marks `pid` as a supported problem)."""
        self._entries[str(pid)] = {
            "title": title,
            "slug": slug,
            "difficulty": difficulty,
            "tags": tags or [],
        }
        self._flush()

    def write_index(self, entries: list[dict]) -> None:
        """Replace the catalog from a list of {id, title, slug, ...} dicts."""
        self._entries = {
            str(e["id"]): {
                "title": e.get("title", ""),
                "slug": e.get("slug", ""),
                "difficulty": e.get("difficulty", ""),
                "tags": e.get("tags", []),
            }
            for e in entries
        }
        self._flush()

    def write_problem(self, payload: dict) -> None:
        """Write a problem definition file and register it in the catalog."""
        (self.root / "problems" / f"{payload['id']}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        self.add_entry(
            payload["id"],
            title=payload.get("title", ""),
            slug=payload.get("slug", ""),
            difficulty=payload.get("difficulty", ""),
            tags=payload.get("tags", []),
        )

    def write_bundle(self, payload: dict) -> None:
        """Write a test bundle file for payload['problem_id']."""
        (self.root / "tests" / f"{payload['problem_id']}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def write_raw(self, relative: str, text: str) -> None:
        """Write arbitrary (possibly malformed) content into the corpus."""
        (self.root / relative).write_text(text, encoding="utf-8")
        corpus._catalog.cache_clear()


@pytest.fixture
def stub_corpus(tmp_path, monkeypatch):
    """Redirect the corpus gateway at a tmp data dir; yields a CorpusStub."""
    root = tmp_path / "corpus-data"
    (root / "problems").mkdir(parents=True)
    (root / "tests").mkdir()
    monkeypatch.setattr(corpus, "_data_root", lambda: root)
    stub = CorpusStub(root)
    yield stub
    corpus._catalog.cache_clear()


# --------------------------------------------------------------------------- #
# Problem seeding helpers — shared across services + commands tests           #
# --------------------------------------------------------------------------- #


def make_problem(
    *,
    pid: int = 1,
    title: str = "Two Sum",
    slug: str = "two-sum",
    difficulty: ProblemDifficulty = ProblemDifficulty.EASY,
    description: str = "Given an array...",
) -> Problem:
    """Minimal Problem suitable for problems.register and friends."""
    if isinstance(difficulty, str):
        difficulty = ProblemDifficulty.from_string(difficulty)
    return Problem(
        problem_detail=ProblemDetail(
            id=pid,
            title=title,
            slug=slug,
            difficulty=difficulty,
            description=description,
        ),
    )


def insert_registered_problem(
    repo: Repository,
    *,
    pid: int = 1,
    language: CodeLanguage = CodeLanguage.PYTHON,
    file_path: str = "problems/0001-two-sum/v001/solution.py",
    **problem_kwargs,
) -> RegisteredProblem:
    """Insert a Problem into the repo's DB and return the resulting RegisteredProblem."""
    problem = make_problem(pid=pid, **problem_kwargs)
    with repo.session() as s:
        s.problems.register(
            problem, source="leetcode", language=language.value, file_path=file_path
        )
        registered = s.problems.get("leetcode", pid)
    assert registered is not None, "register did not insert"
    return registered


@pytest.fixture
def registered_problem(repo) -> RegisteredProblem:
    """A Repository pre-seeded with one Python-language Two Sum entry."""
    return insert_registered_problem(repo)
