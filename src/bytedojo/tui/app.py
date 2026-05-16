"""
ByteDojo TUI Application.

Loads the repo on mount, registers all three modes (Practise / Discover /
Health), and binds the global keys for mode switching + help overlay.
Per-mode keybinds live on each Screen.
"""

from pathlib import Path
from typing import Optional

from textual.app import App
from textual.binding import Binding

from bytedojo.core.logger import setup_logger
from bytedojo.core.repository import Repository
from bytedojo.tui.modals.help import HelpModal
from bytedojo.tui.screens import DiscoverScreen, HealthScreen, PractiseScreen
from bytedojo.tui.theme import THEME_CSS


class DojoApp(App):
    """ByteDojo TUI Application."""

    TITLE = "ByteDojo"
    SUB_TITLE = "Practice Tracker"

    CSS = THEME_CSS

    SCREENS = {
        "practise": PractiseScreen,
        "discover": DiscoverScreen,
        "health":   HealthScreen,
    }

    BINDINGS = [
        Binding("1", "switch_mode('practise')", "Practise", priority=True),
        Binding("2", "switch_mode('discover')", "Discover", priority=True),
        Binding("3", "switch_mode('health')",   "Health",   priority=True),
        Binding("question_mark", "help", "Help", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    #: Repository for the cwd. Loaded once on mount; screens read it via
    #: ``self.app.repo``. ``None`` when no .dojo exists anywhere up the
    #: tree (Discover / Health still work; Practise renders an empty state).
    repo: Optional[Repository] = None

    def on_mount(self) -> None:
        # Ensure the core logger exists. The CLI's `dojo enter` calls
        # setup_logger() before constructing the App, but direct uses
        # (headless tests, embedded launches) skip that — make the TUI
        # self-sufficient instead of crashing in Repository.find().
        try:
            from bytedojo.core.logger import get_logger
            get_logger()
        except RuntimeError:
            setup_logger(debug=False)

        self.repo = Repository.find(Path.cwd())
        self.push_screen("practise")

    # ----------------------------------------------------------------- actions

    def action_switch_mode(self, mode: str) -> None:
        """Replace the current screen with the named mode."""
        if isinstance(self.screen, HelpModal):
            # Close the help overlay before swapping under it.
            self.pop_screen()
        self.switch_screen(mode)

    def action_help(self) -> None:
        """Push the help overlay scoped to the current screen's keybinds."""
        # Don't stack help on top of help.
        if isinstance(self.screen, HelpModal):
            return
        self.push_screen(HelpModal(self.screen))
