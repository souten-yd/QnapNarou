# M3 QNAP web management (prototype)

QTS opens the management landing page at port **8889**. The original upstream
narou.rs Web UI remains unmodified and is linked at **8888**.

The QPKG bundle includes `manager.py`, `installer.py`, and
`update_check.py` (Python standard library only). Runtime Python 3 is
**not embedded yet**: /opt/bin/python3.11 from Entware or a compatible
Python installation is currently required on the NAS. A self-contained
release must resolve this dependency or bundle its interpreter.

## No user token

- The user clicks **最新版を確認** to fetch public QnapNarou Releases.
- The user clicks **最新版へ更新** after a version is found.
- The browser receives a nonce automatically; no manual token setup.
- No automatic nightly checks, package downloads, install, or CI runs.
- The management service rejects public client IPs and enforces same-origin
  requests. No username/password authentication exists: any trusted LAN or
  Tailscale client can use the update button. This is a deliberate local-use
  tradeoff, NOT a WAN-safe admin service.

## QPKG update constraints

The worker only accepts public assets from souten-yd/QnapNarou Releases,
requires a stable newer version and matching architecture, checks the
GitHub-provided SHA-256 digest and exact size, and stages an independent
prior-version package for rollback. Without an accessible prior release,
it refuses to upgrade. It uses QTS `/sbin/qpkg_cli -m` to install.
The normal QTS package signing policy still applies; no silent
`-A 1` signature-policy bypass is used.

GitHub's asset digest guards against corruption/tampering relative to the
GitHub API response, but is not an independent developer signing certificate.
This needs its own trust review before a production release.

The worker is detached from the service being upgraded, and only the
application package is replaced. Novel files and credentials stay in
`QnapNarou-data`. The update process still needs real QTS tests for
power failure, repeated upgrades, failed install, rollback and service restart.
The presence of code does **not** prove those scenarios work.

## Network isolation

On first initialization, the upstream Web UI is configured to bind all
interfaces with external Basic authentication disabled, matching the
requested trusted-LAN-only workflow. Ports 8888 and 8889 MUST NOT be
forwarded to the public Internet. QNAP's own firewall, NAT and Tailscale ACLs
must enforce network isolation. This setup is not suitable for an
untrusted shared LAN without further authentication.

The QNAP service exports `NAROU_RS_DISABLE_SELF_UPDATE=1` so the upstream
updater cannot replace binaries outside QPKG package verification. User
settings must not be overwritten on subsequent launches.

## Release asset naming

Version `0.1.0` for x86_64 must use:

```
QnapNarou_x86_64_0.1.0.qpkg
```

The ARM64 flavor uses `QnapNarou_arm_64_<version>.qpkg` and requires a
native ARM64 QPKG build. QDK's default generated filename must be normalized
by the release build, not by the manager.

QPKG distributions have not been qualified on QTS 5.x; keep this PR draft.
