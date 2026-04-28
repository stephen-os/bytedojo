"""
Problem search utilities for bytedojo.

Provides fuzzy matching and interactive selection for problems.
"""

import click
from typing import List, Dict, Any, Optional
from pathlib import Path

from bytedojo.core.database import DatabaseManager
from bytedojo.core.repository import DojoRepository


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


def _score_match(query: str, problem: Dict[str, Any]) -> int:
    """
    Score how well a problem matches a query.
    Higher score = better match.
    """
    query_norm = _normalize(query)
    title_norm = _normalize(problem.get('title', ''))

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
    db: DatabaseManager,
    identifier: Optional[str] = None,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    language: Optional[str] = None,
    source: str = 'leetcode'
) -> List[Dict[str, Any]]:
    """
    Find problems matching criteria.

    Args:
        db: Database manager instance
        identifier: Numeric problem ID (exact match)
        name: Fuzzy match on title
        desc: Keyword search in description
        language: Filter by programming language
        source: Problem source (default: 'leetcode')

    Returns:
        List of matching problems, sorted by relevance
    """
    # If identifier is numeric, do exact match
    if identifier and identifier.isdigit():
        problem = db.get_problem(source, int(identifier), language or 'python')
        if problem:
            return [problem]
        # If exact match not found with specified language, try all languages
        if language:
            return []
        # Search across all languages
        all_problems = db.list_problems(source=source)
        matches = [p for p in all_problems if p['problem_id'] == identifier]
        return matches

    # Get all problems
    all_problems = db.list_problems(source=source, language=language)

    matches = []

    for problem in all_problems:
        score = 0

        # Match by name
        if name:
            title = problem.get('title', '')
            if _fuzzy_match(name, title):
                score = _score_match(name, problem)
            else:
                continue  # Name specified but doesn't match

        # Match by description
        if desc:
            description = problem.get('description', '') or ''
            if not _fuzzy_match(desc, description):
                continue
            score = max(score, 30)  # Description match

        # If no criteria specified, match all
        if not name and not desc:
            score = 1

        if score > 0:
            matches.append((score, problem))

    # Sort by score descending, then by problem_id
    matches.sort(key=lambda x: (-x[0], x[1].get('problem_id', '')))

    return [m[1] for m in matches]


def select_problem(
    problems: List[Dict[str, Any]],
    prompt_text: str = "Select problem"
) -> Optional[Dict[str, Any]]:
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
    click.echo(click.style("Multiple problems found:", fg='yellow'))
    click.echo("")

    for i, problem in enumerate(problems[:10], 1):  # Limit to 10 options
        pid = problem.get('problem_id', '?')
        title = problem.get('title', 'Unknown')
        difficulty = problem.get('difficulty', '')
        language = problem.get('language', '')

        diff_color = {
            'Easy': 'green',
            'Medium': 'yellow',
            'Hard': 'red'
        }.get(difficulty, 'white')

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
            prompt_text,
            type=click.Choice(choices + ['q']),
            default='1'
        )

        if choice == 'q':
            return None

        return problems[int(choice) - 1]
    except (KeyboardInterrupt, EOFError):
        return None


def resolve_problem(
    identifier: Optional[str] = None,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    language: Optional[str] = None,
    source: str = 'leetcode',
    auto_select: bool = False
) -> Optional[Dict[str, Any]]:
    """
    High-level function to find and select a problem.

    Args:
        identifier: Numeric problem ID or identifier
        name: Search by name
        desc: Search by description
        language: Filter by language
        source: Problem source
        auto_select: If True, auto-select when single match

    Returns:
        Selected problem dict or None

    Raises:
        click.ClickException: If no problems found or repo not initialized
    """
    repo = DojoRepository()

    if not repo.is_initialized():
        raise click.ClickException("No .dojo repository found. Run 'dojo init' first.")

    with DatabaseManager(repo.get_db_path()) as db:
        matches = find_problems(
            db,
            identifier=identifier,
            name=name,
            desc=desc,
            language=language,
            source=source
        )

        if not matches:
            criteria = []
            if identifier:
                criteria.append(f"ID '{identifier}'")
            if name:
                criteria.append(f"name '{name}'")
            if desc:
                criteria.append(f"description '{desc}'")
            if language:
                criteria.append(f"language '{language}'")

            criteria_str = ", ".join(criteria) if criteria else "given criteria"
            raise click.ClickException(f"No problems found matching {criteria_str}")

        if len(matches) == 1 or auto_select:
            return matches[0]

        return select_problem(matches)
