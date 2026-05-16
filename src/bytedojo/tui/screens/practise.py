"""
PractiseScreen — Practise mode. Tree of registered problems backed by
real Repository data.

Tree shape:
    Problem (#1 Two Sum, [array][hash-table])
    ├── python   ●  passed   3 attempts
    │   ├── v003 ● Passed: 56/56  2d
    │   ├── v002 ✗ Passed: 30/56  3d
    │   └── v001 ✗ Passed: 20/56  5d
    ├── java     ○  ungraded 1 attempt
    │   └── v001 ○ —             3d
    └── cpp      ✗  failed   1 attempt
        └── v001 ✗ Passed: 5/56  2d

Expand a problem to see its languages; expand a language to see its
versions. The sidebar shows context-appropriate detail based on which
level is highlighted.

Actions (this pass: keybind stubs that notify; real wiring lands in the
next pass with async progress modals):

    r          → run the focused (problem, language[, version])
    t          → test it
    g          → grade modal (P/F/S)
    v          → review-complete modal (E/G/H)
    o          → open the file in $EDITOR
    /          → focus search (coming next)
    f          → filter palette (coming next)
"""

import os
import subprocess
from typing import Optional, Tuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets.tree import TreeNode

from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.registered_problem import RegisteredProblem
from bytedojo.services.run_service import RunService
from bytedojo.services.test_service import TestService
from bytedojo.tui.modals import (
    GradeModal,
    ReviewCompleteModal,
    RunOutputModal,
    TestResultModal,
)
from bytedojo.tui.store import (
    LanguageEntry,
    PractiseProblem,
    PractiseStore,
    VersionAttempt,
)
from bytedojo.tui.theme import PRIMARY_BORDER, SECONDARY_BORDER, SELECTED_BG
from bytedojo.tui.widgets import (
    Footer,
    FooterView,
    ProblemTree,
    SearchBox,
    Sidebar,
    SidebarData,
    SidebarSection,
    Tab,
    TabsBar,
    language_label,
    problem_label,
    version_label,
)


_DIFF_LABEL = {
    ProblemDifficulty.EASY:   "Easy",
    ProblemDifficulty.MEDIUM: "Medium",
    ProblemDifficulty.HARD:   "Hard",
}


