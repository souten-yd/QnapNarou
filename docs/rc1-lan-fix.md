# RC1 LAN access failure: Narou HTTP :8888 does not start

## Root cause

QnapNarou 0.1.0's QTS management UI listens at port 8889.
The pinned upstream narou.rs Web UI listens at port 8888 and, unless
`server-ws-port` is set, creates a **separate** WebSocket listener on
`8888 + 1 = 8889`. Because 8889 is already reserved by the QNAP manager,
Narou can exit during startup. With logs redirected to /dev/null, the
management page still loads but :8888 reports connection failure.

Additional issue: when upstream binds 0.0.0.0, its HTTP Host and WebSocket
Origin allowlists do not automatically contain the NAS's LAN IP. A server
that starts can reject requests from Safari until the local IP is added.

## RC2 fix

- `ensure_ws.sh` configures `server-ws-port=0` on startup when unset
  or equal to the QNAP management port. This puts WebSocket at `/ws`
  on the existing :8888 HTTP listener.
- `configure_hosts.py` reads the NAS's local interface IP addresses
  through Linux ioctl (read only), and adds private LAN and Tailscale
  interface addresses to both upstream allowlists, without overwriting
  operator-managed entries. Saves only if values actually change.
- Both fixes run for **existing installations** as well as first run.
- QNAP manager :8889 adds a one-click **サーバー状態を確認** button.
- No Rust runtime changes, no new dependency, no new background polling,
  and no changes to novel data or SQLite durability.

## One-time repair for installed RC1, without a reinstall

From SSH on the QNAP NAS:

```sh
APP=$(/sbin/getcfg QnapNarou Install_Path -f /etc/config/qpkg.conf)
DATA="$(dirname "$APP")/QnapNarou-data"
cd "$DATA/library" || exit 1
HOME="$DATA/home" "$APP/runtime/narou_rs" setting server-ws-port=0
```

Stop and start QnapNarou from QTS. Then visit
`http://<NAS-LAN-IP>:8888/`. If the server returns 403 / Forbidden
instead of refusing the connection, install RC2 to correct its interface
allowlists, or add the NAS LAN address manually to both upstream settings.

## Remaining validation

Run `python3 -m unittest discover -s tests -v` and `sh -n` checks,
then generate x86_64 QPKG. Install/test on actual QTS 5.x, including
iPhone Safari and existing library persistence. Do not mark a stable
release until these checks pass.
