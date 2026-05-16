"""Small helpers used across the TUI layer."""

from datetime import datetime
from typing import Optional


def time_ago(dt: Optional[datetime]) -> str:
    """Render a datetime as a compact relative-time string.

    Examples: ``"3s"`` / ``"7m"`` / ``"2h"`` / ``"5d"`` / ``"2w"`` /
    ``"6mo"``. Returns ``"—"`` for ``None`` and ``"now"`` for future
    timestamps (clock skew).
    """
    if dt is None:
        return "—"
    delta = datetime.now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "now"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    if seconds < 604800:
        return f"{seconds // 86400}d"
    if seconds < 2592000:
        return f"{seconds // 604800}w"
    return f"{seconds // 2592000}mo"
