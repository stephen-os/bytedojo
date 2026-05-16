"""Shared CSS + helpers for modal screens.

Every modal uses the same centred bordered card with a title bar at
the top and an optional footer hint at the bottom. Pull this CSS into
each modal's ``DEFAULT_CSS`` so the look stays consistent without
each file repeating the same selectors.
"""

from bytedojo.tui.theme import (
    FAINT_TEXT,
    PRIMARY_BORDER,
    PRIMARY_TEXT,
    SELECTED_BG,
)


#: Shared base CSS for every modal — overlay alignment + card framing.
#: Modals append their own selectors after this block.
BASE_MODAL_CSS = f"""
ModalScreen {{
    align: center middle;
}}

.modal-card {{
    width: 70;
    height: auto;
    padding: 1 2;
    background: {SELECTED_BG};
    border: round {PRIMARY_BORDER};
}}

.modal-title {{
    text-style: bold;
    color: {PRIMARY_TEXT};
    padding-bottom: 1;
}}

.modal-section {{
    color: {FAINT_TEXT};
    padding-bottom: 0;
}}

.modal-row {{
    padding: 0;
}}

.modal-footer {{
    padding-top: 1;
    color: {FAINT_TEXT};
}}

.modal-error {{
    color: red;
    text-style: bold;
}}

.modal-success {{
    color: green;
    text-style: bold;
}}
"""
