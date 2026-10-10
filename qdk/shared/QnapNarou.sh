#!/bin/sh
# QTS service entrypoint. Never truncate logs or touch novel data on idle polling.
set -eu
APP=QnapNarou
GETCFG=/sbin/getcfg
QPKG_CONF=/etc/config/qpkg.conf
INSTALL="$("$GETCFG" "$APP" Install_Path -f "$QPKG_CONF")"
[ -n "$INSTALL" ] && [ -d "$INSTALL" ] || exit 1
BIN="$INSTALL/runtime/narou_rs"
[ -x "$BIN" ] || exit 1
# Data outside the app package; QPKG replacement must never overwrite it.
DATA="$(dirname "$INSTALL")/QnapNarou-data"
HOME_DIR="$DATA/home"
LIBRARY="$DATA/library"
PIDFILE="/var/run/qpkg-narou.pid"
PORT="${NAROU_PORT:-8888}"
case "$PORT" in *[!0-9]*|"") exit 1;; esac
case "$PORT" in 0) exit 1;; esac
[ "$PORT" -le 65535 ] || exit 1
is_running() {
  [ -f "$PIDFILE" ] || return 1
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  case "$pid" in *[!0-9]*|"") return 1;; esac
  [ -r "/proc/$pid/cmdline" ] || return 1
  tr '\000' ' ' <"/proc/$pid/cmdline" | grep -F -q "$BIN"
}
start() {
  if is_running; then return 0; fi
  mkdir -p "$HOME_DIR" "$LIBRARY"
  export HOME="$HOME_DIR"
  cd "$LIBRARY"
  if [ ! -d .narou ]; then "$BIN" init >/dev/null 2>&1 || return 1; fi
  # Preserve upstream security defaults: LAN binding needs explicit
  # upstream authentication and server-bind setup by the operator.
  "$BIN" web --port "$PORT" --no-browser >/dev/null 2>&1 &
  echo "$!" >"$PIDFILE"
  sleep 1
  if is_running; then return 0; fi
  rm -f "$PIDFILE"
  return 1
}
stop() {
  if ! is_running; then rm -f "$PIDFILE"; return 0; fi
  pid="$(cat "$PIDFILE")"
  kill "$pid" 2>/dev/null || true
  i=0
  while [ "$i" -lt 15 ] && kill -0 "$pid" 2>/dev/null; do
    sleep 1; i=$((i + 1))
  done
  if is_running; then
    echo "Process did not stop cleanly; refusing forced kill to protect data" >&2
    return 1
  fi
  rm -f "$PIDFILE"
}
case "${1:-}" in
  start) start;;
  stop) stop;;
  restart) stop && start;;
  status) if is_running; then echo "running"; else echo "stopped"; exit 1; fi;;
  *) echo "Usage: $0 {start|stop|restart|status}" >&2; exit 2;;
esac
