"""
Sidebar — verbatim port of gh-dash's right-pane detail view.

Source: `clone/gh-dash/internal/tui/components/sidebar/sidebar.go` +
`context/styles.go` s.Sidebar.Root (BorderLeft "│" only, padding 0 2).

Layout (top → bottom):
  ─── HEADER ────────────                  e.g. "leetcode · #1"
   <title> (bold, primary)                 e.g. "Two Sum"
   <byline> (faint)                        e.g. "Easy · python · v003"

   ─── SECTION ─────                       (warning-coloured, bold)
   body text in FaintText
   ...
   ─── SECTION ─────
   ...

The whole pane has a single `│` left border in PrimaryBorder colour.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from textual.containers import Vertical
from textual.widgets import Static


@dataclass
class SidebarSection:
    """One titled section in the sidebar body."""
    title: str
    body: str   # multi-line; rendered as a single Static


@dataclass
class SidebarData:
    """Everything the sidebar renders."""
    header: str = ""               # top breadcrumb line, e.g. "leetcode · #1"
    title: str = ""                # bold title, e.g. "Two Sum"
    byline: str = ""               # `<difficulty> · <language> · <version>`
    sections: List[SidebarSection] = field(default_factory=list)


class Sidebar(Vertical):
    """Right-side detail view. Single │ border on the left."""

    def __init__(self, data: Optional[SidebarData] = None) -> None:
        super().__init__()
        self._data = data or SidebarData(title="Select a problem")

    def compose(self):
        yield from self._build(self._data)

    def set_data(self, data: SidebarData) -> None:
        self._data = data
        self.remove_children()
        widgets = list(self._build(data))
        if widgets:
            self.mount_all(widgets)

    def _build(self, d: SidebarData):
        if d.header:
            yield Static(d.header, classes="sidebar-header")
        if d.title:
            yield Static(d.title, classes="sidebar-title")
        if d.byline:
            yield Static(d.byline, classes="sidebar-byline")
        for section in d.sections:
            yield Static(section.title, classes="sidebar-section-head")
            yield Static(section.body, classes="sidebar-body")
