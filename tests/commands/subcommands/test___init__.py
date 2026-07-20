"""Tests for the subcommands package registry."""

import click

from bytedojo.commands import subcommands


_EXPECTED = {
    "init", "stats", "grade", "fetch", "query", "pick",
    "run", "review", "settings", "test", "support",
}


def test_all_lists_every_subcommand():
    """__all__ must enumerate every subcommand the dojo group registers."""
    assert set(subcommands.__all__) == _EXPECTED


def test_every_exported_name_is_a_click_command():
    """Each name in __all__ resolves to a Click command or group."""
    for name in subcommands.__all__:
        obj = getattr(subcommands, name)
        assert isinstance(obj, click.Command), f"{name} is not a Click command"
