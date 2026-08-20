import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, CenterMiddle 
from textual.widgets import Footer, Label, Input, Select, Switch, Static, Button, Rule, Log, ProgressBar 

class TUI(App):
    CSS_PATH = "tui.tcss"
    def compose(self) -> ComposeResult:
        header_box = Vertical(
            Horizontal(
                Label("Username"),
                Input(placeholder="username", compact=True),
            ),
            Horizontal(
                Label("Version"),
                Select(
                    [("First", 1), ("Second", 2)],
                    compact=True
                ),
            ),
            Horizontal(
                Label("Mc Directory"),
                Label(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
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