# claude-skills

개인 Claude Code 스킬 모음. 이 저장소를 클라우드/웹 세션의 `~/.claude/skills/`에
심어서 어떤 저장소에서 작업하든 스킬을 쓸 수 있게 한다.

## 수록 스킬

- **date-course** — 지역·시간·분위기를 받아 웹 검색으로 실제 가게를 찾아 데이트 코스를 제안한다.
- **research** — 주제를 받아 초기 프레임워크 + 웹검색 보강으로 `outline.yaml`·`fields.yaml` 리서치 개요를 만든다. (`validate_json.py` 포함)
- **research-add-items** / **research-add-fields** — 기존 개요에 리서치 대상·필드를 보강한다.
- **research-deep** — 개요를 읽어 대상별 독립 에이전트로 심층 리서치 후 항목별 JSON을 생성하고 검증한다.
- **research-report** — 심층 리서치 JSON들을 마크다운 리포트로 합친다.

> research 계열은 웹 UI에서 `/research`처럼 슬래시로 호출되지 않고, "이 주제 리서치해줘"처럼 **작업을 설명하면 description으로 트리거**된다.

## 웹 세션(claude.ai/code)에서 쓰기

클라우드 환경(Environment)의 **Setup script**에 아래를 추가하면, 모든 웹 세션에서
이 스킬들이 활성화된다.

```bash
git clone https://github.com/LeeGwanHui/claude-skills ~/.claude/skills-repo && \
mkdir -p ~/.claude/skills && \
cp -r ~/.claude/skills-repo/*/ ~/.claude/skills/ && \
pip install pyyaml >/dev/null 2>&1 || true
```

> `research-deep`의 검증 스크립트(`research/validate_json.py`)가 `pyyaml`을 임포트하므로
> 셋업 스크립트 마지막 줄에서 미리 설치한다. (집 PC 터미널에는 이미 있어 불필요)

## 새 스킬 추가

`<skill-name>/SKILL.md` 형태로 폴더를 만들어 커밋·푸시하면 다음 세션부터 반영된다.
로컬(집 PC)에는 `~/.claude/skills/`에 두고, 여기에도 커밋해 두면 웹과 동기화된다.
