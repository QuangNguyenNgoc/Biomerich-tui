"""Accounts screen — manage Roblox accounts, tokens, and launches."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, Button, Input, Label, DataTable
from textual.containers import Vertical, Horizontal

import pyperclip


class AccountsScreen(VerticalScroll):
    """Account management: add, edit, delete, token input, launch."""

    DEFAULT_CSS = """
    AccountsScreen {
        padding: 1;
    }

    #account-table-container {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }

    #account-actions {
        height: auto;
        padding: 0;
    }

    .action-row {
        height: auto;
        padding: 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="account-table-container"):
            yield DataTable(id="account-table", cursor_type="row")
            
        with Horizontal(classes="action-row", id="account-actions"):
            yield Button("Add Account", variant="success", id="btn-add")
            yield Button("Launch All", variant="primary", id="btn-launch-all")
            yield Button("Refresh", variant="default", id="btn-refresh")
            yield Button("Edit Selected", variant="warning", id="btn-edit", disabled=True)
            yield Button("Delete Selected", variant="error", id="btn-delete", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("#", "Name", "Enabled", "Token", "Window", "Modules", "VIP Link")
        self._refresh_list()

    def _refresh_list(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        state = ctrl.get_state()
        accounts = state.get("accounts", [])
        accounts = ctrl.get_live_accounts()

        table = self.query_one(DataTable)
        table.clear()

        for i, acc in enumerate(accounts, 1):
            enabled = "✅" if acc.get("enabled", True) else "❌"
            has_token = "🔑 Set" if acc.get("hasToken") else "⚠️ Missing"
            hwnd = "Bound" if acc.get("hwnd") else "Unbound"
            hwnd = "Bound" if acc.get("hwndKnown") else "Unbound"
            modules = []
            if acc.get("fishingEnabled"):
                modules.append("🎣")
            if acc.get("merchantEnabled"):
                modules.append("🏪")
            if acc.get("autopopEnabled"):
                modules.append("🧪")
            mod_str = " ".join(modules) if modules else "-"
            
            link = acc.get("link", "")
            display_link = link if link else "-"
            if len(display_link) > 30:
                display_link = display_link[:20] + "..." + display_link[-5:]

            table.add_row(
                str(i), acc.get("name", "?"), enabled, has_token, hwnd, mod_str, display_link,
                key=acc.get("id", "")
            )
            
        self._update_button_states()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        if event.button.id == "btn-add":
            self.app.push_screen(AddAccountDialog(), self._on_dialog_closed)
        elif event.button.id == "btn-launch-all":
            ctrl.launch_all_accounts()
            self.notify("Launching all accounts...")
        elif event.button.id == "btn-refresh":
            self._refresh_list()
            self.notify("Refreshed")
        elif event.button.id == "btn-edit":
            table = self.query_one(DataTable)
            if table.cursor_row is not None:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                acc_id = row_key.value
                self.app.push_screen(EditAccountDialog(acc_id=acc_id), self._on_dialog_closed)
        elif event.button.id == "btn-delete":
            table = self.query_one(DataTable)
            if table.cursor_row is not None:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                acc_id = row_key.value
                result = ctrl.delete_account(acc_id)
                if result.get("ok"):
                    self.notify("Account deleted")
                    self._refresh_list()
                else:
                    self.notify(f"Failed to delete: {result.get('error')}", severity="error")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._update_button_states()
        
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        self._update_button_states()
        try:
            # Click copy for Token or Link
            val = str(event.value)
            if val and val != "-" and "Missing" not in val:
                pyperclip.copy(val)
                self.notify(f"Copied '{val}' to clipboard!")
        except Exception:
            pass
        
    def _update_button_states(self) -> None:
        table = self.query_one(DataTable)
        has_selection = table.cursor_row is not None and table.row_count > 0
        self.query_one("#btn-delete", Button).disabled = not has_selection
        self.query_one("#btn-edit", Button).disabled = not has_selection
        
    def _on_dialog_closed(self, result) -> None:
        if result:
            self._refresh_list()


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
            yield Label("VIP Server Link (optional):")
            yield Input(
                placeholder="https://www.roblox.com/games/...",
                id="input-link",
            )
            with Horizontal():
                yield Button("Add", variant="success", id="btn-confirm")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
            return

        if event.button.id == "btn-confirm":
            name = self.query_one("#input-name", Input).value.strip()
            token = self.query_one("#input-token", Input).value.strip()
            link = self.query_one("#input-link", Input).value.strip()
            if not name:
                self.notify("Username is required", severity="error")
                return

            ctrl = self.app.controller
            if ctrl:
                result = ctrl.add_account(name, link=link, token=token if token else None)
                if result.get("ok"):
                    self.notify(f"Account '{name}' added!")
                    self.dismiss(True)
                else:
                    self.notify(
                        f"Failed: {result.get('error', 'Unknown')}",
                        severity="error",
                    )
class EditAccountDialog(Screen):
    """Modal dialog to edit an existing account."""
    
    DEFAULT_CSS = """
    EditAccountDialog {
        align: center middle;
    }

    #dialog-container {
        width: 60;
        height: auto;
        border: thick $warning;
        padding: 1 2;
        background: $surface;
    }
    """
    
    def __init__(self, acc_id: str, **kwargs):
        super().__init__(**kwargs)
        self.acc_id = acc_id
        
    def on_mount(self) -> None:
        ctrl = self.app.controller
        if ctrl:
            state = ctrl.get_state()
            accounts = state.get("accounts", [])
            for acc in accounts:
                if acc.get("id") == self.acc_id:
                    self.query_one("#input-name", Input).value = acc.get("name", "")
                    self.query_one("#input-link", Input).value = acc.get("link", "")
                    break

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Label("Edit Account", classes="title")
            yield Label("Roblox Username:")
            yield Input(placeholder="Enter username...", id="input-name")
            yield Label(".ROBLOSECURITY Token (leave blank to keep current):")
            yield Input(
                placeholder="Paste token here...",
                id="input-token",
                password=True,
            )
            yield Label("VIP Server Link (optional):")
            yield Input(
                placeholder="https://www.roblox.com/games/...",
                id="input-link",
            )
            with Horizontal():
                yield Button("Save", variant="warning", id="btn-save")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
            return

        if event.button.id == "btn-save":
            name = self.query_one("#input-name", Input).value.strip()
            token = self.query_one("#input-token", Input).value.strip()
            link = self.query_one("#input-link", Input).value.strip()
            
            if not name:
                self.notify("Username is required", severity="error")
                return

            ctrl = self.app.controller
            if ctrl:
                result = ctrl.update_account(
                    self.acc_id,
                    name=name,
                    link=link,
                    token=token if token else None,
                )
                if result.get("ok"):
                    self.notify(f"Account '{name}' updated!")
                    self.dismiss(True)
                else:
                    self.notify(
                        f"Failed: {result.get('error', 'Unknown')}",
                        severity="error",
                    )

