"""
Tab bar widget for main navigation.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message


class Tab(Static):
    """A single tab in the tab bar."""

    DEFAULT_CSS = """
    Tab {
        width: auto;
        height: 3;
        padding: 0 3;
        content-align: center middle;
        text-style: bold;
        color: #8b949e;
        background: #161b22;
        border-bottom: tall #161b22;
    }

    Tab:hover {
        color: #e6edf3;
        background: #21262d;
    }

    Tab.active {
        color: #6a2a8a;
        background: #0d1117;
        border-bottom: tall #6a2a8a;
    }

    Tab .shortcut {
        color: #8b949e;
        text-style: none;
    }

    Tab.active .shortcut {
        color: #6a2a8a;
    }
    """

    def __init__(
        self,
        label: str,
        tab_id: str,
        shortcut: str = "",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.label = label
        self.tab_id = tab_id
        self.shortcut = shortcut

    def compose(self) -> ComposeResult:
        if self.shortcut:
            yield Static(f"{self.label} [{self.shortcut}]")
        else:
            yield Static(self.label)

    def on_click(self) -> None:
        """Handle tab click."""
        self.post_message(TabBar.TabSelected(self.tab_id))


class TabBar(Widget):
    """Navigation tab bar."""

    DEFAULT_CSS = """
    TabBar {
        width: 100%;
        height: 3;
        background: #161b22;
        dock: top;
    }

    TabBar Horizontal {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    """

    active_tab: reactive[str] = reactive("dashboard")

    class TabSelected(Message):
        """Message sent when a tab is selected."""

        def __init__(self, tab_id: str) -> None:
            self.tab_id = tab_id
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tabs = [
            ("Dashboard", "dashboard", "1"),
            ("Problems", "problems", "2"),
            ("Review", "review", "3"),
            ("Settings", "settings", "4"),
        ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            for label, tab_id, shortcut in self.tabs:
                tab = Tab(label, tab_id, shortcut, id=f"tab-{tab_id}")
                if tab_id == self.active_tab:
                    tab.add_class("active")
                yield tab

    def watch_active_tab(self, old_tab: str, new_tab: str) -> None:
        """Update tab styling when active tab changes."""
        # Guard against being called before widgets are mounted
        if not self.is_mounted:
            return

        try:
            if old_tab:
                old_widget = self.query_one(f"#tab-{old_tab}", Tab)
                old_widget.remove_class("active")

            new_widget = self.query_one(f"#tab-{new_tab}", Tab)
            new_widget.add_class("active")
        except Exception:
            pass

    def on_tab_bar_tab_selected(self, event: TabSelected) -> None:
        """Handle tab selection."""
        self.active_tab = event.tab_id
