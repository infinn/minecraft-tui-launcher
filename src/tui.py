import os

import minecraft_launcher_lib
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, CenterMiddle
from textual.widgets import Footer, Label, Input, Select, Switch, Button, Log, ProgressBar

from .core.version_collection import VersionUtils
from src.Globals import Globals
from src.utils import load_configuration, JAVA_DOWNLOAD_URL, play_minecraft
from src.state import State


class TUI(App):
    CSS_PATH = "tui.tcss"

    def __init__(self):
        super().__init__()
        Globals.load_cache()
        Globals.minecraftDir = Globals.minecraftDir or Globals.defaultMinecraftDir
        load_configuration()
        State.initialize()
        self._pulse_timer = None
        self._pulse_progress = 0

    def on_mount(self):
        log = self.query_one("#log", Log)
        self.theme = "gruvbox"
        if not State.internet:
            log.write_line("No internet connection. Some features will be unavailable.")
            self.notify("No internet connection", severity="warning", timeout=8)

        if State.java_status == "missing":
            log.write_line(f"No java installed. Download it from: {JAVA_DOWNLOAD_URL}")
            self.notify("No java installed. Download", severity="error", timeout=10)
        else:
            log.write_line(f"Java detected: {State.java_path or 'PATH'}")

        self._update_operation_state()

    def compose(self) -> ComposeResult:
        yield LauncherHeader()
        yield LauncherStatus()
        yield ActionButtons()
        yield LauncherLog()
        yield Footer()

    # --- Selectors / inputs ---
    def on_select_changed(self, event: Select.Changed):
        if event.value is None or event.value is Select.NULL or event.value is Select.BLANK:
            return
        State.set_selected_version(event.value)

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "username-input":
            State.set_username(event.value.strip())

    def on_switch_changed(self, event: Switch.Changed):
        if event.switch.id == "local-switch":
            State.set_local(event.value)
        else:
            State.set_snapshots(event.value)
        self._refresh_version_select()

    # --- Buttons ---
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "download-button":
            self._start_download()
        elif event.button.id == "launch-button":
            self._start_launch()

    # --- Download ---
    def _start_download(self):
        if State.is_busy():
            return
        version = State.selected_version
        if not version:
            self.notify("Select a version", severity="warning")
            return
        if not State.internet:
            self.notify("No internet connection", severity="error")
            return

        State.operation = "downloading"
        State.progress = 0
        State.progress_max = 0
        self.query_one("#log", Log).write_line(f"Downloading Minecraft {version}...")
        self._update_operation_state()

        def cb_status(status):
            self.call_from_thread(self._set_status, status, status)
            self.call_from_thread(self.query_one("#log", Log).write_line, status)

        def cb_progress(value):
            self.call_from_thread(self._set_progress, value, None)

        def cb_max(value):
            self.call_from_thread(self._set_progress, None, value)

        def worker():
            try:
                minecraft_launcher_lib.install.install_minecraft_version(
                    version,
                    State.minecraft_dir,
                    callback={
                        "setStatus": cb_status,
                        "setProgress": cb_progress,
                        "setMax": cb_max,
                    },
                )
            except Exception as exc:
                self.call_from_thread(self._download_failed, str(exc))
                return
            self.call_from_thread(self._download_done)

        self.run_worker(worker, thread=True)

    def _download_done(self):
        State.operation = "idle"
        State.progress = 0
        State.progress_max = 0
        self.query_one(ProgressBar).update(progress=0, total=1)
        self.query_one("#log", Log).write_line("Download complete.")
        self.notify("Download complete", severity="information")
        State.version_utils.updateVersion()
        State.refresh_versions()
        self._refresh_version_select()
        self._update_operation_state()

    def _download_failed(self, error):
        State.operation = "idle"
        self._stop_pulse()
        self.query_one(ProgressBar).update(progress=0, total=1)
        self.query_one("#status-label", Label).update("[bold $error]download failed[/]")
        self.query_one("#details-label", Label).update(error[:120])
        self.query_one("#log", Log).write_line(f"Download error: {error}")
        self.notify("Download failed", severity="error")
        self._update_buttons()

    # --- Launch ---
    def _start_launch(self):
        if State.is_busy():
            return
        if State.java_status != "ready":
            self.notify("Java unavailable", severity="error")
            return
        version = State.selected_version
        username = self.query_one("#username-input", Input).value.strip() or State.username
        if not version:
            self.notify("Select a version", severity="warning")
            return
        if not username:
            self.notify("Enter a username", severity="warning")
            return

        State.set_username(username)
        State.set_selected_version(version)

        State.operation = "launching"
        self.query_one("#log", Log).write_line(f"Launching Minecraft {version} as {username}...")
        self._update_operation_state()
        self._start_pulse()

        def worker():
            try:
                play_minecraft({"version": version, "user": username})
            except Exception as exc:
                self.call_from_thread(self._launch_failed, str(exc))
                return
            self.call_from_thread(self._launch_done)

        self.run_worker(worker, thread=True)

    def _launch_done(self):
        State.operation = "idle"
        self._stop_pulse()
        self.query_one(ProgressBar).update(progress=0, total=1)
        self.query_one("#log", Log).write_line("Game closed.")
        self._update_operation_state()

    def _launch_failed(self, error):
        State.operation = "idle"
        self._stop_pulse()
        self.query_one(ProgressBar).update(progress=0, total=1)
        self.query_one("#status-label", Label).update("[bold $error]launch failed[/]")
        self.query_one("#details-label", Label).update(error[:120])
        self.query_one("#log", Log).write_line(f"Launch error: {error}")
        self.notify("Could not launch the game", severity="error")
        self._update_buttons()

    # --- UI helpers ---
    def _set_status(self, status, details=None):
        self.query_one("#status-label", Label).update(status)
        if details is not None:
            self.query_one("#details-label", Label).update(details)

    def _set_progress(self, progress, max_):
        if progress is not None:
            State.progress = progress
        if max_ is not None:
            State.progress_max = max_
        bar = self.query_one(ProgressBar)
        if State.progress_max and State.progress_max > 0:
            bar.update(total=State.progress_max, progress=State.progress)
        else:
            bar.update(progress=State.progress)

    def _refresh_version_select(self):
        select = self.query_one("#version-select", Select)
        select.set_options(State.version_options or [("no versions", "none")])
        if State.selected_version and State.selected_version in [v[1] for v in State.version_options]:
            try:
                select.value = State.selected_version
            except Exception:
                pass

    def _update_operation_state(self):
        self._update_buttons()
        self._update_status_labels()

    def _update_buttons(self):
        busy = State.is_busy()
        self.query_one("#download-button", Button).disabled = busy
        self.query_one("#launch-button", Button).disabled = busy or State.java_status != "ready"

    def _update_status_labels(self):
        status = self.query_one("#status-label", Label)
        details = self.query_one("#details-label", Label)
        if State.operation == "downloading":
            status.update("[bold $accent]downloading...[/]")
            details.update("Fetching game files from Mojang...")
        elif State.operation == "launching":
            status.update("[bold $accent]launching...[/]")
            details.update(f"Starting Minecraft {State.selected_version}...")
        elif State.java_status == "ready":
            status.update("[bold $success]ready[/]")
            details.update("Ready to play. Select a version and launch.")
        else:
            status.update("[bold $warning]Missing java[/]")
            details.update("Install Java to enable launching.")

    def _start_pulse(self):
        self._pulse_progress = 0
        self.query_one(ProgressBar).update(total=100, progress=0)
        if self._pulse_timer is None:
            self._pulse_timer = self.set_interval(0.08, self._tick_pulse)

    def _tick_pulse(self):
        self._pulse_progress = (self._pulse_progress + 4) % 100
        self.query_one(ProgressBar).update(total=100, progress=self._pulse_progress)

    def _stop_pulse(self):
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
            self._pulse_timer = None


