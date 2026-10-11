# v0.1.7 — iPhone EPUB save/share without replacing the novel list

## Reproduction and behavior

On iOS (especially a Home Screen web app), clicking the old EPUB link
may enter a full-screen native preview without any visible back control.
Adding `target="_blank"` in v0.1.4 was insufficient on that device.

QnapNarou now intercepts **only** a per-novel EPUB download link using a
document capture listener. Clicking it never navigates the page. A small
modal opens with progress and a **Close** control; it fetches the EPUB
from the existing same-origin `/novels/{id}/download` endpoint on demand,
checks HTTP status, a 150 MiB size limit and ZIP/EPUB magic bytes, then
offers the following explicit choices:

- **共有・保存** (Share/Save): shown only if a browser supports file sharing;
  a second user tap calls the iOS share sheet while user activation is valid.
- **ダウンロード**: downloads the prepared in-memory EPUB Blob from a user
  click; if the browser ignores the download attribute, `target="_blank"`
  is limited to this fallback and should keep the original novel list in
  the original browsing context.
- **閉じる**: cancels an unfinished request and closes the modal with no
  navigation. Escape and tapping the backdrop also close it.

NOTE: `navigator.share` requires a secure context. It is often unavailable
at a private `http://192.168.x.x` LAN URL. In that case, a user-visible
explicit Blob download remains available; Safari or installed home-screen
applications can still choose how to open it. No JavaScript can guarantee
a forced native Save to Files on all iOS environments.

## Upstream-update resilience

The implementation lives in the QnapNarou-owned
`tools/qnap_epub_download.js`. During a **native GPL/lite build**,
`tools/build_epub_lite.py` validates the pinned upstream
`src/web/assets/js/ui/render.js`, marks exactly one existing EPUB
download link with `data-qnap-epub`, and appends the independent QNAP
save/share module to the render asset before Rust `include_str!`
embeds it. Exact route and anchor markers must match or the build
fails closed.

Future upstream submodule changes retain the QNAP source file and
automatically reapply it at build time. If upstream changes its markup,
update the integration with a reviewed PR and regression tests: do not
silently skip it. The pinned upstream gitlink itself remains unchanged.
The legacy patch that only added an anchor `target="_blank"` is replaced,
not stacked.

## Data and performance

- No new server endpoint, novel DB mutation, background network polling,
  on-disk cache, access log, or timer when idle.
- Only a user-requested EPUB is fetched into RAM and kept while the modal
  is open; closing releases the in-memory file and revokes Blob URLs.
- Other Narou.rs UI features, epub generation and QTS update functionality
  are unchanged.
- Package x86_64 only; the built GPL Rust executable needs recompilation
  to embed the new JavaScript. Merely rewrapping the old QPKG would not work.

## Verification

Run Python unit tests and zero-dependency Node browser-interception tests
before the one-shot x86_64 Rust/QDK build. The build must verify the compiled
binary contains the QnapNarou overlay marker, preserve EPUB generation and
all QTS services, then publish for real-iPhone validation.

On iPhone test **both Safari and Home Screen launch**, with and without
Web Share availability if feasible. A Download click must not open the
previous irreversible full-screen preview automatically, and the modal
must always provide Close. After saving, confirm the EPUB opens in Books
and returning to the Narou list works.

Prior releases remain available for rollback through QTS App Center.
