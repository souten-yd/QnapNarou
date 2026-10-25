#!/bin/sh
# QTS lifecycle: bounded, memory-only cold-boot retries. Novel data is never deleted.
set -eu
APP=QnapNarou
CONF=/etc/config/qpkg.conf
PIDFILE=/var/run/qpkg-narou.pid
MANAGER_PIDFILE=/var/run/qpkg-narou-manager.pid
BOOT_DIR=/var/run/qpkg-narou-boot-retry
BOOT_REPORT=/var/run/qpkg-narou-boot-status
BOOT_STOP=/var/run/qpkg-narou-boot-stop
MANAGER_PORT=8889
PORT="$(printenv NAROU_PORT 2>/dev/null || printf 8888)"
case "$PORT" in *[!0-9]*|"") exit 1;; esac
[ "$PORT" -gt 0 ] && [ "$PORT" -le 65535 ] && [ "$PORT" != "$MANAGER_PORT" ] || exit 1

# All package paths and the Python dependency are checked at START time,
# never at top-level: QTS can invoke stop/status before /opt and shared
# volumes are mounted, and a boot-time start may be earlier than Entware.
INSTALL=""
BIN=""
DATA=""
HOME_DIR=""
LIBRARY=""
PYTHON=""
BOOT_REASON="prerequisites pending"

memory_status() {
  # /var/run is the NAS memory-backed runtime filesystem (not the novel HDD).
  printf '%s\n' "$1" >"$BOOT_REPORT" 2>/dev/null || true
}

resolve_ready() {
  INSTALL="$(/sbin/getcfg "$APP" Install_Path -f "$CONF" 2>/dev/null || true)"
  if [ -z "$INSTALL" ] || [ ! -d "$INSTALL" ]; then
    BOOT_REASON="waiting for QPKG install volume"
    return 1
  fi
  BIN="$INSTALL/runtime/narou_rs"
  if [ ! -x "$BIN" ]; then
    BOOT_REASON="waiting for QPKG native runtime"
    return 1
  fi
  DATA="$(dirname "$INSTALL")/QnapNarou-data"
  HOME_DIR="$DATA/home"
  LIBRARY="$DATA/library"
  for file in manager.py installer.py update_check.py configure_hosts.py ensure_ws.sh; do
    if [ ! -f "$INSTALL/$file" ]; then
      BOOT_REASON="waiting for QPKG file $file"
      return 1
    fi
  done
  PYTHON=""
  for candidate in /opt/bin/python3.11 /opt/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [ -x "$candidate" ] &&
        "$candidate" -c 'import fcntl, json, socket, urllib.request' >/dev/null 2>&1; then
      PYTHON="$candidate"
      break
    fi
  done
  if [ -z "$PYTHON" ]; then
    BOOT_REASON="waiting for Python 3 /opt readiness"
    return 1
  fi
  return 0
}

is_running() {
  file="$1"; expected="$2"
  [ -f "$file" ] || return 1
  pid="$(cat "$file" 2>/dev/null || true)"
  case "$pid" in *[!0-9]*|"") return 1;; esac
  [ -r "/proc/$pid/cmdline" ] || return 1
  tr '\000' ' ' <"/proc/$pid/cmdline" | grep -F -q "$expected"
}

ports_ready() {
  # Check real TCP listeners, not just surviving PID files.
  "$PYTHON" -c 'import socket,sys
for p in map(int,sys.argv[1:]):
 s=socket.socket()
 s.settimeout(0.6)
 try: s.connect(("127.0.0.1",p))
 except OSError: sys.exit(1)
 finally: s.close()' "$PORT" "$MANAGER_PORT" >/dev/null 2>&1
}

start_once() {
  if ! resolve_ready; then return 1; fi
  if is_running "$PIDFILE" "$BIN" &&
     is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py" &&
     ports_ready; then
    BOOT_REASON="running: Narou $PORT and QTS $MANAGER_PORT"
    return 0
  fi

  # Only initialize a brand-new library when the QPKG volume is mounted.
  # Existing settings, SQLite, downloaded novels and images are untouched.
  mkdir -p "$HOME_DIR" "$LIBRARY" || {
    BOOT_REASON="novel library volume is not writable"; return 1;
  }
  export HOME="$HOME_DIR"
  export NAROU_DATA="$DATA"
  export NAROU_RS_DISABLE_SELF_UPDATE=1
  export PYTHONDONTWRITEBYTECODE=1
  cd "$LIBRARY" || { BOOT_REASON="novel library not mounted"; return 1; }
  if [ ! -d .narou ]; then
    "$BIN" init >/dev/null 2>&1 || { BOOT_REASON="Narou initialization pending"; return 1; }
    "$BIN" setting server-bind=0.0.0.0 >/dev/null 2>&1 || return 1
    "$BIN" setting server-basic-auth.require-for-external-bind=false >/dev/null 2>&1 || return 1
    "$BIN" setting logging=false >/dev/null 2>&1 || return 1
  fi
  "$INSTALL/ensure_ws.sh" "$BIN" "$MANAGER_PORT" >/dev/null 2>&1 || {
    BOOT_REASON="Narou WebSocket configuration failed"; return 1;
  }
  "$PYTHON" "$INSTALL/configure_hosts.py" "$BIN" >/dev/null 2>&1 || {
    BOOT_REASON="Narou LAN host configuration failed"; return 1;
  }
  if ! is_running "$PIDFILE" "$BIN"; then
    "$BIN" web --port "$PORT" --no-browser </dev/null >/dev/null 2>&1 &
    echo "$!" >"$PIDFILE"
  fi
  if ! is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py"; then
    "$PYTHON" "$INSTALL/manager.py" --port "$MANAGER_PORT" </dev/null >/dev/null 2>&1 &
    echo "$!" >"$MANAGER_PIDFILE"
  fi
  # Cold SSD/HDD and Python mounts can delay listen() beyond the old 1s check.
  retries=0
  while [ "$retries" -lt 4 ]; do
    if is_running "$PIDFILE" "$BIN" &&
       is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py" &&
       ports_ready; then
      BOOT_REASON="running: Narou $PORT and QTS $MANAGER_PORT"
      return 0
    fi
    retries=$((retries + 1))
    sleep 2
  done
  BOOT_REASON="waiting for both QTS Web services to listen"
  return 1
}

