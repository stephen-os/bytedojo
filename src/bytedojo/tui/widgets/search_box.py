"""
SearchBox — port of gh-dash's filter-query line under the tabs.

Source: `clone/gh-dash/internal/tui/components/search/` +
`context/styles.go` s.Search.Root (rounded border, primary-border
colour).

Displays the active filter query (in gh-dash: things like
`is:pr review-requested:@me owner:dlvhdr`). For ByteDojo this becomes
the active practise filters: `lang:python status:passed`.

Pure display widget — input/edit lives in a future modal.
"""

from textual.containers import Container
from textual.widgets import Static


class SearchBox(Container):
    """Rounded-border box showing the active filter query."""

    def __init__(self, query: str = "") -> None:
        super().__init__()
        self.add_class("search-box")
        self._query = query

    def compose(self):
        text = self._query if self._query else "no filters · / to search"
        yield Static(text, classes="search-text")

    def set_query(self, query: str) -> None:
        self._query = query
        self.query_one(Static).update(query or "no filters · / to search")
