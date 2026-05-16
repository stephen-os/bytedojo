"""
DiscoverScreen — browse the local LeetCode catalog and see what's
already registered.

Lays out the same chrome as PractiseScreen (TabsBar / SearchBox /
Footer) and uses a DataTable for the catalog list since it can be
thousands of rows and DataTable virtualises its rendering.

Actions (this pass: keybind stubs that notify; real fetch wiring lands
in the next pass alongside the FetchModal):

    enter / f  → fetch the highlighted problem
    p          → pick a random matching problem
    /          → focus the search box
    1 / 2 / 3  → switch mode (handled by the App)
    ?          → help overlay
"""

from typing import Any, List

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.tui.store import CatalogEntry, DiscoverStore
from bytedojo.tui.theme import (
    FAINT_TEXT,
    PRIMARY_TEXT,
)
from bytedojo.tui.widgets import (
    Footer,
    FooterView,
    SearchBox,
    Sidebar,
    SidebarData,
    SidebarSection,
    Tab,
    TabsBar,
    difficulty_markup,
    tag_pill_markup,
)


# How many rows we render up front. The full catalog can be 3000+;
# DataTable still virtualises but we cap to avoid eating startup time on
# layout/measure. Search + filter narrow this further once wired.
_INITIAL_ROW_LIMIT = 500


_LANG_SHORT = {
    CodeLanguage.PYTHON: "py",
    CodeLanguage.JAVA:   "jv",
    CodeLanguage.CPP:    "cc",
}


def _registered_marker(entry: CatalogEntry) -> str:
    """Render a compact registration indicator: ``·`` / ``◐ py`` / ``● 3``."""
    n = len(entry.registered_langs)
    if n == 0:
        return "·"
    if n == 3:
        return "● all"
    return "◐ " + " ".join(_LANG_SHORT.get(l, "?") for l in sorted(entry.registered_langs, key=lambda l: l.value))


