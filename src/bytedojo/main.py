"""
ByteDojo - Main entry point.
"""

import logging
import os
import sys
import traceback

import click

from bytedojo.commands.bytedojo import bytedojo
from bytedojo.core.errors import DojoError


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
    """Entry point for the ByteDojo CLI.

    DojoError is the one approved way to fail (§10): the message is
    rendered without a stack trace (unless --debug) and the process
    exits with the error's code. Click keeps its own code 2 for usage
    errors; SIGINT keeps 130.
    """
    _force_utf8_output()
    try:
        bytedojo()
    except DojoError as e:
        click.echo(click.style(f"  Error: {e.message}", fg="bright_red"), err=True)
        if logging.getLogger("bytedojo").isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
