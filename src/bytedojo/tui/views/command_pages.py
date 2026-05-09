"""
Command pages - Pages for each command with core service integration.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, Label, Log
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widget import Widget
from textual.message import Message
from textual import work

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.core import problem_service
from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.execution import ProblemExecutor
from bytedojo.core.grading import GradingService
from bytedojo.core.review_service import ReviewService
from bytedojo.core.settings import SettingsManager


class BasePage(Widget):
    """Base page with back navigation."""

    DEFAULT_CSS = """
    BasePage {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    BasePage #page-header {
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }

    BasePage #back-btn {
        width: auto;
    }

    BasePage #page-title {
        width: 1fr;
        text-style: bold;
    }

    BasePage #page-content {
        width: 100%;
        height: 1fr;
    }

    BasePage #output {
        width: 100%;
        height: auto;
        max-height: 15;
        margin-top: 1;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    BasePage .selected {
        background: $primary;
    }
    """

    class GoBack(Message):
        """Message to go back to menu."""
        pass

    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title

    def compose(self) -> ComposeResult:
        with Horizontal(id="page-header"):
            yield Button("< Back", id="back-btn", variant="default")
            yield Static(self.title, id="page-title")
        with Container(id="page-content"):
            yield from self.compose_content()

    def compose_content(self) -> ComposeResult:
        """Override to add page content."""
        yield Static("Page content goes here")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.post_message(self.GoBack())


class FetchPage(BasePage):
    """Fetch problems page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Fetch Problems", **kwargs)
        self._language = "python"

    def compose_content(self) -> ComposeResult:
        yield Static("Problem ID(s):")
        yield Input(placeholder="e.g. 1, 1..10, 1,2,3", id="problem-input")
        yield Static("")
        yield Static("Language:")
        with Horizontal():
            yield Button("Python", id="btn-python", classes="selected")
            yield Button("Java", id="btn-java")
            yield Button("C++", id="btn-cpp")
        yield Static("")
        yield Button("Fetch", id="btn-fetch", variant="primary")
        yield Static("", id="output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        btn_id = event.button.id

        if btn_id in ("btn-python", "btn-java", "btn-cpp"):
            self._select_language(btn_id.replace("btn-", ""))
        elif btn_id == "btn-fetch":
            self._do_fetch()

    def _select_language(self, lang: str) -> None:
        self._language = lang
        for btn_id in ("btn-python", "btn-java", "btn-cpp"):
            btn = self.query_one(f"#{btn_id}", Button)
            if btn_id == f"btn-{lang}":
                btn.add_class("selected")
            else:
                btn.remove_class("selected")

    def _do_fetch(self) -> None:
        problem_str = self.query_one("#problem-input", Input).value.strip()
        if not problem_str:
            self._show_output("Error: Please enter problem ID(s)")
            return

        try:
            problem_ids = problem_service.parse_problem_ids((problem_str,))
        except ValueError as e:
            self._show_output(f"Error: {e}")
            return

        self._show_output(f"Fetching {len(problem_ids)} problem(s)...")
        self._fetch_problems(problem_ids)

    @work(thread=True)
    def _fetch_problems(self, problem_ids: list) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self.call_from_thread(self._show_output, "Error: Dojo not initialized")
                return

            lang = CodeLanguage.from_string(self._language)
            if lang == CodeLanguage.UNKNOWN:
                self.call_from_thread(self._show_output, f"Error: Unknown language {self._language}")
                return

            success_count = 0
            skip_count = 0
            error_count = 0

            for pid in problem_ids:
                result = problem_service.place_problem(
                    problem_id=pid,
                    language=lang,
                    repo=repo,
                    force=False
                )
                if result.error:
                    error_count += 1
                elif result.skipped:
                    skip_count += 1
                else:
                    success_count += 1

            msg = f"Done: {success_count} fetched, {skip_count} skipped, {error_count} failed"
            self.call_from_thread(self._show_output, msg)

        except Exception as e:
            self.call_from_thread(self._show_output, f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)


class RunPage(BasePage):
    """Run solution page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Run Solution", **kwargs)

    def compose_content(self) -> ComposeResult:
        yield Static("Problem ID:")
        yield Input(placeholder="Enter problem ID", id="problem-input")
        yield Static("")
        with Horizontal():
            yield Button("Run", id="btn-run", variant="primary")
            yield Button("Run Last", id="btn-run-last")
        yield Static("", id="output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        btn_id = event.button.id

        if btn_id == "btn-run":
            self._do_run(use_last=False)
        elif btn_id == "btn-run-last":
            self._do_run(use_last=True)

    def _do_run(self, use_last: bool) -> None:
        if use_last:
            problem_id = None
        else:
            problem_str = self.query_one("#problem-input", Input).value.strip()
            if not problem_str:
                self._show_output("Error: Please enter a problem ID")
                return
            try:
                problem_id = int(problem_str)
            except ValueError:
                self._show_output("Error: Invalid problem ID")
                return

        self._show_output("Running...")
        self._run_problem(problem_id, use_last)

    @work(thread=True)
    def _run_problem(self, problem_id: int | None, use_last: bool) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self.call_from_thread(self._show_output, "Error: Dojo not initialized")
                return

            executor = ProblemExecutor(repo)

            with DatabaseManager(repo.db_path) as db:
                language = db.get_config('default_language', 'python')

                if use_last:
                    problem = executor.get_last_problem(db, language)
                    if not problem:
                        self.call_from_thread(self._show_output, "Error: No last problem found")
                        return
                else:
                    problem = db.get_problem('leetcode', problem_id, language)
                    if not problem:
                        self.call_from_thread(self._show_output, f"Error: Problem {problem_id} not found")
                        return

                result = executor.run(problem, language)

                lines = [f"Problem #{problem['problem_id']}: {problem['title']}"]
                lines.append(f"Tests: {result.passed}/{result.total}")
                if result.all_passed:
                    lines.append("Status: ALL PASSED")
                else:
                    lines.append("Status: SOME FAILED")
                    for tc in result.test_cases:
                        if not tc.passed:
                            lines.append(f"  - {tc.name}: {tc.error or 'Failed'}")

                self.call_from_thread(self._show_output, "\n".join(lines))

        except Exception as e:
            self.call_from_thread(self._show_output, f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)


class GradePage(BasePage):
    """Grade problem page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Grade Problem", **kwargs)

    def compose_content(self) -> ComposeResult:
        yield Static("Problem ID:")
        yield Input(placeholder="Enter problem ID", id="problem-input")
        yield Static("")
        yield Static("Notes (optional):")
        yield Input(placeholder="Add notes", id="notes-input")
        yield Static("")
        with Horizontal():
            yield Button("Pass", id="btn-pass", variant="success")
            yield Button("Fail", id="btn-fail", variant="error")
        yield Static("", id="output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        btn_id = event.button.id

        if btn_id == "btn-pass":
            self._do_grade(passed=True)
        elif btn_id == "btn-fail":
            self._do_grade(passed=False)

    def _do_grade(self, passed: bool) -> None:
        problem_str = self.query_one("#problem-input", Input).value.strip()
        if not problem_str:
            self._show_output("Error: Please enter a problem ID")
            return

        try:
            problem_id = int(problem_str)
        except ValueError:
            self._show_output("Error: Invalid problem ID")
            return

        notes = self.query_one("#notes-input", Input).value.strip() or None
        self._grade_problem(problem_id, passed, notes)

    def _grade_problem(self, problem_id: int, passed: bool, notes: str | None) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                language = db.get_config('default_language', 'python')
                problem = db.get_problem('leetcode', problem_id, language)

                if not problem:
                    self._show_output(f"Error: Problem {problem_id} not found")
                    return

                grading = GradingService(db)
                result = grading.grade(
                    problem_id=problem_id,
                    source='leetcode',
                    language=language,
                    passed=passed,
                    notes=notes
                )

                status = "PASSED" if passed else "FAILED"
                msg = f"Graded #{problem_id} as {status}"
                if result.next_review:
                    msg += f"\nNext review: {result.next_review.strftime('%Y-%m-%d')}"
                self._show_output(msg)

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)


class PickPage(BasePage):
    """Pick random problem page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Pick Problem", **kwargs)
        self._difficulty = None
        self._status = "unsolved"

    def compose_content(self) -> ComposeResult:
        yield Static("Difficulty:")
        with Horizontal():
            yield Button("Easy", id="btn-easy")
            yield Button("Medium", id="btn-medium")
            yield Button("Hard", id="btn-hard")
            yield Button("Any", id="btn-any-diff", classes="selected")
        yield Static("")
        yield Static("Status:")
        with Horizontal():
            yield Button("Unsolved", id="btn-unsolved", classes="selected")
            yield Button("Failed", id="btn-failed")
            yield Button("Any", id="btn-any-status")
        yield Static("")
        yield Button("Pick Random", id="btn-pick", variant="primary")
        yield Static("", id="output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        btn_id = event.button.id

        if btn_id in ("btn-easy", "btn-medium", "btn-hard", "btn-any-diff"):
            self._select_difficulty(btn_id)
        elif btn_id in ("btn-unsolved", "btn-failed", "btn-any-status"):
            self._select_status(btn_id)
        elif btn_id == "btn-pick":
            self._do_pick()

    def _select_difficulty(self, btn_id: str) -> None:
        diff_map = {"btn-easy": "easy", "btn-medium": "medium", "btn-hard": "hard", "btn-any-diff": None}
        self._difficulty = diff_map.get(btn_id)
        for bid in diff_map.keys():
            btn = self.query_one(f"#{bid}", Button)
            if bid == btn_id:
                btn.add_class("selected")
            else:
                btn.remove_class("selected")

    def _select_status(self, btn_id: str) -> None:
        status_map = {"btn-unsolved": "unsolved", "btn-failed": "failed", "btn-any-status": None}
        self._status = status_map.get(btn_id)
        for bid in status_map.keys():
            btn = self.query_one(f"#{bid}", Button)
            if bid == btn_id:
                btn.add_class("selected")
            else:
                btn.remove_class("selected")

    def _do_pick(self) -> None:
        try:
            import random
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                problems = db.list_problems()

                # Filter by difficulty
                if self._difficulty:
                    problems = [p for p in problems if p.get('difficulty', '').lower() == self._difficulty]

                # Filter by status
                if self._status == "unsolved":
                    problems = [p for p in problems if p.get('test_status') not in ('passed', 'failed')]
                elif self._status == "failed":
                    problems = [p for p in problems if p.get('test_status') == 'failed']

                if not problems:
                    self._show_output("No problems match your criteria")
                    return

                picked = random.choice(problems)
                msg = f"Picked: #{picked['problem_id']} {picked['title']}\n"
                msg += f"Difficulty: {picked.get('difficulty', 'Unknown')}\n"
                msg += f"Status: {picked.get('test_status', 'unsolved')}\n"
                msg += f"File: {picked.get('file_path', 'N/A')}"
                self._show_output(msg)

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)


class QueryPage(BasePage):
    """Query problems page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Query Problems", **kwargs)

    def compose_content(self) -> ComposeResult:
        yield Static("Search:")
        yield Input(placeholder="Search by title or ID", id="search-input")
        yield Static("")
        yield Button("Search", id="btn-search", variant="primary")
        yield Static("", id="output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        if event.button.id == "btn-search":
            self._do_search()

    def _do_search(self) -> None:
        query = self.query_one("#search-input", Input).value.strip().lower()

        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                problems = db.list_problems()

                if query:
                    # Filter by query
                    filtered = []
                    for p in problems:
                        if query in p.get('title', '').lower():
                            filtered.append(p)
                        elif query.isdigit() and int(query) == p.get('problem_id'):
                            filtered.append(p)
                    problems = filtered

                if not problems:
                    self._show_output("No problems found")
                    return

                lines = [f"Found {len(problems)} problem(s):", ""]
                for p in problems[:20]:  # Limit to 20
                    status = p.get('test_status', '-')
                    lines.append(f"#{p['problem_id']:4} {p['title'][:35]:<35} [{status}]")

                if len(problems) > 20:
                    lines.append(f"... and {len(problems) - 20} more")

                self._show_output("\n".join(lines))

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)


class ReviewPage(BasePage):
    """Review session page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Review Session", **kwargs)

    def compose_content(self) -> ComposeResult:
        yield Static("Review problems that are due for practice.")
        yield Static("")
        with Horizontal():
            yield Button("View Due", id="btn-view-due", variant="primary")
            yield Button("View Stats", id="btn-stats")
        yield Static("", id="output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        btn_id = event.button.id

        if btn_id == "btn-view-due":
            self._view_due()
        elif btn_id == "btn-stats":
            self._view_stats()

    def _view_due(self) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                review_service = ReviewService(db)
                due = review_service.get_due_reviews(include_future=False)

                if not due:
                    self._show_output("No reviews due! You're all caught up.")
                    return

                lines = [f"{len(due)} problem(s) due for review:", ""]
                for r in due[:15]:
                    lines.append(f"#{r.problem_id:4} {r.title[:40]}")

                if len(due) > 15:
                    lines.append(f"... and {len(due) - 15} more")

                self._show_output("\n".join(lines))

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _view_stats(self) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                review_service = ReviewService(db)
                stats = review_service.get_stats()

                lines = [
                    "Review Statistics:",
                    "",
                    f"Total in review:  {stats.total_in_review}",
                    f"Due now:          {stats.due_now}",
                    f"Due today:        {stats.due_today}",
                    f"Due this week:    {stats.due_this_week}",
                    f"Mastered:         {stats.mastered}",
                ]
                self._show_output("\n".join(lines))

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)


class StatsPage(BasePage):
    """Statistics page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Statistics", **kwargs)

    def compose_content(self) -> ComposeResult:
        yield Button("Show Stats", id="btn-show", variant="primary")
        yield Static("", id="output")

    def on_mount(self) -> None:
        self._show_stats()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        if event.button.id == "btn-show":
            self._show_stats()

    def _show_stats(self) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                problems = db.list_problems()

                total = len(problems)
                passed = sum(1 for p in problems if p.get('test_status') == 'passed')
                failed = sum(1 for p in problems if p.get('test_status') == 'failed')
                unsolved = total - passed - failed

                easy = sum(1 for p in problems if p.get('difficulty') == 'Easy')
                medium = sum(1 for p in problems if p.get('difficulty') == 'Medium')
                hard = sum(1 for p in problems if p.get('difficulty') == 'Hard')

                lines = [
                    "Your Statistics:",
                    "",
                    f"Total Problems:   {total}",
                    f"  Passed:         {passed}",
                    f"  Failed:         {failed}",
                    f"  Unsolved:       {unsolved}",
                    "",
                    "By Difficulty:",
                    f"  Easy:           {easy}",
                    f"  Medium:         {medium}",
                    f"  Hard:           {hard}",
                ]

                if total > 0:
                    rate = int((passed / total) * 100)
                    lines.append("")
                    lines.append(f"Pass Rate:        {rate}%")

                self._show_output("\n".join(lines))

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)


