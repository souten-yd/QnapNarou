# QnapNarou v0.1.2 RC3 — Built-in EPUB downloads

## Root cause verified in pinned narou.rs

The initial QNAP package was produced by `cargo local-build`, which always
uses the **non-GPL default Rust features**. Without the external AozoraEpub3
engine, converting a novel can produce Aozora text without an EPUB file.
When users click the main Web UI's download icon, the normal variant's
`src/web/novels.rs::download_ebook` returns HTTP 404
`Ebook not found for ID=0` when no EPUB exists.

The upstream `lite` feature embeds AozoraEpub3_Lite and can construct an
EPUB on demand if a saved EPUB is missing. However, its SQLite fast path
currently returns a `novel_outputs.converted_text` payload as though it
were an EPUB. That payload is *text* and may be Brotli-compressed.
The QNAP-specific source patch skips that invalid shortcut and
runs the normal EPUB creation path.

## Build and license

The QPKG continues to contain **all upstream runtime files** from
`cargo local-build` and replaces only `narou_rs` with a fully compiled,
`--features lite` Rust binary targeting `x86_64-unknown-linux-musl`.
It uses the pinned submodule and rejects source drift. It replaces the
non-GPL notices with the upstream full `Third-Party-License.md` and
includes `AozoraEpub3-Lite-License.md`; QPKG metadata states
`GPL-3.0-only`.

Because the executable embeds GPL-3.0-only components, distribute the
complete corresponding source for this binary, including the pinned
narou.rs and AozoraEpub3_Lite revisions and this QNAP patch. See:
- https://github.com/Rumia-Channel/narou.rs
- https://github.com/Rumia-Channel/AozoraEpub3_Lite
- https://github.com/souten-yd/QnapNarou

The original upstream project is still a pinned Git submodule; the QNAP
source patch is applied to the build checkout only. Do not upstream-sync
silently. Never ship a GPL binary with the non-GPL-only notice.

## QTS acceptance

This release is a **preview until tested on the NAS**.
Install the QPKG as an update (do not erase QnapNarou-data).
Open the original Narou UI on port 8888; one previously converted novel
with no EPUB should download a file whose ZIP first entry is
`mimetype` containing `application/epub+zip`. Open it on iPhone Books.
Confirm the management UI on port 8889 still works. Verify both an
existing novel and a new novel, and verify that the library survives QTS
restart. If the EPUB is corrupted, inspect only a short in-RAM diagnostic,
not a persistent debug log.

No automatic background conversions or polling were added; EPUB is built
when requested. This is not a claim of zero disk writes: conversion and
cached novel content still have normal persistence. No direct push,
auto merge, or uncontrolled execution was introduced.
