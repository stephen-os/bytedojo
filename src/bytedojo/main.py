"""
ByteDojo - Main entry point.
"""
import os
import sys

import bytedojo

from bytedojo.commands.bytedojo import bytedojo


def _force_utf8_output():
    """
    Make stdout/stderr UTF-8 before any command renders.

    The CLI prints box rules and status glyphs (─ ✓ ✗ →). When output is
    redirected or piped, Python falls back to the locale encoding — cp1252
    on a default Windows install — and encoding those glyphs raises
    UnicodeEncodeError partway through a command. An explicit
    PYTHONIOENCODING is left alone.
    """
    if os.environ.get("PYTHONIOENCODING"):
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main():
    """Entry point for the ByteDojo CLI."""
    _force_utf8_output()
    bytedojo()

if __name__ == '__main__':
    main()
