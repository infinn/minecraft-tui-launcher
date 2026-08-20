import os
import json
import getpass

class Globals:
    programDir = os.path.dirname(os.path.abspath(__file__))
    minecraftDir = ""
    defaultMinecraftDir = f"C://Users//{getpass.getuser()}//AppData//Roaming//.minecraft"
    firstLaunch = True
    cacheFile = os.path.join(programDir, "cache.json")
    userConfiguration = {}
    latestVersionUsage = ""