class DiscoverScreen(Screen):
    """Catalog browser mode."""

    BINDINGS = [
        Binding("enter", "fetch_selected", "Fetch"),
        Binding("f",     "fetch_selected", "Fetch", show=False),
        Binding("p",     "pick_random",    "Pick random"),
        Binding("slash", "focus_search",   "Search"),
        Binding("r",     "refresh",        "Refresh"),
    ]

    DEFAULT_CSS = """
    DiscoverScreen {
        layout: vertical;
    }

    DiscoverScreen #discover-body {
        height: 1fr;
        layout: horizontal;
    }

    DiscoverScreen DataTable {
        width: 1fr;
        background: $background;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._store: DiscoverStore | None = None
        self._entries: List[CatalogEntry] = []

    # ----------------------------------------------------------------- lifecycle

    def on_mount(self) -> None:
        repo = getattr(self.app, "repo", None)
        self._store = DiscoverStore(repo)
        self._entries = self._store.entries[:_INITIAL_ROW_LIMIT]

        table: DataTable = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = False
        table.add_column("ID",     width=5,  key="id")
        table.add_column("D",      width=1,  key="diff")
        table.add_column("Title",  width=44, key="title")
        table.add_column("Tags",   width=42, key="tags")
        table.add_column("Done",   width=11, key="done")

        for entry in self._entries:
            table.add_row(
                Text(str(entry.problem_id), style=FAINT_TEXT),
                Text.from_markup(difficulty_markup(entry.difficulty)),
                Text(entry.title, style=PRIMARY_TEXT),
                _build_tags_cell(entry.tags),
                _build_done_cell(entry),
            )

        # Initial sidebar focuses the first entry.
        if self._entries:
            self._update_sidebar(self._entries[0])
            self._update_footer(self._entries[0])

    def compose(self) -> ComposeResult:
        yield TabsBar(
            tabs=[
                Tab(label="Practise"),
                Tab(label="Discover"),
                Tab(label="Health"),
            ],
            active_index=1,
            version="bytedojo v0.1.0",
        )
        yield SearchBox(query="(coming soon)")

        yield Horizontal(
            DataTable(id="catalog-table"),
            Sidebar(SidebarData(
                header="catalog",
                title="Discover",
                byline=f"{len(self._entries)} problems shown",
                sections=[SidebarSection(title="HOW", body=(
                    "Highlight a problem and press Enter to open the "
                    "Fetch dialog (coming soon).\n\n"
                    "Press 'p' to pick a random problem."
                ))],
            )),
            id="discover-body",
        )

        yield Footer(
            views=[
                FooterView(label=" 1 Practise"),
                FooterView(label=" 2 Discover", active=True),
                FooterView(label=" 3 Health"),
            ],
            left="catalog",
            right="Discover —",
        )

    # ----------------------------------------------------------------- handlers

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._entries):
            entry = self._entries[idx]
            self._update_sidebar(entry)
            self._update_footer(entry)

    # ----------------------------------------------------------------- actions

    def action_fetch_selected(self) -> None:
        idx = self._cursor_index()
        if idx is None:
            return
        entry = self._entries[idx]
        repo = getattr(self.app, "repo", None)
        if repo is None or not repo.is_initialized:
            self.notify("no .dojo repository — run `dojo init` first.",
                        title="dojo fetch", severity="error")
            return

        # Local import to avoid a circular if FetchModal ever pulls Discover.
        from bytedojo.tui.modals import FetchModal

        def _on_close(_result):
            # Refresh the catalog list so the just-fetched entry shows the
            # new "registered" indicator immediately.
            self.action_refresh()

        self.app.push_screen(
            FetchModal(repo, prefilled_id=entry.problem_id),
            _on_close,
        )

    def action_pick_random(self) -> None:
        if not self._entries:
            return
        import random
        idx = random.randrange(len(self._entries))
        table: DataTable = self.query_one(DataTable)
        table.move_cursor(row=idx)
        self.notify(f"Random: #{self._entries[idx].problem_id} {self._entries[idx].title}",
                    title="pick", severity="information")

    def action_focus_search(self) -> None:
        # The SearchBox is display-only this pass; just notify.
        self.notify("Search wiring coming next pass", title="/", severity="information")

    def action_refresh(self) -> None:
        repo = getattr(self.app, "repo", None)
        self._store = DiscoverStore(repo)
        self._entries = self._store.entries[:_INITIAL_ROW_LIMIT]
        table: DataTable = self.query_one(DataTable)
        table.clear()
        for entry in self._entries:
            table.add_row(
                Text(str(entry.problem_id), style=FAINT_TEXT),
                Text.from_markup(difficulty_markup(entry.difficulty)),
                Text(entry.title, style=PRIMARY_TEXT),
                _build_tags_cell(entry.tags),
                _build_done_cell(entry),
            )
        self.notify("Catalog refreshed", title="r", severity="information")

    # ----------------------------------------------------------------- helpers

    def _cursor_index(self) -> int | None:
        table: DataTable = self.query_one(DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return None
        if table.cursor_row >= len(self._entries):
            return None
        return table.cursor_row

    def _update_sidebar(self, entry: CatalogEntry) -> None:
        registered = (
            "Not yet fetched" if not entry.registered_langs
            else "Registered in: " + ", ".join(
                l.value for l in sorted(entry.registered_langs, key=lambda l: l.value)
            )
        )
        self.query_one(Sidebar).set_data(SidebarData(
            header=f"#{entry.problem_id}",
            title=entry.title,
            byline=entry.difficulty.value,
            sections=[
                SidebarSection(title="TAGS",   body=", ".join(entry.tags) if entry.tags else "—"),
                SidebarSection(title="REGISTERED", body=registered),
                SidebarSection(title="DESCRIPTION",
                               body=(entry.description[:280] + "…") if len(entry.description) > 280 else (entry.description or "—")),
            ],
        ))

    def _update_footer(self, entry: CatalogEntry) -> None:
        self.query_one(Footer).set_left(f"catalog  ·  #{entry.problem_id} {entry.title}")


# --------------------------------------------------------------------------- #
# Cell renderers                                                              #
# --------------------------------------------------------------------------- #

def _build_tags_cell(tags: list[str], limit: int = 4) -> Text:
    """Concatenate up to ``limit`` tag pills; overflow shows ``+N``."""
    out = Text()
    if not tags:
        return out
    visible = tags[:limit]
    for i, t in enumerate(visible):
        if i > 0:
            out.append(" ")
        out.append_text(Text.from_markup(tag_pill_markup(t)))
    if len(tags) > limit:
        out.append(f"  +{len(tags) - limit}", style=FAINT_TEXT)
    return out


def _build_done_cell(entry: CatalogEntry) -> Text:
    """Render the registration indicator + which langs are registered."""
    return Text(_registered_marker(entry), style=FAINT_TEXT)
