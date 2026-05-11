"""
pick - Pick a random problem.
"""

import random
import click
from pathlib import Path

from bytedojo.core import problem_service
from bytedojo.core.repository import Repository
from bytedojo.core.logger import get_logger

from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag


# Define pick command
@click.command()

# Options

# Difficulty filter
@click.option('--difficulty', '-d',
              type=click.Choice(['easy', 'medium', 'hard', '1', '2', '3'], case_sensitive=False),
              help='Filter by difficulty (easy/1, medium/2, hard/3)')

# Tag filter (multiple allowed)
@click.option('--tag', '-t', 'tags', multiple=True,
              help='Filter by algorithm tag (can be used multiple times)')

# Scope flags (mutually exclusive)
@click.option('--all', '-a', 'scope', flag_value='all',
              help='Pick from all problems (ignore registration status)')
@click.option('--solved', '-s', 'scope', flag_value='solved',
              help='Pick from registered/solved problems only')

@click.pass_obj
def pick(ctx, difficulty: str | None, tags: tuple, scope: str | None):
    """
    Pick a random problem.

    By default, selects from problems not yet registered in your .dojo database.

    Scopes:
      (default)    Pick from unsolved problems only
      --all        Pick from all problems (ignore registration status)
      --solved     Pick from registered/solved problems only

    Examples:
      dojo pick                    # Random unsolved problem
      dojo pick -d easy            # Random easy problem
      dojo pick -t array           # Random array problem
      dojo pick -d medium -t tree  # Random medium tree problem
      dojo pick --all              # Random from all problems
      dojo pick --solved           # Random from already registered
    """
    logger = get_logger()
    logger.debug(f"pick: difficulty={difficulty} tags={tags} scope={scope}")

    # Resolve repo
    repo = Repository.open(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Resolve difficulty
    if difficulty is None:
        diff = ProblemDifficulty.NONE
    else:
        diff = ProblemDifficulty.from_string(difficulty)
        if diff == ProblemDifficulty.NONE:
            raise click.ClickException(f"Unknown difficulty: {difficulty}")
    logger.debug(f"pick: resolved difficulty={diff}")

    # Resolve tags
    parsed_tags = None
    if tags:
        parsed_tags = []
        for tag_str in tags:
            tag = ProblemTag.from_string(tag_str)
            if tag == ProblemTag.UNKNOWN:
                logger.warning(f"pick: unknown tag '{tag_str}', skipping")
                continue
            parsed_tags.append(tag)
        if not parsed_tags:
            raise click.ClickException(f"No valid tags found in: {list(tags)}")
    logger.debug(f"pick: resolved tags={parsed_tags}")

    # Query all matching problems from local index
    all_problems = problem_service.query_problems(
        difficulty=diff,
        tags=parsed_tags
    )

    if not all_problems:
        click.echo("No problems found matching your criteria.")
        logger.warning("pick: no problems found matching criteria")
        return

    # Get already-registered problem IDs from repo
    registered_problems = repo.get_registered_problems()
    registered_ids = {p["problem_id"] for p in registered_problems}
    logger.debug(f"pick: {len(registered_ids)} problems already registered")

    # Filter based on scope
    registered_count = len([p for p in all_problems if p.id in registered_ids])

    if scope == 'all':
        # Pick from all problems
        candidates = all_problems
        scope_label = "all"
    elif scope == 'solved':
        # Pick from registered only
        candidates = [p for p in all_problems if p.id in registered_ids]
        scope_label = "registered"
    else:
        # Default: pick from unsolved only
        candidates = [p for p in all_problems if p.id not in registered_ids]
        scope_label = "unsolved"

    if not candidates:
        if scope == 'solved':
            click.echo("No registered problems matching your criteria.")
            logger.info("pick: no registered problems matching criteria")
        else:
            click.echo("All matching problems already registered.")
            click.echo(f"  total: {len(all_problems)}, registered: {registered_count}")
            logger.info("pick: all matching problems already registered")
        return

    # Pick a random problem
    picked = random.choice(candidates)
    logger.info(f"pick: selected #{picked.id} {picked.slug} (scope={scope_label})")

    # Display result
    click.echo(f"Picking from {len(candidates)} {scope_label} problem(s)")
    click.echo(f"  #{picked.id} {picked.title} [{picked.difficulty.value}]")

    if picked.tags:
        tags_display = ", ".join(t.value for t in picked.tags[:5])
        if len(picked.tags) > 5:
            tags_display += f" (+{len(picked.tags) - 5} more)"
        click.echo(f"  tags: {tags_display}")

    click.echo("")
    click.echo(f"Done: pool={len(candidates)} ({scope_label}), registered={registered_count}, total={len(all_problems)}")
    click.echo(f"Fetch with: dojo fetch {picked.id}")
    logger.info(f"pick: complete — picked #{picked.id} from {scope_label}")
