"""Logs screen - activity log, event log, aura log."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, RichLog, TabbedContent, TabPane
from textual.containers import Vertical

from rich.panel import Panel
from rich.text import Text


class LogsScreen(VerticalScroll):
    """Log viewer with tabs for activity, events, and aura."""

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
            with TabPane("Aura Log", id="tab-aura"):
                yield RichLog(
                    highlight=True,
                    markup=True,
                    wrap=True,
                    max_lines=300,
                    id="aura-log",
                )

    def on_mount(self) -> None:
        self._last_activity_id = 0
        self._last_event_id = 0
        self._last_aura_id = 0
        self.set_interval(1.0, self._poll_logs)

    def _poll_logs(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        # Activity log
        try:
            res = ctrl.get_activity_log(self._last_activity_id)
            entries = res.get("entries", [])
            head = res.get("head", self._last_activity_id)
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

                line = Text()
                line.append(f"[{ts}] ", style="bright_black")
                if account:
                    line.append(f"[{account}] ", style="cyan")
                line.append(str(text), style=style)
                activity_log.write(line)

            self._last_activity_id = head
        except Exception:
            pass

        # Event log
        try:
            events = ctrl.get_event_log(self._last_event_id)
            event_log = self.query_one("#event-log", RichLog)
            for ev in events:
                self._last_event_id = max(self._last_event_id, ev.get("id", 0))
                title = str(ev.get("title", ""))
                detail = str(ev.get("detail", ""))
                kind = ev.get("kind", "system")

                color_map = {
                    "biome": "cyan",
                    "aura": "magenta",
                    "merchant": "yellow",
                    "fishing": "blue",
                    "system": "dim",
                }
                color = color_map.get(kind, "white")

                ev_line = Text()
                ev_line.append("● ", style=color)
                ev_line.append(title, style=color)
                if detail:
                    ev_line.append(f"  {detail}")

                event_log.write(ev_line)
        except Exception:
            pass

        # Aura log
        try:
            aura_entries = ctrl.get_aura_log(self._last_aura_id)
            if aura_entries:
                aura_log = self.query_one("#aura-log", RichLog)
                for entry in aura_entries:
                    eid = entry.get("id", 0)
                    if eid > self._last_aura_id:
                        self._last_aura_id = eid
                    ts = entry.get("timestamp", "")
                    acc = entry.get("account", "Unknown")
                    biome = entry.get("biome", "?")
                    found = entry.get("found", [])
                    found_str = ", ".join(found) if found else "None"

                    text = Text()
                    text.append(f"[{ts}] ", style="bright_black")
                    text.append(f"[{acc}] ", style="cyan")
                    text.append("Biome: ", style="white")
                    text.append(f"{biome} ", style="bold magenta")
                    text.append("Aura: ", style="white")
                    text.append(f"{found_str}", style="bold yellow")
                    aura_log.write(text)
        except Exception:
            pass
