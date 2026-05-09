"""
Tests for Repository.
"""

import pytest
from pathlib import Path
from bytedojo.core.repository import Repository


class TestRepositoryInit:
    """Test Repository initialization."""

    def test_init_requires_root_dir(self):
        """Test that root_dir is required."""
        import pytest
        with pytest.raises(TypeError):
            Repository()

    def test_init_with_directory(self, tmp_path):
        """Test initialization with custom directory."""
        repo = Repository(root_dir=tmp_path)

        assert repo.root_dir == tmp_path
        assert repo.dojo_dir == tmp_path / ".dojo"
        assert repo.db_path == tmp_path / ".dojo" / "db.sqlite"

class TestRepositoryExists:
    """Test exists property."""

    def test_exists_returns_false_when_not_exists(self, tmp_path):
        """Test exists returns False when .dojo doesn't exist."""
        repo = Repository(root_dir=tmp_path)

        assert repo.exists is False

    def test_exists_returns_true_when_exists(self, tmp_path):
        """Test exists returns True when .dojo exists."""
        dojo_dir = tmp_path / ".dojo"
        dojo_dir.mkdir()

        repo = Repository(root_dir=tmp_path)

        assert repo.exists is True


class TestRepositoryIsInitialized:
    """Test is_initialized property."""

    def test_is_initialized_false_when_no_dojo(self, tmp_path):
        """Test is_initialized returns False when .dojo doesn't exist."""
        repo = Repository(root_dir=tmp_path)

        assert repo.is_initialized is False

    def test_is_initialized_false_when_no_database(self, tmp_path):
        """Test is_initialized returns False when database doesn't exist."""
        dojo_dir = tmp_path / ".dojo"
        dojo_dir.mkdir()

        repo = Repository(root_dir=tmp_path)

        assert repo.is_initialized is False

    def test_is_initialized_true_when_complete(self, tmp_path):
        """Test is_initialized returns True when fully initialized."""
        dojo_dir = tmp_path / ".dojo"
        dojo_dir.mkdir()
        db_file = dojo_dir / "db.sqlite"
        db_file.touch()

        repo = Repository(root_dir=tmp_path)

        assert repo.is_initialized is True


class TestRepositoryPaths:
    """Test path properties."""

    def test_db_path(self, tmp_path):
        """Test db_path returns correct path."""
        repo = Repository(root_dir=tmp_path)

        assert repo.db_path == tmp_path / ".dojo" / "db.sqlite"

    def test_build_dir(self, tmp_path):
        """Test build_dir returns correct path."""
        repo = Repository(root_dir=tmp_path)

        assert repo.build_dir == tmp_path / ".dojo" / "build"

    def test_problems_dir(self, tmp_path):
        """Test problems_dir returns correct path."""
        repo = Repository(root_dir=tmp_path)

        assert repo.problems_dir == tmp_path / "problems"


class TestRepositoryCreate:
    """Test create() method."""

    def test_create_creates_directories(self, tmp_path):
        """Test create creates .dojo directory and settings file."""
        repo = Repository(root_dir=tmp_path)

        result = repo.create()

        assert result.success
        assert repo.dojo_dir.exists()
        assert repo.settings_path.exists()

    def test_create_creates_database(self, tmp_path):
        """Test create creates database file."""
        repo = Repository(root_dir=tmp_path)

        result = repo.create()

        assert result.success
        assert repo.db_path.exists()

    def test_create_creates_gitignore(self, tmp_path):
        """Test create creates .gitignore."""
        repo = Repository(root_dir=tmp_path)

        repo.create()

        gitignore = repo.dojo_dir / ".gitignore"
        assert gitignore.exists()

        content = gitignore.read_text()
        assert "Python" in content
        assert "*.pyc" in content

    def test_create_creates_readme(self, tmp_path):
        """Test create creates README.md."""
        repo = Repository(root_dir=tmp_path)

        repo.create()

        readme = repo.dojo_dir / "README.md"
        assert readme.exists()

        content = readme.read_text()
        assert "ByteDojo Repository" in content

    def test_create_returns_failure_when_already_exists(self, tmp_path):
        """Test create returns failure when already initialized."""
        repo = Repository(root_dir=tmp_path)

        repo.create()
        result = repo.create()

        assert not result.success

    def test_create_with_force_recreates(self, tmp_path):
        """Test create with force=True recreates repository."""
        repo = Repository(root_dir=tmp_path)

        repo.create()

        # Mark first initialization
        marker = repo.dojo_dir / "marker.txt"
        marker.write_text("first")

        # Reinitialize with force
        result = repo.create(force=True)

        assert result.success
        assert repo.is_initialized

    def test_create_returns_result(self, tmp_path):
        """Test create returns Result dataclass."""
        repo = Repository(root_dir=tmp_path)

        result = repo.create()

        assert hasattr(result, 'success')
        assert hasattr(result, 'message')


class TestRepositoryIntegration:
    """Integration tests for Repository."""

    def test_full_workflow(self, tmp_path):
        """Test complete repository workflow."""
        repo = Repository(root_dir=tmp_path)

        # Initially not initialized
        assert not repo.exists
        assert not repo.is_initialized

        # Create
        result = repo.create()

        # Check result
        assert result.success

        # Now initialized
        assert repo.exists
        assert repo.is_initialized

        # Can access db path
        assert repo.db_path.exists()

        # Database has correct schema
        import sqlite3
        conn = sqlite3.connect(repo.db_path)
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = {row[0] for row in cursor.fetchall()}

        assert 'problems' in tables
        assert 'attempts' in tables
        assert 'reviews' in tables
        assert 'stats' in tables
        assert 'config' in tables

        conn.close()