class PractiseScreen(Screen):
    """Practise mode — Problem → Language → Version tree."""

    BINDINGS = [
        # Refresh from disk (also doubles as gh-dash's r).
        Binding("R", "refresh", "Refresh"),
        # Action stubs — show notifications this pass.
        Binding("r", "run_focused",    "Run"),
        Binding("t", "test_focused",   "Test"),
        Binding("g", "grade_focused",  "Grade"),
        Binding("v", "review_focused", "Review complete"),
        Binding("o", "open_focused",   "Open in $EDITOR"),
        # Coming next.
        Binding("slash", "focus_search", "Search"),
        Binding("f",     "open_filter",  "Filter"),
    ]

    DEFAULT_CSS = f"""
    PractiseScreen {{
        layout: vertical;
    }}

    PractiseScreen #practise-body {{
        height: 1fr;
        layout: horizontal;
    }}

    PractiseScreen #practise-list {{
        width: 2fr;
        min-width: 50;
        border-right: solid {PRIMARY_BORDER};
    }}

    PractiseScreen ProblemTree {{
        background: {SELECTED_BG};
        border: none;
    }}

    PractiseScreen ProblemTree > .tree--cursor {{
        background: {SECONDARY_BORDER};
        text-style: bold;
    }}
    """

    def __init__(self) -> None:
        super().__init__()
        self._store: Optional[PractiseStore] = None

    # ----------------------------------------------------------------- compose

    def compose(self) -> ComposeResult:
        # Tab bar — Practise active.
        yield TabsBar(
            tabs=[
                Tab(label="Practise"),
                Tab(label="Discover"),
                Tab(label="Health"),
            ],
            active_index=0,
            version="bytedojo v0.1.0",
        )

        # Active filter query.
        yield SearchBox(query="lang:python")

        # Body: tree + sidebar.
        tree: ProblemTree = ProblemTree("problems", id="problem-tree")
        tree.root.expand()
        tree.show_root = False

        yield Horizontal(
            tree,
            Sidebar(SidebarData(
                header="practise",
                title="Loading…",
                byline="",
                sections=[],
            )),
            id="practise-body",
        )

        # Footer.
        yield Footer(
            views=[
                FooterView(label=" 1 Practise", active=True),
                FooterView(label=" 2 Discover"),
                FooterView(label=" 3 Health"),
            ],
            left="~/dojo",
            right="Practise",
        )

    def on_mount(self) -> None:
        repo = getattr(self.app, "repo", None)
        self._store = PractiseStore(repo)
        self._populate_tree()

    # ----------------------------------------------------------------- populate

    def _populate_tree(self) -> None:
        tree: ProblemTree = self.query_one(ProblemTree)
        tree.clear()
        tree.root.expand()

        problems = self._store.problems if self._store else []

        if not problems:
            self._render_empty_state()
            return

        for problem in problems:
            p_label = problem_label(
                problem_id=problem.problem_id,
                difficulty=problem.difficulty,
                title=problem.title,
                tags=problem.tags,
            )
            p_node = tree.root.add(
                p_label,
                data={
                    "kind":       "problem",
                    "ref":        problem,
                    "problem_id": problem.problem_id,
                    "difficulty": problem.difficulty,
                    "title":      problem.title,
                    "tags":       problem.tags,
                },
            )
            for lang in problem.languages:
                l_label = language_label(
                    language=lang.language,
                    status=lang.status,
                    versions=len(lang.versions),
                )
                l_node = p_node.add(
                    l_label,
                    data={"kind": "language", "problem": problem, "ref": lang},
                )
                for ver in lang.versions:
                    v_label = version_label(
                        version=ver.version,
                        status=ver.status,
                        output=ver.output,
                        when=ver.when,
                    )
                    l_node.add(
                        v_label,
                        data={
                            "kind":     "version",
                            "problem":  problem,
                            "language": lang,
                            "ref":      ver,
                        },
                        allow_expand=False,
                    )

        first = problems[0]
        self.query_one(Sidebar).set_data(_sidebar_for_problem(first))
        self.query_one(Footer).set_left(self._left_for_problem(first))
        self.query_one(Footer).set_right(f"Practise 1/{len(problems)}")

    def _render_empty_state(self) -> None:
        repo = getattr(self.app, "repo", None)
        if repo is None or not repo.is_initialized:
            self.query_one(Sidebar).set_data(SidebarData(
                header="practise",
                title="No .dojo repository",
                byline="run `dojo init` in this directory (or a parent) and come back",
                sections=[SidebarSection(
                    title="HOW",
                    body=(
                        "ByteDojo TUI walks up from the current directory\n"
                        "looking for a .dojo/ folder. None found here.\n\n"
                        "From a shell:\n"
                        "    cd path/to/where/you/want/it\n"
                        "    dojo init\n"
                        "    dojo enter"
                    ),
                )],
            ))
        else:
            self.query_one(Sidebar).set_data(SidebarData(
                header="practise",
                title="No registered problems",
                byline="fetch one to get started",
                sections=[SidebarSection(
                    title="HOW",
                    body=(
                        "From the shell:\n"
                        "    dojo fetch 1\n"
                        "Or switch to Discover (press 2) and pick one."
                    ),
                )],
            ))
        self.query_one(Footer).set_left("~/dojo")
        self.query_one(Footer).set_right("Practise 0/0")

    # ----------------------------------------------------------------- handlers

    def on_tree_node_highlighted(self, event) -> None:
        node: TreeNode = event.node
        if node is None or node.data is None:
            return

        kind = node.data.get("kind")
        if kind == "problem":
            problem: PractiseProblem = node.data["ref"]
            self.query_one(Sidebar).set_data(_sidebar_for_problem(problem))
            self.query_one(Footer).set_left(self._left_for_problem(problem))
        elif kind == "language":
            problem = node.data["problem"]
            lang: LanguageEntry = node.data["ref"]
            self.query_one(Sidebar).set_data(_sidebar_for_language(problem, lang))
            self.query_one(Footer).set_left(self._left_for_language(problem, lang))
        elif kind == "version":
            problem = node.data["problem"]
            lang = node.data["language"]
            ver: VersionAttempt = node.data["ref"]
            self.query_one(Sidebar).set_data(_sidebar_for_version(problem, lang, ver))
            self.query_one(Footer).set_left(self._left_for_version(problem, lang, ver))

    # ----------------------------------------------------------------- actions

    def action_refresh(self) -> None:
        if self._store is not None:
            self._store.refresh()
        self._populate_tree()
        self.notify("Practise refreshed", title="R", severity="information")

    def action_run_focused(self) -> None:
        resolved = self._resolve_action_target()
        if resolved is None:
            return
        registered, version = resolved
        try:
            result = RunService().run_problem(
                self.app.repo, registered, version=version,
            )
        except Exception as e:  # service-side failures should never escape — be defensive
            self.notify(f"run failed: {e}", title="dojo run", severity="error")
            return
        self.app.push_screen(RunOutputModal(result))

    def action_test_focused(self) -> None:
        resolved = self._resolve_action_target()
        if resolved is None:
            return
        registered, version = resolved
        try:
            result = TestService().test_problem(
                self.app.repo, registered, version=version,
            )
        except Exception as e:
            self.notify(f"test failed: {e}", title="dojo test", severity="error")
            return
        self.app.push_screen(TestResultModal(result))
        # The status changed — refresh the tree once the modal closes.
        # We refresh now (cheap) so the underlying tree reflects the new
        # status as soon as esc dismisses the modal.
        if self._store is not None:
            self._store.refresh()
            self._populate_tree()

    def action_grade_focused(self) -> None:
        resolved = self._resolve_action_target()
        if resolved is None:
            return
        registered, _ = resolved
        def _on_close(_status):
            if self._store is not None:
                self._store.refresh()
                self._populate_tree()
        self.app.push_screen(
            GradeModal(self.app.repo, registered),
            _on_close,
        )

    def action_review_focused(self) -> None:
        resolved = self._resolve_action_target()
        if resolved is None:
            return
        registered, _ = resolved
        def _on_close(_quality):
            if self._store is not None:
                self._store.refresh()
                self._populate_tree()
        self.app.push_screen(
            ReviewCompleteModal(self.app.repo, registered),
            _on_close,
        )

    def action_open_focused(self) -> None:
        resolved = self._resolve_action_target()
        if resolved is None:
            return
        registered, _ = resolved
        if not registered.file_path:
            self.notify("no file path recorded for this attempt",
                        title="open", severity="warning")
            return
        path = self.app.repo.root_dir / registered.file_path
        if not path.exists():
            self.notify(f"file not found: {path}", title="open", severity="error")
            return
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
        # Suspend the TUI, run $EDITOR in the foreground, then restore.
        with self.app.suspend():
            try:
                subprocess.run([editor, str(path)], check=False)
            except FileNotFoundError:
                # Editor not installed; tell the user after we restore.
                self.notify(
                    f"$EDITOR not found ({editor!r}). Set $EDITOR and try again.",
                    title="open", severity="error",
                )

    def action_focus_search(self) -> None:
        # SearchBox is a Static today — the real search input lands in the
        # next pass. Surface a hint so the keybind isn't silent.
        self.notify("search input coming next pass", title="/",
                    severity="information")

    def action_open_filter(self) -> None:
        self.notify("filter palette coming next pass", title="f",
                    severity="information")

    # ----------------------------------------------------------------- helpers

    def _resolve_action_target(
        self,
    ) -> Optional[Tuple[RegisteredProblem, Optional[int]]]:
        """Translate the cursor's tree node into ``(RegisteredProblem, version)``.

        - Cursor on a Problem node → not enough context, notify & return None.
        - Cursor on a Language node → pick its latest version (version=None).
        - Cursor on a Version node → that specific version.

        Looks the RegisteredProblem up via the DB so the service layer gets
        a real row (with the ``id`` it needs for review scheduling, etc.).
        """
        tree: ProblemTree = self.query_one(ProblemTree)
        node = tree.cursor_node
        if node is None or node.data is None:
            self.notify("highlight a problem first.", title="action",
                        severity="warning")
            return None
        kind = node.data.get("kind")
        if kind == "problem":
            self.notify(
                "expand the problem (→) and pick a language first.",
                title="action", severity="warning",
            )
            return None

        if kind == "language":
            problem: PractiseProblem = node.data["problem"]
            lang: LanguageEntry = node.data["ref"]
            version = None
        elif kind == "version":
            problem = node.data["problem"]
            lang = node.data["language"]
            version = node.data["ref"].version
        else:
            return None

        repo = getattr(self.app, "repo", None)
        if repo is None or not repo.is_initialized:
            self.notify("no .dojo repository found.", title="action",
                        severity="error")
            return None

        # Pull the actual RegisteredProblem row — services need its `id`.
        with repo.open_db() as db:
            registered = db.get_problem(
                "leetcode", problem.problem_id, lang.language.value,
            )
        if registered is None:
            self.notify(
                f"#{problem.problem_id} {lang.language.value} not registered.",
                title="action", severity="error",
            )
            return None
        return registered, version

    def _describe_target(self) -> Optional[str]:
        """Build a short human-readable label for whatever's highlighted."""
        tree: ProblemTree = self.query_one(ProblemTree)
        node = tree.cursor_node
        if node is None or node.data is None:
            return None
        kind = node.data.get("kind")
        if kind == "problem":
            p: PractiseProblem = node.data["ref"]
            return f"#{p.problem_id} {p.title}"
        if kind == "language":
            p = node.data["problem"]
            l: LanguageEntry = node.data["ref"]
            return f"#{p.problem_id} {p.title} ({l.language.value})"
        if kind == "version":
            p = node.data["problem"]
            l = node.data["language"]
            v: VersionAttempt = node.data["ref"]
            return f"#{p.problem_id} {p.title} ({l.language.value} v{v.version:03d})"
        return None

    @staticmethod
    def _left_for_problem(p: PractiseProblem) -> str:
        return f"~/dojo  ·  #{p.problem_id} {p.title}"

    @staticmethod
    def _left_for_language(p: PractiseProblem, lang: LanguageEntry) -> str:
        return f"~/dojo  ·  #{p.problem_id} {p.title} · {lang.language.value}"

    @staticmethod
    def _left_for_version(p: PractiseProblem, lang: LanguageEntry, ver: VersionAttempt) -> str:
        return (
            f"~/dojo  ·  #{p.problem_id} {p.title} · "
            f"{lang.language.value} · v{ver.version:03d}"
        )


