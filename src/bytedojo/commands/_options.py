"""
Shared Click option groups (§4.4).

The selector options (--name/--desc/--last/--python) repeat across
run / test / grade / review subcommands. One decorator, one definition;
the matching resolution logic lives in _resolve.resolve_problem.
"""

import click


def selectors(f):
    """Attach the standard problem-selector options to a command."""
    options = [
        click.option(
            "--python",
            "-py",
            "language",
            flag_value="python3",
            help="Prefer the Python attempt (warns on mismatch)",
        ),
        click.option(
            "--last", is_flag=True, help="Use the most recently fetched problem"
        ),
        click.option(
            "--desc", "-d", "desc_search", help="Search by description keywords"
        ),
        click.option("--name", "-n", "name_search", help="Search by problem name"),
    ]
    for option in options:
        f = option(f)
    return f
