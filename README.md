<h1 align="center">Phone-Scanner</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-blue?style=for-the-badge" alt="License GPLv3"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey?style=for-the-badge" alt="Platform Linux | Windows">
  <a href="https://developer.android.com/tools/adb"><img src="https://img.shields.io/badge/target-Android%20(ADB)-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Target Android (ADB)"></a>
</p>
<p align="center">
  <a href="https://github.com/Antech-greyhat/PhoneScanner/commits"><img src="https://img.shields.io/github/last-commit/Antech-greyhat/PhoneScanner?style=flat-square" alt="Last commit"></a>
  <a href="https://github.com/Antech-greyhat/PhoneScanner/issues"><img src="https://img.shields.io/github/issues/Antech-greyhat/PhoneScanner?style=flat-square" alt="Issues"></a>
  <img src="https://img.shields.io/badge/version-0.1.0-blue?style=flat-square" alt="Version 0.1.0">
  <img src="https://img.shields.io/badge/Made%20in-Kenya-006600?style=flat-square" alt="Made in Kenya">
</p>

<p align="center">
Scan your Android phone from your laptop over ADB for sideloaded apps, risky permissions and spyware-like signs.
</p>

<p align="center"><i>Early development. Features are being added.</i></p>

> [!IMPORTANT]
> Scan only phones you own or have permission to scan. Results are signs worth
> checking, not proof. A clean scan does not prove the phone is safe.

## What it checks

Coming soon. This will list each check, why it matters, the adb command it uses, and whether any data leaves the laptop.

## Features

Coming soon. Menu-driven CLI, online and offline modes, HTML and JSON reports, no root needed.

## Requirements

- Python 3.10 or newer
- Git
- Android SDK Platform-Tools (adb)
- A USB data cable (not a charge-only cable)
- An Android phone with USB debugging turned on

## Phone setup (one time)

1. Open **Settings > About phone** and tap **Build number** seven times until it
   says you are now a developer. On some phones this is under
   **About phone > Software information**.
2. Open **Developer options** and turn on **USB debugging**.
3. Connect the phone with a data cable, unlock it, and tap **Allow** on the
   "Allow USB debugging?" prompt. Tick **Always allow from this computer**.
4. Run `adb devices`. You should see your phone with the word `device`.
   `unauthorized` means you have not accepted the prompt yet.
5. When you finish scanning, turn USB debugging off again.

Menu names differ by phone brand (Tecno, Infinix, Samsung, Xiaomi). The official
guide is at <https://developer.android.com/studio/debug/dev-options>.

## Installation

### Windows (do this first)

```powershell
# 1. Install adb
winget install -e --id Google.PlatformTools
# Close and reopen the terminal, then check:
adb version

# 2. Get the code
git clone https://github.com/Antech-greyhat/PhoneScanner.git
cd PhoneScanner

# 3. Make a virtual environment and install
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Run
.venv\Scripts\python.exe -m phone_scanner
```

If `adb` is not found after winget, download Platform-Tools from
<https://developer.android.com/tools/releases/platform-tools>, unzip it, and add
the `platform-tools` folder to your PATH. Windows needs the phone maker's USB
driver; the Google USB driver is only for Google phones. See
<https://developer.android.com/studio/run/oem-usb>.

Running `.venv\Scripts\python.exe` directly means you do not need to activate the
venv, so the PowerShell "running scripts is disabled" error does not apply.

<details>
<summary>If you prefer to activate the venv</summary>

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.venv\Scripts\Activate.ps1
```
</details>

### Linux (Debian, Ubuntu, Kali)

```bash
# 1. Install adb, git and venv support
sudo apt update
sudo apt install adb git python3-venv
adb version

# 2. Let your user talk to the phone over USB
sudo usermod -aG plugdev $LOGNAME
# Log out and log back in after this

# 3. Get the code
git clone https://github.com/Antech-greyhat/PhoneScanner.git
cd PhoneScanner

# 4. Make a virtual environment and install
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 5. Run
.venv/bin/python -m phone_scanner
```

If `adb devices` shows `no permissions`, install udev rules with
`sudo apt install android-sdk-platform-tools-common`, then unplug and replug the
phone. If a package name is different on your distro, use the official
Platform-Tools zip instead.

## Usage

Coming soon. The menu, its options and the CLI flags will be described here.

## Reports

Coming soon. Where reports are saved and what they contain.

## Online and offline mode

Coming soon. How each mode works and how to get the free API keys.

## Troubleshooting

Coming soon. Fixes for `unauthorized`, `offline`, `no permissions`, Windows
drivers and API quota limits.

## Contributing

Contributions are welcome. In short:

1. **Fork** the repo and **clone** your fork.
2. Add this repo as `upstream` and make a branch: `git checkout -b fix/short-name`.
3. Set up Python and install dev deps:
   `pip install -r requirements.txt -r requirements-dev.txt`.
4. Make a small, focused change.
5. Run the checks: `ruff check .`, `ruff format --check .`, `pytest -q`.
6. Commit with a Conventional Commit message and open a PR into `master`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full steps and project rules.

## Roadmap

- Termux support (planned)

<p align="center">
  <a href="https://github.com/Antech-greyhat/PhoneScanner/stargazers"><img src="https://img.shields.io/github/stars/Antech-greyhat/PhoneScanner?style=social" alt="Stars"></a>
  <a href="https://github.com/Antech-greyhat/PhoneScanner/network/members"><img src="https://img.shields.io/github/forks/Antech-greyhat/PhoneScanner?style=social" alt="Forks"></a>
</p>

## Contributors

Thanks to everyone who has helped build Phone-Scanner.

<a href="https://github.com/Antech-greyhat/PhoneScanner/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Antech-greyhat/PhoneScanner" alt="Contributors" />
</a>

## License

Phone-Scanner is free software under the GNU General Public License v3.0 or
later. See [LICENSE](LICENSE).
