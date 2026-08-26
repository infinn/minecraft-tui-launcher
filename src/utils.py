import json
import os
import shutil
import minecraft_launcher_lib
import subprocess
import socket

from src.Globals import Globals

JAVA_DOWNLOAD_URL = "https://www.java.com/"


def load_configuration():
    _ensureMinecraftDirectoryExists()
    _ensure_configuration_file()


def _ensure_configuration_file():
    json_path = os.path.join(Globals.minecraftDir, "configuration-launcher.json")

    if not os.path.isfile(json_path):
        _create_default_file()
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                Globals.userConfiguration = json.load(f)
            except json.JSONDecodeError:
                _create_default_file()


def _create_default_file():
    json_path = os.path.join(Globals.minecraftDir, "configuration-launcher.json")
    default_data = {
        "username": "",
        "uuid": "",
        "token": "",

        "executablePath": "java",
        "defaultExecutablePath": "java",
        "jvmArguments": [],
        "launcherName": "infinn-launcher",
        "launcherVersion": "1.0",
        "gameDirectory": Globals.minecraftDir,
        "demo": False,
        "customResolution": False,
        "resolutionWidth": "854",
        "resolutionHeight": "480"
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(default_data, f, indent=4, ensure_ascii=False)


def _ensureMinecraftDirectoryExists():
    if os.path.isdir(Globals.minecraftDir):
        return

    try:
        os.makedirs(Globals.minecraftDir)
    except Exception:
        Globals.minecraftDir = Globals.defaultMinecraftDir
        _ensureMinecraftDirectoryExists()


def update_cache(minecraft_dir, latest_version_usage):
    Globals.minecraftDir = minecraft_dir
    Globals.lastVersion = latest_version_usage
    Globals.save_cache()


def play_minecraft(config):
    update_cache(Globals.minecraftDir, config["version"])
    Globals.lastUsername = config["user"]
    Globals.save_cache()

    options = {
        'username': config["user"],
        'uuid': '',
        'token': '',

        "launcherName": "infinn-launcher",
        "launcherVersion": "1.0",
    }

    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
        config["version"], Globals.minecraftDir, options
    )
    subprocess.run(minecraft_command)


def hasInternetConnection():
    try:
        socket.create_connection(("api.mojang.com", 80), timeout=5)
        return True
    except OSError:
        return False


def _find_java_in_registry():
    if os.name != "nt":
        return ""
    try:
        import winreg
    except ImportError:
        return ""

    keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Runtime Environment"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Development Kit"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JRE"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AdoptOpenJDK\JRE"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AdoptOpenJDK\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Azul Systems\Zulu"),
    ]
    for hkey, subkey in keys:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                java_home = winreg.QueryValueEx(key, "JavaHome")[0]
                exe = os.path.join(java_home, "bin", "javaw.exe")
                if os.path.isfile(exe):
                    return exe
                exe = os.path.join(java_home, "bin", "java.exe")
                if os.path.isfile(exe):
                    return exe
        except OSError:
            continue

    return ""


def _find_java_in_known_paths():
    if os.name == "nt":
        roots = [
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
        ]
        exe_names = ["javaw.exe", "java.exe"]
    else:
        roots = ["/usr/lib/jvm", "/opt"]
        exe_names = ["java"]

    candidates = []
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _, _ in os.walk(root):
            for name in exe_names:
                exe = os.path.join(dirpath, name)
                if os.path.isfile(exe):
                    candidates.append(exe)

    if not candidates:
        return ""

    def _major_sort_key(path):
        parts = path.lower().split(os.sep)
        for part in parts:
            if "jdk" in part or "jre" in part:
                digits = "".join(ch for ch in part if ch.isdigit())
                if digits:
                    return int(digits)
        return 0

    return sorted(candidates, key=_major_sort_key, reverse=True)[0]


def get_java_path():
    java_path = minecraft_launcher_lib.utils.get_java_executable()
    if java_path and os.path.isfile(java_path):
        return java_path

    which_path = shutil.which("java") or shutil.which("javaw")
    if which_path:
        return which_path

    registry_path = _find_java_in_registry()
    if registry_path:
        return registry_path

    known_path = _find_java_in_known_paths()
    if known_path:
        return known_path

    return ""


def check_java_installed():
    java_path = get_java_path()
    if java_path and os.path.isfile(java_path):
        return True
    try:
        result = subprocess.run(
            ["java", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
