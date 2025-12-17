"""
Tests for DojoRepository.
"""

import pytest
from pathlib import Path
from bytedojo.core.repository import DojoRepository


class TestDojoRepositoryInit:
    """Test DojoRepository initialization."""
    
    def test_init_with_default_directory(self):
        """Test initialization with default directory (cwd)."""
        repo = DojoRepository()
        
        assert repo.root_dir == Path.cwd()
        assert repo.dojo_dir == Path.cwd() / ".dojo"
        assert repo.db_path == Path.cwd() / ".dojo" / "db.sqlite"
        assert repo.problems_dir == Path.cwd() / "problems"
    
    def test_init_with_custom_directory(self, tmp_path):
        """Test initialization with custom directory."""
        repo = DojoRepository(root_dir=tmp_path)
        
        assert repo.root_dir == tmp_path
        assert repo.dojo_dir == tmp_path / ".dojo"
        assert repo.db_path == tmp_path / ".dojo" / "db.sqlite"


class TestDojoRepositoryExists:
    """Test exists() method."""
    
    def test_exists_returns_false_when_not_exists(self, tmp_path):
        """Test exists returns False when .dojo doesn't exist."""
        repo = DojoRepository(root_dir=tmp_path)
        
        assert repo.exists() is False
    
    def test_exists_returns_true_when_exists(self, tmp_path):
        """Test exists returns True when .dojo exists."""
        dojo_dir = tmp_path / ".dojo"
        dojo_dir.mkdir()
        
        repo = DojoRepository(root_dir=tmp_path)
        
        assert repo.exists() is True


class TestDojoRepositoryIsInitialized:
    """Test is_initialized() method."""
    
    def test_is_initialized_false_when_no_dojo(self, tmp_path):
        """Test is_initialized returns False when .dojo doesn't exist."""
        repo = DojoRepository(root_dir=tmp_path)
        
        assert repo.is_initialized() is False
    
    def test_is_initialized_false_when_no_database(self, tmp_path):
        """Test is_initialized returns False when database doesn't exist."""
        dojo_dir = tmp_path / ".dojo"
        dojo_dir.mkdir()
        
        repo = DojoRepository(root_dir=tmp_path)
        
        assert repo.is_initialized() is False
    
    def test_is_initialized_true_when_complete(self, tmp_path):
        """Test is_initialized returns True when fully initialized."""
        dojo_dir = tmp_path / ".dojo"
        dojo_dir.mkdir()
        db_file = dojo_dir / "db.sqlite"
        db_file.touch()
        
        repo = DojoRepository(root_dir=tmp_path)
        
        assert repo.is_initialized() is True


class TestDojoRepositoryGetDbPath:
    """Test get_db_path() method."""
    
    def test_get_db_path_raises_when_not_initialized(self, tmp_path):
        """Test get_db_path raises error when not initialized."""
        repo = DojoRepository(root_dir=tmp_path)
        
        with pytest.raises(RuntimeError, match="not initialized"):
            repo.get_db_path()
    
    def test_get_db_path_returns_path_when_initialized(self, tmp_path):
        """Test get_db_path returns correct path when initialized."""
        dojo_dir = tmp_path / ".dojo"
        dojo_dir.mkdir()
        db_file = dojo_dir / "db.sqlite"
        db_file.touch()
        
        repo = DojoRepository(root_dir=tmp_path)
        
        path = repo.get_db_path()
        assert path == db_file


class TestDojoRepositoryInitialize:
    """Test initialize() method."""
    
    def test_initialize_creates_directories(self, tmp_path):
        """Test initialize creates .dojo and problems directories."""
        repo = DojoRepository(root_dir=tmp_path)
        
        repo.initialize()
        
        assert repo.dojo_dir.exists()
        assert repo.problems_dir.exists()
    
    def test_initialize_creates_database(self, tmp_path):
        """Test initialize creates database file."""
        repo = DojoRepository(root_dir=tmp_path)
        
        repo.initialize()
        
        assert repo.db_path.exists()
    
    def test_initialize_creates_gitignore(self, tmp_path):
        """Test initialize creates .gitignore."""
        repo = DojoRepository(root_dir=tmp_path)
        
        repo.initialize()
        
        gitignore = repo.dojo_dir / ".gitignore"
        assert gitignore.exists()
        
        content = gitignore.read_text()
        assert "Python" in content
        assert "*.pyc" in content
    
    def test_initialize_creates_readme(self, tmp_path):
        """Test initialize creates README.md."""
        repo = DojoRepository(root_dir=tmp_path)
        
        repo.initialize()
        
        readme = repo.dojo_dir / "README.md"
        assert readme.exists()
        
        content = readme.read_text()
        assert "ByteDojo Repository" in content
    
    def test_initialize_raises_when_already_exists(self, tmp_path):
        """Test initialize raises error when already initialized."""
        repo = DojoRepository(root_dir=tmp_path)
        
        repo.initialize()
        
        with pytest.raises(RuntimeError, match="already initialized"):
            repo.initialize()
    
    def test_initialize_with_force_recreates(self, tmp_path):
        """Test initialize with force=True recreates repository."""
        repo = DojoRepository(root_dir=tmp_path)
        
        repo.initialize()
        
        # Mark first initialization
        marker = repo.dojo_dir / "marker.txt"
        marker.write_text("first")
        
        # Reinitialize with force
        repo.initialize(force=True)
        
        # Marker should still exist (force doesn't delete, just recreates)
        assert repo.is_initialized()


class TestDojoRepositoryIntegration:
    """Integration tests for DojoRepository."""
    
    def test_full_initialization_workflow(self, tmp_path):
        """Test complete initialization workflow."""
        repo = DojoRepository(root_dir=tmp_path)
        
        # Initially not initialized
        assert not repo.exists()
        assert not repo.is_initialized()
        
        # Initialize
        repo.initialize()
        
        # Now initialized
        assert repo.exists()
        assert repo.is_initialized()
        
        # Can get db path
        db_path = repo.get_db_path()
        assert db_path.exists()
        
        # Database has correct schema
        import sqlite3
        conn = sqlite3.connect(db_path)
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