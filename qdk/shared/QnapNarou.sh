#!/bin/sh
# QTS lifecycle; novel library and user settings survive QPKG replacement.
set -eu
APP=QnapNarou
CONF=/etc/config/qpkg.conf
INSTALL="$(/sbin/getcfg "$APP" Install_Path -f "$CONF")"
[ -n "$INSTALL" ] && [ -d "$INSTALL" ] || exit 1
BIN="$INSTALL/runtime/narou_rs"
[ -x "$BIN" ] || exit 1
DATA="$(dirname "$INSTALL")/QnapNarou-data"
HOME_DIR="$DATA/home"
LIBRARY="$DATA/library"
PIDFILE="/var/run/qpkg-narou.pid"
MANAGER_PIDFILE="/var/run/qpkg-narou-manager.pid"
PORT="$(printenv NAROU_PORT 2>/dev/null || printf 8888)"
MANAGER_PORT=8889
case "$PORT" in *[!0-9]*|"") exit 1;; esac
[ "$PORT" -gt 0 ] && [ "$PORT" -le 65535 ] || exit 1
[ "$PORT" != "$MANAGER_PORT" ] || exit 1
PYTHON=""
for candidate in /opt/bin/python3.11 /opt/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [ -x "$candidate" ]; then PYTHON="$candidate"; break; fi
done
[ -n "$PYTHON" ] || { echo "Python 3 required for updater manager" >&2; exit 1; }
[ -f "$INSTALL/manager.py" ] && [ -f "$INSTALL/installer.py" ] && [ -f "$INSTALL/update_check.py" ] || exit 1

is_running() {
  file="$1"; expected="$2"
  [ -f "$file" ] || return 1
  pid="$(cat "$file" 2>/dev/null || true)"
  case "$pid" in *[!0-9]*|"") return 1;; esac
  [ -r "/proc/$pid/cmdline" ] || return 1
  tr '\000' ' ' <"/proc/$pid/cmdline" | grep -F -q "$expected"
}
start() {
  if is_running "$PIDFILE" "$BIN" && is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py"; then return 0; fi
  mkdir -p "$HOME_DIR" "$LIBRARY"
  export HOME="$HOME_DIR"
  export NAROU_DATA="$DATA"
  # Keep upstream UI but block its own binary replacement. QPKG updates only.
  export NAROU_RS_DISABLE_SELF_UPDATE=1
  cd "$LIBRARY"
  # First install only: QTS LAN / Tailscale access without manual credentials.
  # WAN exposure of ports 8888 and 8889 must be prohibited by the NAS firewall.
  if [ ! -d .narou ]; then
    "$BIN" init >/dev/null 2>&1 || return 1
    "$BIN" setting server-bind=0.0.0.0 >/dev/null 2>&1 || return 1
    "$BIN" setting server-basic-auth.require-for-external-bind=false >/dev/null 2>&1 || return 1
    "$BIN" setting logging=false >/dev/null 2>&1 || return 1
  fi
  if ! is_running "$PIDFILE" "$BIN"; then
    "$BIN" web --port "$PORT" --no-browser >/dev/null 2>&1 &
    echo "$!" >"$PIDFILE"
  fi
  if ! is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py"; then
    "$PYTHON" "$INSTALL/manager.py" --port "$MANAGER_PORT" >/dev/null 2>&1 &
    echo "$!" >"$MANAGER_PIDFILE"
  fi
  sleep 1
  if is_running "$PIDFILE" "$BIN" && is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py"; then
    return 0
  fi
  echo "QnapNarou startup failed; check Python, Web bind and port conflicts" >&2
  stop || true
  return 1
}
stop_one() {
  file="$1"; expected="$2"
  if ! is_running "$file" "$expected"; then rm -f "$file"; return 0; fi
  pid="$(cat "$file")"
  kill "$pid" 2>/dev/null || true
  i=0
  while [ "$i" -lt 15 ] && is_running "$file" "$expected"; do
    sleep 1; i=$((i + 1))
  done
  if is_running "$file" "$expected"; then
    echo "Unable to stop $expected cleanly; refusing forced kill" >&2
    return 1
  fi
  rm -f "$file"
}
stop() {
  stop_one "$MANAGER_PIDFILE" "$INSTALL/manager.py" || return 1
  stop_one "$PIDFILE" "$BIN"
}
[ "$#" -eq 1 ] || { echo "Usage: $0 {start|stop|restart|status}" >&2; exit 2; }
case "$1" in
  start) start;;
  stop) stop;;
  restart) stop && start;;
  status) if is_running "$PIDFILE" "$BIN" && is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py"; then echo "running"; else echo "stopped"; exit 1; fi;;
  *) echo "Usage: $0 {start|stop|restart|status}" >&2; exit 2;;
esac
