"""
Problem table widget for displaying problems in a list.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, DataTable
from textual.widget import Widget
from textual.message import Message
from textual.reactive import reactive


class ProblemTable(Widget):
    """Table displaying problems with status, difficulty, and title."""

    DEFAULT_CSS = """
    ProblemTable {
        width: 100%;
        height: 1fr;
        background: #0d1117;
    }

    ProblemTable DataTable {
        width: 100%;
        height: 1fr;
        background: #0d1117;
    }

    ProblemTable DataTable > .datatable--header {
        background: #161b22;
        color: #8b949e;
        text-style: bold;
    }

    ProblemTable DataTable > .datatable--cursor {
        background: #21262d;
    }

    ProblemTable DataTable > .datatable--hover {
        background: #161b22;
    }

    ProblemTable #pagination {
        dock: bottom;
        width: 100%;
        height: 1;
        background: #161b22;
        padding: 0 2;
    }

    ProblemTable #pagination .page-info {
        width: 1fr;
        color: #8b949e;
    }

    ProblemTable #pagination .page-nav {
        width: auto;
        color: #8b949e;
    }
    """

    problems: reactive[list] = reactive([])
    current_page: reactive[int] = reactive(1)
    per_page: reactive[int] = reactive(15)
    total_count: reactive[int] = reactive(0)

    class ProblemSelected(Message):
        """Message sent when a problem is selected."""
        def __init__(self, problem: dict) -> None:
            self.problem = problem
            super().__init__()

    class PageChanged(Message):
        """Message sent when page changes."""
        def __init__(self, page: int) -> None:
            self.page = page
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._problem_map: dict = {}  # Map row keys to problems

    def compose(self) -> ComposeResult:
        yield DataTable(id="problems-table")
        with Horizontal(id="pagination"):
            yield Static("", id="page-info", classes="page-info")
            yield Static("[←/h] Prev  [→/l] Next", classes="page-nav")

    def on_mount(self) -> None:
        """Set up the data table."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column("ID", width=6, key="id")
        table.add_column("St", width=3, key="status")
        table.add_column("D", width=2, key="difficulty")
        table.add_column("Title", width=40, key="title")
        table.add_column("Lang", width=6, key="language")
        table.add_column("Tags", width=20, key="tags")

        self._update_pagination_info()

    def watch_problems(self, problems: list) -> None:
        """Update table when problems change."""
        self._refresh_table()

    def watch_current_page(self, page: int) -> None:
        """Update pagination info when page changes."""
        self._update_pagination_info()

    def _refresh_table(self) -> None:
        """Refresh the table with current problems."""
        table = self.query_one(DataTable)
        table.clear()
        self._problem_map.clear()

        for problem in self.problems:
            row_key = self._add_problem_row(table, problem)
            self._problem_map[row_key] = problem

    def _add_problem_row(self, table: DataTable, problem: dict) -> str:
        """Add a problem row to the table."""
        problem_id = str(problem.get('problem_id', '?'))
        status = problem.get('test_status', 'ungraded')
        difficulty = problem.get('difficulty', 'Unknown')
        title = problem.get('title', 'Unknown')
        language = problem.get('language', '')
        tags = problem.get('tags', [])

        # Status icon
        status_icons = {
            'passed': ('✓', 'green'),
            'failed': ('✗', 'red'),
            'skipped': ('○', 'yellow'),
            'ungraded': ('◐', 'white'),
        }
        status_icon, _ = status_icons.get(status, ('○', 'white'))

        # Difficulty icon
        diff_map = {'Easy': 'E', 'Medium': 'M', 'Hard': 'H'}
        diff_icon = diff_map.get(difficulty, '?')

        # Truncate title
        if len(title) > 38:
            title = title[:35] + "..."

        # Format tags
        if isinstance(tags, list):
            tags_str = ", ".join(tags[:2])
            if len(tags) > 2:
                tags_str += f" +{len(tags)-2}"
        else:
            tags_str = str(tags) if tags else ""

        if len(tags_str) > 18:
            tags_str = tags_str[:15] + "..."

        # Language display
        lang_map = {'python': 'PY', 'java': 'JAVA', 'cpp': 'C++'}
        lang_display = lang_map.get(language, language.upper()[:4] if language else '')

        row_key = table.add_row(
            problem_id,
            status_icon,
            diff_icon,
            title,
            lang_display,
            tags_str,
            key=f"problem-{problem.get('id', problem_id)}"
        )

        return row_key

    def _update_pagination_info(self) -> None:
        """Update the pagination display."""
        try:
            page_info = self.query_one("#page-info", Static)
            total_pages = max(1, (self.total_count + self.per_page - 1) // self.per_page)
            start = (self.current_page - 1) * self.per_page + 1
            end = min(self.current_page * self.per_page, self.total_count)

            if self.total_count > 0:
                page_info.update(f"Page {self.current_page}/{total_pages} | Showing {start}-{end} of {self.total_count}")
            else:
                page_info.update("No problems found")
        except Exception:
            pass  # Widget not mounted yet

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if event.row_key and event.row_key.value in self._problem_map:
            problem = self._problem_map[event.row_key.value]
            self.post_message(self.ProblemSelected(problem))

    def action_next_page(self) -> None:
        """Go to next page."""
        total_pages = max(1, (self.total_count + self.per_page - 1) // self.per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.post_message(self.PageChanged(self.current_page))

    def action_prev_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.post_message(self.PageChanged(self.current_page))

    def set_problems(self, problems: list, total: int, page: int = 1) -> None:
        """Set the problems to display."""
        self.total_count = total
        self.current_page = page
        self.problems = problems
        self._update_pagination_info()
