# QnapNarou v0.1.10 — QTS restart/cold-boot repair

## User-visible incident
After restarting a QTS 5.x NAS, the local Narou Web UI and QNAP
management interface stopped responding. The existing service only checks
once (after 1 second), and unconditionally aborts at module import when
Python /opt or the installation volume is not ready.

The real NAS startup logs have not yet been provided: the timing race is
**a supported codebase defect and plausible cause**, but the specific QTS
incident cannot be conclusively attributed without device logs.

## Behavior
- QTS service `start` first tries a normal startup.
- If dependencies are not ready, one bounded background worker retries up
  to 24 times with five-second gaps. It returns control to QTS immediately
  rather than blocking NAS startup for minutes.
- Each try re-reads QTS Install_Path and checks that the runtime, Python,
  the Web manager and configuration utilities exist before touching data.
- The existing home/library directory and settings are preserved; initial
  Narou setup is still only for a new library. WebSocket port 8889 conflict
  fixes and LAN settings remain in place.
- Success requires **both** :8888 and :8889 listeners and their expected
  processes, not a one-second PID check.
- Only one retry worker is permitted; status reports `starting`, `running`,
  or `stopped`. A diagnostic file in `/var/run/qpkg-narou-boot-status`
  records the last startup state in NAS memory only.
- `stop` cancels pending startup and waits for it to exit. No unbounded
  daemon, reboot polling, scheduled disk writes or signature bypass.

## Restore an affected NAS now
From QTS App Center, choose **Start** for QnapNarou. If it fails,
connect using SSH and run:

```sh
APP_DIR="$(/sbin/getcfg QnapNarou Install_Path -f /etc/config/qpkg.conf)"
/bin/sh "$APP_DIR/QnapNarou.sh" start
/bin/sh "$APP_DIR/QnapNarou.sh" status
/sbin/getcfg QnapNarou Enable -f /etc/config/qpkg.conf
```

For v0.1.10, inspect `cat /var/run/qpkg-narou-boot-status` after a
cold boot. Check that QTS App Center keeps the package enabled.

**No logs or untested diagnostic dumps are sent out automatically.**

## Validation and remaining limits
- Shell syntax and isolated-host cold-boot simulation: QPKG storage becomes
  available late; service starts both ports; stop prevents a late restart.
- Python regression tests, QDK staging and unchanged GPL native runtime.
- QTS firmware-specific service ordering and a real NAS reboot **must be
  verified after installing v0.1.10**. A disabled app or changed NAS address
  will not be fixed by the retry worker.
- No changes to EPUB bytes, iPhone Home Screen icons, Web updater or user
  library. QPKG can use the verified v0.1.9 Rust binary without rebuilding.
