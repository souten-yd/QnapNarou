# Release acceptance checklist

Never publish a QPKG based solely on an archive's filename or on a passing unit test.

## Native runtime
- [ ] Upstream narou.rs exact source commit pinned and reproducibly fetched
- [ ] Upstream license and all notices present, matching GPL/non-GPL build flavor
- [ ] Full web frontend bundled, upstream API compatibility verified
- [ ] ELF target architecture and GLIBC/library dependencies verified on actual QTS 5.x
- [ ] QDK output actually generated and inspected
- [ ] Install, service start/stop, uninstall/reinstall, upgrades verified with persistent data

## Web UI
- [ ] QTS Open action opens the actual upstream UI using QNAP LAN address
- [ ] iPhone Safari test including WebSocket and downloads
- [ ] QTS/network security and bind defaults confirmed, no unauthenticated WAN exposure
- [ ] Dedicated Update action in UI, requiring confirmation before installation

## Update safety
- [ ] Only public QnapNarou GitHub Releases, no personal token
- [ ] Verify downloaded asset SHA-256 against independent trusted manifest or digital signature; do not trust asset and same-origin checksum blindly
- [ ] Validate architecture, version monotonicity, package metadata, size and path constraints
- [ ] Stage before stop, preserve novels/settings/credentials, reject symlinks and traversal
- [ ] Roll back application version on error; test power-loss and repeated retries
- [ ] Update does not silently run arbitrary scripts as root

## Low disk access
- [ ] Count idle writes and startup writes on target HDD
- [ ] Bound memory cache and log buffers; document data loss window
- [ ] Batch only safe, noncritical writes, preserve crash consistency
- [ ] Shutdown/explicit save flush path, reboot and outage regression tests
- [ ] No polling or disk writes while idle, subject to upstream runtime limitations

## Cost
- [ ] No CI on each push; run tests locally
- [ ] Build release once per validated milestone
- [ ] Release assets built for QNAP device(s), no generic Linux binary assumptions
