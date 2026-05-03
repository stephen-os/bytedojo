"""
Problem detail modal - View problem details.
"""

import re
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button
from textual.message import Message


class ProblemDetailModal(ModalScreen):
    """Modal showing detailed problem information."""

    CSS = """
    ProblemDetailModal {
        align: center middle;
    }

    #modal-container {
        width: 70%;
        max-width: 80;
        height: auto;
        max-height: 85%;
        background: #161b22;
        border: tall #6a2a8a;
        padding: 0;
    }

    #modal-header {
        width: 100%;
        height: 3;
        background: #6a2a8a;
        padding: 0 2;
    }

    #modal-title {
        width: 1fr;
        color: #e6edf3;
        text-style: bold;
        padding: 1 0;
    }

    #modal-close {
        width: 3;
        text-align: center;
        color: #e6edf3;
        padding: 1 0;
    }

    #modal-close:hover {
        color: #c43a3a;
    }

    #modal-body {
        width: 100%;
        height: auto;
        max-height: 60;
        padding: 1 2;
    }

    .detail-section {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .detail-row {
        width: 100%;
        height: 1;
    }

    .detail-label {
        width: 15;
        color: #8b949e;
    }

    .detail-value {
        width: 1fr;
        color: #e6edf3;
    }

    .detail-value.easy {
        color: #58a6ff;
    }

    .detail-value.medium {
        color: #f06060;
    }

    .detail-value.hard {
        color: #c43a3a;
    }

    .detail-value.passed {
        color: #58a6ff;
    }

    .detail-value.failed {
        color: #c43a3a;
    }

    .detail-value.skipped {
        color: #f06060;
    }

    .section-title {
        width: 100%;
        color: #6a2a8a;
        text-style: bold;
        padding: 1 0 0 0;
        border-bottom: solid #21262d;
    }

    #description-box {
        width: 100%;
        height: auto;
        max-height: 15;
        background: #0d1117;
        border: tall #21262d;
        padding: 1;
        margin: 1 0;
    }

    #description-text {
        width: 100%;
        color: #8b949e;
    }

    #modal-footer {
        width: 100%;
        height: 3;
        background: #21262d;
        padding: 0 2;
        dock: bottom;
    }

    #modal-footer Horizontal {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #modal-footer Button {
        margin: 0 1;
    }

    #modal-footer .shortcut-hint {
        width: 1fr;
        text-align: right;
        color: #8b949e;
        padding: 1 0;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
        ("r", "run", "Run"),
        ("g", "grade", "Grade"),
        ("o", "open_file", "Open File"),
        ("l", "open_url", "Open URL"),
    ]

    class ActionRequested(Message):
        """Message when an action is requested."""
        def __init__(self, action: str, problem: dict) -> None:
            self.action = action
            self.problem = problem
            super().__init__()

    def __init__(self, problem: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.problem = problem

    def compose(self) -> ComposeResult:
        problem = self.problem
        problem_id = problem.get('problem_id', '?')
        title = problem.get('title', 'Unknown')
        difficulty = problem.get('difficulty', 'Unknown')
        status = problem.get('test_status', 'ungraded')
        language = problem.get('language', 'python')
        source = problem.get('source', 'leetcode')
        file_path = problem.get('file_path', '')
        description = problem.get('description', 'No description available.')
        tags = problem.get('tags', [])

        # Generate URL
        url = self._generate_url(source, problem_id, title)

        with Container(id="modal-container"):
            # Header
            with Horizontal(id="modal-header"):
                yield Static(f"#{problem_id} - {title}", id="modal-title")
                yield Static("×", id="modal-close")

            # Body
            with ScrollableContainer(id="modal-body"):
                # Basic info section
                with Vertical(classes="detail-section"):
                    with Horizontal(classes="detail-row"):
                        yield Static("Difficulty:", classes="detail-label")
                        yield Static(difficulty, classes=f"detail-value {difficulty.lower()}")

                    with Horizontal(classes="detail-row"):
                        yield Static("Status:", classes="detail-label")
                        yield Static(status.title(), classes=f"detail-value {status}")

                    with Horizontal(classes="detail-row"):
                        yield Static("Language:", classes="detail-label")
                        yield Static(language.upper(), classes="detail-value")

                    with Horizontal(classes="detail-row"):
                        yield Static("Source:", classes="detail-label")
                        yield Static(source.title(), classes="detail-value")

                    if tags:
                        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
                        with Horizontal(classes="detail-row"):
                            yield Static("Tags:", classes="detail-label")
                            yield Static(tags_str, classes="detail-value")

                # File section
                if file_path:
                    yield Static("File", classes="section-title")
                    with Horizontal(classes="detail-row"):
                        yield Static("Path:", classes="detail-label")
                        yield Static(file_path, classes="detail-value")

                # URL section
                if url:
                    yield Static("Links", classes="section-title")
                    with Horizontal(classes="detail-row"):
                        yield Static("URL:", classes="detail-label")
                        yield Static(url, classes="detail-value")

                # Description section
                yield Static("Description", classes="section-title")
                with Container(id="description-box"):
                    # Clean up description (remove HTML tags, limit length)
                    clean_desc = self._clean_description(description)
                    yield Static(clean_desc, id="description-text")

            # Footer with actions
            with Container(id="modal-footer"):
                with Horizontal():
                    yield Button("Run [R]", variant="primary", id="btn-run")
                    yield Button("Grade [G]", variant="default", id="btn-grade")
                    yield Button("Open [O]", variant="default", id="btn-open")
                    yield Static("[Esc] Close", classes="shortcut-hint")

    def _generate_url(self, source: str, problem_id: str, title: str) -> str:
        """Generate URL for the problem."""
        if source == 'leetcode':
            title_slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            return f"https://leetcode.com/problems/{title_slug}/"
        return ""

    def _clean_description(self, description: str) -> str:
        """Clean up description text."""
        if not description:
            return "No description available."

        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', description)
        # Replace HTML entities
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&quot;', '"')
        # Clean up whitespace
        clean = re.sub(r'\n\s*\n', '\n\n', clean)
        clean = clean.strip()

        # Limit length
        if len(clean) > 500:
            clean = clean[:500] + "..."

        return clean

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-run":
            self.action_run()
        elif event.button.id == "btn-grade":
            self.action_grade()
        elif event.button.id == "btn-open":
            self.action_open_file()

    def on_click(self, event) -> None:
        """Handle clicks on close button."""
        try:
            widget = self.query_one("#modal-close")
            if widget and event.widget == widget:
                self.action_close()
        except Exception:
            pass

    def action_close(self) -> None:
        """Close the modal."""
        self.app.pop_screen()

    def action_run(self) -> None:
        """Run the problem."""
        self.post_message(self.ActionRequested("run", self.problem))
        self.app.pop_screen()

    def action_grade(self) -> None:
        """Grade the problem."""
        self.post_message(self.ActionRequested("grade", self.problem))
        self.app.pop_screen()

    def action_open_file(self) -> None:
        """Open the problem file."""
        file_path = self.problem.get('file_path', '')
        if file_path:
            self.notify(f"Opening: {file_path}", title="Open File")
            # TODO: Actually open the file
        else:
            self.notify("No file associated with this problem", title="Open File")

    def action_open_url(self) -> None:
        """Open the problem URL."""
        url = self._generate_url(
            self.problem.get('source', 'leetcode'),
            self.problem.get('problem_id', ''),
            self.problem.get('title', '')
        )
        if url:
            self.notify(f"Opening: {url}", title="Open URL")
            # TODO: Actually open the URL
        else:
            self.notify("No URL available", title="Open URL")
