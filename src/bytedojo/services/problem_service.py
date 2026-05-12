"""
Problem service - read-side API for problem data.

This module provides problem-related read operations:
- GET:    Load problem data from local JSON files
- QUERY:  Search/filter problems from the local index
- LOOKUP: Find problems registered in a repository's database

Placement (writing problems into a repo) lives on Repository.place_problem.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.code_parameters import CodeParameters
from bytedojo.core.models.code_snippet import CodeSnippet
from bytedojo.core.models.entry_point import EntryPoint
from bytedojo.core.models.example import Example
from bytedojo.core.models.parameter import Parameter
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_code import ProblemCode
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.models.test_case import TestCase
from bytedojo.core.paths import PROBLEMS_INDEX, get_problem_file
from bytedojo.core.repository import Repository
from bytedojo.core.search import find_problems as _find_problems


def _load_index() -> list:
    """Load the problems index as a list of problem entries."""
    if PROBLEMS_INDEX.exists():
        with open(PROBLEMS_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _load_problem_file(problem_id: int) -> Optional[dict]:
    """Load a single problem file by ID."""
    path = get_problem_file(problem_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_problem(data: dict) -> Problem:
    """Build a Problem object from raw data."""
    # Parse tags
    tags = [ProblemTag.from_string(t) for t in data.get("tags", [])]

    # Build the ProblemDetail
    problem_detail = ProblemDetail(
        id=data.get("id", 0),
        title=data.get("title", ""),
        slug=data.get("slug", ""),
        difficulty=ProblemDifficulty.from_string(data.get("difficulty", "")),
        description=data.get("description", ""),
        tags=tags,
    )

    # Parse examples
    examples = [
        Example(
            example_num=ex.get("example_num", 0),
            example_text=ex.get("example_text", ""),
            images=ex.get("images", [])
        )
        for ex in data.get("examples", [])
    ]

    # Parse test cases (language-agnostic, lives at top level now)
    test_cases = [
        TestCase(input=tc.get("input", ""), output=tc.get("output", ""))
        for tc in data.get("test_cases", [])
    ]

    # Build per-language ProblemCode bundles by joining the four per-language maps
    code_snippets_map = data.get("code_snippets", {}) or {}
    entry_points_map = data.get("entry_points", {}) or {}
    types_map = data.get("types", {}) or {}
    test_snippets_map = data.get("test_snippets", {}) or {}

    # Union of all language keys we have any data for
    lang_keys = set()
    lang_keys.update(code_snippets_map.keys())
    lang_keys.update(entry_points_map.keys())
    lang_keys.update(types_map.keys())
    lang_keys.update(test_snippets_map.keys())

    problem_codes: List[ProblemCode] = []
    for lang_str in lang_keys:
        lang = CodeLanguage.from_string(lang_str)
        if lang == CodeLanguage.UNKNOWN:
            continue

        problem_code_snippet = CodeSnippet(
            lang=lang,
            code=code_snippets_map.get(lang_str, ""),
        )

        entry_point = EntryPoint(
            lang=lang,
            expression=entry_points_map.get(lang_str, ""),
        )

        type_data = types_map.get(lang_str, {}) or {}
        input_params: List[Parameter] = []
        for param_dict in type_data.get("input", []):
            for name, type_str in param_dict.items():
                input_params.append(Parameter(name=name, type_str=type_str))
        problem_parameters = CodeParameters(
            lang=lang,
            input_params=input_params,
            output_type=type_data.get("output", "") or "",
        )

        test_code_snippet = CodeSnippet(
            lang=lang,
            code=test_snippets_map.get(lang_str, ""),
        )

        problem_codes.append(ProblemCode(
            lang=lang,
            problem_code=problem_code_snippet,
            problem_parameters=problem_parameters,
            entry_point=entry_point,
            test_code=test_code_snippet,
        ))

    return Problem(
        problem_detail=problem_detail,
        problem_codes=problem_codes,
        examples=examples,
        constraints=data.get("constraints", []),
        hints=data.get("hints", []),
        test_cases=test_cases,
    )

def get_problem(problem_id: int) -> Optional[Problem]:
    """Get a single problem by ID."""
    data = _load_problem_file(problem_id)
    if not data:
        return None
    return _build_problem(data)

def get_problem_by_slug(slug: str) -> Optional[Problem]:
    """
    Get a single problem by slug.

    Args:
        slug: The problem slug (e.g., "two-sum")

    Returns:
        Problem object if found, None otherwise
    """
    index = _load_index()
    for entry in index:
        if entry.get("slug") == slug:
            return get_problem(entry["id"])
    return None


def problem_exists(problem_id: int) -> bool:
    """
    Check if a problem exists.

    Args:
        problem_id: The problem number

    Returns:
        True if problem file exists
    """
    return get_problem_file(problem_id).exists()

def query_problems(
    ids: Optional[List[int]] = None,
    difficulty: ProblemDifficulty = ProblemDifficulty.NONE,
    tags: Optional[List[ProblemTag]] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None
) -> List[ProblemDetail]:
    """
    Query problems with optional filters.

    Uses the index for efficient filtering without loading full problem data.

    Args:
        ids: Filter by specific problem IDs
        difficulty: Filter by difficulty level
        tags: Filter by tags (e.g., [ProblemTag.ARRAY, ProblemTag.HASH_TABLE])
        search: Search text in description
        limit: Maximum number of results

    Returns:
        List of ProblemDetail objects matching the filters
    """
    index = _load_index()
    results = []

    # Pre-compute ID set for efficiency
    id_set = set(ids) if ids else None
    search_lower = search.lower() if search else None

    for entry in index:
        # Filter by IDs
        if id_set and entry["id"] not in id_set:
            continue

        # Filter by difficulty
        if difficulty != ProblemDifficulty.NONE:
            entry_difficulty = ProblemDifficulty.from_string(entry.get("difficulty", ""))
            if entry_difficulty != difficulty:
                continue

        # Filter by tags
        if tags:
            entry_tags = [ProblemTag.from_string(t) for t in entry.get("tags", [])]
            if not any(t in entry_tags for t in tags):
                continue

        # Filter by description search
        if search_lower:
            desc = entry.get("description", "").lower()
            if search_lower not in desc:
                continue

        results.append(ProblemDetail(
            id=entry["id"],
            title=entry.get("title", ""),
            slug=entry.get("slug", ""),
            difficulty=ProblemDifficulty.from_string(entry.get("difficulty", "")),
            description=entry.get("description", ""),
            tags=[ProblemTag.from_string(t) for t in entry.get("tags", [])],
        ))

    results.sort(key=lambda p: p.id)

    if limit:
        results = results[:limit]

    return results


def get_all_tags() -> List[ProblemTag]:
    """
    Get all available tags.

    Returns:
        Sorted list of unique tags
    """
    index = _load_index()
    tags = set()

    for entry in index:
        for tag_str in entry.get("tags", []):
            tags.add(ProblemTag.from_string(tag_str))

    # Remove UNKNOWN if present
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
    ids = []

    for arg in arguments:
        # Split by comma first
        parts = arg.split(',')

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check for range (e.g., "1..10")
            if '..' in part:
                range_parts = part.split('..')
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
    language: Optional[str] = None,
    source: str = "leetcode",
) -> LookupResult:
    """
    Find registered problems in `repo` matching the given criteria.

    Wraps the fuzzy-matching logic in core/search.py and returns a struct
    so the caller can drive its own disambiguation UI (CLI prompt, TUI list).

    Args:
        repo: Repository to search.
        identifier: Numeric problem ID (exact match).
        name: Fuzzy match on title.
        desc: Keyword search in description.
        language: Filter by language.
        source: Problem source (default: 'leetcode').

    Returns:
        LookupResult containing the matches and convenience predicates.
    """
    if not repo.is_initialized:
        return LookupResult()

    with repo.open_db() as db:
        matches = _find_problems(
            db,
            identifier=identifier,
            name=name,
            desc=desc,
            language=language,
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
    """
    path: Optional[Path] = None
    version: Optional[int] = None
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
    # "Latest" — use the file_path stored on the registered problem
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
        return SolutionPathResult(path=file_path)

    # Specific version requested — look up the attempt
    with repo.open_db() as db:
        attempts = db.list_attempts(
            problem.source, problem.problem_id, problem.language.value
        )
    available = [a.version for a in attempts]

    if version not in available:
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

    file_path = repo.attempt_path(full_problem, problem.language, version)
    if not file_path.exists():
        return SolutionPathResult(
            version=version,
            available_versions=available,
            error=f"Version {version} registered but file missing at {file_path}",
        )

    return SolutionPathResult(
        path=file_path,
        version=version,
        available_versions=available,
    )


def get_last_registered_problem(
    repo: Repository,
    language: str,
    source: Optional[str] = None,
) -> Optional[RegisteredProblem]:
    """
    Return the most-recently-fetched registered problem for `language`,
    or None if no problems are registered.

    Args:
        repo: Repository to query.
        language: Language to filter by (e.g. "python3").
        source: Optional source filter. None means any source.
    """
    if not repo.is_initialized:
        return None
    with repo.open_db() as db:
        problems = db.list_problems(source=source, language=language, limit=1)
    return problems[0] if problems else None
