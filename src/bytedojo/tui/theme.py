"""
ByteDojo TUI theme — verbatim port of gh-dash's theme system.

The slot structure (PrimaryText / SecondaryText / FaintText / InvertedText
/ Success / Warning / Error / SelectedBackground / PrimaryBorder /
FaintBorder / SecondaryBorder) mirrors `clone/gh-dash/internal/tui/theme/
theme.go`'s `Theme` struct. The CSS class names below correspond 1:1
with the lipgloss style slots in gh-dash's `context/styles.go`
(Tabs.Tab, Tabs.ActiveTab, Table.CellStyle, Sidebar.Root, Footer style,
ViewSwitcher.Active, etc.).

Default values use the gruvbox preset from
`clone/gh-dash/docs/src/assets/theme-gruvbox.yml` so the look matches
the gh-dash screenshot the user showed me.
"""

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.models.problem_difficulty import ProblemDifficulty
from bytedojo.core.models.problem_status import ProblemStatus


# =========================================================================
# Palette — gruvbox (matches gh-dash theme-gruvbox.yml)
# =========================================================================

# Text slots
PRIMARY_TEXT    = "#fe8019"   # orange — titles, brand, active tab fg
SECONDARY_TEXT  = "#d65d0e"   # darker orange — meta line, repo/author
FAINT_TEXT      = "#d5c4a1"   # cream — muted body text, time columns
INVERTED_TEXT   = "#3c3836"   # dark — text rendered onto selected bg

# Status slots
SUCCESS_TEXT    = "#98971a"   # olive green — passed, success states
WARNING_TEXT    = "#fabd2f"   # yellow — due, in-progress, donate
ERROR_TEXT      = "#fb4934"   # bright red — failed, error
ACTOR_TEXT      = "#d5c4a1"   # cream — same as faint, for authors

# Background slots
SELECTED_BG     = "#282828"   # gruvbox dark bg — highlighted row, footer

# Border slots
PRIMARY_BORDER   = "#665c54"   # mid brown-grey — pane left border, search box
SECONDARY_BORDER = "#3c3836"   # darker — tab separators
FAINT_BORDER     = "#1d2021"   # very dark — row dividers

# Status colours specific to gh-dash that we re-use
OPEN_PR_COLOR    = "#42A0FA"   # sky blue — used for "open" / in-progress
CLOSED_PR_COLOR  = "#656C76"   # gray — used for closed / skipped
MERGED_PR_COLOR  = "#A371F7"   # purple — used for completed-review

# Logo colour (carried over from gh-dash)
LOGO_COLOR       = "#00F9FB"


# =========================================================================
# Slot dispatchers — map ByteDojo enum values to CSS class names
# =========================================================================

def status_text_class(status: ProblemStatus) -> str:
    """Foreground class for status glyphs/labels."""
    return {
        ProblemStatus.PASSED:   "text-success",
        ProblemStatus.FAILED:   "text-error",
        ProblemStatus.SKIPPED:  "text-warning",
        ProblemStatus.UNGRADED: "text-faint",
        ProblemStatus.UNKNOWN:  "text-faint",
    }[status]


def difficulty_text_class(difficulty: ProblemDifficulty) -> str:
    """Foreground class for the difficulty letter."""
    return {
        ProblemDifficulty.EASY:   "text-success",
        ProblemDifficulty.MEDIUM: "text-warning",
        ProblemDifficulty.HARD:   "text-error",
    }.get(difficulty, "text-faint")


def language_label(language: CodeLanguage) -> str:
    """Short label used in the row meta line: `python` / `java` / `cpp`."""
    return {
        CodeLanguage.PYTHON: "python",
        CodeLanguage.JAVA:   "java",
        CodeLanguage.CPP:    "cpp",
    }.get(language, "?")


# =========================================================================
# THEME_CSS — gh-dash style slots as Textual CSS classes
# =========================================================================

