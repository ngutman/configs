# --- Debug/profiling toggles ---
if [[ -n "${ZSH_DEBUGRC+1}" ]]; then
  zmodload zsh/zprof
fi

if [[ -n "${ZSH_PROFILE_TIMING+1}" ]]; then
  zmodload zsh/datetime 2>/dev/null
  : ${ZSH_PROFILE_TIMING_LOG:="${XDG_CACHE_HOME:-$HOME/.cache}/zsh-startup-timing.log"}
  typeset -gF __zsh_timing_start=$EPOCHREALTIME

  __zsh_timing() {
    local -F now=$EPOCHREALTIME
    local -F delta=$(( now - __zsh_timing_start ))
    __zsh_timing_start=$now
    printf '%s\t%0.3f\t%s\n' "$$" "$delta" "$1" >>| "$ZSH_PROFILE_TIMING_LOG"
  }

  __zsh_timing "zshrc start"
fi

# Avoid gitstatus initialization in non-tty shells.
if [[ ! -t 1 ]]; then
  export POWERLEVEL9K_DISABLE_GITSTATUS=true
  rm -f -- "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-dump-${USER}.zsh"{,.zwc}
fi

# --- Optional architecture segment for p10k ---
FG_COLOR=041
prompt_architecture() {
  local arch_name
  arch_name="$(uname -m)"

  if [[ "$arch_name" == "x86_64" ]]; then
    p10k segment -b 7 -f $FG_COLOR -t 'x86'
  elif [[ "$arch_name" == "arm64" ]]; then
    p10k segment -b 7 -f $FG_COLOR -i 'arm64'
  else
    p10k segment -b 7 -f $FG_COLOR -t '?'
  fi
}

# --- Prezto ---
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi
[[ -n "${ZSH_PROFILE_TIMING+1}" ]] && __zsh_timing "prezto init"

# --- Node.js via nvm ---
# Prezto loads nvm with --no-use, so explicitly activate the default alias.
if command -v nvm >/dev/null 2>&1; then
  nvm use --silent default >/dev/null 2>&1
fi

# --- Prompt ---
[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"
[[ -n "${ZSH_PROFILE_TIMING+1}" ]] && __zsh_timing "p10k"

# --- Core aliases ---
alias ll="ls -alh"
alias vi="nvim"
alias lsb="git branch --sort=-committerdate"

# --- Core environment ---
export LC_TIME="en_US.UTF-8"
export DISABLE_DEACTIVATE=1
export EDITOR="vi"
export VISUAL="vi"

# --- tmux: cache pane git branch and rename session as <directory> ---
tmux_auto_rename_session() {
  [[ -z "$TMUX" ]] && return

  local dir branch pane_id sid current
  dir="${PWD:t}"
  pane_id="${TMUX_PANE:-}"

  if [[ -n "$pane_id" ]]; then
    branch="$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || true)"
    if [[ -n "$branch" ]]; then
      branch="${branch//\//-}"
      tmux set-option -pt "$pane_id" @git_branch "$branch" 2>/dev/null
    else
      tmux set-option -upt "$pane_id" @git_branch 2>/dev/null
    fi
  fi

  sid="$(tmux display-message -p '#{session_id}' 2>/dev/null)"
  [[ -z "$sid" ]] && return

  current="$(tmux display-message -p -t "$sid" '#S' 2>/dev/null)"
  [[ "$current" == "$dir" ]] && return

  tmux rename-session -t "$sid" "$dir" 2>/dev/null
}
autoload -Uz add-zsh-hook
add-zsh-hook precmd tmux_auto_rename_session
add-zsh-hook chpwd tmux_auto_rename_session

# --- Optional private/work config ---
[[ -f "$HOME/.zshrc.work" ]] && source "$HOME/.zshrc.work"
[[ -n "${ZSH_PROFILE_TIMING+1}" ]] && __zsh_timing "zshrc.work"

# --- Python toolchain ---
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
[[ -n "${ZSH_PROFILE_TIMING+1}" ]] && __zsh_timing "pyenv"

# --- Completions ---
autoload bashcompinit && bashcompinit
autoload -Uz compinit && compinit

if command -v kubectl >/dev/null 2>&1; then
  source <(kubectl completion zsh)
fi

if command -v aws_completer >/dev/null 2>&1; then
  complete -C "$(command -v aws_completer)" aws
fi
[[ -n "${ZSH_PROFILE_TIMING+1}" ]] && __zsh_timing "completions"

# --- Local bin env + direnv ---
[[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
eval "$(direnv hook zsh)"
[[ -n "${ZSH_PROFILE_TIMING+1}" ]] && __zsh_timing "direnv/env"

# --- pnpm ---
export PNPM_HOME="$HOME/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac

if [[ -n "${ZSH_DEBUGRC+1}" ]]; then
  zprof
fi
