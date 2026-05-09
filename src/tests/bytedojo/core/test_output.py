"""
Tests for output module (echo, success, warn, error, info, header).
"""

from unittest.mock import patch, call

import pytest
from bytedojo.core.output import echo, success, warn, error, info, header


class TestEcho:
    """Test echo function."""

    @patch("bytedojo.core.output.click.echo")
    def test_echo_simple_message(self, mock_echo):
        """Test echo with a simple message."""
        echo("Hello, World!")

        mock_echo.assert_called_once_with("Hello, World!")

    @patch("bytedojo.core.output.click.echo")
    def test_echo_empty_message(self, mock_echo):
        """Test echo with an empty message."""
        echo("")

        mock_echo.assert_called_once_with("")

    @patch("bytedojo.core.output.click.echo")
    def test_echo_multiline_message(self, mock_echo):
        """Test echo with a multiline message."""
        message = "Line 1\nLine 2\nLine 3"
        echo(message)

        mock_echo.assert_called_once_with(message)

    @patch("bytedojo.core.output.click.echo")
    def test_echo_special_characters(self, mock_echo):
        """Test echo with special characters."""
        message = "Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"
        echo(message)

        mock_echo.assert_called_once_with(message)

    @patch("bytedojo.core.output.click.echo")
    def test_echo_unicode_characters(self, mock_echo):
        """Test echo with unicode characters."""
        message = "Unicode: \u2713 \u2717 \u2192 \u00e9"
        echo(message)

        mock_echo.assert_called_once_with(message)


class TestSuccess:
    """Test success function."""

    @patch("bytedojo.core.output.click.secho")
    def test_success_simple_message(self, mock_secho):
        """Test success with a simple message."""
        success("Operation completed!")

        mock_secho.assert_called_once_with("Operation completed!", fg="green")

    @patch("bytedojo.core.output.click.secho")
    def test_success_empty_message(self, mock_secho):
        """Test success with an empty message."""
        success("")

        mock_secho.assert_called_once_with("", fg="green")

    @patch("bytedojo.core.output.click.secho")
    def test_success_multiline_message(self, mock_secho):
        """Test success with a multiline message."""
        message = "Task 1: Done\nTask 2: Done"
        success(message)

        mock_secho.assert_called_once_with(message, fg="green")

    @patch("bytedojo.core.output.click.secho")
    def test_success_uses_green_color(self, mock_secho):
        """Test that success uses green color."""
        success("Test")

        call_args = mock_secho.call_args
        assert call_args[1]["fg"] == "green"


class TestWarn:
    """Test warn function."""

    @patch("bytedojo.core.output.click.secho")
    def test_warn_simple_message(self, mock_secho):
        """Test warn with a simple message."""
        warn("Something might be wrong")

        mock_secho.assert_called_once_with("Warning: Something might be wrong", fg="yellow")

    @patch("bytedojo.core.output.click.secho")
    def test_warn_empty_message(self, mock_secho):
        """Test warn with an empty message."""
        warn("")

        mock_secho.assert_called_once_with("Warning: ", fg="yellow")

    @patch("bytedojo.core.output.click.secho")
    def test_warn_prepends_warning_prefix(self, mock_secho):
        """Test that warn prepends 'Warning: ' prefix."""
        warn("test message")

        call_args = mock_secho.call_args
        assert call_args[0][0].startswith("Warning: ")

    @patch("bytedojo.core.output.click.secho")
    def test_warn_uses_yellow_color(self, mock_secho):
        """Test that warn uses yellow color."""
        warn("Test")

        call_args = mock_secho.call_args
        assert call_args[1]["fg"] == "yellow"

    @patch("bytedojo.core.output.click.secho")
    def test_warn_multiline_message(self, mock_secho):
        """Test warn with a multiline message."""
        message = "Line 1\nLine 2"
        warn(message)

        mock_secho.assert_called_once_with(f"Warning: {message}", fg="yellow")


class TestError:
    """Test error function."""

    @patch("bytedojo.core.output.click.secho")
    def test_error_simple_message(self, mock_secho):
        """Test error with a simple message."""
        error("Something went wrong")

        mock_secho.assert_called_once_with("Error: Something went wrong", fg="red", bold=True)

    @patch("bytedojo.core.output.click.secho")
    def test_error_empty_message(self, mock_secho):
        """Test error with an empty message."""
        error("")

        mock_secho.assert_called_once_with("Error: ", fg="red", bold=True)

    @patch("bytedojo.core.output.click.secho")
    def test_error_prepends_error_prefix(self, mock_secho):
        """Test that error prepends 'Error: ' prefix."""
        error("test message")

        call_args = mock_secho.call_args
        assert call_args[0][0].startswith("Error: ")

    @patch("bytedojo.core.output.click.secho")
    def test_error_uses_red_color(self, mock_secho):
        """Test that error uses red color."""
        error("Test")

        call_args = mock_secho.call_args
        assert call_args[1]["fg"] == "red"

    @patch("bytedojo.core.output.click.secho")
    def test_error_uses_bold(self, mock_secho):
        """Test that error uses bold text."""
        error("Test")

        call_args = mock_secho.call_args
        assert call_args[1]["bold"] is True

    @patch("bytedojo.core.output.click.secho")
    def test_error_multiline_message(self, mock_secho):
        """Test error with a multiline message."""
        message = "Error line 1\nError line 2"
        error(message)

        mock_secho.assert_called_once_with(f"Error: {message}", fg="red", bold=True)


