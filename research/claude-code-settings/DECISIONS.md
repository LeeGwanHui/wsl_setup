# 설계 근거 — 리서치를 실제 설정으로 옮긴 기록

`report.md` 19개 항목에서 무엇을 골랐고 왜 그렇게 골랐는지에 대한 기록이다.

**설정 파일 자체는 여기 없다.** 단일 소스는 아래 한 곳뿐이다:

```
~/dev/projects/wsl_setup/dotfiles/.claude/
  settings.json
  hooks/guard.py
  rules/shell-dotfiles.md
```

`setup-wsl-env.sh`가 이걸 `~/.claude/`로 배치한다 (2026-08-08 적용 완료).
한때 이 디렉터리에 같은 파일의 사본이 있었으나, 두 벌이 갈라질 위험이 있어 지웠다.
설정을 고칠 일이 있으면 `wsl_setup` 쪽을 고친다.

---

## 1. 이 설계를 가른 사실

당시 `.zshrc:142-143`이 `ccd`/`ccr`을 `--dangerously-skip-permissions`로 걸어두고 있었고,
지금도 그대로다(의도된 선택). 여기서 연구 결과 두 줄이 결정적이었다.

| 통제 | bypass 모드에서 |
|---|---|
| `permissions.deny` | **무력** — bypass는 모든 프롬프트와 protected-path 검사를 제거 |
| `PreToolUse` deny 훅 | **작동** — 권한 모드 검사보다 먼저 실행되며 우회 불가 |

> "a PreToolUse `deny` fires before any permission-mode check and cannot be bypassed by
> bypassPermissions/--dangerously-skip-permissions" — `results/Hooks.json`

그래서 두 축으로 갔다. **auto 모드로 실질적 권한 검사를 되찾고**, 그와 별개로
**어떤 모드에서도 뚫리지 않는 훅 가드를 깐다.** 나중에 auto를 꺼도 가드는 남는다.

결과적으로 `cc`는 auto 모드로 뜨고, `ccd`는 여전히 전면 우회이며,
가드 훅은 양쪽 모두에서 작동한다.

## 2. settings.json 선택 근거

| 항목 | 근거 |
|---|---|
| `permissions.defaultMode: "auto"` | Auto Mode & 권한 분류기 — bypass의 공식 대체 경로 |
| `skipDangerousModePermissionPrompt: true` **유지** | `ccd`를 남기기로 했으므로 필요 |
| `permissions.deny` | Permissions — 비밀파일 읽기, force push, reset --hard |
| `permissions.ask` | Permissions — auto 모드에서도 ask는 항상 프롬프트 |
| `autoMode.classifyAllShell: true` | Auto Mode — 모든 셸 명령을 분류기로 |
| `autoMode.environment` / `soft_deny` | Auto Mode — `$defaults`에 이 머신 컨텍스트를 splice |
| `workflowSizeGuideline: "small"` | Agent Teams & Dynamic Workflows — 기본 medium(15 에이전트)은 개인 사용에 과함 |

의도적으로 넣지 않은 것:

- **텔레메트리** — 개인 단일 사용자 머신에서 수집할 대상이 없다. 기본 off가 맞다.
- **`teammateMode`** — Agent Teams를 켜지 않는 한 무의미.
- **Managed 정책** — 조직용. 단일 사용자 머신에 root 소유 정책 파일을 둘 이유가 없다.
- **statusLine** — 취향 영역이라 임의로 정하지 않았다.

## 3. guard.py의 성격과 한계

blunt backstop이지 보안 경계가 아니다. 명령 **문자열**을 보므로
`bash -c "$(...)"`, alias, 열어보지 않은 스크립트 내부는 못 본다.

대가가 하나 있고, 검증 중에 실제로 겪었다: **그 패턴을 언급하거나 스크립트에 담기만
해도 차단된다.** 실행 의도와 무관하다. 거슬리면 `BASH_RULES`에서 해당 줄을 빼면 되도록
리스트 편집만으로 조정되게 짰다.

설계상 **실패해도 세션을 막지 않는다** — 예외가 나면 조용히 exit 0(허용)이다.
가드가 깨져서 작업이 멈추는 쪽이 더 나쁘다고 봤다.

## 4. 남겨둔 것

- **`~/.claude/settings.local.json`의 allow 39개** — 지우면 기존 흐름이 깨질 수 있어
  건드리지 않았다. `classifyAllShell: true`가 이들을 분류기로 돌리므로 실효는 줄어든다.
- **`.zshrc` alias** — `ccd`를 그대로 두기로 한 명시적 결정.

## 5. 되돌리는 법

```sh
ls ~/.claude/settings.json.bak.*        # 적용 전 백업
cp ~/.claude/settings.json.bak.<STAMP> ~/.claude/settings.json
rm -rf ~/.claude/hooks ~/.claude/rules
```

`wsl_setup`에서도 빼려면 `dotfiles/.claude/`를 지우고
`setup-wsl-env.sh`의 `install_dotfile .claude/...` 3줄을 제거한다.
