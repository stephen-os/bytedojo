"""
Filter bar widget for filtering problems.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Input, Button
from textual.widget import Widget
from textual.message import Message
from textual.reactive import reactive


class FilterButton(Static):
    """A toggleable filter button."""

    DEFAULT_CSS = """
    FilterButton {
        width: auto;
        height: 1;
        padding: 0 1;
        margin: 0 1;
        background: #21262d;
        color: #8b949e;
        text-style: bold;
    }

    FilterButton:hover {
        background: #30363d;
        color: #e6edf3;
    }

    FilterButton.active {
        background: #6a2a8a;
        color: #e6edf3;
    }
    """

    def __init__(self, label: str, filter_id: str, **kwargs) -> None:
        super().__init__(label, **kwargs)
        self.filter_id = filter_id

    def on_click(self) -> None:
        """Toggle active state and notify parent."""
        self.toggle_class("active")
        self.post_message(FilterBar.FilterToggled(self.filter_id, self.has_class("active")))


class FilterBar(Widget):
    """Bar with search and filter controls."""

    DEFAULT_CSS = """
    FilterBar {
        width: 100%;
        height: auto;
        background: #161b22;
        padding: 1 2;
    }

    FilterBar #search-row {
        width: 100%;
        height: 3;
        margin-bottom: 1;
    }

    FilterBar #search-input {
        width: 1fr;
        background: #0d1117;
        border: tall #21262d;
        color: #e6edf3;
    }

    FilterBar #search-input:focus {
        border: tall #6a2a8a;
    }

    FilterBar #filter-row {
        width: 100%;
        height: 1;
    }

    FilterBar .filter-group {
        width: auto;
        height: 1;
        margin-right: 2;
    }

    FilterBar .filter-label {
        width: auto;
        color: #8b949e;
        margin-right: 1;
    }

    FilterBar .status-filters {
        width: auto;
    }

    FilterBar .difficulty-filters {
        width: auto;
    }

    /* Difficulty colors */
    FilterBar FilterButton.easy.active {
        background: #58a6ff;
    }

    FilterBar FilterButton.medium.active {
        background: #f06060;
    }

    FilterBar FilterButton.hard.active {
        background: #c43a3a;
    }

    /* Status colors */
    FilterBar FilterButton.passed.active {
        background: #58a6ff;
    }

    FilterBar FilterButton.failed.active {
        background: #c43a3a;
    }

    FilterBar FilterButton.ungraded.active {
        background: #8b949e;
    }
    """

    search_query: reactive[str] = reactive("")

    class FilterToggled(Message):
        """Message when a filter is toggled."""
        def __init__(self, filter_id: str, active: bool) -> None:
            self.filter_id = filter_id
            self.active = active
            super().__init__()

    class SearchChanged(Message):
        """Message when search query changes."""
        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    class FiltersChanged(Message):
        """Message when any filter changes."""
        def __init__(self, filters: dict) -> None:
            self.filters = filters
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._active_filters: dict = {
            "status": set(),
            "difficulty": set(),
        }

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-row"):
            yield Input(placeholder="Search problems... (press / to focus)", id="search-input")

        with Horizontal(id="filter-row"):
            # Status filters
            with Horizontal(classes="filter-group status-filters"):
                yield Static("Status:", classes="filter-label")
                yield FilterButton("All", "status-all", classes="active")
                yield FilterButton("Fetched", "status-fetched")
                yield FilterButton("Passed", "status-passed", classes="passed")
                yield FilterButton("Failed", "status-failed", classes="failed")

            # Difficulty filters
            with Horizontal(classes="filter-group difficulty-filters"):
                yield Static("Difficulty:", classes="filter-label")
                yield FilterButton("E", "diff-easy", classes="easy")
                yield FilterButton("M", "diff-medium", classes="medium")
                yield FilterButton("H", "diff-hard", classes="hard")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self.post_message(self.SearchChanged(event.value))
            self._emit_filters_changed()

    def on_filter_bar_filter_toggled(self, event: FilterToggled) -> None:
        """Handle filter button toggles."""
        filter_id = event.filter_id

        # Handle status filters
        if filter_id.startswith("status-"):
            status = filter_id.replace("status-", "")
            if status == "all":
                # Clear other status filters when "All" is selected
                self._active_filters["status"].clear()
                for btn in self.query("FilterButton.passed, FilterButton.failed, FilterButton.ungraded"):
                    btn.remove_class("active")
                self.query_one("#filter-row FilterButton", FilterButton).add_class("active")
            else:
                # Remove "All" when specific filter is selected
                all_btn = self.query("FilterButton").first()
                if all_btn:
                    all_btn.remove_class("active")

                if event.active:
                    self._active_filters["status"].add(status)
                else:
                    self._active_filters["status"].discard(status)

        # Handle difficulty filters
        elif filter_id.startswith("diff-"):
            diff = filter_id.replace("diff-", "").title()
            if event.active:
                self._active_filters["difficulty"].add(diff)
            else:
                self._active_filters["difficulty"].discard(diff)

        self._emit_filters_changed()

    def _emit_filters_changed(self) -> None:
        """Emit the current filter state."""
        filters = {
            "search": self.search_query,
            "status": list(self._active_filters["status"]),
            "difficulty": list(self._active_filters["difficulty"]),
        }
        self.post_message(self.FiltersChanged(filters))

    def get_filters(self) -> dict:
        """Get current filter state."""
        return {
            "search": self.search_query,
            "status": list(self._active_filters["status"]),
            "difficulty": list(self._active_filters["difficulty"]),
        }

    def focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()