class TestInfo:
    """Test info function."""

    @patch("bytedojo.core.output.click.secho")
    def test_info_simple_message(self, mock_secho):
        """Test info with a simple message."""
        info("Here is some information")

        mock_secho.assert_called_once_with("Here is some information", fg="cyan")

    @patch("bytedojo.core.output.click.secho")
    def test_info_empty_message(self, mock_secho):
        """Test info with an empty message."""
        info("")

        mock_secho.assert_called_once_with("", fg="cyan")

    @patch("bytedojo.core.output.click.secho")
    def test_info_uses_cyan_color(self, mock_secho):
        """Test that info uses cyan color."""
        info("Test")

        call_args = mock_secho.call_args
        assert call_args[1]["fg"] == "cyan"

    @patch("bytedojo.core.output.click.secho")
    def test_info_multiline_message(self, mock_secho):
        """Test info with a multiline message."""
        message = "Info line 1\nInfo line 2"
        info(message)

        mock_secho.assert_called_once_with(message, fg="cyan")

    @patch("bytedojo.core.output.click.secho")
    def test_info_no_prefix(self, mock_secho):
        """Test that info does not add a prefix."""
        message = "Plain message"
        info(message)

        call_args = mock_secho.call_args
        assert call_args[0][0] == message


class TestHeader:
    """Test header function."""

    @patch("bytedojo.core.output.click.secho")
    def test_header_simple_message(self, mock_secho):
        """Test header with a simple message."""
        header("Section Title")

        mock_secho.assert_called_once_with("Section Title", fg="bright_white", bold=True)

    @patch("bytedojo.core.output.click.secho")
    def test_header_empty_message(self, mock_secho):
        """Test header with an empty message."""
        header("")

        mock_secho.assert_called_once_with("", fg="bright_white", bold=True)

    @patch("bytedojo.core.output.click.secho")
    def test_header_uses_bright_white_color(self, mock_secho):
        """Test that header uses bright_white color."""
        header("Test")

        call_args = mock_secho.call_args
        assert call_args[1]["fg"] == "bright_white"

    @patch("bytedojo.core.output.click.secho")
    def test_header_uses_bold(self, mock_secho):
        """Test that header uses bold text."""
        header("Test")

        call_args = mock_secho.call_args
        assert call_args[1]["bold"] is True

    @patch("bytedojo.core.output.click.secho")
    def test_header_multiline_message(self, mock_secho):
        """Test header with a multiline message."""
        message = "Header\nSubheader"
        header(message)

        mock_secho.assert_called_once_with(message, fg="bright_white", bold=True)

    @patch("bytedojo.core.output.click.secho")
    def test_header_no_prefix(self, mock_secho):
        """Test that header does not add a prefix."""
        message = "Plain header"
        header(message)

        call_args = mock_secho.call_args
        assert call_args[0][0] == message


class TestOutputFunctionSequence:
    """Test multiple output functions called in sequence."""

    @patch("bytedojo.core.output.click.secho")
    @patch("bytedojo.core.output.click.echo")
    def test_multiple_output_functions(self, mock_echo, mock_secho):
        """Test calling multiple output functions in sequence."""
        echo("Starting process...")
        header("Main Section")
        info("Processing data")
        success("Step 1 complete")
        warn("Low memory")
        error("Failed to save")

        # Verify echo was called
        mock_echo.assert_called_once_with("Starting process...")

        # Verify secho calls
        assert mock_secho.call_count == 5

    @patch("bytedojo.core.output.click.secho")
    def test_different_colors_used(self, mock_secho):
        """Test that different functions use different colors."""
        success("green message")
        warn("yellow message")
        error("red message")
        info("cyan message")
        header("white message")

        calls = mock_secho.call_args_list
        colors = [c[1]["fg"] for c in calls]

        assert "green" in colors
        assert "yellow" in colors
        assert "red" in colors
        assert "cyan" in colors
        assert "bright_white" in colors


class TestOutputFunctionEdgeCases:
    """Test edge cases for output functions."""

    @patch("bytedojo.core.output.click.echo")
    def test_echo_with_whitespace_only(self, mock_echo):
        """Test echo with whitespace-only message."""
        echo("   ")
        mock_echo.assert_called_once_with("   ")

    @patch("bytedojo.core.output.click.secho")
    def test_success_with_newlines(self, mock_secho):
        """Test success with leading/trailing newlines."""
        success("\n\nMessage\n\n")
        mock_secho.assert_called_once_with("\n\nMessage\n\n", fg="green")

    @patch("bytedojo.core.output.click.secho")
    def test_warn_with_tabs(self, mock_secho):
        """Test warn with tab characters."""
        warn("\tIndented warning")
        mock_secho.assert_called_once_with("Warning: \tIndented warning", fg="yellow")

    @patch("bytedojo.core.output.click.secho")
    def test_error_with_long_message(self, mock_secho):
        """Test error with a very long message."""
        long_message = "x" * 1000
        error(long_message)
        mock_secho.assert_called_once_with(f"Error: {long_message}", fg="red", bold=True)

    @patch("bytedojo.core.output.click.secho")
    def test_info_with_numeric_string(self, mock_secho):
        """Test info with numeric string."""
        info("12345")
        mock_secho.assert_called_once_with("12345", fg="cyan")

    @patch("bytedojo.core.output.click.secho")
    def test_header_with_special_chars(self, mock_secho):
        """Test header with special characters."""
        header("=== HEADER ===")
        mock_secho.assert_called_once_with("=== HEADER ===", fg="bright_white", bold=True)
