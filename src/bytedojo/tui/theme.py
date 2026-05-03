"""
ByteDojo TUI Theme - Fire & Ice color palette.
"""

# Brand Colors (Fire & Ice)
COLORS = {
    # Primary palette from logo
    "purple": "#6a2a8a",        # Back mountain - primary accent
    "red": "#c43a3a",           # Middle mountain - danger/fail
    "coral": "#f06060",         # Front mountain - warning/hover
    "background": "#0d1117",    # Dark blue-black background

    # Extended palette
    "ice_blue": "#58a6ff",      # Success/passed states
    "ice_light": "#79c0ff",     # Links, highlights
    "muted": "#8b949e",         # Secondary text, borders
    "surface": "#161b22",       # Elevated surfaces
    "surface_light": "#21262d", # Cards, panels
    "text": "#e6edf3",          # Primary text
    "text_muted": "#8b949e",    # Secondary text

    # Semantic colors
    "success": "#58a6ff",       # Passed, success
    "warning": "#f06060",       # Warnings, due today
    "error": "#c43a3a",         # Failed, errors, overdue
    "info": "#6a2a8a",          # Info, primary actions
}

# Difficulty colors
DIFFICULTY_COLORS = {
    "Easy": "#58a6ff",      # Ice blue
    "Medium": "#f06060",    # Coral
    "Hard": "#c43a3a",      # Red
}

# Status colors
STATUS_COLORS = {
    "passed": "#58a6ff",    # Ice blue
    "failed": "#c43a3a",    # Red
    "skipped": "#f06060",   # Coral
    "ungraded": "#8b949e",  # Muted
}

# CSS Theme for Textual
THEME_CSS = """
$background: #0d1117;
$surface: #161b22;
$surface-light: #21262d;
$primary: #6a2a8a;
$secondary: #58a6ff;
$accent: #6a2a8a;
$warning: #f06060;
$error: #c43a3a;
$success: #58a6ff;
$text: #e6edf3;
$text-muted: #8b949e;

Screen {
    background: $background;
}

/* Global text styles */
.title {
    text-style: bold;
    color: $primary;
}

.subtitle {
    color: $text-muted;
}

.muted {
    color: $text-muted;
}

/* Status indicators */
.success {
    color: $success;
}

.warning {
    color: $warning;
}

.error {
    color: $error;
}

/* Difficulty badges */
.easy {
    color: #58a6ff;
}

.medium {
    color: #f06060;
}

.hard {
    color: #c43a3a;
}
"""
