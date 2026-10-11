# QnapNarou 0.1.8 — app icon integration

Approved dark-blue book/NAS artwork is retained as `assets/qnapnarou-approved.jpg`.

At QPKG build time, `tools/build_icons.py` derives:
- QDK App Center: `icons/QnapNarou.gif` (64px), `QnapNarou_gray.gif` (64px disabled), `QnapNarou_80.gif` (80px details).
- QTS management portal on port 8889: `apple-touch-icon.png` (180px), `icon-192.png` (192px), `favicon.png` (32px) and a standalone manifest.

To install an iPhone home-screen shortcut **for the QNAP management portal**, open the portal at port 8889 in Safari, Share → Add to Home Screen. If an older shortcut is already installed, remove it and add it again to refresh its icon.

The original upstream Narou Web UI on **port 8888** is unchanged by this icon-only release. Its own Home Screen icon requires an upstream embedded Web asset rebuild and is a separate task; do not misrepresent the 8889 portal icon as changing the 8888 UI.

Packaging happens only during the GitHub/QDK build, using Pillow on the build runner. QTS requires no Pillow, no image conversion service and no new HDD cache/log writes. This release retains the exact verified v0.1.7 native executable with existing EPUB, iPhone download fix and tokenless Web update intact.

The release has three image-format regression tests plus portal-markup checks and a one-shot x86_64 QPKG build. Installed users update via port 8889: Latest → Update. After upgrade QTS App Center may need a refresh to display the new icon.
