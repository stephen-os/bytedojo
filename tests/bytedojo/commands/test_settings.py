"""
Tests for settings command.
"""

import pytest
from click.testing import CliRunner
import sqlite3

from bytedojo.commands.bytedojo import dojo
from bytedojo.core.database import create_database_schema


@pytest.fixture
def initialized_repo(tmp_path, monkeypatch):
    """Create an initialized dojo repository."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Create .dojo directory and database
    dojo_dir = tmp_path / ".dojo"
    dojo_dir.mkdir()
    db_path = dojo_dir / "db.sqlite"
    create_database_schema(db_path)

    # Create settings.json
    settings_path = dojo_dir / "settings.json"
    settings_path.write_text('{"leetcode": {"organization": "difficulty"}}')

    return tmp_path


class TestSettingsCommand:
    """Test dojo settings command."""

    def test_settings_no_repo(self, tmp_path, monkeypatch):
        """Test settings fails when repository not initialized."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(dojo, ['settings'])

        assert result.exit_code != 0
        assert "Repository not initialized" in result.output or "No .dojo repository found" in result.output

    def test_settings_shows_all_settings(self, initialized_repo):
        """Test settings displays all current settings."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['settings'])

        assert result.exit_code == 0
        assert "BYTEDOJO SETTINGS" in result.output
        assert "frequency" in result.output.lower()


class TestSettingsReviewFrequencyCommand:
    """Test dojo settings review-frequency command."""

    def test_review_frequency_no_repo(self, tmp_path, monkeypatch):
        """Test review-frequency fails when repository not initialized."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(dojo, ['settings', 'review-frequency', '7'])

        assert result.exit_code != 0
        assert "Repository not initialized" in result.output or "No .dojo repository found" in result.output

    def test_review_frequency_updates_value(self, initialized_repo):
        """Test review-frequency updates the config value."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['settings', 'review-frequency', '14'])

        assert result.exit_code == 0
        assert "14" in result.output
        assert "updated" in result.output.lower() or "->" in result.output

        # Verify the value was actually updated
        db_path = initialized_repo / ".dojo" / "db.sqlite"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key='review_frequency_days'")
        value = cursor.fetchone()[0]
        conn.close()

        assert value == '14'

    def test_review_frequency_rejects_zero(self, initialized_repo):
        """Test review-frequency rejects 0 days."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['settings', 'review-frequency', '0'])

        assert result.exit_code != 0
        assert "at least 1 day" in result.output

    def test_review_frequency_rejects_negative(self, initialized_repo):
        """Test review-frequency rejects negative values."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['settings', 'review-frequency', '-5'])

        # Click will reject negative as invalid integer or we'll catch it
        assert result.exit_code != 0

    def test_review_frequency_rejects_too_large(self, initialized_repo):
        """Test review-frequency rejects values over 365."""
        runner = CliRunner()

        result = runner.invoke(dojo, ['settings', 'review-frequency', '400'])

        assert result.exit_code != 0
        assert "365" in result.output or "exceed" in result.output.lower()

    def test_review_frequency_accepts_valid_values(self, initialized_repo):
        """Test review-frequency accepts various valid values."""
        runner = CliRunner()

        # Test minimum
        result = runner.invoke(dojo, ['settings', 'review-frequency', '1'])
        assert result.exit_code == 0

        # Test maximum
        result = runner.invoke(dojo, ['settings', 'review-frequency', '365'])
        assert result.exit_code == 0

        # Test common values
        result = runner.invoke(dojo, ['settings', 'review-frequency', '7'])
        assert result.exit_code == 0

        result = runner.invoke(dojo, ['settings', 'review-frequency', '30'])
        assert result.exit_code == 0
