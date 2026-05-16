"""
TabsBar — verbatim port of gh-dash's tabs row.

Source: `clone/gh-dash/internal/tui/components/tabs/tabs.go`
+ `internal/tui/context/styles.go` s.Tabs.{Tab, ActiveTab,
TabSeparator, TabsRow}.

Layout:
  [Tab1 (N)] │ [Tab2 (N)] │ [Tab3 (N)]                       vX.Y.Z

The active tab is bold + primary-text colour against the selected
background. Inactive tabs are dim faint-text. The `│` separator is
secondary-border colour. Right-aligned version label uses
secondary-text. The whole row has a heavy bottom border in
primary-border.
"""

from dataclasses import dataclass
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


@dataclass
class Tab:
    """One tab in the tabs row.

    `count` is rendered as `(N)` after the label, matching gh-dash's
    SectionsShowCount config option (line 141 of tabs.go).
    """
    label: str
    count: Optional[int] = None


class TabsBar(Horizontal):
    """Top row of section tabs with version label pinned right."""

    DEFAULT_CSS = ""   # All styles live in theme.THEME_CSS (.tabs-row family)

    def __init__(
        self,
        tabs: List[Tab],
        active_index: int = 0,
        version: str = "",
    ) -> None:
        super().__init__()
        self.add_class("tabs-row")
        self._tabs = tabs
        self._active_index = active_index
        self._version = version

    def compose(self) -> ComposeResult:
        for i, tab in enumerate(self._tabs):
            if i > 0:
                yield Static("│", classes="tab-separator")

            label = tab.label
            if tab.count is not None:
                label = f"{label} ({tab.count})"

            klass = "tab-active" if i == self._active_index else "tab"
            yield Static(label, classes=klass)

        yield Static("", classes="tabs-spacer")
        if self._version:
            yield Static(self._version, classes="tabs-version")
