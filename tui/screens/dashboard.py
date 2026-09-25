"""Dashboard screen - main overview with engine status, biome, accounts."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, Button, DataTable
from textual.containers import Vertical

from rich.panel import Panel


class DashboardScreen(VerticalScroll):
    """Main dashboard showing engine status, active biome, and account overview."""

    BINDINGS = [
        ("f5", "toggle_engine", "Start/Stop Macro"),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        padding: 1;
    }

    #dash-accounts-table {
        height: auto;
        max-height: 14;
        border: solid $accent;
        margin-bottom: 1;
    }

    #stats-panel {
        height: auto;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
    }

    #activity-panel {
        height: 1fr;
        min-height: 5;
        border: solid $success;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield DataTable(id="dash-accounts-table", cursor_type="none")
        yield Static(id="stats-panel")
        yield Static(id="activity-panel")

    def on_mount(self) -> None:
        # Initialize the DataTable columns once
        table = self.query_one("#dash-accounts-table", DataTable)
        table.add_columns("#", "Name", "Status", "Biome", "Window")

        # Cache state to avoid redundant re-renders
        self._prev_accounts_hash = None
        self._prev_stats_text = None
        self._prev_activity_text = None

        self._refresh_panels()
        self.set_interval(1.0, self._refresh_panels)

    def _refresh_panels(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        # --- 1. Accounts Table (DataTable with update_cell) ---
        self._refresh_accounts_table(ctrl)

        # --- 2. Stats Panel (only update when text changes) ---
        self._refresh_stats_panel(ctrl)

        # --- 3. Activity Panel (only update when text changes) ---
        self._refresh_activity_panel(ctrl)

    def _refresh_accounts_table(self, ctrl) -> None:
        accounts_live = ctrl.get_live_accounts()
        table = self.query_one("#dash-accounts-table", DataTable)

        # Build a hash of current data to check if anything changed
        row_data = []
        for i, acc in enumerate(accounts_live, 1):
            status = "Online" if acc.get("online") else "Offline"
            biome = acc.get("currentBiome") or "-"
            hwnd = "Bound" if acc.get("hwndKnown") else "Unbound"
            row_data.append((
                str(i),
                acc.get("name", "?"),
                status,
                biome,
                hwnd,
            ))

        # Quick hash: convert to tuple for comparison
        data_hash = tuple(row_data)
        if data_hash == self._prev_accounts_hash:
            return  # Nothing changed, skip re-render entirely
        self._prev_accounts_hash = data_hash

        # Check if row count changed (structural change → must rebuild)
        if table.row_count != len(row_data):
            table.clear()
            for row in row_data:
                table.add_row(*row)
        else:
            # Same row count → use update_cell for each cell
            row_keys = list(table.rows.keys())
            col_keys = list(table.columns.keys())
            for r_idx, row in enumerate(row_data):
                for c_idx, value in enumerate(row):
                    table.update_cell(
                        row_keys[r_idx],
                        col_keys[c_idx],
                        value,
                        update_width=False,
                    )

    def _refresh_stats_panel(self, ctrl) -> None:
        stats_panel = self.query_one("#stats-panel", Static)
        try:
            engine = ctrl.engine
            if engine and hasattr(engine, "time"):
                stats = engine.time.live()

                # Session uptime
                session_secs = engine.uptime if hasattr(engine, "uptime") else 0
                m, s = divmod(int(session_secs), 60)
                h, m = divmod(m, 60)
                session = f"{h:02d}:{m:02d}:{s:02d}"

                # Total uptime
                total_secs = stats.get("totalEngine", 0)
                m, s = divmod(int(total_secs), 60)
                h, m = divmod(m, 60)
                total = f"{h:02d}:{m:02d}:{s:02d}"

                afk_txt = ""
                if hasattr(engine, "anti_afk"):
                    is_on = engine.anti_afk.enabled()
                    afk_txt = f"Anti-AFK: [cyan]{'On' if is_on else 'Off'}[/cyan]"

                new_text = f"Session Uptime: [bold]{session}[/bold]\nTotal Uptime: [bold]{total}[/bold]\n{afk_txt}"
            else:
                new_text = "Waiting for Engine..."
        except Exception as e:
            new_text = f"Error: {e}"

        if new_text != self._prev_stats_text:
            self._prev_stats_text = new_text
            stats_panel.update(
                Panel(new_text, title="[bold]Stats & Tracking[/bold]", border_style="yellow")
            )

    def _refresh_activity_panel(self, ctrl) -> None:
        activity_panel = self.query_one("#activity-panel", Static)
        try:
            from core import activity_log

            res = activity_log.since(max(0, activity_log._seq - 10))
            entries = res.get("entries", [])
            if not entries:
                new_text = "[dim]No recent activity[/dim]"
            else:
                lines = []
                for e in entries[-5:]:
                    ts = e.get("ts", "")
                    cat = e.get("category") or e.get("kind", "?")
                    txt = str(e.get("text", ""))[:40]
                    lines.append(f"[[dim]{ts}[/dim]] [[cyan]{cat}[/cyan]] {txt}")
                new_text = "\n".join(lines)
        except Exception as e:
            new_text = f"Error: {e}"

        if new_text != self._prev_activity_text:
            self._prev_activity_text = new_text
            activity_panel.update(
                Panel(new_text, title="Recent Activity", border_style="green")
            )

    def action_toggle_engine(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return
        if ctrl.is_engine_running():
            ctrl.stop_engine()
            self.notify("Macro stopped", severity="warning")
        else:
            result = ctrl.start_engine()
            if result.get("ok"):
                self.notify("Macro started!", severity="information")
            else:
                errors = result.get("errors", ["Unknown error"])
                self.notify(f"Failed: {errors[0]}", severity="error")
        # Force immediate refresh after toggle
        self._prev_accounts_hash = None
        self._prev_stats_text = None
        self._refresh_panels()
