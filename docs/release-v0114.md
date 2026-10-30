# v0.1.14 — Fix bundled preprocess DSL stack error

## Reproduced field symptom

QTS v0.1.13 (narou.rs v0.5.5 local-build) logs `preprocess compile failed for Pixiv` and `アルファポリス` with pest `stack limit reached`. These warnings occur during site-definition compilation, including while updating unrelated Syosetu novels. They are separate from the expected `[updater promote] skipped: no embedded updater hash (develop build)` diagnostics. The displayed Syosetu work had no update; there is no observed database corruption in the supplied log.

## Scope and safety

- Pin upstream v0.5.5 commit `47bee6ba703441d3aa989e29694e3df485c4c643` exactly as v0.1.13; patch only `src/downloader/preprocess/parser.rs` in the throwaway CI source tree during QNAP native compilation.
- Fail closed on upstream parser blob drift (`41d61b8351ec7518bcdf1fda3e8c9be966260942`) or gitlink mismatch. Do not patch the running NAS.
- Dedicated 16 MiB parser thread, max 256 KiB DSL source; retain pest's internal native stack headroom protection. Worker join failures are surfaced as compilation errors, never swallowed.
- The original AST builder, preprocess grammar, actual site YAML, updater behavior, QNAP manager, EPUB overlay and novel data layout remain untouched.
- CI tests both full bundled Pixiv and Alphapolis preprocess scripts with a 2 MiB *caller* stack; checks source-size rejection and the normal EPUB regression. The final binary must contain the QNAP parser thread marker.

## Real QTS acceptance not yet confirmed

1. Back up `QnapNarou-data` and preserve v0.1.13 for recovery. QTS 5.x x86_64 in-place upgrade to v0.1.14 without deleting data.
2. Start/restart QPKG, check ports 8888/8889 and update a Syosetu work; neither Pixiv nor Alphapolis should log the parser stack warning.
3. Test actual Pixiv and Alphapolis update or import with valid access; verify site cookies and permissions separately if the service is blocked or needs authentication.
4. Confirm previously saved novels, metadata and EPUB/iPhone save/share remain intact. For rollback of migrated databases, restore the matching pre-upgrade backup.

This fix addresses definition compilation only; it does **not** guarantee Pixiv/Alphapolis network access, bypass login restrictions or alter their upstream DSL semantics.
