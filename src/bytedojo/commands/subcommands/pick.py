"""
pick - Pick a random problem.
"""

import click

from bytedojo.commands._resolve import require_repo
from bytedojo.commands.ui import dim
from bytedojo.commands.ui.renderers import (
    render_fetch_results,
    render_pick,
    render_pick_empty,
)
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_tag import ProblemTag
from bytedojo.core.repository import Repository
from bytedojo.core.logger import get_logger
from bytedojo.core.settings import SettingsManager
from bytedojo.services import FetchService, PickService, PickScope


@click.command()
@click.option(
    "--difficulty",
    "-d",
    type=click.Choice(["easy", "medium", "hard", "1", "2", "3"], case_sensitive=False),
    help="Filter by difficulty (easy/1, medium/2, hard/3)",
)
@click.option(
    "--tag",
    "-t",
    "tags",
    multiple=True,
    help="Filter by algorithm tag (can be used multiple times)",
)
@click.option(
    "--all",
    "-a",
    "scope",
    flag_value="all",
    help="Pick from all problems (ignore registration status)",
)
@click.option(
    "--solved",
    "-s",
    "scope",
    flag_value="solved",
    help="Pick from registered/solved problems only",
)
@click.option(
    "--fetch",
    "fetch_now",
    is_flag=True,
    help="Fetch the picked problem immediately (non-interactive)",
)
@click.pass_obj
def pick(ctx, difficulty: str | None, tags: tuple, scope: str | None, fetch_now: bool):
    """
    Pick a random problem.

    By default, selects from problems not yet registered and asks
    whether to fetch it, pick again, or quit. Use --fetch to pick and
    fetch in one step.

    Examples:
      dojo pick                    # Random unsolved problem (interactive)
      dojo pick -d easy            # Random easy problem
      dojo pick -t array           # Random array problem
      dojo pick --fetch            # Pick and fetch without prompting
      dojo pick --all              # Random from all problems
      dojo pick --solved           # Random from already registered
    """
    logger = get_logger()
    logger.debug(
        f"pick: difficulty={difficulty} tags={tags} scope={scope} " f"fetch={fetch_now}"
    )

    repo = require_repo()

    # Resolve difficulty (None / "" -> NONE sentinel; unrecognized -> NONE + error)
    diff = (
        ProblemDifficulty.from_string(difficulty)
        if difficulty
        else ProblemDifficulty.NONE
    )
    if difficulty and diff == ProblemDifficulty.NONE:
        raise click.UsageError(f"Unknown difficulty: {difficulty}")

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
            raise click.UsageError(f"No valid tags found in: {list(tags)}")

    pick_scope = {
        "all": PickScope.ALL,
        "solved": PickScope.SOLVED,
    }.get(scope, PickScope.UNSOLVED)

    service = PickService()

    while True:
        result = service.pick(repo, difficulty=diff, tags=parsed_tags, scope=pick_scope)

        if not result.has_pick:
            render_pick_empty(result)
            return

        render_pick(result)

        if fetch_now:
            _fetch_picked(repo, result.picked.id)
            return

        choice = (
            click.prompt(
                "",
                prompt_suffix="  [f]etch / [r]epick / [q]uit: ",
                default="q",
                show_default=False,
            )
            .strip()
            .lower()
        )

        if choice in ("f", "fetch"):
            _fetch_picked(repo, result.picked.id)
            return
        if choice in ("r", "repick"):
            continue
        click.echo(f"  {dim(f'dojo fetch {result.picked.id}')}")
        return


def _fetch_picked(repo: Repository, problem_id: int) -> None:
    """Fetch the picked problem in the configured default language."""
    language = CodeLanguage.from_string(
        SettingsManager(repo.dojo_dir).load().default_language
    )
    batch = FetchService().fetch_and_place_batch(repo, [problem_id], language)
    render_fetch_results(batch)
