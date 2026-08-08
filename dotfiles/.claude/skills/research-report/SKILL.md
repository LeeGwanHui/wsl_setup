---
name: research-report
user-invocable: true
description: Summarize deep research results into markdown report, cover all fields, skip uncertain values.
allowed-tools: Read, Write, Glob, Bash, AskUserQuestion
---

# Research Report - Summary Report

## Trigger
`/research-report`

## Workflow

### Step 1: Locate Results Directory
Find `*/outline.yaml` in current working directory, read topic and output_dir config.

### Step 2: Scan Optional Summary Fields
Read all JSON results, extract fields suitable for TOC display (numeric, short metrics), e.g.:
- github_stars
- google_scholar_cites
- swe_bench_score
- user_scale
- valuation
- release_date

Use AskUserQuestion to ask user:
- Which fields to display in TOC besides item name?
- Provide dynamic options list (based on actual fields in JSON)

### Step 3: Generate Python Conversion Script
Generate `generate_report.py` in `{topic}/` directory, script requirements:
- Read all JSON from output_dir
- Read fields.yaml to get field structure
- Cover all field values from each JSON
- Skip fields with values containing [uncertain]
- Skip fields listed in uncertain array
- Generate markdown report format: Table of contents (with anchor links + user-selected summary fields) + Detailed content (by field category)
- Save to `{topic}/report.md`

**TOC Format Requirements**:
- Must include every item
- Each item displays: number, name (anchor link), user-selected summary fields
- Example: `1. [GitHub Copilot](#github-copilot) - Stars: 10k | Score: 85%`

#### Script Technical Requirements (Must Follow)

**1. JSON Structure Compatibility**
Support two JSON structures:
- Flat structure: Fields directly at top level `{"name": "xxx", "release_date": "xxx"}`
- Nested structure: Fields in category sub-dict `{"basic_info": {"name": "xxx"}, "technical_features": {...}}`

Field lookup order: Top level -> category mapping key -> Traverse all nested dicts

**2. Category Mapping (Derive Dynamically from fields.yaml)**
Do NOT hardcode the category list — it breaks for domain-specific categories. Derive the category keys at runtime from `fields.yaml`'s `field_categories[].category`, so any topic works. Keep only a small builtin alias table for backward compatibility with legacy JSON that nested under a different key, then union it with the categories actually declared in fields.yaml:
```python
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

def build_category_keys(fields_yaml):
    """For each category declared in fields.yaml, the set of JSON keys that may hold it:
    the category name itself plus any known aliases."""
    mapping = {}
    for cat in fields_yaml.get("field_categories", []):
        name = cat["category"]
        mapping[name] = sorted(set([name] + BUILTIN_CATEGORY_ALIASES.get(name, [])))
    return mapping
```
This mirrors `validate_json.py`'s `build_nested_keys()`, so the report and the validator agree on how categories are resolved.

**3. Complex Value Formatting**
- list of dicts (e.g., key_events, funding_history): Format each dict as one line, separate kv with ` | `
- Normal list: Short lists joined with comma, long lists displayed with line breaks
- Nested dict: Recursive formatting, display with semicolon or line breaks
- Long text strings (over 100 chars): Add line breaks `<br>` or use blockquote format for readability

**4. Extra Fields Collection**
Collect fields that exist in JSON but not defined in fields.yaml, put in "Other Info" category. Note to filter:
- Internal fields: `_source_file`, `uncertain`
- Nested structure top-level keys: `basic_info`, `technical_features` etc.
- `uncertain` array: Display each field name on separate line, don't compress into one line

**5. Uncertain Value Skipping**
Skip conditions:
- Field value contains `[uncertain]` string
- Field name is in `uncertain` array
- Field value is None or empty string

### Step 4: Execute Script
Run `python {topic}/generate_report.py`

## Output
- `{topic}/generate_report.py` - Conversion script
- `{topic}/report.md` - Summary report