boot_cleanup() {
  rm -f "$BOOT_DIR/pid" 2>/dev/null || true
  rmdir "$BOOT_DIR" 2>/dev/null || true
}

boot_retry() {
  # Background helper created only by start(). Bounded: 24 attempts max,
  # five-second delay, and no periodic process left running once healthy.
  trap 'boot_cleanup' EXIT
  trap 'exit 0' TERM INT
  count=0
  while [ "$count" -lt 24 ]; do
    [ ! -e "$BOOT_STOP" ] || return 0
    if start_once; then
      memory_status "$BOOT_REASON"
      return 0
    fi
    memory_status "retry $((count + 1))/24: $BOOT_REASON"
    count=$((count + 1))
    sleep 5
  done
  memory_status "startup timed out: $BOOT_REASON; use App Center to restart"
  return 1
}

retry_active() {
  [ -r "$BOOT_DIR/pid" ] || return 1
  pid="$(cat "$BOOT_DIR/pid" 2>/dev/null || true)"
  case "$pid" in *[!0-9]*|"") return 1;; esac
  kill -0 "$pid" 2>/dev/null
}

schedule_retry() {
  if [ -d "$BOOT_DIR" ]; then
    if retry_active; then return 0; fi
    # A crashed helper cannot block later manual start/reboot attempts.
    rm -f "$BOOT_DIR/pid" 2>/dev/null || true
    rmdir "$BOOT_DIR" 2>/dev/null || true
  fi
  if mkdir "$BOOT_DIR" 2>/dev/null; then
    /bin/sh "$0" boot-retry </dev/null >/dev/null 2>&1 &
    echo "$!" >"$BOOT_DIR/pid"
    memory_status "starting in background: $BOOT_REASON"
    return 0
  fi
  retry_active
}

start() {
  rm -f "$BOOT_STOP" 2>/dev/null || true
  if start_once; then
    memory_status "$BOOT_REASON"
    return 0
  fi
  # Returning promptly lets QTS finish booting /opt while the bounded
  # retry worker waits. No unbounded polling or persistent HDD log.
  schedule_retry || { memory_status "unable to schedule startup: $BOOT_REASON"; return 1; }
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
    echo "Unable to stop $expected cleanly" >&2
    return 1
  fi
  rm -f "$file"
}

stop() {
  # Cancel delayed start and wait for the worker to exit before stopping
  # services. This avoids a race where Stop is followed by a late boot retry.
  : >"$BOOT_STOP"
  if retry_active; then
    kill "$(cat "$BOOT_DIR/pid")" 2>/dev/null || true
    i=0
    while [ "$i" -lt 12 ] && retry_active; do
      sleep 1
      i=$((i + 1))
    done
    if retry_active; then
      memory_status "cold-boot worker did not exit; refusing unsafe stop"
      return 1
    fi
  fi
  resolve_ready || true
  if [ -n "$INSTALL" ]; then
    stop_one "$MANAGER_PIDFILE" "$INSTALL/manager.py" || return 1
    if [ -n "$BIN" ]; then stop_one "$PIDFILE" "$BIN" || return 1; fi
  fi
  memory_status "stopped"
}

status() {
  if resolve_ready &&
     is_running "$PIDFILE" "$BIN" &&
     is_running "$MANAGER_PIDFILE" "$INSTALL/manager.py" &&
     ports_ready; then echo "running"; return 0; fi
  if retry_active; then
    echo "starting (bounded cold-boot retry)"
    return 0
  fi
  echo "stopped"
  [ ! -r "$BOOT_REPORT" ] || cat "$BOOT_REPORT"
  return 1
}

[ "$#" -eq 1 ] || { echo "Usage: $0 {start|stop|restart|status|boot-retry}" >&2; exit 2; }
case "$1" in
  start) start;;
  stop) stop;;
  restart) stop && start;;
  status) status;;
  boot-retry) boot_retry;;
  *) echo "Usage: $0 {start|stop|restart|status}" >&2; exit 2;;
esac
