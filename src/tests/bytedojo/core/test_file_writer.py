"""
Tests for FileWriter class.
"""

import pytest
from pathlib import Path
from bytedojo.core.file_writer import FileWriter


class TestFileWriterInit:
    """Test FileWriter initialization."""
    
    def test_init_creates_instance(self):
        """Test that FileWriter can be instantiated."""
        writer = FileWriter()
        assert writer is not None
    
    def test_init_has_logger(self):
        """Test that FileWriter has a logger."""
        writer = FileWriter()
        assert hasattr(writer, 'logger')
        assert writer.logger is not None


class TestFileWriterWrite:
    """Test FileWriter.write method."""
    
    def test_write_creates_file(self, tmp_path):
        """Test that write creates a file."""
        writer = FileWriter()
        filepath = tmp_path / "test.txt"
        content = "Hello, World!"
        
        result = writer.write(content, filepath)
        
        assert filepath.exists()
        assert result == filepath
    
    def test_write_creates_parent_directories(self, tmp_path):
        """Test that write creates parent directories if they don't exist."""
        writer = FileWriter()
        filepath = tmp_path / "subdir1" / "subdir2" / "test.txt"
        content = "Test content"
        
        result = writer.write(content, filepath)
        
        assert filepath.exists()
        assert filepath.parent.exists()
        assert result == filepath
    
    def test_write_with_nested_directories(self, tmp_path):
        """Test writing to deeply nested directories."""
        writer = FileWriter()
        filepath = tmp_path / "a" / "b" / "c" / "d" / "test.txt"
        content = "Nested content"
        
        result = writer.write(content, filepath)
        
        assert filepath.exists()
        assert result == filepath
    
    def test_write_content_is_correct(self, tmp_path):
        """Test that written content matches input."""
        writer = FileWriter()
        filepath = tmp_path / "test.txt"
        content = "Test content with special chars: !@#$%^&*()"
        
        writer.write(content, filepath)
        
        written_content = filepath.read_text(encoding='utf-8')
        assert written_content == content
    
    def test_write_overwrites_existing_file(self, tmp_path):
        """Test that write overwrites existing files."""
        writer = FileWriter()
        filepath = tmp_path / "test.txt"
        
        # Write initial content
        filepath.write_text("Original content")
        
        # Overwrite with new content
        new_content = "New content"
        writer.write(new_content, filepath)
        
        # Check new content
        written_content = filepath.read_text(encoding='utf-8')
        assert written_content == new_content
    
    def test_write_returns_filepath(self, tmp_path):
        """Test that write returns the filepath."""
        writer = FileWriter()
        filepath = tmp_path / "test.txt"
        content = "Content"
        
        result = writer.write(content, filepath)
        
        assert isinstance(result, Path)
        assert result == filepath


class TestFileWriterEncoding:
    """Test FileWriter encoding handling."""
    
    def test_write_utf8_content(self, tmp_path):
        """Test writing UTF-8 content."""
        writer = FileWriter()
        filepath = tmp_path / "utf8.txt"
        content = "Unicode: émojis 🎯 中文"
        
        writer.write(content, filepath)
        
        written_content = filepath.read_text(encoding='utf-8')
        assert written_content == content
    
    def test_write_multiline_content(self, tmp_path):
        """Test writing multiline content."""
        writer = FileWriter()
        filepath = tmp_path / "multiline.txt"
        content = "Line 1\nLine 2\nLine 3"
        
        writer.write(content, filepath)
        
        written_content = filepath.read_text(encoding='utf-8')
        assert written_content == content
    
    def test_write_empty_string(self, tmp_path):
        """Test writing empty string."""
        writer = FileWriter()
        filepath = tmp_path / "empty.txt"
        content = ""
        
        writer.write(content, filepath)
        
        assert filepath.exists()
        assert filepath.read_text(encoding='utf-8') == ""


