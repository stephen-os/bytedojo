"""
Settings management for bytedojo.

Stores user preferences in .dojo/settings.json.
"""

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict, field

from bytedojo.core.logger import get_logger


@dataclass
class LeetCodeSettings:
    """LeetCode-specific settings."""
    organization: str = "flat"  # "flat" or "difficulty"


@dataclass
class Settings:
    """All bytedojo settings."""
    leetcode: LeetCodeSettings = field(default_factory=LeetCodeSettings)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "leetcode": asdict(self.leetcode)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """Create from dictionary."""
        leetcode_data = data.get("leetcode", {})
        return cls(
            leetcode=LeetCodeSettings(**leetcode_data)
        )


class SettingsManager:
    """Manages settings stored in .dojo/settings.json."""

    DEFAULT_SETTINGS = Settings()

    def __init__(self, dojo_path: Path):
        """
        Initialize settings manager.

        Args:
            dojo_path: Path to .dojo directory
        """
        self.dojo_path = dojo_path
        self.settings_path = dojo_path / "settings.json"
        self.logger = get_logger()

    def load(self) -> Settings:
        """
        Load settings from file.

        Returns:
            Settings object (defaults if file doesn't exist)
        """
        if not self.settings_path.exists():
            return Settings()

        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Settings.from_dict(data)
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            return Settings()

    def save(self, settings: Settings) -> None:
        """
        Save settings to file.

        Args:
            settings: Settings object to save
        """
        # Ensure directory exists
        self.dojo_path.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, indent=2)
            self.logger.debug(f"Saved settings to {self.settings_path}")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            raise

    def get(self, key: str) -> Any:
        """
        Get a setting value by dot-notation key.

        Args:
            key: Setting key (e.g., "leetcode.organization")

        Returns:
            Setting value or None if not found
        """
        settings = self.load()
        parts = key.split(".")

        obj: Any = settings
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return None
        return obj

    def set(self, key: str, value: Any) -> bool:
        """
        Set a setting value by dot-notation key.

        Args:
            key: Setting key (e.g., "leetcode.organization")
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        settings = self.load()
        parts = key.split(".")

        if len(parts) < 2:
            self.logger.error(f"Invalid setting key: {key}")
            return False

        # Navigate to parent object
        obj: Any = settings
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                self.logger.error(f"Unknown setting: {key}")
                return False

        # Set the value
        final_key = parts[-1]
        if hasattr(obj, final_key):
            setattr(obj, final_key, value)
            self.save(settings)
            return True
        else:
            self.logger.error(f"Unknown setting: {key}")
            return False

    def create_default(self) -> None:
        """Create default settings file if it doesn't exist."""
        if not self.settings_path.exists():
            self.save(Settings())
            self.logger.debug("Created default settings file")
