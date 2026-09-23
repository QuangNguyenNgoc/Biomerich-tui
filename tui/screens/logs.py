"""Logs screen — activity log, event log, account timeline."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, RichLog, TabbedContent, TabPane, Button
from textual.containers import Vertical

from rich.panel import Panel
from rich.text import Text


class LogsScreen(Screen):
    """Log viewer with tabs for activity, events, and timeline."""

    DEFAULT_CSS = """
    LogsScreen {
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Activity Log", id="tab-activity"):
                yield RichLog(
                    highlight=True,
                    markup=True,
                    wrap=True,
                    max_lines=500,
                    id="activity-log",
                )
            with TabPane("Event Log", id="tab-events"):
                yield RichLog(
                    highlight=True,
                    markup=True,
                    wrap=True,
                    max_lines=150,
                    id="event-log",
                )
            with TabPane("Timeline", id="tab-timeline"):
                yield Static(id="timeline-view")

    def on_mount(self) -> None:
        self._last_activity_id = 0
        self._last_event_id = 0
        self.set_interval(1.0, self._poll_logs)

    def _poll_logs(self) -> None:
        """Poll controller for new log entries."""
        ctrl = self.app.controller
        if ctrl is None:
            return

        # Activity log
        try:
            result = ctrl.get_activity_log(self._last_activity_id)
            entries = result.get("entries", [])
            head = result.get("head", self._last_activity_id)
            activity_log = self.query_one("#activity-log", RichLog)
            for entry in entries:
                kind = entry.get("kind", "info")
                ts = entry.get("ts", "")
                text = entry.get("text", "")
                account = entry.get("account", "")

                style_map = {
                    "info": "white",
                    "warn": "yellow",
                    "error": "red",
                    "success": "green",
                }
                style = style_map.get(kind, "white")

                prefix = f"[dim]{ts}[/dim] "
                if account:
                    prefix += f"[cyan]{account}[/cyan] "
                activity_log.write(f"{prefix}[{style}]{text}[/{style}]")

            self._last_activity_id = head
        except Exception:
            pass

        # Event log
        try:
            events = ctrl.get_event_log(self._last_event_id)
            event_log = self.query_one("#event-log", RichLog)
            for ev in events:
                self._last_event_id = max(self._last_event_id, ev.get("id", 0))
                title = ev.get("title", "")
                detail = ev.get("detail", "")
                kind = ev.get("kind", "system")

                color_map = {
                    "biome": "cyan",
                    "aura": "magenta",
                    "merchant": "yellow",
                    "fishing": "blue",
                    "system": "dim",
                }
                color = color_map.get(kind, "white")
                event_log.write(f"[{color}]● {title}[/{color}]  {detail}")
        except Exception:
            pass
