"""
support - Show environment and toolchain status.
"""

import click

from bytedojo.services import SystemService, SystemReport
from bytedojo.commands.ui import accent, bold, success, warn, error, dim, blank


# Define support command
@click.command()
def support():
    """
    Show environment and toolchain status.

    Reports the ByteDojo version, the Python interpreter dojo is running
    under, the OS, and which language toolchains (Python / Java / C++) are
    detected on this machine. Use it to confirm your environment before
    `dojo run` / `dojo test`, or to gather diagnostic info when reporting
    issues.

    Examples:
      dojo support
    """
    service = SystemService()
    report = service.check()
    _display(report)


# ============================================================================
# DISPLAY
# ============================================================================

def _display(r: SystemReport) -> None:
    """Render a SystemReport to the terminal."""
    blank()
    click.echo(dim("  " + "─" * 70))
    click.echo(f"  {accent('ByteDojo Support')}")
    click.echo(dim("  " + "─" * 70))
    blank()

    _display_environment(r)
    blank()
    _display_toolchains(r)
    blank()
    _display_summary(r)
    blank()


def _display_environment(r: SystemReport) -> None:
    click.echo(f"  {accent('Environment')}")
    click.echo(f"    {dim('ByteDojo')}    {r.bytedojo_version}")
    click.echo(f"    {dim('Python')}      {r.python_version}")
    click.echo(f"                 {dim(r.python_executable)}")
    click.echo(f"    {dim('Platform')}    {r.platform_name}  {dim(r.platform_id)}")
    if r.repository_path:
        click.echo(f"    {dim('Repository')}  {r.repository_path}")
    else:
        click.echo(
            f"    {dim('Repository')}  {dim('not in a .dojo repository')}"
        )


def _display_toolchains(r: SystemReport) -> None:
    click.echo(f"  {accent('Toolchains')}")
    if not r.toolchains:
        click.echo(f"    {dim('(none registered)')}")
        return

    for status in r.toolchains:
        lang = status.language.value
        if status.found:
            marker = success("[OK]") if not status.warning else warn("[WARN]")
            version = status.version or "version unknown"
            click.echo(f"    {marker}  {bold(lang):<14}  {version}")
            for binary, path in status.paths.items():
                click.echo(f"              {dim(f'{binary}: {path}')}")
            if status.warning:
                click.echo(f"              {warn(status.warning)}")
        else:
            marker = error("[NO]")
            missing = ", ".join(status.missing) or "unknown"
            click.echo(f"    {marker}  {bold(lang):<14}  {dim('Missing:')} {missing}")
            if status.install_hint:
                click.echo(f"              {warn(f'Install: {status.install_hint}')}")


def _display_summary(r: SystemReport) -> None:
    click.echo(dim("  " + "─" * 70))
    if not r.toolchains:
        return
    if r.all_ready:
        click.echo(success(f"  All {r.total_count} toolchains ready."))
    else:
        click.echo(
            f"  {warn(str(r.ready_count))} of {r.total_count} toolchains ready."
        )
