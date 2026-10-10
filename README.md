# QnapNarou

QTS 5.x QPKG integration of [Rumia-Channel/narou.rs](https://github.com/Rumia-Channel/narou.rs), with the original Narou Web UI on **8888** and a separate LAN-only QNAP administration screen on **8889**.

## Availability

- [v0.1.1 RC2](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.1-rc2) — LAN/WebSocket startup repair; user-confirmed working on QTS.
- [v0.1.2 RC3](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.2-rc3) — embedded GPL EPUB generator; builds and unit tests passed, QTS EPUB download confirmation pending.
- [v0.1.3 RC4](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.3-rc4) — fixes HTTP 404 when pressing 更新を確認 with only prereleases; QTS verification pending.
- v0.1.4 RC5 — fixes iPhone EPUB download navigation, with a source-guarded patch reapplied on subsequent builds. [PR #9](https://github.com/souten-yd/QnapNarou/pull/9). QTS/iPhone validation pending.

**These are prerelease packages**, not QTS-certified production releases. Back up your novel library before installing manually from QTS App Center. Never delete the QnapNarou-data directory to upgrade.

## Web-based updates

The local administration page checks public GitHub Releases **only when clicked**. No token is required. When only RC versions exist, it shows the current/latest versions and a QPKG download link instead of returning the GitHub /releases/latest HTTP 404.

The in-browser automatic installer/rollback is **not device-qualified** and remains disabled. For now, download the QPKG via the link and install it through QTS App Center. Do not expose ports 8888/8889 to the public Internet.

## Source, licensing and low disk writes

The original source is pinned as a Git submodule for reviewable upstream sync. GPL-labeled packages with the AozoraEpub3_Lite engine ship corresponding third-party notices. See [EPUB notes](docs/epub-rc3.md), [release gates](docs/release-gates.md), and [RC4 update-check details](docs/rc4-update-check.md).

The QNAP wrapper disables HTTP access logs and periodic release polling. Novels and SQLite remain durably stored; no measured HDD I/O reduction is claimed until real NAS before/after metrics exist. No automatic background CI or upgrades are scheduled.
