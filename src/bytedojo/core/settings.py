"""
Settings management for bytedojo.

.dojo/settings.json is the single home for user preferences:

    default_language     language used when no --<lang> flag is given
    review_frequency_days  base SM-2 interval (§8 base_days)
    organize_by_language next-attempt paths gain a <language>/ segment

Internal repository state (initialized_at, default_source) lives in the
sqlite config table instead — one home per key.
"""

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Optional

from bytedojo.core.logger import get_logger

#: CLI-facing setting keys (kebab-case) → Settings attribute names.
SETTING_KEYS = {
    "default-language": "default_language",
    "review-frequency": "review_frequency_days",
    "organize-by-language": "organize_by_language",
}

#: Languages a user may select as default (user-facing names).
SUPPORTED_LANGUAGES = ("python",)

_TRUTHY = {"true", "1", "yes", "on"}
_FALSY = {"false", "0", "no", "off"}


@dataclass
class Settings:
    """All bytedojo user preferences."""

    default_language: str = "python"
    review_frequency_days: int = 7
    organize_by_language: bool = False

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


class SettingsManager:
    """Manages settings stored in .dojo/settings.json."""

    def __init__(self, dojo_path: Path):
        self.dojo_path = dojo_path
        self.settings_path = dojo_path / "settings.json"
        self.logger = get_logger()

    def load(self) -> Settings:
        """Settings from file; defaults when absent or unreadable."""
        if not self.settings_path.exists():
            return Settings()
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Settings.from_dict(data)
        except (OSError, json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"Error loading settings: {e}")
            return Settings()

    def save(self, settings: Settings) -> None:
        """Write settings to file, creating the directory if needed."""
        self.dojo_path.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, indent=2)
        self.logger.debug(f"Saved settings to {self.settings_path}")

    def get(self, key: str) -> Optional[Any]:
        """Value for a CLI-facing key, or None if the key is unknown."""
        attr = SETTING_KEYS.get(key)
        if attr is None:
            return None
        return getattr(self.load(), attr)

    def set(self, key: str, value: str) -> Any:
        """Parse, validate and persist `value` for a CLI-facing key.

        Returns the stored (typed) value.

        Raises:
            KeyError: unknown setting key.
            ValueError: value malformed or out of range for the key.
        """
        attr = SETTING_KEYS.get(key)
        if attr is None:
            raise KeyError(key)

        settings = self.load()
        parsed = _parse_value(attr, value)
        setattr(settings, attr, parsed)
        self.save(settings)
        return parsed

    def create_default(self) -> None:
        """Create the default settings file if it doesn't exist."""
        if not self.settings_path.exists():
            self.save(Settings())
            self.logger.debug("Created default settings file")


def _parse_value(attr: str, value: str) -> Any:
    """Validate a raw CLI string for a Settings attribute."""
    if attr == "default_language":
        language = value.lower()
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language {value!r}. "
                f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
            )
        return language

    if attr == "review_frequency_days":
        try:
            days = int(value)
        except ValueError:
            raise ValueError(f"Review frequency must be a number, got {value!r}")
        if days < 1:
            raise ValueError("Review frequency must be at least 1 day")
        if days > 365:
            raise ValueError("Review frequency cannot exceed 365 days")
        return days

    # organize_by_language
    lowered = str(value).lower()
    if lowered in _TRUTHY:
        return True
    if lowered in _FALSY:
        return False
    raise ValueError(f"Expected true/false, got {value!r}")