class SettingsPage(BasePage):
    """Settings page."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Settings", **kwargs)
        self._language = "python"

    def compose_content(self) -> ComposeResult:
        yield Static("Default Language:")
        with Horizontal():
            yield Button("Python", id="btn-python", classes="selected")
            yield Button("Java", id="btn-java")
            yield Button("C++", id="btn-cpp")
        yield Static("")
        yield Static("Review Frequency (days):")
        yield Input(placeholder="7", id="frequency-input", value="7")
        yield Button("Save Frequency", id="btn-save-freq")
        yield Static("")
        yield Static("Organization:")
        with Horizontal():
            yield Button("Flat", id="btn-flat", classes="selected")
            yield Button("By Difficulty", id="btn-difficulty")
        yield Static("", id="output")

    def on_mount(self) -> None:
        self._load_settings()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        super().on_button_pressed(event)
        btn_id = event.button.id

        if btn_id in ("btn-python", "btn-java", "btn-cpp"):
            lang = btn_id.replace("btn-", "")
            self._save_language(lang)
        elif btn_id == "btn-save-freq":
            self._save_frequency()
        elif btn_id in ("btn-flat", "btn-difficulty"):
            org = "flat" if btn_id == "btn-flat" else "difficulty"
            self._save_organization(org)

    def _load_settings(self) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                return

            with DatabaseManager(repo.db_path) as db:
                self._language = db.get_config('default_language', 'python')
                freq = db.get_config('review_frequency_days', '7')
                self.query_one("#frequency-input", Input).value = freq

            # Update language buttons
            for lang in ("python", "java", "cpp"):
                btn = self.query_one(f"#btn-{lang}", Button)
                if lang == self._language:
                    btn.add_class("selected")
                else:
                    btn.remove_class("selected")

            # Load organization
            settings_mgr = SettingsManager(repo.dojo_dir)
            settings = settings_mgr.load()
            org = settings.leetcode.organization

            self.query_one("#btn-flat", Button).remove_class("selected")
            self.query_one("#btn-difficulty", Button).remove_class("selected")
            if org == "flat":
                self.query_one("#btn-flat", Button).add_class("selected")
            else:
                self.query_one("#btn-difficulty", Button).add_class("selected")

        except Exception:
            pass

    def _save_language(self, lang: str) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                db.set_config('default_language', lang)

            self._language = lang
            for l in ("python", "java", "cpp"):
                btn = self.query_one(f"#btn-{l}", Button)
                if l == lang:
                    btn.add_class("selected")
                else:
                    btn.remove_class("selected")

            self._show_output(f"Language set to {lang}")

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _save_frequency(self) -> None:
        try:
            freq_str = self.query_one("#frequency-input", Input).value.strip()
            freq = int(freq_str)
            if freq < 1 or freq > 365:
                self._show_output("Error: Frequency must be 1-365 days")
                return

            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            with DatabaseManager(repo.db_path) as db:
                db.set_config('review_frequency_days', str(freq))

            self._show_output(f"Review frequency set to {freq} days")

        except ValueError:
            self._show_output("Error: Invalid number")
        except Exception as e:
            self._show_output(f"Error: {e}")

    def _save_organization(self, org: str) -> None:
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                self._show_output("Error: Dojo not initialized")
                return

            settings_mgr = SettingsManager(repo.dojo_dir)
            settings_mgr.set('leetcode.organization', org)

            self.query_one("#btn-flat", Button).remove_class("selected")
            self.query_one("#btn-difficulty", Button).remove_class("selected")
            if org == "flat":
                self.query_one("#btn-flat", Button).add_class("selected")
            else:
                self.query_one("#btn-difficulty", Button).add_class("selected")

            self._show_output(f"Organization set to {org}")

        except Exception as e:
            self._show_output(f"Error: {e}")

    def _show_output(self, text: str) -> None:
        self.query_one("#output", Static).update(text)
