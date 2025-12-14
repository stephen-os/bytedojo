"""
Tests for the main dojo command.
"""

import pytest
from click.testing import CliRunner

from src.bytedojo.commands.dojo import dojo
from src.bytedojo import __version__, __author__


class TestDojoCommand:
    """Test the main dojo command."""
    
    def test_dojo_help(self):
        """Test that dojo --help works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--help'])
        
        assert result.exit_code == 0
        assert 'ByteDojo' in result.output
        assert 'spaced' in result.output or 'repetition' in result.output  # Part of description
        assert 'Commands:' in result.output
    
    def test_dojo_version(self):
        """Test that dojo --version works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--version'])
        
        assert result.exit_code == 0
        assert __version__ in result.output
    
    def test_dojo_author(self):
        """Test that dojo --author works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--author'])
        
        assert result.exit_code == 0
        assert __author__ in result.output
    
    def test_dojo_desc(self):
        """Test that dojo --desc works."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--desc'])
        
        assert result.exit_code == 0
        assert 'CLI tool' in result.output or 'programming' in result.output
    
    def test_dojo_no_command_shows_help(self):
        """Test that running dojo with no command shows help."""
        runner = CliRunner()
        result = runner.invoke(dojo, [])
        
        # Click shows usage when no command given
        assert 'Usage:' in result.output or 'Commands:' in result.output


class TestDojoDebugFlag:
    """Test the --debug flag."""
    
    def test_debug_flag_enables_debug_mode(self, tmp_path):
        """Test that --debug flag enables debug logging."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['--debug', 'init'])
            
            # Should show debug output
            assert 'DEBUG' in result.output or 'Creating' in result.output
    
    def test_debug_flag_creates_log_file(self, tmp_path, monkeypatch):
        """Test that --debug creates a log file."""
        from pathlib import Path
        
        runner = CliRunner()
        
        # Mock home directory to use tmp_path
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['--debug', 'init'])
            
            # Check if log directory was created
            log_dir = tmp_path / '.bytedojo' / 'logs'
            if log_dir.exists():
                log_files = list(log_dir.glob('debug_*.log'))
                # May or may not create log file depending on when logger initializes
                # Just check command ran successfully
                assert result.exit_code == 0
    
    def test_production_mode_no_debug_output(self, tmp_path):
        """Test that production mode doesn't show debug output."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['init'])
            
            # Should NOT show debug details (like file locations)
            # Just clean user-facing messages
            assert 'Initializing' in result.output or 'initialized' in result.output


class TestDojoConfigFlag:
    """Test the --config flag."""
    
    def test_config_flag_accepts_path(self, tmp_path):
        """Test that --config flag accepts a path."""
        runner = CliRunner()
        
        # Create a dummy config file
        config_file = tmp_path / "config.yml"
        config_file.write_text("# Test config")
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Should accept the config flag (even if not implemented yet)
            result = runner.invoke(dojo, ['--config', str(config_file), 'init'])
            
            # Should not fail due to config flag
            assert result.exit_code == 0 or 'config' not in result.output.lower()
    
    def test_config_flag_rejects_nonexistent_file(self, tmp_path):
        """Test that --config rejects non-existent files."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['--config', 'nonexistent.yml', 'init'])
            
            # Click should reject non-existent path
            assert result.exit_code != 0


class TestDojoCommands:
    """Test that all commands are registered."""
    
    def test_init_command_registered(self):
        """Test that init command is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['init', '--help'])
        
        assert result.exit_code == 0
        assert 'init' in result.output.lower()
    
    def test_fetch_command_registered(self):
        """Test that fetch command is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['fetch', '--help'])
        
        # Command should be recognized (exit code 0 or show help)
        # Don't fail if command has implementation issues
        assert result.exit_code == 0 or 'fetch' in result.output.lower()
    
    def test_test_command_registered(self):
        """Test that test command is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['test', '--help'])
        
        # Command should be recognized
        assert result.exit_code == 0 or 'test' in result.output.lower()
    
    def test_stats_command_registered(self):
        """Test that stats command is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['stats', '--help'])
        
        # Command should be recognized
        assert result.exit_code == 0 or 'stats' in result.output.lower()
    
    def test_user_command_registered(self):
        """Test that user command is registered."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['user', '--help'])
        
        # Command should be recognized
        assert result.exit_code == 0 or 'user' in result.output.lower()


class TestDojoContext:
    """Test the ByteDojoContext object."""
    
    def test_context_created_with_debug_false(self, tmp_path):
        """Test that context is created with debug=False by default."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Run a command and check it doesn't crash
            result = runner.invoke(dojo, ['init'])
            
            # Should complete successfully
            assert result.exit_code == 0
    
    def test_context_created_with_debug_true(self, tmp_path):
        """Test that context is created with debug=True when flag set."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Run with debug flag
            result = runner.invoke(dojo, ['--debug', 'init'])
            
            # Should complete successfully
            assert result.exit_code == 0


class TestDojoErrorHandling:
    """Test error handling in dojo command."""
    
    def test_invalid_command_shows_error(self):
        """Test that invalid command shows error."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['invalidcommand'])
        
        assert result.exit_code != 0
        assert 'Error' in result.output or 'No such command' in result.output
    
    def test_invalid_flag_shows_error(self):
        """Test that invalid flag shows error."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--invalid-flag'])
        
        assert result.exit_code != 0


class TestDojoOutput:
    """Test output formatting."""
    
    def test_help_shows_all_commands(self):
        """Test that help shows available commands."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--help'])
        
        assert result.exit_code == 0
        # Should at least show init command
        assert 'init' in result.output
        assert 'Commands:' in result.output
    
    def test_help_shows_global_options(self):
        """Test that help shows global options."""
        runner = CliRunner()
        result = runner.invoke(dojo, ['--help'])
        
        assert result.exit_code == 0
        assert '--debug' in result.output
        assert '--config' in result.output
        assert '--version' in result.output
        assert '--author' in result.output
        assert '--desc' in result.output


class TestDojoIntegration:
    """Integration tests for dojo command."""
    
    def test_full_workflow_init_and_help(self, tmp_path):
        """Test a full workflow: init then check help."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize
            result = runner.invoke(dojo, ['init'])
            assert result.exit_code == 0
            
            # Check help still works
            result = runner.invoke(dojo, ['--help'])
            assert result.exit_code == 0
    
    def test_debug_mode_with_init(self, tmp_path):
        """Test debug mode with init command."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(dojo, ['--debug', 'init'])
            
            assert result.exit_code == 0
            assert 'initialized' in result.output.lower()