"""Live status bar widget — polls status_events.snapshot() and displays engine state."""

from textual.widgets import Static
from textual.reactive import reactive

from rich.text import Text


class StatusBar(Static):
    """A horizontally laid-out status bar showing engine state, biome, and elapsed time."""

    engine_running: reactive[bool] = reactive(False)
    engine_mode: reactive[str] = reactive("idle")
    status_text: reactive[str] = reactive("")
    detail_text: reactive[str] = reactive("")

    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """

    def render(self) -> Text:
        parts = Text()

        # Engine indicator
        if self.engine_running:
            parts.append(" ● ", style="bold green")
            parts.append("RUNNING", style="bold green")
        else:
            parts.append(" ○ ", style="dim")
            parts.append("STOPPED", style="dim")

        parts.append("  │  ", style="dim")

        # Mode
        mode_style = {
            "idle": "yellow",
            "automation": "cyan",
            "eden": "magenta",
        }.get(self.engine_mode, "white")
        parts.append(f"Mode: {self.engine_mode}", style=mode_style)

        # Status text
        if self.status_text:
            parts.append("  │  ", style="dim")
            parts.append(self.status_text, style="white")

        # Detail text
        if self.detail_text:
            parts.append("  │  ", style="dim")
            parts.append(self.detail_text, style="dim italic")

        return parts

    def update_from_snapshot(self, snapshot: dict) -> None:
        """Update status bar from a status_events.snapshot() dict."""
        self.status_text = snapshot.get("text", "")
        self.detail_text = snapshot.get("detail", "")

    def set_engine_state(self, running: bool, mode: str = "idle") -> None:
        self.engine_running = running
        self.engine_mode = mode
