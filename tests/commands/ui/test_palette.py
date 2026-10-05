"""Thin formatting tests for the palette (§4.3)."""

import click
import pytest

from bytedojo.commands.ui import palette


@pytest.mark.parametrize(
    "status, expected",
    [
        ("passed", "✓ PASSED"),
        ("failed", "✗ FAILED"),
        ("error", "! ERROR"),
        ("skipped", "~ SKIPPED"),
        ("ungraded", "· UNGRADED"),
        ("anything-else", "· UNGRADED"),
    ],
)
def test_status_badge(status, expected):
    assert click.unstyle(palette.status_badge(status)) == expected


@pytest.mark.parametrize(
    "status, glyph",
    [("passed", "✓"), ("failed", "✗"), ("error", "!"), ("skipped", "~"), ("x", "·")],
)
def test_status_short(status, glyph):
    assert click.unstyle(palette.status_short(status)) == glyph


@pytest.mark.parametrize(
    "difficulty, expected",
    [("easy", "Easy"), ("MEDIUM", "Medium"), ("hard", "Hard"), ("weird", "Weird")],
)
def test_difficulty_badge_normalises_case(difficulty, expected):
    assert click.unstyle(palette.difficulty_badge(difficulty)) == expected


@pytest.mark.parametrize(
    "difficulty, letter",
    [("easy", "E"), ("medium", "M"), ("hard", "H"), ("??", "?")],
)
def test_difficulty_short(difficulty, letter):
    assert click.unstyle(palette.difficulty_short(difficulty)) == letter


def test_problem_id_zero_pads():
    assert click.unstyle(palette.problem_id(7)) == "#0007"


def test_problem_line_includes_all_parts():
    line = click.unstyle(palette.problem_line(1, "Two Sum", "Easy", "python3"))
    assert "#0001" in line
    assert "Two Sum" in line
    assert "Easy" in line
    assert "[python3]" in line


def test_problem_line_language_is_optional():
    line = click.unstyle(palette.problem_line(1, "Two Sum", "Easy"))
    assert "[" not in line


def test_layout_helpers_print(capsys):
    palette.header("Title")
    palette.rule()
    palette.blank()
    palette.kv("key", "value")
    palette.hint("do the thing")
    palette.footer("bye")

    out = click.unstyle(capsys.readouterr().out)
    assert "Title" in out
    assert "─" in out
    assert "key:" in out and "value" in out
    assert "do the thing" in out
    assert "bye" in out
