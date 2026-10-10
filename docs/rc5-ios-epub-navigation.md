# RC5 — iPhone EPUB download preserves Narou Web UI

## Reported issue
After clicking the download arrow in Narou on iPhone Safari, an EPUB file
preview opens in the same browser tab. The book downloads, but there is no
obvious way to return to the novel list, especially from an installed
home-screen web app.

## Upstream root cause and minimal fix
The pinned upstream `src/web/assets/js/ui/render.js` emits a per-row
`<a href="/novels/{id}/download">` link without any download attribute.
Navigating to the direct EPUB response replaces the novel-list page.

QnapNarou now adds `download target="_blank" rel="noopener noreferrer"`
to **only that one link** at native build time. For browsers implementing
same-origin anchor downloads, the browser saves the EPUB without navigating
away from the list. If iOS instead opens an EPUB preview, it opens as a
separate tab/window, keeping the original list available.

The normal backend route, Content-Disposition, EPUB response, filename,
conversion, library data and upstream styling are left unchanged. This
does not introduce polling or disk logging. No extra JS blob copy is used
for large books, keeping memory use and I/O bounded to the existing path.

## Upstream sync durability
This behavior is expressed as `corrected_download_ui()` inside
`tools/build_epub_lite.py`, the GPL/lite QPKG build entrypoint.
It patches the pinned upstream checkout before `cargo build --features lite`,
so the change is included in Rust's `include_str!` embedded Web UI.

- Exact expected anchor class and download route are validated.
- A changed/missing/duplicate anchor, already patched source or moved route
  fails the QPKG build explicitly; it cannot silently ship an old/broken UI.
- Tests validate the exact pinned upstream `render.js` if submodules are
  checked out. Future upstream syncs must pass this test and either retain
  or intentionally redesign the QNAP patch.
- The original upstream submodule SHA is never mutated by this PR.
  Only the disposable CI checkout is modified for the native build.

## QTS acceptance
1. Upgrade in QTS App Center without uninstalling QnapNarou.
2. Open the original Narou Web UI at port 8888 on iPhone.
3. Tap the DL arrow on an existing novel; confirm an EPUB downloads and
   that the novel-list page remains available in the original tab.
4. Open the EPUB via Files / Books; return to the previous Narou tab.
5. Verify the QTS management UI at port 8889, the update check,
   prior novel library and existing EPUB generation still work.
6. Test both Safari tab usage and iPhone Add to Home Screen (A2HS) if used.
   A2HS can differ from Safari in its handling of external tabs.

The RC5 package is a prerelease until the actual iPhone test is confirmed.
Avoid claiming that a new-tab workaround behaves identically in every
iOS browser; the preferred native download attribute is included, with
new-tab fallback.
