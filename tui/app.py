"""
SolRich_TUI — Main Textual Application.

This replaces the old main.py + bridge.py web UI with a full terminal UI.
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Label, ContentSwitcher
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from tui.widgets.status_bar import StatusBar
from tui.screens.dashboard import DashboardScreen
from tui.screens.accounts import AccountsScreen
from tui.screens.settings import SettingsScreen
from tui.screens.automation import AutomationScreen
from tui.screens.performance import PerformanceScreen
from tui.screens.logs import LogsScreen
from tui.screens.webhooks import WebhooksScreen


# Navigation menu items
NAV_ITEMS = [
    ("dashboard", "Dashboard", "1"),
    ("accounts", "Accounts", "2"),
    ("settings", "Settings", "3"),
    ("automation", "Automation", "4"),
    ("performance", "Performance", "5"),
    ("logs", "Logs", "6"),
    ("webhooks", "Webhooks", "7"),
]

SCREEN_MAP = {
    "dashboard": DashboardScreen,
    "accounts": AccountsScreen,
    "settings": SettingsScreen,
    "automation": AutomationScreen,
    "performance": PerformanceScreen,
    "logs": LogsScreen,
    "webhooks": WebhooksScreen,
}


class SolRichTUI(App):
    """SolRich_TUI — Terminal User Interface for Sol's RNG macro."""

    TITLE = "SolRich_TUI"
    SUB_TITLE = "Sol's RNG Macro — Terminal Edition"

    CSS = """
    Screen {
        background: $background;
    }

    #app-container {
        height: 1fr;
    }

    #sidebar {
        width: 22;
        dock: left;
        border-right: solid $primary;
        padding: 1 0;
    }

    .nav-btn {
        width: 100%;
        margin: 0 0 0 0;
    }

    .nav-btn.-active {
        background: $primary;
        color: $text;
    }

    #content-area {
        width: 1fr;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("f5", "toggle_engine", "Start/Stop Macro", show=True),
        Binding("1", "show_screen('dashboard')", "Dashboard", show=False),
        Binding("2", "show_screen('accounts')", "Accounts", show=False),
        Binding("3", "show_screen('settings')", "Settings", show=False),
        Binding("4", "show_screen('automation')", "Automation", show=False),
        Binding("5", "show_screen('performance')", "Performance", show=False),
        Binding("6", "show_screen('logs')", "Logs", show=False),
        Binding("7", "show_screen('webhooks')", "Webhooks", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.controller = None  # Will be set in on_mount
        self._active_screen_name = "dashboard"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatusBar(id="status-bar")

        with Horizontal(id="app-container"):
            with Vertical(id="sidebar"):
                for key, label, shortcut in NAV_ITEMS:
                    btn = Button(
                        f" {shortcut}  {label}",
                        id=f"nav-{key}",
                        classes="nav-btn",
                        variant="default",
                    )
                    yield btn

            with ContentSwitcher(initial="dashboard", id="content-area"):
                for key, cls in SCREEN_MAP.items():
                    yield cls(id=key)

        yield Footer()

    def on_mount(self) -> None:
        """Initialize core systems after TUI is ready."""
        self._init_controller()
        self._switch_content("dashboard")
        self._start_status_polling()

    def _init_controller(self) -> None:
        """Initialize the AppController (core business logic)."""
        try:
            from tui.app_controller import AppController
            self.controller = AppController()
            self.controller.on("engine_started", self._on_engine_state_change)
            self.controller.on("engine_stopped", self._on_engine_state_change)
            self.controller.on("mode_changed", self._on_mode_change)
            # Start background services after TUI is ready
            self.controller.startup_services()
        except Exception as e:
            self.notify(
                f"Controller init failed: {e}",
                severity="error",
                timeout=10,
            )

    def _start_status_polling(self) -> None:
        """Poll status_events every second to update status bar."""
        self.set_interval(1.0, self._poll_status)

    def _poll_status(self) -> None:
        """Update status bar from engine state."""
        if self.controller is None:
            return
        try:
            status_bar = self.query_one("#status-bar", StatusBar)
            running = self.controller.is_engine_running()
            mode = self.controller.get_engine_mode()
            status_bar.set_engine_state(running, mode)

            snapshot = self.controller.get_status_snapshot()
            status_bar.update_from_snapshot(snapshot)
        except Exception:
            pass

    def _switch_content(self, screen_name: str) -> None:
        """Switch the main content area to a different screen."""
        self._active_screen_name = screen_name

        # Update nav button styles
        for key, _, _ in NAV_ITEMS:
            try:
                btn = self.query_one(f"#nav-{key}", Button)
                if key == screen_name:
                    btn.add_class("-active")
                else:
                    btn.remove_class("-active")
            except Exception:
                pass

        # Switch the active content
        try:
            switcher = self.query_one("#content-area", ContentSwitcher)
            switcher.current = screen_name
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar navigation button clicks."""
        btn_id = event.button.id or ""
        if btn_id.startswith("nav-"):
            screen_name = btn_id[4:]
            self._switch_content(screen_name)

    def action_show_screen(self, screen_name: str) -> None:
        """Action handler for number key shortcuts."""
        self._switch_content(screen_name)

    def action_toggle_engine(self) -> None:
        """Toggle macro engine start/stop via F5."""
        if self.controller is None:
            return
        if self.controller.is_engine_running():
            self.controller.stop_engine()
            self.notify("Macro stopped", severity="warning")
        else:
            result = self.controller.start_engine()
            if result.get("ok"):
                self.notify("Macro started!")
            else:
                errors = result.get("errors", ["Unknown error"])
                self.notify(f"Failed: {errors[0]}", severity="error")

    def _on_engine_state_change(self, *args) -> None:
        """Callback when engine starts/stops."""
        self._poll_status()

    def _on_mode_change(self, mode: str) -> None:
        """Callback when engine mode changes."""
        self.notify(f"Mode: {mode}")
        self._poll_status()

    def action_quit(self) -> None:
        """Clean shutdown."""
        if self.controller:
            try:
                self.controller.shutdown()
            except Exception:
                pass
        self.exit()
