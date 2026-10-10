# QnapNarou architecture and milestones

## Scope and distribution
QnapNarou packages the upstream [narou.rs](https://github.com/Rumia-Channel/narou.rs) Web UI for QTS. Do not rewrite or replace the upstream UI. Upstream source stays under `upstream/narou.rs` in a pinned Git submodule, so contributors can fetch and merge upstream updates. The local QNAP integration is separate.

Distributions must contain the entire upstream runtime payload: `narou_rs`, helper executables as needed, `webnovel/`, `preset/`, `commitversion`, `LICENSE`, `README.md`, and `Third-Party-License.md`. Verify architecture, libc compatibility, dependencies, and executable permissions on the target QNAP.

**License choice:** upstream standard (BSD-2-Clause) requires external AozoraEpub3 for conversion; upstream `lite` feature bundles GPL-3.0 code, making the binary distribution GPL-3.0. Do not distribute mismatched notices or suggest standard has bundled EPUB conversion.

## Roadmap and merge gates

1. M1: upstream reference, documented architecture, staging validator, local tests, no per-push CI. Gate: documented reproducible staging on Linux, no misleading QPKG claim.
2. M2: QDK QPKG packaging, startup/shutdown/service, QTS icon/launch URL, x86_64/aarch64 artifacts, complete runtime files. Gate: install/start/stop/uninstall and data persistence on real QTS.
3. M3: tokenless UI update from public, signed or checksum-validated QnapNarou GitHub release asset. Download to staging, verify platform/format, atomic swap, rollback on failure; never replace data or do unattended execution. Gate: end-to-end upgrade/rollback including interrupted download.
4. M4: low-write mode including in-memory log ring buffer, bounded memory cache, aggregated writes, flush on clean shutdown and explicit save, safety telemetry, and durability tests. Gate: measured HDD IOPS reduction and bounded recovery loss.
5. M5: upstream update automation, compatibility and security review, release. Gate: test updated upstream UI, licenses, complete package assets and publish release.

## IO policy

RAM-first is an optimization, not a claim of zero writes. Never put primary persistent libraries, SQLite database, credentials, or pending downloads only in tmpfs without crash protection. Allow bounded buffering (suggested starting point: up to 32 MiB or 5 minutes for noncritical logs/events, with override); durable content should use explicit write batch checkpoints, atomic rename and fsync where required. Keep access logs off by default. Disable aggressive per-second polling and flush. Report best-effort memory buffering and worst-case data-loss window clearly.

Avoid copying the upstream updater's arbitrary host installation semantics directly to QTS; update only QnapNarou release packages through its privileged service and narrowly scoped validation. Server must bind to LAN interface only on explicit admin configuration; otherwise bind loopback until QTS integration is validated.

## CI budget

No CI on each push. Run fast `python3 -m unittest discover -s tests -v` locally. Trigger manual `workflow_dispatch` release only when milestone gate passes. Each PR should include test evidence and review the exact diff before merge.
