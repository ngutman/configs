# Changelog

All notable shareable config changes in this repo are tracked here.

## 2026-04-06

### Added
- tmux helper scripts for background battery caching and lightweight status-right refresh
- cached per-pane git branch display in tmux pane borders
- Pi packages for `pi-web-access` and `pi-subagents`
- Pi shell command prefix that loads `~/.path_config` and activates the default `nvm` Node version
- Ghostty `macos-option-as-alt = true`

### Changed
- zsh now activates the default `nvm` alias after Prezto initialization
- zsh now caches git branch metadata into tmux pane options on both `precmd` and `chpwd`
- tmux session auto-rename now uses the current directory name without appending the branch
- tmux pane borders now emphasize the active pane while showing pane index, current path, and cached git branch data
- Pi defaults now use `gpt-5.4`
- Pi sub-core usage tools are enabled

### Docs
- updated `tmux/README.md` with current helper-script setup, pane-border notes, and reload instructions
- updated the root `README.md` to cover current tmux and pi symlink targets and changelog
