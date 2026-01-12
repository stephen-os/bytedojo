"""
Codeforces query command.
"""

import click

from bytedojo.core.logger import get_logger
from bytedojo.core.codeforces import CodeforcesClient
from bytedojo.core.repository import DojoRepository
from bytedojo.core.database import DatabaseManager


# Rating ranges for difficulty levels
DIFFICULTY_RATINGS = {
    'easy': (0, 1199),
    'medium': (1200, 1599),
    'hard': (1600, 2099),
    'expert': (2100, 3500),
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


def _get_rating_color(rating):
    """Get color based on Codeforces rating."""
    if rating is None:
        return 'white'
    elif rating < 1200:
        return 'bright_black'  # Gray (newbie)
    elif rating < 1400:
        return 'green'  # Green
    elif rating < 1600:
        return 'cyan'  # Cyan
    elif rating < 1900:
        return 'blue'  # Blue
    elif rating < 2100:
        return 'magenta'  # Purple
    elif rating < 2400:
        return 'yellow'  # Orange/Yellow
    else:
        return 'red'  # Red


def _get_status_map(problems, repo):
    """Get status map for a list of problems from the database."""
    status_map = {}
    if repo.is_initialized():
        with DatabaseManager(repo.get_db_path()) as db:
            for problem in problems:
                db_problem = db.get_problem('codeforces', problem.problem_id)
                if db_problem:
                    status_map[problem.problem_id] = db_problem.get('test_status')
    return status_map


def _display_page(all_problems, page, per_page, repo):
    """Display a single page of problems."""
    total = len(all_problems)
    total_pages = (total + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    page_problems = all_problems[start_idx:end_idx]

    # Get database status for problems on this page
    status_map = _get_status_map(page_problems, repo)

    # Display header
    click.echo(f"\nCodeforces Problems (Page {page}/{total_pages}, {total} total)\n")
    click.echo(f"{'ID':>7}  {'St':3}  {'Rating':>6}  Name")
    click.echo("-" * 70)

    # Display results
    for problem in page_problems:
        status = status_map.get(problem.problem_id)
        status_icon = STATUS_ICONS.get(status, STATUS_ICONS[None])

        rating_str = str(problem.rating) if problem.rating else "N/A"
        rating_color = _get_rating_color(problem.rating)
        rating_styled = click.style(f"{rating_str:>6}", fg=rating_color)

        click.echo(f"{problem.problem_id:>7}  {status_icon}  {rating_styled}  {problem.name}")

    # Footer
    click.echo("-" * 70)
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
    type=click.Choice(['easy', 'medium', 'hard', 'expert'], case_sensitive=False),
    help='Filter by difficulty level'
)
@click.option(
    '--rating-min', '-r',
    type=int,
    help='Minimum rating (e.g., 800)'
)
@click.option(
    '--rating-max', '-R',
    type=int,
    help='Maximum rating (e.g., 1500)'
)
@click.option(
    '--tag', '-t',
    multiple=True,
    help='Filter by tag (can be used multiple times)'
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
def query(ctx, difficulty: str, rating_min: int, rating_max: int, tag: tuple,
          page: int, per_page: int, list_tags: bool):
    """
    Search Codeforces problems with local status.

    Status indicators:
      [P] Passed    [F] Failed    [S] Skipped    [ ] Not graded/fetched

    Navigation (after results display):
      n = next page    p = prev page    # = jump to page    q = quit

    Examples:
      dojo codeforces query                      # Browse all problems
      dojo codeforces query -d easy              # Easy problems (< 1200)
      dojo codeforces query -r 1200 -R 1600      # Rating range
      dojo codeforces query -t dp -t graphs      # By tags
      dojo codeforces query --list-tags          # Show all tags
    """
    logger = get_logger()
    client = CodeforcesClient()

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

    # Convert difficulty to rating range
    if difficulty:
        diff_range = DIFFICULTY_RATINGS.get(difficulty.lower())
        if diff_range:
            rating_min = rating_min or diff_range[0]
            rating_max = rating_max or diff_range[1]

    # Convert tag tuple to list
    tags_list = list(tag) if tag else None

    # Query problems from Codeforces
    logger.info("Fetching problems from Codeforces...")
    all_problems = client.query_problems(
        rating_min=rating_min,
        rating_max=rating_max,
        tags=tags_list
    )

    if not all_problems:
        logger.warning("No problems found matching your criteria")
        return

    # Get repository for status lookups
    repo = DojoRepository()

    # Enter interactive pagination loop
    _interactive_loop(all_problems, page, per_page, repo)
