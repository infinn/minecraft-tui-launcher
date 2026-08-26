import os

from src.Globals import Globals
from .core.version_collection import VersionUtils
from src.utils import hasInternetConnection, check_java_installed, get_java_path


class State:
    LAUNCHER_VERSION = "1.0.0"
    LAUNCHER_NAME = "infinn launcher"

    version_utils: "VersionUtils" = None
    show_snapshots: bool = False
    show_local: bool = False
    version_options: list = []
    selected_version: str = ""

    username: str = ""
    minecraft_dir: str = ""

    java_status: str = "unknown" 
    java_path: str = ""

    internet: bool = False

    operation: str = "idle"
    progress: float = 0.0
    progress_max: float = 0.0

    @classmethod
    def initialize(cls):
        cls.minecraft_dir = Globals.minecraftDir or Globals.defaultMinecraftDir
        cls.username = Globals.lastUsername or Globals.userConfiguration.get("username", "")
        cls.internet = hasInternetConnection()
        cls._check_java()

        cls.version_utils = VersionUtils()
        cls.refresh_versions()

        if not cls.selected_version and Globals.lastVersion:
            cls.selected_version = Globals.lastVersion

    @classmethod
    def refresh_versions(cls):
        if cls.version_utils is None:
            cls.version_options = []
            return

        if cls.show_local:
            versions = cls.version_utils.getInstalledVersions(cls.show_snapshots)
        elif cls.show_snapshots:
            versions = cls.version_utils.getVersionList()
        else:
            versions = cls.version_utils.getReleaseVersions()

        cls.version_options = [(v[0], v[0]) for v in versions]

        if not cls.selected_version and cls.version_options:
            cls.selected_version = cls.version_options[0][1]
        elif cls.selected_version:
            ids = [v[1] for v in cls.version_options]
            if cls.selected_version not in ids:
                cls.selected_version = cls.version_options[0][1] if cls.version_options else ""

    @classmethod
    def set_snapshots(cls, enabled: bool):
        current = cls.selected_version
        cls.show_snapshots = enabled
        cls.refresh_versions()
        if current in [v[1] for v in cls.version_options]:
            cls.selected_version = current

    @classmethod
    def set_local(cls, enabled: bool):
        cls.show_local = enabled
        cls.refresh_versions()

    @classmethod
    def set_username(cls, username: str):
        cls.username = username
        Globals.lastUsername = username
        Globals.save_cache()

    @classmethod
    def set_selected_version(cls, version: str):
        cls.selected_version = version
        Globals.lastVersion = version
        Globals.save_cache()

    @classmethod
    def _check_java(cls):
        if Globals.javaPath and os.path.isfile(Globals.javaPath):
            cls.java_status = "ready"
            cls.java_path = Globals.javaPath
            return
        if check_java_installed():
            cls.java_path = get_java_path()
            Globals.javaPath = cls.java_path
            Globals.save_cache()
            cls.java_status = "ready"
            return
        cls.java_path = ""
        cls.java_status = "missing"

    @classmethod
    def is_busy(cls) -> bool:
        return cls.operation != "idle"
