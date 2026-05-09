"""
Tests for the container module (PodmanManager).
"""

import pytest
import subprocess
from unittest.mock import MagicMock, patch, PropertyMock
import sys

from bytedojo.core.container import (
    PodmanManager,
    PodmanNotFoundError,
    PodmanMachineError,
    ContainerError,
    ContainerStatus,
    PISTON_IMAGE,
    get_podman_manager,
)


class TestPodmanManager:
    """Tests for PodmanManager class."""

    def test_init(self):
        """Test PodmanManager initialization."""
        manager = PodmanManager()
        assert manager._podman_path is None

    @patch("shutil.which")
    def test_find_podman_in_path(self, mock_which):
        """Test finding Podman in PATH."""
        mock_which.return_value = "/usr/bin/podman"
        manager = PodmanManager()
        assert manager._find_podman() == "/usr/bin/podman"

    @patch("shutil.which")
    def test_find_podman_not_found(self, mock_which):
        """Test PodmanNotFoundError when Podman is not installed."""
        mock_which.return_value = None
        manager = PodmanManager()

        with pytest.raises(PodmanNotFoundError) as exc_info:
            manager._find_podman()

        assert "Podman not found" in str(exc_info.value)
        assert "winget install" in str(exc_info.value) or "brew install" in str(exc_info.value)

    @patch("shutil.which")
    def test_is_podman_installed_true(self, mock_which):
        """Test is_podman_installed returns True when installed."""
        mock_which.return_value = "/usr/bin/podman"
        manager = PodmanManager()
        assert manager.is_podman_installed() is True

    @patch("shutil.which")
    def test_is_podman_installed_false(self, mock_which):
        """Test is_podman_installed returns False when not installed."""
        mock_which.return_value = None
        manager = PodmanManager()
        assert manager.is_podman_installed() is False

    @patch.object(PodmanManager, "_run_podman")
    @patch.object(PodmanManager, "_find_podman")
    def test_get_podman_version(self, mock_find, mock_run):
        """Test getting Podman version."""
        mock_find.return_value = "/usr/bin/podman"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="podman version 4.5.0"
        )

        manager = PodmanManager()
        version = manager.get_podman_version()

        assert version == "4.5.0"
        mock_run.assert_called_once_with(["--version"], check=False)

    @patch.object(PodmanManager, "_run_podman")
    @patch.object(PodmanManager, "_find_podman")
    def test_is_machine_running_true(self, mock_find, mock_run):
        """Test is_machine_running when machine is running."""
        mock_find.return_value = "/usr/bin/podman"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"Name": "default", "Running": true}]'
        )

        manager = PodmanManager()

        with patch.object(sys, "platform", "win32"):
            assert manager.is_machine_running() is True

    @patch.object(PodmanManager, "_run_podman")
    @patch.object(PodmanManager, "_find_podman")
    def test_is_machine_running_false(self, mock_find, mock_run):
        """Test is_machine_running when machine is stopped."""
        mock_find.return_value = "/usr/bin/podman"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"Name": "default", "Running": false}]'
        )

        manager = PodmanManager()

        with patch.object(sys, "platform", "win32"):
            assert manager.is_machine_running() is False

    @patch.object(sys, "platform", "linux")
    def test_is_machine_running_linux(self):
        """Test is_machine_running returns True on Linux (no machine needed)."""
        manager = PodmanManager()
        assert manager.is_machine_running() is True

    @patch.object(PodmanManager, "_run_podman")
    @patch.object(PodmanManager, "_find_podman")
    def test_is_image_pulled_true(self, mock_find, mock_run):
        """Test is_image_pulled when image exists."""
        mock_find.return_value = "/usr/bin/podman"
        mock_run.return_value = MagicMock(returncode=0)

        manager = PodmanManager()
        assert manager.is_image_pulled(PISTON_IMAGE) is True
        mock_run.assert_called_with(["image", "exists", PISTON_IMAGE], check=False)

    @patch.object(PodmanManager, "_run_podman")
    @patch.object(PodmanManager, "_find_podman")
    def test_is_image_pulled_false(self, mock_find, mock_run):
        """Test is_image_pulled when image doesn't exist."""
        mock_find.return_value = "/usr/bin/podman"
        mock_run.return_value = MagicMock(returncode=1)

        manager = PodmanManager()
        assert manager.is_image_pulled(PISTON_IMAGE) is False

    @patch.object(PodmanManager, "_run_podman")
    @patch.object(PodmanManager, "_find_podman")
    def test_pull_image_success(self, mock_find, mock_run):
        """Test pulling an image successfully."""
        mock_find.return_value = "/usr/bin/podman"
        mock_run.return_value = MagicMock(returncode=0)

        callback = MagicMock()
        manager = PodmanManager()
        manager.pull_image(PISTON_IMAGE, progress_callback=callback)

        mock_run.assert_called_with(["pull", PISTON_IMAGE], timeout=600)
        callback.assert_called()

    @patch.object(PodmanManager, "_run_podman")
    @patch.object(PodmanManager, "_find_podman")
    def test_pull_image_failure(self, mock_find, mock_run):
        """Test pull_image raises ContainerError on failure."""
        mock_find.return_value = "/usr/bin/podman"
        mock_run.side_effect = ContainerError("Failed to pull")

        manager = PodmanManager()
        with pytest.raises(ContainerError):
            manager.pull_image(PISTON_IMAGE)

    @patch.object(PodmanManager, "is_podman_installed")
    @patch.object(PodmanManager, "is_image_pulled")
    @patch.object(PodmanManager, "start_machine")
    @patch.object(sys, "platform", "win32")
    def test_ensure_ready_success(self, mock_start, mock_pulled, mock_installed):
        """Test ensure_ready when everything is set up."""
        mock_installed.return_value = True
        mock_pulled.return_value = True

        manager = PodmanManager()
        manager.ensure_ready()  # Should not raise

        mock_start.assert_called_once()

    @patch.object(PodmanManager, "is_podman_installed")
    def test_ensure_ready_podman_not_installed(self, mock_installed):
        """Test ensure_ready raises when Podman not installed."""
        mock_installed.return_value = False

        manager = PodmanManager()
        with pytest.raises(PodmanNotFoundError):
            manager.ensure_ready()

    @patch.object(PodmanManager, "is_podman_installed")
    @patch.object(PodmanManager, "is_machine_running")
    @patch.object(PodmanManager, "is_image_pulled")
    def test_get_status(self, mock_pulled, mock_running, mock_installed):
        """Test get_status returns correct ContainerStatus."""
        mock_installed.return_value = True
        mock_running.return_value = True
        mock_pulled.return_value = True

        manager = PodmanManager()

        with patch.object(manager, "is_machine_exists", return_value=True):
            status = manager.get_status()

        assert status.podman_installed is True
        assert status.machine_running is True
        assert status.piston_image_pulled is True
        assert status.error is None


class TestContainerStatus:
    """Tests for ContainerStatus dataclass."""

    def test_container_status_defaults(self):
        """Test ContainerStatus default values."""
        status = ContainerStatus(
            podman_installed=False,
            machine_exists=False,
            machine_running=False,
            piston_image_pulled=False
        )
        assert status.error is None

    def test_container_status_with_error(self):
        """Test ContainerStatus with error message."""
        status = ContainerStatus(
            podman_installed=False,
            machine_exists=False,
            machine_running=False,
            piston_image_pulled=False,
            error="Podman not found"
        )
        assert status.error == "Podman not found"


class TestGetPodmanManager:
    """Tests for get_podman_manager singleton."""

    def test_get_podman_manager_returns_instance(self):
        """Test get_podman_manager returns a PodmanManager instance."""
        # Reset the singleton for testing
        import bytedojo.core.container as container_module
        container_module._manager = None

        manager = get_podman_manager()
        assert isinstance(manager, PodmanManager)

    def test_get_podman_manager_singleton(self):
        """Test get_podman_manager returns same instance."""
        import bytedojo.core.container as container_module
        container_module._manager = None

        manager1 = get_podman_manager()
        manager2 = get_podman_manager()
        assert manager1 is manager2