THEME_CSS = f"""
Screen {{
    background: {SELECTED_BG};
}}

/* ============================================================ */
/* Text slot classes                                              */
/* ============================================================ */

.text-primary   {{ color: {PRIMARY_TEXT}; }}
.text-secondary {{ color: {SECONDARY_TEXT}; }}
.text-faint     {{ color: {FAINT_TEXT}; }}
.text-inverted  {{ color: {INVERTED_TEXT}; }}
.text-success   {{ color: {SUCCESS_TEXT}; }}
.text-warning   {{ color: {WARNING_TEXT}; }}
.text-error     {{ color: {ERROR_TEXT}; }}
.text-actor     {{ color: {ACTOR_TEXT}; }}

.bold  {{ text-style: bold; }}
.faint {{ text-style: dim; }}

/* ============================================================ */
/* Tabs row — gh-dash Tabs.TabsRow + Tab + ActiveTab             */
/* ============================================================ */

.tabs-row {{
    height: 2;
    background: {SELECTED_BG};
    border-bottom: heavy {PRIMARY_BORDER};
}}

.tabs-row .tab {{
    padding: 0 2;
    color: {FAINT_TEXT};
    text-style: dim;
    height: 1;
}}

.tabs-row .tab-active {{
    padding: 0 2;
    background: {SELECTED_BG};
    color: {PRIMARY_TEXT};
    text-style: bold;
    height: 1;
}}

.tabs-row .tab-separator {{
    color: {SECONDARY_BORDER};
    width: 3;
    content-align: center middle;
    height: 1;
}}

.tabs-row .tabs-spacer {{
    width: 1fr;
    height: 1;
}}

.tabs-row .tabs-version {{
    padding: 0 1 0 2;
    color: {SECONDARY_TEXT};
    text-style: bold;
    height: 1;
    content-align: right middle;
}}

/* ============================================================ */
/* Search box — gh-dash Search.Root (rounded border)             */
/* ============================================================ */

.search-box {{
    height: 3;
    border: round {PRIMARY_BORDER};
    padding: 0 1;
    color: {FAINT_TEXT};
}}

.search-box .search-text {{
    color: {FAINT_TEXT};
}}

/* ============================================================ */
/* Section / list area                                            */
/* ============================================================ */

.section {{
    padding: 0 1;
    background: {SELECTED_BG};
}}

.section-empty {{
    color: {FAINT_TEXT};
    text-style: dim;
    padding: 1 0 1 1;
}}

/* Table header row */
.table-header {{
    height: 1;
    background: {SELECTED_BG};
    color: {FAINT_TEXT};
    text-style: dim;
    border-bottom: solid {FAINT_BORDER};
}}

.table-header .header-cell {{
    padding: 0 1;
    color: {FAINT_TEXT};
}}

/* ============================================================ */
/* Problem row — 2-line extended layout                           */
/* gh-dash equivalent: prrow.renderExtendedTitle (lines 188-222)  */
/* ============================================================ */

ProblemRow {{
    height: 2;
    padding: 0;
    background: {SELECTED_BG};
    border-bottom: solid {FAINT_BORDER};
}}

ProblemRow.--highlight {{
    background: {SELECTED_BG};
}}

ProblemRow .row-state {{
    width: 3;
    content-align: center top;
    height: 2;
}}

ProblemRow .row-body {{
    width: 1fr;
    height: 2;
    padding: 0 0 0 1;
}}

ProblemRow .row-meta {{
    height: 1;
    color: {SECONDARY_TEXT};
}}

ProblemRow .row-title {{
    height: 1;
    color: {PRIMARY_TEXT};
    text-style: bold;
}}

ProblemRow .row-side {{
    width: auto;
    padding: 0 1;
    height: 2;
    color: {FAINT_TEXT};
}}

ProblemRow .row-time {{
    width: 6;
    padding: 0 1 0 0;
    content-align: right top;
    color: {FAINT_TEXT};
    height: 2;
}}

/* ============================================================ */
/* Sidebar — gh-dash Sidebar.Root (single left │ border)         */
/* ============================================================ */

Sidebar {{
    width: 50;
    min-width: 36;
    border-left: solid {PRIMARY_BORDER};
    padding: 0 2;
    background: {SELECTED_BG};
}}

Sidebar .sidebar-header {{
    height: 1;
    padding-left: 1;
    background: {SELECTED_BG};
    color: {SECONDARY_TEXT};
}}

Sidebar .sidebar-title {{
    height: 3;
    padding: 1 1 0 1;
    background: {SELECTED_BG};
    color: {PRIMARY_TEXT};
    text-style: bold;
}}

Sidebar .sidebar-byline {{
    height: 1;
    color: {FAINT_TEXT};
}}

Sidebar .sidebar-section-head {{
    color: {WARNING_TEXT};
    text-style: bold;
    padding: 1 0 0 0;
}}

Sidebar .sidebar-body {{
    color: {FAINT_TEXT};
}}

/* ============================================================ */
/* Footer — gh-dash Common.FooterStyle + ViewSwitcher             */
/* ============================================================ */

Footer {{
    dock: bottom;
    height: 1;
    background: {SELECTED_BG};
}}

Footer .view-switcher {{
    width: auto;
    height: 1;
    background: {SECONDARY_BORDER};
    color: {INVERTED_TEXT};
}}

Footer .view-active {{
    padding: 0 1;
    background: {SECONDARY_BORDER};
    color: {PRIMARY_TEXT};
    text-style: bold;
}}

Footer .view-inactive {{
    padding: 0 1;
    background: {SECONDARY_BORDER};
    color: {FAINT_TEXT};
}}

Footer .view-separator {{
    color: {PRIMARY_BORDER};
    width: 3;
    content-align: center middle;
}}

Footer .footer-left {{
    padding: 0 1;
    color: {FAINT_TEXT};
}}

Footer .footer-spacer {{
    width: 1fr;
}}

Footer .footer-right {{
    padding: 0 1;
    color: {FAINT_TEXT};
}}

Footer .donate-pill {{
    background: {SELECTED_BG};
    color: {WARNING_TEXT};
    padding: 0 1;
    text-style: underline;
}}

Footer .help-pill {{
    background: {FAINT_TEXT};
    color: {INVERTED_TEXT};
    padding: 0 1;
}}
"""
