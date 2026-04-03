#!/bin/sh
set -eu

tmux set-option -g status-right ' #{?@battery_status,#{@battery_status},}#{?@battery_bar, #{@battery_bar},}#{?@battery_percentage, #{@battery_percentage},} | %R | %d %b | #{user} | #h '

# Redraw status for attached clients so the cheaper format is visible
# immediately after a reload.
tmux list-clients -F '#{client_tty}' 2>/dev/null | while IFS= read -r client; do
  [ -n "$client" ] || continue
  tmux refresh-client -S -t "$client" 2>/dev/null || true
done
