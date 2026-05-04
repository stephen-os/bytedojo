"""
Fetch modal - Fetch problems from LeetCode.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input, Checkbox, ProgressBar
from textual.message import Message
from textual import work

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.problem_fetcher import ProblemFetcher, FetchedProblem


class FetchModal(ModalScreen):
    """Modal for fetching problems from LeetCode."""

    CSS = """
    FetchModal {
        align: center middle;
    }

    #fetch-container {
        width: 65;
        height: auto;
        background: #161b22;
        border: tall #6a2a8a;
        padding: 0;
    }

    #fetch-header {
        width: 100%;
        height: 3;
        background: #6a2a8a;
        padding: 0 2;
    }

    #fetch-title {
        width: 1fr;
        color: #e6edf3;
        text-style: bold;
        padding: 1 0;
    }

    #fetch-close {
        width: 3;
        text-align: center;
        color: #e6edf3;
        padding: 1 0;
    }

    #fetch-close:hover {
        color: #c43a3a;
    }

    #fetch-body {
        width: 100%;
        height: auto;
        padding: 2;
    }

    .input-group {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .input-label {
        color: #8b949e;
        padding-bottom: 1;
    }

    #problem-input {
        width: 100%;
        background: #0d1117;
        border: tall #21262d;
    }

    #problem-input:focus {
        border: tall #6a2a8a;
    }

    .input-hint {
        color: #8b949e;
        padding-top: 1;
    }

    #language-buttons {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    #language-buttons Button {
        margin-right: 1;
    }

    .lang-btn {
        background: #21262d;
    }

    .lang-btn:hover {
        background: #30363d;
    }

    .lang-btn.selected {
        background: #6a2a8a;
    }

    #options-row {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    #force-checkbox {
        color: #8b949e;
    }

    #fetch-actions {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #fetch-actions Button {
        margin: 0 1;
        min-width: 12;
    }

    #btn-fetch {
        background: #58a6ff;
    }

    #btn-fetch:hover {
        background: #79c0ff;
    }

    #btn-cancel {
        background: #21262d;
    }

    #btn-cancel:hover {
        background: #30363d;
    }

    #progress-section {
        width: 100%;
        height: auto;
        padding: 1 0;
        display: none;
    }

    #progress-section.visible {
        display: block;
    }

    #progress-bar {
        width: 100%;
        height: 1;
        background: #21262d;
    }

    #progress-bar > .bar--bar {
        background: #6a2a8a;
    }

    #progress-text {
        width: 100%;
        color: #8b949e;
        text-align: center;
        padding-top: 1;
    }

    #result-section {
        width: 100%;
        height: auto;
        padding: 1 0;
        display: none;
    }

    #result-section.visible {
        display: block;
    }

    .result-success {
        color: #58a6ff;
    }

    .result-skip {
        color: #f06060;
    }

    .result-error {
        color: #c43a3a;
    }

    #fetch-footer {
        width: 100%;
        height: 1;
        background: #21262d;
        padding: 0 2;
        color: #8b949e;
        text-align: center;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
        ("enter", "submit", "Fetch"),
    ]

    class FetchCompleted(Message):
        """Message when fetch is completed."""
        def __init__(self, success_count: int, skip_count: int, error_count: int) -> None:
            self.success_count = success_count
            self.skip_count = skip_count
            self.error_count = error_count
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._selected_language = "python"
        self._is_fetching = False
        self._total_problems = 0
        self._fetched_count = 0

    def compose(self) -> ComposeResult:
        with Container(id="fetch-container"):
            # Header
            with Horizontal(id="fetch-header"):
                yield Static("Fetch Problems", id="fetch-title")
                yield Static("×", id="fetch-close")

            # Body
            with Vertical(id="fetch-body"):
                # Problem IDs input
                with Vertical(classes="input-group"):
                    yield Static("Problem ID(s):", classes="input-label")
                    yield Input(
                        placeholder="e.g., 1, 1..10, 1,2,5..10",
                        id="problem-input"
                    )
                    yield Static("Supports: single (1), range (1..10), list (1,2,3)", classes="input-hint")

                # Language selection
                with Vertical(classes="input-group"):
                    yield Static("Language:", classes="input-label")
                    with Horizontal(id="language-buttons"):
                        yield Button("Python", id="btn-python", classes="lang-btn selected")
                        yield Button("Java", id="btn-java", classes="lang-btn")
                        yield Button("C++", id="btn-cpp", classes="lang-btn")

                # Options
                with Horizontal(id="options-row"):
                    yield Checkbox("Force overwrite existing", id="force-checkbox")

                # Progress section (hidden initially)
                with Vertical(id="progress-section"):
                    yield ProgressBar(id="progress-bar", total=100)
                    yield Static("Fetching...", id="progress-text")

                # Result section (hidden initially)
                with Vertical(id="result-section"):
                    yield Static("", id="result-text")

                # Action buttons
                with Horizontal(id="fetch-actions"):
                    yield Button("Fetch", id="btn-fetch")
                    yield Button("Cancel", id="btn-cancel")

            # Footer
            yield Static("[Enter] Fetch  [Esc] Close", id="fetch-footer")

    def on_mount(self) -> None:
        """Focus the input on mount."""
        self.query_one("#problem-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-fetch":
            self._start_fetch()
        elif button_id == "btn-cancel":
            self.action_close()
        elif button_id == "btn-python":
            self._select_language("python")
        elif button_id == "btn-java":
            self._select_language("java")
        elif button_id == "btn-cpp":
            self._select_language("cpp")

    def on_click(self, event) -> None:
        """Handle clicks on close button."""
        try:
            widget = self.query_one("#fetch-close")
            if widget and event.widget == widget:
                self.action_close()
        except Exception:
            pass

    def _select_language(self, language: str) -> None:
        """Select a language."""
        self._selected_language = language

        # Update button styles
        for lang in ["python", "java", "cpp"]:
            btn = self.query_one(f"#btn-{lang}", Button)
            if lang == language:
                btn.add_class("selected")
            else:
                btn.remove_class("selected")

    def _start_fetch(self) -> None:
        """Start the fetch process."""
        if self._is_fetching:
            return

        # Get input values
        problem_input = self.query_one("#problem-input", Input)
        problem_str = problem_input.value.strip()

        if not problem_str:
            self.notify("Please enter problem ID(s)", title="Error", severity="error")
            return

        # Parse problem IDs
        try:
            problem_ids = ProblemFetcher.parse_problem_ids((problem_str,))
        except ValueError as e:
            self.notify(str(e), title="Error", severity="error")
            return

        if not problem_ids:
            self.notify("No valid problem IDs", title="Error", severity="error")
            return

        # Get force option
        force = self.query_one("#force-checkbox", Checkbox).value

        # Show progress section
        self._is_fetching = True
        self._total_problems = len(problem_ids)
        self._fetched_count = 0

        progress_section = self.query_one("#progress-section")
        progress_section.add_class("visible")

        result_section = self.query_one("#result-section")
        result_section.remove_class("visible")

        # Disable fetch button
        self.query_one("#btn-fetch", Button).disabled = True

        # Start fetch worker
        self._fetch_problems(problem_ids, self._selected_language, force)

    @work(exclusive=True, thread=True)
    def _fetch_problems(self, problem_ids: list, language: str, force: bool) -> None:
        """Fetch problems in a worker thread."""
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self.call_from_thread(self._show_error, "Dojo not initialized")
                return

            fetcher = ProblemFetcher(repo)

            # Get output directory
            with DatabaseManager(repo.db_path) as db:
                default_source = db.get_config('default_source', 'leetcode')

            output_dir = repo.root_path / default_source

            def on_progress(result: FetchedProblem):
                self.call_from_thread(self._update_progress, result)

            result = fetcher.fetch(
                problem_ids=problem_ids,
                language=language,
                output_dir=output_dir,
                force=force,
                on_progress=on_progress
            )

            self.call_from_thread(
                self._show_result,
                result.success_count,
                result.skip_count,
                result.error_count
            )

        except Exception as e:
            self.call_from_thread(self._show_error, str(e))

    def _update_progress(self, result: FetchedProblem) -> None:
        """Update progress display."""
        self._fetched_count += 1

        # Update progress bar
        progress = (self._fetched_count / self._total_problems) * 100
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(progress=progress)

        # Update text
        status = "fetched" if result.success and not result.skipped else "skipped" if result.skipped else "failed"
        progress_text = self.query_one("#progress-text", Static)
        progress_text.update(f"[{self._fetched_count}/{self._total_problems}] #{result.problem_id} {status}")

    def _show_result(self, success_count: int, skip_count: int, error_count: int) -> None:
        """Show fetch results."""
        self._is_fetching = False

        # Hide progress, show results
        self.query_one("#progress-section").remove_class("visible")
        result_section = self.query_one("#result-section")
        result_section.add_class("visible")

        # Build result text
        parts = []
        if success_count:
            parts.append(f"[#58a6ff]{success_count} fetched[/]")
        if skip_count:
            parts.append(f"[#f06060]{skip_count} skipped[/]")
        if error_count:
            parts.append(f"[#c43a3a]{error_count} failed[/]")

        result_text = self.query_one("#result-text", Static)
        result_text.update(" | ".join(parts) if parts else "No problems processed")

        # Re-enable fetch button
        self.query_one("#btn-fetch", Button).disabled = False

        # Notify completion
        self.notify(
            f"Fetched {success_count}, skipped {skip_count}, failed {error_count}",
            title="Fetch Complete"
        )

        # Post message
        self.post_message(self.FetchCompleted(success_count, skip_count, error_count))

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self._is_fetching = False

        self.query_one("#progress-section").remove_class("visible")
        result_section = self.query_one("#result-section")
        result_section.add_class("visible")

        result_text = self.query_one("#result-text", Static)
        result_text.update(f"[#c43a3a]Error: {message}[/]")

        self.query_one("#btn-fetch", Button).disabled = False
        self.notify(message, title="Error", severity="error")

    def action_close(self) -> None:
        """Close the modal."""
        if not self._is_fetching:
            self.app.pop_screen()

    def action_submit(self) -> None:
        """Submit the fetch."""
        self._start_fetch()
