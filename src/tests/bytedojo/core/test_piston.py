"""
Tests for the piston module (PistonExecutor).
"""

import pytest
import json
import urllib.error
from unittest.mock import MagicMock, patch, Mock

from bytedojo.core.piston import (
    PistonExecutor,
    PistonError,
    ExecutionRequest,
    ExecutionResult,
    PISTON_PORT,
    CONTAINER_NAME,
    get_executor,
)
from bytedojo.core.container import PodmanManager, ContainerError


class TestExecutionRequest:
    """Tests for ExecutionRequest dataclass."""

    def test_execution_request_defaults(self):
        """Test ExecutionRequest default values."""
        request = ExecutionRequest(
            language="python",
            code="print('hello')"
        )
        assert request.stdin == ""
        assert request.timeout == 30
        assert request.version == "*"

    def test_execution_request_with_all_params(self):
        """Test ExecutionRequest with all parameters."""
        request = ExecutionRequest(
            language="python",
            code="print('hello')",
            stdin='{"test": 1}',
            timeout=60,
            version="3.11"
        )
        assert request.language == "python"
        assert request.code == "print('hello')"
        assert request.stdin == '{"test": 1}'
        assert request.timeout == 60
        assert request.version == "3.11"


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_defaults(self):
        """Test ExecutionResult default values."""
        result = ExecutionResult(
            stdout="output",
            stderr="",
            exit_code=0,
            timed_out=False
        )
        assert result.compile_output == ""
        assert result.compile_error is False

    def test_execution_result_with_compile_error(self):
        """Test ExecutionResult with compile error."""
        result = ExecutionResult(
            stdout="",
            stderr="SyntaxError",
            exit_code=1,
            timed_out=False,
            compile_output="Line 1: Error",
            compile_error=True
        )
        assert result.compile_error is True
        assert result.compile_output == "Line 1: Error"


