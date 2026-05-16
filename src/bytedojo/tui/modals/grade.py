"""
GradeModal — pick pass/fail/skip + optional notes, then call GradingService.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.services.grading_service import GradingService
from bytedojo.tui.modals._base import BASE_MODAL_CSS


class GradeModal(ModalScreen[Optional[str]]):
    """Single-key Pass/Fail/Skip selector with an inline notes field.

    Calls ``GradingService.grade()`` on submit and dismisses with the
    applied status (or ``None`` if cancelled).
    """

    BINDINGS = [
        Binding("p", "set_status('passed')",   "Pass"),
        Binding("f", "set_status('failed')",   "Fail"),
        Binding("s", "set_status('skipped')",  "Skip"),
        Binding("enter", "submit", "Submit"),
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = BASE_MODAL_CSS + """
    .grade-status-row {
        padding: 0 0 1 0;
    }

    .grade-choice {
        padding: 0 2;
    }

    .grade-choice-active {
        text-style: bold;
        background: $boost;
    }

    Input {
        margin-top: 1;
    }
    """

    def __init__(
        self,
        repo: Repository,
        problem: RegisteredProblem,
    ) -> None:
        super().__init__()
        self._repo = repo
        self._problem = problem
        self._status: Optional[str] = None

    def compose(self) -> ComposeResult:
        title = f"Grade #{self._problem.problem_id}  ·  {self._problem.title}"
        yield Vertical(
            Static(title, classes="modal-title"),
            Static(
                f"language: {self._problem.language.value}",
                classes="modal-section",
            ),
            Static(
                "  [P]ass    [F]ail    [S]kip",
                classes="grade-status-row",
                id="grade-status-display",
            ),
            Static("Notes (optional):", classes="modal-section"),
            Input(placeholder="…", id="grade-notes"),
            Static(
                "enter submit · esc cancel",
                classes="modal-footer",
            ),
            classes="modal-card",
        )

    # ----------------------------------------------------------------- actions

    def action_set_status(self, status: str) -> None:
        self._status = status
        display = self.query_one("#grade-status-display", Static)
        markers = {
            "passed":  "  [P]ass★    [F]ail    [S]kip",
            "failed":  "  [P]ass    [F]ail★   [S]kip",
            "skipped": "  [P]ass    [F]ail    [S]kip★",
        }
        display.update(markers[status])

    def action_submit(self) -> None:
        if self._status is None:
            self.app.notify(
                "Choose [P]ass / [F]ail / [S]kip first",
                title="grade", severity="warning",
            )
            return
        notes = self.query_one("#grade-notes", Input).value.strip() or None
        result = GradingService().grade(
            self._repo, self._problem, status=self._status, notes=notes,
        )
        if result.failed:
            self.app.notify(
                result.error or "grade failed",
                title="grade", severity="error",
            )
            self.dismiss(None)
            return
        msg = f"recorded {self._status.upper()}"
        if result.scheduled_review:
            msg += f" · review in {result.review_frequency_days}d"
        self.app.notify(msg, title="dojo grade", severity="information")
        self.dismiss(self._status)

    def action_cancel(self) -> None:
        self.dismiss(None)
