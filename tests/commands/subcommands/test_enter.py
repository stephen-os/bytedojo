"""Tests for `dojo enter` (TUI launcher)."""

import sys
import types

from click.testing import CliRunner

from bytedojo.commands.subcommands.enter import enter


def test_enter_constructs_and_runs_the_tui(monkeypatch):
    """`dojo enter` instantiates DojoApp and calls run()."""
    calls = {"init": 0, "run": 0}

    class FakeDojoApp:
        def __init__(self):
            calls["init"] += 1

        def run(self):
            calls["run"] += 1

    # The import happens inside the command body — replace the symbol on
    # the bytedojo.tui module so the lazy `from bytedojo.tui import DojoApp`
    # finds our fake.
    fake_tui = types.ModuleType("bytedojo.tui")
    fake_tui.DojoApp = FakeDojoApp
    monkeypatch.setitem(sys.modules, "bytedojo.tui", fake_tui)

    result = CliRunner().invoke(enter, [])

    assert result.exit_code == 0, result.output
    assert calls["init"] == 1
    assert calls["run"] == 1
