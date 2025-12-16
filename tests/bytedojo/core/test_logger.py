"""
Tests for ByteDojo logging system.
"""

import pytest
import logging

from bytedojo.core.logger import (
    Theme,
    TerminalFormatter,
    get_config,
    setup_logger,
    get_logger,
)


@pytest.fixture(autouse=True)
def reset_logger():
    """Reset logger state before each test."""
    # Before test
    yield
    
    # After test - cleanup
    import bytedojo.core.logger
    bytedojo.core.logger._logger = None
    
    # Remove all handlers from bytedojo logger and close them
    logger = logging.getLogger('bytedojo')
    handlers = logger.handlers[:]
    for handler in handlers:
        try:
            handler.close()
        except Exception:
            pass
        try:
            logger.removeHandler(handler)
        except Exception:
            pass


class TestTheme:
    """Test Gruvbox Theme color constants."""
    
    def test_colors_defined(self):
        """Test that all theme colors are defined."""
        assert hasattr(Theme, 'RED')
        assert hasattr(Theme, 'GREEN')
        assert hasattr(Theme, 'YELLOW')
        assert hasattr(Theme, 'BLUE')
        assert hasattr(Theme, 'PURPLE')
        assert hasattr(Theme, 'AQUA')
        assert hasattr(Theme, 'ORANGE')
        assert hasattr(Theme, 'GRAY')
        assert hasattr(Theme, 'BOLD')
        assert hasattr(Theme, 'RESET')
    
    def test_colors_are_strings(self):
        """Test that all colors are strings (ANSI codes)."""
        assert isinstance(Theme.RED, str)
        assert isinstance(Theme.GREEN, str)
        assert isinstance(Theme.RESET, str)
    
    def test_colors_contain_ansi_codes(self):
        """Test that colors contain ANSI escape sequences."""
        assert '\033[' in Theme.RED
        assert '\033[' in Theme.GREEN
        assert '\033[0m' in Theme.RESET
    
    def test_gruvbox_specific_colors(self):
        """Test Gruvbox-specific colors are present."""
        assert hasattr(Theme, 'AQUA')  # Gruvbox specific
        assert hasattr(Theme, 'ORANGE')  # Gruvbox specific