class TestPistonExecutor:
    """Tests for PistonExecutor class."""

    def test_init_with_default_manager(self):
        """Test PistonExecutor uses default manager."""
        with patch("bytedojo.core.piston.get_podman_manager") as mock_get:
            mock_get.return_value = MagicMock()
            executor = PistonExecutor()
            assert executor.manager is not None

    def test_init_with_custom_manager(self):
        """Test PistonExecutor with custom manager."""
        mock_manager = MagicMock()
        executor = PistonExecutor(podman_manager=mock_manager)
        assert executor.manager is mock_manager

    @patch.object(PistonExecutor, "_is_piston_running")
    def test_ensure_piston_running_already_running(self, mock_is_running):
        """Test _ensure_piston_running when Piston is already running."""
        mock_is_running.return_value = True
        mock_manager = MagicMock()

        executor = PistonExecutor(podman_manager=mock_manager)
        endpoint = executor._ensure_piston_running()

        assert endpoint == f"http://localhost:{PISTON_PORT}"
        mock_manager.ensure_ready.assert_called_once()

    @patch.object(PistonExecutor, "_wait_for_api")
    @patch.object(PistonExecutor, "_is_piston_running")
    def test_ensure_piston_running_starts_container(self, mock_is_running, mock_wait):
        """Test _ensure_piston_running starts container when not running."""
        mock_is_running.return_value = False
        mock_manager = MagicMock()

        executor = PistonExecutor(podman_manager=mock_manager)
        endpoint = executor._ensure_piston_running()

        assert endpoint == f"http://localhost:{PISTON_PORT}"
        mock_manager._run_podman.assert_called()
        mock_wait.assert_called_once()

    def test_is_piston_running_true(self):
        """Test _is_piston_running when container is running."""
        mock_manager = MagicMock()
        mock_manager._run_podman.return_value = MagicMock(
            stdout="abc123"  # Container ID present means running
        )

        executor = PistonExecutor(podman_manager=mock_manager)
        assert executor._is_piston_running() is True

    def test_is_piston_running_false(self):
        """Test _is_piston_running when container is not running."""
        mock_manager = MagicMock()
        mock_manager._run_podman.return_value = MagicMock(
            stdout=""  # Empty means not running
        )

        executor = PistonExecutor(podman_manager=mock_manager)
        assert executor._is_piston_running() is False

    def test_is_piston_running_exception(self):
        """Test _is_piston_running returns False on exception."""
        mock_manager = MagicMock()
        mock_manager._run_podman.side_effect = Exception("Failed")

        executor = PistonExecutor(podman_manager=mock_manager)
        assert executor._is_piston_running() is False

    def test_get_filename_python(self):
        """Test _get_filename for Python."""
        executor = PistonExecutor(podman_manager=MagicMock())
        assert executor._get_filename("python") == "main.py"
        assert executor._get_filename("python3") == "main.py"

    def test_get_filename_java(self):
        """Test _get_filename for Java."""
        executor = PistonExecutor(podman_manager=MagicMock())
        assert executor._get_filename("java") == "Main.java"

    def test_get_filename_cpp(self):
        """Test _get_filename for C++."""
        executor = PistonExecutor(podman_manager=MagicMock())
        assert executor._get_filename("cpp") == "main.cpp"

    def test_get_filename_unknown(self):
        """Test _get_filename for unknown language."""
        executor = PistonExecutor(podman_manager=MagicMock())
        assert executor._get_filename("unknown_lang") == "main.txt"

    def test_parse_result_success(self):
        """Test _parse_result for successful execution."""
        executor = PistonExecutor(podman_manager=MagicMock())

        piston_response = {
            "run": {
                "stdout": "Hello World",
                "stderr": "",
                "code": 0
            }
        }

        result = executor._parse_result(piston_response)

        assert result.stdout == "Hello World"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.timed_out is False
        assert result.compile_error is False

    def test_parse_result_runtime_error(self):
        """Test _parse_result for runtime error."""
        executor = PistonExecutor(podman_manager=MagicMock())

        piston_response = {
            "run": {
                "stdout": "",
                "stderr": "NameError: name 'x' is not defined",
                "code": 1
            }
        }

        result = executor._parse_result(piston_response)

        assert result.exit_code == 1
        assert "NameError" in result.stderr

    def test_parse_result_compile_error(self):
        """Test _parse_result for compile error."""
        executor = PistonExecutor(podman_manager=MagicMock())

        piston_response = {
            "compile": {
                "output": "Error: invalid syntax",
                "code": 1
            },
            "run": {
                "stdout": "",
                "stderr": "",
                "code": 0
            }
        }

        result = executor._parse_result(piston_response)

        assert result.compile_error is True
        assert "invalid syntax" in result.compile_output
        assert result.exit_code == 1

    def test_parse_result_timeout(self):
        """Test _parse_result for timed out execution."""
        executor = PistonExecutor(podman_manager=MagicMock())

        piston_response = {
            "run": {
                "stdout": "",
                "stderr": "Execution timed out",
                "code": 137,
                "signal": "SIGKILL"
            }
        }

        result = executor._parse_result(piston_response)

        assert result.timed_out is True

    @patch("urllib.request.urlopen")
    @patch.object(PistonExecutor, "_ensure_piston_running")
    def test_execute_success(self, mock_ensure, mock_urlopen):
        """Test execute with successful response."""
        mock_ensure.return_value = "http://localhost:2000"

        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "run": {
                "stdout": "42",
                "stderr": "",
                "code": 0
            }
        }).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        executor = PistonExecutor(podman_manager=MagicMock())
        result = executor.execute(ExecutionRequest(
            language="python",
            code="print(42)"
        ))

        assert result.stdout == "42"
        assert result.exit_code == 0

    @patch("urllib.request.urlopen")
    @patch.object(PistonExecutor, "_ensure_piston_running")
    def test_execute_http_error(self, mock_ensure, mock_urlopen):
        """Test execute raises PistonError on HTTP error."""
        mock_ensure.return_value = "http://localhost:2000"

        mock_error = urllib.error.HTTPError(
            "http://localhost:2000",
            500,
            "Internal Server Error",
            {},
            None
        )
        mock_urlopen.side_effect = mock_error

        executor = PistonExecutor(podman_manager=MagicMock())

        with pytest.raises(PistonError) as exc_info:
            executor.execute(ExecutionRequest(language="python", code="print(1)"))

        assert "Piston API error" in str(exc_info.value)

    @patch.object(PistonExecutor, "_ensure_piston_running")
    def test_execute_connection_error(self, mock_ensure):
        """Test execute raises PistonError on connection failure."""
        mock_ensure.return_value = "http://localhost:2000"

        executor = PistonExecutor(podman_manager=MagicMock())

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with pytest.raises(PistonError) as exc_info:
                executor.execute(ExecutionRequest(language="python", code="print(1)"))

            assert "Failed to connect" in str(exc_info.value)

    def test_stop(self):
        """Test stop method calls correct podman commands."""
        mock_manager = MagicMock()
        executor = PistonExecutor(podman_manager=mock_manager)

        executor.stop()

        # Should have called stop and rm
        calls = mock_manager._run_podman.call_args_list
        assert any("stop" in str(call) for call in calls)
        assert any("rm" in str(call) for call in calls)

    def test_cleanup(self):
        """Test cleanup method."""
        mock_manager = MagicMock()
        executor = PistonExecutor(podman_manager=mock_manager)

        executor.cleanup()

        mock_manager.cleanup.assert_called_once()


class TestGetExecutor:
    """Tests for get_executor singleton."""

    def test_get_executor_returns_instance(self):
        """Test get_executor returns a PistonExecutor instance."""
        import bytedojo.core.piston as piston_module
        piston_module._executor = None

        with patch("bytedojo.core.piston.get_podman_manager"):
            executor = get_executor()
            assert isinstance(executor, PistonExecutor)

    def test_get_executor_singleton(self):
        """Test get_executor returns same instance."""
        import bytedojo.core.piston as piston_module
        piston_module._executor = None

        with patch("bytedojo.core.piston.get_podman_manager"):
            executor1 = get_executor()
            executor2 = get_executor()
            assert executor1 is executor2
