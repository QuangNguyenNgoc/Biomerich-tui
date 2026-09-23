"""Dashboard screen — main overview with engine status, biome, accounts."""

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
        grid-size: 2 2;
        grid-gutter: 1;
        padding: 1;
    }

    #engine-panel {
        row-span: 1;
        column-span: 1;
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    #biome-panel {
        row-span: 1;
        column-span: 1;
        height: auto;
        border: solid $secondary;
        padding: 1;
    }

    #accounts-panel {
        row-span: 1;
        column-span: 2;
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }

    #stats-panel {
        row-span: 1;
        column-span: 2;
        height: auto;
        border: solid $surface;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="engine-panel")
        yield Static(id="biome-panel")
        yield Static(id="accounts-panel")

    def on_mount(self) -> None:
        self._refresh_panels()
        self.set_interval(1.0, self._refresh_panels)

    def _refresh_panels(self) -> None:
        """Refresh all dashboard panels from controller state."""
        ctrl = self.app.controller
        if ctrl is None:
            return

        # Engine panel
        engine_panel = self.query_one("#engine-panel", Static)
        running = ctrl.is_engine_running()
        mode = ctrl.get_engine_mode()
        status_icon = "🟢 RUNNING" if running else "🔴 STOPPED"
        engine_panel.update(
            Panel(
                f"{status_icon}\nMode: [bold]{mode}[/bold]",
                title="[bold]Macro Engine[/bold]",
                border_style="green" if running else "red",
            )
        )

        # Biome panel
        biome_panel = self.query_one("#biome-panel", Static)
        state = ctrl.get_state()
        accounts_state = state.get("accounts", [])
        biome_text = ""
        for acc in accounts_state:
            name = acc.get("name", "?")
            biome = acc.get("biome", "Normal")
            online = "🟢" if acc.get("online") else "🔴"
            biome_text += f"{online} {name}: [bold cyan]{biome}[/bold cyan]\n"
        if not biome_text:
            biome_text = "[dim]No accounts configured[/dim]"
        biome_panel.update(
            Panel(
                biome_text.strip(),
                title="[bold]Active Biomes[/bold]",
                border_style="cyan",
            )
        )

        # Accounts panel
        accounts_panel = self.query_one("#accounts-panel", Static)
        table = Table(title="Accounts", expand=True, show_lines=False)
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Biome", style="magenta")
        table.add_column("Window", style="yellow")

        for i, acc in enumerate(accounts_state, 1):
            status = "Online" if acc.get("online") else "Offline"
            status_style = "green" if acc.get("online") else "red"
            biome = acc.get("biome", "-")
            hwnd = "Bound" if acc.get("hwnd") else "Unbound"
            table.add_row(
                str(i),
                acc.get("name", "?"),
                f"[{status_style}]{status}[/{status_style}]",
                biome,
                hwnd,
            )

        accounts_panel.update(Panel(table, border_style="blue"))

    def action_toggle_engine(self) -> None:
        """Toggle macro engine start/stop."""
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
