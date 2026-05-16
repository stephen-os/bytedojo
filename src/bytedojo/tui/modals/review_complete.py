"""
ReviewCompleteModal — pick easy/good/hard quality, call ReviewService.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.core.repository import Repository
from bytedojo.services.review_service import ReviewQuality, ReviewService
from bytedojo.tui.modals._base import BASE_MODAL_CSS


class ReviewCompleteModal(ModalScreen[Optional[ReviewQuality]]):
    """Single-key Easy/Good/Hard chooser → ``ReviewService.complete_review``."""

    BINDINGS = [
        Binding("e", "complete('easy')", "Easy"),
        Binding("g", "complete('good')", "Good"),
        Binding("h", "complete('hard')", "Hard"),
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = BASE_MODAL_CSS

    def __init__(
        self,
        repo: Repository,
        problem: RegisteredProblem,
    ) -> None:
        super().__init__()
        self._repo = repo
        self._problem = problem

    def compose(self) -> ComposeResult:
        title = (
            f"Review complete  ·  #{self._problem.problem_id}  "
            f"{self._problem.title}"
        )
        yield Vertical(
            Static(title, classes="modal-title"),
            Static(
                f"language: {self._problem.language.value}",
                classes="modal-section",
            ),
            Static(
                "How did the review go?",
                classes="modal-section",
            ),
            Static("  [E]asy — interval grows extra",      classes="modal-row"),
            Static("  [G]ood — interval grows by ease",    classes="modal-row"),
            Static("  [H]ard — interval reset to 1 day",   classes="modal-row"),
            Static("esc cancel", classes="modal-footer"),
            classes="modal-card",
        )

    # ----------------------------------------------------------------- actions

    def action_complete(self, quality_str: str) -> None:
        quality = ReviewQuality(quality_str)
        result = ReviewService().complete_review(
            self._repo, self._problem.id, quality,
        )
        if result.failed:
            self.app.notify(
                result.error or "review-complete failed",
                title="review", severity="error",
            )
            self.dismiss(None)
            return
        msg = (
            f"interval {result.previous_interval}d → {result.next_interval}d  ·  "
            f"ease {result.previous_ease:.2f} → {result.next_ease:.2f}"
        )
        self.app.notify(msg, title=f"dojo review complete --{quality.value}",
                        severity="information")
        self.dismiss(quality)

    def action_cancel(self) -> None:
        self.dismiss(None)
