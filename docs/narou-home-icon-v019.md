# QnapNarou v0.1.9 — original Narou Home Screen icon (:8888)

Version v0.1.8 provides approved QNAP App Center and :8889 management portal
icons. Version v0.1.9 extends the **same approved art** to the *original*
Narou.rs Web UI served on :8888, so direct iPhone Safari → Add to Home Screen
shows the QnapNarou book/NAS icon instead of the upstream default N icon.

## Native asset injection (reviewable upstream sync)

The upstream Rust server serves its HTML and assets using `include_str!` and
`include_bytes!`. It does not dynamically read app icon files from QTS.
Therefore only a **new native compile** can make the original :8888 UI serve
the icon.

On the pinned upstream gitlink checkout, during QNAP GPL/native build:
1. `tools/build_epub_lite.py` applies the existing EPUB/JS fixes.
2. `tools/build_narou_home_icon.py` validates upstream `index.html` title,
   `frontend.rs` asset route and known embedded asset switch.
3. It inserts the correct `apple-touch-icon` link into only the upstream
   HTML head, adds one image/png asset branch in Rust and saves a derived
   180×180 PNG from the committed QNAP-approved icon.
4. The Rust build embeds that PNG in the compiled binary. No filesystem
   icon read, on-device Pillow processing, new background service or disk write.

If upstream updates change these exact locations, the overlay raises an
error instead of silently losing the icon. The upstream gitlink stays pinned
until reviewed.

## iPhone acceptance and caching

- On Safari, open the novel library directly on :8888; Share → Add to Home
  Screen. The approved icon should appear.
- Previously created icons may be cached by iOS. Delete only the iPhone
  Home Screen shortcut, **not NAS app or data**, and add the shortcut again.
- Port :8889 remains the separate QTS management portal and keeps its
  own icon from v0.1.8.
- Existing EPUB generation, safe download modal, user novels, Web updater,
  manifest source pin and QTS App Center icons are unchanged.

## Validation

Python regressions + JavaScript browser simulation + pinned upstream source
guard + static musl GPL Rust build + native EPUB test + QDK package generation.
A single CI run per milestone minimizes Actions cost. Confirm on actual QTS
and iPhone after update; no full native Apple browser emulation is claimed.
