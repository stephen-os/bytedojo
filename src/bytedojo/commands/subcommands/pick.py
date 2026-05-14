"""
pick - Pick a random problem.
"""

import click
from pathlib import Path

from bytedojo.core.repository import Repository
from bytedojo.core.logger import get_logger
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.services import PickService, PickScope


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

    repo = Repository.find(Path.cwd())
    if repo is None:
        raise click.ClickException("Not inside a .dojo repository. Please run 'dojo init' first.")

    # Resolve difficulty (None / "" -> NONE sentinel; unrecognized -> NONE + error)
    diff = ProblemDifficulty.from_string(difficulty) if difficulty else ProblemDifficulty.NONE
    if difficulty and diff == ProblemDifficulty.NONE:
        raise click.ClickException(f"Unknown difficulty: {difficulty}")

    # Resolve tags (drop UNKNOWN with a warning; fail if none are valid)
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

    # Resolve scope
    pick_scope = {
        'all': PickScope.ALL,
        'solved': PickScope.SOLVED,
    }.get(scope, PickScope.UNSOLVED)

    # Pick
    service = PickService()
    result = service.pick(repo, difficulty=diff, tags=parsed_tags, scope=pick_scope)

    # Display
    if result.total_count == 0:
        click.echo("No problems found matching your criteria.")
        return

    if not result.has_pick:
        if result.scope == PickScope.SOLVED:
            click.echo("No registered problems matching your criteria.")
        else:
            click.echo("All matching problems already registered.")
            click.echo(f"  total: {result.total_count}, registered: {result.registered_count}")
        return

    picked = result.picked
    label = result.scope.display_label

    click.echo(f"Picking from {result.pool_size} {label} problem(s)")
    click.echo(f"  #{picked.id} {picked.title} [{picked.difficulty.value}]")

    if picked.tags:
        tags_display = ", ".join(t.value for t in picked.tags[:5])
        if len(picked.tags) > 5:
            tags_display += f" (+{len(picked.tags) - 5} more)"
        click.echo(f"  tags: {tags_display}")

    click.echo("")
    click.echo(
        f"Done: pool={result.pool_size} ({label}), "
        f"registered={result.registered_count}, total={result.total_count}"
    )
    click.echo(f"Fetch with: dojo fetch {picked.id}")
