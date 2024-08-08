# README

## universalPip
#### Universal Package Installer for Python

[![PyPI](https://img.shields.io/pypi/v/universalPip)](https://pypi.org/project/universalPip/)
[![downloads](https://static.pepy.tech/badge/universalPip/month)](https://pepy.tech/project/universalPip)

## Table of contents
- [Description](#description)
- [Story](#story)
- [Note about universal wheels](#note-about-universal-wheels)
- [Note about packaging](#important-note-about-packaging)
- [`uPip`'s installation logic](#uPips-installation-logic)
- [Uninstall packages](#how-to-uninstall-packages-installed-by-uPip)
- [Install the CLI](#installation)
- [Usage](#usage)
    - [Install a package](#install-a-package)
    - [Create `universal2` wheel](#create-an-universal2-wheel)
    - [Check if a package is universal](#check-if-a-package-is-universal)
    - [Show default stored wheel directory](#show-default-stored-wheel-directory)
    - [Invoke pip](#invoke-pip)
    - [`uPip`'s version](#printing-uPips-version)
    - [Print documentation](#print-documentation)
- [Contributing](#contributing)
- [License](#license)

## Changelog
You can view the complete changelog [here](https://github.com/MaximeLeMagicien/uPip/blob/main/Changelog.md).

<hr>

### Description
The `universalPip` package (called `uPip` in this document) is a Python package which completes the `pip` command line tool provided with any standard Python3 installation. `uPip`'s main goal is to provide an easy way to install any python package in `universal2` binary mode, which is compatible with any macOS installation.

### Story
As you probably know, Apple recently stopped using `intel chips` as their processor for new macs. They released in September 2020 their own chip called the `M1`. Unfortunatly, apps built on intel chips can't run properly on M1 and newer chips. A complete app rebuild is necessary. Even if `rosetta` exists and enables the aibility to run `x86_64` apps on `M1` architecture, it is not a durable solution.

Due to the fact that most people still uses `intel` architecture and want to publish apps on both architectures, developers needs to package their apps into an `universal` app bundle in order to run their app on any mac installation.

Those changes had an huge impact on Python packages. In fact, all binary files (with `.so` extension) needed to be recompiled on newer macs with M1 chips to extend compatibility. This is why packages with binary dependencies now provides two different wheels: the first one `macosx_10_X_x86_64.whl` for `intel` macs and `macosx_11_0_arm64.whl` for `M1` macs and newer. See [below](#important-note-about-packaging) for more information.

In order to compile applications in universal mode, with `pyinstaller` for example; installed wheels in the Python environment need to have both architectures inside their `.so` binaries files. Usually these wheel distributions are named like this: `macosx_11_0_universal2.whl` (See [here](#note-about-universal-wheels) for more information about compiling `universal2` applications using `pyinstaller`). <u>Unfortunatly, some packages do not provide these kind of wheels but only seperarated wheels for each architecture.</u> 

`uPip`'s story starts here: knowing all the facts mentionned above, the Python Package Index needed a new package to easily install any Python package in `universal2` mode. <u>`uPip` has `pip`'s same capabilities but adds a layer of verification when installing a package. If no `universal2` distribution wheel exists in the package repository, it will download each architecture wheel and fusionnate their wheels to create an `universal2` distribution and then install it.</u> Read [installation logic](#uPips-installation-logic) for further information.

### Note about universal wheels
`uPip`'s main goal is to handle the case where no `universal2` wheel distribution is provided for a package release. But not all packages needs an `universal2` wheel. In fact, if a package (like this one) doesn't have any binary dependencies, it often has only one release named `py3-none-any.whl` which means that all package's logic is coded in Python only and is compatible with any installation. So, even on `arm64` or `x86_64` mac architectures, those packages will work normally. See [installation logic](#uPips-installation-logic) for more information.

### Important note about packaging
Even if compiling universal app bundles for both `x86_64` and `arm64` architectures is possible, universal applications are way heavier in terms of size than separated architecture applications. For instance, a small app packaged with `pyinstaller` for `x86_64` only has a 50 MB size whereas the same application compiled in `universal2` mode has a 250 MB size.<br><b>Take this warning in consideration when compiling bigger applications because their final size can either double or triple!</b>

In order to compile an universal bundle on macOS with PyInstaller, you need to have all your project's requirements and dependencies installed in `universal2` mode and set inside your `.spec` file the target architecture to `universal2`. Read [pyinstaller's documentation](https://pyinstaller.org/en/stable/feature-notes.html#macos-multi-arch-support) for more information.

### `uPip`'s Installation logic
When installing a package, `uPip` will follow this logic: 
- First, check if an `universal2.whl` exists for the given release version.
    - If such a release exists, downloads it and installs it
- If no `universal2.whl` distribution exists, checks if a distribution `p3-none-any.whl` exists, meaning that the current packages has no platform specific dependencies.
    - If such a release exists, downloads it and installs it
- If neither `universal2.whl` and `p3-none-any.whl` distribution exists, downloads both `macos_10_X_x86_64.whl` and `macosx_11_0_arm64.whl` wheels to fuse them into `macosx_11_0_universal2.whl` and then installs the created wheel.

When the universal2 wheel is installed, `uPip` checks the newly installed package's dependencies to also update them if they are not in universal2 mode. The same logic applies for processing package's dependencies as described above.

### How to uninstall packages installed by `uPip`?
There is no specific tool to uninstall packages installed by `uPip`. You can use `pip` directly to uninstall any package installed by `uPip` as you would normally do for a normal package. Or you can [invoke pip from `uPip`](#invoke-pip) to be sure to call the same python version as the one used by `uPip`.

### Installation
To install the `uPip` package, you can use the following command:

```shell
$ pip install universalPip
```
To verify the installation, call the `uPip` CLI from the terminal:
```shell
$ uPip
```
If the CLI is correctly installed, the documentation should show up.

### Usage
#### Install a package 
<hr>
Once installed, you can use the `uPip` package to install other Python packages. Here's an example:

<br>Let's say we want to install [mzdata2mat](https://github.com/MaximeLeMagicien/mzdata2mat), a package aimed to convert `.mzData.xml` files into `.mat` files. Here is the command to install the package:

```shell
$ uPip --install mzdata2mat
```
The installation will be performed into the `site-packages` of the python installation which downloaded `uPip` inside the `wheels` folder.<br>

Additionnaly, you can add `--version` tag to specify a release version to install. Command would be: 
```shell
$ uPip --install mzdata2mat --version "1.0.0"
```
If no version is specified, the latest one will be used.
<hr>

#### Create an universal2 wheel
If you just want to create a wheel without installing it, use the following command:
```shell
$ uPip --makeU mzdata2mat
```
Same logic for the `--version` tag, either specify it to create an `universal2` wheel or don't specify it and the latest version available will be used.

All created wheels are stored inside `uPip`'s install directory in the `site-packages` of the python installation in a folder called `wheels`. If you want to specify a custom path use the following command:
```shell
$ uPip --makeU mzdata2mat --destination "path/to/folder"
```

If `--destination` is not provided, default path will be used.
<hr>

#### Check if a package is universal
To avoid installing twice a package already in `universal2` mode, you can use the verification process of `uPip` by using this command:
```shell
$ uPip --checkU mzdata2mat
```
This command will verify if all `.so` files inside `mzdata2mat` package are in fat mode with both `arm64` and `x86_64` architectures inside.
<hr>

#### Show default stored wheel directory
You can show where is located the `wheels` directory by using this command:
```shell
$ uPip --showPath
```
This will print the default save location.
<hr>

#### Invoke `pip`
You can trigger pip from `uPip` CLI by adding this parameter to the command: `--pip`.
Here is an example:
```shell
$ uPip --pip "show mzdata2mat"
```
One main advantage to use `uPip` to call `pip` is to be sure to call the same python version of pip as the one used to run `uPip`. For instance, it could be useful to run pip like this in order to uninstall packages.

<hr>

#### Printing `uPip`'s version
To show `uPip`'s version use the following command:
```shell
$ uPip --V
```

<hr>

#### Print documentation
As a normal package, to print `uPip`'s documentation in the terminal use the following command:
```shell
$ uPip -h
```
or simply:
```shell
$ uPip
```
In fact, if there is no parameters provided with `uPip`'s call, documentation is printed by default.
### Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/MaximeLeMagicien/uPip).

### License
This package is licensed under the MIT License. See the [LICENSE](https://github.com/MaximeLeMagicien/uPip/blob/main/LICENSE) file for more details.