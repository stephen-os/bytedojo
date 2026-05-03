"""
Settings view - Configure ByteDojo preferences.
"""

from textual.app import ComposeResult
from textual.widgets import Static, Button, Select, Input
from textual.containers import Container, Vertical, Horizontal
from textual.widget import Widget
from textual.message import Message

from bytedojo.core.repository import Repository
from bytedojo.core.database import DatabaseManager
from bytedojo.core.settings import SettingsManager


class SettingRow(Widget):
    """A single setting row with label and control."""

    DEFAULT_CSS = """
    SettingRow {
        width: 100%;
        height: auto;
        padding: 1 2;
        background: #161b22;
        margin-bottom: 1;
    }

    SettingRow:hover {
        background: #21262d;
    }

    SettingRow .setting-label {
        width: 20;
        color: #e6edf3;
        padding: 1 0;
    }

    SettingRow .setting-description {
        width: 1fr;
        color: #8b949e;
        padding: 1 0;
    }

    SettingRow .setting-control {
        width: 20;
        height: auto;
    }

    SettingRow Select {
        width: 100%;
    }

    SettingRow Input {
        width: 100%;
    }
    """


class SettingsView(Widget):
    """Settings configuration view."""

    DEFAULT_CSS = """
    SettingsView {
        width: 100%;
        height: 100%;
        background: #0d1117;
    }

    #settings-container {
        width: 100%;
        height: 100%;
        padding: 2;
    }

    #settings-header {
        width: 100%;
        height: 3;
        padding: 0 0 1 0;
    }

    #settings-title {
        color: #6a2a8a;
        text-style: bold;
    }

    .section-container {
        width: 100%;
        height: auto;
        margin-bottom: 2;
    }

    .section-header {
        width: 100%;
        height: 2;
        color: #e6edf3;
        text-style: bold;
        border-bottom: solid #21262d;
        padding: 0 0 1 0;
        margin-bottom: 1;
    }

    .setting-row {
        width: 100%;
        height: 3;
        padding: 0 2;
        background: #161b22;
        margin-bottom: 1;
    }

    .setting-row:hover {
        background: #21262d;
    }

    .setting-label {
        width: 25;
        color: #e6edf3;
        padding: 1 0;
    }

    .setting-value {
        width: 15;
        color: #58a6ff;
        text-style: bold;
        padding: 1 0;
    }

    .setting-desc {
        width: 1fr;
        color: #8b949e;
        padding: 1 0;
    }

    .setting-action {
        width: auto;
        padding: 1 0;
    }

    #settings-footer {
        width: 100%;
        height: 3;
        dock: bottom;
        background: #21262d;
        padding: 1 2;
    }

    #settings-footer .footer-text {
        color: #8b949e;
    }

    #save-btn {
        background: #6a2a8a;
    }

    #save-btn:hover {
        background: #8a4aaa;
    }

    #reset-btn {
        background: #21262d;
    }

    #reset-btn:hover {
        background: #30363d;
    }

    .lang-python { color: #58a6ff; }
    .lang-java { color: #f06060; }
    .lang-cpp { color: #6a2a8a; }

    .org-flat { color: #58a6ff; }
    .org-difficulty { color: #f06060; }
    """

    class SettingsChanged(Message):
        """Message when settings are changed."""
        def __init__(self, key: str, value: str) -> None:
            self.key = key
            self.value = value
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._settings = {}

    def compose(self) -> ComposeResult:
        with Container(id="settings-container"):
            # Header
            with Horizontal(id="settings-header"):
                yield Static("Settings", id="settings-title")

            # Defaults Section
            with Vertical(classes="section-container"):
                yield Static("Defaults", classes="section-header")

                # Default Language
                with Horizontal(classes="setting-row", id="row-language"):
                    yield Static("Default Language", classes="setting-label")
                    yield Static("python", classes="setting-value", id="val-language")
                    yield Static("Language for fetch/run commands", classes="setting-desc")
                    yield Button("Change", classes="setting-action", id="btn-language")

                # Default Source
                with Horizontal(classes="setting-row", id="row-source"):
                    yield Static("Default Source", classes="setting-label")
                    yield Static("leetcode", classes="setting-value", id="val-source")
                    yield Static("Problem source platform", classes="setting-desc")

            # Review Section
            with Vertical(classes="section-container"):
                yield Static("Review", classes="section-header")

                # Review Frequency
                with Horizontal(classes="setting-row", id="row-frequency"):
                    yield Static("Review Frequency", classes="setting-label")
                    yield Static("7 days", classes="setting-value", id="val-frequency")
                    yield Static("Days between reviews after passing", classes="setting-desc")
                    yield Button("Change", classes="setting-action", id="btn-frequency")

            # LeetCode Section
            with Vertical(classes="section-container"):
                yield Static("LeetCode", classes="section-header")

                # Organization
                with Horizontal(classes="setting-row", id="row-organization"):
                    yield Static("Organization", classes="setting-label")
                    yield Static("flat", classes="setting-value", id="val-organization")
                    yield Static("Folder structure (flat or by difficulty)", classes="setting-desc")
                    yield Button("Change", classes="setting-action", id="btn-organization")

            # Footer
            with Horizontal(id="settings-footer"):
                yield Static("Settings are saved automatically", classes="footer-text")

    def on_mount(self) -> None:
        """Load settings on mount."""
        self._load_settings()

    def _load_settings(self) -> None:
        """Load current settings from storage."""
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                return

            # Load from database
            with DatabaseManager(repo.db_path) as db:
                self._settings['language'] = db.get_config('default_language', 'python')
                self._settings['source'] = db.get_config('default_source', 'leetcode')
                self._settings['frequency'] = db.get_config('review_frequency_days', '7')

            # Load from settings file
            settings_manager = SettingsManager(repo.dojo_dir)
            settings = settings_manager.load()
            self._settings['organization'] = settings.leetcode.organization

            # Update display
            self._update_display()

        except Exception:
            pass

    def _update_display(self) -> None:
        """Update the display with current settings."""
        try:
            # Language
            lang = self._settings.get('language', 'python')
            lang_widget = self.query_one("#val-language", Static)
            lang_widget.update(lang)
            lang_widget.remove_class("lang-python", "lang-java", "lang-cpp")
            lang_widget.add_class(f"lang-{lang}")

            # Source
            source = self._settings.get('source', 'leetcode')
            self.query_one("#val-source", Static).update(source)

            # Frequency
            freq = self._settings.get('frequency', '7')
            self.query_one("#val-frequency", Static).update(f"{freq} days")

            # Organization
            org = self._settings.get('organization', 'flat')
            org_widget = self.query_one("#val-organization", Static)
            org_widget.update(org)
            org_widget.remove_class("org-flat", "org-difficulty")
            org_widget.add_class(f"org-{org}")

        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-language":
            self._cycle_language()
        elif button_id == "btn-frequency":
            self._cycle_frequency()
        elif button_id == "btn-organization":
            self._cycle_organization()

    def _cycle_language(self) -> None:
        """Cycle through available languages."""
        languages = ['python', 'java', 'cpp']
        current = self._settings.get('language', 'python')
        try:
            idx = languages.index(current)
            new_lang = languages[(idx + 1) % len(languages)]
        except ValueError:
            new_lang = 'python'

        self._save_setting('language', new_lang)

    def _cycle_frequency(self) -> None:
        """Cycle through common frequencies."""
        frequencies = ['1', '3', '7', '14', '30']
        current = self._settings.get('frequency', '7')
        try:
            idx = frequencies.index(current)
            new_freq = frequencies[(idx + 1) % len(frequencies)]
        except ValueError:
            new_freq = '7'

        self._save_setting('frequency', new_freq)

    def _cycle_organization(self) -> None:
        """Toggle between organization modes."""
        current = self._settings.get('organization', 'flat')
        new_org = 'difficulty' if current == 'flat' else 'flat'
        self._save_setting('organization', new_org)

    def _save_setting(self, key: str, value: str) -> None:
        """Save a setting and update display."""
        try:
            repo = Repository(Path.cwd())
            if not repo.is_initialized:
                return

            if key in ['language', 'source', 'frequency']:
                with DatabaseManager(repo.db_path) as db:
                    if key == 'language':
                        db.set_config('default_language', value)
                    elif key == 'source':
                        db.set_config('default_source', value)
                    elif key == 'frequency':
                        db.set_config('review_frequency_days', value)

            elif key == 'organization':
                settings_manager = SettingsManager(repo.dojo_dir)
                settings_manager.set('leetcode.organization', value)

            self._settings[key] = value
            self._update_display()

            # Notify
            self.notify(f"Updated {key} to {value}", title="Settings")
            self.post_message(self.SettingsChanged(key, value))

        except Exception as e:
            self.notify(f"Failed to save: {e}", title="Error", severity="error")

    def refresh_settings(self) -> None:
        """Refresh settings from storage."""
        self._load_settings()
