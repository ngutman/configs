# configs

Personal dotfiles/configs I can share publicly.

## Structure

- `zsh/.zshrc` — public/shareable zsh config (loads optional local `~/.zshrc.work`)
- `tmux/.tmux.conf.local` — my tmux customizations (performance-tuned status line, pane labels, mouse + copy-mode tweaks)
- `tmux/agent-layout.conf` — tmux bindings/options for the compact multi-agent sidebar workflow
- `tmux/README.md` — tmux features, agent layout usage, and setup notes
- `tmux/scripts/` — helper scripts for tmux status/battery and the agent sidebar controller/UI
- `ghostty/config` — Ghostty terminal configuration
- `pi/agent/settings.json` — pi agent general settings (no auth)
- `pi/agent/pi-sub-core-settings.json` — pi-sub-core settings
- `pi/agent/pi-sub-bar-settings.json` — pi-sub-bar display settings
- `CHANGELOG.md` — notable shareable config changes in this repo

## Local symlinks

```bash
# zsh
ln -sfn ~/workspace/configs/zsh/.zshrc ~/.zshrc
# keep private/work-only settings local and untracked:
# ~/.zshrc.work

# tmux (using gpakosz base config)
git clone https://github.com/gpakosz/.tmux.git ~/.tmux
ln -sfn ~/.tmux/.tmux.conf ~/.tmux.conf
ln -sfn ~/workspace/configs/tmux/.tmux.conf.local ~/.tmux.conf.local
mkdir -p ~/.tmux/scripts
ln -sfn ~/workspace/configs/tmux/agent-layout.conf ~/.tmux/agent-layout.conf
ln -sfn ~/workspace/configs/tmux/scripts/tmux-battery-cache.sh ~/.tmux/scripts/tmux-battery-cache.sh
ln -sfn ~/workspace/configs/tmux/scripts/tmux-apply-fast-status.sh ~/.tmux/scripts/tmux-apply-fast-status.sh
ln -sfn ~/workspace/configs/tmux/scripts/agent-layout ~/.tmux/scripts/agent-layout
ln -sfn ~/workspace/configs/tmux/scripts/agent-sidebar.py ~/.tmux/scripts/agent-sidebar.py

# ghostty
mkdir -p ~/.config/ghostty
ln -sfn ~/workspace/configs/ghostty/config ~/.config/ghostty/config

# pi settings (no auth)
mkdir -p ~/.pi/agent
ln -sfn ~/workspace/configs/pi/agent/settings.json ~/.pi/agent/settings.json
ln -sfn ~/workspace/configs/pi/agent/pi-sub-core-settings.json ~/.pi/agent/pi-sub-core-settings.json
ln -sfn ~/workspace/configs/pi/agent/pi-sub-bar-settings.json ~/.pi/agent/pi-sub-bar-settings.json
```

## Safety rules before publishing

- Never commit `.env*`, SSH keys, API tokens, cloud creds, cookies, kubeconfigs, or private certs.
- Review all `#()` shell commands in tmux/zsh for accidental secret output.
- Replace usernames/hostnames if they reveal sensitive internal details.
