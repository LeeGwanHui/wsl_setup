# --- powerlevel10k instant prompt (must stay near top) ---
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

export ZSH="$HOME/.oh-my-zsh"
ZSH_CUSTOM="${ZSH_CUSTOM:-$ZSH/custom}"
ZSH_THEME="powerlevel10k/powerlevel10k"

# zsh-completions keeps its completion files in src/. oh-my-zsh runs compinit
# before it sources plugin files, so the fpath entry has to be added here
# rather than by listing the plugin in plugins=().
fpath+=("$ZSH_CUSTOM/plugins/zsh-completions/src")

# Order matters: fzf-tab must load before the plugins that wrap ZLE widgets,
# zsh-syntax-highlighting stays near the end, and history-substring-search
# goes after it so its arrow-key bindings win.
plugins=(
  git
  sudo
  command-not-found
  colored-man-pages
  extract
  python
  node
  npm
  docker
  fzf-tab
  zsh-autosuggestions
  zsh-syntax-highlighting
  history-substring-search
)
source $ZSH/oh-my-zsh.sh

# --- history (larger, shared, deduped) ---
HISTFILE="$HOME/.zsh_history"
HISTSIZE=50000
SAVEHIST=50000
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE
setopt EXTENDED_HISTORY        # record a timestamp per entry
setopt HIST_EXPIRE_DUPS_FIRST  # trim duplicates first when HISTSIZE is hit
setopt HIST_FIND_NO_DUPS       # don't show the same line twice while searching
setopt HIST_SAVE_NO_DUPS       # don't write duplicates to HISTFILE
setopt HIST_REDUCE_BLANKS      # strip superfluous whitespace
setopt HIST_VERIFY             # let !! expand onto the line instead of running

# --- shell options ---
setopt AUTO_PUSHD              # cd pushes onto the dir stack (cd -1 .. cd -9)
setopt PUSHD_IGNORE_DUPS
setopt PUSHD_SILENT
setopt INTERACTIVE_COMMENTS    # allow # comments at the prompt
setopt EXTENDED_GLOB
setopt NO_BEEP

# Ctrl+W stops at path separators instead of eating the whole path
WORDCHARS='*?_-.[]~&;!#$%^(){}<>'

# --- completion behaviour ---
# case-insensitive, then partial-word, then substring matching
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*:descriptions' format '[%d]'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' special-dirs true
# fzf-tab needs zsh's own menu off so it can capture the unambiguous prefix.
# oh-my-zsh sets `menu select` on the 5-component pattern, so override that too.
zstyle ':completion:*' menu no
zstyle ':completion:*:*:*:*:*' menu no

# --- fzf-tab ---
zstyle ':fzf-tab:*' switch-group '<' '>'
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always --group-directories-first $realpath'
zstyle ':fzf-tab:complete:__zoxide_z:*' fzf-preview 'eza -1 --color=always --group-directories-first $realpath'
zstyle ':fzf-tab:complete:*:*' fzf-preview \
  '[[ -d $realpath ]] && eza -1 --color=always --group-directories-first $realpath || batcat --style=numbers --color=always --line-range=:200 $realpath 2>/dev/null'
zstyle ':completion:*:git-checkout:*' sort false

# --- history-substring-search keys (type a prefix, then Up/Down) ---
if (( $+widgets[history-substring-search-up] )); then
  bindkey '^[[A' history-substring-search-up
  bindkey '^[[B' history-substring-search-down
  bindkey '^P'   history-substring-search-up
  bindkey '^N'   history-substring-search-down
fi

# --- nvm (lazy) ---
# Sourcing nvm.sh costs ~600ms, roughly 80% of this shell's startup time.
# Instead, follow the `default` alias by reading $NVM_DIR/alias/* directly and
# put that version's bin on PATH, so node/npm/npx cost nothing. Only the `nvm`
# command itself pays, and only the first time it is called.
export NVM_DIR="$HOME/.nvm"

