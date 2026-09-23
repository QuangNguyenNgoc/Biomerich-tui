"""Accounts screen — manage Roblox accounts, tokens, and launches."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, Button, Input, Label
from textual.containers import Vertical, Horizontal

from rich.panel import Panel
from rich.table import Table


class AccountsScreen(VerticalScroll):
    """Account management: add, edit, delete, token input, launch."""

    DEFAULT_CSS = """
    AccountsScreen {
        padding: 1;
    }

    #account-list {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #account-actions {
        height: auto;
        padding: 1;
    }

    .action-row {
        height: 3;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="account-list")
        with Horizontal(classes="action-row"):
            yield Button("Add Account", variant="success", id="btn-add")
            yield Button("Launch All", variant="primary", id="btn-launch-all")
            yield Button("Refresh", variant="default", id="btn-refresh")

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        state = ctrl.get_state()
        accounts = state.get("accounts", [])

        table = Table(title="Roblox Accounts", expand=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan bold")
        table.add_column("Enabled", style="green")
        table.add_column("Token", style="yellow")
        table.add_column("Window", style="magenta")
        table.add_column("Modules", style="blue")

        for i, acc in enumerate(accounts, 1):
            enabled = "✅" if acc.get("enabled", True) else "❌"
            has_token = "🔑 Set" if acc.get("hasToken") else "⚠️ Missing"
            hwnd = "Bound" if acc.get("hwnd") else "Unbound"
            modules = []
            if acc.get("fishingEnabled"):
                modules.append("🎣")
            if acc.get("merchantEnabled"):
                modules.append("🏪")
            if acc.get("autopopEnabled"):
                modules.append("🧪")
            mod_str = " ".join(modules) if modules else "-"
            table.add_row(
                str(i), acc.get("name", "?"), enabled, has_token, hwnd, mod_str
            )

        panel = Panel(table, border_style="blue")
        self.query_one("#account-list", Static).update(panel)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        if event.button.id == "btn-add":
            self.app.push_screen(AddAccountDialog())
        elif event.button.id == "btn-launch-all":
            ctrl.launch_all_accounts()
            self.notify("Launching all accounts...")
        elif event.button.id == "btn-refresh":
            self._refresh_list()
            self.notify("Refreshed")


class AddAccountDialog(Screen):
    """Modal dialog to add a new account."""

    DEFAULT_CSS = """
    AddAccountDialog {
        align: center middle;
    }

    #dialog-container {
        width: 60;
        height: auto;
        border: thick $primary;
        padding: 1 2;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Label("Add New Account", classes="title")
            yield Label("Roblox Username:")
            yield Input(placeholder="Enter username...", id="input-name")
            yield Label(".ROBLOSECURITY Token (optional):")
            yield Input(
                placeholder="Paste token here...",
                id="input-token",
                password=True,
            )
            with Horizontal():
                yield Button("Add", variant="success", id="btn-confirm")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.app.pop_screen()
            return

        if event.button.id == "btn-confirm":
            name = self.query_one("#input-name", Input).value.strip()
            token = self.query_one("#input-token", Input).value.strip()
            if not name:
                self.notify("Username is required", severity="error")
                return

            ctrl = self.app.controller
            if ctrl:
                result = ctrl.add_account(name, token=token if token else None)
                if result.get("ok"):
                    self.notify(f"Account '{name}' added!")
                else:
                    self.notify(
                        f"Failed: {result.get('error', 'Unknown')}",
                        severity="error",
                    )
            self.app.pop_screen()
