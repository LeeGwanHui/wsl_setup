#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert results/*.json into a single markdown report.

Reads outline.yaml (topic, item order, output_dir) and fields.yaml (field
structure), then renders results/*.json into report.md.

Rules enforced here (per the research-report skill):
  - every item in outline.yaml appears in the TOC
  - fields whose value contains "[uncertain]" are skipped
  - fields listed in a result's "uncertain" array are skipped
  - empty / None values are skipped
  - category keys are derived from fields.yaml at runtime, never hardcoded
"""

import json
import re
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent

# Legacy aliases only; the authoritative keys come from fields.yaml.
BUILTIN_CATEGORY_ALIASES = {
    "basic_info": ["basic_info", "Basic Info"],
    "technical_features": ["technical_features", "technical_characteristics", "Technical Features"],
    "performance_metrics": ["performance_metrics", "performance", "Performance Metrics"],
    "milestone_significance": ["milestone_significance", "milestones", "Milestone Significance"],
    "business_info": ["business_info", "commercial_info", "Business Info"],
    "competition_ecosystem": ["competition_ecosystem", "competition", "Competition & Ecosystem"],
    "history": ["history", "History"],
    "market_positioning": ["market_positioning", "market", "Market Positioning"],
}

SKIP_KEYS = {"_source_file", "uncertain"}

# Human-readable headings for this topic's categories.
CATEGORY_LABELS = {
    "basic_info": "기본 정보",
    "scope_and_loading": "스코프 / 로딩",
    "popularity_adoption": "채택도",
    "recommended_config": "추천 설정",
    "best_practices": "모범 사례",
    "recent_changes": "최근 변경",
}

FIELD_LABELS = {
    "setting_name": "설정 명칭",
    "file_location": "파일 위치",
    "official_doc_status": "공식 문서",
    "version_introduced": "도입 버전",
    "scope_layer": "우선순위 계층",
    "loading_trigger": "로딩 시점",
    "context_cost": "컨텍스트 비용",
    "adoption_evidence": "채택 근거",
    "config_snippet": "설정 스니펫",
    "determinism_vs_flexibility": "결정적 vs 권고적",
    "best_practices": "모범 사례",
    "anti_patterns": "안티패턴",
    "security_risk_level": "보안 리스크",
    "recent_changes": "최근 변경 내역",
    "lifecycle_status": "라이프사이클",
}

# Fields rendered as fenced code blocks rather than prose.
CODE_FIELDS = {"config_snippet"}

# True: render uncertain fields with a ⚠️ marker. False: drop them (skill default).
MARK_UNCERTAIN = True

# --- TOC summary fields chosen by the user -------------------------------
RISK_GRADES = [
    ("위험", ["위험", "DANGEROUS", "HIGH RISK"]),
    ("주의", ["주의", "CAUTION", "MODERATE"]),
    ("안전", ["안전", "SAFE", "LOW RISK"]),
]
LIFECYCLE_GRADES = [
    ("Experimental", ["EXPERIMENTAL", "실험적", "RESEARCH PREVIEW"]),
    ("Deprecated", ["DEPRECATED", "지원중단"]),
    ("Beta", ["BETA"]),
    ("Stable", ["STABLE", "정식", "GENERALLY AVAILABLE", "GA"]),
]


def load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_category_keys(fields_yaml):
    """For each category declared in fields.yaml, the set of JSON keys that may
    hold it: the category name itself plus any known aliases."""
    mapping = OrderedDict()
    for cat in fields_yaml.get("field_categories", []):
        name = cat["category"]
        mapping[name] = sorted(set([name] + BUILTIN_CATEGORY_ALIASES.get(name, [])))
    return mapping


def norm(s):
    """Normalize a name so an outline item can be matched to its result file."""
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", str(s)).lower()


def github_anchor(heading):
    a = heading.strip().lower()
    a = re.sub(r"[^\w\s\-가-힣]", "", a)
    return re.sub(r"\s+", "-", a).strip("-")


def find_field(data, field, category_keys):
    """Locate a field value: top level, then its category container, then any
    nested dict. Returns None when absent."""
    if field in data and not isinstance(data[field], dict):
        return data[field]
    for keys in category_keys.values():
        for key in keys:
            container = data.get(key)
            if isinstance(container, dict) and field in container:
                value = container[field]
                if not isinstance(value, dict):
                    return value
    for value in data.values():
        if isinstance(value, dict) and field in value and not isinstance(value[field], dict):
            return value[field]
    return None


def classify(value, field, uncertain_list):
    """Return "empty" (drop), "uncertain" (render with a marker), or "ok".

    The skill's default is to drop uncertain fields outright. For this topic that
    removed version_introduced from 18/19 items and recent_changes from 13/19 —
    the official docs rarely version-stamp features, so nearly every result flags
    those fields. Marking beats dropping here: the content is still useful, it is
    just not authoritative. Set MARK_UNCERTAIN = False to restore the default.
    """
    if value is None:
        return "empty"
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if not text.strip():
        return "empty"
    if field in uncertain_list or "[uncertain]" in text:
        return "uncertain"
    return "ok"


def format_value(value, indent=0):
    """Render a JSON value as markdown."""
    pad = "  " * indent
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(v, dict) for v in value):
            lines = []
            for item in value:
                parts = [f"**{k}**: {v}" for k, v in item.items() if v not in (None, "")]
                lines.append(f"{pad}- " + " | ".join(parts))
            return "\n".join(lines)
        flat = [str(v).strip() for v in value if str(v).strip()]
        joined = ", ".join(flat)
        if len(joined) <= 100 and not any("\n" in s for s in flat):
            return joined
        return "\n".join(f"{pad}- {s}" for s in flat)
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            rendered = format_value(v, indent + 1)
            if not rendered:
                continue
            label = FIELD_LABELS.get(k, k)
            if "\n" in rendered:
                lines.append(f"{pad}- **{label}**:\n{rendered}")
            else:
                lines.append(f"{pad}- **{label}**: {rendered}")
        return "\n".join(lines)
    return str(value)


def grade_of(text, table, fallback):
    """Pick the grade whose marker appears earliest in the text."""
    if not text:
        return fallback
    head = str(text)[:200].upper()
    best, best_pos = fallback, len(head) + 1
    for label, markers in table:
        for marker in markers:
            pos = head.find(marker.upper())
            if pos != -1 and pos < best_pos:
                best, best_pos = label, pos
    return best


def main():
    outline = load_yaml(BASE / "outline.yaml")
    fields_yaml = load_yaml(BASE / "fields.yaml")
    category_keys = build_category_keys(fields_yaml)

    out_dir = BASE / outline.get("execution", {}).get("output_dir", "./results").lstrip("./")
    results = {}
    for path in sorted(out_dir.glob("*.json")):
        results[norm(path.stem)] = (path, json.load(path.open(encoding="utf-8")))

    known_fields = [
        (cat["category"], f["name"])
        for cat in fields_yaml.get("field_categories", [])
        for f in cat.get("fields", [])
    ]
    known_field_names = {name for _, name in known_fields}
    container_keys = {k for keys in category_keys.values() for k in keys}

    items, missing, used = [], [], set()
    for entry in outline.get("items", []):
        key = norm(entry["name"])
        if key not in results:
            missing.append(entry["name"])
            continue
        used.add(key)
        path, data = results[key]
        items.append((entry, path, data))

    for key, (path, data) in results.items():
        if key not in used:
            items.append(({"name": path.stem, "category": ""}, path, data))

    lines = []
    topic = outline.get("topic", "Research Report")
    lines.append(f"# {topic}")
    lines.append("")
    lines.append(
        f"> 생성일 {date.today().isoformat()} · 항목 {len(items)}개 · "
        f"출처 `{out_dir.name}/`"
    )
    lines.append(">")
    if MARK_UNCERTAIN:
        lines.append(
            "> 값에 `[uncertain]`이 포함되었거나 각 결과의 `uncertain` 배열에 등재된 필드는 "
            "제목 옆에 ⚠️ 로 표시됩니다. 내용은 참고용이며 공식 문서로 확정된 값이 아닙니다 "
            "— 특히 도입 버전은 공식 문서가 기능별로 명시하지 않아 커뮤니티 체인지로그에 의존했습니다."
        )
    else:
        lines.append(
            "> 값에 `[uncertain]`이 포함되었거나 각 결과의 `uncertain` 배열에 등재된 필드는 "
            "이 보고서에서 생략됩니다."
        )
    if missing:
        lines.append(">")
        lines.append("> 미조사 항목: " + ", ".join(missing))
    lines.append("")

    # ---------------------------------------------------------------- TOC
    lines.append("## 목차")
    lines.append("")
    lines.append("| # | 항목 | 보안 리스크 | 라이프사이클 |")
    lines.append("|---|---|---|---|")

    toc_rows, sections = [], []
    for idx, (entry, path, data) in enumerate(items, 1):
        name = entry["name"]
        heading = f"{idx}. {name}"
        anchor = github_anchor(heading)
        uncertain_list = data.get("uncertain") or []

        risk_raw = find_field(data, "security_risk_level", category_keys)
        life_raw = find_field(data, "lifecycle_status", category_keys)
        risk = grade_of(risk_raw, RISK_GRADES, "—")
        life = grade_of(life_raw, LIFECYCLE_GRADES, "—")
        toc_rows.append(f"| {idx} | [{name}](#{anchor}) | {risk} | {life} |")

        # ------------------------------------------------------ section
        body = [f"## {heading}", ""]
        if entry.get("category"):
            body.append(f"`{entry['category']}`")
            body.append("")

        skipped = []
        for cat_name in category_keys:
            cat_fields = [f for c, f in known_fields if c == cat_name]
            rendered = []
            for field in cat_fields:
                value = find_field(data, field, category_keys)
                verdict = classify(value, field, uncertain_list)
                if verdict == "empty":
                    continue
                if verdict == "uncertain":
                    skipped.append(field)
                    if not MARK_UNCERTAIN:
                        continue
                label = FIELD_LABELS.get(field, field)
                if verdict == "uncertain":
                    label += " ⚠️"
                text = format_value(value)
                if not text:
                    continue
                if field in CODE_FIELDS:
                    runs = re.findall(r"`+", text)
                    fence = "`" * max(3, max((len(r) for r in runs), default=0) + 1)
                    rendered.append(f"**{label}**\n\n{fence}\n{text}\n{fence}")
                else:
                    rendered.append(f"**{label}**\n\n{text}")
            if rendered:
                body.append(f"### {CATEGORY_LABELS.get(cat_name, cat_name)}")
                body.append("")
                body.append("\n\n".join(rendered))
                body.append("")

        # ------------------------------------------------- extra fields
        extras = []
        for key, value in data.items():
            if key in SKIP_KEYS or key in container_keys or key in known_field_names:
                continue
            text = format_value(value)
            if text:
                extras.append(f"**{key}**\n\n{text}")
        if extras:
            body.append("### 기타 정보")
            body.append("")
            body.append("\n\n".join(extras))
            body.append("")

        if skipped or uncertain_list:
            summary = (
                "이 항목에서 ⚠️ 로 표시된 불확실 필드"
                if MARK_UNCERTAIN
                else "불확실하여 생략된 필드"
            )
            body.append(f"<details><summary>{summary}</summary>")
            body.append("")
            for field in sorted(set(skipped) | set(uncertain_list)):
                body.append(f"- {FIELD_LABELS.get(field, field)} (`{field}`)")
            body.append("")
            body.append("</details>")
            body.append("")

        body.append(f"<sub>출처: `{out_dir.name}/{path.name}`</sub>")
        body.append("")
        sections.append("\n".join(body))

    lines.extend(toc_rows)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("\n---\n\n".join(sections))

    report = BASE / "report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {report} ({report.stat().st_size} bytes, {len(items)} items)")
    if missing:
        print("WARNING missing results for:", ", ".join(missing), file=sys.stderr)


if __name__ == "__main__":
    main()