# --------------------------------------------------------------------------- #
# Sidebar builders — depth-aware                                              #
# --------------------------------------------------------------------------- #

def _sidebar_for_problem(problem: PractiseProblem) -> SidebarData:
    lang_summary = "\n".join(
        f"{lang.language.value:<8}  {lang.status.value:<10}  "
        f"{len(lang.versions)} attempts"
        for lang in problem.languages
    )
    return SidebarData(
        header=f"#{problem.problem_id}",
        title=problem.title,
        byline=f"{_DIFF_LABEL.get(problem.difficulty, '?')} · {len(problem.languages)} languages",
        sections=[
            SidebarSection(title="TAGS",
                           body=", ".join(problem.tags) if problem.tags else "—"),
            SidebarSection(title="LANGUAGES", body=lang_summary or "—"),
        ],
    )


def _sidebar_for_language(problem: PractiseProblem, lang: LanguageEntry) -> SidebarData:
    versions_body = "\n".join(
        f"v{v.version:03d}  {v.status.value:<10}  {v.output:<18}  {v.when}"
        for v in lang.versions
    )
    return SidebarData(
        header=f"#{problem.problem_id} · {lang.language.value}",
        title=problem.title,
        byline=f"{_DIFF_LABEL.get(problem.difficulty, '?')} · {lang.language.value} · "
               f"{len(lang.versions)} attempts",
        sections=[
            SidebarSection(title="LATEST STATUS",
                           body=f"{lang.status.value}"),
            SidebarSection(title="VERSIONS", body=versions_body or "—"),
        ],
    )


def _sidebar_for_version(
    problem: PractiseProblem, lang: LanguageEntry, ver: VersionAttempt,
) -> SidebarData:
    return SidebarData(
        header=f"#{problem.problem_id} · {lang.language.value} · v{ver.version:03d}",
        title=problem.title,
        byline=f"{_DIFF_LABEL.get(problem.difficulty, '?')} · "
               f"{lang.language.value} · v{ver.version:03d}",
        sections=[
            SidebarSection(title="STATUS",   body=ver.status.value),
            SidebarSection(title="OUTPUT",   body=ver.output),
            SidebarSection(title="WHEN",     body=ver.when),
        ],
    )
