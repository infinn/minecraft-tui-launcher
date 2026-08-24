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

    def on_mount(self):
        log = self.query_one("#log", Log)

        if not State.internet:
            log.write("Sin conexion a internet. Algunas funciones no estaran disponibles.")
            self.notify("Sin conexion a internet", severity="warning", timeout=8)

        if State.java_status == "missing":
            log.write(f"No java installed. Download it from: {JAVA_DOWNLOAD_URL}")
            self.notify("No java installed. Download", severity="error", timeout=10)
        else:
            log.write(f"Java detectado: {State.java_path or 'PATH'}")

        self._update_operation_state()

    def compose(self) -> ComposeResult:
        yield LauncherHeader()
        yield LauncherStatus()
        yield ActionButtons()
        yield LauncherLog()
        yield Footer()

    # --- Selectores / inputs ---
    def on_select_changed(self, event: Select.Changed):
        if event.value is None or event.value is Select.NULL or event.value is Select.BLANK:
            return
        State.set_selected_version(event.value)

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "username-input":
            State.set_username(event.value.strip())

    def on_switch_changed(self, event: Switch.Changed):
        State.set_snapshots(event.value)
        self._refresh_version_select()

    # --- Botones ---
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "download-button":
            self._start_download()
        elif event.button.id == "launch-button":
            self._start_launch()

    # --- Descarga ---
    def _start_download(self):
        if State.is_busy():
            return
        version = State.selected_version
        if not version:
            self.notify("Selecciona una version", severity="warning")
            return
        if not State.internet:
            self.notify("No hay conexion a internet", severity="error")
            return

        State.operation = "downloading"
        State.progress = 0
        State.progress_max = 0
        self.query_one("#log", Log).write_line(f"Descargando Minecraft {version}...")
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
        self.query_one("#log", Log).write("Descarga completada.")
        self.notify("Descarga completada", severity="information")
        State.version_utils.updateVersion()
        State.refresh_versions()
        self._refresh_version_select()
        self._update_operation_state()

    def _download_failed(self, error):
        State.operation = "idle"
        self.query_one("#status-label", Label).update("[bold $error]download failed[/]")
        self.query_one("#details-label", Label).update(error[:120])
        self.query_one("#log", Log).write(f"Error de descarga: {error}")
        self.notify("Descarga fallida", severity="error")
        self._update_operation_state()

    # --- Lanzamiento ---
    def _start_launch(self):
        if State.is_busy():
            return
        if State.java_status != "ready":
            self.notify("Java no disponible", severity="error")
            return
        version = State.selected_version
        username = self.query_one("#username-input", Input).value.strip() or State.username
        if not version:
            self.notify("Selecciona una version", severity="warning")
            return
        if not username:
            self.notify("Ingresa un nombre de usuario", severity="warning")
            return

        State.set_username(username)
        State.set_selected_version(version)

        State.operation = "launching"
        self.query_one("#log", Log).write(f"Lanzando Minecraft {version} como {username}...")
        self._update_operation_state()

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
        self.query_one("#log", Log).write("Juego cerrado.")
        self._update_operation_state()

    def _launch_failed(self, error):
        State.operation = "idle"
        self.query_one("#status-label", Label).update("[bold $error]launch failed[/]")
        self.query_one("#details-label", Label).update(error[:120])
        self.query_one("#log", Log).write(f"Error al lanzar: {error}")
        self.notify("No se pudo lanzar el juego", severity="error")
        self._update_operation_state()

    # --- Helpers de UI ---
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
        busy = State.is_busy()
        self.query_one("#download-button", Button).disabled = busy
        self.query_one("#launch-button", Button).disabled = busy or State.java_status != "ready"

        status = self.query_one("#status-label", Label)
        if State.operation == "downloading":
            status.update("[bold $accent]downloading...[/]")
        elif State.operation == "launching":
            status.update("[bold $accent]launching...[/]")
        elif State.java_status == "ready":
            status.update("[bold $success]ready[/]")
        else:
            status.update("[bold $warning]Missing java[/]")


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
                Select(State.version_options, value=version_value, compact=True, id="version-select"),
            )
        else:
            yield Horizontal(
                Label("Version", id="text"),
                Select([("no versions", "none")], value="none", compact=True, id="version-select"),
            )

        yield Horizontal(
            Label("Mc Directory", id="text"),
            Label(State.minecraft_dir, id="mc-dir-label"),
        )
        yield Horizontal(
            Label("Snapshots", id="text"),
            Switch(value=State.show_snapshots, id="snapshot-switch"),
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
    def on_mount(self):
        self.id = "buttons-secction"

    def compose(self) -> ComposeResult:
        yield CenterMiddle(Button("Download", id="download-button"))
        yield CenterMiddle(Button("Launch", id="launch-button", disabled=True))


class LauncherLog(Vertical):
    def on_mount(self):
        self.border_title = "log"
        self.classes = "box"

    def compose(self) -> ComposeResult:
        yield Log(id="log", auto_scroll=True)
