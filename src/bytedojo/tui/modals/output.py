"""
RunOutputModal — display stdout/stderr/exit_code from a RunService call.

Triggered by ``r`` in PractiseScreen. The service call itself runs
synchronously before the modal opens (Python is fast; even C++ compile
finishes in a few seconds). For longer-running languages we'll switch
to a worker-backed progress modal in a later pass.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from bytedojo.core.toolchains.base import ExecutionResult
from bytedojo.services.run_service import RunServiceResult
from bytedojo.tui.modals._base import BASE_MODAL_CSS


class RunOutputModal(ModalScreen[None]):
    """Modal showing the captured stdout / stderr / exit code of a run."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("q", "app.pop_screen", "Close"),
    ]

    DEFAULT_CSS = BASE_MODAL_CSS + """
    RunOutputModal .modal-card {
        width: 100;
        max-height: 30;
    }

    RunOutputModal #run-output {
        height: auto;
        max-height: 18;
        padding: 1 0;
    }

    RunOutputModal .output-line {
        padding: 0;
    }

    RunOutputModal .stderr-line {
        color: $warning;
    }
    """

    def __init__(self, result: RunServiceResult, title_hint: str = "") -> None:
        super().__init__()
        self._result = result
        self._title_hint = title_hint

    def compose(self) -> ComposeResult:
        if self._result.failed:
            yield Vertical(
                Static(f"dojo run — failed", classes="modal-title"),
                Static(self._result.error or "unknown error",
                       classes="modal-error"),
                Static("esc / q close", classes="modal-footer"),
                classes="modal-card",
            )
            return

        execution: ExecutionResult = self._result.execution
        problem = self._result.problem
        header = (
            f"dojo run  ·  #{problem.problem_id} {problem.title}  ·  "
            f"{problem.language.value}"
        )
        if self._result.version is not None:
            header += f"  v{self._result.version:03d}"

        # Pick the status banner colour by exit code.
        if execution.timed_out:
            status = ("TIMED OUT", "modal-error")
        elif execution.compile_error:
            status = (f"compile error", "modal-error")
        elif execution.exit_code == 0:
            status = (f"exit 0  (OK)", "modal-success")
        else:
            status = (f"exit {execution.exit_code}", "modal-error")

        body_rows = [
            Static(header, classes="modal-title"),
            Static(status[0], classes=status[1]),
            Static(f"file: {self._result.file_path}", classes="modal-section"),
        ]

        # stdout block
        if execution.stdout:
            body_rows.append(Static("STDOUT", classes="modal-section"))
            stdout_text = execution.stdout.rstrip("\n") or "(empty)"
            body_rows.append(
                VerticalScroll(
                    *(Static(line, classes="output-line")
                      for line in stdout_text.splitlines() or ["(empty)"]),
                    id="run-output",
                )
            )

        # stderr block
        if execution.stderr and not execution.timed_out:
            body_rows.append(Static("STDERR", classes="modal-section"))
            stderr_text = execution.stderr.rstrip("\n")
            body_rows.append(
                VerticalScroll(
                    *(Static(line, classes="stderr-line")
                      for line in stderr_text.splitlines()),
                    id="run-stderr",
                )
            )

        # compile error block (often duplicates stderr, but make it explicit)
        if execution.compile_error and execution.compile_error != execution.stderr:
            body_rows.append(Static("COMPILE ERROR", classes="modal-section"))
            body_rows.append(
                VerticalScroll(
                    *(Static(line, classes="stderr-line")
                      for line in execution.compile_error.splitlines()),
                    id="run-compile-error",
                )
            )

        body_rows.append(Static("esc / q close", classes="modal-footer"))
        yield Vertical(*body_rows, classes="modal-card")
