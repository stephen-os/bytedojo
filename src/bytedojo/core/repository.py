"""
Repository management for .dojo directories.

Handles checking for .dojo existence, initialization status, etc.
"""

from pathlib import Path

from bytedojo.core.database import create_database_schema
from bytedojo.core.templates import GITIGNORE, README

from bytedojo.core.result import Result

class Repository:
    """Manages .dojo repository paths and initialization."""

    def __init__(self, root_dir: Path):
        """
        Initialize repository manager.

        Args:
            root_dir: Root directory containing .dojo.
        """
        self.root_dir = root_dir
        self.dojo_dir = self.root_dir / ".dojo"
        self.db_path = self.dojo_dir / "db.sqlite"
        self.settings_path = self.dojo_dir / "settings.json"

    @property
    def exists(self) -> bool:
        """Check if .dojo directory exists."""
        return self.dojo_dir.exists()

    @property
    def is_initialized(self) -> bool:
        """Check if .dojo is properly initialized with database."""
        return self.exists and self.db_path.exists()

    @property
    def build_dir(self) -> Path:
        """Get path to build directory."""
        return self.dojo_dir / "build"

    @property
    def problems_dir(self) -> Path:
        """Get path to problems directory."""
        return self.root_dir / "problems"

    def create(self, force: bool = False) -> Result:
        """
        Initialize the repository.

        Args:
            force: If True, reinitialize even if exists

        Returns:
            Result with success status and message
        """

        # If .dojo already exists and we're not forcing, return False
        if self.exists and not force:
            return Result(success=False, message=".dojo already exists. Use --force to reinitialize.")

        # Create .dojo directory
        self.dojo_dir.mkdir(exist_ok=True)

        # Create database
        create_database_schema(self.db_path)

        # Create default settings
        self._create_default_settings()

        # Create .gitignore
        self._create_gitignore()

        # Create README
        self._create_readme()

        return Result(success=True, message="Repository initialized successfully.")

    def _create_default_settings(self):
        """Create default settings.json file."""
        from bytedojo.core.settings import SettingsManager
        settings_manager = SettingsManager(self.dojo_dir)
        settings_manager.create_default()

    def _create_gitignore(self):
        """Create .gitignore for the .dojo directory."""
        gitignore = self.dojo_dir / ".gitignore"
        gitignore.write_text(GITIGNORE, encoding='utf-8')

    def _create_readme(self):
        """Create README in .dojo directory."""
        readme = self.dojo_dir / "README.md"
        readme.write_text(README, encoding='utf-8')