class TestFileWriterDifferentFileTypes:
    """Test writing different file types."""
    
    def test_write_python_file(self, tmp_path):
        """Test writing a Python file."""
        writer = FileWriter()
        filepath = tmp_path / "test.py"
        content = "def hello():\n    print('Hello')"
        
        writer.write(content, filepath)
        
        assert filepath.exists()
        assert filepath.suffix == ".py"
    
    def test_write_markdown_file(self, tmp_path):
        """Test writing a Markdown file."""
        writer = FileWriter()
        filepath = tmp_path / "README.md"
        content = "# Title\n\nContent"
        
        writer.write(content, filepath)
        
        assert filepath.exists()
        assert filepath.suffix == ".md"
    
    def test_write_json_file(self, tmp_path):
        """Test writing a JSON file."""
        writer = FileWriter()
        filepath = tmp_path / "data.json"
        content = '{"key": "value"}'
        
        writer.write(content, filepath)
        
        assert filepath.exists()
        assert filepath.suffix == ".json"


class TestFileWriterEdgeCases:
    """Test edge cases."""
    
    def test_write_with_existing_parent_directory(self, tmp_path):
        """Test that existing parent directories don't cause errors."""
        writer = FileWriter()
        
        # Create parent directory first
        parent = tmp_path / "existing"
        parent.mkdir()
        
        filepath = parent / "test.txt"
        content = "Content"
        
        # Should not raise error
        writer.write(content, filepath)
        
        assert filepath.exists()
    
    def test_write_multiple_files_same_writer(self, tmp_path):
        """Test writing multiple files with the same writer instance."""
        writer = FileWriter()
        
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"
        
        writer.write("Content 1", file1)
        writer.write("Content 2", file2)
        writer.write("Content 3", file3)
        
        assert file1.exists()
        assert file2.exists()
        assert file3.exists()
    
    def test_write_long_content(self, tmp_path):
        """Test writing long content."""
        writer = FileWriter()
        filepath = tmp_path / "long.txt"
        content = "A" * 10000  # 10k characters
        
        writer.write(content, filepath)
        
        written_content = filepath.read_text(encoding='utf-8')
        assert len(written_content) == 10000
    
    def test_write_with_special_chars_in_filename(self, tmp_path):
        """Test writing file with special characters in name."""
        writer = FileWriter()
        filepath = tmp_path / "file-with_special.chars.txt"
        content = "Content"
        
        writer.write(content, filepath)
        
        assert filepath.exists()


class TestFileWriterLogging:
    """Test logging behavior."""
    
    def test_write_logs_debug_message(self, tmp_path, capsys):
        """Test that write logs a debug message."""
        from bytedojo.core.logger import setup_logger
        
        # Setup logger in debug mode
        setup_logger(debug=True)
        
        writer = FileWriter()
        filepath = tmp_path / "test.txt"
        content = "Content"
        
        writer.write(content, filepath)
        
        # Check stdout for debug message
        captured = capsys.readouterr()
        assert "Wrote file" in captured.out
        assert str(filepath) in captured.out


class TestFileWriterIntegration:
    """Integration tests for FileWriter."""
    
    def test_write_leetcode_problem_structure(self, tmp_path):
        """Test writing files in LeetCode problem structure."""
        writer = FileWriter()
        
        # Simulate writing problems to organized directories
        easy_problem = tmp_path / "problems" / "easy" / "0001-two-sum.py"
        medium_problem = tmp_path / "problems" / "medium" / "0002-add-two-numbers.py"
        hard_problem = tmp_path / "problems" / "hard" / "0004-median-sorted-arrays.py"
        
        writer.write("# Easy problem", easy_problem)
        writer.write("# Medium problem", medium_problem)
        writer.write("# Hard problem", hard_problem)
        
        assert easy_problem.exists()
        assert medium_problem.exists()
        assert hard_problem.exists()
        
        # Check directory structure
        assert (tmp_path / "problems" / "easy").exists()
        assert (tmp_path / "problems" / "medium").exists()
        assert (tmp_path / "problems" / "hard").exists()
    
    def test_write_and_read_roundtrip(self, tmp_path):
        """Test writing and reading back content."""
        writer = FileWriter()
        filepath = tmp_path / "roundtrip.txt"
        original_content = "Original content with\nmultiple lines\nand special chars: éà"
        
        # Write
        writer.write(original_content, filepath)
        
        # Read back
        read_content = filepath.read_text(encoding='utf-8')
        
        # Should match exactly
        assert read_content == original_content