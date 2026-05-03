"""
Dashboard view - Main menu for navigating commands.
"""

from textual.app import ComposeResult
from textual.widgets import Static, ListView, ListItem, Label
from textual.containers import Container
from textual.widget import Widget
from textual.message import Message


class MenuItem(ListItem):
    """A menu item representing a command."""

    def __init__(self, command: str, description: str, shortcut: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.command = command
        self.description = description
        self.shortcut = shortcut

    def compose(self) -> ComposeResult:
        shortcut_text = f"[{self.shortcut}]" if self.shortcut else ""
        yield Label(f"{self.command:<12} {self.description:<40} {shortcut_text}")


class DashboardView(Widget):
    """Main menu dashboard."""

    DEFAULT_CSS = """
    DashboardView {
        width: 100%;
        height: 100%;
    }

    #menu-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    #menu-title {
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }

    #menu-list {
        width: 100%;
        height: 1fr;
    }

    #menu-list > ListItem {
        padding: 0 1;
    }

    #menu-list > ListItem:hover {
        background: $surface-lighten-1;
    }

    #menu-list:focus > ListItem.--highlight {
        background: $primary;
    }
    """

    class CommandSelected(Message):
        """Message when a command is selected."""
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="menu-container"):
            yield Static("Select a command:", id="menu-title")
            yield ListView(
                MenuItem("fetch", "Fetch problems from LeetCode", "f"),
                MenuItem("run", "Run solution against test cases", "r"),
                MenuItem("grade", "Grade a problem pass/fail", "g"),
                MenuItem("pick", "Pick a random problem", "p"),
                MenuItem("query", "Search and filter problems", ""),
                MenuItem("review", "Start a review session", ""),
                MenuItem("stats", "View your statistics", ""),
                MenuItem("settings", "Configure preferences", ""),
                id="menu-list"
            )

    def on_mount(self) -> None:
        """Focus the menu on mount."""
        self.query_one("#menu-list", ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle menu item selection."""
        if isinstance(event.item, MenuItem):
            self.post_message(self.CommandSelected(event.item.command))

    def refresh_stats(self) -> None:
        """Placeholder for compatibility."""
        pass
