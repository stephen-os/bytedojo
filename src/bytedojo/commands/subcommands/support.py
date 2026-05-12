"""
support - Show environment and toolchain status.
"""

import click

from bytedojo.services import SystemService, SystemReport


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
    click.echo("")
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo(click.style("  BYTEDOJO SUPPORT", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='bright_black'))
    click.echo("")

    _display_environment(r)
    click.echo("")
    _display_toolchains(r)
    click.echo("")
    _display_summary(r)
    click.echo("")


def _display_environment(r: SystemReport) -> None:
    click.echo(click.style("  Environment:", fg='cyan'))
    click.echo(f"    ByteDojo:    {r.bytedojo_version}")
    click.echo(f"    Python:      {r.python_version}")
    click.echo(f"                 {click.style(r.python_executable, fg='bright_black')}")
    click.echo(f"    Platform:    {r.platform_name}  ({r.platform_id})")
    if r.repository_path:
        click.echo(f"    Repository:  {r.repository_path}")
    else:
        click.echo(
            f"    Repository:  "
            f"{click.style('not in a .dojo repository', fg='bright_black')}"
        )


def _display_toolchains(r: SystemReport) -> None:
    click.echo(click.style("  Toolchains:", fg='cyan'))
    if not r.toolchains:
        click.echo("    (none registered)")
        return

    for status in r.toolchains:
        lang = status.language.value
        if status.found:
            marker = click.style("[OK]", fg='green')
            version = status.version or "version unknown"
            # Stable column for the language name regardless of marker color codes
            click.echo(f"    {marker}  {lang:10}  {version}")
            for binary, path in status.paths.items():
                click.echo(
                    f"              "
                    f"{click.style(f'{binary}: {path}', fg='bright_black')}"
                )
        else:
            marker = click.style("[NO]", fg='red')
            missing = ", ".join(status.missing) or "unknown"
            click.echo(f"    {marker}  {lang:10}  Missing: {missing}")
            if status.install_hint:
                click.echo(
                    f"              "
                    f"{click.style(f'Install: {status.install_hint}', fg='yellow')}"
                )


def _display_summary(r: SystemReport) -> None:
    click.echo(click.style("-" * 70, fg='bright_black'))
    if not r.toolchains:
        return
    if r.all_ready:
        click.echo(click.style(
            f"  All {r.total_count} toolchains ready.", fg='green'
        ))
    else:
        click.echo(
            f"  {r.ready_count} of {r.total_count} toolchains ready."
        )
