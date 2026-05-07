"""
Tests for test_fetcher module (loads test case data from JSON files).
"""

import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest
from bytedojo.core.test_fetcher import _load_test_file, fetch_test_cases, is_testable
from bytedojo.core.models import Case


class TestLoadTestFile:
    """Test _load_test_file function."""

    def test_load_test_file_success(self):
        """Test loading a test file that exists."""
        test_data = {"input_output": [{"input": "1", "output": "2"}]}
        json_content = json.dumps(test_data)

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        with patch("bytedojo.core.test_fetcher.get_test_file", return_value=mock_path):
            with patch("builtins.open", mock_open(read_data=json_content)):
                result = _load_test_file(1)

        assert result == test_data

    def test_load_test_file_not_found(self):
        """Test loading a test file that does not exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False

        with patch("bytedojo.core.test_fetcher.get_test_file", return_value=mock_path):
            result = _load_test_file(999)

        assert result is None

    def test_load_test_file_empty_json(self):
        """Test loading a test file with empty JSON object."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        with patch("bytedojo.core.test_fetcher.get_test_file", return_value=mock_path):
            with patch("builtins.open", mock_open(read_data="{}")):
                result = _load_test_file(1)

        assert result == {}

    def test_load_test_file_complex_data(self):
        """Test loading a test file with complex nested data."""
        test_data = {
            "input_output": [
                {"input": "nums = [1,2,3]", "output": "[0,1,2]"},
                {"input": "nums = [4,5,6]", "output": "[3,4,5]"}
            ],
            "metadata": {"difficulty": "easy"}
        }
        json_content = json.dumps(test_data)

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        with patch("bytedojo.core.test_fetcher.get_test_file", return_value=mock_path):
            with patch("builtins.open", mock_open(read_data=json_content)):
                result = _load_test_file(42)

        assert result == test_data
        assert len(result["input_output"]) == 2

    def test_load_test_file_calls_get_test_file_with_problem_id(self):
        """Test that _load_test_file passes correct problem_id to get_test_file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False

        with patch("bytedojo.core.test_fetcher.get_test_file", return_value=mock_path) as mock_get:
            _load_test_file(123)

        mock_get.assert_called_once_with(123)


class TestFetchTestCases:
    """Test fetch_test_cases function."""

    def test_fetch_test_cases_success(self):
        """Test fetching test cases successfully."""
        test_data = {
            "input_output": [
                {"input": "nums = [1,2]", "output": "[0,1]"},
                {"input": "nums = [3,4]", "output": "[1,0]"}
            ]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert len(result) == 2
        assert isinstance(result[0], Case)
        assert result[0].input == "nums = [1,2]"
        assert result[0].output == "[0,1]"
        assert result[1].input == "nums = [3,4]"
        assert result[1].output == "[1,0]"

    def test_fetch_test_cases_empty_list(self):
        """Test fetching test cases when input_output is empty."""
        test_data = {"input_output": []}

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert result == []

    def test_fetch_test_cases_no_file(self):
        """Test fetching test cases when file does not exist."""
        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=None):
            result = fetch_test_cases(999)

        assert result == []

    def test_fetch_test_cases_no_input_output_key(self):
        """Test fetching test cases when input_output key is missing."""
        test_data = {"other_key": "value"}

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert result == []

    def test_fetch_test_cases_missing_input_field(self):
        """Test fetching test cases when input field is missing."""
        test_data = {
            "input_output": [
                {"output": "result"}
            ]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert len(result) == 1
        assert result[0].input == ""
        assert result[0].output == "result"

    def test_fetch_test_cases_missing_output_field(self):
        """Test fetching test cases when output field is missing."""
        test_data = {
            "input_output": [
                {"input": "test input"}
            ]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert len(result) == 1
        assert result[0].input == "test input"
        assert result[0].output == ""

    def test_fetch_test_cases_missing_both_fields(self):
        """Test fetching test cases when both input and output fields are missing."""
        test_data = {
            "input_output": [{}]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert len(result) == 1
        assert result[0].input == ""
        assert result[0].output == ""

    def test_fetch_test_cases_single_case(self):
        """Test fetching a single test case."""
        test_data = {
            "input_output": [
                {"input": "x = 5", "output": "25"}
            ]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(100)

        assert len(result) == 1
        assert result[0].input == "x = 5"
        assert result[0].output == "25"

    def test_fetch_test_cases_multiple_cases(self):
        """Test fetching multiple test cases."""
        test_data = {
            "input_output": [
                {"input": "a", "output": "1"},
                {"input": "b", "output": "2"},
                {"input": "c", "output": "3"},
                {"input": "d", "output": "4"},
                {"input": "e", "output": "5"}
            ]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert len(result) == 5
        for i, case in enumerate(result):
            assert isinstance(case, Case)

    def test_fetch_test_cases_calls_load_test_file(self):
        """Test that fetch_test_cases calls _load_test_file with correct problem_id."""
        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=None) as mock_load:
            fetch_test_cases(456)

        mock_load.assert_called_once_with(456)

    def test_fetch_test_cases_with_multiline_input(self):
        """Test fetching test cases with multiline input."""
        test_data = {
            "input_output": [
                {"input": "line1\nline2\nline3", "output": "result"}
            ]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert len(result) == 1
        assert result[0].input == "line1\nline2\nline3"

    def test_fetch_test_cases_with_special_characters(self):
        """Test fetching test cases with special characters."""
        test_data = {
            "input_output": [
                {"input": "arr = [1,2,3]", "output": "[\"a\", \"b\"]"}
            ]
        }

        with patch("bytedojo.core.test_fetcher._load_test_file", return_value=test_data):
            result = fetch_test_cases(1)

        assert len(result) == 1
        assert result[0].input == "arr = [1,2,3]"
        assert result[0].output == "[\"a\", \"b\"]"


class TestIsTestable:
    """Test is_testable function."""

    def test_is_testable_true(self):
        """Test is_testable returns True when test cases exist."""
        test_cases = [Case(input="1", output="2")]

        with patch("bytedojo.core.test_fetcher.fetch_test_cases", return_value=test_cases):
            result = is_testable(1)

        assert result is True

    def test_is_testable_false_empty(self):
        """Test is_testable returns False when no test cases exist."""
        with patch("bytedojo.core.test_fetcher.fetch_test_cases", return_value=[]):
            result = is_testable(999)

        assert result is False

    def test_is_testable_multiple_cases(self):
        """Test is_testable returns True with multiple test cases."""
        test_cases = [
            Case(input="a", output="1"),
            Case(input="b", output="2"),
            Case(input="c", output="3")
        ]

        with patch("bytedojo.core.test_fetcher.fetch_test_cases", return_value=test_cases):
            result = is_testable(1)

        assert result is True

    def test_is_testable_calls_fetch_test_cases(self):
        """Test that is_testable calls fetch_test_cases with correct problem_id."""
        with patch("bytedojo.core.test_fetcher.fetch_test_cases", return_value=[]) as mock_fetch:
            is_testable(789)

        mock_fetch.assert_called_once_with(789)

    def test_is_testable_single_case(self):
        """Test is_testable with exactly one test case."""
        test_cases = [Case(input="x", output="y")]

        with patch("bytedojo.core.test_fetcher.fetch_test_cases", return_value=test_cases):
            result = is_testable(1)

        assert result is True


class TestIntegration:
    """Integration tests for test_fetcher module."""

    def test_full_flow_with_valid_file(self):
        """Test the full flow from file to test cases."""
        test_data = {
            "input_output": [
                {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"},
                {"input": "nums = [3,2,4], target = 6", "output": "[1,2]"}
            ]
        }
        json_content = json.dumps(test_data)

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        with patch("bytedojo.core.test_fetcher.get_test_file", return_value=mock_path):
            with patch("builtins.open", mock_open(read_data=json_content)):
                cases = fetch_test_cases(1)
                testable = is_testable(1)

        assert len(cases) == 2
        assert testable is True
        assert cases[0].input == "nums = [2,7,11,15], target = 9"
        assert cases[0].output == "[0,1]"

    def test_full_flow_with_missing_file(self):
        """Test the full flow when file does not exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False

        with patch("bytedojo.core.test_fetcher.get_test_file", return_value=mock_path):
            cases = fetch_test_cases(999)
            testable = is_testable(999)

        assert cases == []
        assert testable is False
