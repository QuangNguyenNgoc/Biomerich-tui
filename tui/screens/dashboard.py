"""Dashboard screen - main overview with engine status, biome, accounts."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Header, Static, Button, Label
from textual.containers import Vertical, Horizontal, Container

from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class DashboardScreen(VerticalScroll):
    """Main dashboard showing engine status, active biome, and account overview."""

    BINDINGS = [
        ("f5", "toggle_engine", "Start/Stop Macro"),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 1 3;
        grid-gutter: 1;
        padding: 1;
    }

    #accounts-panel { row-span: 1; column-span: 1; height: auto; border: solid $accent; padding: 1; }
    #stats-panel { row-span: 1; column-span: 1; height: auto; border: solid $warning; padding: 1; }
    #activity-panel { row-span: 1; column-span: 1; height: 1fr; border: solid $success; padding: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="accounts-panel")
        yield Static(id="stats-panel")
        yield Static(id="activity-panel")

    def on_mount(self) -> None:
        self._refresh_panels()
        self.set_interval(1.0, self._refresh_panels)

    def _refresh_panels(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        # 1. Accounts panel (Top priority)
        accounts_panel = self.query_one("#accounts-panel", Static)
        accounts_live = ctrl.get_live_accounts()
        table = Table(title="Accounts", expand=True, show_lines=False)
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Biome", style="magenta")
        table.add_column("Window", style="yellow")

        for i, acc in enumerate(accounts_live, 1):
            status = "Online" if acc.get("online") else "Offline"
            status_style = "green" if acc.get("online") else "red"
            biome = acc.get("currentBiome") or "-"
            hwnd = "Bound" if acc.get("hwndKnown") else "Unbound"
            table.add_row(
                str(i),
                acc.get("name", "?"),
                f"[{status_style}]{status}[/{status_style}]",
                biome,
                hwnd,
            )

        accounts_panel.update(Panel(table, border_style="blue"))

        # 2. Stats panel (Time Tracking & Eden/Biome)
        stats_panel = self.query_one("#stats-panel", Static)
        try:
            engine = ctrl.engine
            if engine and hasattr(engine, "time"):
                stats = engine.time.live()

                # Format session
                session_secs = engine.uptime if hasattr(engine, "uptime") else 0
                m, s = divmod(int(session_secs), 60)
                h, m = divmod(m, 60)
                session = f"{h:02d}:{m:02d}:{s:02d}"

                # Format total
                total_secs = stats.get("totalEngine", 0)
                m, s = divmod(int(total_secs), 60)
                h, m = divmod(m, 60)
                total = f"{h:02d}:{m:02d}:{s:02d}"

                afk_txt = ""
                if hasattr(engine, "anti_afk"):
                    is_on = engine.anti_afk.enabled()
                    afk_txt = f"Anti-AFK: [cyan]{'On' if is_on else 'Off'}[/cyan]"

                stats_text = f"Session Uptime: [bold]{session}[/bold]\nTotal Uptime: [bold]{total}[/bold]\n{afk_txt}"
                stats_panel.update(
                    Panel(
                        stats_text,
                        title="[bold]Stats & Tracking[/bold]",
                        border_style="yellow",
                    )
                )
            else:
                stats_panel.update(
                    Panel(
                        "Waiting for Engine...",
                        title="[bold]Stats & Tracking[/bold]",
                        border_style="yellow",
                    )
                )
        except Exception as e:
            stats_panel.update(
                Panel(
                    f"Error: {e}",
                    title="[bold]Stats & Tracking[/bold]",
                    border_style="yellow",
                )
            )

        # 3. Activity Panel (mini view)
        activity_panel = self.query_one("#activity-panel", Static)
        try:
            from core import activity_log

            res = activity_log.since(max(0, activity_log._seq - 10))
            entries = res.get("entries", [])
            if not entries:
                activity_panel.update(
                    Panel(
                        "[dim]No recent activity[/dim]",
                        title="Activity Log",
                        border_style="green",
                    )
                )
            else:
                lines = []
                for e in entries[-5:]:
                    ts = e.get("ts", "")
                    cat = e.get("category") or e.get("kind", "?")
                    txt = str(e.get("text", ""))[:40]
                    lines.append(f"[[dim]{ts}[/dim]] [[cyan]{cat}[/cyan]] {txt}")
                activity_panel.update(
                    Panel(
                        "\n".join(lines), title="Recent Activity", border_style="green"
                    )
                )
        except Exception as e:
            activity_panel.update(
                Panel(f"Error: {e}", title="Activity Log", border_style="red")
            )

    def action_toggle_engine(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return
        if ctrl.is_engine_running():
            result = ctrl.stop_engine()
            self.notify("Macro stopped", severity="warning")
        else:
            result = ctrl.start_engine()
            if result.get("ok"):
                self.notify("Macro started!", severity="information")
            else:
                errors = result.get("errors", ["Unknown error"])
                self.notify(f"Failed: {errors[0]}", severity="error")
        self._refresh_panels()
