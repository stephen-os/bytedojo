"""
ui.py - Shared terminal output utilities for the ByteDojo CLI.

Uses Click's built-in named colors so Click handles all terminal
compatibility. Callers use the helpers below.
"""

import click
from typing import Optional

# ─── Primitives ───────────────────────────────────────────────────────────────

def accent(text) -> str:
    return click.style(str(text), fg='bright_white', bold=True)

def bold(text) -> str:
    return click.style(str(text), bold=True)

def success(text) -> str:
    return click.style(str(text), fg='bright_green')

def warn(text) -> str:
    return click.style(str(text), fg='yellow')

def error(text) -> str:
    return click.style(str(text), fg='bright_red')

def dim(text) -> str:
    return click.style(str(text), fg='bright_black')

# ─── Domain ───────────────────────────────────────────────────────────────────

def problem_id(n: int) -> str:
    return accent(f"#{n:04d}")

def difficulty_badge(d: str) -> str:
    d = d.strip().lower()
    if d == "easy":   return success("Easy")
    if d == "medium": return warn("Medium")
    if d == "hard":   return error("Hard")
    return dim(d.title())

def difficulty_short(d: str) -> str:
    d = d.strip().lower()
    if d == "easy":   return success("E")
    if d == "medium": return warn("M")
    if d == "hard":   return error("H")
    return dim("?")

def status_badge(status: str) -> str:
    s = status.strip().lower()
    if s == "passed":   return success("✓ PASSED")
    if s == "failed":   return error("✗ FAILED")
    if s == "skipped":  return warn("~ SKIPPED")
    return dim("· UNGRADED")

def status_short(status: str) -> str:
    s = status.strip().lower()
    if s == "passed":   return success("✓")
    if s == "failed":   return error("✗")
    if s == "skipped":  return warn("~")
    return dim("·")

def lang_tag(lang: str) -> str:
    return dim(f"[{lang}]")

def problem_line(n: int, title: str, diff: str, lang: Optional[str] = None) -> str:
    parts = [problem_id(n), bold(title), difficulty_badge(diff)]
    if lang:
        parts.append(lang_tag(lang))
    return "  ".join(parts)

# ─── Layout ───────────────────────────────────────────────────────────────────

def header(text: str) -> None:
    click.echo()
    click.echo(f"  {accent(text)}")

def rule() -> None:
    click.echo(dim("  " + "─" * 58))

def blank() -> None:
    click.echo()

def footer(text: str) -> None:
    click.echo(dim(f"\n  {text}"))

def kv(key: str, value: str) -> None:
    click.echo(f"  {dim(key + ':')}  {bold(value)}")

def hint(text: str) -> None:
    click.echo(f"  {dim(text)}")
