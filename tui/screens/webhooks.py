"""Webhooks screen — Discord webhook management."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, Button, Input, Label, Switch
from textual.containers import Vertical, Horizontal

from rich.panel import Panel
from rich.table import Table


class WebhooksScreen(VerticalScroll):
    """Discord webhook CRUD and routing configuration."""

    DEFAULT_CSS = """
    WebhooksScreen {
        padding: 1;
    }

    #webhook-list {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="webhook-list")
        with Horizontal():
            yield Button("Add Webhook", variant="success", id="btn-add-wh")
            yield Button("Test Send", variant="primary", id="btn-test-wh")
            yield Button("Refresh", variant="default", id="btn-refresh-wh")

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        state = ctrl.get_state()
        webhooks = state.get("webhooks", [])

        table = Table(title="Discord Webhooks", expand=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan bold")
        table.add_column("URL", style="yellow", max_width=50)
        table.add_column("Enabled", style="green")

        for i, wh in enumerate(webhooks, 1):
            url = wh.get("url", "")
            # Mask URL for security
            if len(url) > 40:
                url = url[:30] + "..." + url[-10:]
            enabled = "✅" if wh.get("enabled", True) else "❌"
            table.add_row(str(i), wh.get("name", f"Webhook {i}"), url, enabled)

        if not webhooks:
            self.query_one("#webhook-list", Static).update(
                Panel("[dim]No webhooks configured[/dim]", title="Webhooks")
            )
        else:
            self.query_one("#webhook-list", Static).update(Panel(table))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        if event.button.id == "btn-add-wh":
            self.app.push_screen(AddWebhookDialog())
        elif event.button.id == "btn-test-wh":
            self.notify("Test webhook sent!")
        elif event.button.id == "btn-refresh-wh":
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
            with Horizontal():
                yield Button("Add", variant="success", id="btn-wh-confirm")
                yield Button("Cancel", variant="error", id="btn-wh-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-wh-cancel":
            self.app.pop_screen()
            return

        if event.button.id == "btn-wh-confirm":
            name = self.query_one("#input-wh-name", Input).value.strip()
            url = self.query_one("#input-wh-url", Input).value.strip()
            if not url:
                self.notify("URL is required", severity="error")
                return

            ctrl = self.app.controller
            if ctrl:
                ctrl.add_webhook(name=name or "Webhook", url=url)
                self.notify(f"Webhook '{name}' added!")
            self.app.pop_screen()