_nvm_default_version() {
  local target=default n=0
  while (( n++ < 10 )); do
    [[ $target == v?* && -d $NVM_DIR/versions/node/$target ]] && { print -r -- $target; return 0 }
    [[ -r $NVM_DIR/alias/$target ]] || return 1
    target="$(<"$NVM_DIR/alias/$target")"
  done
  return 1
}

_nvm_ver="$(_nvm_default_version)"
if [[ -n $_nvm_ver ]]; then
  # Canonical nvm path, so a later `nvm use` strips it correctly.
  path=("$NVM_DIR/versions/node/$_nvm_ver/bin" $path)
  nvm() {
    unset -f nvm
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" --no-use
    [ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
    nvm "$@"
  }
else
  # Default version didn't resolve; load nvm the slow, always-correct way.
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
fi
unset _nvm_ver
unset -f _nvm_default_version

# --- pipx / python user bin ---
export PATH="$HOME/.local/bin:$PATH"

# --- latest neovim (apt version lags upstream) ---
export PATH="$HOME/.local/nvim-linux-x86_64/bin:$PATH"

# --- Ubuntu package name quirks ---
[ -x /usr/bin/batcat ] && alias bat='batcat'
[ -x /usr/bin/fdfind ] && alias fd='fdfind'

# --- auto-cd out of /mnt/c into Linux home ---
if [[ "$PWD" == /mnt/c/* ]]; then
  cd ~
fi

# --- quality of life ---
alias gs='git status'
alias gd='git diff'
alias cc='claude'
alias ccd='claude --dangerously-skip-permissions'
alias ccr='claude --resume --dangerously-skip-permissions'

# --- eza (modern ls) ---
if command -v eza &>/dev/null; then
  alias ls='eza --group-directories-first'
  alias ll='eza -alF --group-directories-first'
  alias la='eza -a --group-directories-first'
  alias lt='eza --tree --level=2'
else
  alias ll='ls -alF'
  alias la='ls -A'
fi

# fzf key bindings / completion (Ubuntu apt package)
[ -f /usr/share/doc/fzf/examples/key-bindings.zsh ] && source /usr/share/doc/fzf/examples/key-bindings.zsh
[ -f /usr/share/doc/fzf/examples/completion.zsh ] && source /usr/share/doc/fzf/examples/completion.zsh
# fzf's completion.zsh rebinds Tab to fzf-completion, which clobbers fzf-tab.
# Re-claim Tab; fzf's ** trigger and its Ctrl-R/Ctrl-T/Alt-C widgets are unaffected.
(( $+functions[enable-fzf-tab] )) && enable-fzf-tab

# fzf tuning. These run through sh, so they need the real binary names
# (fdfind/batcat), not the interactive aliases set above.
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --info=inline'
if [ -x /usr/bin/fdfind ]; then
  export FZF_DEFAULT_COMMAND='fdfind --type f --hidden --follow --exclude .git'
  export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
  export FZF_ALT_C_COMMAND='fdfind --type d --hidden --follow --exclude .git'
fi
[ -x /usr/bin/batcat ] && export FZF_CTRL_T_OPTS="--preview 'batcat --style=numbers --color=always --line-range=:300 {}'"
[ -x /usr/bin/eza ] && export FZF_ALT_C_OPTS="--preview 'eza -1 --color=always --group-directories-first {}'"
export FZF_CTRL_R_OPTS="--preview 'echo {}' --preview-window down:3:hidden:wrap --bind '?:toggle-preview'"

# --- powerlevel10k config (run `p10k configure` to regenerate) ---
[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh

# kimi-code (skipped when not installed)
[ -d "$HOME/.kimi-code/bin" ] && export PATH="$HOME/.kimi-code/bin:$PATH"

# --- default editor ---
export EDITOR=nvim
export VISUAL=nvim

# --- zoxide (smarter cd, keeps `cd` name) --- must be the last line
command -v zoxide &>/dev/null && eval "$(zoxide init zsh --cmd cd)"
