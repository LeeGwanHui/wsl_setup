# claude-skills

개인 Claude Code 스킬 모음. 이 저장소를 클라우드/웹 세션의 `~/.claude/skills/`에
심어서 어떤 저장소에서 작업하든 스킬을 쓸 수 있게 한다.

## 수록 스킬

- **date-course** — 지역·시간·분위기를 받아 웹 검색으로 실제 가게를 찾아 데이트 코스를 제안한다.

## 웹 세션(claude.ai/code)에서 쓰기

클라우드 환경(Environment)의 **Setup script**에 아래를 추가하면, 모든 웹 세션에서
이 스킬들이 활성화된다.

```bash
git clone https://github.com/LeeGwanHui/claude-skills ~/.claude/skills-repo && \
mkdir -p ~/.claude/skills && \
cp -r ~/.claude/skills-repo/*/ ~/.claude/skills/
```

## 새 스킬 추가

`<skill-name>/SKILL.md` 형태로 폴더를 만들어 커밋·푸시하면 다음 세션부터 반영된다.
로컬(집 PC)에는 `~/.claude/skills/`에 두고, 여기에도 커밋해 두면 웹과 동기화된다.
