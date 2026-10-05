"""
Corpus gateway — the single seam over the bundled problem data.

All problem/test data ships inside the package at ``bytedojo/data`` and
is read through ``importlib.resources`` so it works identically from a
source checkout and an installed wheel. Nothing else in the app reads
the data files or their paths directly.

Layout:
    bytedojo/data/index.json          catalog {id: {title, slug, difficulty, tags}}
    bytedojo/data/problems/<id>.json  problem definitions (prose + signature)
    bytedojo/data/tests/<id>.json     test bundles (signature + method + cases)

The set of catalog ids is exactly the set of supported problems — every
id has both a problem definition and a test bundle (enforced by
scripts/validate_data.py).
"""

import json
from functools import lru_cache
from types import MappingProxyType
from typing import Any, Mapping

from bytedojo.core.errors import (
    BundleNotFoundError,
    DataError,
    UnsupportedProblemError,
)
from bytedojo.core.models.example import Example
from bytedojo.core.models.problem import Problem
from bytedojo.core.models.problem_detail import ProblemDetail
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.core.models.test_bundle import TestBundle, TestSignature

#: The bundle schema this build understands (§6.2 — must be validated).
SCHEMA_VERSION = 1


def _data_root():
    """Traversable root of the bundled data directory."""
    from importlib.resources import files

    return files("bytedojo").joinpath("data")


def _read_json(relative: str, *, context: str) -> Any:
    """Read and parse a JSON resource; DataError with context on failure."""
    resource = _data_root().joinpath(relative)
    try:
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as err:
        raise DataError(f"Bundled {context} is missing ({relative}).") from err
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise DataError(f"Bundled {context} is malformed ({relative}): {err}") from err


@lru_cache(maxsize=1)
def _catalog() -> Mapping[int, dict]:
    raw = _read_json("index.json", context="catalog index")
    try:
        entries = {int(pid): entry for pid, entry in raw.items()}
    except (AttributeError, ValueError) as err:
        raise DataError("Bundled catalog index has an invalid shape.") from err
    return MappingProxyType(entries)


def index() -> Mapping[int, dict]:
    """The catalog: {id: {title, slug, difficulty, tags}} (read-only)."""
    return _catalog()


def has_problem(problem_id: int) -> bool:
    """Whether `problem_id` is a supported (bundled) problem."""
    return problem_id in _catalog()


def problem(problem_id: int) -> Problem:
    """Load and parse the bundled problem definition for `problem_id`.

    Raises UnsupportedProblemError for ids outside the catalog and
    DataError when the definition file is missing or malformed.
    """
    if not has_problem(problem_id):
        raise UnsupportedProblemError(problem_id)
    data = _read_json(f"problems/{problem_id}.json", context="problem definition")
    return _build_problem(data)


def bundle(problem_id: int) -> TestBundle:
    """Load the typed test bundle for `problem_id`.

    Raises BundleNotFoundError when absent and DataError on a malformed
    file or an unsupported schema_version.
    """
    resource = _data_root().joinpath(f"tests/{problem_id}.json")
    try:
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as err:
        raise BundleNotFoundError(problem_id) from err
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise DataError(
            f"Test bundle for problem #{problem_id} is malformed: {err}"
        ) from err

    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise DataError(
            f"Test bundle for problem #{problem_id} has schema_version "
            f"{version!r}; this build understands {SCHEMA_VERSION}."
        )
    try:
        return TestBundle(**data)
    except (TypeError, KeyError) as err:
        raise DataError(
            f"Test bundle for problem #{problem_id} has an invalid shape: {err}"
        ) from err


def bundle_text(problem_id: int) -> str:
    """Raw JSON text of a test bundle (for staging into a build dir)."""
    resource = _data_root().joinpath(f"tests/{problem_id}.json")
    try:
        return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as err:
        raise BundleNotFoundError(problem_id) from err


def _build_problem(data: dict) -> Problem:
    """Build a Problem from raw problem-definition JSON."""
    detail = ProblemDetail(
        id=data.get("id", 0),
        title=data.get("title", ""),
        slug=data.get("slug", ""),
        difficulty=ProblemDifficulty.from_string(data.get("difficulty", "")),
        description=data.get("description", ""),
        tags=[ProblemTag.from_string(t) for t in data.get("tags", [])],
    )

    examples = [
        Example(
            example_num=ex.get("example_num", 0),
            example_text=ex.get("example_text", ""),
        )
        for ex in data.get("examples", [])
    ]

    sig_data = data.get("signature")
    signature = TestSignature(**sig_data) if sig_data else None

    return Problem(
        problem_detail=detail,
        examples=examples,
        constraints=data.get("constraints", []),
        hints=data.get("hints", []),
        signature=signature,
    )
