"""
Tests for Context class.
"""

import pytest
from pathlib import Path
from bytedojo.core.context import Context


class TestContextInit:
    """Test Context initialization."""
    
    def test_init_default_values(self):
        """Test that Context initializes with default values."""
        ctx = Context()
        
        assert ctx.debug is False
        assert ctx.config_path is None
        assert ctx.logger is not None
    
    def test_init_with_debug_true(self):
        """Test initialization with debug=True."""
        ctx = Context(debug=True)
        
        assert ctx.debug is True
        assert ctx.config_path is None
    
    def test_init_with_debug_false(self):
        """Test initialization with debug=False."""
        ctx = Context(debug=False)
        
        assert ctx.debug is False
    
    def test_init_with_config_path(self, tmp_path):
        """Test initialization with config_path."""
        config_file = tmp_path / "config.yml"
        ctx = Context(config_path=config_file)
        
        assert ctx.config_path == config_file
        assert ctx.debug is False
    
    def test_init_with_both_parameters(self, tmp_path):
        """Test initialization with both debug and config_path."""
        config_file = tmp_path / "config.yml"
        ctx = Context(debug=True, config_path=config_file)
        
        assert ctx.debug is True
        assert ctx.config_path == config_file


class TestContextLogger:
    """Test Context logger attribute."""
    
    def test_logger_is_set(self):
        """Test that logger is set during initialization."""
        ctx = Context()
        
        assert hasattr(ctx, 'logger')
        assert ctx.logger is not None
    
    def test_logger_is_same_instance(self):
        """Test that all contexts share the same logger."""
        ctx1 = Context()
        ctx2 = Context()
        
        # Both should have the same logger instance (singleton)
        assert ctx1.logger is ctx2.logger


class TestContextAttributes:
    """Test Context attributes."""
    
    def test_has_debug_attribute(self):
        """Test that Context has debug attribute."""
        ctx = Context()
        assert hasattr(ctx, 'debug')
    
    def test_has_config_path_attribute(self):
        """Test that Context has config_path attribute."""
        ctx = Context()
        assert hasattr(ctx, 'config_path')
    
    def test_has_logger_attribute(self):
        """Test that Context has logger attribute."""
        ctx = Context()
        assert hasattr(ctx, 'logger')
    
    def test_debug_is_boolean(self):
        """Test that debug is a boolean."""
        ctx = Context(debug=True)
        assert isinstance(ctx.debug, bool)
    
    def test_config_path_is_path_or_none(self, tmp_path):
        """Test that config_path is Path or None."""
        ctx1 = Context()
        ctx2 = Context(config_path=tmp_path / "config.yml")
        
        assert ctx1.config_path is None
        assert isinstance(ctx2.config_path, Path)


class TestContextMutability:
    """Test Context attribute mutability."""
    
    def test_can_change_debug_after_init(self):
        """Test that debug can be changed after initialization."""
        ctx = Context(debug=False)
        ctx.debug = True
        
        assert ctx.debug is True
    
    def test_can_change_config_path_after_init(self, tmp_path):
        """Test that config_path can be changed after initialization."""
        ctx = Context()
        new_path = tmp_path / "new_config.yml"
        ctx.config_path = new_path
        
        assert ctx.config_path == new_path


class TestContextUsage:
    """Test Context in realistic usage scenarios."""
    
    def test_context_for_production_mode(self):
        """Test context setup for production mode."""
        ctx = Context(debug=False)
        
        assert ctx.debug is False
        assert ctx.logger is not None
    
    def test_context_for_debug_mode(self):
        """Test context setup for debug mode."""
        ctx = Context(debug=True)
        
        assert ctx.debug is True
        assert ctx.logger is not None
    
    def test_context_with_custom_config(self, tmp_path):
        """Test context with custom config file."""
        config_file = tmp_path / "custom_config.yml"
        config_file.write_text("# Custom config")
        
        ctx = Context(config_path=config_file)
        
        assert ctx.config_path.exists()
        assert ctx.config_path == config_file
    
    def test_multiple_contexts_independent(self, tmp_path):
        """Test that multiple contexts are independent."""
        config1 = tmp_path / "config1.yml"
        config2 = tmp_path / "config2.yml"
        
        ctx1 = Context(debug=True, config_path=config1)
        ctx2 = Context(debug=False, config_path=config2)
        
        assert ctx1.debug is True
        assert ctx2.debug is False
        assert ctx1.config_path != ctx2.config_path
        
        # But they share the logger (singleton)
        assert ctx1.logger is ctx2.logger