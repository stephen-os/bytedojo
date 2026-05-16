"""
HealthScreen — environment, settings, and stats. Read-mostly mode.

Three vertically-stacked sections:

1. STATUS   — bytedojo version, python interpreter, platform, repo
              path, toolchain pills (one per registered language).
2. SETTINGS — current settings as a flat key/value table.
3. STATS    — problem counts overall + per difficulty + per language.

No interactive editing this pass; the design doc says "Enter to edit"
on a setting row but that's a follow-up.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

from bytedojo.tui.store import HealthStore
from bytedojo.tui.theme import (
    ERROR_TEXT,
    FAINT_TEXT,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SUCCESS_TEXT,
    WARNING_TEXT,
)
from bytedojo.tui.widgets import (
    Footer,
    FooterView,
    Tab,
    TabsBar,
)


class HealthScreen(Screen):
    """Status + Settings + Stats."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    HealthScreen {
        layout: vertical;
    }

    HealthScreen #health-body {
        height: 1fr;
        padding: 1 2;
        background: $background;
    }

    HealthScreen .section-title {
        text-style: bold;
        padding: 1 0 0 0;
    }

    HealthScreen .section-line {
        padding: 0 0 0 2;
    }

    HealthScreen .section-blank {
        height: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._store: HealthStore | None = None

    # ----------------------------------------------------------------- lifecycle

    def compose(self) -> ComposeResult:
        yield TabsBar(
            tabs=[
                Tab(label="Practise"),
                Tab(label="Discover"),
                Tab(label="Health"),
            ],
            active_index=2,
            version="bytedojo v0.1.0",
        )

        yield VerticalScroll(id="health-body")

        yield Footer(
            views=[
                FooterView(label=" 1 Practise"),
                FooterView(label=" 2 Discover"),
                FooterView(label=" 3 Health", active=True),
            ],
            left="health",
            right="Health",
        )

    def on_mount(self) -> None:
        repo = getattr(self.app, "repo", None)
        self._store = HealthStore(repo)
        self._render_body()

    # ----------------------------------------------------------------- actions

    def action_refresh(self) -> None:
        repo = getattr(self.app, "repo", None)
        self._store = HealthStore(repo)
        self._render_body()
        self.notify("Health refreshed", title="r", severity="information")

    # ----------------------------------------------------------------- render

    def _render_body(self) -> None:
        body = self.query_one("#health-body", VerticalScroll)
        body.remove_children()
        data = self._store.data if self._store else None
        if data is None:
            body.mount(Static("Loading…"))
            return

        # --- STATUS -----------------------------------------------------
        body.mount(Static(Text("STATUS", style=f"{PRIMARY_TEXT} bold"),
                          classes="section-title"))
        report = data.system_report
        body.mount(_kv_row("ByteDojo",  report.bytedojo_version))
        body.mount(_kv_row("Python",    report.python_version))
        body.mount(_kv_row("Executable", report.python_executable))
        body.mount(_kv_row("Platform",  f"{report.platform_name}  ({report.platform_id})"))
        body.mount(_kv_row("Repository",
                           str(report.repository_path) if report.repository_path
                           else "not in a .dojo repository"))

        # Toolchain rows
        body.mount(Static("", classes="section-blank"))
        body.mount(Static(Text("TOOLCHAINS", style=f"{PRIMARY_TEXT} bold"),
                          classes="section-title"))
        for status in report.toolchains:
            marker = (
                Text("[OK]", style=SUCCESS_TEXT)
                if status.found
                else Text("[NO]", style=ERROR_TEXT)
            )
            lang = status.language.value
            line = Text("  ")
            line.append_text(marker)
            line.append(f"  {lang:<10}  ", style=SECONDARY_TEXT)
            if status.found:
                line.append(status.version or "version unknown", style=PRIMARY_TEXT)
            else:
                missing = ", ".join(status.missing) or "unknown"
                line.append(f"missing: {missing}", style=ERROR_TEXT)
                if status.install_hint:
                    line.append(f"   {status.install_hint}", style=WARNING_TEXT)
            body.mount(Static(line))

        # --- SETTINGS ---------------------------------------------------
        body.mount(Static("", classes="section-blank"))
        body.mount(Static(Text("SETTINGS", style=f"{PRIMARY_TEXT} bold"),
                          classes="section-title"))
        if not data.settings:
            body.mount(Static(Text("  no .dojo repository here", style=FAINT_TEXT)))
        else:
            for k, v in data.settings.items():
                body.mount(_kv_row(k, v))

        # --- STATS ------------------------------------------------------
        body.mount(Static("", classes="section-blank"))
        body.mount(Static(Text("STATS", style=f"{PRIMARY_TEXT} bold"),
                          classes="section-title"))
        if not data.stats:
            body.mount(Static(Text("  no .dojo repository here", style=FAINT_TEXT)))
        else:
            for k, v in data.stats.items():
                body.mount(_kv_row(k, v))

        # --- REVIEWS ----------------------------------------------------
        body.mount(Static("", classes="section-blank"))
        body.mount(Static(Text("REVIEWS", style=f"{PRIMARY_TEXT} bold"),
                          classes="section-title"))
        due_label = "due today" if data.review_due == 1 else "due today"
        body.mount(_kv_row("Reviews", f"{data.review_due} {due_label}"))


def _kv_row(key: str, value: str) -> Static:
    line = Text("  ")
    line.append(f"{key:<22}", style=SECONDARY_TEXT)
    line.append(value, style=PRIMARY_TEXT)
    return Static(line, classes="section-line")
