# tmux config

This repo uses [gpakosz/.tmux](https://github.com/gpakosz/.tmux) as the base config and keeps local overrides in `tmux/.tmux.conf.local`.

## Features enabled in this config

### Terminal integration
- `tmux-256color` when available
- Ghostty extended key support via:
  - `set -s extended-keys always`
  - `set -s extended-keys-format csi-u`
  - `set -as terminal-features 'xterm-ghostty*:extkeys'`
  - `set -as terminal-features 'ghostty*:extkeys'`

### Navigation and mouse
- Mouse mode enabled
- Wheel scroll enters copy mode when needed
- Native tmux copy-mode scrolling restored (no smooth-scroll plugin)
- Copy mode keeps custom `C-a` previous-word binding

### Visual tweaks
- Double pane borders
- Highlighted active pane border
- Pane border status shown at the bottom
- Pane border text shows:
  - pane index
  - current pane path

### Status line
- gpakosz theme base retained
- Status refresh interval increased to 15 seconds to reduce jitter
- Right status shows:
  - prefix / mouse / pairing / synchronized indicators
  - cached battery status, bar, and percentage
  - time and date
  - local tmux user
  - short hostname

### Performance-oriented changes
- Removed per-refresh git branch lookup from `pane-border-format`
- Replaced shell-heavy local username/hostname/root helpers with tmux-native `#{user}` and `#h`
- Battery data is refreshed in the background and written into cached `@battery_*` options
- A small post-load helper reapplies the lightweight `status-right` after the theme initializes

## Helper scripts

The config expects these helper scripts to exist under `~/.tmux/scripts/`:

- `tmux/scripts/tmux-battery-cache.sh`
- `tmux/scripts/tmux-apply-fast-status.sh`

Suggested setup:

```bash
mkdir -p ~/.tmux/scripts
ln -sfn ~/workspace/configs/tmux/scripts/tmux-battery-cache.sh ~/.tmux/scripts/tmux-battery-cache.sh
ln -sfn ~/workspace/configs/tmux/scripts/tmux-apply-fast-status.sh ~/.tmux/scripts/tmux-apply-fast-status.sh
```

## Reload

```bash
tmux source-file ~/.tmux.conf
```
