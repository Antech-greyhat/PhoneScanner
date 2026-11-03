# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-03

First release.

### Added

- Read-only adb wrapper that finds adb, lists devices with their state, reads
  device info, and refuses any command that could change the phone.
- Menu-driven CLI with an ANSI banner (with ASCII fallbacks), a status line,
  saved settings, a first-run permission prompt, and the flags `--version`,
  `--no-banner`/`-q`, `--no-color` and `--debug`.
- Data collection from the phone: third-party apps and installers, requested
  and granted permissions, launcher activities, enabled accessibility services
  and device admins.
- Per-app checks: sideloaded, risky permissions, accessibility enabled, device
  admin and no launcher icon.
- Risk scoring with points and plain reasons, Low/Medium/High levels, a
  banking-trojan combo, and a Play-Store-only allowlist.
- Quick scan wired end to end, with a results table and self-contained HTML and
  JSON reports.
- Offline and online APK hash checking: on-device hashing, a local hash list,
  a MalwareBazaar updater, and online lookups through a 7-day cache, the local
  list, MalwareBazaar and VirusTotal, with VirusTotal rate limiting. Only
  hashes are sent online, never files.

[0.1.0]: https://github.com/Antech-greyhat/PhoneScanner/releases/tag/v0.1.0
