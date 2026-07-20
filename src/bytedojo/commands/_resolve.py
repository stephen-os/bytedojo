"""
Shared CLI helper — resolve a registered problem from the standard
identifier / name / desc / last selectors.

Used by `dojo grade` and `dojo review`. Both take the same selector flags
and do the same find + disambiguate dance; this helper is the single
source of truth for that flow.

Disambiguation uses the interactive prompt in core.search.select_problem,
which is CLI-only. The TUI calls find_registered_problems directly and
presents its own picker.
"""

from typing import Optional

import click

from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.core.search import select_problem
from bytedojo.services.problem_service import (
    find_registered_problems,
    get_last_registered_problem,
)


def resolve_problem(
    repo: Repository,
    language: str,
    *,
    identifier: Optional[str],
    name: Optional[str],
    desc: Optional[str],
    last: bool,
    command_name: str,
    require_selector: bool = True,
) -> RegisteredProblem:
    """
    Resolve the problem this command should act on.

    Args:
        repo: The repository to look up registered problems in.
        language: Language to filter by (e.g. "python3").
        identifier: Numeric problem ID (exact match) or None.
        name: Fuzzy match on title, or None.
        desc: Keyword search in description, or None.
        last: If True, use the most-recently-fetched problem.
        command_name: The verb used in error message examples
            (e.g. "test", "run", "grade").
        require_selector: When True (default), raise if none of
            identifier / name / desc / last are provided. Callers
            that have a fallback mode (e.g. grade's batch view)
            should pass False.

    Returns:
        The resolved RegisteredProblem.

    Raises:
        click.ClickException: No selector provided, no match found, or
            no problems registered for `--last`.
        click.Abort: User cancelled the disambiguation prompt.
    """
    if last:
        problem = get_last_registered_problem(repo, language=language)
        if problem is None:
            lang_flag = language if language != 'python3' else 'python'
            raise click.ClickException(
                f"No {language} problems found. "
                f"Fetch one first with: dojo fetch <id> --{lang_flag}"
            )
        return problem

    if require_selector and not identifier and not name and not desc:
        raise click.ClickException(
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
        language=language,
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
        raise click.ClickException(
            f"No {language} problems found matching {criteria_str}. "
            f"Fetch one first with: dojo fetch <id>"
        )

    if lookup.is_unique:
        return lookup.unique

    # Multiple matches — interactive disambiguation (CLI only)
    chosen = select_problem(lookup.matches)
    if chosen is None:
        raise click.Abort()
    return chosen
