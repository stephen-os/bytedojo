"""
Problem search utilities for bytedojo.

Provides fuzzy matching and interactive selection for registered
problems. Problems are unique per (source, problem_id) — language is
attempt metadata and plays no part in identity here.
"""

import click
from typing import List, Optional

from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repositories import ProblemsRepository


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def _fuzzy_match(query: str, text: str) -> bool:
    """
    Check if query fuzzy matches text.

    Simple substring matching for now.
    """
    query_norm = _normalize(query)
    text_norm = _normalize(text)

    # Direct substring match
    if query_norm in text_norm:
        return True

    # Word-by-word match (all query words must be present)
    query_words = query_norm.split()
    return all(word in text_norm for word in query_words)


def _score_match(query: str, problem: RegisteredProblem) -> int:
    """
    Score how well a problem matches a query.
    Higher score = better match.
    """
    query_norm = _normalize(query)
    title_norm = _normalize(problem.title)

    # Exact title match
    if query_norm == title_norm:
        return 100

    # Title starts with query
    if title_norm.startswith(query_norm):
        return 80

    # Title contains query as substring
    if query_norm in title_norm:
        return 60

    # All query words in title
    query_words = query_norm.split()
    if all(word in title_norm for word in query_words):
        return 40

    # Partial word match
    if any(word in title_norm for word in query_words):
        return 20

    return 0


def find_problems(
    problems: ProblemsRepository,
    identifier: Optional[str] = None,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    source: str = "leetcode",
) -> List[RegisteredProblem]:
    """
    Find registered problems matching criteria.

    Args:
        problems: The problems repository to search.
        identifier: Numeric problem ID (exact match)
        name: Fuzzy match on title
        desc: Keyword search in description
        source: Problem source (default: 'leetcode')

    Returns:
        List of matching problems, sorted by relevance
    """
    # An identifier is an exact numeric id — anything else matches nothing
    # (use --name/--desc for text searches).
    if identifier:
        if not identifier.isdigit():
            return []
        problem = problems.get(source, int(identifier))
        return [problem] if problem else []

    all_problems = problems.list(source=source)

    matches = []

    for problem in all_problems:
        score = 0

        # Match by name
        if name:
            if _fuzzy_match(name, problem.title):
                score = _score_match(name, problem)
            else:
                continue  # Name specified but doesn't match

        # Match by description
        if desc:
            description = problem.description or ""
            if not _fuzzy_match(desc, description):
                continue
            score = max(score, 30)  # Description match

        # If no criteria specified, match all
        if not name and not desc:
            score = 1

        if score > 0:
            matches.append((score, problem))

    # Sort by score descending, then by problem_id
    matches.sort(key=lambda x: (-x[0], x[1].problem_id))

    return [m[1] for m in matches]


def select_problem(
    problems: List[RegisteredProblem], prompt_text: str = "Select problem"
) -> Optional[RegisteredProblem]:
    """
    Interactive selection when multiple problems match.

    Args:
        problems: List of matching problems
        prompt_text: Text to display before selection

    Returns:
        Selected problem or None if cancelled
    """
    if not problems:
        return None

    if len(problems) == 1:
        return problems[0]

    # Display options
    click.echo("")
    click.echo(click.style("Multiple problems found:", fg="yellow"))
    click.echo("")

    for i, problem in enumerate(problems[:10], 1):  # Limit to 10 options
        pid = problem.problem_id
        title = problem.title
        difficulty = problem.difficulty.value if problem.difficulty else ""
        language = problem.language.value if problem.language else ""

        diff_color = {"easy": "green", "medium": "yellow", "hard": "red"}.get(
            difficulty.lower(), "white"
        )

        click.echo(f"  [{i}] {pid} - {title}", nl=False)
        if difficulty:
            click.echo(f" ({click.style(difficulty, fg=diff_color)})", nl=False)
        if language:
            click.echo(f" [{language}]", nl=False)
        click.echo("")

    if len(problems) > 10:
        click.echo(f"  ... and {len(problems) - 10} more")

    click.echo("")

    # Get selection
    try:
        choices = [str(i) for i in range(1, min(len(problems), 10) + 1)]
        choice = click.prompt(
            prompt_text, type=click.Choice(choices + ["q"]), default="1"
        )

        if choice == "q":
            return None

        return problems[int(choice) - 1]
    except (KeyboardInterrupt, EOFError):
        return None
