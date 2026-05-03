"""
Problems view - Browse and manage problems.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static
from textual.widget import Widget
from textual.message import Message

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.tui.widgets.problem_table import ProblemTable
from bytedojo.tui.widgets.filter_bar import FilterBar


class ProblemsView(Widget):
    """View for browsing and managing problems."""

    DEFAULT_CSS = """
    ProblemsView {
        width: 100%;
        height: 100%;
        background: #0d1117;
    }

    ProblemsView .view-title {
        text-style: bold;
        color: #6a2a8a;
        text-align: center;
        padding: 1 0;
        width: 100%;
    }

    ProblemsView .view-divider {
        color: #21262d;
        text-align: center;
        width: 100%;
    }

    ProblemsView #problems-container {
        width: 100%;
        height: 1fr;
        padding: 0 2;
    }

    ProblemsView #action-hints {
        dock: bottom;
        width: 100%;
        height: 1;
        background: #161b22;
        color: #8b949e;
        padding: 0 2;
    }
    """

    BINDINGS = [
        ("slash", "focus_search", "Search"),
        ("f", "fetch_selected", "Fetch"),
        ("r", "run_selected", "Run"),
        ("g", "grade_selected", "Grade"),
        ("v", "view_selected", "View"),
        ("left", "prev_page", "Previous Page"),
        ("right", "next_page", "Next Page"),
        ("h", "prev_page", "Previous Page"),
        ("l", "next_page", "Next Page"),
    ]

    class ProblemAction(Message):
        """Message when an action is requested on a problem."""
        def __init__(self, action: str, problem: dict) -> None:
            self.action = action
            self.problem = problem
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._all_problems: list = []
        self._filtered_problems: list = []
        self._current_page: int = 1
        self._per_page: int = 15
        self._selected_problem: dict | None = None
        self._current_filters: dict = {}

    def compose(self) -> ComposeResult:
        yield Static("═" * 60, classes="view-divider")
        yield Static("PROBLEMS", classes="view-title")
        yield Static("═" * 60, classes="view-divider")

        yield FilterBar(id="filter-bar")

        with Container(id="problems-container"):
            yield ProblemTable(id="problem-table")

        yield Static(
            "[/] Search  [F] Fetch  [R] Run  [G] Grade  [Enter] View  [←→] Pages",
            id="action-hints"
        )

    def on_mount(self) -> None:
        """Load problems when mounted."""
        self._load_problems()

    def _load_problems(self) -> None:
        """Load problems from database."""
        repo = Repository(Path.cwd())

        if not repo.is_initialized:
            self._all_problems = []
            self._filtered_problems = []
            self._update_table()
            return

        with DatabaseManager(repo.db_path) as db:
            self._all_problems = db.list_problems()

        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply current filters to problems."""
        filters = self._current_filters
        search = filters.get("search", "").lower()
        status_filters = filters.get("status", [])
        difficulty_filters = filters.get("difficulty", [])

        filtered = self._all_problems

        # Apply search filter
        if search:
            filtered = [
                p for p in filtered
                if search in p.get('title', '').lower()
                or search in str(p.get('problem_id', '')).lower()
                or search in p.get('description', '').lower()
            ]

        # Apply status filter
        if status_filters:
            status_map = {
                "passed": ["passed"],
                "failed": ["failed"],
                "fetched": ["ungraded", "passed", "failed", "skipped"],
                "ungraded": ["ungraded"],
            }
            allowed_statuses = set()
            for sf in status_filters:
                allowed_statuses.update(status_map.get(sf, [sf]))

            filtered = [
                p for p in filtered
                if p.get('test_status', 'ungraded') in allowed_statuses
            ]

        # Apply difficulty filter
        if difficulty_filters:
            filtered = [
                p for p in filtered
                if p.get('difficulty', 'Unknown') in difficulty_filters
            ]

        self._filtered_problems = filtered
        self._current_page = 1
        self._update_table()

    def _update_table(self) -> None:
        """Update the problem table with current page of filtered problems."""
        table = self.query_one(ProblemTable)

        start = (self._current_page - 1) * self._per_page
        end = start + self._per_page
        page_problems = self._filtered_problems[start:end]

        table.set_problems(
            problems=page_problems,
            total=len(self._filtered_problems),
            page=self._current_page
        )

    def on_filter_bar_filters_changed(self, event: FilterBar.FiltersChanged) -> None:
        """Handle filter changes."""
        self._current_filters = event.filters
        self._apply_filters()

    def on_filter_bar_search_changed(self, event: FilterBar.SearchChanged) -> None:
        """Handle search changes."""
        self._current_filters["search"] = event.query
        self._apply_filters()

    def on_problem_table_problem_selected(self, event: ProblemTable.ProblemSelected) -> None:
        """Handle problem selection."""
        self._selected_problem = event.problem
        self.post_message(self.ProblemAction("view", event.problem))

    def on_problem_table_page_changed(self, event: ProblemTable.PageChanged) -> None:
        """Handle page changes from table."""
        self._current_page = event.page
        self._update_table()

    def action_focus_search(self) -> None:
        """Focus the search input."""
        filter_bar = self.query_one(FilterBar)
        filter_bar.focus_search()

    def action_prev_page(self) -> None:
        """Go to previous page."""
        if self._current_page > 1:
            self._current_page -= 1
            self._update_table()

    def action_next_page(self) -> None:
        """Go to next page."""
        total_pages = max(1, (len(self._filtered_problems) + self._per_page - 1) // self._per_page)
        if self._current_page < total_pages:
            self._current_page += 1
            self._update_table()

    def action_fetch_selected(self) -> None:
        """Fetch the selected problem."""
        if self._selected_problem:
            self.post_message(self.ProblemAction("fetch", self._selected_problem))
        else:
            self.notify("Select a problem first", title="Fetch")

    def action_run_selected(self) -> None:
        """Run the selected problem."""
        if self._selected_problem:
            self.post_message(self.ProblemAction("run", self._selected_problem))
        else:
            self.notify("Select a problem first", title="Run")

    def action_grade_selected(self) -> None:
        """Grade the selected problem."""
        if self._selected_problem:
            self.post_message(self.ProblemAction("grade", self._selected_problem))
        else:
            self.notify("Select a problem first", title="Grade")

    def action_view_selected(self) -> None:
        """View the selected problem details."""
        if self._selected_problem:
            self.post_message(self.ProblemAction("view", self._selected_problem))
        else:
            self.notify("Select a problem first", title="View")

    def refresh_problems(self) -> None:
        """Refresh the problems list."""
        self._load_problems()
