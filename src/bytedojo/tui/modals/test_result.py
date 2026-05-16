"""
TestResultModal — display a TestServiceResult: summary banner + per-case rows.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from bytedojo.services.test_service import (
    TestCaseResult,
    TestRunResult,
    TestServiceResult,
)
from bytedojo.tui.modals._base import BASE_MODAL_CSS


class TestResultModal(ModalScreen[None]):
    """Modal summarising a `dojo test` run."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("q", "app.pop_screen", "Close"),
    ]

    DEFAULT_CSS = BASE_MODAL_CSS + """
    TestResultModal .modal-card {
        width: 100;
        max-height: 32;
    }

    TestResultModal #test-cases {
        height: auto;
        max-height: 20;
        padding: 1 0;
    }

    TestResultModal .case-pass {
        color: green;
    }

    TestResultModal .case-fail {
        color: red;
    }

    TestResultModal .case-error {
        color: $warning;
    }
    """

    def __init__(self, result: TestServiceResult, title_hint: str = "") -> None:
        super().__init__()
        self._result = result
        self._title_hint = title_hint

    def compose(self) -> ComposeResult:
        # Hard pre-flight failure (no toolchain / no file / no bundle).
        if self._result.failed:
            yield Vertical(
                Static("dojo test — failed", classes="modal-title"),
                Static(self._result.error or "unknown error",
                       classes="modal-error"),
                Static("esc / q close", classes="modal-footer"),
                classes="modal-card",
            )
            return

        # Soft skip — bundle empty.
        if self._result.skipped:
            yield Vertical(
                Static("dojo test — skipped", classes="modal-title"),
                Static(self._result.skip_reason or "skipped",
                       classes="modal-section"),
                Static("esc / q close", classes="modal-footer"),
                classes="modal-card",
            )
            return

        run: TestRunResult = self._result.run_result
        problem = self._result.problem
        header = (
            f"dojo test  ·  #{problem.problem_id} {problem.title}  ·  "
            f"{problem.language.value}"
        )
        if self._result.version is not None:
            header += f"  v{self._result.version:03d}"

        # Status banner.
        status_label = run.status.upper()
        if run.status == "passed":
            status_class = "modal-success"
        elif run.status == "error":
            status_class = "modal-error"
        elif run.status == "failed":
            status_class = "modal-error"
        else:
            status_class = "modal-section"
        summary = (
            f"{status_label}  ·  passed {run.passed_count}/{run.total_cases}"
            f"  ·  failed {run.failed_count}"
            f"  ·  errors {run.error_count}"
        )

        body_rows = [
            Static(header, classes="modal-title"),
            Static(summary, classes=status_class),
        ]

        # Compile-error fast path.
        if run.compile_error:
            body_rows.append(Static("COMPILE ERROR", classes="modal-section"))
            body_rows.append(
                VerticalScroll(
                    *(Static(line, classes="case-error")
                      for line in run.compile_error.splitlines()),
                    id="test-compile-error",
                )
            )
            body_rows.append(Static("esc / q close", classes="modal-footer"))
            yield Vertical(*body_rows, classes="modal-card")
            return

        # Runtime-error banner.
        if run.runtime_error:
            body_rows.append(Static("RUNTIME ERROR", classes="modal-section"))
            body_rows.append(Static(run.runtime_error, classes="case-error"))

        # Per-case detail (focus on failures for terseness).
        failed_cases = [c for c in run.case_results if not c.passed]
        if failed_cases:
            body_rows.append(Static(
                f"FAILING CASES ({len(failed_cases)})",
                classes="modal-section",
            ))
            body_rows.append(
                VerticalScroll(
                    *(_format_case(c) for c in failed_cases),
                    id="test-cases",
                )
            )
        elif run.case_results:
            body_rows.append(Static("All cases passed.", classes="case-pass"))

        body_rows.append(Static("esc / q close", classes="modal-footer"))
        yield Vertical(*body_rows, classes="modal-card")


def _format_case(case: TestCaseResult) -> Static:
    if case.timed_out:
        label = f"  #{case.case_number}  TIMED OUT"
        cls = "case-error"
    elif case.error:
        label = f"  #{case.case_number}  ERROR  {case.error[:60]}"
        cls = "case-error"
    else:
        label = (
            f"  #{case.case_number}  FAIL  "
            f"input={case.input_str[:30]!r}  "
            f"expected={case.expected[:20]}  actual={case.actual[:20]}"
        )
        cls = "case-fail"
    return Static(label, classes=cls)
