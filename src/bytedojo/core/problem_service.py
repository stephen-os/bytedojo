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
from bytedojo.core.models.test_case import TestCase
from bytedojo.core.paths import PROBLEMS_INDEX, get_problem_file
from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager


@dataclass
class PlaceResult:
    """Result of placing a problem."""
    problem_id: int
    title: str
    language: CodeLanguage
    version: int
    file_path: Path
    skipped: bool = False
    error: Optional[str] = None


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


def place_problem(
    problem_id: int,
    language: CodeLanguage,
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
            title=problem.problem_detail.title,
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
                title=problem.problem_detail.title,
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
            title=problem.problem_detail.title,
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
