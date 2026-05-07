"""
Problem service - unified API for problem operations.

This module provides all problem-related operations:
- GET: Load problem data from local JSON files
- QUERY: Search/filter problems from index
- PLACE: Create workspace files and register in database
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from bytedojo.core.models import Problem, ProblemSummary, CodeSnippet, Difficulty, Language, Status
from bytedojo.core.paths import PROBLEMS_INDEX, get_problem_file
from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager


@dataclass
class PlaceResult:
    """Result of placing a problem."""
    problem_id: int
    title: str
    language: Language
    version: int
    file_path: Path
    skipped: bool = False
    error: Optional[str] = None


def _load_index() -> dict:
    """Load the problems index."""
    if PROBLEMS_INDEX.exists():
        with open(PROBLEMS_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _load_problem_file(problem_id: int) -> Optional[dict]:
    """Load a single problem file by ID."""
    path = get_problem_file(problem_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_problem(data: dict) -> Problem:
    """Build a Problem object from raw data."""
    snippets_dict = data.get("code_snippets", {})
    code_snippets = []
    for lang_str, code in snippets_dict.items():
        lang = Language.from_string(lang_str)
        if lang != Language.UNKNOWN:
            code_snippets.append(CodeSnippet(lang=lang, code=code))

    return Problem(
        id=data.get("id", 0),
        title=data.get("title", ""),
        title_slug=data.get("slug", ""),
        difficulty=Difficulty.from_string(data.get("difficulty", "")),
        description=data.get("description", ""),
        code_snippets=code_snippets,
        test_cases=[]
    )


def get_problem(problem_id: int) -> Optional[Problem]:
    """
    Get a single problem by ID.

    Args:
        problem_id: The problem number (e.g., 1 for Two Sum)

    Returns:
        Problem object if found, None otherwise
    """
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
    entry = index.get(slug)
    if not entry:
        return None
    return get_problem(entry["id"])


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
    difficulty: Difficulty = Difficulty.NONE,
    tags: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> List[ProblemSummary]:
    """
    Query problems with optional filters.

    Uses the index for efficient filtering without loading full problem data.

    Args:
        difficulty: Filter by difficulty level
        tags: Filter by algorithm tags (e.g., ["Array", "Hash Table"])
        limit: Maximum number of results

    Returns:
        List of ProblemSummary objects matching the filters
    """
    index = _load_index()
    results = []

    for slug, entry in index.items():
        if difficulty != Difficulty.NONE:
            entry_difficulty = Difficulty.from_string(entry.get("difficulty", ""))
            if entry_difficulty != difficulty:
                continue

        if tags:
            entry_tags = [t.lower() for t in entry.get("topics", [])]
            if not any(t.lower() in entry_tags for t in tags):
                continue

        results.append(ProblemSummary(
            id=entry["id"],
            title=entry.get("title", ""),
            title_slug=slug,
            difficulty=Difficulty.from_string(entry.get("difficulty", "")),
            tags=entry.get("topics", [])
        ))

    results.sort(key=lambda p: p.id)

    if limit:
        results = results[:limit]

    return results


def get_all_tags() -> List[str]:
    """
    Get all available algorithm tags.

    Returns:
        Sorted list of unique tags
    """
    index = _load_index()
    tags = set()

    for entry in index.values():
        for tag in entry.get("topics", []):
            tags.add(tag)

    return sorted(tags)


def place_problem(
    problem_id: int,
    language: Language,
    repo: Repository,
    force: bool = False,
    source: str = "leetcode"
) -> PlaceResult:
    """
    Place a problem: create workspace file and register in database.

    Args:
        problem_id: The problem number
        language: Programming language for the solution
        repo: Repository instance (must be initialized)
        force: If True, create new version even if problem exists
        source: Problem source (default: 'leetcode')

    Returns:
        PlaceResult with file path and metadata
    """
    # Load problem from JSON
    problem = get_problem(problem_id)
    if not problem:
        return PlaceResult(
            problem_id=problem_id,
            title="",
            language=language,
            version=0,
            file_path=Path(),
            error=f"Problem {problem_id} not found"
        )

    # Check if repo is initialized
    if not repo.is_initialized:
        return PlaceResult(
            problem_id=problem_id,
            title=problem.title,
            language=language,
            version=0,
            file_path=Path(),
            error="Repository not initialized. Run 'dojo init' first."
        )

    with DatabaseManager(repo.db_path) as db:
        # Check if already registered (unless force)
        if not force and db.is_problem_registered(source, problem_id, language.value):
            return PlaceResult(
                problem_id=problem_id,
                title=problem.title,
                language=language,
                version=0,
                file_path=Path(),
                skipped=True
            )

        # Create versioned attempt (gets next version number)
        attempt_data = db.create_attempt(problem_id, language.value, source)
        version = attempt_data['version']

        # Build folder path: problems/{id}-{slug}/{language}/v{version}/
        folder_name = problem.get_folder_name()
        version_str = f"v{version:03d}"
        attempt_path = repo.problems_dir / folder_name / language.value / version_str
        attempt_path.mkdir(parents=True, exist_ok=True)

        # Write starter code
        starter_code = problem.get_snippet(language)
        solution_filename = problem.get_solution_filename(language)
        solution_path = attempt_path / solution_filename

        if starter_code:
            solution_path.write_text(starter_code, encoding='utf-8')

        # Register problem in database
        db.register_problem(
            problem=problem,
            source=source,
            language=language.value,
            file_path=str(solution_path),
            force=force
        )

        return PlaceResult(
            problem_id=problem_id,
            title=problem.title,
            language=language,
            version=version,
            file_path=solution_path
        )


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
