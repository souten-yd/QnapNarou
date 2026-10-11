# QnapNarou

QTS 5.x QPKG integration of [Rumia-Channel/narou.rs](https://github.com/Rumia-Channel/narou.rs).

## v0.1.9 — icon integration

- [v0.1.5 updater bootstrap](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.5) — first Web-updater version, installed once through QTS App Center.
- v0.1.9: the approved book/NAS icon is also embedded in the original Narou :8888 Web UI for direct iPhone Home Screen shortcuts. See [v0.1.9 icon notes](docs/narou-home-icon-v019.md).
- [v0.1.6 stable](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.6) — QTS Web-updater acceptance passed on the NAS.
- v0.1.7 — EPUB save/share modal on iPhone; avoids automatically navigating away from the original novel list, and is reapplied on reviewed upstream builds. See [iOS notes](docs/ios-epub-save-v017.md).
- Original narou.rs Web UI remains on **port 8888**; QTS management is on **port 8889**.
- GPL-3.0-only AozoraEpub3_Lite EPUB generation is built in. iPhone downloads preserve the original novel-list tab where the browser permits; a new tab is used as a fallback.
- QTS LAN and WebSocket port conflict fixes, and RC-aware update discovery, are included.
- User has confirmed basic QTS/iPhone operation of v0.1.4 RC5. The **v0.1.5 Web-initiated upgrade path has not yet been confirmed on a real NAS**; update/rollback and sustained disk-write measurements remain open.

Use QTS App Center to install or upgrade the QPKG **without uninstalling**. Back up `QnapNarou-data` before making changes. Do not publish NAS ports 8888 and 8889 to the public Internet. A compatible Python 3 interpreter is currently needed for the local management page (commonly `/opt/bin/python3.11`).

## Updating

From **v0.1.5**, QTS manager can apply a newer **stable** GitHub QPKG directly from the Web UI: click 最新版を確認 → 最新版へ更新. No user-entered token, background polling or credential setup. Downloads are checked for exact release URL, size, SHA-256 and architecture. The previous stable QPKG is fetched for recovery before installing. Updates run in a detached worker; the installed version and both Web ports must pass a bounded health check. If validation fails, the worker attempts a verified rollback. Preview (RC) releases still require QTS App Center manual installation.

**Bootstrap:** v0.1.4 has this action disabled, so install v0.1.5 once through App Center. LAN/Tailscale only; do not expose ports publicly. QTS signature policy is not bypassed. NAS one-click upgrade and power-loss recovery still require real-device testing.

## Source, licenses, upstream integration

The original upstream source is pinned in `upstream/narou.rs` via Git submodule. QNAP changes to EPUB delivery and iOS navigation are explicit build-time source transformations in `tools/build_epub_lite.py`. An upstream source change that invalidates their assumptions fails the build rather than silently dropping the fixes.

The GPL binary must be distributed with corresponding source and third-party license notices. See [upstream sync instructions](docs/upstream.md) and [EPUB details](docs/epub-rc3.md).

## Disk writes and CI

Idle HTTP logging and periodic release checks are disabled. Novel data and SQLite remain durable on disk; full RAM-first write batching and an actual measured IOPS reduction are **not** claimed as implemented. Expensive Rust/QDK builds are performed manually per milestone, not on every push.
