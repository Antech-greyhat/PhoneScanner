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

<!-- demo gif: .github/assets/demo.gif -->

> [!IMPORTANT]
> Scan only phones you own or have permission to scan. Results are signs worth
> checking, not proof. A clean scan does not prove the phone is safe.

## Contents

- [What it checks](#what-it-checks)
- [Features](#features)
- [Requirements](#requirements)
- [Phone setup (one time)](#phone-setup-one-time)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Reports](#reports)
- [Online and offline mode](#online-and-offline-mode)
- [Troubleshooting](#troubleshooting)
- [Limits](#limits)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [Contributors](#contributors)
- [License](#license)

## What it checks

Phone-Scanner is read-only on the phone. Everything stays on your laptop,
except in Online mode, where only APK hashes (never files or your app list) are
sent to a lookup service.

| Check | Why it matters | adb command used | Data leaves laptop? |
|---|---|---|---|
| Sideloaded apps | Apps installed from outside a store are a common malware route | `pm list packages -3 -i -f` | No |
| Risky permissions | SMS, contacts, call log and screen-overlay access can be abused | `dumpsys package <app>` | No |
| Accessibility services | A service can read the screen and tap for the app | `settings get secure enabled_accessibility_services` | No |
| Device admins | Device admin apps have strong control over the phone | `dumpsys device_policy` | No |
| Hidden apps | An app with no launcher icon can hide from the app list | `cmd package query-activities ... LAUNCHER` | No |
| APK hash match | Confirms an app matches known malware | `pm path` + `sha256sum` (or `pull`) | Online mode: hash only |

## Features

- Menu-driven CLI with a clear status line (device, mode, report format)
- Quick scan (apps, permissions, services) and Full scan (adds APK hashing)
- Offline mode (no internet, no keys) and Online mode (hash lookups)
- Local hash list, plus MalwareBazaar and VirusTotal lookups online
- HTML and JSON reports
- Read-only on the phone; no root needed

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

## Quick start

Once `adb` is installed (see [Installation](#installation)) and the phone is set
up (see [Phone setup](#phone-setup-one-time)), clone the repo and run the tool:

**Windows (PowerShell):**

```powershell
git clone https://github.com/Antech-greyhat/PhoneScanner.git
cd PhoneScanner
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m phone_scanner
```

**Linux:**

```bash
git clone https://github.com/Antech-greyhat/PhoneScanner.git
cd PhoneScanner
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m phone_scanner
```

Then confirm the phone shows up (`adb devices` lists it as `device`), pick
`[01] Quick scan`, and open the report it saves to `reports/`. Offline mode is
the default and needs no API keys.

## Usage

Start the tool, then pick an option by number (`1` or `01` both work):

```
.venv\Scripts\python.exe -m phone_scanner      # Windows
.venv/bin/python -m phone_scanner              # Linux
```

| Option | What it does |
|---|---|
| `[01]` Quick scan | Apps, permissions and services. No hashes. |
| `[02]` Full scan | Quick scan plus an APK hash check. |
| `[03]` Mode | Switch between Online and Offline. |
| `[04]` Report format | Switch between HTML and JSON. |
| `[05]` View last report | Open the newest report. |
| `[06]` Update offline hash list | Download recent APK hashes from MalwareBazaar. |
| `[99]` About | Show version and license. |
| `[00]` Exit | Quit. |

On the first run it asks once whether you own the phone or have permission to
scan it, and remembers your answer.

Command-line flags:

| Flag | What it does |
|---|---|
| `--version` | Print the version and exit. |
| `--no-banner`, `-q` | Skip the start-up banner. |
| `--no-color` | Turn off colour (also honours the `NO_COLOR` environment variable). |
| `--debug` | Show debug logging. |

## Reports

Reports are saved to a `reports/` folder as `scan-YYYYMMDD-HHMMSS.html` or
`scan-YYYYMMDD-HHMMSS.json`, depending on the format you chose in `[04]`. The
HTML report is one self-contained file that opens in any browser and works
offline. Each report has a summary (counts per risk level), a per-app table
(installer, level, score and the reasons), and the device details with a
shortened serial.

> [!WARNING]
> A report lists the apps on your phone. Keep report files private and do not
> commit them. The `reports/` folder is gitignored.

<details>
<summary>JSON report shape</summary>

```json
{
  "tool_version": "0.1.0",
  "scan_time": "2026-11-03T12:34:56Z",
  "scan_type": "full",
  "mode": "offline",
  "device": { "model": "...", "android_version": "...", "serial": "..." },
  "summary": { "Low": 90, "Medium": 4, "High": 1 },
  "apps": [
    {
      "package": "com.example.app",
      "installer": "com.android.vending",
      "findings": ["sideloaded"],
      "score": 3,
      "level": "Low",
      "reasons": [{ "key": "sideloaded", "points": 3, "text": "..." }],
      "hash": { "source": "offline", "verdict": "malicious", "label": "..." }
    }
  ],
  "notes": "A clean result does not prove the phone is safe. ..."
}
```
</details>

## Online and offline mode

**Offline (default).** No internet and no API keys. Quick scan checks apps,
permissions and services. Full scan hashes each app's APK and compares it to a
local hash list, which you build and grow with `[06]`.

**Online.** Full scan looks each hash up in this order: a local 7-day cache,
your local hash list, MalwareBazaar, then VirusTotal for anything still unknown.
**Only hashes are sent, never APK files or your app list.**

Keys go in a `.env` file (copy `.env.example`). They are read from `.env` only
and are never printed or saved:

```
VT_API_KEY=your_virustotal_key
MB_AUTH_KEY=your_malwarebazaar_key
```

- MalwareBazaar key (free): <https://auth.abuse.ch>
- VirusTotal key (free): virustotal.com, Profile > API key

The free VirusTotal API allows 4 requests a minute and 500 a day, so the tool
waits about 15 seconds between VirusTotal calls and stops asking it once a quota
error comes back. The free VirusTotal and MalwareBazaar APIs are for
non-commercial use. Never commit your keys.

## Troubleshooting

| Problem | Fix |
|---|---|
| `adb` not found | Install Platform-Tools, then close and reopen the terminal. Add the `platform-tools` folder to PATH if needed. |
| Device shows `unauthorized` | Unlock the phone and tap **Allow** on the USB debugging prompt. Tick **Always allow from this computer**. |
| Device shows `offline` | Replug the phone, or run `adb kill-server` then `adb start-server`. |
| `no permissions` (Linux) | `sudo apt install android-sdk-platform-tools-common`, then unplug and replug. |
| Windows does not see the phone | Install the phone maker's USB driver. The Google USB driver is only for Google phones. |
| VirusTotal quota hit | Wait for the daily quota to reset, or use Offline mode. |

## Limits

- **Signs, not proof.** A flag means "worth checking", not "infected".
- **Unknown is not clean.** No hash match means the app is not in the lists, not
  that it is safe.
- **New malware is not in hash lists yet**, so a fresh threat can be missed.
- The allowlist only lowers the score of apps installed from the Play Store, so
  a sideloaded fake with a copied package name keeps its score.

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
