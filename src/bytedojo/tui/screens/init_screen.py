"""
Initialization screen for setting up a new dojo repository.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, Vertical, Center

from bytedojo.core.repository import Repository


class InitScreen(Screen):
    """Screen for initializing a new dojo repository."""

    CSS = """
    InitScreen {
        align: center middle;
    }

    #init-container {
        width: 60;
        height: auto;
        padding: 2 4;
        border: solid $primary;
        background: $surface;
    }

    #init-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    #init-description {
        text-align: center;
        color: $text-muted;
        padding-bottom: 2;
    }

    #init-path {
        text-align: center;
        color: $text;
        padding-bottom: 2;
    }

    #init-buttons {
        align: center middle;
        height: auto;
        padding-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("enter", "initialize", "Initialize"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the initialization screen."""
        repo = Repository(Path.cwd())

        yield Header()
        yield Center(
            Container(
                Static("Initialize ByteDojo", id="init-title"),
                Static(
                    "No dojo repository found in this directory.\n"
                    "Create one to start tracking your progress.",
                    id="init-description"
                ),
                Static(f"Location: {repo.root_dir}", id="init-path"),
                Container(
                    Button("Initialize", variant="primary", id="btn-init"),
                    Button("Quit", variant="default", id="btn-quit"),
                    id="init-buttons"
                ),
                id="init-container"
            )
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-init":
            self.action_initialize()
        elif event.button.id == "btn-quit":
            self.app.exit()

    def action_initialize(self) -> None:
        """Initialize the dojo repository."""
        repo = Repository(Path.cwd())

        try:
            repo.initialize()
            self.notify("Dojo initialized successfully!", title="Success")
            # Dismiss this screen and show the main screen
            self.app.pop_screen()
            self.app.push_screen("main")
        except Exception as e:
            self.notify(f"Failed to initialize: {e}", title="Error", severity="error")
