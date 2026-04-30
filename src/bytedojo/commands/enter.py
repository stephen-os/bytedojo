"""
Enter command - Launch the ByteDojo TUI environment.
"""

import click

from bytedojo.commands.utils import get_initialized_repo


@click.command()
def enter():
    """
    Enter the ByteDojo TUI environment.

    Launches an interactive terminal user interface for managing
    your LeetCode problems, reviews, and progress.

    Examples:
      dojo enter                 # Launch the TUI
    """
    # Ensure repo is initialized
    get_initialized_repo()

    # Import here to avoid loading Textual unless needed
    from bytedojo.tui import DojoApp

    app = DojoApp()
    app.run()
