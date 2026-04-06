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
  - cached git branch for that pane when available

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
- Avoids per-refresh git branch lookup in `pane-border-format` by caching branch names in a pane-scoped `@git_branch` option from the shell
- Replaced shell-heavy local username/hostname/root helpers with tmux-native `#{user}` and `#h`
- Battery data is refreshed in the background and written into cached `@battery_*` options
- A small post-load helper reapplies the lightweight `status-right` after the theme initializes

### Multi-agent compact sidebar workflow
- Provides a `wide` mode for horizontal multi-pane viewing
- Provides a `compact` mode with a persistent left sidebar and one focused agent pane
- Uses stable pane registration via `@agent_name_<pane_id>` options
- Sidebar rows display `folder - (branch) - X` when branch / active state are available
- Branch text is rendered in bright yellow, active marker uses colored foreground text, and no background highlight is used
- Compact mode supports direct keyboard selection and mouse click selection in the sidebar
- New managed panes can be created with a derived name from pane path + branch

## Agent layout files

The agent-layout implementation lives in this repo and is linked into `~/.tmux`.
It requires `bash`, `tmux`, and `python3` (for the interactive sidebar UI):

- `tmux/agent-layout.conf`
- `tmux/scripts/agent-layout`
- `tmux/scripts/agent-sidebar.py`

Expected links:

```bash
ln -sfn ~/workspace/configs/tmux/agent-layout.conf ~/.tmux/agent-layout.conf
ln -sfn ~/workspace/configs/tmux/scripts/agent-layout ~/.tmux/scripts/agent-layout
ln -sfn ~/workspace/configs/tmux/scripts/agent-sidebar.py ~/.tmux/scripts/agent-sidebar.py
```

The active local config should remain linked here as well:

```bash
ln -sfn ~/workspace/configs/tmux/.tmux.conf.local ~/.tmux.conf.local
```

`~/.tmux.conf.local` sources `~/.tmux/agent-layout.conf`, so the symlink above is the active entrypoint.

## Helper scripts

The config expects these helper scripts to exist under `~/.tmux/scripts/`:

- `tmux/scripts/tmux-battery-cache.sh`
- `tmux/scripts/tmux-apply-fast-status.sh`
- `tmux/scripts/agent-layout`
- `tmux/scripts/agent-sidebar.py`

Suggested setup:

```bash
mkdir -p ~/.tmux/scripts
ln -sfn ~/workspace/configs/tmux/scripts/tmux-battery-cache.sh ~/.tmux/scripts/tmux-battery-cache.sh
ln -sfn ~/workspace/configs/tmux/scripts/tmux-apply-fast-status.sh ~/.tmux/scripts/tmux-apply-fast-status.sh
ln -sfn ~/workspace/configs/tmux/scripts/agent-layout ~/.tmux/scripts/agent-layout
ln -sfn ~/workspace/configs/tmux/scripts/agent-sidebar.py ~/.tmux/scripts/agent-sidebar.py
ln -sfn ~/workspace/configs/tmux/agent-layout.conf ~/.tmux/agent-layout.conf
```

## Agent layout usage

### Key bindings
- `prefix m` — switch to compact mode
- `prefix M` — switch to wide mode
- `prefix N` — create a new managed pane and auto-label it from pane path / branch
- `prefix a` — focus the sidebar pane
- `prefix x` — kill the current managed pane using the custom compact-aware kill flow
- `prefix ]` / `prefix [` — next / previous agent
- `prefix Down` / `prefix Up` — next / previous agent
- `prefix Tab` — toggle last active agent

### Commands
```bash
~/.tmux/scripts/agent-layout compact
~/.tmux/scripts/agent-layout wide
~/.tmux/scripts/agent-layout new
~/.tmux/scripts/agent-layout kill-current
~/.tmux/scripts/agent-layout focus-sidebar
~/.tmux/scripts/agent-layout focus-right
~/.tmux/scripts/agent-layout register <pane-id> <name>
~/.tmux/scripts/agent-layout list-agents
~/.tmux/scripts/agent-layout snapshot
~/.tmux/scripts/agent-layout cleanup-dead
~/.tmux/scripts/agent-layout refresh
~/.tmux/scripts/agent-layout repair
~/.tmux/scripts/agent-layout status
```

### Compact mode controls
When the sidebar is focused:
- `j` / `k` or arrow keys — move selection
- `Enter` — focus selected agent
- `1..9` — direct switch
- `n` / `p` — next / previous agent
- `Esc` / `q` — return focus to the active pane
- mouse click — switch to clicked agent row
- mouse wheel — move selection

### Notes
- Folder text comes from the pane current path basename.
- Branch text comes from the cached `@git_branch` pane option set by shell hooks in `~/.zshrc`.
- Branch cache updates on both `precmd` and `chpwd`, so directory changes in interactive zsh panes update the sidebar more reliably.
- If compact state gets stale, use:

```bash
~/.tmux/scripts/agent-layout wide
~/.tmux/scripts/agent-layout compact
```

## Reload

```bash
tmux source-file ~/.tmux.conf
```
