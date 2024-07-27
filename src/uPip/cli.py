from .uPip import PkgManager
from argparse import ArgumentParser
from subprocess import check_call
import sys
import os

__version__ = "0.1.0"

def installPackage(name : str, version : str = None):
    Manager = PkgManager(name)
    Manager.makeAndInstallUniversal2Wheel(version if version != "latest" else Manager.getLatestVersion())

def checkPackage(name : str):
    Manager = PkgManager(name)
    if Manager.checkUniversalInstallation():
        print(f"{name} is installed as universal2 package.")
    else:
        print(f"{name} is not installed as universal2 package.")

def processInput():
    parser = ArgumentParser(prog="uPip", description="Creates an Universal2 distribution for given package on PyPI and installs it.")
    parser.add_argument("--install", type=str, required=False, help="Installs the package with given name and version as universal2 package. If package does not provide any universal2 distribution, attemps to creates one. If version is not provided, latest version will be installed. You can provide a path to a wheel file to install it directly.")
    parser.add_argument("--makeU", type=str, required=False, help="Creates universal2 distribution for given package. If version is not provided, latest version will be used.")
    parser.add_argument("--version", type=str, required=False, help="Version of the package to be installed. If not provided, latest version will be installed.", default="latest")
    parser.add_argument("--checkU", type=str, help="Checks if the package is already installed as universal2 package.", required=False)
    parser.add_argument("--pip", type=str, required=False, help="""Invoques pip module with given arguments. For example : 'uPkg --pip "show -f packageName"' Quotes MUST be provided for better command parsing.""")
    parser.add_argument("--V", action="store_true", help="Shows current version of uPip.", required=False)
    args = parser.parse_args()
    
    if args.V:
        print(f"uPip version : {__version__}")
        return
    
    elif args.install:
        if os.path.exists(args.install):
            check_call([sys.executable, "-m", "pip", "install", args.install], text=True)
            name = args.install.split("-", 1)[0]
            manager = PkgManager(name)
            manager.processDependencies()
        else:
            installPackage(args.install, args.version)
        return
    
    elif args.makeU:
        manager = PkgManager(args.makeU)
        code = manager.hasUniversal2Wheel(args.version if args.version != "latest" else manager.getLatestVersion())
        manager.create_universal2_wheel(code)
        return
    
    elif args.checkU:
        checkPackage(args.checkU)
        return
    
    elif args.pip:
        check_call([sys.executable, "-m", "pip", args.pip], text=True)
        return

    else:
        parser.print_help()
        return 