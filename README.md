# configs

Personal dotfiles/configs I can share publicly.

## Structure

- `tmux/.tmux.conf.local` — my tmux customizations (with pane-bottom git/path)
- `ghostty/config` — Ghostty terminal configuration

## Local symlinks

```bash
# tmux (using gpakosz base config)
git clone https://github.com/gpakosz/.tmux.git ~/.tmux
ln -sfn ~/.tmux/.tmux.conf ~/.tmux.conf
ln -sfn ~/workspace/configs/tmux/.tmux.conf.local ~/.tmux.conf.local

# ghostty
mkdir -p ~/.config/ghostty
ln -sfn ~/workspace/configs/ghostty/config ~/.config/ghostty/config
```

## Safety rules before publishing

- Never commit `.env*`, SSH keys, API tokens, cloud creds, cookies, kubeconfigs, or private certs.
- Review all `#()` shell commands in tmux/zsh for accidental secret output.
- Replace usernames/hostnames if they reveal sensitive internal details.
