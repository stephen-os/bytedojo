"""
Tests for settings management (LeetCodeSettings, Settings, SettingsManager).
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from bytedojo.core.settings import (
    LeetCodeSettings,
    Settings,
    SettingsManager,
)


class TestLeetCodeSettings:
    """Test LeetCodeSettings dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = LeetCodeSettings()
        assert settings.organization == "flat"

    def test_custom_organization_flat(self):
        """Test creating settings with flat organization."""
        settings = LeetCodeSettings(organization="flat")
        assert settings.organization == "flat"

    def test_custom_organization_difficulty(self):
        """Test creating settings with difficulty organization."""
        settings = LeetCodeSettings(organization="difficulty")
        assert settings.organization == "difficulty"

    def test_equality(self):
        """Test that identical settings are equal."""
        settings1 = LeetCodeSettings(organization="flat")
        settings2 = LeetCodeSettings(organization="flat")
        assert settings1 == settings2

    def test_inequality(self):
        """Test that different settings are not equal."""
        settings1 = LeetCodeSettings(organization="flat")
        settings2 = LeetCodeSettings(organization="difficulty")
        assert settings1 != settings2


class TestSettings:
    """Test Settings dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = Settings()
        assert settings.leetcode is not None
        assert settings.leetcode.organization == "flat"

    def test_custom_leetcode_settings(self):
        """Test creating settings with custom LeetCodeSettings."""
        leetcode = LeetCodeSettings(organization="difficulty")
        settings = Settings(leetcode=leetcode)
        assert settings.leetcode.organization == "difficulty"

    def test_equality(self):
        """Test that identical settings are equal."""
        settings1 = Settings()
        settings2 = Settings()
        assert settings1 == settings2

    def test_inequality(self):
        """Test that different settings are not equal."""
        settings1 = Settings(leetcode=LeetCodeSettings(organization="flat"))
        settings2 = Settings(leetcode=LeetCodeSettings(organization="difficulty"))
        assert settings1 != settings2


class TestSettingsToDict:
    """Test Settings.to_dict method."""

    def test_to_dict_default(self):
        """Test converting default settings to dict."""
        settings = Settings()
        result = settings.to_dict()

        assert "leetcode" in result
        assert result["leetcode"]["organization"] == "flat"

    def test_to_dict_custom(self):
        """Test converting custom settings to dict."""
        settings = Settings(leetcode=LeetCodeSettings(organization="difficulty"))
        result = settings.to_dict()

        assert result["leetcode"]["organization"] == "difficulty"

    def test_to_dict_is_serializable(self):
        """Test that to_dict result is JSON serializable."""
        settings = Settings()
        result = settings.to_dict()

        # Should not raise
        json_str = json.dumps(result)
        assert json_str is not None


class TestSettingsFromDict:
    """Test Settings.from_dict class method."""

    def test_from_dict_valid(self):
        """Test creating settings from valid dict."""
        data = {"leetcode": {"organization": "difficulty"}}
        settings = Settings.from_dict(data)

        assert settings.leetcode.organization == "difficulty"

    def test_from_dict_empty(self):
        """Test creating settings from empty dict uses defaults."""
        data = {}
        settings = Settings.from_dict(data)

        assert settings.leetcode.organization == "flat"

    def test_from_dict_partial(self):
        """Test creating settings from partial dict."""
        data = {"leetcode": {}}
        settings = Settings.from_dict(data)

        assert settings.leetcode.organization == "flat"

    def test_from_dict_roundtrip(self):
        """Test that to_dict and from_dict are reversible."""
        original = Settings(leetcode=LeetCodeSettings(organization="difficulty"))
        data = original.to_dict()
        restored = Settings.from_dict(data)

        assert restored == original


class TestSettingsManagerInit:
    """Test SettingsManager initialization."""

    def test_init_sets_paths(self):
        """Test that init sets correct paths."""
        dojo_path = Path("/test/.dojo")
        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        assert manager.dojo_path == dojo_path
        assert manager.settings_path == dojo_path / "settings.json"

    def test_init_gets_logger(self):
        """Test that init gets logger."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        assert manager.logger == mock_logger


