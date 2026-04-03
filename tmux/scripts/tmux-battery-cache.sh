#!/bin/sh
set -eu

CACHE_DIR="${TMPDIR:-/tmp}/tmux-status-cache-$UID"
PIDFILE="$CACHE_DIR/battery.pid"
INTERVAL="${TMUX_BATTERY_CACHE_INTERVAL:-60}"

mkdir -p "$CACHE_DIR"

cleanup() {
  rm -f "$PIDFILE"
}

if [ -f "$PIDFILE" ]; then
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    exit 0
  fi
fi

echo $$ > "$PIDFILE"
trap cleanup EXIT INT TERM HUP

set_battery_vars() {
  status="$1"
  percentage="$2"
  bar="$3"
  tmux set-option -gq @battery_status "$status"
  tmux set-option -gq @battery_percentage "$percentage"
  tmux set-option -gq @battery_bar "$bar"
}

clear_battery_vars() {
  tmux set-option -gu @battery_status 2>/dev/null || true
  tmux set-option -gu @battery_percentage 2>/dev/null || true
  tmux set-option -gu @battery_bar 2>/dev/null || true
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
  if ! command -v pmset >/dev/null 2>&1; then
    clear_battery_vars
    return
  fi

  line="$(pmset -g batt 2>/dev/null | awk '/InternalBattery/ { print; exit }')"
  if [ -z "$line" ]; then
    clear_battery_vars
    return
  fi

  pct="$(printf '%s' "$line" | grep -Eo '[0-9]+%' | head -1 | tr -d '%')"
  if [ -z "$pct" ]; then
    clear_battery_vars
    return
  fi

  case "$line" in
    *discharging*|*Discharging*) status='↓' ;;
    *) status='↑' ;;
  esac

  bar="$(build_bar "$pct")"
  set_battery_vars "$status" "${pct}%" "$bar"
}

while :; do
  if tmux start-server >/dev/null 2>&1; then
    update_once || true
  fi
  sleep "$INTERVAL"
done
