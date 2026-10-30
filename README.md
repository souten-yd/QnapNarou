# QnapNarou

## v0.1.13 — narou.rs v0.5.5 (2026-10-30)

- Pinned upstream v0.5.5 (`47bee6ba703441d3aa989e29694e3df485c4c643`); dedicated one-shot Actions builds the complete native GPL/lite x86_64 QPKG and publishes only after checks pass.
- Upstream v0.5.4/v0.5.5 includes dependency/security fixes, new UI dialogs and library metadata/SQLite migrations. Existing QNAP ports 8888/8889, persistent novel data directory, iPhone EPUB modal, icons and read-only I/O probe remain.
- M4 SQLite RAM cache is **not** enabled. QTS installation, schema migration and rollback need real-device acceptance. **Back up QnapNarou-data before upgrading.** [Acceptance checklist](docs/release-v0113.md).

QTS 5.x QPKG integration of [Rumia-Channel/narou.rs](https://github.com/Rumia-Channel/narou.rs).

## v0.1.12 — read-only disk I/O diagnosis (M4 safe subset)

- Builds the same reviewed upstream narou.rs v0.5.3, complete GPL EPUB/iPhone UI and icons as v0.1.11.
- QDK includes the read-only on-demand `io_probe.py` in shared files. It reports whole-device read/write IOPS, throughput and busy %, not per-process activity; no background sampling. [QTS measurement instructions](docs/low-write.md).
- Restores all six diagnostic files from merged PR #18 that were unintentionally reverted by the v0.1.11 publishing recovery merge. No SQLite WAL/cache, runtime startup semantics, installer, or novel data changes.
- A guarded GitHub Actions one-shot source build verifies the pinned SHA, native Rust tests, QDK package inclusion and final SHA256SUMS from the correct root before publishing v0.1.12. Real QTS boot, interrupted upgrade/rollback and idle I/O measurements are still not device-verified.

## v0.1.11 — reviewed narou.rs v0.5.3 source build

- One-shot GitHub Actions x86_64 musl/GPL source build pinned to upstream v0.5.3 (4c0c15849690b12ee27faf617eabbb863b73d72a). Includes QNAP EPUB modal/iPhone icon overlays and complete QDK QPKG output.
- No scheduled polling. Manual Actions rebuild uses pinned source; Web updater remains explicitly user initiated.
- QTS v0.1.11 install/rollback/IOPS acceptance remains unverified on hardware. Back up QnapNarou-data before upgrading.

## v0.1.10 — QTS cold-boot auto-recovery

- [v0.1.5 updater bootstrap](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.5) — first Web-updater version, installed once through QTS App Center.
- [v0.1.9](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.9): approved book/NAS icon in both iPhone Home Screen shortcuts and QNAP App Center.
- v0.1.10: bounded automatic recovery if the QTS shared volume/Python dependencies are late after reboot. See [boot recovery notes](docs/qts-reboot-recovery-v0110.md).
- [v0.1.6 stable](https://github.com/souten-yd/QnapNarou/releases/tag/v0.1.6) — QTS Web-updater acceptance passed on the NAS.
- v0.1.7 — EPUB save/share modal on iPhone; avoids automatically navigating away from the original novel list, and is reapplied on reviewed upstream builds. See [iOS notes](docs/ios-epub-save-v017.md).
- Original narou.rs Web UI remains on **port 8888**; QTS management is on **port 8889**.
- GPL-3.0-only AozoraEpub3_Lite EPUB generation is built in. iPhone downloads preserve the original novel-list tab where the browser permits; a new tab is used as a fallback.
- QTS LAN and WebSocket port conflict fixes, and RC-aware update discovery, are included.
- User has confirmed basic QTS/iPhone operation of v0.1.4 RC5. The **v0.1.5 to v0.1.6 Web-triggered upgrade succeeded on a real QTS NAS**. Automatic rollback and sustained disk-write measurements remain unverified.

Use QTS App Center to install or upgrade the QPKG **without uninstalling**. Back up `QnapNarou-data` before making changes. Do not publish NAS ports 8888 and 8889 to the public Internet. A compatible Python 3 interpreter is currently needed for the local management page (commonly `/opt/bin/python3.11`).

## Updating

From **v0.1.5**, QTS manager can apply a newer **stable** GitHub QPKG directly from the Web UI: click 最新版を確認 → 最新版へ更新. No user-entered token, background polling or credential setup. Downloads are checked for exact release URL, size, SHA-256 and architecture. The previous stable QPKG is fetched for recovery before installing. Updates run in a detached worker; the installed version and both Web ports must pass a bounded health check. If validation fails, the worker attempts a verified rollback. Preview (RC) releases still require QTS App Center manual installation.

**Bootstrap:** v0.1.4 has this action disabled, so install v0.1.5 once through App Center. LAN/Tailscale only; do not expose ports publicly. QTS signature policy is not bypassed. The successful Web-update path was confirmed on a QTS NAS; interrupted updates and power-loss recovery still require separate real-device testing.

## Source, licenses, upstream integration

The original upstream source is pinned in `upstream/narou.rs` via Git submodule. QNAP changes to EPUB delivery and iOS navigation are explicit build-time source transformations in `tools/build_epub_lite.py`. An upstream source change that invalidates their assumptions fails the build rather than silently dropping the fixes.

The GPL binary must be distributed with corresponding source and third-party license notices. See [upstream sync instructions](docs/upstream.md) and [EPUB details](docs/epub-rc3.md).

## Disk writes and CI

Idle HTTP logging and periodic release checks are disabled. Novel data and SQLite remain durable on disk; full RAM-first write batching and an actual measured IOPS reduction are **not** claimed as implemented. Expensive Rust/QDK builds are performed manually per milestone, not on every push.
