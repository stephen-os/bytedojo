"""
Stats card widget for displaying metrics.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.widget import Widget


class StatsCard(Widget):
    """A card displaying a statistic with label."""

    DEFAULT_CSS = """
    StatsCard {
        width: 1fr;
        height: auto;
        min-height: 7;
        padding: 1 2;
        background: #161b22;
        border: tall #21262d;
    }

    StatsCard:hover {
        background: #21262d;
    }

    StatsCard .card-title {
        text-style: bold;
        color: #8b949e;
        text-align: center;
        padding-bottom: 1;
    }

    StatsCard .card-value {
        text-style: bold;
        color: #e6edf3;
        text-align: center;
        height: 2;
    }

    StatsCard .card-value.large {
        text-style: bold;
    }

    StatsCard .card-subtitle {
        color: #8b949e;
        text-align: center;
    }

    StatsCard.success .card-value {
        color: #58a6ff;
    }

    StatsCard.warning .card-value {
        color: #f06060;
    }

    StatsCard.error .card-value {
        color: #c43a3a;
    }

    StatsCard.accent .card-value {
        color: #6a2a8a;
    }
    """

    def __init__(
        self,
        title: str,
        value: str | int,
        subtitle: str = "",
        variant: str = "",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.value = str(value)
        self.subtitle = subtitle
        if variant:
            self.add_class(variant)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.title, classes="card-title")
            yield Static(self.value, classes="card-value large")
            if self.subtitle:
                yield Static(self.subtitle, classes="card-subtitle")
