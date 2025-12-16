"""
Tests for the init command.
"""

import pytest
import sqlite3
from pathlib import Path
from click.testing import CliRunner

from bytedojo.commands.dojo import dojo


class TestInitCommand:
    """Test the init command."""
    
    def test_init_creates_dojo_directory(self, tmp_path):
        """Test that init creates .dojo directory."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['init'])
            
            assert result.exit_code == 0
            assert Path('.dojo').exists()
            assert Path('.dojo').is_dir()
    
    def test_init_creates_database(self, tmp_path):
        """Test that init creates database file."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['init'])
            
            assert result.exit_code == 0
            db_path = Path('.dojo/db.sqlite')
            assert db_path.exists()
            assert db_path.is_file()
    
    def test_init_creates_problems_directory(self, tmp_path):
        """Test that init creates problems directory."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['init'])
            
            assert result.exit_code == 0
            assert Path('problems').exists()
            assert Path('problems').is_dir()
    
    def test_init_creates_gitignore(self, tmp_path):
        """Test that init creates .gitignore."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['init'])
            
            assert result.exit_code == 0
            gitignore = Path('.dojo/.gitignore')
            assert gitignore.exists()
            
            content = gitignore.read_text()
            assert '# Python' in content
            assert '__pycache__/' in content
            assert 'logs/' in content
    
    def test_init_creates_readme(self, tmp_path):
        """Test that init creates README."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['init'])
            
            assert result.exit_code == 0
            readme = Path('.dojo/README.md')
            assert readme.exists()
            
            content = readme.read_text()
            assert 'ByteDojo Repository' in content
            assert 'Database Schema' in content
    
    def test_init_fails_if_already_initialized(self, tmp_path):
        """Test that init fails if .dojo already exists."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First init - should succeed
            result = runner.invoke(dojo, ['init'])
            assert result.exit_code == 0
            
            # Second init - should fail
            result = runner.invoke(dojo, ['init'])
            assert result.exit_code != 0
            assert 'already initialized' in result.output.lower()
    
    def test_init_force_flag_reinitializes(self, tmp_path):
        """Test that --force flag allows reinitializing."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First init
            result = runner.invoke(dojo, ['init'])
            assert result.exit_code == 0
            
            # Second init with --force should succeed
            result = runner.invoke(dojo, ['init', '--force'])
            assert result.exit_code == 0
            assert Path('.dojo').exists()
    
    def test_init_output_messages(self, tmp_path):
        """Test that init shows appropriate messages."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['init'])
            
            assert result.exit_code == 0
            assert 'Initializing ByteDojo repository' in result.output
            assert 'initialized successfully' in result.output
            assert 'Next steps' in result.output


class TestDatabaseSchema:
    """Test the database schema created by init."""
    
    def test_problems_table_exists(self, tmp_path):
        """Test that problems table is created."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='problems'
            """)
            assert cursor.fetchone() is not None
            conn.close()
    
    def test_problems_table_schema(self, tmp_path):
        """Test problems table has correct columns."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(problems)")
            columns = {row[1] for row in cursor.fetchall()}
            
            expected_columns = {
                'id', 'source', 'problem_id', 'title', 'difficulty',
                'category', 'tags', 'description', 'file_path', 'fetched_at'
            }
            assert expected_columns.issubset(columns)
            conn.close()
    
    def test_attempts_table_exists(self, tmp_path):
        """Test that attempts table is created."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='attempts'
            """)
            assert cursor.fetchone() is not None
            conn.close()
    
    def test_attempts_table_schema(self, tmp_path):
        """Test attempts table has correct columns."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(attempts)")
            columns = {row[1] for row in cursor.fetchall()}
            
            expected_columns = {
                'id', 'problem_id', 'attempted_at', 'passed',
                'time_taken', 'notes'
            }
            assert expected_columns.issubset(columns)
            conn.close()
    
    def test_reviews_table_exists(self, tmp_path):
        """Test that reviews table is created."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='reviews'
            """)
            assert cursor.fetchone() is not None
            conn.close()
    
    def test_reviews_table_schema(self, tmp_path):
        """Test reviews table has correct columns."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(reviews)")
            columns = {row[1] for row in cursor.fetchall()}
            
            expected_columns = {
                'id', 'problem_id', 'next_review_date', 'interval_days',
                'ease_factor', 'repetitions'
            }
            assert expected_columns.issubset(columns)
            conn.close()
    
    def test_stats_table_exists(self, tmp_path):
        """Test that stats table is created."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='stats'
            """)
            assert cursor.fetchone() is not None
            conn.close()
    
    def test_stats_table_schema(self, tmp_path):
        """Test stats table has correct columns."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(stats)")
            columns = {row[1] for row in cursor.fetchall()}
            
            expected_columns = {
                'id', 'date', 'problems_attempted', 'problems_solved',
                'total_time_minutes'
            }
            assert expected_columns.issubset(columns)
            conn.close()
    
    def test_config_table_exists(self, tmp_path):
        """Test that config table is created."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='config'
            """)
            assert cursor.fetchone() is not None
            conn.close()
    
    def test_config_has_default_values(self, tmp_path):
        """Test that config table has default values."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("SELECT key, value FROM config")
            config = dict(cursor.fetchall())
            
            assert 'initialized_at' in config
            assert 'default_language' in config
            assert config['default_language'] == 'python'
            assert 'default_source' in config
            assert config['default_source'] == 'leetcode'
            assert 'problems_dir' in config
            assert config['problems_dir'] == 'problems'
            
            conn.close()
    
    def test_foreign_key_constraints(self, tmp_path):
        """Test that foreign key constraints are set up."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            # Check attempts table foreign key
            cursor.execute("PRAGMA foreign_key_list(attempts)")
            fk = cursor.fetchone()
            assert fk is not None
            assert fk[2] == 'problems'  # References problems table
            
            # Check reviews table foreign key
            cursor.execute("PRAGMA foreign_key_list(reviews)")
            fk = cursor.fetchone()
            assert fk is not None
            assert fk[2] == 'problems'  # References problems table
            
            conn.close()
    
    def test_unique_constraint_on_problems(self, tmp_path):
        """Test that problems table has unique constraint on source+problem_id."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            conn = sqlite3.connect('.dojo/db.sqlite')
            cursor = conn.cursor()
            
            # Try to insert duplicate
            cursor.execute("""
                INSERT INTO problems (source, problem_id, title)
                VALUES ('leetcode', '1', 'Two Sum')
            """)
            
            # This should raise an error due to unique constraint
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO problems (source, problem_id, title)
                    VALUES ('leetcode', '1', 'Two Sum Duplicate')
                """)
            
            conn.close()


class TestInitDebugMode:
    """Test init command in debug mode."""
    
    def test_init_debug_mode_verbose(self, tmp_path):
        """Test that debug mode shows verbose output."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['--debug', 'init'])
            
            assert result.exit_code == 0
            # Debug mode should show more details
            assert 'DEBUG' in result.output or 'Creating' in result.output


class TestInitFileEncoding:
    """Test that files are created with correct encoding."""
    
    def test_gitignore_utf8_encoding(self, tmp_path):
        """Test that .gitignore uses UTF-8 encoding."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            gitignore = Path('.dojo/.gitignore')
            # Should not raise encoding errors
            content = gitignore.read_text(encoding='utf-8')
            assert len(content) > 0
    
    def test_readme_utf8_encoding(self, tmp_path):
        """Test that README uses UTF-8 encoding."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(dojo, ['init'])
            
            readme = Path('.dojo/README.md')
            # Should not raise encoding errors
            content = readme.read_text(encoding='utf-8')
            assert len(content) > 0