from .universalPip import PkgManager
from argparse import ArgumentParser
from subprocess import check_call
import sys
import os
import asyncio

__version__ = "0.1.0"

def installPackage(name : str, version : str = None):
    Manager = PkgManager(name)
    asyncio.run(Manager.makeAndInstallUniversal2Wheel(version if version != "latest" else Manager.getLatestVersion()))

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
    parser.add_argument("--destination", type=str, required=False, help="Destination path for the universal2 wheel file. If not provided, current working directory will be used.")
    parser.add_argument("--version", type=str, required=False, help="Version of the package to be installed. If not provided, latest version will be installed.", default="latest")
    parser.add_argument("--checkU", type=str, help="Checks if the package is already installed as universal2 package.", required=False)
    parser.add_argument("--showPath", action="store_true", help="Gives the path to the stored universal2 wheels on your system.", required=False)
    parser.add_argument("--pip", type=str, required=False, help="""Invoques pip module with given arguments. For example : 'upip --pip "show -f packageName"' Quotes MUST be provided for better command parsing.""")
    parser.add_argument("--V", action="store_true", help="Shows current version of uPip.", required=False)
    
    args = parser.parse_args()
    
    if args.V:
        print(f"uPip version : {__version__}")
        return
    
    if args.showPath:
        print(f"Path to stored universal2 wheels : {os.path.join(os.path.dirname(__file__), 'wheels')}")
        return

    elif args.install:
        if os.path.exists(args.install):
            check_call([sys.executable, "-m", "pip", "install", args.install, "--force-reinstall"], text=True)
            name = args.install.rsplit("/", 1)[1].split("-", 1)[0]
            manager = PkgManager(name)
            asyncio.run(manager.installRemainingDependencies())
        else:
            installPackage(args.install, args.version)
        return
    
    elif args.makeU:
        manager = PkgManager(args.makeU)
        code = manager.hasUniversal2Wheel(args.version if args.version != "latest" else manager.getLatestVersion())
        if args.destination:
            manager.create_universal2_wheel(code, args.destination)
        else:
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