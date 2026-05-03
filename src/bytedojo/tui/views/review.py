"""
Review view - Spaced repetition review session.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, Center
from textual.widgets import Static, Button, ProgressBar
from textual.widget import Widget
from textual.message import Message
from textual.reactive import reactive

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.review_service import ReviewService, ReviewProblem


class ReviewProgress(Widget):
    """Progress bar for review session."""

    DEFAULT_CSS = """
    ReviewProgress {
        width: 100%;
        height: 3;
        padding: 0 4;
        background: #161b22;
    }

    ReviewProgress Horizontal {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    ReviewProgress .progress-label {
        width: auto;
        color: #8b949e;
        padding-right: 2;
    }

    ReviewProgress ProgressBar {
        width: 1fr;
        padding: 0 2;
    }

    ReviewProgress .progress-count {
        width: auto;
        color: #6a2a8a;
        text-style: bold;
        padding-left: 2;
    }
    """

    current: reactive[int] = reactive(0)
    total: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static("Progress:", classes="progress-label")
            yield ProgressBar(total=100, show_eta=False)
            yield Static("0/0", id="progress-count", classes="progress-count")

    def watch_current(self, value: int) -> None:
        self._update_display()

    def watch_total(self, value: int) -> None:
        self._update_display()

    def _update_display(self) -> None:
        try:
            progress_bar = self.query_one(ProgressBar)
            count_label = self.query_one("#progress-count", Static)

            if self.total > 0:
                progress_bar.update(total=100, progress=(self.current / self.total) * 100)
                count_label.update(f"{self.current}/{self.total}")
            else:
                progress_bar.update(total=100, progress=0)
                count_label.update("0/0")
        except Exception:
            pass


class ReviewCard(Widget):
    """Card displaying current problem to review."""

    DEFAULT_CSS = """
    ReviewCard {
        width: 100%;
        height: auto;
        padding: 2 4;
        background: #161b22;
        border: tall #21262d;
        margin: 1 4;
    }

    ReviewCard .card-header {
        width: 100%;
        text-align: center;
        padding-bottom: 1;
    }

    ReviewCard .problem-id {
        color: #6a2a8a;
        text-style: bold;
    }

    ReviewCard .problem-title {
        color: #e6edf3;
        text-style: bold;
        text-align: center;
        padding: 1 0;
    }

    ReviewCard .divider {
        color: #21262d;
        text-align: center;
        width: 100%;
    }

    ReviewCard .detail-row {
        width: 100%;
        height: 1;
        padding: 0 2;
    }

    ReviewCard .detail-label {
        width: 18;
        color: #8b949e;
    }

    ReviewCard .detail-value {
        width: 1fr;
        color: #e6edf3;
    }

    ReviewCard .detail-value.easy {
        color: #58a6ff;
    }

    ReviewCard .detail-value.medium {
        color: #f06060;
    }

    ReviewCard .detail-value.hard {
        color: #c43a3a;
    }

    ReviewCard .file-path {
        color: #8b949e;
        text-align: center;
        padding: 1 0;
    }

    ReviewCard .url {
        color: #58a6ff;
        text-align: center;
    }
    """

    def __init__(self, problem: ReviewProblem | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.problem = problem

    def compose(self) -> ComposeResult:
        if not self.problem:
            yield Static("No problem loaded", classes="problem-title")
            return

        p = self.problem

        with Vertical():
            yield Static(f"#{p.problem_id}", classes="card-header problem-id")
            yield Static(p.title, classes="problem-title")
            yield Static("─" * 50, classes="divider")

            with Horizontal(classes="detail-row"):
                yield Static("Difficulty:", classes="detail-label")
                yield Static(p.difficulty, classes=f"detail-value {p.difficulty.lower()}")

            with Horizontal(classes="detail-row"):
                yield Static("Language:", classes="detail-label")
                yield Static(p.language.upper(), classes="detail-value")

            with Horizontal(classes="detail-row"):
                yield Static("Times Reviewed:", classes="detail-label")
                yield Static(str(p.repetitions), classes="detail-value")

            with Horizontal(classes="detail-row"):
                yield Static("Due:", classes="detail-label")
                due_text = ReviewService.format_due_date(p.next_review_date)
                yield Static(due_text, classes="detail-value")

            yield Static("─" * 50, classes="divider")

            if p.file_path:
                yield Static(f"📁 {p.file_path}", classes="file-path")

            if p.url:
                yield Static(f"🔗 {p.url}", classes="url")

    def set_problem(self, problem: ReviewProblem | None) -> None:
        """Update the displayed problem."""
        self.problem = problem
        self.refresh(recompose=True)


class GradeButtons(Widget):
    """Buttons for grading the current problem."""

    DEFAULT_CSS = """
    GradeButtons {
        width: 100%;
        height: auto;
        padding: 2 4;
    }

    GradeButtons .grade-row {
        width: 100%;
        height: 3;
        align: center middle;
    }

    GradeButtons Button {
        margin: 0 2;
        min-width: 16;
    }

    GradeButtons .btn-pass {
        background: #58a6ff;
    }

    GradeButtons .btn-pass:hover {
        background: #79c0ff;
    }

    GradeButtons .btn-fail {
        background: #c43a3a;
    }

    GradeButtons .btn-fail:hover {
        background: #f06060;
    }

    GradeButtons .btn-skip {
        background: #21262d;
    }

    GradeButtons .btn-skip:hover {
        background: #30363d;
    }

    GradeButtons .action-row {
        width: 100%;
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    GradeButtons .hint {
        width: 100%;
        text-align: center;
        color: #8b949e;
        padding-top: 1;
    }
    """

    class GradeSelected(Message):
        """Message when a grade is selected."""
        def __init__(self, grade: str) -> None:
            self.grade = grade
            super().__init__()

    class ActionSelected(Message):
        """Message when an action is selected."""
        def __init__(self, action: str) -> None:
            self.action = action
            super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="grade-row"):
                yield Button("Pass [P]", id="btn-pass", classes="btn-pass")
                yield Button("Fail [F]", id="btn-fail", classes="btn-fail")
                yield Button("Skip [S]", id="btn-skip", classes="btn-skip")

            with Horizontal(classes="action-row"):
                yield Button("Open File [O]", id="btn-open", variant="default")
                yield Button("Open URL [L]", id="btn-url", variant="default")
                yield Button("Run [R]", id="btn-run", variant="default")

            yield Static("[N] Add Notes  [Q] Quit Session", classes="hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id

        if btn_id == "btn-pass":
            self.post_message(self.GradeSelected("passed"))
        elif btn_id == "btn-fail":
            self.post_message(self.GradeSelected("failed"))
        elif btn_id == "btn-skip":
            self.post_message(self.GradeSelected("skipped"))
        elif btn_id == "btn-open":
            self.post_message(self.ActionSelected("open"))
        elif btn_id == "btn-url":
            self.post_message(self.ActionSelected("url"))
        elif btn_id == "btn-run":
            self.post_message(self.ActionSelected("run"))


class ReviewComplete(Widget):
    """Widget shown when review session is complete."""

    DEFAULT_CSS = """
    ReviewComplete {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    ReviewComplete #complete-box {
        width: 50;
        height: auto;
        padding: 3 4;
        background: #161b22;
        border: tall #58a6ff;
        text-align: center;
    }

    ReviewComplete .complete-icon {
        color: #58a6ff;
        text-style: bold;
    }

    ReviewComplete .complete-title {
        color: #e6edf3;
        text-style: bold;
        padding: 1 0;
    }

    ReviewComplete .complete-stats {
        color: #8b949e;
        padding: 1 0;
    }

    ReviewComplete Button {
        margin-top: 2;
    }
    """

    class DismissRequested(Message):
        """Message when dismiss is requested."""
        pass

    def __init__(self, stats: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = stats

    def compose(self) -> ComposeResult:
        with Center():
            with Container(id="complete-box"):
                yield Static("✓", classes="complete-icon")
                yield Static("Review Complete!", classes="complete-title")
                yield Static(
                    f"Passed: {self.stats.get('passed', 0)}  "
                    f"Failed: {self.stats.get('failed', 0)}  "
                    f"Skipped: {self.stats.get('skipped', 0)}",
                    classes="complete-stats"
                )
                yield Button("Done", variant="primary", id="btn-done")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-done":
            self.post_message(self.DismissRequested())


class NoReviewsDue(Widget):
    """Widget shown when no reviews are due."""

    DEFAULT_CSS = """
    NoReviewsDue {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    NoReviewsDue #no-reviews-box {
        width: 50;
        height: auto;
        padding: 3 4;
        background: #161b22;
        border: tall #58a6ff;
        text-align: center;
    }

    NoReviewsDue .icon {
        color: #58a6ff;
        text-style: bold;
    }

    NoReviewsDue .title {
        color: #e6edf3;
        text-style: bold;
        padding: 1 0;
    }

    NoReviewsDue .subtitle {
        color: #8b949e;
    }

    NoReviewsDue .hint {
        color: #8b949e;
        padding-top: 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with Container(id="no-reviews-box"):
                yield Static("✓", classes="icon")
                yield Static("All Caught Up!", classes="title")
                yield Static("No problems due for review.", classes="subtitle")
                yield Static("Come back later or solve new problems.", classes="hint")


class ReviewView(Widget):
    """View for spaced repetition review sessions."""

    DEFAULT_CSS = """
    ReviewView {
        width: 100%;
        height: 100%;
        background: #0d1117;
    }

    ReviewView .view-title {
        text-style: bold;
        color: #6a2a8a;
        text-align: center;
        padding: 1 0;
        width: 100%;
    }

    ReviewView .view-divider {
        color: #21262d;
        text-align: center;
        width: 100%;
    }

    ReviewView #review-content {
        width: 100%;
        height: 1fr;
    }

    ReviewView #session-container {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        ("p", "grade_pass", "Pass"),
        ("f", "grade_fail", "Fail"),
        ("s", "grade_skip", "Skip"),
        ("o", "open_file", "Open File"),
        ("l", "open_url", "Open URL"),
        ("r", "run_problem", "Run"),
        ("n", "add_notes", "Add Notes"),
        ("q", "quit_session", "Quit Session"),
    ]

    class SessionEnded(Message):
        """Message when review session ends."""
        pass

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._due_problems: list[ReviewProblem] = []
        self._current_index: int = 0
        self._session_stats: dict = {"passed": 0, "failed": 0, "skipped": 0}
        self._current_notes: str = ""
        self._session_active: bool = False

    def compose(self) -> ComposeResult:
        yield Static("═" * 60, classes="view-divider")
        yield Static("REVIEW SESSION", classes="view-title")
        yield Static("═" * 60, classes="view-divider")

        yield ReviewProgress(id="review-progress")

        with Container(id="review-content"):
            yield Container(id="session-container")

    def on_mount(self) -> None:
        """Load due reviews when mounted."""
        self._load_due_reviews()
        self._render_session()

    def _load_due_reviews(self) -> None:
        """Load problems due for review."""
        repo = Repository(Path.cwd())

        if not repo.is_initialized:
            self._due_problems = []
            return

        with DatabaseManager(repo.db_path) as db:
            service = ReviewService(db)
            self._due_problems = service.get_due_reviews(include_future=False)

        self._current_index = 0
        self._session_stats = {"passed": 0, "failed": 0, "skipped": 0}
        self._session_active = len(self._due_problems) > 0

    def _render_session(self) -> None:
        """Render the current session state."""
        container = self.query_one("#session-container")
        container.remove_children()

        # Update progress
        progress = self.query_one(ReviewProgress)
        progress.total = len(self._due_problems)
        progress.current = self._current_index

        if not self._due_problems:
            container.mount(NoReviewsDue())
        elif self._current_index >= len(self._due_problems):
            # Session complete
            container.mount(ReviewComplete(self._session_stats))
        else:
            # Show current problem
            problem = self._due_problems[self._current_index]
            container.mount(ReviewCard(problem, id="review-card"))
            container.mount(GradeButtons(id="grade-buttons"))

    def _grade_current(self, grade: str) -> None:
        """Grade the current problem and move to next."""
        if not self._session_active or self._current_index >= len(self._due_problems):
            return

        problem = self._due_problems[self._current_index]

        # Apply grade using grading service
        repo = Repository(Path.cwd())
        with DatabaseManager(repo.db_path) as db:
            from bytedojo.core.grading import GradingService
            service = GradingService(db)
            service.grade_problem(problem.id, grade, self._current_notes or None)

        # Update stats
        self._session_stats[grade] = self._session_stats.get(grade, 0) + 1

        # Show feedback
        if grade == "passed":
            self.notify("✓ Passed! Scheduled for next review.", title="Graded")
        elif grade == "failed":
            self.notify("✗ Failed. Keep practicing!", title="Graded")
        else:
            self.notify("○ Skipped.", title="Graded")

        # Reset notes and move to next
        self._current_notes = ""
        self._current_index += 1
        self._render_session()

    def on_grade_buttons_grade_selected(self, event: GradeButtons.GradeSelected) -> None:
        """Handle grade selection."""
        self._grade_current(event.grade)

    def on_grade_buttons_action_selected(self, event: GradeButtons.ActionSelected) -> None:
        """Handle action selection."""
        if not self._due_problems or self._current_index >= len(self._due_problems):
            return

        problem = self._due_problems[self._current_index]

        if event.action == "open":
            if problem.file_path:
                self.notify(f"Opening: {problem.file_path}", title="Open File")
            else:
                self.notify("No file associated", title="Open File")
        elif event.action == "url":
            if problem.url:
                self.notify(f"Opening: {problem.url}", title="Open URL")
            else:
                self.notify("No URL available", title="Open URL")
        elif event.action == "run":
            self.notify(f"Running problem #{problem.problem_id}...", title="Run")

    def on_review_complete_dismiss_requested(self, event: ReviewComplete.DismissRequested) -> None:
        """Handle completion dismiss."""
        self._session_active = False
        self._load_due_reviews()
        self._render_session()

    def action_grade_pass(self) -> None:
        """Grade current problem as passed."""
        self._grade_current("passed")

    def action_grade_fail(self) -> None:
        """Grade current problem as failed."""
        self._grade_current("failed")

    def action_grade_skip(self) -> None:
        """Grade current problem as skipped."""
        self._grade_current("skipped")

    def action_open_file(self) -> None:
        """Open the problem file."""
        if self._due_problems and self._current_index < len(self._due_problems):
            problem = self._due_problems[self._current_index]
            if problem.file_path:
                self.notify(f"Opening: {problem.file_path}", title="Open File")

    def action_open_url(self) -> None:
        """Open the problem URL."""
        if self._due_problems and self._current_index < len(self._due_problems):
            problem = self._due_problems[self._current_index]
            if problem.url:
                self.notify(f"Opening: {problem.url}", title="Open URL")

    def action_run_problem(self) -> None:
        """Run the current problem."""
        if self._due_problems and self._current_index < len(self._due_problems):
            problem = self._due_problems[self._current_index]
            self.notify(f"Running problem #{problem.problem_id}...", title="Run")

    def action_add_notes(self) -> None:
        """Add notes to the current grade."""
        self.notify("Notes input coming soon!", title="Add Notes")

    def action_quit_session(self) -> None:
        """Quit the current review session."""
        self._session_active = False
        self.post_message(self.SessionEnded())

    def refresh_reviews(self) -> None:
        """Refresh the review list."""
        self._load_due_reviews()
        self._render_session()
