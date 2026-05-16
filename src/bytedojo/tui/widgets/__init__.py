"""ByteDojo TUI widgets — verbatim port of gh-dash component shapes."""

from bytedojo.tui.widgets.footer import Footer, FooterView
from bytedojo.tui.widgets.labels import (
    difficulty_markup,
    language_label,
    problem_label,
    status_glyph_markup,
    tag_pill_markup,
    tags_markup,
    version_label,
)
from bytedojo.tui.widgets.problem_tree import ProblemTree
from bytedojo.tui.widgets.search_box import SearchBox
from bytedojo.tui.widgets.sidebar import Sidebar, SidebarData, SidebarSection
from bytedojo.tui.widgets.tabs_bar import Tab, TabsBar

__all__ = [
    "TabsBar", "Tab",
    "SearchBox",
    "ProblemTree",
    "Sidebar", "SidebarData", "SidebarSection",
    "Footer", "FooterView",
    "problem_label", "language_label", "version_label",
    "tag_pill_markup", "tags_markup",
    "difficulty_markup", "status_glyph_markup",
]
