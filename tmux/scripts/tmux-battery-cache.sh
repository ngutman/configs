#!/bin/sh
set -eu

CACHE_DIR="${TMPDIR:-/tmp}/tmux-status-cache-$UID"
INTERVAL="${TMUX_BATTERY_CACHE_INTERVAL:-60}"

mkdir -p "$CACHE_DIR"

resolve_socket_path() {
  if [ -n "${TMUX:-}" ]; then
    socket_path=${TMUX%%,*}
    if [ -n "$socket_path" ]; then
      printf '%s\n' "$socket_path"
      return 0
    fi
  fi

  tmux display-message -p '#{socket_path}' 2>/dev/null || true
}

SOCKET_PATH="$(resolve_socket_path)"
if [ -z "$SOCKET_PATH" ]; then
  exit 0
fi

SOCKET_KEY="$(printf '%s' "$SOCKET_PATH" | tr '/: ' '___')"
LOCK_DIR="$CACHE_DIR/battery.lock.$SOCKET_KEY"
PIDFILE="$LOCK_DIR/pid"
sleep_pid=""

get_server_pid() {
  tmux -S "$SOCKET_PATH" display-message -p '#{pid}' 2>/dev/null || true
}

cleanup() {
  if [ -n "${sleep_pid:-}" ]; then
    kill "$sleep_pid" 2>/dev/null || true
  fi
  rm -rf "$LOCK_DIR"
}

acquire_lock() {
  attempt=0
  while [ "$attempt" -lt 2 ]; do
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      printf '%s\n' "$$" > "$PIDFILE"
      return 0
    fi

    pid=""
    if [ -f "$PIDFILE" ]; then
      pid="$(cat "$PIDFILE" 2>/dev/null || true)"
    fi
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      return 1
    fi

    rm -rf "$LOCK_DIR" 2>/dev/null || true
    attempt=$((attempt + 1))
  done

  return 1
}

acquire_lock || exit 0
trap cleanup EXIT INT TERM HUP

OWNER_PID="$(get_server_pid)"
if [ -z "$OWNER_PID" ]; then
  exit 0
fi

tmux_cmd() {
  tmux -S "$SOCKET_PATH" "$@"
}

set_battery_vars() {
  status="$1"
  percentage="$2"
  bar="$3"
  tmux_cmd set-option -gq @battery_status "$status"
  tmux_cmd set-option -gq @battery_percentage "$percentage"
  tmux_cmd set-option -gq @battery_bar "$bar"
}

clear_battery_vars() {
  tmux_cmd set-option -gu @battery_status 2>/dev/null || true
  tmux_cmd set-option -gu @battery_percentage 2>/dev/null || true
  tmux_cmd set-option -gu @battery_bar 2>/dev/null || true
}

build_bar() {
  pct="$1"
  filled=$(( (pct + 9) / 20 ))
  if [ "$filled" -gt 5 ]; then
    filled=5
  fi
  empty=$(( 5 - filled ))

  bar=""
  i=0
  while [ "$i" -lt "$filled" ]; do
    bar="${bar}◼"
    i=$(( i + 1 ))
  done
  i=0
  while [ "$i" -lt "$empty" ]; do
    bar="${bar}◻"
    i=$(( i + 1 ))
  done
  printf '%s' "$bar"
}

update_once() {
  current_pid="$(get_server_pid)"
  if [ -z "$current_pid" ] || [ "$current_pid" != "$OWNER_PID" ]; then
    return 1
  fi

  if ! command -v pmset >/dev/null 2>&1; then
    clear_battery_vars
    return 0
  fi

  line="$(pmset -g batt 2>/dev/null | awk '/InternalBattery/ { print; exit }')"
  if [ -z "$line" ]; then
    clear_battery_vars
    return 0
  fi

  pct="$(printf '%s' "$line" | grep -Eo '[0-9]+%' | head -1 | tr -d '%')"
  if [ -z "$pct" ]; then
    clear_battery_vars
    return 0
  fi

  case "$line" in
    *discharging*|*Discharging*) status='↓' ;;
    *) status='↑' ;;
  esac

  bar="$(build_bar "$pct")"
  set_battery_vars "$status" "${pct}%" "$bar"
}

while :; do
  current_pid="$(get_server_pid)"
  if [ -z "$current_pid" ] || [ "$current_pid" != "$OWNER_PID" ]; then
    break
  fi

  update_once || break

  sleep "$INTERVAL" &
  sleep_pid=$!
  wait "$sleep_pid"
  sleep_pid=""
done
