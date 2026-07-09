---
name: research
user-invocable: true
allowed-tools: Read, Write, Glob, WebSearch, Task, AskUserQuestion
description: Conduct preliminary research on a topic and generate research outline. For academic research, benchmark research, technology selection, etc.
---

# Research Skill - Preliminary Research

## Trigger
`/research <topic>`

## Workflow

### Step 1: Generate Initial Framework from Model Knowledge
Based on topic, use model's existing knowledge to generate:
- Main research objects/items list in this domain
- Suggested research field framework

Output {step1_output}, use AskUserQuestion to confirm:
- Need to add/remove items?
- Does field framework meet requirements?

### Step 2: Web Search Supplement
Use AskUserQuestion to ask for time range (e.g., last 6 months, since 2024, unlimited).

**Parameter Retrieval**:
- `{topic}`: User input research topic
- `{YYYY-MM-DD}`: Current date
- `{step1_output}`: Complete output from Step 1
- `{time_range}`: User specified time range

**Hard Constraint**: The following prompt must be strictly reproduced, only replacing variables in {xxx}, do not modify structure or wording.

Launch 1 web-search-agent (background), **Prompt Template**:
```python
prompt = f"""## Task
Research topic: {topic}
Current date: {YYYY-MM-DD}

Based on the following initial framework, supplement latest items and recommended research fields.

## Existing Framework
{step1_output}

## Goals
1. Verify if existing items are missing important objects
2. Supplement items based on missing objects
3. Continue searching for {topic} related items within {time_range} and supplement
4. Supplement new fields

## Output Requirements
Return structured results directly (do not write files):

### Supplementary Items
- item_name: Brief explanation (why it should be added)
...

### Recommended Supplementary Fields
- field_name: Field description (why this dimension is needed)
...

### Sources
- [Source1](url1)
- [Source2](url2)
"""
```

**One-shot Example** (assuming researching AI Coding History):
```
## Task
Research topic: AI Coding History
Current date: 2025-12-30

Based on the following initial framework, supplement latest items and recommended research fields.

## Existing Framework
### Items List
1. GitHub Copilot: Developed by Microsoft/GitHub, first mainstream AI coding assistant
2. Cursor: AI-first IDE, based on VSCode
...

### Field Framework
- Basic Info: name, release_date, company
- Technical Features: underlying_model, context_window
...

## Goals
1. Verify if existing items are missing important objects
2. Supplement items based on missing objects
3. Continue searching for AI Coding History related items within since 2024 and supplement
4. Supplement new fields

## Output Requirements
Return structured results directly (do not write files):

### Supplementary Items
- item_name: Brief explanation (why it should be added)
...

### Recommended Supplementary Fields
- field_name: Field description (why this dimension is needed)
...

### Sources
- [Source1](url1)
- [Source2](url2)
```

### Step 3: Ask User for Existing Fields
Use AskUserQuestion to ask if user has existing field definition file, if so read and merge.

### Step 4: Generate Outline (Separate Files)
Merge {step1_output}, {step2_output} and user's existing fields, generate two files.

**Hard Constraint — Schema Compliance**: `fields.yaml` and `outline.yaml` MUST follow the exact schemas below. These keys are consumed literally by `validate_json.py` (`field_categories[].category`, `fields[].name`, `fields[].required`) and by `/research-deep` and `/research-report`. Do NOT rename top-level keys, and do NOT flatten the structure. Getting a key wrong silently breaks validation and reporting downstream.

#### 4a. fields.yaml Schema (field definitions)

```yaml
# Top-level key MUST be `field_categories` (a list). Each entry is one category.
field_categories:
  - category: <category_key>        # REQUIRED. snake_case, English. Used as the JSON nesting key + report section.
    fields:
      - name: <field_key>           # REQUIRED. snake_case, English. Becomes the JSON key (stable across languages).
        description: <text>         # REQUIRED. What the field captures + expected format/unit.
        detail_level: brief         # REQUIRED. One of: brief | moderate | detailed  (how deep deep-research should go)
        required: true              # OPTIONAL, default false. If true, validate_json.py FAILS when the field is missing.

# Reserved. Leave empty at outline time; /research-deep auto-fills per-item uncertain fields into each item's JSON.
uncertain: []
```

Rules:
- `category` values SHOULD reuse the standard keys where they fit so reporting maps cleanly: `basic_info`, `technical_features`, `performance_metrics`, `milestone_significance`, `business_info`, `competition_ecosystem`, `history`, `market_positioning`. Add domain-specific categories freely when none fit.
- Field `name` and `category` are English snake_case (they are JSON keys, kept stable). Field *values* are filled later and may be any language.
- Mark only the truly essential fields `required: true` — over-marking causes spurious validation failures.

**Complete fields.yaml example** (AI Coding History):
```yaml
field_categories:
  - category: basic_info
    fields:
      - name: name
        description: Official product/tool name
        detail_level: brief
        required: true
      - name: release_date
        description: First public release date (YYYY-MM or YYYY-MM-DD)
        detail_level: brief
        required: true
      - name: company
        description: Developing company or organization
        detail_level: brief
        required: true
  - category: technical_features
    fields:
      - name: underlying_model
        description: Foundation model(s) powering the tool
        detail_level: moderate
        required: false
      - name: context_window
        description: Max context length supported, in tokens
        detail_level: brief
        required: false
  - category: milestone_significance
    fields:
      - name: key_events
        description: Ordered list of milestone events; each {date, event}
        detail_level: detailed
        required: false
uncertain: []
```

#### 4b. outline.yaml Schema (items + execution config)

```yaml
topic: <Research topic>             # REQUIRED. Human-readable, matches Step 1 topic.
topic_slug: <topic_slug>            # REQUIRED. lowercase, spaces -> _, special chars removed. Also the directory name.
items:                              # REQUIRED. One entry per research object.
  - name: <item name>               # REQUIRED. Display name; slugified to <name>.json in deep phase.
    category: <group label>         # OPTIONAL. Free-text grouping (e.g. "International Product").
    description: <one-line context> # REQUIRED. Short context passed to the deep-research agent.
execution:                          # REQUIRED.
  batch_size: <int>                 # Parallel agents per batch. Confirm via AskUserQuestion.
  items_per_agent: <int>            # Items each agent handles. Confirm via AskUserQuestion.
  output_dir: ./results             # Where deep-phase JSON is written. Default: ./results
```

**Complete outline.yaml example** (AI Coding History):
```yaml
topic: AI Coding History
topic_slug: ai_coding_history
items:
  - name: GitHub Copilot
    category: International Product
    description: Microsoft/GitHub, first mainstream AI coding assistant
  - name: Cursor
    category: International Product
    description: AI-first IDE based on VSCode
execution:
  batch_size: 3
  items_per_agent: 2
  output_dir: ./results
```

### Step 5: Output and Confirm
- Create directory: `./{topic_slug}/`
- Save: `outline.yaml` and `fields.yaml`
- Show to user for confirmation

## Output Path
```
{current_working_directory}/{topic_slug}/
  ├── outline.yaml    # items list + execution config
  └── fields.yaml     # field definitions
```

## Follow-up Commands
- `/research-add-items` - Supplement items
- `/research-add-fields` - Supplement fields
- `/research-deep` - Start deep research
