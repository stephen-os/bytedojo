"""Tests for the .dojo file templates."""

from bytedojo.core.templates import GITIGNORE, README


def test_gitignore_is_non_empty_string():
    assert isinstance(GITIGNORE, str)
    assert GITIGNORE.strip() != ""


def test_gitignore_covers_common_ignore_patterns():
    """Coverage check: ensure the standard pyc/IDE/OS noise is ignored."""
    assert "__pycache__/" in GITIGNORE
    assert "*.pyc" in GITIGNORE
    assert ".vscode/" in GITIGNORE
    assert ".DS_Store" in GITIGNORE


def test_gitignore_covers_bytedojo_specific_artefacts():
    assert "logs/" in GITIGNORE
    assert "*.log" in GITIGNORE


def test_readme_is_non_empty_string():
    assert isinstance(README, str)
    assert README.strip() != ""


def test_readme_documents_the_dojo_layout():
    """README is what users see — must describe the directory shape."""
    assert "ByteDojo Repository" in README
    assert ".dojo/" in README
    assert "db.sqlite" in README
    assert "settings.json" in README


def test_readme_includes_usage_examples():
    """README should show the basic command surface."""
    assert "dojo fetch" in README
    assert "dojo grade" in README
    assert "dojo review" in README
