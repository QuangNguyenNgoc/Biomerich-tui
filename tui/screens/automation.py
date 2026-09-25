import pyperclip
"""Automation screen — calibration, fishing, merchant, autopop, eden config."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, Button, Label, TabbedContent, TabPane, Input, Switch
from textual.containers import Vertical, Horizontal

from rich.panel import Panel
from rich.table import Table


class AutomationScreen(VerticalScroll):
    """Automation configuration with tabs for each subsystem."""

    DEFAULT_CSS = """
    AutomationScreen {
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Calibration", id="tab-calib"):
                yield CalibrationPane()
            with TabPane("Fishing", id="tab-fishing"):
                yield FishingPane()
            with TabPane("Merchant", id="tab-merchant"):
                yield MerchantPane()
            with TabPane("Auto Pop", id="tab-autopop"):
                yield AutoPopPane()
            with TabPane("Eden", id="tab-eden"):
                yield EdenPane()


class CalibrationPane(Static):
    """Calibration sub-panel: preset selection, manual capture, import/export."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Calibration[/bold]")
            yield Label("Select a preset or capture manually.")
            with Horizontal():
                yield Button(
                    "Auto-Detect & Apply", variant="primary", id="btn-calib-auto"
                )
                yield Button("Manual Capture", variant="warning", id="btn-calib-manual")
            with Horizontal():
                yield Button("Import JSON", variant="default", id="btn-calib-import")
                yield Button("Export JSON", variant="default", id="btn-calib-export")
            yield Static(id="calib-status")

    def on_mount(self) -> None:
        self._refresh_status()

    def _refresh_status(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return
        state = ctrl.get_state()
        automation = state.get("automation", {})
        preset = automation.get("preset", "None")
        pixel_count = len(automation.get("pixels", {}))
        self.query_one("#calib-status", Static).update(
            Panel(
                f"Active Preset: [bold cyan]{preset}[/bold cyan]\n"
                f"Calibrated Points: [bold]{pixel_count}[/bold]",
                title="Status",
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        if event.button.id == "btn-calib-auto":
            result = ctrl.apply_recommended_preset()
            if result.get("ok"):
                self.notify(f"Applied preset: {result.get('preset', '?')}")
            else:
                self.notify("No matching preset found", severity="warning")
            self._refresh_status()

        elif event.button.id == "btn-calib-export":
            text = ctrl.export_calibration()
            if text:
                self.notify("Calibration JSON copied to clipboard")


class FishingPane(Static):
    """Fishing configuration sub-panel."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Fishing Bot[/bold]")
            yield Label("[dim]Configure fishing automation per account[/dim]")
            yield Static(id="fishing-info")

    def on_mount(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return
        state = ctrl.get_state()
        fishing = state.get("automation", {}).get("fishing", {})
        info = f"OCR Failsafe: {'✅' if fishing.get('ocrFailsafe') else '❌'}\n"
        info += f"Webhook: {'✅' if fishing.get('webhookEnabled') else '❌'}"
        self.query_one("#fishing-info", Static).update(
            Panel(info, title="Fishing Config")
        )


class MerchantPane(Static):
    """Merchant autobuy sub-panel."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Merchant Autobuy[/bold]")
            yield Label("[dim]Configure auto-purchase from Mari, Jester, Rin[/dim]")
            yield Static(id="merchant-info")

    def on_mount(self) -> None:
        self.query_one("#merchant-info", Static).update(
            Panel(
                "[dim]Merchant config will load from controller[/dim]",
                title="Merchants",
            )
        )


class AutoPopPane(Static):
    """Auto Pop item consumption sub-panel."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Auto Pop[/bold]")
            yield Label("[dim]Automatically use items when specific biomes roll[/dim]")
            yield Static(id="autopop-info")

    def on_mount(self) -> None:
        self.query_one("#autopop-info", Static).update(
            Panel(
                "[dim]AutoPop config will load from controller[/dim]", title="Auto Pop"
            )
        )


class EdenPane(Static):
    """Eden automation sub-panel."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Eden Automation[/bold]")
            yield Label("[dim]Configure Eden click spam[/dim]")
            yield Static(id="eden-info")

    def on_mount(self) -> None:
        self.query_one("#eden-info", Static).update(
            Panel("[dim]Eden config will load from controller[/dim]", title="Eden")
        )
