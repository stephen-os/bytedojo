"""
Repository — represents a .dojo repository and the operations on it.

Construct via classmethods (`find`, `open`, `create`) or directly with a
root path. The Repository owns its location, knows its own state, and
mediates all operations against its contents (database, problems, etc.).
"""

from pathlib import Path
from typing import Optional, List

from bytedojo.core.database import Database, create_database_schema
from bytedojo.core.logger import get_logger
from bytedojo.core.models.attempt import Attempt
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.templates import GITIGNORE, README


class Repository:
    """A .dojo repository rooted at a directory."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    # ------------------------------------------------------------------
    # Locators / lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def open(cls, path: Path) -> Optional["Repository"]:
        """Return the Repository at `path`, or None if no .dojo is present."""
        logger = get_logger()
        if not (path / ".dojo").is_dir():
            logger.debug(f"No repository found at path: {path}")
            return None
        logger.debug(f"Repository found at path: {path}")
        return cls(root_dir=path)

    @classmethod
    def find(cls, start_path: Path) -> Optional["Repository"]:
        """
        Walk upward from `start_path` looking for a .dojo. Returns the
        first Repository found, or None if no ancestor contains one.
        """
        logger = get_logger()
        current = start_path.resolve()
        while True:
            if (current / ".dojo").is_dir():
                logger.debug(f"Repository found above {start_path}: {current}")
                return cls(root_dir=current)
            if current.parent == current:
                logger.debug(f"No repository found above {start_path}")
                return None
            current = current.parent

    @classmethod
    def create(cls, path: Path, force: bool = False) -> Optional["Repository"]:
        """
        Create a new .dojo at `path`. Returns the Repository on success,
        None if a .dojo already exists and `force=False`.
        """
        logger = get_logger()
        repo = cls(root_dir=path)
        if repo.exists and not force:
            logger.debug(f".dojo already exists at {path}")
            return None
        logger.debug(f"Creating repository at {path} (force={force})")
        repo.dojo_dir.mkdir(exist_ok=True)
        create_database_schema(repo.db_path)
        repo._write_default_settings()
        repo._write_gitignore()
        repo._write_readme()
        return repo

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    @property
    def dojo_dir(self) -> Path:
        return self.root_dir / ".dojo"

    @property
    def db_path(self) -> Path:
        return self.dojo_dir / "db.sqlite"

    @property
    def settings_path(self) -> Path:
        return self.dojo_dir / "settings.json"

    @property
    def build_dir(self) -> Path:
        return self.dojo_dir / "build"

    @property
    def problems_dir(self) -> Path:
        return self.root_dir / "problems"

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def exists(self) -> bool:
        """Whether the .dojo directory is present on disk."""
        return self.dojo_dir.exists()

    @property
    def is_initialized(self) -> bool:
        """Whether .dojo is present and the database has been created."""
        return self.exists and self.db_path.exists()

    # ------------------------------------------------------------------
    # Database access
    # ------------------------------------------------------------------

    def open_db(self) -> Database:
        """Construct a fresh Database bound to this repo's db path."""
        return Database(self.db_path)

    # ------------------------------------------------------------------
    # Repo-level operations
    # ------------------------------------------------------------------

    def is_problem_registered(
        self,
        source: str,
        problem_id: int,
        language: CodeLanguage,
    ) -> bool:
        """Whether a problem is registered in this repo's database."""
        if not self.is_initialized:
            raise RuntimeError("Repository not initialized. Run 'dojo init' first.")
        with self.open_db() as db:
            return db.is_problem_registered(source, problem_id, language.value)

    def get_registered_problems(self) -> List[RegisteredProblem]:
        """Get all registered problems from the database."""
        if not self.is_initialized:
            return []
        with self.open_db() as db:
            return db.list_problems()

    def register_attempt(
        self,
        problem: Problem,
        language: CodeLanguage,
        source: str = "leetcode",
    ) -> Attempt:
        """
        Create a new versioned attempt and register the problem in the DB.
        Returns the Attempt (problem_id, language, version).
        """
        if not self.is_initialized:
            raise RuntimeError("Repository not initialized. Run 'dojo init' first.")

        problem_id = problem.problem_detail.id

        with self.open_db() as db:
            attempt = db.create_attempt(source, problem_id, language.value)

            db.register_problem(
                problem=problem,
                source=source,
                language=language.value,
                file_path=str(self.attempt_path(problem, language, attempt.version)),
            )

            return attempt

    def attempt_path(
        self,
        problem: Problem,
        language: CodeLanguage,
        version: int,
    ) -> Path:
        """Solution file path for a given problem/language/version."""
        folder_name = problem.get_folder_name()
        version_str = f"v{version:03d}"
        return (
            self.problems_dir
            / folder_name
            / language.value
            / version_str
            / problem.get_solution_filename(language)
        )

    def place_problem(self, path: Path, content: str) -> None:
        """
        Write `content` to `path`, creating parent directories.

        Filesystem only — no DB writes. The caller (FetchService) decides
        both the destination and what content goes in the file (raw
        snippet, formatter output, etc.).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        if content:
            path.write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_default_settings(self) -> None:
        from bytedojo.core.settings import SettingsManager
        SettingsManager(self.dojo_dir).create_default()

    def _write_gitignore(self) -> None:
        (self.dojo_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")

    def _write_readme(self) -> None:
        (self.dojo_dir / "README.md").write_text(README, encoding="utf-8")