class TestSettingsManagerLoad:
    """Test SettingsManager.load method."""

    def test_load_returns_defaults_when_file_not_exists(self):
        """Test that load returns defaults when file doesn't exist."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        with patch.object(Path, "exists", return_value=False):
            settings = manager.load()

        assert settings.leetcode.organization == "flat"

    def test_load_reads_file(self):
        """Test that load reads and parses JSON file."""
        dojo_path = Path("/test/.dojo")
        file_content = '{"leetcode": {"organization": "difficulty"}}'

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=file_content)):
                settings = manager.load()

        assert settings.leetcode.organization == "difficulty"

    def test_load_returns_defaults_on_json_error(self):
        """Test that load returns defaults when JSON is invalid."""
        dojo_path = Path("/test/.dojo")
        file_content = "not valid json"

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=file_content)):
                settings = manager.load()

        assert settings.leetcode.organization == "flat"

    def test_load_logs_error_on_exception(self):
        """Test that load logs error on exception."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Read error")):
                settings = manager.load()

        mock_logger.error.assert_called_once()
        assert settings.leetcode.organization == "flat"


class TestSettingsManagerSave:
    """Test SettingsManager.save method."""

    def test_save_creates_directory(self):
        """Test that save creates directory if needed."""
        dojo_path = MagicMock(spec=Path)
        dojo_path.__truediv__ = MagicMock(return_value=Path("/test/.dojo/settings.json"))

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch("builtins.open", mock_open()):
            manager.save(settings)

        dojo_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_save_writes_json(self):
        """Test that save writes correct JSON to file."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        settings = Settings(leetcode=LeetCodeSettings(organization="difficulty"))

        m = mock_open()
        with patch.object(Path, "mkdir"):
            with patch("builtins.open", m):
                manager.save(settings)

        # Check that open was called with write mode
        m.assert_called_once()
        call_args = m.call_args
        assert call_args[0][1] == 'w'

    def test_save_logs_debug_on_success(self):
        """Test that save logs debug message on success."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(Path, "mkdir"):
            with patch("builtins.open", mock_open()):
                manager.save(settings)

        mock_logger.debug.assert_called_once()

    def test_save_raises_on_write_error(self):
        """Test that save raises exception on write error."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(Path, "mkdir"):
            with patch("builtins.open", side_effect=IOError("Write error")):
                with pytest.raises(IOError):
                    manager.save(settings)

        mock_logger.error.assert_called_once()


class TestSettingsManagerGet:
    """Test SettingsManager.get method."""

    def test_get_valid_key(self):
        """Test getting a valid setting by key."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        settings = Settings(leetcode=LeetCodeSettings(organization="difficulty"))
        with patch.object(manager, "load", return_value=settings):
            result = manager.get("leetcode.organization")

        assert result == "difficulty"

    def test_get_returns_object_for_partial_key(self):
        """Test getting an object for partial key."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            result = manager.get("leetcode")

        assert isinstance(result, LeetCodeSettings)

    def test_get_returns_none_for_invalid_key(self):
        """Test that get returns None for invalid key."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            result = manager.get("nonexistent.key")

        assert result is None

    def test_get_returns_none_for_deeply_invalid_key(self):
        """Test that get returns None for deeply nested invalid key."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            result = manager.get("leetcode.nonexistent.deep")

        assert result is None


class TestSettingsManagerSet:
    """Test SettingsManager.set method."""

    def test_set_valid_key(self):
        """Test setting a valid key."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            with patch.object(manager, "save") as mock_save:
                result = manager.set("leetcode.organization", "difficulty")

        assert result is True
        mock_save.assert_called_once()
        # Verify the settings were modified
        saved_settings = mock_save.call_args[0][0]
        assert saved_settings.leetcode.organization == "difficulty"

    def test_set_returns_false_for_single_part_key(self):
        """Test that set returns False for single part key."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            result = manager.set("leetcode", "value")

        assert result is False
        mock_logger.error.assert_called_once()

    def test_set_returns_false_for_invalid_parent_key(self):
        """Test that set returns False when parent key doesn't exist."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            result = manager.set("nonexistent.key", "value")

        assert result is False
        mock_logger.error.assert_called_once()

    def test_set_returns_false_for_invalid_final_key(self):
        """Test that set returns False when final key doesn't exist."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            result = manager.set("leetcode.nonexistent", "value")

        assert result is False
        mock_logger.error.assert_called_once()

    def test_set_logs_error_for_unknown_setting(self):
        """Test that set logs error for unknown setting."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        settings = Settings()
        with patch.object(manager, "load", return_value=settings):
            manager.set("unknown.setting", "value")

        mock_logger.error.assert_called()


