"""
Presentation seam for the CLI (§4.3).

- palette: click-styled text primitives + tiny layout helpers
- renderers: one render function per view; commands hand them a
  view-model (usually a service result struct) and never format
  output themselves

Re-exports the palette so command modules can keep importing helpers
from `bytedojo.commands.ui`.
"""

from bytedojo.commands.ui.palette import (  # noqa: F401
    accent,
    blank,
    bold,
    difficulty_badge,
    difficulty_short,
    dim,
    error,
    footer,
    header,
    hint,
    kv,
    lang_tag,
    problem_id,
    problem_line,
    rule,
    status_badge,
    status_short,
    success,
    warn,
)
