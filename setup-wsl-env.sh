#!/usr/bin/env bash
# WSL Ubuntu 개발 환경 설정 스크립트
#
# 대상: Ubuntu 26.04 LTS (WSL2)
# 실행: bash setup-wsl-env.sh
#
# 여러 번 실행해도 안전합니다. 이미 설치된 것은 건너뛰고, 기존 dotfile은
# 덮어쓰기 전에 타임스탬프를 붙여 백업합니다.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES="$SCRIPT_DIR/dotfiles"
STAMP="$(date +%Y%m%d-%H%M%S)"
ZSH_DIR="$HOME/.oh-my-zsh"
ZSH_CUSTOM="$ZSH_DIR/custom"
NVM_VERSION="v0.40.1"

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31m[x] %s\033[0m\n' "$*" >&2; exit 1; }

# 이 스크립트는 $HOME 아래에 사용자 소유 파일을 만듭니다. root로 돌리면
# 소유권이 뒤틀리므로 막습니다. sudo는 apt 단계에서만 개별적으로 씁니다.
[ "$(id -u)" -ne 0 ] || die "root로 실행하지 마세요. 일반 사용자로 실행하면 필요할 때 sudo를 묻습니다."
[ -d "$DOTFILES" ] || die "dotfiles 디렉터리가 없습니다: $DOTFILES"

# ---------------------------------------------------------------------------
log "1. apt 업데이트"
sudo apt update && sudo apt upgrade -y

# ---------------------------------------------------------------------------
log "2. 기본 패키지 설치"
# eza / zoxide / fzf / ripgrep / fd-find / bat 는 Ubuntu 26.04 기본 저장소에
# 모두 들어 있어 별도 PPA가 필요 없습니다.
sudo apt install -y \
    build-essential curl wget git unzip zip ca-certificates gnupg \
    lsb-release software-properties-common \
    zsh tmux htop tree jq \
    fzf ripgrep fd-find bat eza zoxide \
    python3 python3-pip python3-venv python3-dev python3-yaml pipx
# python3-yaml: research 스킬의 validate_json.py가 임포트합니다.

# ---------------------------------------------------------------------------
log "3. GitHub CLI (gh)"
if command -v gh >/dev/null 2>&1; then
    info "이미 설치됨: $(gh --version | head -1)"
else
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
    sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
    sudo apt update && sudo apt install -y gh
fi

# ---------------------------------------------------------------------------
log "4. locale (en_US.UTF-8)"
sudo locale-gen en_US.UTF-8 || true
sudo update-locale LANG=en_US.UTF-8 || true

# ---------------------------------------------------------------------------
log "5. oh-my-zsh"
if [ -d "$ZSH_DIR" ]; then
    info "이미 설치됨, 건너뜀"
else
    RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c \
        "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# ---------------------------------------------------------------------------
log "6. powerlevel10k 테마 + zsh 플러그인"
clone_if_missing() {
    local url="$1" dest="$2"
    if [ -d "$dest" ]; then
        info "이미 있음: $(basename "$dest")"
    else
        git clone --depth=1 "$url" "$dest"
    fi
}
clone_if_missing https://github.com/romkatv/powerlevel10k              "$ZSH_CUSTOM/themes/powerlevel10k"
clone_if_missing https://github.com/zsh-users/zsh-autosuggestions      "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
clone_if_missing https://github.com/zsh-users/zsh-syntax-highlighting  "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
clone_if_missing https://github.com/zsh-users/zsh-completions          "$ZSH_CUSTOM/plugins/zsh-completions"
clone_if_missing https://github.com/Aloxaf/fzf-tab                     "$ZSH_CUSTOM/plugins/fzf-tab"

# ---------------------------------------------------------------------------
log "7. nvm + Node.js LTS"
export NVM_DIR="$HOME/.nvm"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    curl -o- "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh" | bash
fi
# shellcheck disable=SC1091
\. "$NVM_DIR/nvm.sh"
# `nvm install --lts` 를 무조건 돌리면 안 됩니다. 재실행할 때마다 새로 나온
# LTS 패치로 올라가고, 전역 npm 패키지(claude, tree-sitter 등)는 옛 버전
# 디렉터리에 남아 PATH에서 통째로 사라집니다. 그래서 쓸 수 있는 default가
# 없을 때만 설치합니다.
if nvm which default >/dev/null 2>&1; then
    info "이미 설치됨: $(nvm version default)"
    info "올리려면: nvm install --lts --reinstall-packages-from=default && nvm alias default 'lts/*'"
else
    nvm install --lts
    nvm alias default 'lts/*'
fi

# ---------------------------------------------------------------------------
log "8. Claude Code"
# .zshrc의 cc / ccd / ccr alias가 이 명령을 가리킵니다.
if command -v claude >/dev/null 2>&1; then
    info "이미 설치됨: $(claude --version 2>/dev/null || echo unknown)"
else
    npm install -g @anthropic-ai/claude-code
fi

# ---------------------------------------------------------------------------
log "9. neovim (apt 버전은 업스트림보다 한참 뒤처짐)"
# .zshrc가 EDITOR=nvim으로 잡고 이 경로를 PATH에 넣습니다.
NVIM_DIR="$HOME/.local/nvim-linux-x86_64"
if [ -x "$NVIM_DIR/bin/nvim" ]; then
    info "이미 설치됨: $("$NVIM_DIR/bin/nvim" --version | head -1)"
else
    mkdir -p "$HOME/.local"
    tmp="$(mktemp -d)"
    curl -fsSL -o "$tmp/nvim.tar.gz" \
        https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz
    tar -xzf "$tmp/nvim.tar.gz" -C "$HOME/.local"
    rm -rf "$tmp"
    info "설치됨: $("$NVIM_DIR/bin/nvim" --version | head -1)"
fi

# ---------------------------------------------------------------------------
log "10. pipx PATH 등록"
pipx ensurepath >/dev/null 2>&1 || true

# ---------------------------------------------------------------------------
log "11. MesloLGS NF 폰트 (Windows 쪽에 설치 필요)"
# 폰트는 터미널을 그리는 Windows가 가지고 있어야 합니다. WSL 안에 깔아도
# Windows Terminal은 보지 못하므로, 여기서는 Windows 다운로드 폴더에 내려두고
# 설치는 사용자가 합니다.
# Windows 사용자명은 cmd.exe에게 물어보는 게 정확합니다.
# /mnt/c/Users/* 를 그냥 훑으면 Default, Public 같은 시스템 프로필이 먼저 걸립니다.
win_downloads() {
    local user dir
    user="$(cmd.exe /c 'echo %USERNAME%' 2>/dev/null | tr -d '\r\n' || true)"
    if [ -n "$user" ] && [ -d "/mnt/c/Users/$user/Downloads" ]; then
        printf '%s\n' "/mnt/c/Users/$user/Downloads"
        return 0
    fi
    # cmd.exe 상호운용이 꺼져 있을 때: 시스템 프로필을 빼고 첫 후보
    for dir in /mnt/c/Users/*/Downloads; do
        case "$dir" in
            */Default/*|*/"Default User"/*|*/Public/*|*/"All Users"/*|*/defaultuser0/*) continue ;;
        esac
        [ -d "$dir" ] && { printf '%s\n' "$dir"; return 0; }
    done
    return 1
}

WIN_USER_DIR="$(win_downloads || true)"
if [ -n "$WIN_USER_DIR" ]; then
    FONT_DIR="$WIN_USER_DIR/MesloLGS-NF"
    mkdir -p "$FONT_DIR"
    for variant in "Regular" "Bold" "Italic" "Bold Italic"; do
        target="$FONT_DIR/MesloLGS NF $variant.ttf"
        if [ -f "$target" ]; then
            info "이미 받음: $variant"
        else
            curl -fsSL -o "$target" \
                "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20${variant// /%20}.ttf"
            info "받음: $variant"
        fi
    done
    info "설치: 위 폴더의 ttf 4개를 모두 선택 → 우클릭 → '설치'"
    info "그다음 Windows Terminal → 설정 → Ubuntu 프로필 → 글꼴을 'MesloLGS NF'로"
else
    warn "/mnt/c 를 찾지 못했습니다. 폰트는 직접 받아 Windows에 설치하세요:"
    warn "  https://github.com/romkatv/powerlevel10k#manual-font-installation"
fi

# ---------------------------------------------------------------------------
log "12. dotfile 배치"
install_dotfile() {
    local src="$DOTFILES/$1" dst="$HOME/$1"
    [ -f "$src" ] || { warn "원본 없음, 건너뜀: $1"; return 0; }
    if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
        info "변경 없음: $1"
        return 0
    fi
    [ -e "$dst" ] && { cp -a "$dst" "$dst.bak.$STAMP"; info "백업: $1.bak.$STAMP"; }
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    info "배치: $1"
}
install_dotfile .zshrc
install_dotfile .p10k.zsh
install_dotfile .tmux.conf

# Claude Code 설정. settings.json은 권한/훅/auto 모드만 담습니다.
# 세션마다 눌러 쌓이는 일회성 allow 항목은 ~/.claude/settings.local.json에
# 따로 남으며 여기서 건드리지 않습니다.
install_dotfile .claude/settings.json
install_dotfile .claude/hooks/guard.py
install_dotfile .claude/rules/shell-dotfiles.md

# 스킬은 디렉터리 단위라 install_dotfile로 처리할 수 없습니다.
# 덮어쓰기만 하고 지우지는 않습니다 — 홈에만 있는 파일(date-course/.kakao_key,
# __pycache__ 등)을 날리지 않기 위해서입니다.
install_skills() {
    local src="$DOTFILES/.claude/skills" dst="$HOME/.claude/skills" name
    [ -d "$src" ] || { warn "원본 없음, 건너뜀: .claude/skills"; return 0; }
    mkdir -p "$dst"
    for dir in "$src"/*/; do
        name="$(basename "$dir")"
        mkdir -p "$dst/$name"
        cp -a "$dir." "$dst/$name/"
        info "스킬: $name"
    done
}
install_skills

# p10k은 프롬프트를 캐시해 두므로, 설정이 바뀌면 캐시를 버려야 반영됩니다.
rm -f "${XDG_CACHE_HOME:-$HOME/.cache}"/p10k-instant-prompt-*.zsh*

# ---------------------------------------------------------------------------
log "13. 기본 셸을 zsh로"
if [ "$(getent passwd "$USER" | cut -d: -f7)" != "$(command -v zsh)" ]; then
    sudo chsh -s "$(command -v zsh)" "$USER"
    info "변경됨 (다음 로그인부터 적용)"
else
    info "이미 zsh"
fi

# ---------------------------------------------------------------------------
cat <<EOF

======================================================================
 설치 완료

 적용 방법 (둘 중 하나):
   1) exec zsh
   2) WSL 완전 재시작:  powershell 에서  wsl --shutdown  후 다시 실행

 폰트를 방금 설치했다면 Windows Terminal 글꼴을 'MesloLGS NF'로
 바꾼 뒤 창을 새로 열어야 아이콘이 제대로 보입니다.

 백업된 파일:  ~/*.bak.$STAMP
======================================================================
EOF
