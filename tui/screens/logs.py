"""Logs screen — activity log, event log, account timeline."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, RichLog, TabbedContent, TabPane, Button
from textual.containers import Vertical

from rich.panel import Panel
from rich.text import Text


class LogsScreen(VerticalScroll):
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

                log_line = Text()
                log_line.append(f"{ts} ", style="dim")
                if account:
                    log_line.append(f"{account} ", style="cyan")
                log_line.append(text, style=style)

                activity_log.write(log_line)

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
        except Exception as e:
            pass

        # Timeline
        try:
            from core.account_timeline import get_all_summaries
            import datetime

            summaries = get_all_summaries()
            timeline_view = self.query_one("#timeline-view", Static)
            if not summaries:
                timeline_view.update(
                    Panel(
                        "[dim]No timeline data available yet.[/dim]", title="Timeline"
                    )
                )
            else:
                from rich.table import Table

                table = Table(expand=True, box=None)
                table.add_column("Account", style="cyan")
                table.add_column("State", style="bold")
                table.add_column("Duration", justify="right")

                for account_id, summary in summaries.items():
                    name = summary.get("name") or account_id
                    current_state = summary.get("current_state")
                    state_text = ""
                    if current_state:
                        st = current_state.get("state", "unknown")
                        since = current_state.get("since", 0)
                        dur = int(datetime.datetime.now().timestamp() - since)

                        m, s = divmod(dur, 60)
                        h, m = divmod(m, 60)
                        dur_str = f"{h:02d}:{m:02d}:{s:02d}"

                        color = (
                            "green"
                            if st == "running"
                            else "dim" if st == "stopped" else "yellow"
                        )
                        state_text = f"[{color}]{st}[/{color}]"
                        table.add_row(name, state_text, dur_str)

                timeline_view.update(Panel(table, title="Account Timeline"))
        except Exception:
            pass
