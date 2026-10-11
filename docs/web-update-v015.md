# v0.1.5 Web QPKG updater — local-only, stable releases

## Quick start

The QTS App Center must install v0.1.5 once because v0.1.4's POST
/api/install handler is deliberately disabled. From **the next stable release
onwards**, click **最新版を確認**, then **最新版へ更新** on port 8889.
No manual token, password, SSH, Docker or scheduled polling.

This is intended only for trusted LAN / Tailscale access. Never port-forward
8888 or 8889 to the public Internet. A random nonce and same-origin browser
header prevent cross-site POSTs without involving the user.

## Verified update flow

1. Discover releases **on demand** from the public GitHub API. Only strictly
   newer **stable** versions are eligible for one-click install; RC is manual.
2. A separate updater process, launched by the manager, performs an
   independent stable-only release lookup and retrieves the **installed stable
   version** package for rollback from its exact version tag.
3. Before installing, obtain both old and new QPKGs into QnapNarou-data/updates,
   validating allowed download host/redirect, exact asset name/size and
   GitHub-published SHA-256 digest. Files cannot be reused or symlinked.
4. Call /sbin/qpkg_cli -m QPKG -q -K. QTS's own package signing policy is
   enforced: no -A signature-policy bypass is used.
5. Wait for QTS to register the new version and for both port 8888 (Narou)
   and port 8889 (QNAP manager) to listen. Try the QTS service start once
   if necessary. If checks fail, reinstall the verified prior QPKG and
   verify recovery. Report failures explicitly; never claim success simply
   because qpkg_cli returned zero.
6. Status is stored only in /dev/shm/QnapNarou and polled by the browser
   only while an update is running. There is no idle status polling.
   Staged QPKGs are removed after completion or failure.
7. QnapNarou-data/library, novels, SQLite, settings and credentials are never
   deleted by this updater.

### Limits and qualification

The command path is covered by unit tests with simulated package installs,
checksum corruption, version mismatches, rollback and duplicate updates.
An actual QTS **Web-triggered** in-place upgrade has not yet been performed
and must be confirmed by the NAS operator. A power failure during QTS's
own QPKG installation cannot be made atomic by this Python wrapper alone.
Manual NAS backup before the first trial remains recommended.

The updater requires a QTS installation capable of installing the same
unsigned community QPKG with the current QTS signature policy. If the CLI
refuses the QPKG, the update is reported as failed; do not silently override
the NAS signature policy.

Only x86_64 QPKGs have been built and checked. Current embedded GPL EPUB
engine, iPhone navigation overlay, upstream pin, and original Narou UI remain
unchanged.

## No full Rust rebuild

The v0.1.5 release job extracts the previously SHA-256 validated v0.1.4
QPKG, locates its entire runtime tree, verifies the binary/EPUB asset
payload, then builds a new QDK QPKG with the updated manager, installer,
release-checker and v0.1.5 metadata. The native binary is byte-identical
to v0.1.4, avoiding another costly Rust compile.
