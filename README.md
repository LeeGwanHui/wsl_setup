# wsl_setup

WSL2 Ubuntu 개발 환경을 한 번에 재현하기 위한 저장소.
셸 설정, Claude Code 설정, 개인 스킬까지 이 머신을 구성하는 것을 전부 담는다.

```
setup-wsl-env.sh    설치 스크립트 (여러 번 실행해도 안전)
dotfiles/
  .zshrc            zsh + oh-my-zsh 설정
  .p10k.zsh         powerlevel10k 프롬프트 설정
  .tmux.conf        tmux 설정
  .claude/          → ~/.claude/ 로 배치
    settings.json           권한 / 훅 / auto 모드
    hooks/guard.py          PreToolUse 가드
    rules/shell-dotfiles.md .zshrc 편집 시에만 로드되는 규칙
    skills/                 개인 스킬 (date-course, research 계열)
research/
  claude-code-settings/     위 settings.json의 근거가 된 리서치
```

## 사용

```sh
bash setup-wsl-env.sh
exec zsh
```

기존 dotfile은 덮어쓰기 전에 `~/.zshrc.bak.<타임스탬프>` 형태로 백업됩니다.

## 설치되는 것

**apt** — build-essential, git, curl/wget, zsh, tmux, htop, tree, jq,
fzf, ripgrep, fd-find, bat, eza, zoxide, python3 일체(+python3-yaml), pipx
(Ubuntu 26.04 기본 저장소에 전부 있어 PPA가 필요 없습니다)

**apt (별도 저장소)** — gh (GitHub 공식 저장소)

**zsh** — oh-my-zsh, powerlevel10k 테마, 플러그인 4종
(zsh-autosuggestions, zsh-syntax-highlighting, zsh-completions, fzf-tab)

**직접 설치** — nvm + Node.js LTS, Claude Code(npm 전역), neovim(최신 tarball → `~/.local`)

**폰트** — MesloLGS NF를 Windows 다운로드 폴더에 내려둡니다.
설치와 터미널 글꼴 지정은 Windows 쪽에서 직접 해야 합니다(아래 참고).

## Claude Code 설정

`dotfiles/.claude/`가 `~/.claude/`로 배치됩니다. 세션마다 승인을 눌러 쌓이는
일회성 allow 항목은 `~/.claude/settings.local.json`에 따로 남고, 여기서는
건드리지 않습니다.

**`settings.json`** — `permissions.defaultMode`를 `auto`로 둡니다. 프롬프트는 거의
안 뜨지만 분류기가 `curl|bash`, force push, 비밀 유출 같은 걸 먼저 걸러냅니다.
`.zshrc`의 `ccd` alias(`--dangerously-skip-permissions`)는 그대로 두었으므로,
필요할 때 여전히 전부 우회할 수 있습니다.

**`hooks/guard.py`** — PreToolUse 훅. 이게 필요한 이유는 하나입니다:

> bypass 모드는 모든 프롬프트와 protected-path 검사를 제거하지만,
> **PreToolUse의 `deny`는 권한 모드 검사보다 먼저 실행되어 우회할 수 없습니다.**

즉 `ccd`로 띄워도 살아있는 유일한 통제입니다. `rm -rf`, `git reset --hard`,
force push, `curl|sh`, `mkfs`, `.env`/SSH 키 접근 등을 막습니다.
명령 문자열만 보므로 `bash -c "$(...)"` 안쪽은 못 봅니다. 안전벨트지 보안 경계가 아닙니다.
예외가 나면 조용히 통과시킵니다 — 가드가 깨져서 작업이 멈추는 쪽이 더 나쁩니다.

대가가 하나 있습니다: **차단 패턴을 언급하거나 스크립트에 담기만 해도 막힙니다.**
실행 의도와 무관합니다. 거슬리면 `guard.py`의 `BASH_RULES`에서 해당 줄을 빼면 됩니다.

**`rules/shell-dotfiles.md`** — `paths:` 프론트매터가 붙은 경로 스코프 규칙.
아래 "손댈 때 주의할 점"의 내용을 담고 있으며, `.zshrc`나 `wsl_setup/**`을
실제로 읽을 때만 컨텍스트에 올라옵니다. 그 외 세션에서는 토큰을 쓰지 않습니다.

## 스킬

`dotfiles/.claude/skills/`가 `~/.claude/skills/`로 배치됩니다.
**덮어쓰기만 하고 지우지는 않습니다** — 홈에만 있는 `date-course/.kakao_key`,
`__pycache__` 같은 것을 날리지 않기 위해서입니다.

- **date-course** — 지역·시간·분위기를 받아 웹 검색으로 실제 가게를 찾아 데이트 코스를 제안한다.
- **research** — 주제를 받아 `outline.yaml`·`fields.yaml` 리서치 개요를 만든다. (`validate_json.py` 포함)
- **research-add-items** / **research-add-fields** — 기존 개요에 대상·필드를 보강한다.
- **research-deep** — 개요를 읽어 대상별 독립 에이전트로 심층 리서치 후 항목별 JSON을 생성하고 검증한다.
- **research-report** — 심층 리서치 JSON들을 마크다운 리포트로 합친다.

> research 계열은 웹 UI에서 `/research`처럼 슬래시로 호출되지 않고,
> "이 주제 리서치해줘"처럼 **작업을 설명하면 description으로 트리거**된다.

`.kakao_key`는 `.gitignore`로 막혀 있습니다. 절대 커밋하지 마세요.

