import json
import os
import minecraft_launcher_lib
import subprocess
import socket

from src.config import VERSION_LAUNCHER
from src.Globals import Globals

class MineManager:
    def __init__(self, user):
        self.MINECRAFT_DIRECTORY = f"C://Users//{user}//AppData//Roaming//.minecraft"
        self.SRC_JSON = f"{self.MINECRAFT_DIRECTORY}//configuration.json"

        self.configuration = {}

        self._ensure_file()
        
        self.callback = {}
    
    def _ensure_file(self):
        if not os.path.isfile(self.SRC_JSON):
            self._create_default_file()
        else:
            with open(self.SRC_JSON, "r", encoding="utf-8") as f:
                try:
                    self.configuration = json.load(f)
                except json.JSONDecodeError:
                    self._create_default_file()

    def _create_default_file(self):
        default_data = {
            "username": "",
            "uuid": "",
            "token": "",

            "executablePath": "java",
            "defaultExecutablePath": "java",
            "jvmArguments": [],
            "launcherName": "infinn-launcher",
            "launcherVersion": VERSION_LAUNCHER,
            "gameDirectory": self.MINECRAFT_DIRECTORY,
            "demo": False,
            "customResolution": False,
            "resolutionWidth": "854",
            "resolutionHeight": "480"
        }
        with open(self.SRC_JSON, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
        self.configuration = default_data
    
    def get_version(self, only_local=True, only_released=True):
        local_version = []
        mojang_version = []

        mine_version_local = minecraft_launcher_lib.utils.get_installed_versions(self.MINECRAFT_DIRECTORY)

        for version in mine_version_local:
            if only_released and version["type"] != "release":
                continue
            local_version.append(version["id"] + f' ({version["type"]}) [local]')

        if not only_local:
            version_list = minecraft_launcher_lib.utils.get_version_list()
            for version in version_list:
                if only_released and version["type"] != "release":
                    continue
                mojang_version.append(version["id"] + f' ({version["type"]})')

        return local_version if only_local else local_version + mojang_version
    
    def set_minecrat_directory(self, path):
        self.MINECRAFT_DIRECTORY = path
        self.SRC_JSON = f"{self.MINECRAFT_DIRECTORY}//configuration.json"

    async def install_minecraft(self, version):
        minecraft_launcher_lib.install.install_minecraft_version(
            version,
            self.MINECRAFT_DIRECTORY,
            callback={
                "setStatus": self.callback["setStatus"],
                "setProgress": self.callback["setProgress"],
                "setMax": self.callback["setMax"],
            }
        )

def load_configuration():
    _ensureMinecraftDirectoryExists()
    _ensure_configuration_file()

    pass

def _ensure_configuration_file():
    json_path = f"{Globals.minecraftDir}//configuration.json"

    if not os.path.isfile(json_path):
        _create_default_file()
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                Globals.userConfiguration = json.load(f)
            except json.JSONDecodeError:
                _create_default_file()


def _create_default_file():
    json_path = f"{Globals.minecraftDir}//configuration.json"
    default_data = {
        "username": "",
        "uuid": "",
        "token": "",

        "executablePath": "java",
        "defaultExecutablePath": "java",
        "jvmArguments": [],
        "launcherName": "infinn-launcher",
        "launcherVersion": VERSION_LAUNCHER,
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
    return(parse_list)

def update_cache(minecraft_dir, latest_version_usage):
    data = {
        "minecraftDir": minecraft_dir,
        "latestVersionUsage": latest_version_usage
    }

    try:
        with open(Globals.cacheFile, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
    except Exception as e:
            print("Error al guardar el cache:", e)

def play_minecraft(config):
    update_cache(Globals.minecraftDir, config["version"])

    options = {
        'username': config["user"],
        'uuid': '',
        'token': '',
            
        "launcherName": "infinn-launcher",
        "launcherVersion": VERSION_LAUNCHER,
    }

    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(config["version"], Globals.minecraftDir, options)
    subprocess.run(minecraft_command)

def hasInternetConnection():
    try:
        socket.create_connection(("api.mojang.com", 80))
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
    
