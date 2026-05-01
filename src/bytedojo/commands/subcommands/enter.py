"""
Enter command - Launch the ByteDojo TUI environment.
"""

import click


@click.command()
def enter():
    """
    Enter the ByteDojo TUI environment.

    Launches an interactive terminal user interface for managing
    your LeetCode problems, reviews, and progress. If no dojo repository
    exists, you'll be guided through initialization.

    Examples:
      dojo enter                 # Launch the TUI
    """
    # Import here to avoid loading Textual unless needed
    from bytedojo.tui import DojoApp

    app = DojoApp()
    app.run()
