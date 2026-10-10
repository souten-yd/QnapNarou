# v0.1.4 stable release — evidence and limitations

## Evidence

- QTS and iPhone acceptance: user reports RC5 works in general, including EPUB download/navigation. This does not imply every iOS home-screen mode or recovery path has been tested.
- Pinned upstream narou.rs source is included through Git submodule. QNAP EPUB and iOS changes are applied and checked in the compilation process.
- One-shot [RC5 build](https://github.com/souten-yd/QnapNarou/actions/runs/38094392643): Python regression tests, x86_64 musl binary, embedded-link marker, EPUB native unit test, QDK package and SHA-256 **passed**. Initial workflow failed **only at release publication** because of shell quoting in its notes.
- [RC5 publish-only workflow](https://github.com/souten-yd/QnapNarou/actions/runs/38095525099): verified the existing QPKG's SHA-256, then published the RC5 prerelease successfully without recompiling.
- Stable v0.1.4 reuses the **identical built QPKG** with SHA-256 `c7c7b003fd014bdefd2288fdb40f307c810290976cf3e5639d91ef4a0f9cc3e5` (no rebuild), version `0.1.4`.

## Explicitly not qualified

- Web-based automatic install and rollback (API returns 409; QTS App Center manual installation is required).
- NAS outage recovery / interrupted upgrade / indefinite storage preservation beyond tested QTS usage.
- Disk IOPS reduction, memory-only batch commits and QNAP ARM64 packaging.
- App Center certificate/signature recognition on every NAS model and complete iOS A2HS browser behavior.

Do not merge separate experimental RAM-cache or upstream automation features as part of this stable milestone. Preserve the original Narou UI, local-only management policy and data directory.
