"""
FetchModal — input a problem ID + pick a language, then call FetchService.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.repository import Repository
from bytedojo.services.fetch_service import FetchResult, FetchService
from bytedojo.tui.modals._base import BASE_MODAL_CSS


class FetchModal(ModalScreen[Optional[FetchResult]]):
    """Single-problem fetch — ID input + language single-key choice."""

    BINDINGS = [
        Binding("p", "set_language('python3')", "Python"),
        Binding("j", "set_language('java')",    "Java"),
        Binding("c", "set_language('cpp')",     "C++"),
        Binding("ctrl+f", "toggle_force",       "Toggle force"),
        Binding("enter", "submit", "Fetch"),
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = BASE_MODAL_CSS + """
    FetchModal .modal-card {
        width: 70;
    }

    FetchModal .fetch-status {
        padding: 1 0 0 0;
    }

    Input {
        margin-top: 1;
    }
    """

    def __init__(
        self,
        repo: Repository,
        prefilled_id: Optional[int] = None,
        default_language: CodeLanguage = CodeLanguage.PYTHON,
    ) -> None:
        super().__init__()
        self._repo = repo
        self._prefilled_id = prefilled_id
        self._language = default_language
        self._force = False

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("dojo fetch", classes="modal-title"),
            Static("Problem ID:", classes="modal-section"),
            Input(
                value=str(self._prefilled_id) if self._prefilled_id else "",
                placeholder="e.g. 1 or 200",
                id="fetch-id",
            ),
            Static(
                self._language_display(),
                id="fetch-language-row",
                classes="fetch-status",
            ),
            Static(
                self._force_display(),
                id="fetch-force-row",
                classes="modal-row",
            ),
            Static(
                "enter fetch · esc cancel · p/j/c language · ctrl+f toggle force",
                classes="modal-footer",
            ),
            classes="modal-card",
        )

    def on_mount(self) -> None:
        # Auto-focus the ID input.
        self.query_one("#fetch-id", Input).focus()

    # ----------------------------------------------------------------- actions

    def action_set_language(self, lang_value: str) -> None:
        self._language = CodeLanguage.from_string(lang_value)
        self.query_one("#fetch-language-row", Static).update(self._language_display())

    def action_toggle_force(self) -> None:
        self._force = not self._force
        self.query_one("#fetch-force-row", Static).update(self._force_display())

    def action_submit(self) -> None:
        raw = self.query_one("#fetch-id", Input).value.strip()
        if not raw:
            self.app.notify("enter a problem ID first", title="fetch",
                            severity="warning")
            return
        try:
            problem_id = int(raw)
        except ValueError:
            self.app.notify(f"not a valid id: {raw!r}", title="fetch",
                            severity="error")
            return

        result = FetchService().fetch_and_place(
            self._repo, problem_id, self._language, force=self._force,
        )
        if result.failed:
            self.app.notify(
                result.error or "fetch failed",
                title="dojo fetch", severity="error",
            )
            self.dismiss(result)
            return
        if result.skipped:
            self.app.notify(
                f"#{result.problem_id} skipped: {result.skip_reason}",
                title="dojo fetch", severity="warning",
            )
            self.dismiss(result)
            return

        self.app.notify(
            f"placed #{result.problem_id} {result.title} v{result.version}",
            title="dojo fetch", severity="information",
        )
        self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)

    # ----------------------------------------------------------------- display

    def _language_display(self) -> str:
        marker = {
            CodeLanguage.PYTHON: "★ Python    Java       C++       ",
            CodeLanguage.JAVA:   "  Python  ★ Java       C++       ",
            CodeLanguage.CPP:    "  Python    Java     ★ C++       ",
        }.get(self._language, "")
        return f"Language: {marker.strip()}"

    def _force_display(self) -> str:
        return f"Force:    {'[ON ] (bumps version)' if self._force else '[OFF]'}"
