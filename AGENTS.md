# AGENTS.md

Guidelines for agents and contributors working in this configs repository.

## Purpose

This repo is for **publicly shareable local configuration only**.

## Hard rules

- Never commit secrets or credentials.
- Never commit machine-specific auth/session data.
- Prefer portable defaults over host-specific paths.
- Keep changes small and easy to reason about.

## Do not commit

- `.env*`
- `**/auth.json`
- SSH/GPG keys
- cloud credentials (`~/.aws`, kube credentials, tokens)
- private certificates/keys
- caches and runtime artifacts

## Safe-to-share examples

- tmux config (`tmux/.tmux.conf.local`)
- terminal config (`ghostty/config`)
- pi non-auth settings (`pi/agent/*.json` excluding auth)

## Validation checklist before commit

1. Run a secret scan (regex/gitleaks).
2. Review diffs for accidental hostnames/usernames/internal paths.
3. Ensure symlinks target files inside this repo (or documented upstream deps).
4. Update `README.md` if setup instructions changed.

## Commit/push behavior

- Do **not** commit or push unless explicitly requested by the user.
- When requested, use conventional commits (e.g. `chore(configs): ...`).
