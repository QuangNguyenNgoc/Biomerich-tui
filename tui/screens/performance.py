"""Performance screen — throttle, RAM trim, benchmark."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll
from textual.widgets import Static, Button, Switch, Input, Label, ProgressBar
from textual.containers import Vertical, Horizontal

from rich.panel import Panel
from rich.table import Table


class PerformanceScreen(VerticalScroll):
    """Performance management: throttle, RAM trim, benchmark."""

    DEFAULT_CSS = """
    PerformanceScreen {
        padding: 1;
        overflow-y: auto;
    }

    .perf-section {
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        # Throttle section
        with Vertical(classes="perf-section"):
            yield Label("[bold]Process Throttling[/bold]")
            with Horizontal():
                yield Label("Enabled:", classes="setting-label")
                yield Switch(value=False, id="sw-throttle")
            yield Static(id="throttle-status")

        # RAM Trim section
        with Vertical(classes="perf-section"):
            yield Label("[bold]RAM Trim[/bold]")
            with Horizontal():
                yield Label("Enabled:", classes="setting-label")
                yield Switch(value=False, id="sw-ram-trim")
            with Horizontal():
                yield Button("Trim Now", variant="primary", id="btn-trim-now")
            yield Static(id="ram-status")

        # Benchmark section
        with Vertical(classes="perf-section"):
            yield Label("[bold]Performance Benchmark[/bold]")
            yield Label(
                "[dim]Compares CPU/RAM usage: unthrottled vs throttled (60s each)[/dim]"
            )
            with Horizontal():
                yield Button("Start Benchmark", variant="success", id="btn-bench-start")
                yield Button("Stop", variant="error", id="btn-bench-stop")
            yield Static(id="bench-status")

        # Live metrics
        yield Static(id="live-metrics")

    def on_mount(self) -> None:
        self._refresh_all()
        self.set_interval(2.0, self._refresh_metrics)

    def _refresh_all(self) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return
        settings = ctrl.get_settings()
        try:
            self.query_one("#sw-throttle", Switch).value = settings.get(
                "throttleEnabled", False
            )
            self.query_one("#sw-ram-trim", Switch).value = settings.get(
                "ramTrimEnabled", False
            )
        except Exception:
            pass
        self._refresh_metrics()

    def _refresh_metrics(self) -> None:
        """Refresh live performance metrics."""
        ctrl = self.app.controller
        if ctrl is None:
            return

        try:
            perf_data = ctrl.get_performance()
            table = Table(title="Roblox Instances", expand=True)
            table.add_column("Account", style="cyan")
            table.add_column("PID", style="dim")
            table.add_column("CPU %", style="yellow")
            table.add_column("RAM (MB)", style="magenta")

            for instance in perf_data.get("roblox", []):
                table.add_row(
                    instance.get("account", "?"),
                    str(instance.get("pid", "?")),
                    f"{instance.get('cpu', 0):.1f}%",
                    f"{instance.get('ramMb', 0):.0f}",
                )

            self.query_one("#live-metrics", Static).update(
                Panel(table, title="[bold]Live Metrics[/bold]", border_style="green")
            )
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        ctrl = self.app.controller
        if ctrl is None:
            return

        if event.button.id == "btn-trim-now":
            result = ctrl.trim_ram_now()
            freed = result.get("freedMb", 0)
            self.notify(f"Freed {freed:.0f} MB RAM")

        elif event.button.id == "btn-bench-start":
            ctrl.start_benchmark()
            self.notify("Benchmark started (120s total)...")

        elif event.button.id == "btn-bench-stop":
            ctrl.stop_benchmark()
            self.notify("Benchmark stopped")
