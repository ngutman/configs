# Changelog

All notable shareable config changes in this repo are tracked here.

## 2026-04-06

### Added
- tmux compact multi-agent sidebar workflow with:
  - `tmux/agent-layout.conf`
  - `tmux/scripts/agent-layout`
  - `tmux/scripts/agent-sidebar.py`
- tmux key bindings for compact/wide mode, agent cycling, sidebar focus, and compact-aware pane creation / killing
- cached per-pane git branch display in tmux pane borders
- Pi packages for `pi-web-access` and `pi-subagents`
- Pi shell command prefix that loads `~/.path_config` and activates the default `nvm` Node version
- Ghostty `macos-option-as-alt = true`

### Changed
- zsh now activates the default `nvm` alias after Prezto initialization
- zsh now caches git branch metadata into tmux pane options on both `precmd` and `chpwd`
- tmux session auto-rename now uses the current directory name without appending the branch
- Pi defaults now use `gpt-5.4`
- Pi sub-core usage tools are enabled

### Docs
- expanded `tmux/README.md` with agent layout setup and usage notes
- updated the root `README.md` to cover the agent layout files and changelog
