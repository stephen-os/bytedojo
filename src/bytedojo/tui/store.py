"""
Data assembly for the TUI screens.

Each store reads from the (read-only-to-the-TUI) ``Repository`` /
``problem_service`` / ``SystemService`` and shapes the result into the
small typed structures each screen renders. Screens stay thin and
testable; data plumbing lives here.

Stores are intentionally not Textual-aware — they're plain Python so
they can be exercised directly in tests.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.repository import Repository
from bytedojo.core.settings import SettingsManager
from bytedojo.services import problem_service
from bytedojo.services.review_service import ReviewService
from bytedojo.services.system_service import SystemReport, SystemService
from bytedojo.tui.util import time_ago


# =========================================================================
# Practise — Problem grouped by id, with languages and version history
# =========================================================================

@dataclass
class VersionAttempt:
    """One versioned attempt of a (problem, language)."""
    version: int
    status: ProblemStatus
    output: str       # e.g. "Passed: 56/56" / "—" / "Compile error"
    when: str         # relative time label


@dataclass
class LanguageEntry:
    """All attempts for one language of a problem."""
    language: CodeLanguage
    status: ProblemStatus            # latest status — used by the row label
    versions: List[VersionAttempt] = field(default_factory=list)


@dataclass
class PractiseProblem:
    """Top-level problem entry — what Practise tree shows."""
    problem_id: int
    title: str
    difficulty: ProblemDifficulty
    tags: List[str] = field(default_factory=list)
    languages: List[LanguageEntry] = field(default_factory=list)


class PractiseStore:
    """Loads registered problems grouped by ``problem_id`` with per-language
    version children. The ``problems`` attribute is empty if there is no
    initialised repo on the current path.
    """

    def __init__(self, repo: Optional[Repository]) -> None:
        self.repo = repo
        self.problems: List[PractiseProblem] = []
        if repo is not None and repo.is_initialized:
            self._reload()

    def _reload(self) -> None:
        assert self.repo is not None
        registered = self.repo.get_registered_problems()

        # Group RegisteredProblems by problem_id.
        by_pid: Dict[int, List] = {}
        for rp in registered:
            by_pid.setdefault(rp.problem_id, []).append(rp)

        problems: List[PractiseProblem] = []
        for pid, rps in sorted(by_pid.items()):
            # Augment with the catalog JSON for tags + canonical title.
            full = problem_service.get_problem(pid)
            if full is not None:
                title = full.problem_detail.title
                difficulty = full.problem_detail.difficulty
                tags = [t.value for t in full.problem_detail.tags]
            else:
                # Catalog missing — fall back to what's on the row.
                title = rps[0].title or "(untitled)"
                difficulty = rps[0].difficulty
                tags = []

            languages: List[LanguageEntry] = []
            for rp in sorted(rps, key=lambda r: r.language.value):
                attempts = self._load_attempts(rp)
                versions = [
                    VersionAttempt(
                        version=a.version,
                        status=a.test_status if a.test_status != ProblemStatus.UNKNOWN else a.status,
                        output=a.test_output or "—",
                        when=time_ago(a.last_test_run or a.created_at),
                    )
                    for a in sorted(attempts, key=lambda x: -x.version)
                ]
                languages.append(LanguageEntry(
                    language=rp.language,
                    status=rp.status,
                    versions=versions,
                ))

            problems.append(PractiseProblem(
                problem_id=pid,
                title=title,
                difficulty=difficulty,
                tags=tags,
                languages=languages,
            ))

        self.problems = problems

    def _load_attempts(self, rp) -> list:
        assert self.repo is not None
        with self.repo.open_db() as db:
            return db.list_attempts(rp.source, rp.problem_id, rp.language.value)

    def refresh(self) -> None:
        """Re-read from disk. Called on the screen's ``r`` keybind."""
        if self.repo is not None and self.repo.is_initialized:
            self._reload()


# =========================================================================
# Discover — catalog browse with registration indicator
# =========================================================================

@dataclass
class CatalogEntry:
    """One problem in the local LeetCode catalog (registered or not)."""
    problem_id: int
    title: str
    difficulty: ProblemDifficulty
    description: str
    tags: List[str] = field(default_factory=list)
    registered_langs: Set[CodeLanguage] = field(default_factory=set)


class DiscoverStore:
    """Loads the local LeetCode catalog and cross-references it against the
    repo's registrations to produce a ``registered_langs`` per entry.
    Works even without a repo (registered set is just empty).
    """

    def __init__(self, repo: Optional[Repository]) -> None:
        self.repo = repo
        self.entries: List[CatalogEntry] = self._load()

    def _load(self) -> List[CatalogEntry]:
        # `query_problems()` returns lightweight ProblemDetail objects.
        catalog = problem_service.query_problems()
        registered: Dict[int, Set[CodeLanguage]] = {}
        if self.repo is not None and self.repo.is_initialized:
            for rp in self.repo.get_registered_problems():
                registered.setdefault(rp.problem_id, set()).add(rp.language)
        return [
            CatalogEntry(
                problem_id=p.id,
                title=p.title,
                difficulty=p.difficulty,
                description=p.description,
                tags=[t.value for t in p.tags],
                registered_langs=registered.get(p.id, set()),
            )
            for p in catalog
        ]


# =========================================================================
# Health — toolchains + settings + stats for the "Health" mode
# =========================================================================

@dataclass
class HealthData:
    repo: Optional[Repository]
    system_report: SystemReport
    settings: Dict[str, str]     # ordered display rows
    stats: Dict[str, str]        # ordered display rows
    review_due: int              # count of reviews due today (0 when no repo)


class HealthStore:
    """Loads toolchain status + settings + stats for the Health screen."""

    def __init__(self, repo: Optional[Repository]) -> None:
        self.repo = repo
        self.data = self._load()

    def _load(self) -> HealthData:
        system_report = SystemService().check()

        settings: Dict[str, str] = {}
        stats: Dict[str, str] = {}
        review_due = 0

        if self.repo is not None and self.repo.is_initialized:
            # Settings: settings.json + db config.
            mgr = SettingsManager(self.repo.dojo_dir)
            user_settings = mgr.load()
            with self.repo.open_db() as db:
                settings["default_language"]      = db.get_config("default_language", "python")
                settings["default_source"]        = db.get_config("default_source", "leetcode")
                settings["review_frequency_days"] = db.get_config("review_frequency_days", "7")
            settings["leetcode.organization"] = user_settings.leetcode.organization

            # Stats: registered totals + breakdowns.
            with self.repo.open_db() as db:
                summary = db.get_summary_stats()

            stats["Total problems"] = str(summary.total_problems)
            for diff, count in sorted(summary.by_difficulty.items()):
                stats[f"  {diff}"] = str(count)
            if summary.by_language:
                stats["By language"] = ""
                for lang, count in sorted(summary.by_language.items()):
                    stats[f"  {lang}"] = str(count)

            # Review queue.
            review_due = ReviewService().get_due_count(self.repo)

        return HealthData(
            repo=self.repo,
            system_report=system_report,
            settings=settings,
            stats=stats,
            review_due=review_due,
        )
