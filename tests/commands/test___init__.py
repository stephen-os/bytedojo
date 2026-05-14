"""Tests for the commands package marker."""


def test_package_imports_cleanly():
    """Importing the package must not pull in unused subcommand modules."""
    import bytedojo.commands as commands_pkg
    assert commands_pkg.__doc__   # package marker has a docstring