### 웹 세션(claude.ai/code)에서 쓰기

클라우드 환경(Environment)의 **Setup script**에 아래를 추가하면, 모든 웹 세션에서
이 스킬들이 활성화된다. 통합으로 스킬 경로가 저장소 루트에서
`dotfiles/.claude/skills/` 아래로 바뀌었으므로 기존 스크립트를 갱신해야 한다.

```bash
git clone https://github.com/LeeGwanHui/wsl_setup ~/.claude/skills-repo && \
mkdir -p ~/.claude/skills && \
cp -r ~/.claude/skills-repo/dotfiles/.claude/skills/*/ ~/.claude/skills/ && \
pip install pyyaml >/dev/null 2>&1 || true
```

> `validate_json.py`가 `pyyaml`을 임포트하므로 마지막 줄에서 미리 설치한다.
> 집 PC는 `setup-wsl-env.sh`가 `python3-yaml`을 apt로 깔아주므로 불필요하다.

## 폰트가 필요한 이유

프롬프트를 실제로 그리는 건 WSL이 아니라 Windows Terminal입니다.
WSL 안에 폰트를 설치해도 소용이 없습니다.

1. `C:\Users\<사용자>\Downloads\MesloLGS-NF\` 의 ttf 4개 선택 → 우클릭 → **설치**
2. Windows Terminal → 설정 → Ubuntu 프로필 → 글꼴을 **MesloLGS NF** 로
3. 터미널 창을 새로 열기

글꼴을 바꾸지 않으면 아이콘 자리가 네모(□)로 보입니다.

## 셸 설정 요약

`.zshrc`에서 챙기고 있는 것들:

| 키/명령 | 동작 |
|---|---|
| `Tab` | fzf 창으로 완성. 디렉터리는 `eza`, 파일은 `bat` 미리보기 |
| `ESC` `ESC` | 방금 입력한 줄 앞에 `sudo` 붙이기 |
| 몇 글자 + `↑` | 그 접두어로 시작하는 명령만 히스토리 검색 |
| `Ctrl+R` | fzf 히스토리 검색 |
| `Ctrl+T` | fzf 파일 찾기 |
| `Alt+C` | fzf 디렉터리 이동 |
| `cd -2` | 두 단계 전 디렉터리로 (`AUTO_PUSHD`) |
| `cd 부분이름` | zoxide. 자주 간 디렉터리로 점프 |
| `x 파일` | 압축 형식 무관 해제 (`extract` 플러그인) |

## 손댈 때 주의할 점

`.zshrc`는 순서에 민감합니다. 바꾸기 전에 알아둘 것:

- **zoxide 초기화는 반드시 마지막 줄.** 뒤에 뭔가 붙으면 매 셸마다 경고가 뜹니다.
- **플러그인 순서** — `fzf-tab`은 위젯을 감싸는 플러그인들보다 앞,
  `zsh-syntax-highlighting`은 뒤쪽, `history-substring-search`는 그보다 더 뒤.
- **`enable-fzf-tab` 호출을 지우지 말 것.** fzf 자체 `completion.zsh`가
  Tab 키를 가로채므로 되찾아와야 합니다.
- **`zsh-completions`는 `plugins=()`에 넣지 않습니다.** oh-my-zsh가
  플러그인 파일보다 `compinit`을 먼저 돌리기 때문에, `fpath`에 직접 등록합니다.
- **fzf 환경변수에는 `fdfind`/`batcat`을 씁니다.** `fd`/`bat`은 alias일 뿐이라
  fzf가 실행하는 `sh`에서는 통하지 않습니다.
- **nvm은 지연 로드됩니다.** 시작 시간의 80%를 먹던 탓입니다. `node`/`npm`/`npx`는
  기본 버전 경로를 PATH에 직접 넣어 바로 쓰고, `nvm` 명령만 첫 호출 때 로드합니다.
  그래서 `nvm` 탭 완성은 `nvm`을 한 번 실행한 뒤부터 동작합니다.

## Node 버전 올리기

스크립트는 Node가 이미 있으면 **건드리지 않습니다.** 일부러 그렇게 했습니다.
`nvm install --lts`를 무조건 돌리면 재실행할 때마다 새 LTS 패치로 올라가는데,
전역 npm 패키지(`claude`, `tree-sitter` 등)는 옛 버전 디렉터리에 남아
PATH에서 통째로 사라집니다.

올릴 때는 패키지를 함께 옮기세요:

```sh
nvm install --lts --reinstall-packages-from=default
nvm alias default 'lts/*'
```

## research/

`dotfiles/.claude/settings.json`이 왜 그런 모양인지에 대한 근거가 들어 있습니다.
Claude Code 설정 19개 항목을 조사한 원자료(`results/` JSON 19개), 종합 보고서
(`report.md`), 보고서 생성 스크립트, 그리고 설계 결정 기록(`DECISIONS.md`).

설정과 수명주기가 다릅니다 — 설정은 계속 쓰이지만 이 리서치는 2026-08 시점의
스냅샷입니다. Claude Code가 크게 바뀌면 `research-deep`으로 다시 돌리면 됩니다.

## 이 설정에 포함하지 않은 것

- **kimi-code** — `.zshrc`가 설치돼 있으면 PATH에 넣지만, 설치 자체는 하지 않습니다.
- **pipx 도구(yt-dlp 등)** — 셸 설정과 무관해서 각자 `pipx install` 하세요.
- **텔레메트리 / Managed 정책** — 개인 단일 사용자 머신에는 불필요합니다.
