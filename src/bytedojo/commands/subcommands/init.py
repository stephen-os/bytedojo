"""
Init command - Creates a .dojo directory.
"""

import click
from pathlib import Path

from bytedojo.core.repository import Repository

@click.command()
@click.option('--path', '-p', type=click.Path(path_type=Path), default=None,
              help='Directory to initialize (defaults to current directory)')
@click.option('--force', is_flag=True, help='Reinitialize even if .dojo already exists')
@click.pass_obj
def init(ctx, path: Path, force: bool):
    """
    Initialize a ByteDojo repository.

    Creates a .dojo directory with:
    - db.sqlite for tracking problems and stats
    - settings.json for configuration
    - .gitignore to exclude build artifacts
    """
    target = path if path is not None else Path.cwd()
    if Repository.create(path=target, force=force) is not None:
        click.secho(f"Repository initialized at {target}.", fg="green")
    else:
        click.secho(f"Failed to initialize repository at {target}.", fg="red")
        raise SystemExit(1)
