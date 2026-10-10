#!/bin/sh
# QnapNarou reserves 8889 for its management UI. narou.rs defaults the
# WebSocket listener to HTTP_PORT+1, which also resolves to 8889.
# Reading the effective setting through the CLI covers SQLite-backed configs.
# Only alter the absent or conflicting value; preserve explicit other ports.
set -eu
[ "$#" -eq 2 ] || exit 2
binary="$1"
reserved_port="$2"
[ -x "$binary" ] || exit 1
case "$reserved_port" in ""|*[!0-9]*) exit 2;; esac
current="$("$binary" setting server-ws-port)" || exit 1
current="$(printf '%s' "$current" | tr -d '\r\n[:space:]')"
case "$current" in
  ""|"$reserved_port")
    "$binary" setting server-ws-port=0 >/dev/null || exit 1
    ;;
  0)
    ;;
  *)
    # An explicit non-conflicting port belongs to the existing user.
    ;;
esac
