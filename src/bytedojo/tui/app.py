"""
ByteDojo TUI Application.

Main Textual application for the ByteDojo terminal user interface.
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container


class DojoApp(App):
    """ByteDojo TUI Application."""

    TITLE = "ByteDojo"
    SUB_TITLE = "LeetCode Practice Tracker"

    CSS = """
    Screen {
        background: $surface;
    }

    #welcome {
        width: 100%;
        height: auto;
        padding: 2 4;
        text-align: center;
    }

    #welcome Static {
        text-align: center;
    }

    .title {
        text-style: bold;
        color: $accent;
    }

    .subtitle {
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Container(
            Static("Welcome to ByteDojo", classes="title"),
            Static("Your LeetCode practice companion", classes="subtitle"),
            Static(""),
            Static("Press ? for help or q to quit"),
            id="welcome"
        )
        yield Footer()

    def action_help(self) -> None:
        """Show help information."""
        self.notify("Help panel coming soon!", title="Help")