class TestSettingsManagerCreateDefault:
    """Test SettingsManager.create_default method."""

    def test_create_default_when_file_not_exists(self):
        """Test that create_default creates file when it doesn't exist."""
        dojo_path = Path("/test/.dojo")
        mock_logger = MagicMock()

        with patch("bytedojo.core.settings.get_logger", return_value=mock_logger):
            manager = SettingsManager(dojo_path)

        with patch.object(Path, "exists", return_value=False):
            with patch.object(manager, "save") as mock_save:
                manager.create_default()

        mock_save.assert_called_once()
        mock_logger.debug.assert_called()

    def test_create_default_does_nothing_when_file_exists(self):
        """Test that create_default does nothing when file exists."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        with patch.object(Path, "exists", return_value=True):
            with patch.object(manager, "save") as mock_save:
                manager.create_default()

        mock_save.assert_not_called()

    def test_create_default_saves_default_settings(self):
        """Test that create_default saves default settings."""
        dojo_path = Path("/test/.dojo")

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        with patch.object(Path, "exists", return_value=False):
            with patch.object(manager, "save") as mock_save:
                manager.create_default()

        saved_settings = mock_save.call_args[0][0]
        assert saved_settings.leetcode.organization == "flat"


class TestSettingsManagerDefaultSettings:
    """Test SettingsManager.DEFAULT_SETTINGS class attribute."""

    def test_default_settings_is_settings_instance(self):
        """Test that DEFAULT_SETTINGS is a Settings instance."""
        assert isinstance(SettingsManager.DEFAULT_SETTINGS, Settings)

    def test_default_settings_has_flat_organization(self):
        """Test that DEFAULT_SETTINGS has flat organization."""
        assert SettingsManager.DEFAULT_SETTINGS.leetcode.organization == "flat"


class TestSettingsIntegration:
    """Integration tests for settings workflow."""

    def test_load_save_roundtrip(self, tmp_path):
        """Test that save then load preserves settings."""
        dojo_path = tmp_path / ".dojo"

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        # Save custom settings
        original = Settings(leetcode=LeetCodeSettings(organization="difficulty"))
        manager.save(original)

        # Load and verify
        loaded = manager.load()
        assert loaded.leetcode.organization == "difficulty"

    def test_get_set_roundtrip(self, tmp_path):
        """Test that set then get preserves value."""
        dojo_path = tmp_path / ".dojo"

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        # Create initial file
        manager.create_default()

        # Set value
        result = manager.set("leetcode.organization", "difficulty")
        assert result is True

        # Get and verify
        value = manager.get("leetcode.organization")
        assert value == "difficulty"

    def test_create_default_then_load(self, tmp_path):
        """Test creating default then loading."""
        dojo_path = tmp_path / ".dojo"

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        manager.create_default()
        settings = manager.load()

        assert settings.leetcode.organization == "flat"

    def test_modify_and_save_preserves_other_settings(self, tmp_path):
        """Test that modifying one setting preserves others."""
        dojo_path = tmp_path / ".dojo"

        with patch("bytedojo.core.settings.get_logger"):
            manager = SettingsManager(dojo_path)

        # Create with defaults
        manager.create_default()

        # Modify
        manager.set("leetcode.organization", "difficulty")

        # Load and verify all settings
        settings = manager.load()
        assert settings.leetcode.organization == "difficulty"
