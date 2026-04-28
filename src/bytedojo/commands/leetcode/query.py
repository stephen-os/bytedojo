"""
LeetCode query command.
"""

import click

from bytedojo.core.logger import get_logger
from bytedojo.core.leetcode import LeetCodeClient
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


DIFFICULTY_MAP = {
    'easy': 1,
    'medium': 2,
    'hard': 3,
    '1': 1,
    '2': 2,
    '3': 3,
}

# Status indicators
STATUS_ICONS = {
    'passed': click.style('[P]', fg='green'),
    'failed': click.style('[F]', fg='red'),
    'skipped': click.style('[S]', fg='yellow'),
    'untested': click.style('[ ]', fg='bright_black'),  # Legacy ungraded
    'ungraded': click.style('[ ]', fg='bright_black'),
    None: click.style('[ ]', fg='bright_black'),  # Not in db
}

DIFFICULTY_SHORT = {
    'Easy': click.style('E', fg='green'),
    'Medium': click.style('M', fg='yellow'),
    'Hard': click.style('H', fg='red'),
}


def _get_status_map(problems, repo):
    """
    Get status map for a list of problems from the database.

    Returns the best status across all languages for each problem.
    Priority: passed > failed > skipped > ungraded
    """
    status_map = {}
    if repo.is_initialized():
        with DatabaseManager(repo.get_db_path()) as db:
            for problem in problems:
                # Check all languages for this problem
                statuses = []
                for lang in ['python', 'java', 'cpp']:
                    db_problem = db.get_problem('leetcode', problem.id, lang)
                    if db_problem:
                        statuses.append(db_problem.get('test_status'))

                if statuses:
                    # Return best status (passed > failed > skipped > ungraded)
                    if 'passed' in statuses:
                        status_map[problem.id] = 'passed'
                    elif 'failed' in statuses:
                        status_map[problem.id] = 'failed'
                    elif 'skipped' in statuses:
                        status_map[problem.id] = 'skipped'
                    else:
                        status_map[problem.id] = statuses[0]  # ungraded/untested
    return status_map


def _display_page(all_problems, page, per_page, repo):
    """Display a single page of problems."""
    total = len(all_problems)
    total_pages = (total + per_page - 1) // per_page
    page = max(1, min(page, total_pages))  # Clamp to valid range

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    page_problems = all_problems[start_idx:end_idx]

    # Get database status for problems on this page
    status_map = _get_status_map(page_problems, repo)

    # Display header
    click.echo(f"\nLeetCode Problems (Page {page}/{total_pages}, {total} total)\n")
    click.echo(f"{'ID':>5}  {'St':3}  {'D'}  Title")
    click.echo("-" * 60)

    # Display results
    for problem in page_problems:
        status = status_map.get(problem.id)
        status_icon = STATUS_ICONS.get(status, STATUS_ICONS[None])
        diff_icon = DIFFICULTY_SHORT.get(problem.difficulty, '?')

        # Premium marker
        title = problem.title
        if problem.paid_only:
            title += click.style(' $', fg='cyan')

        click.echo(f"{problem.id:>5}  {status_icon}  {diff_icon}  {title}")

    # Footer with pagination info
    click.echo("-" * 60)
    click.echo(f"Page {page}/{total_pages} | Showing {start_idx + 1}-{end_idx} of {total}")

    return page, total_pages


def _interactive_loop(all_problems, start_page, per_page, repo):
    """Run interactive pagination loop."""
    total_pages = (len(all_problems) + per_page - 1) // per_page
    current_page = start_page

    while True:
        current_page, total_pages = _display_page(all_problems, current_page, per_page, repo)

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
@click.option(
    '--difficulty', '-d',
    type=click.Choice(['easy', 'medium', 'hard', '1', '2', '3'], case_sensitive=False),
    help='Filter by difficulty (easy/1, medium/2, hard/3)'
)
@click.option(
    '--tag', '-t',
    multiple=True,
    help='Filter by algorithm tag (can be used multiple times)'
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
def query(ctx, difficulty: str, tag: tuple, page: int, per_page: int, list_tags: bool):
    """
    Search LeetCode problems with local status.

    Status indicators:
      [P] Passed    [F] Failed    [S] Skipped    [ ] Not graded/fetched

    Navigation (after results display):
      n = next page    p = prev page    # = jump to page    q = quit

    Examples:
      dojo leetcode query                          # Browse all problems
      dojo leetcode query -d easy                  # Easy problems only
      dojo leetcode query -t array                 # Array problems
      dojo leetcode query -d medium -t dp -n 50   # 50 per page
      dojo leetcode query --list-tags              # Show all tags
    """
    logger = get_logger()
    client = LeetCodeClient()

    # Handle --list-tags
    if list_tags:
        logger.info("Fetching available tags...")
        tags = client.get_available_tags()
        if tags:
            click.echo(f"Available tags ({len(tags)}):")
            for t in tags:
                click.echo(f"  {t}")
        else:
            logger.warning("No tags found")
        return

    # Convert difficulty to int
    difficulty_int = None
    if difficulty:
        difficulty_int = DIFFICULTY_MAP.get(difficulty.lower())

    # Convert tag tuple to list
    tags_list = list(tag) if tag else None

    # Query problems from LeetCode (once)
    logger.info("Fetching problems from LeetCode...")
    all_problems = client.query_problems(
        difficulty=difficulty_int,
        tags=tags_list
    )

    if not all_problems:
        logger.warning("No problems found matching your criteria")
        return

    # Get repository for status lookups
    repo = DojoRepository()

    # Enter interactive pagination loop
    _interactive_loop(all_problems, page, per_page, repo)
