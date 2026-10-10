# QnapNarou

QTS 5.x QPKG integration of [Rumia-Channel/narou.rs](https://github.com/Rumia-Channel/narou.rs).

## v0.1.4 — stable release

- [Download the stable QPKG](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.4) (x86_64).
- Original narou.rs Web UI remains on **port 8888**; QTS management is on **port 8889**.
- GPL-3.0-only AozoraEpub3_Lite EPUB generation is built in. iPhone downloads preserve the original novel-list tab where the browser permits; a new tab is used as a fallback.
- QTS LAN and WebSocket port conflict fixes, and RC-aware update discovery, are included.
- User has reported basic QTS/iPhone operation of RC5. This is **not an independent device certification**; upgrade/rollback and sustained disk-write measurements remain pending.

Use QTS App Center to install or upgrade the QPKG **without uninstalling**. Back up `QnapNarou-data` before making changes. Do not publish NAS ports 8888 and 8889 to the public Internet. A compatible Python 3 interpreter is currently needed for the local management page (commonly `/opt/bin/python3.11`).

## Updating

The QTS manager checks public GitHub Releases **only when the user clicks 更新を確認**. It shows the latest stable or release-candidate version and offers a QPKG download link. No manual token is required. Installation is performed via QTS App Center: **automatic installation from the Web page is disabled server-side** until device-level crash/restart/rollback tests pass. Future releases must preserve this gate unless explicitly verified and approved.

## Source, licenses, upstream integration

The original upstream source is pinned in `upstream/narou.rs` via Git submodule. QNAP changes to EPUB delivery and iOS navigation are explicit build-time source transformations in `tools/build_epub_lite.py`. An upstream source change that invalidates their assumptions fails the build rather than silently dropping the fixes.

The GPL binary must be distributed with corresponding source and third-party license notices. See [upstream sync instructions](docs/upstream.md) and [EPUB details](docs/epub-rc3.md).

## Disk writes and CI

Idle HTTP logging and periodic release checks are disabled. Novel data and SQLite remain durable on disk; full RAM-first write batching and an actual measured IOPS reduction are **not** claimed as implemented. Expensive Rust/QDK builds are performed manually per milestone, not on every push.
