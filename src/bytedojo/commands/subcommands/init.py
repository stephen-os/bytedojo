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
    if Repository.create(path=Path.cwd(), force=force) is not None:
        click.secho("Repository initialized successfully.", fg="green")
    else:
        click.secho("Failed to initialize repository.", fg="red")
        raise SystemExit(1)
