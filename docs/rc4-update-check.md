# RC4 — GitHub Releases update check and safe preview downloads

## QTS evidence and root cause

QNAP/iPhone Web manager at port 8889 returned
`Error: HTTP Error 404: Not Found` upon pressing 更新を確認.

The release checker was calling
`https://api.github.com/repos/souten-yd/QnapNarou/releases/latest`,
which only returns **the latest non-prerelease**. On 2026-10-11 the repository
has v0.1.0-rc1, v0.1.1-rc2 and v0.1.2-rc3, all prereleases; therefore
`/releases/latest` returns 404.

## M6 corrective scope

- One button click performs one GitHub Releases list read, limited to 256 KiB.
- Validates tags (`vX.Y.Z` or `vX.Y.Z-rcN`), unique architecture-matched
  QPKG asset, exact repository download URL, size and GitHub SHA-256 digest.
- Selects the highest version; stable wins at equal numeric version and RC
  candidates are sorted by RC number. Draft/malformed/other-architecture
  releases are excluded.
- QTS Web manager displays the installed version, latest available release,
  prerelease indicator, and a link to retrieve the QPKG; **no manually
  configured token or credentials**.
- The existing in-Web automatic installation control remains **disabled**
  while install/rollback/self-restart are not device-qualified.
  In particular, RC packages MUST NOT be silently installed by the
  stable-only installer workflow. Use the QTS App Center for manual
  prerelease package upgrades.
- No startup polling, HDD log writes, direct edits of the novel library,
  or modification of the original Narou UI on port 8888.

## Acceptance

1. Upgrade the QPKG to `v0.1.3-rc4` from QTS App Center.
2. Open `http://<NAS-IP>:8889` and click 最新版を確認.
3. Confirm the page displays installed version `0.1.3`,
   latest release `v0.1.3-rc4`, and "新しいQPKGはありません".
4. Confirm the package download link is present, and neither the
   automatic updater nor installed novel data changes.
5. Confirm `http://<NAS-IP>:8888` continues serving Narou's original
   UI and a previously downloaded EPUB remains accessible.

The codebase still needs a separate QTS-tested, crash-safe, rollback-safe
one-click installer before automatically enabling そのまま更新. Do not
claim that preview download implies a successful QTS in-place upgrade.
