"""About / Credits screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.widgets import Label, Button, Static

from core import creator


class AboutScreen(VerticalScroll):
    """Credits, author info, and external links."""

    DEFAULT_CSS = """
    AboutScreen {
        padding: 2 4;
        align: center middle;
    }

    #about-container {
        width: 80;
        height: auto;
        border: thick $primary;
        padding: 2 4;
        background: $surface;
    }

    .about-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
    }

    .about-section {
        margin-bottom: 1;
    }

    .link-row {
        align: center middle;
        margin-top: 1;
        margin-bottom: 2;
    }

    .btn-link {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        links = creator.links()
        with Vertical(id="about-container"):
            yield Label(
                "[bold cyan]Biomerich (Fork)[/bold cyan]", classes="about-header"
            )

            yield Label(
                "A Terminal UI overhaul and fork of the SolRich project.",
                classes="about-section",
            )
            yield Label(
                "Maintained by [bold]QuangNguyenNgoc[/bold].", classes="about-section"
            )

            with Horizontal(classes="link-row"):
                yield Button(
                    "GitHub (Fork)",
                    id="btn-gh-fork",
                    variant="primary",
                    classes="btn-link",
                )

            yield Label(
                "[bold magenta]Original Project: SolRich[/bold magenta]",
                classes="about-header",
            )
            yield Label(
                f"Created by [bold]{links.get('name', 'Finnerich')}[/bold]",
                classes="about-section",
            )

            with Horizontal(classes="link-row"):
                yield Button(
                    "Original Discord",
                    id="btn-discord",
                    variant="default",
                    classes="btn-link",
                )
                yield Button(
                    "Original YouTube",
                    id="btn-youtube",
                    variant="error",
                    classes="btn-link",
                )

            yield Label("Notes:", classes="about-section")
            yield Label(
                f"[italic]{links.get('notes', '')}[/italic]", classes="about-section"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        ctrl = self.app.controller
        if not ctrl:
            return

        links = creator.links()

        if event.button.id == "btn-gh-fork":
            ctrl.open_url("https://github.com/QuangNguyenNgoc/Biomerich-tui")
        elif event.button.id == "btn-discord":
            ctrl.open_url(links.get("discord", ""))
        elif event.button.id == "btn-youtube":
            ctrl.open_url(links.get("youtube", ""))