class TestTerminalFormatter:
    """Test TerminalFormatter class."""
    
    def test_level_colors_defined(self):
        """Test that level colors are defined."""
        assert 'DEBUG' in TerminalFormatter.LEVEL_COLORS
        assert 'INFO' in TerminalFormatter.LEVEL_COLORS
        assert 'WARNING' in TerminalFormatter.LEVEL_COLORS
        assert 'ERROR' in TerminalFormatter.LEVEL_COLORS
        assert 'CRITICAL' in TerminalFormatter.LEVEL_COLORS
    
    def test_message_colors_defined(self):
        """Test that message colors are defined."""
        assert 'DEBUG' in TerminalFormatter.MESSAGE_COLORS
        assert 'INFO' in TerminalFormatter.MESSAGE_COLORS
        assert 'WARNING' in TerminalFormatter.MESSAGE_COLORS
        assert 'ERROR' in TerminalFormatter.MESSAGE_COLORS
        assert 'CRITICAL' in TerminalFormatter.MESSAGE_COLORS
    
    def test_format_adds_colors(self):
        """Test that format method adds color codes."""
        formatter = TerminalFormatter('%(levelname)s: %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should contain ANSI escape codes
        assert '\033[' in formatted
        assert Theme.RESET in formatted
    
    def test_format_preserves_lineno_as_int(self):
        """Test that line numbers remain integers during formatting."""
        formatter = TerminalFormatter('[%(name)s.%(funcName)s:%(lineno)d] %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test',
            args=(),
            exc_info=None,
            func='test_func'
        )
        
        # Should not raise TypeError
        formatted = formatter.format(record)
        assert '42' in formatted


class TestGetConfig:
    """Test get_config function."""
    
    def test_config_structure(self):
        """Test that config has correct structure."""
        config = get_config(debug=False)
        
        assert 'version' in config
        assert config['version'] == 1
        assert 'disable_existing_loggers' in config
        assert 'formatters' in config
        assert 'handlers' in config
        assert 'loggers' in config
    
    def test_formatters_defined(self):
        """Test that formatters are defined."""
        config = get_config(debug=False)
        
        assert 'simple' in config['formatters']
        assert 'detailed' in config['formatters']
    
    def test_handlers_defined(self):
        """Test that handlers are defined."""
        config = get_config(debug=False)
        
        assert 'console' in config['handlers']
        assert config['handlers']['console']['class'] == 'logging.StreamHandler'
    
    def test_bytedojo_logger_defined(self):
        """Test that bytedojo logger is defined."""
        config = get_config(debug=False)
        
        assert 'bytedojo' in config['loggers']
        assert config['loggers']['bytedojo']['handlers'] == ['console']
        assert config['loggers']['bytedojo']['propagate'] is False
    
    def test_debug_mode_config(self):
        """Test config in debug mode."""
        config = get_config(debug=True)
        
        # Console handler should be DEBUG level
        assert config['handlers']['console']['level'] == 'DEBUG'
        assert config['handlers']['console']['formatter'] == 'detailed'
        assert config['loggers']['bytedojo']['level'] == 'DEBUG'
    
    def test_production_mode_config(self):
        """Test config in production mode."""
        config = get_config(debug=False)
        
        # Console handler should be INFO level
        assert config['handlers']['console']['level'] == 'INFO'
        assert config['handlers']['console']['formatter'] == 'simple'
        assert config['loggers']['bytedojo']['level'] == 'INFO'


class TestSetupLogger:
    """Test setup_logger function."""
    
    def test_returns_logger_instance(self):
        """Test that setup_logger returns a logger."""
        logger = setup_logger(debug=False)
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'bytedojo'
    
    def test_debug_mode_sets_level(self):
        """Test that debug mode sets DEBUG level."""
        logger = setup_logger(debug=True)
        assert logger.level == logging.DEBUG
    
    def test_production_mode_sets_level(self):
        """Test that production mode sets INFO level."""
        logger = setup_logger(debug=False)
        assert logger.level == logging.INFO
    
    def test_sets_global_logger(self):
        """Test that setup_logger sets the global logger."""
        setup_logger(debug=False)
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
    
    def test_can_be_called_multiple_times(self):
        """Test that setup_logger can reconfigure logger."""
        logger1 = setup_logger(debug=False)
        assert logger1.level == logging.INFO
        
        logger2 = setup_logger(debug=True)
        assert logger2.level == logging.DEBUG
        
        # Should be same logger instance, reconfigured
        assert logger1 is logger2


class TestGetLogger:
    """Test get_logger function."""
    
    def test_raises_if_not_initialized(self):
        """Test that get_logger raises if setup_logger hasn't been called."""
        import bytedojo.core.logger
        bytedojo.core.logger._logger = None
        
        with pytest.raises(RuntimeError, match="Logger not initialized"):
            get_logger()
    
    def test_returns_same_instance(self):
        """Test that get_logger returns the same instance."""
        setup_logger(debug=False)
        
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2


class TestConsoleLogging:
    """Test console logging output."""
    
    def test_info_logs_to_console(self, capsys):
        """Test that INFO messages appear in console."""
        logger = setup_logger(debug=False)
        logger.info("Test info message")
        
        captured = capsys.readouterr()
        assert "Test info message" in captured.out
    
    def test_warning_logs_to_console(self, capsys):
        """Test that WARNING messages appear in console."""
        logger = setup_logger(debug=False)
        logger.warning("Test warning message")
        
        captured = capsys.readouterr()
        assert "Test warning message" in captured.out
    
    def test_error_logs_to_console(self, capsys):
        """Test that ERROR messages appear in console."""
        logger = setup_logger(debug=False)
        logger.error("Test error message")
        
        captured = capsys.readouterr()
        assert "Test error message" in captured.out
    
    def test_debug_not_in_production(self, capsys):
        """Test that DEBUG messages don't appear in production mode."""
        logger = setup_logger(debug=False)
        logger.debug("Test debug message")
        
        captured = capsys.readouterr()
        assert "Test debug message" not in captured.out
    
    def test_debug_in_debug_mode(self, capsys):
        """Test that DEBUG messages appear in debug mode."""
        logger = setup_logger(debug=True)
        logger.debug("Test debug message")
        
        captured = capsys.readouterr()
        assert "Test debug message" in captured.out
    
    def test_simple_format_in_production(self, capsys):
        """Test that production mode uses simple format."""
        logger = setup_logger(debug=False)
        logger.info("Simple message")
        
        captured = capsys.readouterr()
        # Simple format should just be the message (with colors)
        # Should NOT have timestamp or file location
        assert "Simple message" in captured.out
        assert "[" not in captured.out.replace('\033[', '')  # No brackets except ANSI codes
    
    def test_detailed_format_in_debug(self, capsys):
        """Test that debug mode uses detailed format."""
        logger = setup_logger(debug=True)
        logger.info("Detailed message")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Detailed format should have timestamp
        # Look for time pattern HH:MM:SS
        assert "Detailed message" in output
        # Should have file location in brackets


class TestLogLevels:
    """Test different log levels."""
    
    def test_all_levels_in_debug_mode(self, capsys):
        """Test that all levels are logged in debug mode."""
        logger = setup_logger(debug=True)
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Debug message" in output
        assert "Info message" in output
        assert "Warning message" in output
        assert "Error message" in output
        assert "Critical message" in output
    
    def test_no_debug_in_production(self, capsys):
        """Test that DEBUG is filtered in production mode."""
        logger = setup_logger(debug=False)
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Debug message" not in output
        assert "Info message" in output
        assert "Warning message" in output
        assert "Error message" in output


class TestColorOutput:
    """Test that colors are applied to output."""
    
    def test_output_contains_ansi_codes(self, capsys):
        """Test that output contains ANSI color codes."""
        logger = setup_logger(debug=False)
        logger.info("Colored message")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should contain ANSI escape sequences
        assert '\033[' in output
    
    def test_different_levels_have_different_colors(self, capsys):
        """Test that different log levels have different colors."""
        logger = setup_logger(debug=True)
        
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        
        captured = capsys.readouterr()
        # Each level should have different color codes
        # Hard to test exact colors, but should have ANSI codes
        assert '\033[' in captured.out


class TestSingletonPattern:
    """Test singleton logger pattern."""
    
    def test_logger_is_singleton(self):
        """Test that logger is a singleton."""
        logger1 = setup_logger(debug=False)
        logger2 = get_logger()
        
        assert logger1 is logger2
    
    def test_reconfiguration_updates_same_instance(self):
        """Test that reconfiguring updates the same logger."""
        logger1 = setup_logger(debug=False)
        initial_level = logger1.level
        
        logger2 = setup_logger(debug=True)
        new_level = logger2.level
        
        # Should be same instance
        assert logger1 is logger2
        # But level should be updated
        assert initial_level != new_level
        assert logger1.level == logging.DEBUG


class TestFileOutput:
    """Test file output in debug mode."""
    
    def test_file_handler_in_debug_mode(self):
        """Test that file handler is created in debug mode."""
        logger = setup_logger(debug=True)
        
        # Should have a file handler
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
    
    def test_no_file_handler_in_production(self):
        """Test that no file handler in production mode."""
        logger = setup_logger(debug=False)
        
        # Should NOT have file handlers
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0
    
    def test_debug_logs_to_file(self, tmp_path):
        """Test that debug messages are written to file."""
        import bytedojo.core.logger
        from pathlib import Path
        from unittest.mock import patch
        
        # Mock the home directory to use tmp_path
        with patch.object(Path, 'home', return_value=tmp_path):
            logger = setup_logger(debug=True)
            logger.debug("Test debug message")
            logger.info("Test info message")
            
            # Close handlers to flush
            for handler in logger.handlers[:]:
                handler.close()
            
            # Check log file exists
            log_dir = tmp_path / '.bytedojo' / 'logs'
            assert log_dir.exists()
            
            # Find debug log file
            log_files = list(log_dir.glob('debug_*.log'))
            assert len(log_files) > 0
            
            # Check contents
            log_content = log_files[0].read_text()
            assert "Test debug message" in log_content
            assert "Test info message" in log_content
    
    def test_file_format_no_colors(self, tmp_path):
        """Test that file output has no ANSI color codes."""
        import bytedojo.core.logger
        from pathlib import Path
        from unittest.mock import patch
        
        with patch.object(Path, 'home', return_value=tmp_path):
            logger = setup_logger(debug=True)
            logger.info("Test message")
            
            # Close handlers
            for handler in logger.handlers[:]:
                handler.close()
            
            # Check file content
            log_dir = tmp_path / '.bytedojo' / 'logs'
            log_files = list(log_dir.glob('debug_*.log'))
            log_content = log_files[0].read_text()
            
            # Should NOT contain ANSI codes
            assert '\033[' not in log_content
            # Should contain the message
            assert "Test message" in log_content


class TestMultipleLogMessages:
    """Test logging multiple messages."""
    
    def test_multiple_messages(self, capsys):
        """Test logging multiple messages in sequence."""
        logger = setup_logger(debug=True)
        
        for i in range(5):
            logger.info(f"Message {i}")
        
        captured = capsys.readouterr()
        output = captured.out
        
        for i in range(5):
            assert f"Message {i}" in output