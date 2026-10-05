"""
Problem service - read-side API for problem data.

This module provides problem-related read operations:
- GET:    Load problem data from local JSON files
- QUERY:  Search/filter problems from the local index
- LOOKUP: Find problems registered in a repository's database

Placement (writing problems into a repo) lives on Repository.place_problem.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from bytedojo.core import corpus
from bytedojo.core.models.attempt_stats import AttemptStats
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.models.repository_stats import RepositoryStats
from bytedojo.core.repository import Repository
from bytedojo.core.search import find_problems as _find_problems


def get_problem(problem_id: int) -> Optional[Problem]:
    """Get a single problem by ID, or None if unsupported."""
    if not corpus.has_problem(problem_id):
        return None
    return corpus.problem(problem_id)


def get_problem_by_slug(slug: str) -> Optional[Problem]:
    """Get a single problem by slug (e.g. "two-sum"), or None if unknown."""
    for pid, entry in corpus.index().items():
        if entry.get("slug") == slug:
            return corpus.problem(pid)
    return None


def problem_exists(problem_id: int) -> bool:
    """Whether `problem_id` is in the bundled catalog."""
    return corpus.has_problem(problem_id)


def _entry_detail(pid: int, entry: dict) -> ProblemDetail:
    """Build a ProblemDetail from a catalog entry (no description)."""
    return ProblemDetail(
        id=pid,
        title=entry.get("title", ""),
        slug=entry.get("slug", ""),
        difficulty=ProblemDifficulty.from_string(entry.get("difficulty", "")),
        tags=[ProblemTag.from_string(t) for t in entry.get("tags", [])],
    )


def query_problems(
    ids: Optional[List[int]] = None,
    difficulty: ProblemDifficulty = ProblemDifficulty.NONE,
    tags: Optional[List[ProblemTag]] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[ProblemDetail]:
    """
    Query the bundled catalog with optional filters.

    Filters on catalog metadata (id / difficulty / tags) are cheap. A
    `search` additionally matches against the problem title and, for the
    entries that survive the other filters, the full description loaded
    from the bundled problem definition.

    Returns:
        List of ProblemDetail objects matching the filters, sorted by id.
    """
    id_set = set(ids) if ids else None
    search_lower = search.lower() if search else None

    results = []
    for pid, entry in corpus.index().items():
        if id_set and pid not in id_set:
            continue

        if difficulty != ProblemDifficulty.NONE:
            entry_difficulty = ProblemDifficulty.from_string(
                entry.get("difficulty", "")
            )
            if entry_difficulty != difficulty:
                continue

        if tags:
            entry_tags = [ProblemTag.from_string(t) for t in entry.get("tags", [])]
            if not any(t in entry_tags for t in tags):
                continue

        if search_lower:
            title = entry.get("title", "").lower()
            if search_lower not in title:
                description = corpus.problem(pid).problem_detail.description
                if search_lower not in description.lower():
                    continue

        results.append(_entry_detail(pid, entry))

    results.sort(key=lambda p: p.id)

    if limit:
        results = results[:limit]

    return results


def get_all_tags() -> List[ProblemTag]:
    """All tags present in the catalog, sorted, UNKNOWN excluded."""
    tags = set()
    for entry in corpus.index().values():
        for tag_str in entry.get("tags", []):
            tags.add(ProblemTag.from_string(tag_str))

    tags.discard(ProblemTag.UNKNOWN)

    return sorted(tags, key=lambda t: t.value)


def parse_problem_ids(arguments: tuple) -> List[int]:
    """
    Parse problem IDs from command arguments.

    Supports formats:
    - Single: "1"
    - Multiple: "1,2,3"
    - Range: "1..10"
    - Mixed: "1,5..10,15"

    Args:
        arguments: Tuple of argument strings

    Returns:
        List of problem IDs

    Raises:
        ValueError: If parsing fails
    """
    ids: List[int] = []

    for arg in arguments:
        # Split by comma first
        parts = arg.split(",")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check for range (e.g., "1..10")
            if ".." in part:
                range_parts = part.split("..")
                if len(range_parts) != 2:
                    raise ValueError(f"Invalid range format: {part}")

                try:
                    start = int(range_parts[0].strip())
                    end = int(range_parts[1].strip())
                except ValueError:
                    raise ValueError(f"Invalid range values: {part}")

                if start > end:
                    raise ValueError(f"Invalid range: start ({start}) > end ({end})")

                ids.extend(range(start, end + 1))
            else:
                # Single ID
                try:
                    ids.append(int(part))
                except ValueError:
                    raise ValueError(f"Invalid problem ID: {part}")

    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for pid in ids:
        if pid not in seen:
            seen.add(pid)
            unique_ids.append(pid)

    return unique_ids


# ----------------------------------------------------------------------------
# LOOKUP: find problems registered in a repository's database
# ----------------------------------------------------------------------------


@dataclass
class LookupResult:
    """
    Result of looking up registered problems by criteria.

    Convenience predicates let the caller decide how to handle the three
    cases (none / one / many) without rewriting boilerplate.
    """

    matches: List[RegisteredProblem] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.matches)

    @property
    def is_empty(self) -> bool:
        return not self.matches

    @property
    def is_unique(self) -> bool:
        return len(self.matches) == 1

    @property
    def is_ambiguous(self) -> bool:
        return len(self.matches) > 1

    @property
    def unique(self) -> Optional[RegisteredProblem]:
        """The single match if unique, else None."""
        return self.matches[0] if self.is_unique else None


def find_registered_problems(
    repo: Repository,
    *,
    identifier: Optional[str] = None,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    source: str = "leetcode",
) -> LookupResult:
    """
    Find registered problems in `repo` matching the given criteria.

    Wraps the fuzzy-matching logic in core/search.py and returns a struct
    so the caller can drive its own disambiguation UI.

    Args:
        repo: Repository to search.
        identifier: Numeric problem ID (exact match).
        name: Fuzzy match on title.
        desc: Keyword search in description.
        source: Problem source (default: 'leetcode').

    Returns:
        LookupResult containing the matches and convenience predicates.
    """
    if not repo.is_initialized:
        return LookupResult()

    with repo.session() as s:
        matches = _find_problems(
            s.problems,
            identifier=identifier,
            name=name,
            desc=desc,
            source=source,
        )
    return LookupResult(matches=matches)


@dataclass
class SolutionPathResult:
    """
    Result of resolving a solution file path for a registered problem.

    When `version` is None on the request, the caller is asking for "latest"
    and we use the file_path stored on the RegisteredProblem. When `version`
    is given, we look up the specific attempt and compute its path.

    `available_versions` is always populated when a specific version was
    requested, so the caller can render an actionable error if the version
    doesn't exist (e.g. "v3 not found. Available: v1, v2.").

    `language` is the resolved attempt's language — with flat versioning
    an older version may be in a different language than the latest, and
    the toolchain choice must follow the attempt actually being run.
    """

    path: Optional[Path] = None
    version: Optional[int] = None
    language: Optional[CodeLanguage] = None
    available_versions: List[int] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def found(self) -> bool:
        return self.path is not None


def resolve_solution_path(
    repo: Repository,
    problem: RegisteredProblem,
    *,
    version: Optional[int] = None,
) -> SolutionPathResult:
    """
    Resolve the absolute path to a registered problem's solution file.

    Args:
        repo: Repository (for build paths and DB queries).
        problem: The registered problem.
        version: Specific version to resolve, or None for the latest
            (which uses problem.file_path).

    Returns:
        SolutionPathResult with the resolved path or enough context to
        build an actionable error.
    """
    with repo.session() as s:
        attempts = s.attempts.list(problem.source, problem.problem_id)

    # "Latest" — use the file_path stored on the registered problem,
    # but determine which attempt that corresponds to so callers can
    # record per-version results and pick the right toolchain.
    if version is None:
        if not problem.file_path:
            return SolutionPathResult(error="Problem has no associated file path")
        file_path = Path(problem.file_path)
        if not file_path.is_absolute():
            file_path = repo.root_dir / file_path
        if not file_path.exists():
            return SolutionPathResult(
                error=f"Solution file not found: {file_path}",
            )

        latest = attempts[-1] if attempts else None
        return SolutionPathResult(
            path=file_path,
            version=latest.version if latest else None,
            language=latest.language if latest else problem.language,
        )

    # Specific version requested — look up the attempt
    by_version = {a.version: a for a in attempts}
    available = sorted(by_version)

    attempt = by_version.get(version)
    if attempt is None:
        return SolutionPathResult(
            available_versions=available,
            error=f"Version {version} not found",
        )

    # Need the full Problem for the slug-based folder name
    full_problem = get_problem(problem.problem_id)
    if full_problem is None:
        return SolutionPathResult(
            available_versions=available,
            error=f"Problem #{problem.problem_id} data not found",
        )

    file_path = repo.attempt_path(full_problem, attempt.language, version)
    if not file_path.exists():
        return SolutionPathResult(
            version=version,
            available_versions=available,
            error=f"Version {version} registered but file missing at {file_path}",
        )

    return SolutionPathResult(
        path=file_path,
        version=version,
        language=attempt.language,
        available_versions=available,
    )


def get_last_registered_problem(
    repo: Repository,
    source: Optional[str] = None,
) -> Optional[RegisteredProblem]:
    """
    Return the most-recently-fetched registered problem, or None if no
    problems are registered.

    Args:
        repo: Repository to query.
        source: Optional source filter. None means any source.
    """
    if not repo.is_initialized:
        return None
    with repo.session() as s:
        return s.problems.latest(source=source)


def get_summary_stats(repo: Repository) -> RepositoryStats:
    """Registered-problem counts for `dojo stats`."""
    with repo.session() as s:
        return s.problems.summary_stats()


def list_registered_problems(
    repo: Repository,
    *,
    source: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> List[RegisteredProblem]:
    """Registered problems matching the filters, ordered by problem id."""
    with repo.session() as s:
        return s.problems.list(source=source, difficulty=difficulty)


def get_attempt_status_map(
    repo: Repository,
    source: str = "leetcode",
) -> dict[int, AttemptStats]:
    """Aggregate attempt stats per problem id (for query/stats badges)."""
    if not repo.is_initialized:
        return {}
    with repo.session() as s:
        return s.attempts.all_stats(source)
