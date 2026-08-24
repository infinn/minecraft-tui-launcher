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


def get_parse_version(versionList):
    parse_list = []
    for version in versionList:
        parse_list.append(version["id"] + f' ({version["type"]})')
    return parse_list


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


def check_java_installed():
    java_path = minecraft_launcher_lib.utils.get_java_executable()
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


def get_java_path():
    java_path = minecraft_launcher_lib.utils.get_java_executable()
    if java_path and os.path.isfile(java_path):
        return java_path

    which_path = shutil.which("java")
    if which_path:
        return which_path

    return ""
