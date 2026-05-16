"""
Label / pill renderers — Rich markup helpers for tree node labels.

Three primitives:

- `tag_pill_markup(tag)` — GitHub-style coloured bubble. Each tag name
  hashes to a stable colour from a curated palette so the same tag
  always renders the same colour.

- `difficulty_markup(d)` — single-letter E / M / H in the difficulty
  colour.

- `status_glyph_markup(s)` — ● / ✗ / ▲ / ○ in the status colour.

Plus three higher-level builders that compose the above into the full
labels used in the problem tree (problem row / language row / version
row).
"""

import hashlib

from rich.text import Text

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus
from bytedojo.tui.theme import (
    ERROR_TEXT,
    FAINT_TEXT,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SUCCESS_TEXT,
    WARNING_TEXT,
)


# --------------------------------------------------------------------------- #
# Tag pill — deterministic hash-to-palette                                    #
# --------------------------------------------------------------------------- #

#: Curated palette inspired by GitHub's default label colours.
#: Each entry is (background_hex, foreground_hex). Backgrounds are saturated;
#: foregrounds are picked for legibility on that background.
_TAG_PALETTE: list[tuple[str, str]] = [
    ("#0e8a16", "#ffffff"),  # green
    ("#5319e7", "#ffffff"),  # purple
    ("#1d76db", "#ffffff"),  # blue
    ("#d93f0b", "#ffffff"),  # orange
    ("#fbca04", "#1c1c1c"),  # yellow (dark fg)
    ("#0052cc", "#ffffff"),  # blue darker
    ("#b60205", "#ffffff"),  # red
    ("#5b3a8d", "#ffffff"),  # eggplant
    ("#006b75", "#ffffff"),  # teal
    ("#c5def5", "#1c1c1c"),  # light blue (dark fg)
    ("#bfdadc", "#1c1c1c"),  # pale teal (dark fg)
    ("#c2e0c6", "#1c1c1c"),  # mint
    ("#fef2c0", "#1c1c1c"),  # pale yellow
    ("#f9d0c4", "#1c1c1c"),  # peach
    ("#e99695", "#1c1c1c"),  # salmon
    ("#bb84d5", "#1c1c1c"),  # lavender
]


def _tag_color(name: str) -> tuple[str, str]:
    """Stable (bg, fg) for a tag name via md5 → palette index."""
    digest = hashlib.md5(name.encode("utf-8")).digest()
    idx = digest[0] % len(_TAG_PALETTE)
    return _TAG_PALETTE[idx]


def tag_pill_markup(tag: str) -> str:
    """Rich markup for one colored tag pill: ` array `."""
    bg, fg = _tag_color(tag)
    return f"[{fg} on {bg}] {tag} [/]"


def tags_markup(tags: list[str], limit: int | None = None) -> str:
    """Space-joined run of tag pills.

    If ``limit`` is set and we have more tags than that, the trailing ones
    collapse into a faint `+N` indicator.
    """
    if not tags:
        return ""
    if limit is None or len(tags) <= limit:
        return " ".join(tag_pill_markup(t) for t in tags)
    head = " ".join(tag_pill_markup(t) for t in tags[:limit])
    return f"{head} [{FAINT_TEXT}]+{len(tags) - limit}[/]"


# --------------------------------------------------------------------------- #
# Difficulty + status glyphs                                                  #
# --------------------------------------------------------------------------- #

_DIFFICULTY_LETTER = {
    ProblemDifficulty.EASY:   "E",
    ProblemDifficulty.MEDIUM: "M",
    ProblemDifficulty.HARD:   "H",
}

_DIFFICULTY_COLOR = {
    ProblemDifficulty.EASY:   SUCCESS_TEXT,
    ProblemDifficulty.MEDIUM: WARNING_TEXT,
    ProblemDifficulty.HARD:   ERROR_TEXT,
}


def difficulty_markup(d: ProblemDifficulty) -> str:
    color = _DIFFICULTY_COLOR.get(d, FAINT_TEXT)
    letter = _DIFFICULTY_LETTER.get(d, "?")
    return f"[{color} bold]{letter}[/]"


_STATUS_GLYPH = {
    ProblemStatus.PASSED:   "●",
    ProblemStatus.FAILED:   "✗",
    ProblemStatus.SKIPPED:  "▲",
    ProblemStatus.UNGRADED: "○",
    ProblemStatus.UNKNOWN:  "○",
}

