"""
Main screen for the ByteDojo TUI.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container

from bytedojo.tui.views.dashboard import DashboardView
from bytedojo.tui.views.command_pages import (
    FetchPage, RunPage, GradePage, PickPage,
    QueryPage, ReviewPage, StatsPage, SettingsPage,
    BasePage
)


class MainScreen(Screen):
    """Main screen with menu navigation."""

    CSS = """
    MainScreen {
        background: $surface;
    }

    #content-area {
        width: 100%;
        height: 1fr;
    }

    .page {
        width: 100%;
        height: 100%;
    }

    .page.hidden {
        display: none;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "back", "Back"),
        ("f", "go_fetch", "Fetch"),
        ("r", "go_run", "Run"),
        ("g", "go_grade", "Grade"),
        ("p", "go_pick", "Pick"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="content-area"):
            yield DashboardView(id="page-menu", classes="page")
            yield FetchPage(id="page-fetch", classes="page hidden")
            yield RunPage(id="page-run", classes="page hidden")
            yield GradePage(id="page-grade", classes="page hidden")
            yield PickPage(id="page-pick", classes="page hidden")
            yield QueryPage(id="page-query", classes="page hidden")
            yield ReviewPage(id="page-review", classes="page hidden")
            yield StatsPage(id="page-stats", classes="page hidden")
            yield SettingsPage(id="page-settings", classes="page hidden")

        yield Footer()

    def _show_page(self, page_id: str) -> None:
        """Show a specific page, hide others."""
        for page in self.query(".page"):
            page.add_class("hidden")

        try:
            target = self.query_one(f"#page-{page_id}")
            target.remove_class("hidden")
        except Exception:
            # Fall back to menu
            self.query_one("#page-menu").remove_class("hidden")

    def _go_back(self) -> None:
        """Return to the menu."""
        self._show_page("menu")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_back(self) -> None:
        """Go back to menu."""
        self._go_back()

    def action_go_fetch(self) -> None:
        """Go to fetch page."""
        self._show_page("fetch")

    def action_go_run(self) -> None:
        """Go to run page."""
        self._show_page("run")

    def action_go_grade(self) -> None:
        """Go to grade page."""
        self._show_page("grade")

    def action_go_pick(self) -> None:
        """Go to pick page."""
        self._show_page("pick")

    def on_dashboard_view_command_selected(self, event: DashboardView.CommandSelected) -> None:
        """Handle command selection from menu."""
        self._show_page(event.command)

    def on_base_page_go_back(self, event: BasePage.GoBack) -> None:
        """Handle back navigation from any page."""
        self._go_back()
