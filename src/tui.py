import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, CenterMiddle 
from textual.widgets import Footer, Label, Input, Select, Switch, Static, Button, Rule, Log, ProgressBar 
from .core.version_collection import VersionUtils
from src.Globals import Globals

class TUI(App):
    CSS_PATH = "tui.tcss"
    def compose(self) -> ComposeResult:
        version_list = VersionUtils().getReleaseVersions()
        header_box = Vertical(
            Horizontal(
                Label("Username"),
                Input(placeholder="username", compact=True),
            ),
            Horizontal(
                Label("Version"),
                Select(
                    version_list,
                    compact=True
                ),
            ),
            Horizontal(
                Label("Mc Directory"),
                Label(Globals.defaultMinecraftDir),
            ),
            classes="box"
        )
        status_box = Vertical(
            Horizontal(
                Label("Status"),
                Label("Loading..."),
            ),
            Horizontal(
                Label("Details"),
                Label(""),
            ),
            ProgressBar(show_percentage=False, show_eta=False),
            classes="box"
        )

        header_box.border_title = "infinn launcher"

        yield header_box
        yield status_box
        yield Horizontal(
            CenterMiddle(
                Button("Download"),
            ),
            CenterMiddle(
                Button("Launch"),
            ),
        )
        log_box = Vertical(
            Log(),
            classes="box"
        )
        log_box.border_title = "log"
        yield log_box

        yield Footer()