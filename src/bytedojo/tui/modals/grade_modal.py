"""
Grade modal - Grade a problem with notes.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input, TextArea
from textual.message import Message

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.grading import GradingService


class GradeModal(ModalScreen):
    """Modal for grading a problem."""

    CSS = """
    GradeModal {
        align: center middle;
    }

    #grade-container {
        width: 60;
        height: auto;
        background: #161b22;
        border: tall #6a2a8a;
        padding: 0;
    }

    #grade-header {
        width: 100%;
        height: 3;
        background: #6a2a8a;
        padding: 0 2;
    }

    #grade-title {
        width: 1fr;
        color: #e6edf3;
        text-style: bold;
        padding: 1 0;
    }

    #grade-close {
        width: 3;
        text-align: center;
        color: #e6edf3;
        padding: 1 0;
    }

    #grade-close:hover {
        color: #c43a3a;
    }

    #grade-body {
        width: 100%;
        height: auto;
        padding: 2;
    }

    .problem-info {
        width: 100%;
        text-align: center;
        padding-bottom: 1;
    }

    .problem-id {
        color: #6a2a8a;
        text-style: bold;
    }

    .problem-title {
        color: #e6edf3;
    }

    .section-label {
        color: #8b949e;
        padding: 1 0 0 0;
    }

    #notes-input {
        width: 100%;
        height: 4;
        background: #0d1117;
        border: tall #21262d;
        margin: 1 0;
    }

    #notes-input:focus {
        border: tall #6a2a8a;
    }

    #grade-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #grade-buttons Button {
        margin: 0 1;
        min-width: 14;
    }

    .btn-pass {
        background: #58a6ff;
    }

    .btn-pass:hover {
        background: #79c0ff;
    }

    .btn-fail {
        background: #c43a3a;
    }

    .btn-fail:hover {
        background: #f06060;
    }

    .btn-skip {
        background: #21262d;
    }

    .btn-skip:hover {
        background: #30363d;
    }

    #grade-footer {
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
        ("p", "grade_pass", "Pass"),
        ("f", "grade_fail", "Fail"),
        ("s", "grade_skip", "Skip"),
    ]

    class GradeApplied(Message):
        """Message when a grade is applied."""
        def __init__(self, problem: dict, grade: str, notes: str | None) -> None:
            self.problem = problem
            self.grade = grade
            self.notes = notes
            super().__init__()

    def __init__(self, problem: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.problem = problem

    def compose(self) -> ComposeResult:
        problem = self.problem
        problem_id = problem.get('problem_id', '?')
        title = problem.get('title', 'Unknown')

        with Container(id="grade-container"):
            # Header
            with Horizontal(id="grade-header"):
                yield Static("Grade Problem", id="grade-title")
                yield Static("×", id="grade-close")

            # Body
            with Vertical(id="grade-body"):
                yield Static(f"#{problem_id}", classes="problem-info problem-id")
                yield Static(title, classes="problem-info problem-title")

                yield Static("Notes (optional):", classes="section-label")
                yield Input(
                    placeholder="Add notes about your solution...",
                    id="notes-input"
                )

                with Horizontal(id="grade-buttons"):
                    yield Button("Pass [P]", id="btn-pass", classes="btn-pass")
                    yield Button("Fail [F]", id="btn-fail", classes="btn-fail")
                    yield Button("Skip [S]", id="btn-skip", classes="btn-skip")

            # Footer
            yield Static("[Esc] Cancel", id="grade-footer")

    def _get_notes(self) -> str | None:
        """Get the notes from the input."""
        try:
            notes_input = self.query_one("#notes-input", Input)
            notes = notes_input.value.strip()
            return notes if notes else None
        except Exception:
            return None

    def _apply_grade(self, grade: str) -> None:
        """Apply the grade and close."""
        notes = self._get_notes()
        problem_db_id = self.problem.get('id')

        if problem_db_id:
            repo = Repository(Path.cwd())
            with DatabaseManager(repo.db_path) as db:
                service = GradingService(db)
                result = service.grade_problem(problem_db_id, grade, notes)

                if result.success:
                    if grade == "passed":
                        self.notify(
                            f"✓ Passed! Scheduled for review in {result.review_frequency_days} days.",
                            title="Graded"
                        )
                    elif grade == "failed":
                        self.notify("✗ Failed. Keep practicing!", title="Graded")
                    else:
                        self.notify("○ Skipped.", title="Graded")

        self.post_message(self.GradeApplied(self.problem, grade, notes))
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-pass":
            self._apply_grade("passed")
        elif event.button.id == "btn-fail":
            self._apply_grade("failed")
        elif event.button.id == "btn-skip":
            self._apply_grade("skipped")

    def on_click(self, event) -> None:
        """Handle clicks on close button."""
        try:
            widget = self.query_one("#grade-close")
            if widget and event.widget == widget:
                self.action_close()
        except Exception:
            pass

    def action_close(self) -> None:
        """Close the modal."""
        self.app.pop_screen()

    def action_grade_pass(self) -> None:
        """Grade as passed."""
        self._apply_grade("passed")

    def action_grade_fail(self) -> None:
        """Grade as failed."""
        self._apply_grade("failed")

    def action_grade_skip(self) -> None:
        """Grade as skipped."""
        self._apply_grade("skipped")
