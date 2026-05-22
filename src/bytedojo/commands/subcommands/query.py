"""
Query command - Search problems from local data.
"""

import click
from pathlib import Path

from bytedojo.core.logger import get_logger
from bytedojo.core.repository import Repository
from bytedojo.core.attempt_service import AttemptService
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.services import problem_service
from bytedojo.commands.ui import dim, hint, status_short, difficulty_short


def _get_best_status(status_map, problem_id):
    """Get best status for a problem from status_map."""
    lang_stats = status_map.get(problem_id, {})
    if not lang_stats:
        return ProblemStatus.UNKNOWN

    # Collect latest statuses from all languages
    statuses = [stats.latest_status for stats in lang_stats.values()]

    if ProblemStatus.PASSED in statuses:
        return ProblemStatus.PASSED
    elif ProblemStatus.FAILED in statuses:
        return ProblemStatus.FAILED
    elif ProblemStatus.SKIPPED in statuses:
        return ProblemStatus.SKIPPED
    elif ProblemStatus.UNGRADED in statuses:
        return ProblemStatus.UNGRADED
    return ProblemStatus.UNKNOWN


def _display_page(all_problems, page, per_page, status_map):
    """Display a single page of problems."""
    total = len(all_problems)
    total_pages = (total + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    page_problems = all_problems[start_idx:end_idx]

    # Display header
    click.echo(f"\n  Problems {dim(f'(page {page}/{total_pages}, {total} total)')}\n")

    # Display results
    for problem in page_problems:
        status = _get_best_status(status_map, problem.id)
        status_icon = status_short(status.value)
        diff_icon = difficulty_short(problem.difficulty.value)

        click.echo(f"  {problem.id:>5}  {status_icon}  {diff_icon}  {problem.title}")

    # Footer with pagination info
    click.echo()
    hint(f"n next  p prev  q quit  ·  page {page} of {total_pages}")

    return page, total_pages


def _interactive_loop(all_problems, start_page, per_page, status_map):
    """Run interactive pagination loop."""
    total_pages = (len(all_problems) + per_page - 1) // per_page
    current_page = start_page

    while True:
        current_page, total_pages = _display_page(all_problems, current_page, per_page, status_map)

        # Show navigation help
        nav_hints = []
        if current_page > 1:
            nav_hints.append("p=prev")
        if current_page < total_pages:
            nav_hints.append("n=next")
        nav_hints.append("#=page")
        nav_hints.append("q=quit")

        prompt = f"[{' | '.join(nav_hints)}]: "

        try:
            user_input = click.prompt("", prompt_suffix=prompt, default="q", show_default=False).strip().lower()
        except click.Abort:
            break

        if user_input in ('q', 'quit', ''):
            break
        elif user_input in ('n', 'next', '>'):
            if current_page < total_pages:
                current_page += 1
            else:
                click.echo("Already on last page.")
        elif user_input in ('p', 'prev', '<'):
            if current_page > 1:
                current_page -= 1
            else:
                click.echo("Already on first page.")
        else:
            # Try to parse as page number
            try:
                page_num = int(user_input)
                if 1 <= page_num <= total_pages:
                    current_page = page_num
                else:
                    click.echo(f"Invalid page. Enter 1-{total_pages}.")
            except ValueError:
                click.echo("Invalid input. Use n/p/#/q.")


@click.command()
@click.argument('problem_ids', nargs=-1)
@click.option(
    '--difficulty', '-d',
    type=click.Choice(['easy', 'medium', 'hard', '1', '2', '3'], case_sensitive=False),
    help='Filter by difficulty (easy/1, medium/2, hard/3)'
)
@click.option(
    '--tag', '-t',
    multiple=True,
    help='Filter by tag (comma-separated or multiple flags)'
)
@click.option(
    '--search', '-s',
    type=str,
    help='Search text in problem descriptions'
)
@click.option(
    '--page', '-p',
    type=int,
    default=1,
    help='Starting page number (default: 1)'
)
@click.option(
    '--per-page', '-n',
    type=int,
    default=20,
    help='Problems per page (default: 20)'
)
@click.option(
    '--list-tags',
    is_flag=True,
    help='List all available tags and exit'
)
@click.pass_obj
def query(ctx, problem_ids: tuple, difficulty: str, tag: tuple, search: str, page: int, per_page: int, list_tags: bool):
    """
    Search LeetCode problems with local status.

    Optionally specify problem IDs or ranges to filter:
      dojo query 1 2 3              # Specific IDs
      dojo query 1..10              # Range of IDs
      dojo query 1,5..10,15         # Mixed format

    Status indicators:
      ✓ Passed    ✗ Failed    ~ Skipped    · Not graded/fetched

    Navigation (after results display):
      n = next page    p = prev page    # = jump to page    q = quit

    Examples:
      dojo query                          # Browse all problems
      dojo query 1..50                    # Problems 1-50
      dojo query -d easy                  # Easy problems only
      dojo query -t array                 # Array problems
      dojo query -t array,hash-table      # Multiple tags
      dojo query -s "binary search"       # Search in descriptions
      dojo query -d medium -t dp -n 50    # 50 per page
      dojo query --list-tags              # Show all tags
    """
    logger = get_logger()
    logger.debug(f"query: problem_ids={problem_ids} difficulty={difficulty} tag={tag} "
                 f"search={search} page={page} per_page={per_page} list_tags={list_tags}")

    # Resolve repo
    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Handle --list-tags
    if list_tags:
        tags = problem_service.get_all_tags()
        if tags:
            click.echo(f"Available tags ({len(tags)}):")
            for t in tags:
                click.echo(f"  {t.value}")
        else:
            click.echo("No tags found.")
        logger.debug(f"query: list-tags returned {len(tags) if tags else 0} tags")
        return

    # Parse problem IDs if provided
    ids_list = None
    if problem_ids:
        try:
            ids_list = problem_service.parse_problem_ids(problem_ids)
        except ValueError as e:
            raise click.ClickException(str(e))

    # Convert tag strings to Tag enums (support comma-separated)
    tags_list = None
    if tag:
        all_tags = []
        for t in tag:
            # Split by comma to support comma-separated tags
            for part in t.split(','):
                part = part.strip()
                if part:
                    all_tags.append(ProblemTag.from_string(part))
        # Filter out UNKNOWN tags
        tags_list = [t for t in all_tags if t != ProblemTag.UNKNOWN]
        if not tags_list:
            logger.debug("query: no valid tags after filtering")
            tags_list = None

    # Resolve difficulty
    if difficulty is None:
        difficulty_enum = ProblemDifficulty.NONE
    else:
        difficulty_enum = ProblemDifficulty.from_string(difficulty)
        if difficulty_enum == ProblemDifficulty.NONE:
            raise click.ClickException(f"Unknown difficulty: {difficulty}")
    logger.debug(f"query: resolved difficulty={difficulty_enum}")

    # Query problems
    problems = problem_service.query_problems(
        ids=ids_list,
        difficulty=difficulty_enum,
        tags=tags_list,
        search=search
    )
    logger.debug(f"query: found {len(problems)} problems")

    if not problems:
        click.echo("No problems found matching your criteria.")
        return

    # Get status map if repo is initialized
    status_map = {}
    if repo.is_initialized:
        attempts = AttemptService(repo)
        all_stats = attempts.get_all_stats()
        problem_ids_set = {p.id for p in problems}
        status_map = {pid: stats for pid, stats in all_stats.items() if pid in problem_ids_set}

    # Enter interactive pagination loop
    _interactive_loop(problems, page, per_page, status_map)
