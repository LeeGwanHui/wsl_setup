---
paths:
  - "**/.zshrc"
  - "**/dotfiles/.zshrc"
  - "**/wsl_setup/**"
---

# WSL 셸 환경 수정 규칙

`.zshrc`는 순서에 민감하다. 아래는 wsl_setup/README.md에 기록된 제약이며, 어기면
매 셸 시작마다 경고가 뜨거나 기능이 조용히 죽는다.

- **zoxide 초기화는 반드시 파일 마지막 줄.** 뒤에 무언가 추가하면 매 셸마다 경고.
- **플러그인 순서** — `fzf-tab`은 위젯을 감싸는 플러그인들보다 앞,
  `zsh-syntax-highlighting`은 뒤쪽, `history-substring-search`는 그보다 더 뒤.
- **`enable-fzf-tab` 호출을 지우지 말 것.** fzf 자체 `completion.zsh`가 Tab을
  가로채므로 되찾아와야 한다.
- **`zsh-completions`는 `plugins=()`에 넣지 않는다.** oh-my-zsh가 플러그인 파일보다
  `compinit`을 먼저 돌리므로 `fpath`에 직접 등록한다.
- **fzf 환경변수에는 `fdfind`/`batcat`을 쓴다.** `fd`/`bat`은 alias일 뿐이라
  fzf가 실행하는 `sh`에서는 통하지 않는다.
- **nvm은 지연 로드된다.** 시작 시간의 80%를 먹던 탓. `node`/`npm`/`npx`는 기본 버전
  경로를 PATH에 직접 넣고, `nvm` 명령만 첫 호출 때 로드한다.

## 편집 후

`zsh -n ~/.zshrc`로 문법을 확인한다. 실제 적용은 새 셸에서만 확인 가능하다.

## Node 버전을 올릴 때

`setup-wsl-env.sh`는 Node가 이미 있으면 건드리지 않는다. 의도된 동작이다.
올릴 때는 전역 패키지를 함께 옮긴다:

```sh
nvm install --lts --reinstall-packages-from=default
nvm alias default 'lts/*'
```