class LauncherHeader(Vertical):
    def on_mount(self):
        self.border_title = f"{State.LAUNCHER_NAME}  v{State.LAUNCHER_VERSION}"
        self.classes = "box"

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Label("Username", id="text"),
            Input(placeholder="username", id="username-input", compact=True, value=State.username),
        )

        if State.version_options:
            version_value = State.selected_version if State.selected_version in [v[1] for v in State.version_options] else State.version_options[0][1]
            yield Horizontal(
                Label("Version", id="text"),
                Vertical(
                    Select(State.version_options, value=version_value, compact=True, id="version-select"),
                    Horizontal(
                        Label("Snapshots", id="text"),
                        Switch(value=State.show_snapshots, id="snapshot-switch"),
                        classes="switch-row",
                    ),
                    Horizontal(
                        Label("Local", id="text"),
                        Switch(value=State.show_local, id="local-switch"),
                        classes="switch-row",
                    ),
                ),
                classes="version-section"
            )
        else:
            yield Horizontal(
                Label("Version", id="text"),
                Select([("no versions", "none")], value="none", compact=True, id="version-select"),
                classes="version-section"
            )

        yield Horizontal(
            Label("Mc Directory", id="text"),
            Label(State.minecraft_dir, id="mc-dir-label"),
        )


class LauncherStatus(Vertical):
    def on_mount(self):
        self.classes = "box"
        self.id = "launcher-status"

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
    def on_mount(self):
        self.id = "buttons-secction"

    def compose(self) -> ComposeResult:
        yield CenterMiddle(Button("Download", id="download-button"))
        yield CenterMiddle(Button("Launch", id="launch-button", disabled=True))


class LauncherLog(Vertical):
    def on_mount(self):
        self.border_title = "log"
        self.classes = "box"
        self.id = "log-section"

    def compose(self) -> ComposeResult:
        yield Log(id="log", auto_scroll=True)
