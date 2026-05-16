"""HelpModal — keybind overlay scoped to the screen that pushed it."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpModal(ModalScreen):
    """A centred bordered card showing the current screen's keybinds.

    Walks the BINDINGS of the source screen so per-mode keybinds appear
    without each screen having to redeclare them somewhere.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("question_mark", "app.pop_screen", "Close"),
        Binding("q", "app.pop_screen", "Close"),
    ]

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }

    HelpModal #help-card {
        width: 70;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: round $accent;
    }

    HelpModal .help-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    HelpModal .help-row {
        padding: 0 0;
    }

    HelpModal .help-footer {
        padding-top: 1;
        color: $text-muted;
    }
    """

    def __init__(self, source_screen) -> None:
        super().__init__()
        self._source_screen = source_screen

    def compose(self) -> ComposeResult:
        title = self._source_screen.__class__.__name__.replace("Screen", "")
        rows = [Static(f"{title} · keybinds", classes="help-title")]
        seen: set[str] = set()
        for binding in self._collect_bindings():
            if binding.key in seen:
                continue
            seen.add(binding.key)
            key_label = _format_key(binding.key)
            description = binding.description or binding.action
            rows.append(Static(f"  {key_label:<12}  {description}", classes="help-row"))
        rows.append(Static("esc / ? / q  close this overlay", classes="help-footer"))
        yield Vertical(*rows, id="help-card")

    def _collect_bindings(self) -> list[Binding]:
        """Pull BINDINGS from the source screen + the App itself."""
        out: list[Binding] = []
        # Source screen first so its keys shadow App keys with the same letter.
        for entry in getattr(self._source_screen, "BINDINGS", []):
            out.append(_to_binding(entry))
        for entry in getattr(self.app.__class__, "BINDINGS", []):
            out.append(_to_binding(entry))
        return out


def _to_binding(entry) -> Binding:
    """Normalise a BINDINGS entry to a Binding regardless of declaration style."""
    if isinstance(entry, Binding):
        return entry
    # Tuple form: ("key", "action", "description")
    key = entry[0]
    action = entry[1] if len(entry) > 1 else ""
    desc = entry[2] if len(entry) > 2 else action
    return Binding(key, action, desc)


def _format_key(key: str) -> str:
    """Render a Textual key spec for human display."""
    mapping = {
        "question_mark": "?",
        "escape": "esc",
    }
    return mapping.get(key, key)
