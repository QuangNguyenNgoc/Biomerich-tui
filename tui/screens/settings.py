"""Settings screen — grouped settings editor."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, Switch, Input, Select, Label, Button
from textual.containers import Vertical, Horizontal

from rich.panel import Panel

# Setting definitions: (key, label, type, default, options/range)
SETTING_GROUPS = {
    "General": [
        ("hotkey", "Macro Hotkey", "str", "F5"),
        ("modeHotkey", "Mode Toggle Hotkey", "str", "none"),
    ],
    "Anti-AFK": [
        ("antiAfkEnabled", "Enable Anti-AFK", "bool", True),
        ("antiAfkStandalone", "Run when engine stopped", "bool", False),
        ("antiAfkInterval", "Interval (seconds)", "int", 300),
        ("antiAfkAction", "Action", "select", "space", ["space", "zoom"]),
    ],
    "Notifications": [
        ("windowsNotificationsEnabled", "Windows Tray Notifications", "bool", True),
        ("biomeLogging", "Log Biome Events", "bool", True),
    ],
    "Clipping": [
        ("clippingEnabled", "Enable Auto Clipping", "bool", False),
        ("clipHotkey", "Clip Hotkey", "str", ""),
        ("clipBiomeDelay", "Biome Clip Delay (sec)", "int", 3),
        ("clipAuraMinimumRarity", "Min Aura Rarity", "int", 0),
    ],
    "Safety": [
        ("fakePingGuard", "Anti-Fake Rare Ping", "bool", True),
        ("fakePingPrompt", "Prompt on Fake Ping", "bool", True),
        ("biomeHealthMonitorEnabled", "Biome Health Monitor", "bool", True),
        ("biomeHealthTimeoutMinutes", "Health Timeout (min)", "int", 30),
    ],
    "Display": [
        ("monitorDimEnabled", "Monitor Dim", "bool", False),
        ("monitorDimLevel", "Dim Level (0-80%)", "int", 40),
    ],
}


class SettingsScreen(VerticalScroll):
    """Grouped settings view with toggles and inputs."""

    DEFAULT_CSS = """
    SettingsScreen {
        padding: 1;
        overflow-y: auto;
    }

    .settings-group {
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }

    .setting-row {
        height: 3;
        padding: 0 1;
    }

    .setting-label {
        width: 40;
    }
    """

    def compose(self) -> ComposeResult:
        for group_name, settings in SETTING_GROUPS.items():
            with Vertical(classes="settings-group"):
                yield Label(f"[bold]{group_name}[/bold]")
                for key, label, stype, default, *extra in settings:
                    with Horizontal(classes="setting-row"):
                        yield Label(label, classes="setting-label")
                        if stype == "bool":
                            yield Switch(value=default, id=f"sw-{key}")
                        elif stype == "int":
                            yield Input(
                                str(default),
                                type="integer",
                                id=f"in-{key}",
                            )
                        elif stype == "str":
                            yield Input(str(default), id=f"in-{key}")
                        elif stype == "select" and extra:
                            options = [(opt, opt) for opt in extra[0]]
                            yield Select(
                                options,
                                value=default,
                                id=f"sel-{key}",
                            )

        with Horizontal():
            yield Button("Save", variant="success", id="btn-save")
            yield Button("Reset", variant="warning", id="btn-reset")

    def on_mount(self) -> None:
        self._load_settings()

    def _load_settings(self) -> None:
        """Load current settings from controller into widgets."""
        ctrl = self.app.controller
        if ctrl is None:
            return
        settings = ctrl.get_settings()

        for _group_name, group_settings in SETTING_GROUPS.items():
            for key, _label, stype, default, *_extra in group_settings:
                value = settings.get(key, default)
                try:
                    if stype == "bool":
                        self.query_one(f"#sw-{key}", Switch).value = bool(value)
                    elif stype in ("int", "str"):
                        self.query_one(f"#in-{key}", Input).value = str(value)
                    elif stype == "select":
                        self.query_one(f"#sel-{key}", Select).value = value
                except Exception:
                    pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._save_settings()
        elif event.button.id == "btn-reset":
            self._load_settings()
            self.notify("Settings reset to saved values")

    def _save_settings(self) -> None:
        """Collect widget values and push to controller."""
        ctrl = self.app.controller
        if ctrl is None:
            return

        for _group_name, group_settings in SETTING_GROUPS.items():
            for key, _label, stype, _default, *_extra in group_settings:
                try:
                    if stype == "bool":
                        value = self.query_one(f"#sw-{key}", Switch).value
                    elif stype == "int":
                        value = int(self.query_one(f"#in-{key}", Input).value)
                    elif stype == "str":
                        value = self.query_one(f"#in-{key}", Input).value
                    elif stype == "select":
                        value = self.query_one(f"#sel-{key}", Select).value
                    else:
                        continue
                    ctrl.set_setting(key, value)
                except Exception:
                    pass

        ctrl.save_config()
        self.notify("Settings saved!", severity="information")
