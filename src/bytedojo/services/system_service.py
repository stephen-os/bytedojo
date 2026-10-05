"""
System service — collect environment and toolchain status.

Used by `dojo support` (and later the TUI) to answer the "is my system set
up correctly?" question without duplicating detection logic per surface.
"""

import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from bytedojo import __version__ as BYTEDOJO_VERSION
from bytedojo.core.logger import get_logger
from bytedojo.core.repository import Repository
from bytedojo.core.toolchains import ToolchainStatus, all_toolchains


@dataclass
class SystemReport:
    """Snapshot of environment + toolchain status."""
    bytedojo_version: str
    python_version: str
    python_executable: str
    platform_name: str           # human-readable, e.g. "Windows 11"
    platform_id: str             # technical, e.g. "win32"
    repository_path: Optional[Path] = None
    toolchains: List[ToolchainStatus] = field(default_factory=list)

    @property
    def ready_count(self) -> int:
        return sum(1 for s in self.toolchains if s.found and not s.warning)

    @property
    def total_count(self) -> int:
        return len(self.toolchains)

    @property
    def all_ready(self) -> bool:
        return self.total_count > 0 and self.ready_count == self.total_count


class SystemService:
    """Collect environment metadata + run toolchain detection."""

    def __init__(self):
        self.logger = get_logger()

    def check(self) -> SystemReport:
        """Gather a fresh SystemReport. Cheap; safe to call repeatedly."""
        info = sys.version_info
        python_version = f"{info.major}.{info.minor}.{info.micro}"

        # Repository is optional — `dojo support` is useful outside a repo too.
        repo = Repository.find(Path.cwd())
        repo_path = repo.root_dir if repo is not None else None

        toolchains = [tc.detect() for tc in all_toolchains()]

        self.logger.debug(
            f"system_service: probed {len(toolchains)} toolchains, "
            f"{sum(1 for s in toolchains if s.found)} ready"
        )

        return SystemReport(
            bytedojo_version=BYTEDOJO_VERSION,
            python_version=python_version,
            python_executable=sys.executable,
            platform_name=f"{platform.system()} {platform.release()}",
            platform_id=sys.platform,
            repository_path=repo_path,
            toolchains=toolchains,
        )
