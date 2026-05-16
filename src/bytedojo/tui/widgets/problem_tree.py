"""
ProblemTree — custom Textual Tree that right-aligns tag bubbles.

The base Textual ``Tree`` widget takes a single Rich ``Text`` label per
node and renders it left-to-right. To get the gh-dash layout where
tags flush to the right edge of the pane regardless of title length,
we have to override ``render_label`` and recompute the visible label
at render time using the live widget width.

We store each problem's title (left side) and tags (right side)
separately on ``node.data`` so the render can assemble them with the
correct padding. Other node kinds (language / version) render whatever
label was set at construction time, unchanged.
"""

from typing import Any

from rich.style import Style
from rich.text import Text
from textual.widgets import Tree
from textual.widgets._tree import TreeNode

from bytedojo.tui.widgets.labels import (
    problem_title_markup,
    tag_bubbles_markup,
)


class ProblemTree(Tree[Any]):
    """Tree that right-aligns tag bubbles for problem (top-level) nodes.

    Expects ``node.data`` for problem nodes to be a dict with:
        - ``kind`` = ``"problem"``
        - ``problem_id``, ``difficulty``, ``title``, ``tags`` (the raw
          fields used to rebuild the label)
        - ``ref`` = the original ``Problem`` object (for callers)

    Other node kinds are rendered untouched.

    Problem rows also get a subtle ``underline`` applied to their full
    rendered width — Textual's Tree renders 1 row per node so we can't
    insert blank spacer rows without breaking cursor navigation. The
    underline gives the visual "row separator" effect instead.
    """

    #: Rich Style applied to the entire problem-row label to draw a
    #: subtle horizontal under-line beneath the row content. ``underline=True``
    #: is additive — Rich preserves existing fg/bg colours per character
    #: and just turns on the underline flag, so the title still reads
    #: orange, tags still read bubble-coloured, etc.
    _ROW_UNDERLINE = Style(underline=True)

    DEFAULT_CSS = """
    ProblemTree {
        padding: 0 1;
    }
    """

    @staticmethod
    def _node_depth(node: TreeNode[Any]) -> int:
        """Number of parent hops to the root (root itself is depth 0)."""
        depth = 0
        cur = node
        while cur.parent is not None:
            depth += 1
            cur = cur.parent
        return depth

    def render_label(
        self, node: TreeNode[Any], base_style: Style, style: Style
    ) -> Text:
        # Default behaviour for non-problem nodes (language / version).
        data = node.data
        if not isinstance(data, dict) or data.get("kind") != "problem":
            label = (
                node.label.copy() if isinstance(node.label, Text)
                else Text.from_markup(str(node.label))
            )
            label.stylize(style)
            return label

        # Rebuild the problem label so tags can be right-aligned.
        title = problem_title_markup(
            problem_id=data["problem_id"],
            difficulty=data["difficulty"],
            title=data["title"],
        )
        tags = tag_bubbles_markup(data["tags"])

        # Widget width is 0 during pre-mount width measurement passes —
        # fall back to a simple inline join in that case. The real render
        # pass runs again with size.width populated.
        tree_width = self.size.width
        if tree_width <= 0:
            label = Text()
            label.append_text(title)
            if tags.cell_len:
                label.append("  ")
                label.append_text(tags)
            label.stylize(self._ROW_UNDERLINE)
            label.stylize(style)
            return label

        # Estimate the indent cells consumed before the label: chevron +
        # depth-1 levels of guide. Tree depth-1 is the first child level
        # (where problem nodes live since show_root is False). Subtract
        # an extra 2 cells for the widget's horizontal padding so the
        # tag pills sit flush to the visible right edge of the pane.
        depth = self._node_depth(node)
        indent_cells = 2 + max(0, depth - 1) * 2
        usable = max(20, tree_width - indent_cells - 4)

        pad = usable - title.cell_len - tags.cell_len
        if pad < 2:
            pad = 2

        label = Text()
        label.append_text(title)
        label.append(" " * pad)
        label.append_text(tags)
        # Underline the whole row to give a subtle separator.
        label.stylize(self._ROW_UNDERLINE)
        # Highlight/cursor style still wins because Textual layers it on top.
        label.stylize(style)
        return label
