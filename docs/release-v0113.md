# QnapNarou v0.1.13 upstream v0.5.5 — release validation

## Source and boundaries

- Upstream tag v0.5.5 peeled SHA: `47bee6ba703441d3aa989e29694e3df485c4c643`. This is an explicit gitlink update, not a moving upstream main.
- Preserve QTS ports 8888 (original Narou) and 8889 (manager), persistent `QnapNarou-data`, on-demand QPKG updates, read-only `io_probe.py`, iPhone Safari EPUB/share overlay and icons.
- The v0.1.13 Action checks exact upstream tag/commit and QPKG version, Python/JS/shell regression, native x86_64 musl GPL/lite build, embedded EPUB and icon, native EPUB test, complete runtime, QDK package and SHA256SUMS. It refuses to overwrite an existing release.
- No background source polling, SQLite RAM cache, startup build, or autonomous NAS installation.

## Device acceptance (not yet claimed)

1. Make and verify a backup of all `QnapNarou-data` (novels, SQLite, login credentials and settings); save a v0.1.12 QPKG.
2. Upgrade a QTS 5.x x86_64 device in-place; validate both ports, host allowlist, WebSocket, cold-boot recovery and manager's explicit update flow.
3. Using a copy of an actual library, confirm upstream v0.5.4/v0.5.5 SQLite migration preserves books, tags, read state and settings; reboot and convert/EPUB-test.
4. Confirm iOS share/download modal and icons; test customized `AozoraEpub3.ini` and `custom_chuki_tag.txt` are retained while their `.default` files ship.
5. Compare idle IOPS with read-only probe only on manual request; test interrupted install and rollback using a **pre-migration database backup**, not a potentially incompatible migrated DB.

Real-QTS data migration, crash recovery and rollback remain unverified by GitHub CI. Keep ports available only on LAN/Tailscale.
