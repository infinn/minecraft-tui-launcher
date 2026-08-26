import os
import json
import getpass

class Globals:
    programDir = os.path.dirname(os.path.abspath(__file__))

    if os.name == "nt":
        _home = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        _home = os.path.expanduser("~")
    defaultMinecraftDir = os.path.join(_home, ".minecraft")

    minecraftDir = ""
    firstLaunch = True
    cacheFile = os.path.join(programDir, "cache.json")
    userConfiguration = {}
    latestVersionUsage = ""

    lastUsername = ""
    lastVersion = ""
    javaPath = ""
    windowWidth = 80
    windowHeight = 24
    lastProfile = ""
    profiles = []

    @classmethod
    def load_cache(cls):
        if not os.path.isfile(cls.cacheFile):
            cls._create_default_cache()
            return

        try:
            with open(cls.cacheFile, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            cls._create_default_cache()
            return

        cls.minecraftDir = data.get("minecraftDir", cls.defaultMinecraftDir)
        cls.lastVersion = data.get("lastVersion", "")
        cls.lastUsername = data.get("lastUsername", "")
        cls.javaPath = data.get("javaPath", "")
        cls.windowWidth = data.get("windowWidth", 80)
        cls.windowHeight = data.get("windowHeight", 24)
        cls.lastProfile = data.get("lastProfile", "")
        cls.profiles = data.get("profiles", [])
        cls.firstLaunch = False

    @classmethod
    def save_cache(cls):
        data = {
            "minecraftDir": cls.minecraftDir,
            "lastVersion": cls.lastVersion,
            "lastUsername": cls.lastUsername,
            "javaPath": cls.javaPath,
            "windowWidth": cls.windowWidth,
            "windowHeight": cls.windowHeight,
            "lastProfile": cls.lastProfile,
            "profiles": cls.profiles,
        }
        try:
            with open(cls.cacheFile, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except OSError as e:
            print("Error saving cache:", e)

    @classmethod
    def _create_default_cache(cls):
        cls.minecraftDir = cls.defaultMinecraftDir
        cls.lastVersion = ""
        cls.lastUsername = ""
        cls.javaPath = ""
        cls.windowWidth = 80
        cls.windowHeight = 24
        cls.lastProfile = ""
        cls.profiles = []
        cls.save_cache()