_STATUS_COLOR = {
    ProblemStatus.PASSED:   SUCCESS_TEXT,
    ProblemStatus.FAILED:   ERROR_TEXT,
    ProblemStatus.SKIPPED:  WARNING_TEXT,
    ProblemStatus.UNGRADED: FAINT_TEXT,
    ProblemStatus.UNKNOWN:  FAINT_TEXT,
}


def status_glyph_markup(s: ProblemStatus) -> str:
    color = _STATUS_COLOR.get(s, FAINT_TEXT)
    glyph = _STATUS_GLYPH.get(s, "○")
    return f"[{color}]{glyph}[/]"


# --------------------------------------------------------------------------- #
# Composite labels — split into title (left) and tags (right) so the          #
# ProblemTree widget can compute width-aware padding and flush-right them.    #
# --------------------------------------------------------------------------- #

#: Powerline half-circle glyphs used as pill end-caps. Render in the
#: pill's *background* colour against the terminal background so the
#: arcs visually extend the pill body. Requires a Nerd Font installed.
_PILL_LEFT  = ""   #
_PILL_RIGHT = ""   #


def problem_title_markup(
    *,
    problem_id: int,
    difficulty: ProblemDifficulty,
    title: str,
) -> Text:
    """Left side of the problem row: id + difficulty + title."""
    label = Text()
    label.append(f"#{problem_id:<4}", style=FAINT_TEXT)
    label.append("  ")

    diff_letter = _DIFFICULTY_LETTER.get(difficulty, "?")
    diff_color = _DIFFICULTY_COLOR.get(difficulty, FAINT_TEXT)
    label.append(diff_letter, style=f"{diff_color} bold")
    label.append("  ")

    label.append(title, style=f"{PRIMARY_TEXT} bold")
    return label


def tag_bubbles_markup(tags: list[str], max_tags: int = 5) -> Text:
    """Right side of the problem row: real pill-shaped tags (Nerd Font arcs).

    Each tag renders as:
         tag 
    with the half-circle glyphs in the same colour as the pill background,
    giving a rounded-bubble look. Falls back to a plain coloured block
    visually if the terminal's font lacks the Powerline arcs.
    """
    out = Text()
    if not tags:
        return out

    visible = tags[:max_tags]
    for i, tag in enumerate(visible):
        if i > 0:
            out.append(" ")
        bg, fg = _tag_color(tag)
        # Left arc in pill-bg colour on terminal bg.
        out.append(_PILL_LEFT, style=bg)
        # Pill body: tag text with pill bg.
        out.append(tag, style=f"{fg} on {bg}")
        # Right arc.
        out.append(_PILL_RIGHT, style=bg)

    if len(tags) > max_tags:
        out.append(f"  +{len(tags) - max_tags}", style=FAINT_TEXT)

    return out


# Backwards-compat shim: callers that used the single-string `problem_label`
# still work, but they get a non-right-aligned result. ProblemTree below
# replaces this for the live render.
def problem_label(
    *,
    problem_id: int,
    difficulty: ProblemDifficulty,
    title: str,
    tags: list[str],
) -> Text:
    """Single-line problem label with tags appended inline (no right-align).

    Kept as a fallback for the initial `tree.add(...)` call before render-time
    width is known. The custom `ProblemTree.render_label` rewrites the
    visible label every render so the tags are flush-right in the pane.
    """
    label = problem_title_markup(
        problem_id=problem_id, difficulty=difficulty, title=title,
    )
    if tags:
        label.append("  ")
        label.append_text(tag_bubbles_markup(tags))
    return label


def language_label(
    *,
    language: CodeLanguage,
    status: ProblemStatus,
    versions: int,
) -> str:
    """Level-1 node label: `python   ●  passed   3 attempts`."""
    return (
        f"[{SECONDARY_TEXT}]{language.value:<8}[/]  "
        f"{status_glyph_markup(status)}  "
        f"[{FAINT_TEXT}]{status.value:<10}[/]  "
        f"[{FAINT_TEXT}]{versions} attempts[/]"
    )


def version_label(
    *,
    version: int,
    status: ProblemStatus,
    output: str,
    when: str,
) -> str:
    """Level-2 node label: `v003  ●  Passed: 56/56   2d`."""
    return (
        f"[{FAINT_TEXT}]v{version:03d}[/]  "
        f"{status_glyph_markup(status)}  "
        f"[{FAINT_TEXT}]{output:<18}[/]  "
        f"[{FAINT_TEXT}]{when}[/]"
    )
