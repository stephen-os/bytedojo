"""
ByteDojo TUI Application.

Main Textual application for the ByteDojo terminal user interface.
"""

from textual.app import App

from bytedojo.core.repository import Repository
from bytedojo.tui.screens import InitScreen, MainScreen
from bytedojo.tui.theme import THEME_CSS


class DojoApp(App):
    """ByteDojo TUI Application."""

    TITLE = "ByteDojo"
    SUB_TITLE = "LeetCode Practice Tracker"

    CSS = THEME_CSS

    SCREENS = {
        "init": InitScreen,
        "main": MainScreen,
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Called when the app is mounted. Determine which screen to show."""
        repo = Repository(Path.cwd())

        if repo.is_initialized:
            self.push_screen("main")
        else:
            self.push_screen("init")
