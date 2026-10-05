"""
support - Show environment and toolchain status.
"""

import click

from bytedojo.commands.ui.renderers import render_support
from bytedojo.services import SystemService


@click.command()
def support():
    """
    Show environment and toolchain status.

    Reports the ByteDojo version, the Python interpreter dojo is running
    under (warning if it's below 3.10), the OS, and which language
    toolchains are detected on this machine. Diagnostic only — it never
    fails.

    Examples:
      dojo support
    """
    report = SystemService().check()
    render_support(report)
