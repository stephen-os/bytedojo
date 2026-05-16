"""
Footer — verbatim port of gh-dash's bottom status bar.

Source: `clone/gh-dash/internal/tui/components/footer/footer.go` View()
+ `context/styles.go` s.Common.FooterStyle + s.ViewSwitcher.*

Layout:
  [view-switcher pills] left-section   <spacer>   right-section [donate] [? help]

Single 1-row bar on the SelectedBackground. View-switcher pills sit on
a SecondaryBorder background — active view in primary-text bold, inactive
in faint-text. Right-pinned: donate pill (warning fg, underlined) +
`? help` pill (faint-text bg, inverted-text fg).
"""

from dataclasses import dataclass
from typing import List

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


@dataclass
class FooterView:
    """One view-switcher entry: `icon label` rendered as a pill."""
    label: str
    active: bool = False


class Footer(Horizontal):
    """Bottom status bar with view-switcher pills + status + help/donate."""

    def __init__(
        self,
        views: List[FooterView],
        left: str = "",
        right: str = "",
    ) -> None:
        super().__init__()
        self._views = views
        self._left = left
        self._right = right

    def compose(self) -> ComposeResult:
        # View switcher block (left)
        for i, view in enumerate(self._views):
            if i > 0:
                yield Static("│", classes="view-separator")
            klass = "view-active" if view.active else "view-inactive"
            yield Static(view.label, classes=klass)

        # Left status section (e.g. repo · user · updated)
        if self._left:
            yield Static(self._left, classes="footer-left", id="footer-left")

        # Spacer pushes right side to the right
        yield Static("", classes="footer-spacer")

        # Right status section (e.g. PR 1/3 (fetched 3))
        if self._right:
            yield Static(self._right, classes="footer-right", id="footer-right")

        # Pinned pills on the far right
        yield Static("♥ donate", classes="donate-pill")
        yield Static("? help", classes="help-pill")

    def set_left(self, text: str) -> None:
        self._left = text
        try:
            self.query_one("#footer-left", Static).update(text)
        except Exception:
            pass   # widget not mounted yet

    def set_right(self, text: str) -> None:
        self._right = text
        try:
            self.query_one("#footer-right", Static).update(text)
        except Exception:
            pass
