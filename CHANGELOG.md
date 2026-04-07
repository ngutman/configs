# Changelog

All notable shareable config changes in this repo are tracked here.

## 2026-04-06

### Added
- tmux compact multi-agent sidebar workflow, now packaged as a local plugin under:
  - `tmux/plugins/tmux-agents-sidebar/plugin.tmux`
  - `tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar`
  - `tmux/plugins/tmux-agents-sidebar/scripts/agents-sidebar.py`
- tmux-agents-sidebar shell integration tests under:
  - `tmux/plugins/tmux-agents-sidebar/run_tests`
  - `tmux/plugins/tmux-agents-sidebar/tests/`
- Pi extension hook for tmux-agents-sidebar status updates:
  - `pi/agent/extensions/agents-sidebar-status.ts`
- tmux key bindings for compact/wide mode, agent cycling, sidebar focus, compact-aware pane creation / killing, and prefix `Up` / `Down` agent navigation
- cached per-pane git branch display in tmux pane borders
- Pi packages for `pi-web-access` and `pi-subagents`
- Pi shell command prefix that loads `~/.path_config` and activates the default `nvm` Node version
- Ghostty `macos-option-as-alt = true`

### Changed
- zsh now activates the default `nvm` alias after Prezto initialization
- zsh now caches git branch metadata into tmux pane options on both `precmd` and `chpwd`
- tmux session auto-rename now uses the current directory name without appending the branch
- tmux-agents-sidebar is loaded via a local plugin entrypoint and now renders separate `Agents` and `Panes` sections backed by pane metadata + heuristics for `pi`, `codex`, and `claude`
- tmux-agents-sidebar compact mode now parks inactive panes in a detached tmux store session instead of visible helper windows in the main session
- Pi defaults now use `gpt-5.4`
- Pi sub-core usage tools are enabled

### Docs
- expanded `tmux/README.md` with plugin-based agents sidebar setup, two-section sidebar behavior, metadata commands, and test notes
- updated the root `README.md` to cover the plugin layout, pi extension symlinks, and changelog
