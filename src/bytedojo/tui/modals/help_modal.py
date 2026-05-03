"""
Help modal - Display keyboard shortcuts and help information.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static


class HelpModal(ModalScreen):
    """Modal showing keyboard shortcuts and help."""

    CSS = """
    HelpModal {
        align: center middle;
    }

    #help-container {
        width: 70;
        height: auto;
        max-height: 80%;
        background: #161b22;
        border: tall #6a2a8a;
        padding: 0;
    }

    #help-header {
        width: 100%;
        height: 3;
        background: #6a2a8a;
        padding: 0 2;
    }

    #help-title {
        width: 1fr;
        color: #e6edf3;
        text-style: bold;
        padding: 1 0;
    }

    #help-close {
        width: 3;
        text-align: center;
        color: #e6edf3;
        padding: 1 0;
    }

    #help-close:hover {
        color: #c43a3a;
    }

    #help-body {
        width: 100%;
        height: auto;
        max-height: 50;
        padding: 1 2;
    }

    .help-section {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .section-title {
        width: 100%;
        color: #6a2a8a;
        text-style: bold;
        padding: 1 0 0 0;
        border-bottom: solid #21262d;
    }

    .shortcut-row {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    .shortcut-key {
        width: 12;
        color: #58a6ff;
        text-style: bold;
    }

    .shortcut-desc {
        width: 1fr;
        color: #e6edf3;
    }

    #help-footer {
        width: 100%;
        height: 2;
        background: #21262d;
        padding: 0 2;
        color: #8b949e;
        content-align: center middle;
    }

    .brand-text {
        color: #6a2a8a;
        text-style: bold;
    }

    .ice-text {
        color: #58a6ff;
    }

    .fire-text {
        color: #f06060;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
        ("question_mark", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            # Header
            with Horizontal(id="help-header"):
                yield Static("Keyboard Shortcuts", id="help-title")
                yield Static("×", id="help-close")

            # Body
            with ScrollableContainer(id="help-body"):
                # Navigation
                with Vertical(classes="help-section"):
                    yield Static("Navigation", classes="section-title")
                    yield self._shortcut("1", "Dashboard tab")
                    yield self._shortcut("2", "Problems tab")
                    yield self._shortcut("3", "Review tab")
                    yield self._shortcut("4", "Settings tab")
                    yield self._shortcut("Tab", "Next element")
                    yield self._shortcut("Shift+Tab", "Previous element")

                # Global Actions
                with Vertical(classes="help-section"):
                    yield Static("Global Actions", classes="section-title")
                    yield self._shortcut("F", "Fetch problems")
                    yield self._shortcut("R", "Run current problem")
                    yield self._shortcut("G", "Grade problem")
                    yield self._shortcut("P", "Pick random problem")
                    yield self._shortcut("?", "Show this help")
                    yield self._shortcut("Q", "Quit application")

                # Problems Browser
                with Vertical(classes="help-section"):
                    yield Static("Problems Browser", classes="section-title")
                    yield self._shortcut("Enter", "View problem details")
                    yield self._shortcut("j / Down", "Next problem")
                    yield self._shortcut("k / Up", "Previous problem")
                    yield self._shortcut("h / Left", "Previous page")
                    yield self._shortcut("l / Right", "Next page")
                    yield self._shortcut("/", "Search problems")

                # Review Session
                with Vertical(classes="help-section"):
                    yield Static("Review Session", classes="section-title")
                    yield self._shortcut("P", "Mark as Passed")
                    yield self._shortcut("F", "Mark as Failed")
                    yield self._shortcut("S", "Skip problem")
                    yield self._shortcut("O", "Open solution file")
                    yield self._shortcut("L", "Open LeetCode URL")
                    yield self._shortcut("N", "Add notes")

                # Modals
                with Vertical(classes="help-section"):
                    yield Static("Modals & Dialogs", classes="section-title")
                    yield self._shortcut("Escape", "Close modal")
                    yield self._shortcut("Enter", "Confirm/Submit")

            # Footer
            with Horizontal(id="help-footer"):
                yield Static("ByteDojo - Practice makes perfect")

    def _shortcut(self, key: str, description: str) -> Horizontal:
        """Create a shortcut row."""
        row = Horizontal(classes="shortcut-row")
        row.compose_add_child(Static(key, classes="shortcut-key"))
        row.compose_add_child(Static(description, classes="shortcut-desc"))
        return row

    def on_click(self, event) -> None:
        """Handle clicks on close button."""
        try:
            widget = self.query_one("#help-close")
            if widget and event.widget == widget:
                self.action_close()
        except Exception:
            pass

    def action_close(self) -> None:
        """Close the modal."""
        self.app.pop_screen()
