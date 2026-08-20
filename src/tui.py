import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, CenterMiddle 
from textual.widgets import Footer, Label, Input, Select, Switch, Static, Button, Rule, Log, ProgressBar 
from .core.version_collection import VersionUtils
from src.Globals import Globals
from src.utils import load_configuration, check_java_installed, get_java_path, JAVA_DOWNLOAD_URL

class TUI(App):
    CSS_PATH = "tui.tcss"

    def on_mount(self):
        Globals.load_cache()
        Globals.minecraftDir = Globals.minecraftDir or Globals.defaultMinecraftDir
        load_configuration()
        
        self._check_java()
    
    def compose(self) -> ComposeResult:
        yield LauncherHeader()
        yield LauncherStatus()
        yield ActionButtons()
        yield LauncherLog()
        yield Footer()

    def _check_java(self):
        status_label = self.query_one("#status-label", Label)
        details_label = self.query_one("#details-label", Label)
        log_widget = self.query_one("#log", Log)
        launch_button = self.query_one("#launch-button", Button)

        if Globals.javaPath and os.path.isfile(Globals.javaPath):
            launch_button.disabled = False
            status_label.update("[bold $success]ready[/]")
            details_label.update(f"java: {Globals.javaPath}")
            log_widget.write(f"Java cargado desde cache: {Globals.javaPath}")
            return

        if check_java_installed():
            Globals.javaPath = get_java_path()
            Globals.save_cache()
            launch_button.disabled = False
            status_label.update("[bold $success]ready[/]")
            details_label.update(f"java: {Globals.javaPath or 'PATH'}")
            log_widget.write(f"Java detectado: {Globals.javaPath or 'PATH'}")
            return

        Globals.javaPath = ""
        launch_button.disabled = True
        status_label.update("[bold $warning]Missing java[/]")
        details_label.update("[bold $error]No java installed[/]")
        log_widget.write(f"No java installed. Download it from: {JAVA_DOWNLOAD_URL}")
        self.notify("No java installed. Download", severity="error", timeout=10)

class LauncherHeader(Vertical):
    def on_mount(self):
        self.border_title = "infinn launcher"
        self.classes = "box"

    def compose(self) -> ComposeResult:
        version_list = VersionUtils().getReleaseVersions()
        username_value = Globals.lastUsername or Globals.userConfiguration.get("username", "")
        
        yield Horizontal(
            Label("Username", id="text"),
            Input(placeholder="username", compact=True, value=username_value),
        )
        yield Horizontal(
            Label("Version", id="text"),
            Select(version_list, compact=True),
        )
        yield Horizontal(
            Label("Mc Directory", id="text"),
            Label(Globals.minecraftDir),
        )

class LauncherStatus(Vertical):
    def on_mount(self):
        self.classes = "box"

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Label("Status", id="text"),
            Label("Loading...", id="status-label"),
        )
        yield Horizontal(
            Label("Details", id="text"),
            Label("", id="details-label"),
        )
        yield ProgressBar(show_percentage=False, show_eta=False)

class ActionButtons(Horizontal):
    def compose(self) -> ComposeResult:
        yield CenterMiddle(Button("Download", id="download-button"))
        yield CenterMiddle(Button("Launch", id="launch-button", disabled=True))

class LauncherLog(Vertical):
    def on_mount(self):
        self.border_title = "log"
        self.classes = "box"

    def compose(self) -> ComposeResult:
        yield Log(id="log", auto_scroll = True)