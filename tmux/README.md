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
  - Pi pane activity indicator when available (`[·]` waiting, `[●]` running, `[⚙]` tool, `[✓]` finished, `[✗]` errored)
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
- Packaged as a local tmux plugin under `tmux/plugins/tmux-agents-sidebar`
- Provides a `wide` mode for horizontal multi-pane viewing
- Provides a `compact` mode with a persistent left sidebar and one focused pane
- In compact mode, inactive panes are parked in a detached tmux store session instead of visible helper windows in the main session
- Splits the sidebar into `Agents` and `Panes` sections
- Uses stable pane registration via `@agents_sidebar_name_<pane_id>` plus per-pane metadata for `kind`, `provider`, and `status`
- Detects coding agents heuristically (`pi`, `codex`, `claude`) and supports explicit pane classification
- Includes a pi extension hook that marks pi panes as agents and updates both sidebar state and pane-border indicators during `session_start`, `agent_start`, `tool_execution_*`, `agent_end`, and `session_shutdown`
- Compact mode supports direct keyboard selection and mouse click selection in the sidebar
- New managed panes can be created with a derived name from pane path + branch

## tmux-agents-sidebar plugin

The canonical tmux-agents-sidebar implementation now lives here:

- `tmux/plugins/tmux-agents-sidebar/plugin.tmux`
- `tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar`
- `tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar.py`

It requires `bash`, `tmux`, and `python3` (for the interactive sidebar UI).

The local tmux config loads the plugin from the standard tmux plugin path.
Link it into place like this:

```bash
mkdir -p ~/.tmux/plugins
ln -sfn ~/workspace/configs/tmux/plugins/tmux-agents-sidebar ~/.tmux/plugins/tmux-agents-sidebar
```

```tmux
run-shell "$HOME/.tmux/plugins/tmux-agents-sidebar/plugin.tmux"
```

Convenience entrypoints also live at:

- `tmux/agents-sidebar.conf`
- `tmux/scripts/agents-sidebar`
- `tmux/scripts/agents-sidebar.py`

Those make it easy to symlink or invoke the plugin from `~/.tmux`.

## Helper scripts

The active tmux config expects these helper scripts to exist under `~/.tmux/scripts/`:

- `tmux/scripts/tmux-battery-cache.sh`
- `tmux/scripts/tmux-apply-fast-status.sh`

Suggested setup:

```bash
mkdir -p ~/.tmux/scripts
ln -sfn ~/workspace/configs/tmux/scripts/tmux-battery-cache.sh ~/.tmux/scripts/tmux-battery-cache.sh
ln -sfn ~/workspace/configs/tmux/scripts/tmux-apply-fast-status.sh ~/.tmux/scripts/tmux-apply-fast-status.sh
```

## Pi hook setup for pane activity indicators

The pane-border activity indicator for Pi sessions comes from the global Pi extension:

- `pi/agent/extensions/agents-sidebar-status.ts`

Suggested setup:

```bash
mkdir -p ~/.pi/agent ~/.pi/agent/extensions
ln -sfn ~/workspace/configs/pi/agent/settings.json ~/.pi/agent/settings.json
ln -sfn ~/workspace/configs/pi/agent/extensions/minimal-footer.ts ~/.pi/agent/extensions/minimal-footer.ts
ln -sfn ~/workspace/configs/pi/agent/extensions/agents-sidebar-status.ts ~/.pi/agent/extensions/agents-sidebar-status.ts
```

Then reload Pi in each running session with:

```text
/reload
```

Indicator meanings near the pane border:
- `[·]` — waiting for input
- `[●]` — currently running
- `[⚙]` — executing a tool
- `[✓]` — just finished successfully
- `[✗]` — last run ended with an error

## tmux-agents-sidebar usage

When the plugin is enabled:

### Key bindings
- `prefix m` — switch to compact mode
- `prefix M` — switch to wide mode
- `prefix N` — create a new managed agent pane and auto-label it from pane path / branch
- `prefix a` — focus the sidebar pane
- `prefix x` — kill the current managed pane using the custom compact-aware kill flow
- `prefix ]` / `prefix [` — next / previous entry
- `prefix Down` / `prefix Up` — next / previous entry
- `prefix Tab` — toggle last active entry

### Commands
```bash
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar compact
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar wide
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar new
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar kill-current
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar focus <name>
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar focus-sidebar
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar focus-right
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar register <pane-id> <name>
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar mark-agent <pane-id> [provider] [label]
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar mark-pane <pane-id> [label]
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar set-status <pane-id> <status> [text]
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar clear-status <pane-id>
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar list-entries
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar list-agents
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar snapshot
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar cleanup-dead
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar refresh
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar repair
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar status
```

### Compact mode controls
When the sidebar is focused:
- `j` / `k` or arrow keys — move selection across both sections
- `Enter` — focus selected entry
- `1..9` — direct switch
- `n` / `p` — next / previous entry
- `Esc` / `q` — return focus to the active pane
- mouse click — switch to clicked row
- mouse wheel — move selection

### Notes
- Folder text comes from the pane current path basename.
- Branch text comes from the cached `@git_branch` pane option set by shell hooks in `~/.zshrc`.
- Branch cache updates on both `precmd` and `chpwd`, so directory changes in interactive zsh panes update the sidebar more reliably.
- Compact mode keeps inactive panes in a detached tmux session named like `__agents_sidebar_store_<session-key>`.
- `register` and `new` create agent entries; ordinary shell panes stay in `Panes` unless you mark or detect them as agents.
- Heuristic agent detection looks at explicit metadata first, then pane title / command / child-process hints.
- `pi/agent/extensions/agents-sidebar-status.ts` publishes pi lifecycle status into tmux so pane borders and sidebar rows update immediately when Pi is waiting, running, executing tools, finishing, or erroring.
- If compact state gets stale, use:

```bash
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar wide
~/workspace/configs/tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar compact
```

## Tests

The plugin includes executable shell integration tests modeled after common tmux plugin test layouts (`run_tests` + `tests/test_*.sh`). Run them from the plugin directory:

```bash
cd ~/workspace/configs/tmux/plugins/tmux-agents-sidebar
./run_tests
```

## Reload

```bash
tmux source-file ~/.tmux.conf
```
