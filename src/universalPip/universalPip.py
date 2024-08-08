import requests
import sys
import os
import subprocess
from delocate.fuse import fuse_wheels
import regex

class PkgManager():
    def __init__(self, packageName : str) -> None:
        self.allDependencies : list[str] = []
        self.packageInfo : dict = {}
        self.extras : list[str] = []
        self.closest : bool = None
        self.distributions : list[dict] = []
        if not os.path.exists("wheels"):
            os.mkdir("wheels")
        [baseName, extras] = self.processPackageName(packageName)
        if self.checkExistingPackage(baseName):
            self.packageName : str = baseName
            self.extras = extras
        else:
            raise Exception(f"Package {packageName} does not exist on PyPi.")
        self.targetPyVersion : int = int(f"{sys.version_info.major}{sys.version_info.minor}")

    def processPackageName(self, packageName : str):
        if packageName.find("[") != -1:
            baseName = packageName.split("[")[0]
            extras = packageName.split(baseName)[1]
            formattedExtras : list[str] = extras[1:-1].split(",")
            toRemove : list[str] = []
            for extra in formattedExtras:
                if extra.strip().isalnum():
                    formattedExtras[formattedExtras.index(extra)] = extra.strip()
                else:
                    toRemove.append(extra)
            for extra in toRemove:
                formattedExtras.remove(extra)
            return baseName, formattedExtras
        return packageName, []

    def checkExistingPackage(self, pkgName : str) -> bool:
        url = f"https://pypi.org/pypi/{pkgName}/json"
        response = requests.get(url)
        try:
            if response.json()["message"] == "Not Found":
                return False
        except KeyError:
            self.packageInfo = response.json()
            req = requests.get(f"https://pypi.org/simple/{pkgName}/", headers={"Accept": "application/vnd.pypi.simple.v1+json"})
            js = req.json()
            self.packageInfo["releases"] = js["files"]
            self.packageInfo["versions"] = js["versions"]
            return True
        
    def getAvailableDistributionsForRelease(self, release : str):
        releases : dict = self.packageInfo["releases"]
        if release not in self.packageInfo["versions"]:
            raise Exception(f"Release {release} does not exists for package {self.packageName}")
        distributions : list[str] = []
        for distribution in releases:
            if distribution["filename"].find(release) != -1 and distribution["filename"].find(f"cp{self.targetPyVersion}") != -1:
                distributions.append(distribution)

        if len(distributions) == 0:
            print(f"No matching distribution found for Python {self.targetPyVersion} and release {release}. Trying to get the closest distribution available...")
        else:
            self.distributions = distributions
            return False
        A = releases
        for dist in releases:
            if dist["filename"].find("macosx") == -1 or dist["filename"].find(release) == -1:
                A.remove(dist)
        reg = regex.compile("-cp([0-9]*)-")
        closestVersion = 0
        latestarm64 : str = None
        latestx86_64 : str = None
        for distribution in releases:
            if distribution["filename"].find(release) != -1:
                v = reg.findall(distribution["filename"])
                if len(v) != 0:
                    if int(v[0]) <= self.targetPyVersion:
                        if int(v[0]) > closestVersion:
                            closestVersion = int(v[0])
                            if distribution["filename"].find("arm64") != -1:
                                latestarm64 = distribution
                            elif distribution["filename"].find("x86_64") != -1:
                                latestx86_64 = distribution
        if latestarm64 and latestx86_64:
            print(f"Found {latestarm64["filename"]} for Python {reg.findall(latestarm64["filename"])[0]} and release {release}.")
            print(f"Found {latestx86_64["filename"]} for Python {reg.findall(latestx86_64["filename"])[0]} and release {release}.")
            self.distributions = [latestarm64, latestx86_64]
            return True
        else:
            for distribution in range(len(releases)):
                if releases[distribution]["filename"].find(release) != -1:
                    if releases[distribution]["filename"].find(f"py{str(sys.version_info.major)}") != -1:
                        distributions.append(releases[distribution])
            self.distributions = distributions
            return True

    def getLatestVersion(self) -> str:
        versions : list[str] = self.packageInfo["versions"]
        return versions[-1]
        
    def hasUniversal2Wheel(self, release : str):
        self.closest = self.getAvailableDistributionsForRelease(release)
        for distribution in self.distributions:
            if distribution["filename"].endswith("universal2.whl"):
                return 0
            elif distribution['filename'].find(f"py{str(sys.version_info.major)}-none-any") != -1:
                return 1
        return 10
    
    async def makeAndInstallUniversal2Wheel(self, release : str) -> None:
        code = self.hasUniversal2Wheel(release)
        if code == 0:
            print(f"Universal2 wheel already exists for release {release}.")
        elif code == 1:
            print("Any wheel found. Installing...")
        if self.checkLocalUniversal2Wheel(release) == False:
            [installedDist, uWheelName] = self.create_universal2_wheel(code)
            print(uWheelName)
        else:
            print("Found Universal2 wheel in local cache.")
            uWheelName = self.checkLocalUniversal2Wheel(release)
        if code == 0 or code == 10:
            print("Installing universal2 wheel...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", uWheelName, "--force-reinstall"])
                print("Universal2 wheel installed.")
                if self.checkUniversalInstallation():
                    print(f"Universal2 wheel for {self.packageName} is installed correctly.")
                    if 'installedDist' in locals():
                        print("Cleaning up...")
                        for dist in installedDist:
                            os.remove(dist)
                        print("Cleanup complete.")
                    print("Checking for remaining dependencies & installing them if not in universal2 mode already...")
                    await self.installRemainingDependencies()
            except subprocess.CalledProcessError as e:
                print(f"Error installing universal2 wheel: {e.output}")
        elif code == 1:
            print("Installing any wheel...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", uWheelName, "--force-reinstall"])
                print("Any wheel installed.")
                print("No check needed for universal2 mode since this module is in Python language only (none-any wheel).")
            except subprocess.CalledProcessError as e:
                print(f"Error installing any wheel: {e.output}")
        return

    def create_universal2_wheel(self, code : int, dest: str = "wheels"):
        installedDist : list[str] = []
        uWheelName : str = None
        for distribution in self.distributions:
            if self.closest:
                pass
            elif distribution["filename"].find(f"cp{str(self.targetPyVersion)}") and distribution['filename'].find("macosx") != -1:
                print(f"Downloading {distribution['filename']}...")
                URL : str = distribution["url"]
                if dest == "wheels":
                    if not os.path.exists("wheels"):
                        os.mkdir("wheels")
                dReq = requests.get(URL, stream=True)
                with open(f"{dest}/{distribution['filename']}", "wb") as file:
                    for chunk in dReq.iter_content(chunk_size=1024):
                        file.write(chunk)
                    file.close()
                installedDist.append(f"{dest}/{distribution['filename']}")
            else:
                pass
            
        if code == 10:
            print("Creating universal2 wheel...")
            if installedDist[0].find("x86_64") != -1:
                uWheelName = installedDist[1].replace("arm64", "universal2")
                fuse_wheels(installedDist[0], installedDist[1], uWheelName)
            else:
                uWheelName = installedDist[0].replace("arm64", "universal2")
                fuse_wheels(installedDist[1], installedDist[0], uWheelName)
            print("Universal2 wheel created.")
        return installedDist, uWheelName

    async def installRemainingDependencies(self):
        pkg = subprocess.check_output([sys.executable, "-m", "pip", "show", self.packageName], text=True)
        requires : list[str] = pkg.split("Requires: ")[1].split("Required-by:")[0].split("\n")[0].strip().split(",")
        print(f"Following dependencies found : {requires}")
        if requires != ['']:
            for dep in requires:
                n = dep.strip()
                print(f"Checking {n}...")
                subPkg = subprocess.check_output([sys.executable, "-m", "pip", "show", n], text=True)
                version : str = subPkg.split("Version: ")[1].split("\n")[0]
                installer = PkgManager(n)
                await installer.makeAndInstallUniversal2Wheel(version)
        print("All dependencies are now in universal2 mode. Done !")
        return

    def checkUniversalInstallation(self):
        print("Checking fat mode for .so files...")
        try:
            output = subprocess.check_output([sys.executable, "-m", "pip", "show", "-f", self.packageName], text=True)
            location = output.split("Location: ")[1].split("Requires:")[0].strip()
            installedFiles = output.split("Files:")[1].split("\n  ")[1:-1]
            toRemove = []
            for file in installedFiles:
                if file.find(".dist-info") != -1:
                    toRemove.append(file)
                elif file.find(".so") == -1:
                    toRemove.append(file)
            for file in toRemove:
                installedFiles.remove(file)
            OK = True
            for soFile in installedFiles:
                output = subprocess.check_output(["lipo", "-info", os.path.join(location, soFile)], text=True)
                if output.find("Non-fat file") != -1:
                    print(f"{soFile} is not in fat mode.")
                    OK = False
                else:
                    print(f"{soFile} is in fat mode.")
            return OK
            
        except subprocess.CalledProcessError as e:
            print(f"Error checking fat mode: {e.output}")

    def processDependencies(self):
        deps : list[str] = self.packageInfo["info"]["requires_dist"]
        for dep in deps:
            if dep.find("extra") == -1:
                checker = PkgManager(dep)
                if not checker.hasUniversal2Wheel(checker.getLatestVersion()):
                    self.allDependencies.append(dep)
        return

    def checkLocalUniversal2Wheel(self, version : str):
        files = os.listdir("wheels")
        exp = regex.compile(f"{self.packageName}-{version}.*cp{self.targetPyVersion}.*macosx.*universal2.whl")
        for file in files:
            if exp.findall(file) != []:
                return os.path.join(os.getcwd(), "wheels", file)
        return False