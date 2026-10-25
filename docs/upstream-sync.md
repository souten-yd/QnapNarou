# Upstream synchronization and reproducible QPKG builds

Original narou.rs is a pinned Git submodule and is never updated on NAS startup.

1. `git submodule update --init --recursive`; run `python3 tools/update_upstream.py --tag vX.Y.Z` to read a **dry-run** commit list and SHA.
2. Review the exact upstream tag, dependencies, download/API, SQLite, licensing, iPhone EPUB and icon overlay anchors before mutating source.
3. On a feature branch only, run `python3 tools/update_upstream.py --tag vX.Y.Z --apply --expected-sha <reviewed SHA>`. This stages only the gitlink; run `git diff --cached --submodule=log` and open a PR.
4. Bump QPKG version and update one-shot Actions pin, and test Python/JS, native GPL EPUB runtime, QDK QPKG, real QTS install/upgrade/rollback and novel persistence before distribution.
5. v0.1.11 pins tag v0.5.3 to 4c0c15849690b12ee27faf617eabbb863b73d72a. The new `qnapnarou-upstream-v0111.yml` Action is manually rerunnable, and on first merge into main performs a **single** build and release only if all CI gates pass. It cannot silently fetch or build arbitrary upstream main.

No schedule, background NAS source update, automatic merge, or unreviewed gitlink mutation is part of this tooling. QTS on-device acceptance of the new source remains a deployment gate. The M4 SQLite RAM-cache patch is **not enabled** and must not be treated as validated until crash-durability and real idle I/O tests pass.
