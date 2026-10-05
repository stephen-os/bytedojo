"""
Shared CLI helper — resolve a registered problem from the standard
identifier / name / desc / last selectors.

Problems are unique per (source, problem_id); language is attempt
metadata (§7.1). A `--python`-style flag is therefore a preference,
not a filter: when the resolved problem's latest attempt is in a
different language we warn rather than silently picking another file.

Disambiguation uses the interactive prompt in core.search.select_problem.
"""

from pathlib import Path
from typing import Optional

import click

from bytedojo.core.errors import ProblemNotFoundError, RepoNotFoundError
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.core.search import select_problem
from bytedojo.services.problem_service import (
    find_registered_problems,
    get_last_registered_problem,
)


def require_repo() -> Repository:
    """The repository containing cwd, or RepoNotFoundError (§10)."""
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise RepoNotFoundError()
    return repo


def resolve_problem(
    repo: Repository,
    *,
    identifier: Optional[str],
    name: Optional[str],
    desc: Optional[str],
    last: bool,
    command_name: str,
    language: Optional[str] = None,
    require_selector: bool = True,
) -> RegisteredProblem:
    """
    Resolve the problem this command should act on.

    Args:
        repo: The repository to look up registered problems in.
        identifier: Numeric problem ID (exact match) or None.
        name: Fuzzy match on title, or None.
        desc: Keyword search in description, or None.
        last: If True, use the most-recently-fetched problem.
        command_name: The verb used in error message examples
            (e.g. "test", "run", "grade").
        language: The explicitly requested language (e.g. "python3"),
            or None when no language flag was given. Used only for the
            latest-attempt mismatch warning.
        require_selector: When True (default), raise if none of
            identifier / name / desc / last are provided. Callers
            that have a fallback mode (e.g. grade's batch view)
            should pass False.

    Returns:
        The resolved RegisteredProblem.

    Raises:
        click.UsageError: No selector provided.
        ProblemNotFoundError: No registered problem matched.
        click.Abort: User cancelled the disambiguation prompt.
    """
    problem = _lookup(
        repo,
        identifier=identifier,
        name=name,
        desc=desc,
        last=last,
        command_name=command_name,
        require_selector=require_selector,
    )
    _warn_on_language_mismatch(problem, language)
    return problem


def _lookup(
    repo: Repository,
    *,
    identifier: Optional[str],
    name: Optional[str],
    desc: Optional[str],
    last: bool,
    command_name: str,
    require_selector: bool,
) -> RegisteredProblem:
    if last:
        problem = get_last_registered_problem(repo)
        if problem is None:
            raise ProblemNotFoundError(
                "No problems registered yet. " "Fetch one first with: dojo fetch <id>"
            )
        return problem

    if require_selector and not identifier and not name and not desc:
        raise click.UsageError(
            f"Please specify a problem ID, --name, --desc, or --last\n"
            f"Examples:\n"
            f"  dojo {command_name} 1\n"
            f"  dojo {command_name} --name 'Two Sum'\n"
            f"  dojo {command_name} --last"
        )

    lookup = find_registered_problems(
        repo,
        identifier=identifier,
        name=name,
        desc=desc,
    )

    if lookup.is_empty:
        criteria = []
        if identifier:
            criteria.append(f"ID '{identifier}'")
        if name:
            criteria.append(f"name '{name}'")
        if desc:
            criteria.append(f"description '{desc}'")
        criteria_str = ", ".join(criteria) if criteria else "given criteria"
        raise ProblemNotFoundError(
            f"No registered problems found matching {criteria_str}. "
            f"Fetch one first with: dojo fetch <id>"
        )

    unique = lookup.unique
    if unique is not None:
        return unique

    # Multiple matches — interactive disambiguation (CLI only)
    chosen = select_problem(lookup.matches)
    if chosen is None:
        raise click.Abort()
    return chosen


def _warn_on_language_mismatch(
    problem: RegisteredProblem,
    requested_language: Optional[str],
) -> None:
    """Warn when an explicit language flag disagrees with the attempt."""
    if requested_language is None:
        return
    if problem.language.value == requested_language:
        return
    click.echo(
        click.style(
            f"  Warning: latest attempt for #{problem.problem_id} is "
            f"{problem.language.value}, not {requested_language}.",
            fg="yellow",
        ),
        err=True,
    )
