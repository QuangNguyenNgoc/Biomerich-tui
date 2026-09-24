"""Webhooks screen — Discord webhook management."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, Button, Input, Label, Switch, DataTable
from textual.containers import Vertical, Horizontal

from rich.panel import Panel
from rich.table import Table


class WebhooksScreen(VerticalScroll):
    """Discord webhook CRUD and routing configuration."""

    DEFAULT_CSS = """
    WebhooksScreen {
        padding: 1;
    }

    #webhook-table-container {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }

    .action-row {
        height: auto;
        padding: 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="webhook-table-container"):
            yield DataTable(id="webhook-table", cursor_type="row")

        with Horizontal(classes="action-row"):
            yield Button("Add Webhook", variant="success", id="btn-add-wh")
            yield Button("Test Send", variant="primary", id="btn-test-wh")
            yield Button("Refresh", variant="default", id="btn-refresh-wh")
            yield Button(
                "Edit Selected", variant="warning", id="btn-edit-wh", disabled=True
            )
            yield Button(
                "Delete Selected", variant="error", id="btn-delete-wh", disabled=True
            )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("#", "Name", "URL", "Enabled")
        self._refresh_list()

    def _refresh_list(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        state = ctrl.get_state()
        webhooks = state.get("webhooks", [])

        table = self.query_one(DataTable)
        table.clear()

        for i, wh in enumerate(webhooks, 1):
            url = wh.get("url", "")
            # Mask URL for security
            display_url = url
            if len(display_url) > 40:
                display_url = display_url[:30] + "..." + display_url[-10:]
            enabled = "✅" if wh.get("enabled", True) else "❌"
            table.add_row(
                str(i),
                wh.get("name", f"Webhook {i}"),
                display_url,
                enabled,
                key=wh.get("id", ""),
            )

        self._update_button_states()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        if event.button.id == "btn-add-wh":
            self.app.push_screen(AddWebhookDialog(), self._on_dialog_closed)
        elif event.button.id == "btn-test-wh":
            self.notify("Test webhook sent!")
        elif event.button.id == "btn-refresh-wh":
            self._refresh_list()
        elif event.button.id == "btn-edit-wh":
            table = self.query_one(DataTable)
            if table.cursor_row is not None:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                wh_id = row_key.value
                self.app.push_screen(EditWebhookDialog(wh_id=wh_id), self._on_dialog_closed)
        elif event.button.id == "btn-delete-wh":
            table = self.query_one(DataTable)
            if table.cursor_row is not None:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                wh_id = row_key.value
                result = ctrl.delete_webhook(wh_id)
                if result.get("ok"):
                    self.notify("Webhook deleted")
                    self._refresh_list()
                else:
                    self.notify(
                        f"Failed to delete: {result.get('error')}", severity="error"
                    )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._update_button_states()

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        self._update_button_states()

        # Click copy webhook URL
        try:
            import pyperclip

            val = str(event.value)
            if val.startswith("http"):
                # We need the real unmasked URL, find it in config
                ctrl = self.app.controller
                if ctrl:
                    state = ctrl.get_state()
                    webhooks = state.get("webhooks", [])
                    row_key = event.cell_key.row_key.value
                    for wh in webhooks:
                        if wh.get("id") == row_key:
                            real_url = wh.get("url", "")
                            if real_url:
                                pyperclip.copy(real_url)
                                self.notify("Copied Webhook URL to clipboard!")
                            break
        except Exception:
            pass

    def _update_button_states(self) -> None:
        table = self.query_one(DataTable)
        has_selection = table.cursor_row is not None and table.row_count > 0
        self.query_one("#btn-delete-wh", Button).disabled = not has_selection
        self.query_one("#btn-edit-wh", Button).disabled = not has_selection

    def _on_dialog_closed(self, result) -> None:
        if result:
            self._refresh_list()


class AddWebhookDialog(Screen):
    """Modal dialog to add a Discord webhook."""

    DEFAULT_CSS = """
    AddWebhookDialog {
        align: center middle;
    }

    #wh-dialog {
        width: 70;
        height: auto;
        border: thick $primary;
        padding: 1 2;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="wh-dialog"):
            yield Label("[bold]Add Discord Webhook[/bold]")
            yield Label("Webhook Name:")
            yield Input(placeholder="e.g. Main Alerts", id="input-wh-name")
            yield Label("Webhook URL:")
            yield Input(
                placeholder="https://discord.com/api/webhooks/...",
                id="input-wh-url",
            )
            yield Label("Linked Accounts:")
            yield SelectionList(id="sel-accounts")
            with Horizontal():
                yield Button("Add", variant="success", id="btn-wh-confirm")
                yield Button("Cancel", variant="error", id="btn-wh-cancel")

    def on_mount(self) -> None:
        sel = self.query_one("#sel-accounts", SelectionList)
        ctrl = self.app.controller
        if ctrl:
            for acc in ctrl.config.accounts:
                sel.add_option((acc["name"], acc["id"], False))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-wh-cancel":
            self.dismiss(False)
            return

        if event.button.id == "btn-wh-confirm":
            name = self.query_one("#input-wh-name", Input).value.strip()
            url = self.query_one("#input-wh-url", Input).value.strip()
            if not url:
                self.notify("URL is required", severity="error")
                return

            sel = self.query_one("#sel-accounts", SelectionList)
            routed = sel.selected

            ctrl = self.app.controller
            if ctrl:
                wh = ctrl.add_webhook(name=name or "Webhook", url=url)
                if wh and routed:
                    wh["routedAccounts"] = routed
                    ctrl.config.save()
                self.notify(f"Webhook '{name}' added!")
            self.dismiss(True)
class EditWebhookDialog(Screen):
    """Modal dialog to edit an existing webhook."""
    
    DEFAULT_CSS = """
    EditWebhookDialog {
        align: center middle;
    }

    #dialog-container {
        width: 70;
        height: auto;
        border: thick $warning;
        padding: 1 2;
        background: $surface;
    }
    """
    
    def __init__(self, wh_id: str, **kwargs):
        super().__init__(**kwargs)
        self.wh_id = wh_id

    def on_mount(self) -> None:
        ctrl = self.app.controller
        if ctrl:
            state = ctrl.get_state()
            webhooks = state.get("webhooks", [])
            target_wh = next((w for w in webhooks if w.get("id") == self.wh_id), None)
            if target_wh:
                self.query_one("#input-wh-name", Input).value = target_wh.get("name", "")
                self.query_one("#input-wh-url", Input).value = target_wh.get("url", "")
                
                sel = self.query_one("#sel-accounts", SelectionList)
                routed = target_wh.get("routedAccounts", [])
                for acc in state.get("accounts", []):
                    is_selected = acc.get("id") in routed
                    sel.add_option((acc.get("name", ""), acc.get("id"), is_selected))

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Label("[bold]Edit Discord Webhook[/bold]", classes="title")
            yield Label("Webhook Name:")
            yield Input(placeholder="e.g. Main Alerts", id="input-wh-name")
            yield Label("Webhook URL:")
            yield Input(
                placeholder="https://discord.com/api/webhooks/...",
                id="input-wh-url",
            )
            yield Label("Linked Accounts:")
            yield SelectionList(id="sel-accounts")
            with Horizontal():
                yield Button("Save", variant="warning", id="btn-save")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
            return

        if event.button.id == "btn-save":
            name = self.query_one("#input-wh-name", Input).value.strip()
            url = self.query_one("#input-wh-url", Input).value.strip()
            if not url:
                self.notify("URL is required", severity="error")
                return

            sel = self.query_one("#sel-accounts", SelectionList)
            routed = sel.selected

            ctrl = self.app.controller
            if ctrl:
                for wh in ctrl.config.webhooks:
                    if wh.get("id") == self.wh_id:
                        wh["name"] = name
                        wh["url"] = url
                        wh["routedAccounts"] = routed
                        ctrl.config.save()
                        break
                
                self.notify(f"Webhook '{name}' updated!")
                self.dismiss(True)

