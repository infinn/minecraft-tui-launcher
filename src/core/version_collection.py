import requests
import json
import os

from src.Globals import Globals


class VersionUtils:

    def __init__(self):

        self._installedVersions: dict[str] = {}
        self._vanillaVersions: dict[str] = {}
        self._versions: dict[str] = {}
        self._latestSnapshot = ""
        self._latestRelease = ""

        self._load_vanilla_version()
        self.updateVersion()

    def _load_vanilla_version(self):
        _version_data = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json").json()
        
        self._latestRelease = _version_data["latest"]["release"]
        self._latestSnapshot = _version_data["latest"]["snapshot"]

        for currentVersion in _version_data["versions"]:
            self._vanillaVersions[currentVersion["id"]] = {
                "id": currentVersion["id"],
                "type": currentVersion["type"],
            }
        
    def updateVersion(self):
        _installed_version = {}
        _versions = {}

        # copy vanilla version
        for key, value in self._vanillaVersions.items():
            _versions[key] = value

        # check version files 
        if not os.path.isdir(os.path.join(Globals.minecraftDir, "versions")):
            self._versions = _versions
            return
        
        # check versions
        for currentVersion in os.listdir(os.path.join(Globals.minecraftDir, "versions")):
            jsonPath = os.path.join(Globals.minecraftDir, "versions", currentVersion, f"{currentVersion}.json")

            if not os.path.isfile(jsonPath):
                continue

            with open(jsonPath, "r", encoding="utf-8") as f:
                try:
                    versionInfo = json.load(f)
                except json.decoder.JSONDecodeError as e:
                    print(f"Error while parsing {jsonPath}: {e.args[0]}")
                    continue

            _installed_version[versionInfo["id"]] = {
                "id": versionInfo["id"],
                "type": versionInfo["type"],
            }

        for key, value in _installed_version.items():
            _versions[key] = value

        self._installedVersions = _installed_version
        self._versions = _versions

    def getVersionList(self):
        return list(self._versions.values())

    def getInstalledVersions(self):
        return list(self._installedVersions.values())

    def getLatestRelease(self):
        return self._latestRelease

    def getLatestSnapshot(self):
        return self._latestSnapshot
