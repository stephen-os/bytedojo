"""
Container management - Podman-based container runtime.

This module manages the Podman container lifecycle:
- Installing/detecting Podman
- Managing Podman machine (Windows/Mac)
- Running containers on demand
"""

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


class PodmanNotFoundError(Exception):
    """Raised when Podman is not installed."""
    pass


class PodmanMachineError(Exception):
    """Raised when Podman machine operations fail."""
    pass


class ContainerError(Exception):
    """Raised when container operations fail."""
    pass


@dataclass
class ExecutionResult:
    """Result of running code in a container."""
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False


class PodmanManager:
    """Manages Podman container lifecycle."""

    MACHINE_NAME = "podman-machine-default"

    def __init__(self):
        self._podman_path: Optional[str] = None
        self._use_wsl: bool = False
        self._ready: bool = False

    def _find_podman(self) -> str:
        """Find the Podman executable."""
        if self._podman_path:
            return self._podman_path

        podman = shutil.which("podman")
        if podman:
            self._podman_path = podman
            return podman

        if sys.platform == "win32":
            common_paths = [
                Path(os.environ.get("ProgramFiles", "")) / "RedHat" / "Podman" / "podman.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Podman" / "podman.exe",
            ]
            for path in common_paths:
                if path.exists():
                    self._podman_path = str(path)
                    return self._podman_path

        raise PodmanNotFoundError(
            "Podman not found. Please install Podman:\n"
            "  Windows: winget install RedHat.Podman\n"
            "  Mac: brew install podman\n"
            "  Linux: See https://podman.io/docs/installation"
        )

    def _run_podman(
        self,
        args: List[str],
        check: bool = True,
        timeout: Optional[int] = None,
        input_data: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """Run a Podman command."""
        if sys.platform == "win32" and self._use_wsl:
            cmd = ["wsl", "-d", self.MACHINE_NAME, "--", "podman"] + args
        else:
            podman = self._find_podman()
            cmd = [podman] + args

        try:
            return subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                check=check,
                timeout=timeout
            )
        except subprocess.CalledProcessError as e:
            raise ContainerError(f"Podman command failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise ContainerError(f"Podman command timed out")

    def _normalize_wsl_output(self, text: str) -> str:
        """Normalize WSL output by removing null characters."""
        return text.replace('\x00', '').replace('\r', '')

    def _is_wsl_machine_exists(self) -> bool:
        """Check if the Podman WSL machine exists."""
        try:
            result = subprocess.run(
                ["wsl", "--list", "--quiet"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = self._normalize_wsl_output(result.stdout)
            return self.MACHINE_NAME in output
        except Exception:
            return False

    def _is_wsl_machine_running(self) -> bool:
        """Check if the Podman WSL machine is running."""
        try:
            result = subprocess.run(
                ["wsl", "--list", "--verbose"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = self._normalize_wsl_output(result.stdout)
            for line in output.split('\n'):
                if self.MACHINE_NAME in line and 'Running' in line:
                    return True
        except Exception:
            pass
        return False

    def _start_wsl_machine(self) -> bool:
        """Start the WSL machine."""
        try:
            subprocess.run(
                ["wsl", "-d", self.MACHINE_NAME, "--", "echo", "started"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return True
        except Exception:
            return False

    def _init_machine(self, progress_callback=None) -> None:
        """Initialize Podman machine (Windows/Mac only)."""
        if progress_callback:
            progress_callback("Initializing Podman machine (this may take a few minutes)...")

        try:
            self._run_podman([
                "machine", "init",
                "--cpus", "2",
                "--memory", "2048",
                "--disk-size", "20"
            ], timeout=300)
        except ContainerError as e:
            raise PodmanMachineError(f"Failed to initialize Podman machine: {e}")

    def ensure_ready(self, progress_callback=None) -> None:
        """Ensure Podman is ready to run containers."""
        if self._ready:
            return

        # Check Podman installed
        self._find_podman()

        # Start machine if needed (Windows/Mac)
        if sys.platform == "linux":
            self._ready = True
            return

        # Windows: use WSL mode
        if sys.platform == "win32":
            if not self._is_wsl_machine_exists():
                self._init_machine(progress_callback)

            if progress_callback:
                progress_callback("Starting Podman machine...")

            if self._start_wsl_machine():
                self._use_wsl = True
                for _ in range(30):
                    if self._is_wsl_machine_running():
                        if progress_callback:
                            progress_callback("Podman machine ready.")
                        self._ready = True
                        return
                    time.sleep(1)
            raise PodmanMachineError("Podman machine failed to start")

        # Mac: use podman machine commands
        try:
            result = self._run_podman(["machine", "list", "--format", "json"], check=False)
            if result.returncode == 0 and result.stdout.strip():
                machines = json.loads(result.stdout)
                if not machines:
                    self._init_machine(progress_callback)
                elif not any(m.get("Running") for m in machines):
                    if progress_callback:
                        progress_callback("Starting Podman machine...")
                    self._run_podman(["machine", "start"], timeout=120)
        except Exception as e:
            raise PodmanMachineError(f"Failed to start Podman machine: {e}")

        self._ready = True

    def is_image_available(self, image: str) -> bool:
        """Check if an image is available locally."""
        try:
            result = self._run_podman(["image", "exists", image], check=False)
            return result.returncode == 0
        except Exception:
            return False

    def pull_image(self, image: str, progress_callback=None) -> None:
        """Pull a container image."""
        if progress_callback:
            progress_callback(f"Pulling {image}...")

        try:
            self._run_podman(["pull", image], timeout=600)
        except ContainerError as e:
            raise ContainerError(f"Failed to pull image {image}: {e}")

    def run_code(
        self,
        image: str,
        command: List[str],
        code: str,
        timeout: int = 30,
        memory_limit: str = "256m"
    ) -> ExecutionResult:
        """
        Run code in a container and return the result.

        Args:
            image: Container image (e.g., "python:3.11-slim")
            command: Command to run (e.g., ["python"])
            code: Code to execute (passed via stdin to interpreter)
            timeout: Execution timeout in seconds
            memory_limit: Memory limit (e.g., "256m")

        Returns:
            ExecutionResult with stdout, stderr, exit code
        """
        self.ensure_ready()

        # Pull image if not available
        if not self.is_image_available(image):
            self.pull_image(image)

        # Run: echo "code" | podman run --rm -i python:3.11-slim python
        args = [
            "run",
            "--rm",
            "--network=none",
            f"--memory={memory_limit}",
            "-i",
            image,
        ] + command

        try:
            result = self._run_podman(
                args,
                check=False,
                input_data=code,
                timeout=timeout + 5  # Add buffer for container overhead
            )
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                timed_out=False
            )
        except ContainerError as e:
            if "timed out" in str(e).lower():
                return ExecutionResult(
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    exit_code=124,
                    timed_out=True
                )
            raise


