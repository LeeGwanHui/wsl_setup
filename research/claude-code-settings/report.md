# Claude Code settings.json / CLAUDE.md 개발자 모범 설정

> 생성일 2026-08-08 · 항목 19개 · 출처 `results/`
>
> 값에 `[uncertain]`이 포함되었거나 각 결과의 `uncertain` 배열에 등재된 필드는 제목 옆에 ⚠️ 로 표시됩니다. 내용은 참고용이며 공식 문서로 확정된 값이 아닙니다 — 특히 도입 버전은 공식 문서가 기능별로 명시하지 않아 커뮤니티 체인지로그에 의존했습니다.

## 목차

| # | 항목 | 보안 리스크 | 라이프사이클 |
|---|---|---|---|
| 1 | [Permissions](#1-permissions) | 위험 | Stable |
| 2 | [Hooks](#2-hooks) | 위험 | Stable |
| 3 | [Environment Variables](#3-environment-variables) | 주의 | Stable |
| 4 | [Model 설정](#4-model-설정) | 주의 | Stable |
| 5 | [StatusLine 커스터마이징](#5-statusline-커스터마이징) | 주의 | Stable |
| 6 | [MCP 서버 설정](#6-mcp-서버-설정) | 위험 | Stable |
| 7 | [Subagents](#7-subagents) | 주의 | Stable |
| 8 | [Slash Commands](#8-slash-commands) | 주의 | Stable |
| 9 | [Output Styles](#9-output-styles) | 안전 | Stable |
| 10 | [CLAUDE.md 구조 및 계층](#10-claudemd-구조-및-계층) | 안전 | Stable |
| 11 | [Sandbox / 위험 작업 안전설정](#11-sandbox-위험-작업-안전설정) | 위험 | Stable |
| 12 | [settings 파일 계층 (user/project/local)](#12-settings-파일-계층-userprojectlocal) | 주의 | Stable |
| 13 | [Skills](#13-skills) | 주의 | Stable |
| 14 | [Plugins & Plugin Marketplaces](#14-plugins-plugin-marketplaces) | 주의 | Stable |
| 15 | [Auto Mode & 권한 분류기](#15-auto-mode-권한-분류기) | 주의 | Stable |
| 16 | [Rules (경로 스코프 규칙)](#16-rules-경로-스코프-규칙) | 안전 | Stable |
| 17 | [Managed/Enterprise 정책 설정](#17-managedenterprise-정책-설정) | 안전 | Stable |
| 18 | [Telemetry / OpenTelemetry 설정](#18-telemetry-opentelemetry-설정) | 주의 | Stable |
| 19 | [Agent Teams & Dynamic Workflows](#19-agent-teams-dynamic-workflows) | 주의 | Experimental |

---

## 1. Permissions

`권한/보안`

### 기본 정보

**설정 명칭**

permissions

**파일 위치**

.claude/settings.json (project, shared/committed), .claude/settings.local.json (project-local, gitignored), ~/.claude/settings.json (user/global), and managed/enterprise policy files (managed-settings.json at /Library/Application Support/ClaudeCode/ on macOS, /etc/claude-code/ on Linux/WSL, C:\Program Files\ClaudeCode\ on Windows). The permissions object holds allow/deny/ask arrays plus defaultMode and additionalDirectories. Manage interactively with the /permissions command.

**공식 문서**

Officially documented with a dedicated page. Primary: https://code.claude.com/docs/en/permissions (Configure permissions). Related: https://code.claude.com/docs/en/settings (settings reference and precedence), https://code.claude.com/docs/en/permission-modes, https://code.claude.com/docs/en/sandboxing, https://code.claude.com/docs/en/iam. Starter example settings: https://github.com/anthropics/claude-code/tree/main/examples/settings

**도입 버전 ⚠️**

[uncertain] The permissions system has existed since early Claude Code releases and predates most versioned docs, so no single introduction version/date is authoritative. Individual refinements are versioned: the `manual` alias for `default` mode requires v2.1.200+, workspace-trust handling of settings.local.json was fixed in v2.1.200, and gitignore character escaping in generated path rules landed in v2.1.202.

### 스코프 / 로딩

**우선순위 계층**

Permission rules follow the standard settings precedence, highest to lowest: (1) Managed/enterprise settings (cannot be overridden by anything, including CLI args), (2) Command-line arguments (--allowedTools/--disallowedTools, session-only), (3) Local project settings .claude/settings.local.json, (4) Shared project settings .claude/settings.json, (5) User settings ~/.claude/settings.json. Unlike most settings which override, permission rules MERGE across all scopes. Crucially, deny is absolute across scopes: if a tool/pattern is denied at ANY level, no other level can allow it (a user-level deny blocks a project-level allow and vice-versa), because deny rules from every scope are evaluated before allow rules. Within a single evaluation the order is deny -> ask -> allow, first match wins, and specificity does NOT change the order (a broad deny beats a narrow allow). Managed settings can set allowManagedPermissionRulesOnly:true to forbid user/project scopes from defining allow/ask/deny rules at all.

**로딩 시점**

Loaded at session start from all applicable settings files and enforced by Claude Code (the harness) on every tool call, NOT by the model. Instructions in the prompt or CLAUDE.md cannot change what is allowed. Project-level allow rules and additionalDirectories are read at startup but only APPLIED after the user accepts the workspace-trust dialog; deny and ask rules apply immediately without trust. Rules are re-evaluated per tool invocation; PreToolUse hooks run before the permission prompt and can further deny/ask/skip, but cannot override deny/ask rules (deny-first precedence is preserved).

**컨텍스트 비용**

Negligible/zero token cost. Permission rules are enforcement metadata evaluated by the harness and are not injected into the model context. A bare-tool deny rule (e.g. `Bash` or `mcp__*`) actually REDUCES context by removing that tool's schema from what the model sees, whereas a scoped deny like `Bash(rm *)` leaves the tool visible and only blocks matching calls.

### 채택도

**채택 근거**

Core, near-universal feature of Claude Code configuration; heavily covered by community. Official starter configs shipped in the anthropics/claude-code repo (examples/settings). Widely written up: DEV Community guides ('Lock Down Claude Code With 5 Permission Patterns', 'settings.json: the one config file most developers ignore'), ClaudeCodeLab, claudefa.st settings/permissions guides, claudedirectory.org 2026 permissions guide, and numerous blog posts. Active GitHub issue traffic (e.g. #4956 command-chaining bypass, #20254 pattern-limitation docs, #28784 cd:* chaining) indicates broad real-world use.

### 추천 설정

**설정 스니펫**

```
{
  "permissions": {
    "defaultMode": "default",
    "additionalDirectories": ["../shared-lib"],
    "allow": [
      "Bash(npm run test:*)",
      "Bash(npm run lint)",
      "Bash(git commit:*)",
      "Bash(git diff:*)",
      "Read(./src/**)",
      "WebFetch(domain:docs.anthropic.com)"
    ],
    "ask": [
      "Bash(git push:*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git reset --hard:*)",
      "Bash(git push --force*)",
      "Bash(git push * --force*)",
      "Bash(git clean -fd*)",
      "Bash(terraform destroy*)",
      "Bash(kubectl delete*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(**/*.pem)",
      "Read(~/.ssh/**)"
    ],
    "disableBypassPermissionsMode": "disable"
  }
}

// Notes:
// - Rule syntax is Tool or Tool(specifier). `Tool(param:value)` matches a top-level
//   input parameter (deny/ask only), e.g. Agent(model:opus), Bash(run_in_background:true).
// - The `:*` suffix == a trailing ` *` (word-boundary). `Bash(ls:*)` == `Bash(ls *)`.
// - Deny-all a tool: `"deny": ["Bash"]` or `"Bash(*)"` removes the tool from context.
// - Deny every MCP tool: `"deny": ["mcp__*"]`; `"*"` in deny matches every tool.
// - Read/Edit use gitignore-style globs: //abs, ~/home, /project-anchored, ./cwd, ** across dirs.
```

**결정적 vs 권고적**

Deterministic / code-enforced. Permission rules are applied by the Claude Code harness on every tool call, not advisory to the model. A matching deny hard-blocks the call and a matching ask hard-forces a prompt regardless of prompt or CLAUDE.md instructions. Caveat: enforcement is application-level and Bash argument matching is prefix/pattern based, so it is deterministic about WHICH string patterns it blocks but is NOT a substitute for OS-level isolation. For guaranteed enforcement against subprocesses and argument-smuggling, pair deny rules with sandboxing (OS-level, /sandbox) and/or PreToolUse hooks.

### 모범 사례

**모범 사례**

1) Deny-first for irreversible/destructive operations: git reset --hard, git push --force (deny BOTH flag positions), git clean -fd, rm -rf, terraform destroy, kubectl delete, DROP TABLE, etc. Deny wins over any allow at any scope. 2) Protect secrets with Read deny globs: Read(./.env), Read(./.env.*), Read(./secrets/**), Read(**/*.pem), Read(~/.ssh/**); remember these also cover recognized Bash file readers (cat/head/tail/sed) but NOT arbitrary scripts. 3) Do NOT rely on Bash rules to constrain command ARGUMENTS (e.g. limiting curl to a domain) - patterns are bypassable via flags, protocols, redirects, variables, extra spaces, and command chaining. Instead deny curl/wget/network tools outright and allow specific hosts via WebFetch(domain:...). 4) Use `ask` for intent-changing but sometimes-needed ops (git push, git commit, Write/Edit in sensitive areas) and `allow` for safe read/verify commands (tests, lint, git status/diff/log) to cut prompt fatigue. 5) Put organization-wide non-negotiable denies in managed settings, optionally with allowManagedPermissionRulesOnly / disableBypassPermissionsMode / disableAutoMode set to "disable" so users can't loosen them. 6) Layer defenses: permissions (which tools/paths) + sandboxing (OS-level Bash filesystem/network enforcement, survives prompt injection) + PreToolUse hooks (custom runtime validation, exit code 2 blocks before allow rules). 7) Prefer specific runner+inner-command rules (Bash(devbox run npm test)) because env runners/exec wrappers like devbox/npx/docker exec/watch/find -exec are not auto-covered by a prefix rule. 8) Keep .claude/settings.local.json gitignored for personal rules; commit shared team rules in .claude/settings.json.

**안티패턴**

1) Trusting Bash argument constraints for security (e.g. Bash(curl https://github.com/ *)) - trivially bypassed; the docs explicitly warn against it. 2) Denying Read(./.env) but forgetting the file can be exfiltrated via a subprocess/script the Read rule doesn't cover - use sandboxing for hard enforcement. 3) Only denying one force-push spelling; must deny both `--force` before and after the remote (git push --force* AND git push * --force*). 4) Assuming allow rules override a deny - they never do; deny is evaluated first at every scope. 5) Assuming a narrow allow creates an exception to a broad deny - it doesn't (Bash(aws *) deny blocks even Bash(aws s3 ls) allow). 6) Using bypassPermissions mode (or leaving auto mode enabled) in a non-isolated environment - one bypass session undoes every rule; restrict via disableBypassPermissionsMode/disableAutoMode. 7) Committing settings.local.json (leaks personal rules / can trigger workspace-trust suppression of its allow rules). 8) Writing a rule for a tool's transcript label (e.g. 'Stop Task') instead of its canonical name (TaskStop) - it silently won't match. 9) Trying to gate canonicalized fields via param syntax (Bash(command:rm *)) - ignored with a startup warning; use Bash(rm *). 10) Expecting a single leading slash to mean filesystem-absolute in Read/Edit - /path anchors at the settings source; use //path for true absolute.

**보안 리스크**

위험/주의 (High-importance, security-critical control). Permissions are the primary guardrail deciding what an autonomous agent may execute, so misconfiguration is directly dangerous. Deny rules for destructive commands are the main safety net against events like the well-known accidental `git reset --hard` data loss. Key residual risks: Bash pattern matching is prefix/string based and bypassable (command chaining, flag reordering, env runners, redirects), so application-level rules alone are NOT a strong boundary - treat them as convenience + first line, and add OS-level sandboxing and/or PreToolUse hooks for real enforcement. bypassPermissions and auto modes are the highest-risk settings and should be disabled outside isolated containers/VMs.

### 최근 변경

**최근 변경 내역 ⚠️**

Active area of change through 2026 H1: (a) `Tool(param:value)` parameter-matching for deny/ask rules (e.g. Agent(model:opus), Agent(isolation:worktree), Bash(run_in_background:true)); (b) tool-name glob rules in deny/ask, e.g. `mcp__*` denies all MCP tools and `*` matches every tool; (c) `dontAsk` and `auto` permission modes added, plus `manual` as an alias/label for `default` (v2.1.200+); (d) workspace-trust handling of .claude/settings.local.json fixed - v2.1.196-2.1.199 wrongly ignored its allow rules, restored in v2.1.200; (e) gitignore special-character escaping in auto-generated path rules (v2.1.202); (f) tightened integration with sandboxing (autoAllowBashIfSandboxed default true; sandbox filesystem/network boundaries merge with Read/Edit deny and WebFetch domain rules); (g) managed-only controls expanded: allowManagedPermissionRulesOnly, allowManagedMcpServersOnly, sandbox.network.allowManagedDomainsOnly, disableSideloadFlags (v2.1.193+); (h) `Cd` rules to gate the /cd command. Exact release dates for individual permission features are [uncertain].

**라이프사이클**

Stable and actively maintained (GA). It is a core, non-experimental part of Claude Code configuration. Complementary sandboxing is also GA. No deprecation announced; the feature set is being extended (param matching, tool-name globs, new modes) rather than wound down.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Permissions.json`</sub>

---

## 2. Hooks

`자동화/확장`

### 기본 정보

**설정 명칭**

hooks

**파일 위치**

Configured under the top-level "hooks" key in any settings file: ~/.claude/settings.json (user, all projects), .claude/settings.json (project, shareable/committable), .claude/settings.local.json (project, gitignored), managed policy settings (organization-wide), plugin hooks/hooks.json (when a plugin is enabled), and skill/subagent frontmatter (while that component is active). Hook scripts themselves are conventionally stored in .claude/hooks/. Browse configured hooks with the read-only /hooks menu.

**공식 문서**

Yes. Two official pages: reference at https://code.claude.com/docs/en/hooks (full event schemas, JSON input/output, exit codes, async/HTTP/MCP/prompt/agent hooks) and guide at https://code.claude.com/docs/en/hooks-guide (setup walkthrough, common patterns, troubleshooting). A reference Bash validator example lives at https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py

**도입 버전 ⚠️**

Initially introduced ~June 2025 (PreToolUse, PostToolUse, Notification, Stop, SubagentStop, and the core settings.json schema). The event surface has expanded substantially since. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Hooks follow the standard settings precedence: managed policy settings > project local (.claude/settings.local.json) > project shared (.claude/settings.json) > user (~/.claude/settings.json), plus plugin and skill/agent-frontmatter layers. Hooks are additive rather than overriding: when multiple hooks match one event, all of them run in parallel (identical commands are deduplicated) and their outputs are merged. For PreToolUse permission decisions the most restrictive answer wins, in the order deny > defer > ask > allow. additionalContext text from every matching hook is kept and passed to Claude together. Hooks configured in managed settings still run even when "disableAllHooks": true is set at a lower layer (managed settings must also set it).

**로딩 시점**

Executed outside the model's context: the harness fires a hook deterministically at its lifecycle point (session start/end, prompt submit, before/after a tool call, on notification, on stop, on compaction, etc.). The matcher (and optional "if" permission-rule filter) decides whether a given hook runs for a given occurrence. Command hooks receive event JSON on stdin and communicate back via stdout/stderr/exit code; HTTP hooks receive the same JSON as a POST body. Settings-file edits are normally hot-reloaded by the file watcher.

**컨텍스트 비용**

The hook configuration itself consumes no model context (it is harness config, not loaded into the prompt). Runtime cost is opt-in: only hooks that emit additionalContext, stdout on UserPromptSubmit/SessionStart, or systemMessage inject text into Claude's context. type:"prompt" and type:"agent" hooks additionally spend tokens on a separate model call/subagent when they fire.

### 채택도

**채택 근거 ⚠️**

Widely adopted as the primary deterministic-control primitive for Claude Code. Popular community resources include the disler/claude-code-hooks-mastery GitHub repo, luongnv89/claude-howto, and numerous 2026 production guides/blogs (morphllm, thepromptshelf, totalum, pixelmojo, claudefast, hidekazu-konishi). Anthropic ships a first-party security-guidance plugin that integrates via hooks, and hooks are the standard mechanism bundled inside plugins (hooks/hooks.json). [uncertain]

### 추천 설정

**설정 스니펫**

```
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(git push *)",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-git-policy.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "echo 'Reminder: run tests before committing.'" }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "notify-send 'Claude Code' 'needs your attention'" }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          { "type": "command", "command": "git log --oneline -5" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if all tasks are complete. If not, respond with {\"ok\": false, \"reason\": \"what remains\"}."
          }
        ]
      }
    ]
  },
  "disableAllHooks": false
}

// A PreToolUse command-hook script that blocks with structured JSON (stdout, exit 0):
// {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Use rg instead of grep"}}
// Or block via exit code: write reason to stderr and exit 2.
```

**결정적 vs 권고적**

Primarily deterministic: command/HTTP/mcp_tool hooks are code-enforced guarantees that always run at their lifecycle point, independent of model judgment (the headline use case). Two handler types are advisory/judgment-based: type:"prompt" (single Claude call returning ok/reason) and type:"agent" (subagent verification, experimental). Even structured control has hard limits: a PreToolUse "deny" fires before any permission-mode check and cannot be bypassed by bypassPermissions/--dangerously-skip-permissions, but a hook "allow" cannot override deny/ask permission rules (hooks can tighten, not loosen).

### 모범 사례

**모범 사례**

1) Use hooks for guarantees you don't want to depend on the LLM choosing (formatting, protected-file blocking, audit logging, notifications). 2) Keep matchers as narrow as possible; auto-approval hooks (PermissionRequest returning allow) must never use empty/'.*' matcher. 3) Use the "if" field (permission-rule syntax like Bash(git *), Edit(*.ts), v2.1.85+) to filter by tool arguments so the process only spawns on real matches. 4) Reference scripts via "$CLAUDE_PROJECT_DIR"/${CLAUDE_PLUGIN_ROOT}, make them chmod +x, and use exec form ("args": []) to avoid shell-quoting issues. 5) For Stop hooks that loop, parse stop_hook_active and exit 0 when true to avoid the 8-consecutive-block cap (raise via CLAUDE_CODE_STOP_HOOK_BLOCK_CAP). 6) Block with exit 2 + stderr OR exit 0 + JSON, never both. 7) For per-file-change coverage, remember Bash can also modify files, so also add a Stop hook that scans the working tree. 8) Guard shell profiles with an interactive-shell check ($- == *i*) so stray echo output doesn't corrupt hook JSON. 9) Debug with /hooks, Ctrl+O transcript view, and claude --debug-file. 10) Prefer command hooks over experimental agent hooks for production.

**안티패턴**

Empty/'.*' matcher on PermissionRequest auto-approve (auto-approves file writes and shell commands). Relying on one hook's deny to suppress a sibling hook's side effects (all matching hooks run regardless). Multiple hooks returning updatedInput on the same tool (parallel, non-deterministic; last to finish wins). Mixing exit 2 with JSON stdout (JSON is ignored on exit 2). Assuming PostToolUse can undo an action (tool already ran). Using PermissionRequest hooks in -p/non-interactive mode (they don't fire there; use PreToolUse). Depending on a hook's "if" filter for hard security (it fails open on unparseable commands; use the permission system instead). Unconditional echo in shell profiles corrupting hook JSON output.

**보안 리스크**

위험 (high). Hooks execute arbitrary shell commands automatically with the user's full privileges at many lifecycle points, so a malicious or careless hook (especially from an untrusted repo's committed .claude/settings.json, plugin, or skill) is a code-execution vector; review hooks before deploying in shared/production environments. Conversely, hooks are also a key security control: PreToolUse deny cannot be bypassed by bypassPermissions, making them useful for enforcing guardrails users can't override. Handle secrets carefully (HTTP hooks resolve only allowedEnvVars-listed variables in headers).

### 최근 변경

**최근 변경 내역 ⚠️**

The event surface expanded well beyond the original set to 30+ events, now including SubagentStart, PostToolBatch, PostToolUseFailure, PermissionRequest, PermissionDenied, Setup, StopFailure, TeammateIdle, TaskCreated/TaskCompleted, UserPromptExpansion, InstructionsLoaded, ConfigChange, CwdChanged, FileChanged, WorktreeCreate/WorktreeRemove, PostCompact, MessageDisplay, Elicitation/ElicitationResult, plus SessionEnd. Handler types grew to five: command, http, mcp_tool, prompt, agent (agent experimental). Notable 2026 additions: async hooks (async/asyncRewake, ~Jan 2026); PostToolUse/PostToolUseFailure inputs gained duration_ms; PostToolUse can now replace output for all tools via hookSpecificOutput.updatedToolOutput (previously MCP-only); Notification matchers agent_needs_input/agent_completed (v2.1.198+); Edit,Write comma list separators (v2.1.191+); the "if" argument filter (v2.1.85+). [uncertain]

**라이프사이클**

Stable and actively developed core feature. Most events and the command/http/mcp_tool/prompt handler types are stable; type:"agent" hooks are explicitly experimental and may change (docs recommend command hooks for production).

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Hooks.json`</sub>

---

## 3. Environment Variables

`환경/모델`

### 기본 정보

**설정 명칭**

Environment Variables (settings.json `env` block and CLAUDE_CODE_* / ANTHROPIC_* environment variable flags)

**파일 위치**

Set inside the `env` object of any settings file (`~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, or managed `managed-settings.json`), or exported in the shell environment before launching `claude`. Some variables (identity/hosting variables such as `CLAUDE_CODE_REMOTE`) are honored only from the real shell environment, not from the `env` block.

**공식 문서**

Officially documented. Dedicated reference page 'Environment variables' at https://code.claude.com/docs/en/env-vars (redirected from https://docs.claude.com/en/docs/claude-code/settings). The `env` block itself is documented on the Settings page at https://code.claude.com/docs/en/settings. As of v2.1.207 Claude Code exposes 200+ environment variables and 80+ settings.

**도입 버전 ⚠️**

The `env` block and core auth variables (ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, HTTP(S)_PROXY) have existed since early Claude Code releases. Newer flags carry per-variable version tags in the docs, e.g. `env`-block color handling changed in v2.1.143, hosting identity variables ignored in `env` from v2.1.195, and `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS` from v2.1.198. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Environment variables set via the `env` block follow the same settings precedence as other settings: Managed (highest, cannot be overridden) > Command-line args > Local (`.claude/settings.local.json`) > Project (`.claude/settings.json`) > User (`~/.claude/settings.json`, lowest). Separately, an actual shell/exported environment variable generally takes precedence over the corresponding settings-file field it maps to (for example `ANTHROPIC_MODEL` overrides the `model` setting; `ANTHROPIC_API_KEY` overrides subscription auth). Values injected via `env` reach the Claude Code session and every subprocess it spawns (Bash/PowerShell commands, hooks, MCP servers).

**로딩 시점**

Read once at session startup (when `claude` launches). The `env` block is parsed from settings files and injected into the process and child-process environment, so it takes effect regardless of how `claude` was launched. Changes require restarting `claude` to take effect. Variables are not part of the model context window; they act as runtime configuration flags consumed by the CLI and its subprocesses.

**컨텍스트 비용**

Effectively zero token/context cost. Environment variables are runtime configuration flags consumed by the CLI and its subprocesses; they are not loaded into the model's context window. (Their effects, e.g. disabling CLAUDE.md loading or telemetry, may indirectly change how much other content is loaded.)

### 채택도

**채택 근거**

Widely adopted and referenced across the community: dedicated third-party guides (claudefa.st 'Claude Code Settings Reference', scalably.io, blog.vincentqiao.com copy-paste templates), community catalog repos such as HikaruEgashira/claude-code-shared-settings (environment_variables.md) and shanraisshan/claude-code-best-practice (claude-settings.md), and ClaudeLog configuration guides. Third-party model gateways (Z.AI, LM Studio, OpenRouter, Bedrock/Vertex/Foundry setups) rely on ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN, making these variables a de-facto standard integration surface. Enterprise deployments commonly use `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` / `DISABLE_TELEMETRY` via managed settings.

### 추천 설정

**설정 스니펫**

```
{
  "env": {
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "BASH_DEFAULT_TIMEOUT_MS": "300000",
    "BASH_MAX_TIMEOUT_MS": "600000",
    "API_TIMEOUT_MS": "1200000",
    "MAX_THINKING_TOKENS": "32000"
  }
}

// Gateway / proxy routing example (do NOT hardcode secrets; prefer apiKeyHelper or shell env):
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://your-gateway.example.com",
    "HTTPS_PROXY": "http://corp-proxy:8080",
    "NO_PROXY": "localhost,127.0.0.1,.internal"
  }
}

// Common flags reference:
//   ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN  -> auth (X-Api-Key vs Bearer)
//   ANTHROPIC_BASE_URL                        -> route to proxy/gateway
//   ANTHROPIC_MODEL / ANTHROPIC_DEFAULT_*_MODEL -> model selection
//   HTTP_PROXY / HTTPS_PROXY / NO_PROXY       -> corporate proxy
//   DEBUG=1 (or --debug)                      -> debug mode
//   CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 -> "safe/quiet" mode (no analytics/telemetry/crash reports/autoupdater)
//   DISABLE_TELEMETRY / DO_NOT_TRACK          -> disable telemetry
//   CLAUDE_CODE_USE_BEDROCK / CLAUDE_CODE_USE_VERTEX -> cloud provider backends
```

**결정적 vs 권고적**

Deterministic. Environment variables are hard configuration flags enforced by the harness/CLI at runtime (not advisory guidance the model may choose to follow). They reliably toggle behavior such as auth, proxying, timeouts, telemetry, and feature disables.

### 모범 사례

**모범 사례**

Use the `env` block for values that must apply to every session and to spawned subprocesses (hooks, MCP servers, Bash), so behavior is consistent no matter how `claude` is launched. Keep secrets OUT of committed files: put ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN in the shell environment, in gitignored `.claude/settings.local.json`, or better use the `apiKeyHelper` setting (with `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` for rotation) rather than hardcoding. For enterprise/managed rollouts, set privacy and network flags (`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_TELEMETRY`, proxy/cert variables like `CLAUDE_CODE_CERT_STORE`, `CLAUDE_CODE_CLIENT_CERT`) in managed-settings.json so they cannot be overridden. Use `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` as a single umbrella switch instead of setting DISABLE_AUTOUPDATER/DISABLE_BUG_COMMAND/DISABLE_ERROR_REPORTING/DISABLE_TELEMETRY individually. For gateways, note ANTHROPIC_BASE_URL disables MCP tool search and (on non-api.anthropic.com hosts, v2.1.196+) Remote Control by default. Prefer setting NO_COLOR/FORCE_COLOR and interface-color/identity variables in the real shell, since the `env` block ignores some of them (v2.1.143 / v2.1.195). Remember changes require a `claude` restart.

**안티패턴**

Committing API keys or auth tokens in `.claude/settings.json` (project scope is shared/committed to git) — a credential-leak risk. Assuming an `env`-block value overrides a real exported shell variable — precedence and per-variable behavior vary (some identity/color variables are ignored from `env`). Expecting mid-session changes to apply without restarting `claude`. Setting NO_COLOR/FORCE_COLOR in the `env` block and expecting Claude Code's own UI colors to change (they only pass to subprocesses since v2.1.143). Pointing ANTHROPIC_BASE_URL at a gateway without realizing MCP tool search and Remote Control are disabled by default. Over-disabling features (e.g. CLAUDE_CODE_DISABLE_CLAUDE_MDS, CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING) and then losing memory/`/rewind` functionality unexpectedly.

**보안 리스크**

주의 (Caution) — moderate. The mechanism itself is safe, but it is a common credential-leak vector: secrets (ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, cloud keys) placed in committed project settings can be exposed. ANTHROPIC_API_KEY requires approval in interactive mode. Variables that change network trust (ANTHROPIC_BASE_URL, proxy, custom CA/cert variables) or disable safety/telemetry behavior should be locked down via managed settings in regulated environments. Feature-disable flags are low-risk operationally but can silently remove protections (checkpointing, memory).

### 최근 변경

**최근 변경 내역**

Active area of change in 2026 H1. Notable additions/updates: v2.1.143 — NO_COLOR/FORCE_COLOR in `env` only pass to subprocesses, not the UI; v2.1.169 — API_FORCE_IDLE_TIMEOUT; v2.1.172 — CLAUDE_CODE_CHILD_SESSION; v2.1.181 — CLAUDE_AX_SCREEN_READER, CLAUDE_CLIENT_PRESENCE_FILE; v2.1.193 — CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP; v2.1.195 — hosting identity variables (CLAUDE_CODE_REMOTE, CLAUDE_CODE_ACCOUNT_UUID) ignored when set in `env`; v2.1.196 — ANTHROPIC_BASE_URL disables Remote Control on non-anthropic hosts, CLAUDE_CODE_DISABLE_BG_EXIT_HANDOFF; v2.1.198 — CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS, CLAUDE_AFK_TIMEOUT_MS/COUNTDOWN_MS; v2.1.199 — CLAUDE_CODE_BRIDGE_SESSION_ID; v2.1.203 — ANTHROPIC_FOUNDRY_AUTH_TOKEN (Microsoft Foundry). ANTHROPIC_SMALL_FAST_MODEL is now deprecated in favor of ANTHROPIC_DEFAULT_HAIKU_MODEL.

**라이프사이클**

Stable and actively maintained. The `env` block and core variables are stable/production. Individual flags vary: some are experimental or provider-specific gateways, and ANTHROPIC_SMALL_FAST_MODEL is deprecated (replaced by ANTHROPIC_DEFAULT_HAIKU_MODEL).

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Environment_Variables.json`</sub>

---

## 4. Model 설정

`환경/모델`

### 기본 정보

**설정 명칭**

Model configuration settings — model, fallbackModel, availableModels, enforceAvailableModels, includeCoAuthoredBy, and effort/thinking controls (effortLevel, /effort, MAX_THINKING_TOKENS)

**파일 위치**

settings.json at all scopes: user (~/.claude/settings.json), project (.claude/settings.json), local (.claude/settings.local.json), managed/policy (enterprise managed-settings.json or admin console). MAX_THINKING_TOKENS and CLAUDE_CODE_EFFORT_LEVEL go under the `env` block or the shell environment; effortLevel and includeCoAuthoredBy are top-level keys.

**공식 문서**

Documented. Settings reference: https://code.claude.com/docs/en/settings . Model configuration (model aliases, availableModels, enforceAvailableModels, fallbackModel chains, effort levels, extended thinking): https://code.claude.com/docs/en/model-config . Effort concept: https://platform.claude.com/docs/en/build-with-claude/effort

**도입 버전**

enforceAvailableModels: v2.1.175+. availableModels managed-list replace-instead-of-merge behavior: v2.1.175. `/model` persists selection as default: v2.1.153. Effort levels/ultracode via --effort and SDK: ultracode value v2.1.203+; non-interactive /effort session-only behavior v2.1.205. availableModels/effortLevel and fallbackModel predate these. includeCoAuthoredBy is a long-standing legacy key, now superseded by the `attribution` object.

### 스코프 / 로딩

**우선순위 계층**

Standard precedence (highest to lowest): managed/policy settings > command-line flags (--model, --fallback-model, --effort) > local (.claude/settings.local.json) > project (.claude/settings.json) > user (~/.claude/settings.json). Most keys follow this. Special cases: (1) fallbackModel does NOT merge across files — the highest-precedence file that defines it supplies the entire chain. (2) availableModels normally concatenates+dedupes across user/project/local, but as of v2.1.175 a managed list REPLACES lower-precedence entries rather than merging; admin-deployed managed sources also do not merge with each other. (3) enforceAvailableModels + availableModels must be deployed together in the single highest-precedence managed source. (4) An entry naming a specific version disables that family's wildcard within the effective list.

**로딩 시점**

Read from settings files at session start; not injected into the model's context window. `model` is read once at startup and applied on next restart (change mid-session with /model). effortLevel is read at startup and can be changed mid-session with /effort or the /model slider. fallbackModel and availableModels are evaluated at startup and whenever a model switch is attempted. Slash commands (/model, /effort, /config) write these keys back to settings when they persist a choice.

**컨텍스트 비용**

Negligible. These are harness configuration values enforced by Claude Code's code, not documents loaded into the prompt — they consume no token budget. (Extended thinking / effort themselves affect generated thinking-token spend, but the settings that configure them do not occupy context.)

### 채택도

**채택 근거 ⚠️**

Core, widely-adopted settings covered in the official docs and reproduced across community references (e.g., ClaudeLog configuration guide, community settings.json reference gists such as gist.github.com/mculp, and multiple third-party 'settings.json guide' blog posts). availableModels/enforceAvailableModels are enterprise/admin-oriented and appear in managed-deployment and MDM guidance; model/fallbackModel/effortLevel/includeCoAuthoredBy appear in typical individual-developer dotfiles.

### 추천 설정

**설정 스니펫**

```
// User or project .claude/settings.json — typical individual setup
{
  "model": "opusplan",
  "fallbackModel": ["claude-sonnet-5", "claude-haiku-4-5"],
  "effortLevel": "high",
  "includeCoAuthoredBy": true
}

// Managed/policy settings — enterprise model restriction
{
  "model": "claude-sonnet-4-5",
  "availableModels": ["claude-sonnet-4-5", "haiku"],
  "enforceAvailableModels": true,
  "env": {
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-5"
  }
}

// Disable extended thinking regardless of effort (no effect on Fable 5)
{
  "env": {
    "MAX_THINKING_TOKENS": "0"
  }
}

// Notes:
// - model accepts an alias (default, best, fable, sonnet, opus, haiku, sonnet[1m], opus[1m], opusplan) or a full model name (e.g. claude-opus-4-8).
// - fallbackModel is capped at 3 entries after dedup; "default" expands to the default model; extra entries ignored.
// - effortLevel accepts only low | medium | high | xhigh (max and ultracode are session-only; use --effort or /effort for those).
// - enforceAvailableModels requires a non-empty availableModels; needs v2.1.175+.
```

**결정적 vs 권고적**

Deterministic / code-enforced. Claude Code's harness reads and applies these values directly — model selection, allowlist enforcement, fallback switching, effort clamping, and commit attribution are all handled in code, not left to the model's discretion. availableModels/enforceAvailableModels are hard restrictions (blocked models are hidden from the picker and rejected on selection). The lone advisory element is `ultrathink` in a prompt, which only adds an in-context instruction without changing the effort sent to the API.

### 모범 사례

**모범 사례**

1) Set `model` in user settings to your everyday default; use `opusplan` to plan with Opus and execute with Sonnet, saving Opus-tier cost. 2) Configure `fallbackModel` as an array (max 3) so overload/unavailability of the primary model degrades gracefully for the rest of the turn instead of failing; remember the fallback lasts one turn only and your next message retries the primary. 3) For enterprises, pair `availableModels` with `enforceAvailableModels: true` so the Default picker option can't bypass the allowlist to the account-type default; also pin `ANTHROPIC_DEFAULT_*_MODEL` env vars when you need a specific version rather than just a family. 4) Deploy availableModels + enforceAvailableModels together in the single highest-precedence managed source (they don't merge). 5) Use `effortLevel` for a persistent low/medium/high/xhigh default; reach for `max`/`ultracode` per-session via /effort or --effort since they aren't persistable. 6) Let adaptive-reasoning models (Fable 5, Sonnet 5, Opus 4.7+) manage thinking via effort rather than fixed budgets. 7) Keep `includeCoAuthoredBy` (or the newer `attribution` object) explicit in team settings so commit trailers are consistent; set to false if your repo policy forbids AI co-author trailers. 8) On third-party providers (Bedrock/Vertex/Foundry) pin model version IDs via ANTHROPIC_DEFAULT_*_MODEL before rollout, and deliver allowlists via MDM/managed files since server-managed settings aren't received there.

**안티패턴**

1) Setting only `availableModels` and expecting the Default picker option to be restricted — it is NOT constrained unless `enforceAvailableModels: true` is also set (and availableModels is non-empty). 2) Using `availableModels: []` (empty) to lock down models — an empty array blocks named selections but never engages Default enforcement, so the account-type Default remains usable. 3) Putting more than 3 entries in fallbackModel — extras are silently ignored. 4) Assuming fallbackModel merges across settings files — it does not; only the highest-precedence file's chain is used. 5) Splitting availableModels and enforceAvailableModels across different managed sources — admin-deployed managed sources don't merge, so the pair is ignored when the admin console delivers any settings. 6) Trying to persist `max` or `ultracode` via effortLevel — rejected; those are session-only. 7) Expecting MAX_THINKING_TOKENS=0 to disable thinking on Fable 5 — it cannot be turned off there. 8) Listing a family wildcard alongside a specific version (e.g. ["sonnet", "claude-sonnet-4-5"]) and expecting all Sonnet versions — the specific entry disables the family wildcard, allowing only 4.5. 9) Relying on device-deployed managed settings for cloud/web/Desktop sessions — those run on Anthropic VMs and need server-managed settings for allowlist enforcement.

**보안 리스크**

주의 (moderate). These settings govern which models run and how commits are attributed, not shell/command execution, so they are not high-risk. availableModels/enforceAvailableModels are governance/compliance controls — misconfiguring them (e.g. forgetting enforceAvailableModels, or splitting the pair across non-merging managed sources) silently fails open and lets users reach unapproved models, which is the main risk. Note these allowlists are enforced by Claude Code itself, not the server (except separate org-level restrictions on Enterprise plans), so they are a policy guardrail rather than a hard server boundary. includeCoAuthoredBy is informational (commit-trailer content) with negligible security impact.

### 최근 변경

**최근 변경 내역**

First half of 2026: enforceAvailableModels added (v2.1.175) to extend the availableModels allowlist to the Default model. availableModels managed-list behavior changed to replace (not merge) lower-precedence entries as of v2.1.175. Effort system expanded: xhigh level and per-model default effort holds (high on Fable 5/Opus 4.8, xhigh on Opus 4.7); `ultracode` effort mode added (--effort/SDK value v2.1.203+; sends xhigh plus dynamic-workflow orchestration, session-only); non-interactive /effort is session-only and can't release the model-default hold (v2.1.205). Organization default model (v2.1.196+) and organization effort limits (v2.1.195+) added for Enterprise. availableModels picker now shows a labeled row for pinned full model IDs (v2.1.199). includeCoAuthoredBy is being superseded by the richer `attribution` object (commit/pr templates).

**라이프사이클 ⚠️**

Stable/GA for model, fallbackModel, availableModels, enforceAvailableModels, effortLevel, MAX_THINKING_TOKENS. includeCoAuthoredBy: stable but legacy/soft-deprecated — still honored (default true) but superseded by the newer `attribution` settings object, which takes precedence when both are set. ultracode/max effort and organization-level model/effort controls are current GA features but Enterprise-plan gated.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 라이프사이클 (`lifecycle_status`)

</details>

<sub>출처: `results/Model_설정.json`</sub>

---

## 5. StatusLine 커스터마이징

`UI/UX`

### 기본 정보

**설정 명칭**

statusLine (custom status line)

**파일 위치**

Configured via the `statusLine` object in `~/.claude/settings.json` (user) or `.claude/settings.json` (project). The script it points to is a separate executable file, conventionally `~/.claude/statusline.sh` (or `.py`/`.js`/`.ps1`). Related keys: `subagentStatusLine` (same location) and the `/statusline` slash command which auto-generates the script and edits settings for you.

**공식 문서**

Yes. Dedicated official page: 'Customize your status line' at https://code.claude.com/docs/en/statusline (covers setup, the full stdin JSON schema, ready-to-use Bash/Python/Node/PowerShell examples, and troubleshooting).

**도입 버전 ⚠️**

[uncertain] The statusLine feature has existed since the 1.x era of Claude Code (mid-2025); the exact first version/date is not stated in the docs. Individual sub-features are dated by min-version comments in the docs (e.g. COLUMNS/LINES env vars require v2.1.153, per-context-window token semantics changed in v2.1.132, prompt_id requires v2.1.196, per-subagent model/context fields require v2.1.205).

### 스코프 / 로딩

**우선순위 계층**

Follows the standard settings.json precedence chain: enterprise/managed > command-line args > local project (.claude/settings.local.json) > shared project (.claude/settings.json) > user (~/.claude/settings.json). A higher-priority layer's `statusLine` object replaces (not merges into) a lower one — you get one active status line, whichever wins. Plugins can also ship a default `statusLine`/`subagentStatusLine` in their own settings.json. Most users configure it at the user layer so it applies across all projects.

**로딩 시점**

Executes as an external shell command (like a hook), NOT loaded into the model's context. Claude Code pipes session JSON to the script's stdin and renders its stdout. It runs on events: after each new assistant message, after `/compact` finishes, when the permission mode changes, and when vim mode toggles. Updates are debounced at 300ms; if a new update fires while the script is still running, the in-flight run is cancelled. The optional `refreshInterval` (seconds, minimum 1) additionally re-runs it on a fixed timer for time-based data (e.g. a clock) or during idle periods while background subagents change state.

**컨텍스트 비용**

Zero token / context cost. The docs state explicitly: 'The status line runs locally and does not consume API tokens.' It is a local process whose output is rendered in the UI, so it never occupies the model's context window budget.

### 채택도

**채택 근거 ⚠️**

Widely adopted; the official docs themselves recommend community projects. Notable ready-made tools: ccstatusline (github.com/sirmalloc/ccstatusline) and starship-claude (github.com/martinemde/starship-claude) are both name-checked in the official docs' Tips section. Other popular projects include cship (github.com/stephenleo/cship, a Rust ~10ms-render statusline with Starship passthrough), gabriel-dehan/claude_monitor_statusline, and sotayamashita/claude-code-statusline (Rust). Numerous blog write-ups exist (dandoescode.com, gordonbeeming.com, aihero.dev, alexop.dev, claudefa.st, voitanos.io) and community 'complete guide' gists. [uncertain] exact GitHub star counts were not verified.

### 추천 설정

**설정 스니펫**

```
// ~/.claude/settings.json — point at a script file:
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2
  }
}

// Or an inline one-liner using jq (no separate script file):
{
  "statusLine": {
    "type": "command",
    "command": "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0)% context\"'"
  }
}

// Windows (PowerShell script), works whether routed via Git Bash or PowerShell:
{
  "statusLine": {
    "type": "command",
    "command": "powershell -NoProfile -File C:/Users/username/.claude/statusline.ps1"
  }
}

// Example script: ~/.claude/statusline.sh (chmod +x it) — model + dir + context %
#!/bin/bash
input=$(cat)                        # Claude Code sends session JSON on stdin
MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
echo "[$MODEL] 📁 ${DIR##*/} | ${PCT}% context"

// Fastest path: run `/statusline show model name and context % with a progress bar`
// and Claude Code writes the script and edits settings.json for you.
// Optional keys: refreshInterval (seconds, min 1) and hideVimModeIndicator (bool).
```

**결정적 vs 권고적**

Deterministic. It is code the harness executes verbatim on every event — the model does not decide what to show. Output is entirely a function of your script plus the fixed stdin JSON (the only advisory part is that the model authors the script when you use /statusline).

### 모범 사례

**모범 사례**

1) Read all of stdin first (`input=$(cat)`), then parse — the JSON arrives as one blob. 2) Always provide fallbacks for null/absent fields: `// 0` or `// empty` in jq, `or 0` in Python, `?.`/`|| 0` in Node — many fields (used_percentage, current_usage, rate_limits, pr, worktree) are null or absent early in a session or for non-subscribers. 3) Prefer the pre-calculated `context_window.used_percentage` over computing it yourself; if you must compute, use the input-only formula (input + cache_creation + cache_read, excluding output) to match. 4) Keep output short — the bar has limited width and long output wraps/truncates. 5) Cache slow commands: `git status`/`git diff` in big repos cause lag; cache to a temp file keyed on `session_id` (stable per session, unique across sessions) — NOT `$$`/pid which change every invocation. 6) Use `refreshInterval` only for time-based/idle-updating data (clock, background subagent git state). 7) Prefer `workspace.current_dir` over `cwd` (identical value, consistent with project_dir). 8) On Windows write the command path with forward slashes (Git Bash eats backslashes). 9) Read terminal size from `COLUMNS`/`LINES` env vars (v2.1.153+) — `tput cols` can't see the terminal. 10) For colors use ANSI codes and `printf '%b'` (more reliable than `echo -e`); for clickable links use OSC 8 sequences. 11) Test with mock input: `echo '{...}' | ./statusline.sh`. 12) Let `/statusline` generate the first version, then tweak.

**안티패턴**

Using process IDs ($$, os.getpid(), process.pid) as a cache key — they change every run and defeat caching. Running expensive git commands unconditionally on every 300ms-debounced update, causing visible lag. Writing diagnostics to stdout (only stdout is rendered; put errors on stderr) or, conversely, printing your real output to stderr so the bar goes blank. Forgetting `chmod +x` on the script. Non-zero exit or no output — either blanks the status line. Overly long output or heavy multi-line ANSI/OSC sequences, which truncate or garble on narrow terminals. Backslash paths in `command` on Windows (silently fail under Git Bash). Assuming rate_limits/pr/effort/worktree are always present — they are conditionally absent. Not realizing that setting `disableAllHooks: true` also disables the status line.

**보안 리스크**

주의 (Caution). statusLine runs an arbitrary shell command locally on every session event, so a malicious or careless script is a code-execution vector — the same class of risk as hooks. Claude Code gates it behind the workspace trust dialog: the command only runs after you accept trust for the directory (otherwise you see 'statusline skipped · restart to fix'), and it is disabled entirely when `disableAllHooks` is true. It consumes no API tokens and cannot bypass permissions on its own, so risk is moderate rather than high — but never paste an untrusted status line script into settings, especially a project/plugin-supplied one, without reading it.

### 최근 변경

**최근 변경 내역**

Actively evolving through 2026 H1. Documented recent additions: COLUMNS/LINES terminal-size env vars (v2.1.153+); context_window token fields changed from cumulative session totals to current-context semantics (v2.1.132); `prompt_id` field added (v2.1.196+); `subagentStatusLine` setting with per-task `model` and `contextWindowSize` fields (v2.1.205+). The schema also carries newer fields such as `effort.level` (low/medium/high/xhigh/max), `thinking.enabled`, `rate_limits` (five_hour/seven_day), `pr.*`, `worktree.*`, `workspace.git_worktree`, and `workspace.repo.*`. The `refreshInterval` and `hideVimModeIndicator` options and OSC 8 clickable-link support are part of the current feature set.

**라이프사이클**

Stable and generally available. It is a first-class, officially documented feature with a dedicated docs page, a built-in `/statusline` command, and an official statusline-setup agent. No deprecation signals; still gaining fields and options.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/StatusLine_커스터마이징.json`</sub>

---

## 6. MCP 서버 설정

`연동`

### 기본 정보

**설정 명칭**

MCP server configuration (.mcp.json + settings.json MCP controls: enableAllProjectMcpServers, enabledMcpjsonServers, disabledMcpjsonServers, allowedMcpServers, deniedMcpServers, allowManagedMcpServersOnly, managed-mcp.json)

**파일 위치**

Server DEFINITIONS live in: (1) .mcp.json at project root (project scope, committed to git, shared with team); (2) ~/.claude.json under a project path (local scope, default, private) or top-level (user scope, all projects); (3) plugin .mcp.json / plugin.json mcpServers block; (4) system-path managed-mcp.json for exclusive enterprise control (/Library/Application Support/ClaudeCode/ on macOS, /etc/claude-code/ on Linux/WSL, C:\Program Files\ClaudeCode\ on Windows). Server CONTROL POLICY lives in settings files: .claude/settings.json (project, shared), .claude/settings.local.json (project-local, gitignored), ~/.claude/settings.json (user), and managed settings. enableAllProjectMcpServers / enabledMcpjsonServers / disabledMcpjsonServers approve project .mcp.json servers; allowedMcpServers / deniedMcpServers / allowManagedMcpServersOnly are the allow/deny policy layer.

**공식 문서**

Fully documented across two dedicated official pages. Primary: https://code.claude.com/docs/en/mcp (Connect Claude Code to tools via MCP - transports, scopes, .mcp.json format, auth, tool search) and https://code.claude.com/docs/en/managed-mcp (Control MCP server access - allowedMcpServers/deniedMcpServers/managed-mcp.json). Related: https://code.claude.com/docs/en/settings (settings reference incl. enableAllProjectMcpServers/enabledMcpjsonServers/disabledMcpjsonServers), https://code.claude.com/docs/en/mcp-quickstart, https://code.claude.com/docs/en/server-managed-settings, https://code.claude.com/docs/en/plugins-reference#mcp-servers.

**도입 버전 ⚠️**

[uncertain] MCP support and .mcp.json/scopes predate most versioned docs and have no single authoritative introduction date. Individual refinements are versioned: alwaysLoad field (v2.1.121), claude mcp login/logout (v2.1.186), idle-timeout for tool calls (v2.1.187), allowAllClaudeAiMcps managed setting (v2.1.149), deniedMcpServers serverName accepting any string (v2.1.182), workspace-trust gating of .mcp.json approvals in claude mcp list/get (v2.1.196), roots/list returning additional working dirs (v2.1.203), and the missing-type error wording change (v2.1.202).

### 스코프 / 로딩

**우선순위 계층**

Two independent layers. (A) SERVER DEFINITION precedence, when the same server name/endpoint is defined in multiple places Claude Code connects once using the highest-precedence source and does NOT merge fields across scopes: 1) Local scope, 2) Project scope (.mcp.json), 3) User scope, 4) Plugin-provided servers, 5) claude.ai connectors. The three named scopes match duplicates by name; plugins/connectors match by endpoint (URL or command). (B) POLICY/APPROVAL layer follows standard settings precedence (managed > local project settings.local.json > project settings.json > user). Key merge rules: allowedMcpServers entries from every settings source MERGE (a user can broaden the allowlist) UNLESS allowManagedMcpServersOnly:true is set in a managed source, which then keeps only the managed allowlist. deniedMcpServers ALWAYS merges from every source and a deny match cannot be overridden by any allow. disabledMcpjsonServers in any settings file always rejects that project server. A deployed managed-mcp.json is exclusive: only its servers load and users cannot add others.

**로딩 시점**

Server definitions are read at session start and servers connect in the background (non-blocking by default; alwaysLoad:true forces a blocking connect capped at the 5s connect timeout). Project .mcp.json servers do NOT auto-connect: they sit at pending approval until the user approves them interactively, or approval is granted via enableAllProjectMcpServers / enabledMcpjsonServers in settings. As of v2.1.196, approvals in checked-in .claude/settings.json are ignored in an untrusted folder (server stays pending) until you accept the workspace-trust dialog; approvals from user settings, managed settings, and --settings still apply untrusted. With tool search enabled (default), only tool NAMES + 2KB server instructions load at startup and full tool schemas are fetched on demand via ToolSearch; alwaysLoad:true exempts a server so all its tools load upfront. allowedMcpServers/deniedMcpServers are evaluated by the harness before a server is allowed to load (denylist checked first, then allowlist).

**컨텍스트 비용**

Low by default because MCP tool search is on by default: only tool names and server instructions (each truncated to 2KB) enter context at startup, and full tool schemas load on demand through ToolSearch, so adding servers has minimal context impact. Cost rises when ENABLE_TOOL_SEARCH=false (all schemas loaded upfront) or when a server sets alwaysLoad:true (all its tools always in context). MCP tool OUTPUT also consumes context: a warning fires above 10,000 tokens and the default cap is 25,000 tokens (MAX_MCP_OUTPUT_TOKENS). The allow/deny policy settings themselves are enforcement metadata with negligible token cost.

### 채택도

**채택 근거**

Core, heavily-used integration surface with extensive first- and third-party coverage. Official: dedicated docs pages, the mcp-server-dev plugin in anthropics/claude-plugins-official, and the Anthropic Directory of reviewed connectors. Third-party guides in 2026: systemprompt.io 'Install and Configure MCP Servers in Claude Code (2026)', builder.io 'Claude Code MCP Servers', maketocreate.com and thepromptshelf.dev 2026 setup guides, scalably.io settings.json guide, generalanalysis.com security guide. Community tooling exists specifically for this (e.g. henkisdabro/Claude-Code-MCP-Server-Selector TUI to toggle servers for context savings). Active GitHub issue traffic confirms real-world use: anthropics/claude-code #32882 (plugin .mcp.json ignored when allowedMcpServers set in managed-settings.json), #24657 (enabledMcpjsonServers in settings.local.json ignored), #3106 (report user-disabled servers in claude mcp list).

### 추천 설정

**설정 스니펫**

```
// 1) Project-scoped servers, committed to git: .mcp.json at project root
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_PAT}" }
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp",
      "alwaysLoad": false
    },
    "db": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub", "--dsn", "${DB_DSN}"],
      "env": { "CACHE_DIR": "/tmp" },
      "timeout": 600000
    }
  }
}

// Notes on .mcp.json:
// - type accepts http (alias streamable-http), sse (deprecated), ws, stdio.
// - An entry with a url but no type is an error (read as stdio). Always set type.
// - ${VAR} and ${VAR:-default} expand in command, args, env, url, headers.
// - Never commit real secrets; use ${VAR} or OAuth (/mcp) instead.

// 2) Approve project servers without per-server prompts: .claude/settings.json
{
  "enableAllProjectMcpServers": false,
  "enabledMcpjsonServers": ["github", "sentry"],
  "disabledMcpjsonServers": ["db"]
}

// 3) Enterprise policy (managed settings source): allow/deny lists
{
  "allowManagedMcpServersOnly": true,
  "allowedMcpServers": [
    { "serverUrl": "https://api.githubcopilot.com/*" },
    { "serverUrl": "https://*.internal.example.com/*" },
    { "serverCommand": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."] }
  ],
  "deniedMcpServers": [
    { "serverUrl": "https://*.untrusted.example.com/*" },
    { "serverCommand": ["npx", "-y", "unapproved-package"] },
    { "serverName": "claude.ai Slack" }
  ]
}

// Notes on allow/deny policy:
// - Entry keys: serverUrl (exact or * wildcards, incl. scheme; hostname case-insensitive),
//   serverCommand (exact command+args, in order), serverName (literal label, NOT a security control).
// - Denylist is checked first and always wins; allowlist unset = all allowed, [] = none allowed.
// - allowedMcpServers merges from every source UNLESS allowManagedMcpServersOnly:true (managed only).
// - For remote servers, a serverName allow counts only if the allowlist has no serverUrl entries
//   (same for serverCommand on stdio) -> prefer serverUrl/serverCommand for real enforcement.

// 4) Deploy a fixed set / disable MCP entirely: managed-mcp.json (system path)
{ "mcpServers": {} }   // empty map blocks every MCP server everywhere
```

**결정적 vs 권고적**

Mixed. allowedMcpServers/deniedMcpServers/allowManagedMcpServersOnly, disabledMcpjsonServers, and managed-mcp.json are DETERMINISTIC / harness-enforced: they decide before the model sees anything whether a server loads, and a deny cannot be overridden by prompt or CLAUDE.md. Caveat: serverName matching is NOT a security boundary (a user can label any server 'github'), so only serverUrl/serverCommand entries provide robust enforcement, and ${VAR} entries can expand to user-controlled values. The definitions in .mcp.json and the enableAllProjectMcpServers/enabledMcpjsonServers approvals are configuration, not advisory-to-model. Whether Claude actually invokes a connected server's tools is model-driven (advisory) and shaped by server instructions/descriptions under tool search.

### 모범 사례

**모범 사례**

1) Prefer HTTP transport for remote servers (widest support, OAuth, --transport flag); SSE is deprecated. Set type explicitly on every entry (url-without-type is an error). 2) Use the right scope: local (default, private/experimental/credentialed), project .mcp.json (team-shared, commit it), user (personal cross-project). Remember MCP 'local scope' lives in ~/.claude.json, not .claude/settings.local.json. 3) Keep secrets out of committed .mcp.json and out of managed-mcp.json env blocks: use ${VAR}/${VAR:-default} expansion, OAuth via /mcp or claude mcp login, or headersHelper for custom schemes. 4) For teams, control project-server approval explicitly with enabledMcpjsonServers (allowlist by name) rather than blanket enableAllProjectMcpServers=true; use disabledMcpjsonServers to hard-reject a risky one. 5) For orgs, enforce with managed sources: allowedMcpServers + allowManagedMcpServersOnly:true for an approved catalog, or managed-mcp.json for exclusive fixed deployment / empty map to disable MCP; use serverUrl/serverCommand (not serverName) for enforcement. 6) Manage context: leave tool search on (default), reserve alwaysLoad:true for the few servers needed every turn, raise MAX_MCP_OUTPUT_TOKENS only for known large-output servers, and set per-server timeout for slow tools. 7) Trust before approving: audit each server for prompt-injection risk; approvals in checked-in settings are (correctly) ignored until you accept the workspace-trust dialog. 8) Reference plugin-bundled tools by full name mcp__plugin_<plugin>_<server>__<tool> in permission/hook/subagent rules.

**안티패턴**

1) Committing API keys/tokens directly in .mcp.json env or headers (leaks to the whole team via git). 2) Relying on serverName in allowedMcpServers/deniedMcpServers for security, a user can rename any server, so it enforces nothing; use serverUrl/serverCommand. 3) Setting allowedMcpServers without allowManagedMcpServersOnly and expecting it to be authoritative, users' own settings merge in and broaden it. 4) Blanket enableAllProjectMcpServers=true on untrusted or cloned repos (auto-approves every project server, including malicious ones); combined with prompt-injection this is a real risk. 5) Writing a url entry with no type field (silently skipped as a misconfigured stdio server). 6) Assuming allowManagedMcpServersOnly also locks permission rules, it does not (that is allowManagedPermissionRulesOnly). 7) Expecting an allow rule to override a deny, denylist always wins. 8) Loading many servers with alwaysLoad:true or ENABLE_TOOL_SEARCH=false and exhausting the context window. 9) Using reserved names (workspace, claude-in-chrome, computer-use, Claude Preview, Claude Browser) for a custom server, it is skipped with a warning. 10) Forgetting -- before the stdio command in claude mcp add, so the server's flags get parsed as Claude's options.

**보안 리스크**

위험/주의 (High-importance, security-critical). MCP servers execute code and fetch external content, so they are a primary prompt-injection and data-exfiltration vector; Anthropic explicitly does not security-audit third-party servers. Key risks: blanket auto-approval of project/cloned-repo servers, secrets committed in .mcp.json, serverName-based allow/deny giving a false sense of enforcement, and stdio/headersHelper servers running arbitrary local shell commands (headersHelper at project scope runs only after workspace trust). Mitigations: enforce allow/deny by serverUrl/serverCommand in managed sources, use managed-mcp.json for exclusive control (or empty map to disable), restrict OAuth scopes via oauth.scopes, keep tool search on, and require workspace trust before approvals apply.

### 최근 변경

**최근 변경 내역 ⚠️**

Active area through 2026 H1. Notable versioned changes: allowAllClaudeAiMcps managed setting to load claude.ai connectors alongside managed-mcp.json (v2.1.149); connectors you never signed in to collapsed behind 'Show unused connectors' (v2.1.161); claude mcp login/logout for CLI OAuth and --no-browser detection (v2.1.186, v2.1.191); deniedMcpServers serverName accepting any non-empty string to block claude.ai connectors by display name (v2.1.182); idle-timeout aborting stalled MCP tool calls (v2.1.187, extended to stdio and gaining a per-server timeout floor in v2.1.203); root-level anyOf/oneOf/allOf schema flattening and non-interactive auth reporting (v2.1.195/2.1.196); workspace-trust now gates .mcp.json approvals read from checked-in settings in claude mcp list/get (v2.1.196) and from untracked settings.local.json (v2.1.207); roots/list now returns additional working directories with list_changed notifications (v2.1.203); improved missing-type error wording and gitignore escaping (v2.1.202); Claude Browser reserved and failed-connection errors surfaced to Claude (v2.1.205); anthropic/requiresUserInteraction per-tool always-approve annotation (v2.1.199). Exact dates for some items are [uncertain].

**라이프사이클**

Stable / GA and actively extended. .mcp.json, the three scopes, and the allow/deny + managed-mcp.json policy layer are core, non-experimental features. HTTP is the recommended remote transport; SSE transport is explicitly DEPRECATED (use HTTP). MCP tool search is GA and enabled by default. No deprecation of the configuration mechanism itself; the surface is being expanded (new managed controls, auth flows, timeouts) rather than wound down.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/MCP_서버_설정.json`</sub>

---

## 7. Subagents

`자동화/확장`

### 기본 정보

**설정 명칭**

Subagents (custom subagents / .claude/agents/*.md)

**파일 위치**

Markdown files with YAML frontmatter in an agents/ directory, resolved from several scopes (highest to lowest precedence): managed-settings .claude/agents/ (organization-wide), the --agents CLI flag (session-only JSON, not saved to disk), .claude/agents/ (current project, discovered by walking up from the cwd to the repo root, plus any --add-dir directories), ~/.claude/agents/ (user, all projects), and a plugin's agents/ directory. Both project and user directories are scanned recursively, so subfolders like agents/review/ are allowed. Identity comes only from the frontmatter name field, not the filename or subfolder path (except plugin subagents, where a subfolder becomes part of the scoped identifier, e.g. agents/review/security.md -> my-plugin:review:security). Subagent transcripts live at ~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl; agent-memory (when memory is enabled) at ~/.claude/agent-memory/<name>/, .claude/agent-memory/<name>/, or .claude/agent-memory-local/<name>/.

**공식 문서**

Yes. Primary page: https://code.claude.com/docs/en/sub-agents ("Create custom subagents"). Closely related official pages: https://code.claude.com/docs/en/agent-teams (multi-agent teammates), https://code.claude.com/docs/en/context-window (context savings), https://code.claude.com/docs/en/hooks (SubagentStart/SubagentStop), https://code.claude.com/docs/en/plugins-reference#agents (plugin agents), and the Agent SDK docs at https://code.claude.com/docs/en/agent-sdk/overview.

**도입 버전 ⚠️**

Custom subagents (.claude/agents/*.md with YAML frontmatter) shipped in mid-2025 as one of Claude Code's core extension mechanisms. Exact first version is not documented in the current docs. Many capabilities were layered on later: nested subagents in v2.1.172 (~2026), extended-thinking inheritance in v2.1.198, and the /agents wizard was removed in v2.1.198. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Precedence when multiple subagents share the same name (highest to lowest): 1) managed settings, 2) --agents CLI flag, 3) project .claude/agents/, 4) user ~/.claude/agents/, 5) plugin agents/. Managed definitions override project and user definitions of the same name. Across nested project directories, the definition closest to the working directory wins (v2.1.178+). Within a single directory tree (including subfolders), duplicate names are a misconfiguration: only one loads, chosen by filesystem read order, and /doctor (v2.1.205+) flags the collision. Unlike settings.json, subagents don't deep-merge fields; a higher-priority definition of a name fully replaces the lower one. Plugin subagents load alongside custom ones under their scoped name but ignore the hooks, mcpServers, and permissionMode fields for security.

**로딩 시점**

A subagent runs only on demand, never at session start. It is invoked in four ways: (1) automatic delegation - Claude reads each subagent's description field and delegates when a task matches (phrasing like "use proactively" encourages this); (2) natural language - naming the subagent in your prompt (Claude still decides); (3) @-mention - @"name (agent)" or @agent-<name> guarantees that specific subagent runs for one task; (4) session-wide - claude --agent <name> or the "agent" setting makes the subagent's system prompt/tools/model the main thread for the whole session. Definition files are hot-watched: edits to existing agents/ directories are picked up within seconds with no restart, but a brand-new agents directory (its first file) or a --disable-slash-commands session requires a restart. Each invocation spawns a fresh instance; SendMessage (by agent ID or name) resumes an existing one with full history.

**컨텍스트 비용**

Very low standing cost, high isolation benefit. Subagent definitions are NOT loaded into the main conversation at startup - only the (usually short) name+description of available subagents is visible so Claude can decide when to delegate. The real value is context isolation: a subagent runs in its own fresh 200K-token context window, so verbose work (test output, log scanning, doc fetching, wide code search) stays out of the main conversation and only a summary returns. Costs appear only when a subagent actually runs (its own token spend on a separate context and, if model differs, a separate prompt cache). Caveat: many subagents each returning large detailed results back to the main thread can still consume significant main-context tokens; and preloaded skills (skills field) inject full skill content into the subagent's context.

### 채택도

**채택 근거 ⚠️**

Subagents are one of the most widely adopted Claude Code extension mechanisms, with a large third-party ecosystem: VoltAgent/awesome-claude-code-subagents (100+ specialized agents), 0xfurai/claude-code-subagents (100+ production-ready agents), supatest-ai/awesome-claude-code-sub-agents, rahulvrane/awesome-claude-agents, lst97/claude-code-sub-agents, hesreallyhim/awesome-claude-code and a-list-of-claude-code-agents, plus a dedicated directory site subagents.cc for discovering/sharing agents. Anthropic ships built-in subagents (Explore, Plan, general-purpose, statusline-setup, claude-code-guide) and documents subagents as a first-class feature, and they are a standard packaging unit inside plugins. [uncertain]

### 추천 설정

**설정 스니펫**

```
# ~/.claude/agents/code-reviewer.md  (user scope) or .claude/agents/code-reviewer.md (project scope)
---
name: code-reviewer
description: Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code.
tools: Read, Grep, Glob, Bash   # allowlist; omit to inherit all tools. disallowedTools works as a denylist.
model: inherit                  # sonnet | opus | haiku | fable | claude-opus-4-8 | inherit (default: inherit)
# --- optional fields ---
# disallowedTools: Write, Edit
# permissionMode: default       # default|acceptEdits|auto|dontAsk|bypassPermissions|plan (manual = alias for default, v2.1.200+)
# effort: high                  # low|medium|high|xhigh|max (overrides session effort)
# maxTurns: 20
# skills: [api-conventions, error-handling-patterns]   # full skill content preloaded at startup
# memory: project               # user|project|local -> persistent cross-session agent-memory dir
# background: true              # always run in background
# isolation: worktree           # run in a temporary git worktree (isolated repo copy)
# color: blue                   # red|blue|green|yellow|purple|orange|pink|cyan
# mcpServers: [github]          # names or inline server defs; scopes MCP to this agent
# hooks: { PreToolUse: [ { matcher: "Bash", hooks: [ { type: command, command: "./scripts/validate.sh" } ] } ] }
---

You are a senior code reviewer ensuring high standards of code quality and security.
When invoked: run git diff, focus on modified files, and review immediately.
Report Critical / Warning / Suggestion, with concrete fixes.

# --- Restrict which subagents this one may spawn (only meaningful as a main --agent thread) ---
# tools: Agent(worker, researcher), Read, Bash   # allowlist of spawnable types
# For a normal subagent, listing bare `Agent` in tools enables nested spawning; the type list in parens is ignored.

# --- Session-only CLI definition (not saved to disk) ---
# claude --agents '{"debugger":{"description":"Debug errors and test failures","prompt":"You are an expert debugger...","tools":["Read","Edit","Bash"],"model":"sonnet"}}'

# --- Disable a subagent (settings.json) ---
# { "permissions": { "deny": ["Agent(Explore)", "Agent(code-reviewer)"] } }
# --- Make one the session default (.claude/settings.json) ---
# { "agent": "code-reviewer" }
```

**결정적 vs 권고적**

Mixed, leaning advisory. WHICH subagent runs is largely model-driven (Claude decides delegation from the description field), unless you force it with @-mention, --agent, or the "agent" setting. What a subagent CAN do is deterministic and code-enforced: the tools/disallowedTools allowlist/denylist, permissionMode, mcpServers scoping, maxTurns cap, and the fixed depth-5 nesting limit are all enforced by the harness regardless of model judgment, and frontmatter PreToolUse hooks can hard-block operations. So the routing is advisory; the sandbox around each subagent is deterministic.

### 모범 사례

**모범 사례**

1) Write a sharp, action-oriented description - it is the sole signal Claude uses to auto-delegate; add "use proactively"/"use immediately after X" to encourage delegation. 2) Design single-purpose subagents (one job done well) rather than one mega-agent. 3) Grant least-privilege tools: use a tight tools allowlist (e.g. Read, Grep, Glob for read-only reviewers) or disallowedTools to strip Write/Edit; this both hardens and focuses the agent. 4) Choose model deliberately - model: inherit for parity, model: haiku to cut cost on cheap/verbose tasks, model: sonnet/opus for hard reasoning; CLAUDE_CODE_SUBAGENT_MODEL can override globally. 5) Use subagents to isolate high-volume output (test runs, log/doc processing) so only a summary returns to main context. 6) Preload domain knowledge with the skills field instead of hoping the agent discovers a skill mid-run. 7) Enable memory: project for agents that should accumulate codebase knowledge across sessions (recommended default scope; shareable via VCS). 8) Restate must-follow rules in the delegation prompt - the subagent gets CLAUDE.md but not your conversation history, and Explore/Plan skip CLAUDE.md entirely. 9) Check project subagents into version control for team reuse. 10) For finer control than tools allows, add a PreToolUse hook (e.g. block SQL writes) rather than removing Bash entirely. 11) Restrict nested spawning with Agent(type,...) or by omitting Agent from tools. 12) Use isolation: worktree when a subagent should experiment without touching your checkout.

**안티패턴**

Vague/generic descriptions (Claude can't tell when to delegate, so auto-delegation silently never fires). Duplicate name values in the same directory tree (only one loads, chosen non-deterministically by read order). Assuming the subagent sees your chat history, already-read files, or invoked skills - it starts fresh; forgetting to restate constraints in the delegation prompt. Granting all tools / bypassPermissions to an unattended subagent (it can write to .git/.claude and run commands without approval). Spawning many subagents that each dump large detailed results back into main context, defeating the context-saving purpose. Listing Skill in tools to preload a skill (use the skills field; tools:Skill only controls invocation ability). Expecting per-subagent extended-thinking control (there is none - it's inherited). Creating the first file in a brand-new agents directory mid-session and expecting it to load without a restart. Relying on plugin subagents for hooks/mcpServers/permissionMode (those fields are ignored for plugin-scoped agents). Using a hyphenated SubagentStart/Stop matcher on <v2.1.195 without anchoring (^name$), since it matches as an unanchored regex.

**보안 리스크**

주의 (medium/caution). Subagents are a privilege-management tool AND a potential risk. Upside: they enforce least privilege - a read-only reviewer with tools: Read, Grep, Glob genuinely cannot write files, and PreToolUse hooks can hard-block dangerous operations. Downside: an over-permissive subagent (broad tools plus permissionMode: bypassPermissions) executes operations without approval, including writes to sensitive dirs like .git/.claude/.vscode; a parent's bypassPermissions/acceptEdits/auto also propagates and cannot be loosened by a child but a child inheriting it runs unattended. A malicious project-committed .claude/agents/*.md (with hooks or inline mcpServers) is a code-execution vector - review untrusted repos' agent files before running. Note messages from a launching agent are never permission approval, and no agent message can change a subagent's permissions/CLAUDE.md/config; only the permission system or the human can. Plugin subagents are hardened by ignoring hooks/mcpServers/permissionMode.

### 최근 변경

**최근 변경 내역 ⚠️**

Active development through 2026 H1. Notable: v2.1.172 - a subagent can spawn nested subagents (recursive, capped at depth 5, fixed/non-configurable; a depth-5 agent gets no Agent tool). v2.1.198 - subagents inherit the main conversation's extended-thinking setting (previously always disabled); subagents run in the BACKGROUND by default; built-in Explore now inherits the main model (capped at Opus on the Claude API) instead of always Haiku; CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1 added; the /agents interactive wizard was removed (it now just tells you to edit .claude/agents/ or ask Claude). v2.1.196 - CLAUDE_CODE_SUBAGENT_MODEL=inherit now behaves as unset. v2.1.186 - background subagents surface permission prompts in the main session instead of auto-denying. v2.1.187 - a background subagent's depth is fixed at first spawn. v2.1.191 - manually stopped subagents no longer auto-resume; v2.1.199 - SendMessage validates the name still refers to the same agent, and API-error handling for subagents improved (partial output returned, "Agent terminated early due to an API error"). v2.1.200 - permissionMode: manual alias. v2.1.203 - worktree isolation runs Bash in the worktree. v2.1.205 - --append-subagent-system-prompt flag; /doctor reports duplicate-name agent files. v2.1.206 - sibling roster (system reminder listing peer named agents for SendMessage). Fork subagents (/fork, CLAUDE_CODE_FORK_SUBAGENT) matured: v2.1.117 introduced, v2.1.161 /fork on by default. Task tool renamed to Agent in v2.1.63 (Task(...) still works as alias). [uncertain]

**라이프사이클**

Stable, core, actively developed feature. Custom subagents, scopes, and frontmatter are stable/GA. A few sub-capabilities are newer or explicitly experimental: fork subagents / letting Claude spawn forks is experimental and staged-rollout; the type:"agent" style verification via hooks is experimental. No part is deprecated - the only removal is the interactive /agents wizard (v2.1.198), with file-based definitions unchanged.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Subagents.json`</sub>

---

## 8. Slash Commands

`자동화/확장`

### 기본 정보

**설정 명칭**

Custom slash commands (custom commands defined as .claude/commands/*.md; as of 2026 merged into Skills, where the same feature is expressed as .claude/skills/<name>/SKILL.md)

**파일 위치**

Project commands: .claude/commands/<name>.md (committed, shared with the team). Personal commands: ~/.claude/commands/<name>.md (all your projects). Subdirectories create namespaces, e.g. .claude/commands/frontend/component.md is invoked as /frontend:component. Each .md file's name (without extension) becomes the command typed after '/'. Anthropic has merged custom commands into Skills: a file at .claude/commands/deploy.md and a skill at .claude/skills/deploy/SKILL.md both create /deploy and behave the same way; existing .claude/commands/ files keep working and support the same frontmatter, but Skills are now the recommended form because they add a directory for supporting files and automatic model invocation.

**공식 문서**

Yes. The former dedicated slash-commands page now resolves to the Skills documentation at https://code.claude.com/docs/en/slash-commands (title: 'Extend Claude with skills'), which documents the .claude/commands/ format, frontmatter reference, string substitutions, and dynamic context injection. Related official pages: built-in and bundled commands reference at https://code.claude.com/docs/en/commands and the SDK equivalent at https://code.claude.com/docs/en/agent-sdk/slash-commands. The open Agent Skills standard is at https://agentskills.io.

**도입 버전 ⚠️**

Custom slash commands (.claude/commands/*.md prompt templates with $ARGUMENTS) were one of the earliest Claude Code extensibility features, present since the 2024/early-2025 releases. The merge of custom commands into the Skills system and the richer frontmatter/substitution surface described here landed across 2026 (v2.1.x). [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Precedence when names collide, most-to-least authoritative: enterprise/managed > personal (~/.claude) > project (.claude). A skill at any level overrides a bundled skill of the same name. Plugin commands/skills live in a plugin-name:command namespace and cannot collide with user/project entries. Critical rule: if a command (.claude/commands/foo.md) and a skill (.claude/skills/foo/SKILL.md) share a name, the skill takes precedence. Subdirectory namespacing (/frontend:component) prevents name clashes within one scope. Nested .claude/commands|skills below the working directory are also discovered on demand in monorepos.

**로딩 시점**

Primarily user-invoked: typing /<command-name> [args] expands the markdown file into a prompt injected into the conversation. Because commands are now unified with skills, the command's description is also loaded into the skill listing so the model can auto-invoke a matching command unless disable-model-invocation: true is set (classic .claude/commands files with only a body and no description behave as manual prompt templates). When invoked, any !`shell` / @file references and $ substitutions are rendered first, then the fully-expanded body enters context. As of v2.1.199 you can stack up to six commands/skills at the start of one message (e.g. /code-review /fix-issue 123).

**컨텍스트 비용**

The command body is on-demand: it only enters context when the command is invoked, and then stays in context for the rest of the session (auto-compaction re-attaches the most recent invocation within a token budget). The command's description (when present) is always loaded into the skill/command listing so the model knows it exists; that listing is budgeted (~1% of the context window by default, tunable via skillListingBudgetFraction / SLASH_COMMAND_TOOL_CHAR_BUDGET). Bodyless prompt-template commands with no description add essentially nothing until invoked.

### 채택도

**채택 근거 ⚠️**

Custom slash commands are among the most widely shared Claude Code artifacts. hesreallyhim/awesome-claude-code (a curated hub whose largest section is slash commands, CLAUDE.md files, and workflows) has ~21.6k GitHub stars. wshobson/commands advertises ~57 production-ready commands (workflows + tools) and has spawned mirrors/forks (igorjs/claude-commands-wshobson, webmattic/claude-commands). Other collections: danielrosehill/Claude-Slash-Commands, GetBindu/awesome-claude-code-and-skills, and searchable community indexes cataloging 300+ commands. Numerous 2026 guides (builder.io, alexop.dev, datacamp, claudedirectory.org, codesignal) treat /command files as a core onboarding step. [uncertain]

### 추천 설정

**설정 스니펫**

````
# File: .claude/commands/fix-issue.md  (invoked as /fix-issue 123)
# Frontmatter is optional; all fields work identically in .claude/commands/*.md and skills.
---
description: Fix a GitHub issue by number following our coding standards
argument-hint: [issue-number]
disable-model-invocation: true          # manual-only: don't let the model auto-run it
allowed-tools: Bash(gh *) Bash(git add *) Bash(git commit *)
model: inherit
---

## Live context (rendered before Claude sees the prompt)
- Issue: !`gh issue view $ARGUMENTS --json title,body -q '.title + "\n\n" + .body'`
- Current branch: !`git branch --show-current`
- Coding standards: @docs/CONTRIBUTING.md

## Task
Fix GitHub issue $ARGUMENTS:
1. Understand the requirements from the issue above
2. Implement the fix
3. Add or update tests
4. Create a conventional commit

# --- Namespacing: .claude/commands/frontend/component.md  ->  /frontend:component
# --- Positional args: use $ARGUMENTS (all), or $ARGUMENTS[0] / shorthand $0, $1, $2
# --- Named args via frontmatter:  arguments: [issue, branch]  then use $issue / $branch
# --- Multi-line shell block:
# ```!
# node --version
# git status --short
# ```
````

**결정적 vs 권고적**

Advisory. A slash command is a prompt-template: its rendered text is injected and the model decides how to act on it, so behavior is non-deterministic. The only deterministic parts are the preprocessing steps that run before the model sees anything: !`shell` command substitution, @file inclusion, and $ARGUMENTS/$N variable expansion. For guarantees the model cannot skip (formatting, blocking), use hooks instead; commands are for reusable intent, not enforcement.

### 모범 사례

**모범 사례**

1) Create commands reactively, not speculatively: take the single most-repeated paragraph from your recent sessions, drop it in .claude/commands/<verb>.md, add a one-line description. 2) Name files after the verb you'd want to type (fix-issue, commit, review). 3) Use $ARGUMENTS for the one or two slots that vary; use $0/$1 or named `arguments:` for multiple positional inputs, and quote multi-word args (/cmd "hello world" second). 4) Add argument-hint so autocomplete shows expected inputs. 5) Ground the prompt in live state with !`git diff`, !`gh pr diff`, @file references instead of asking the model to guess. 6) For side-effectful workflows (/deploy, /commit, /send-slack) set disable-model-invocation: true so only you trigger them, and pre-approve exactly the tools they need with narrow allowed-tools patterns like Bash(git commit *). 7) Commit project commands to version control so a teammate can use them with zero docs. 8) Follow the scope progression: personal (~/.claude/commands) -> project (.claude/commands) -> plugin for distribution. 9) Keep bodies concise (state what to do, not why); migrate to a skill directory when you need supporting files, reference docs, or automatic model invocation. 10) Use subdirectory namespacing (frontend/, backend/) to keep large command sets organized.

**안티패턴**

Building commands you have never actually needed (they rarely fit the real workflow). Putting long reference material inline in a frequently-auto-invoked command instead of moving it to a skill's supporting files (recurring token cost). Broad allowed-tools like Bash(*) that hand a template blanket shell access. Letting a side-effect command (deploy/commit) stay model-invocable, so Claude runs it unprompted because the code 'looks ready' — set disable-model-invocation: true. Forgetting that !`...` executes automatically at expansion time with your privileges, so an untrusted repo's committed command can run arbitrary shell the moment it is invoked. Naming a command the same as an existing skill and being surprised the skill wins. Using !`` interpolation for something that must be enforced (that belongs in a hook). Not quoting multi-word arguments, so $1 captures only the first word.

**보안 리스크**

주의 (caution / medium). A command .md is inert text until invoked, but on invocation two vectors execute with the user's full privileges: (a) !`shell` and ```! blocks run arbitrary commands during expansion, and (b) allowed-tools can silently pre-approve tools (e.g. Bash) while the command is active. Project commands live in the repo, so a malicious committed .claude/commands file is a code-execution risk — review third-party commands before invoking, and they only take effect after accepting the workspace-trust dialog. Mitigations: keep allowed-tools narrow, prefer disable-model-invocation for anything with side effects, and set disableSkillShellExecution: true (ideally in managed settings) to neutralize !`` execution org-wide.

### 최근 변경

**최근 변경 내역 ⚠️**

2026 (v2.1.x): Custom commands were merged into the Skills system — .claude/commands/*.md still works and shares the same frontmatter reference, but Skills (.claude/skills/<name>/SKILL.md) are the recommended form because they support supporting files and automatic model invocation, and a same-named skill now takes precedence over a command. Expanded string substitution: $ARGUMENTS[N] and the $N shorthand ($0, $1, ...), named `arguments:` frontmatter -> $name, plus ${CLAUDE_SESSION_ID}, ${CLAUDE_SKILL_DIR}, and ${CLAUDE_PROJECT_DIR} (v2.1.196+). Command/skill stacking at the start of one message, up to six (v2.1.199). Re-invocation with identical rendered content no longer duplicates the body in context (v2.1.202). Multi-line ```! shell blocks and the disableSkillShellExecution policy setting for turning off !`` execution. skillOverrides settings state 'off' now also hides entries from SDK/Remote Control callers (v2.1.199). [uncertain on exact per-version attribution]

**라이프사이클**

Stable and fully supported. .claude/commands/*.md is not deprecated and keeps working, but it is effectively superseded by / folded into Skills, which Anthropic documents as the recommended way to author new commands. Treat existing command files as a still-valid subset of the Skills feature.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Slash_Commands.json`</sub>

---

## 9. Output Styles

`UI/UX`

### 기본 정보

**설정 명칭**

outputStyle (Output Styles)

**파일 위치**

The `outputStyle` field lives in a settings file — by default `/config` saves your selection to `.claude/settings.local.json` (local project level), but it can be set in any settings layer (`~/.claude/settings.json` user, `.claude/settings.json` project, or managed policy settings.json). Custom styles are standalone Markdown files stored in one of three directories: `~/.claude/output-styles/` (user), `.claude/output-styles/` (project), or the managed-settings `.claude/output-styles/` (managed policy). Plugins can also ship styles in a plugin `output-styles/` directory. Related commands: `/config` (menu), the deprecated `/output-style` and `/output-style:new` commands.

**공식 문서**

Yes. Dedicated official page: 'Output styles' at https://code.claude.com/docs/en/output-styles (markdown source at https://code.claude.com/docs/en/output-styles.md). Covers built-in styles, the `outputStyle` setting, custom-style file format/frontmatter, how it modifies the system prompt, token cost, and comparisons to CLAUDE.md, --append-system-prompt, agents, and skills.

**도입 버전 ⚠️**

[uncertain] Output styles (including the Explanatory and Learning built-ins) were introduced in the Claude Code 1.x era around August 2025; the exact first version/date is not stated in the docs. The Proactive built-in style is a later addition. Documented version markers: the standalone `/output-style` command was deprecated in v2.1.73 and removed in v2.1.91; nested project-style same-name resolution (closest-to-cwd wins) was added in v2.1.178.

### 스코프 / 로딩

**우선순위 계층**

The `outputStyle` value follows the standard settings.json precedence chain: enterprise/managed policy > command-line args > local project (`.claude/settings.local.json`) > shared project (`.claude/settings.json`) > user (`~/.claude/settings.json`). Only one style is active at a time — the highest-priority layer's value wins (replace, not merge). The set of *available* custom styles, by contrast, is additive: styles are discovered from user, project (every `.claude/output-styles/` between cwd and repo root), managed, and plugin directories all at once. As of v2.1.178, when nested project directories define a style with the same name, the one closest to the working directory is used. A plugin style with `force-for-plugin: true` overrides the user's `outputStyle` setting whenever that plugin is enabled (first-loaded wins if several set it).

**로딩 시점**

Always-on for the session: the output style is baked into the system prompt, which Claude Code reads once at session start. It is not model-judged, path-matched, or invoked — it applies to every response. Because it is part of the system prompt, changing the style does NOT take effect mid-conversation; a change requires `/clear` or a new session to be picked up. All styles also emit periodic reminders during the conversation to keep Claude adhering to the style.

**컨텍스트 비용**

Always loaded into context (it is part of the system prompt), so it costs input tokens every session. The added system-prompt text increases input tokens, but prompt caching amortizes this after the first request in a session. Output-token cost varies by style: the built-in Explanatory and Learning styles are longer by design and increase output tokens; custom styles cost whatever their instructions tell Claude to produce. Note that changing the output style invalidates the prompt cache (it alters the cached system prompt).

### 채택도

**채택 근거 ⚠️**

Strong community adoption and attachment. Curated collection: github.com/hesreallyhim/awesome-claude-code-output-styles-that-i-really-like (an 'awesome' list of community styles). The feature's near-removal in late October 2025 triggered a rapid, high-volume community backlash — GitHub issues #10671 ('[FEATURE] Please don't remove Output-Styles!'), #10721 ('[BUG] IMPORTANT: 2.0.30 please KEEP the output-style'), plus #10672 and #10694 — with users flagging it as blocking production workflows, prompting Anthropic to reverse the deprecation within ~4 days. Numerous write-ups and guides exist (tessl.io, eesel.ai, builder.io '8 Claude Code Settings', note.com, heyclau.de, claude-blog.setec.rs, claudepluginhub.com), and marketplaces list output-style migration skills. [uncertain] exact GitHub star counts and marketplace install numbers were not verified.

### 추천 설정

**설정 스니펫**

```
// 1) Select a built-in style via the setting directly (any settings.json layer):
{
  "outputStyle": "Explanatory"
}
// Built-in values: "Default", "Proactive", "Explanatory", "Learning", or a custom style's name.
// Easiest path: run `/config` -> Output style -> pick from the menu (saves to .claude/settings.local.json).

// 2) Create a custom output style — a Markdown file at
//    ~/.claude/output-styles/diagrams-first.md   (user)
// or .claude/output-styles/diagrams-first.md     (project)
// The file name is the style name unless `name` is set in frontmatter.
---
name: Diagrams first
description: Lead every explanation with a diagram
keep-coding-instructions: true
---

When explaining code, architecture, or data flow, start with a Mermaid diagram
showing the structure, then explain in prose.

## Diagram conventions
Use `flowchart TD` for control flow and `sequenceDiagram` for request paths.
Keep diagrams under 15 nodes.

// 3) Non-coding custom style (omit keep-coding-instructions to DROP Claude Code's
//    built-in software-engineering instructions entirely, e.g. a writing assistant):
---
name: Tech writer
description: Acts as a documentation writer, not a software engineer
---
You are a technical writer. Produce clear, well-structured prose...

// 4) Plugin-shipped style that auto-applies when the plugin is enabled:
---
name: Company voice
description: Enforces house style
force-for-plugin: true
---
...

// Frontmatter fields: name, description, keep-coding-instructions (default false),
// force-for-plugin (plugins only, default false).
// Any change to the active style takes effect only after /clear or a new session.
```

**결정적 vs 권고적**

Advisory. Output styles are natural-language instructions injected into the system prompt that the model is asked (and periodically reminded) to follow — they steer behavior but do not deterministically force it, unlike code-enforced mechanisms such as hooks or permissions. The one deterministic aspect is the loading mechanism itself: the harness reliably places the chosen style's text in the system prompt at session start and toggles the built-in coding instructions on/off via keep-coding-instructions.

### 모범 사례

**모범 사례**

1) Use output styles for HOW Claude communicates (role, tone, default format) that should apply to EVERY turn; use CLAUDE.md for project facts/conventions, `--append-system-prompt` for one-off single-invocation additions, agents for separately-scoped helpers, and skills for reusable invoked workflows. 2) Set `keep-coding-instructions: true` when you still want Claude coding normally but with a communication tweak (e.g. always answer with a diagram); OMIT it (default false) when Claude isn't doing software engineering at all (writing assistant, data analyst, business tasks) so the built-in SWE instructions are dropped. 3) Remember changes only take effect after `/clear` or a new session — the style is read once at session start; don't expect a mid-conversation switch to apply. 4) Add a clear `description` so the `/config` picker is legible. 5) Prefer `/config` to select styles now that the standalone `/output-style` command is removed (v2.1.91+). 6) Scope styles by level: user dir for personal defaults, project dir for team-shared styles committed to the repo, managed policy for org enforcement, plugins (with optional `force-for-plugin`) for distribution. 7) Keep the added system-prompt text concise to limit input-token overhead (though prompt caching amortizes it). 8) For nested repos, rely on the v2.1.178+ rule that the same-named style closest to the working directory wins.

**안티패턴**

Using an output style to store project/codebase context or conventions — that belongs in CLAUDE.md; a style is for role/tone/format. Expecting a style switch to apply immediately in the current conversation (it needs /clear or a new session). Forgetting that omitting keep-coding-instructions silently STRIPS Claude Code's built-in software-engineering guidance (scoping changes, comments, verification) — a common cause of a custom style suddenly 'forgetting how to code'. Bloating the style with long instructions that inflate every request's input tokens. Confusing the file name vs. the `name` frontmatter (file name is the default style name). Assuming the deprecated `/output-style` command still exists (removed v2.1.91 — use /config or edit the setting). Setting `force-for-plugin: true` casually, since it overrides the user's own outputStyle choice whenever the plugin is enabled.

**보안 리스크**

안전 (Safe / low risk). Output styles only inject natural-language text into the system prompt; they cannot execute code, bypass permissions, or auto-run tools, so they are not a code-execution vector like hooks or statusLine. The modest cautions are: (a) a plugin/project/managed style with `force-for-plugin: true` or high-precedence placement can silently change Claude's behavior and tone for everyone using that repo/plugin, and (b) dropping keep-coding-instructions removes safety-relevant coding guidance — review third-party or team-shared styles before adopting them. Otherwise risk is minimal.

### 최근 변경

**최근 변경 내역**

Turbulent then stabilized in 2025 H2 – 2026 H1. Late October 2025 (~v2.0.30): Anthropic announced deprecating output styles in favor of plugins/system-prompt flags; ~4 days of community backlash (GitHub issues #10671, #10721, #10672, #10694) led to restoration by ~v2.0.32 (early Nov 2025). The feature was then ENHANCED: the `keep-coding-instructions` frontmatter option (hybrid styles that keep SWE behavior) and plugin distribution / `force-for-plugin` support were added. The standalone `/output-style` command was deprecated in v2.1.73 and removed in v2.1.91 (superseded by `/config` and direct `outputStyle` editing). v2.1.178 added nested-project resolution where a same-named style closest to the working directory wins. The Proactive built-in style (stronger autonomous-execution guidance than auto mode, without changing permission mode) is part of the current built-in set.

**라이프사이클**

Stable and generally available, and a first-class documented feature (dedicated docs page, `/config` integration, plugin support). Note one nuance: the FEATURE is stable, but its standalone `/output-style` slash command is deprecated/removed (v2.1.91) — configuration now goes through `/config` or the `outputStyle` setting. The 2025 deprecation of the whole feature was reversed and it is not currently slated for removal.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Output_Styles.json`</sub>

---

## 10. CLAUDE.md 구조 및 계층

`메모리/문서`

### 기본 정보

**설정 명칭**

CLAUDE.md (memory files) — structure and hierarchy

**파일 위치**

CLAUDE.md files live at several scoped locations, loaded from broadest to most specific: (1) Managed policy — macOS /Library/Application Support/ClaudeCode/CLAUDE.md, Linux/WSL /etc/claude-code/CLAUDE.md, Windows C:\Program Files\ClaudeCode\CLAUDE.md (or inline via the managed-settings.json "claudeMd" key); (2) User ~/.claude/CLAUDE.md; (3) Project ./CLAUDE.md or ./.claude/CLAUDE.md; (4) Local ./CLAUDE.local.md (gitignored, personal per-project). Nested CLAUDE.md/CLAUDE.local.md in subdirectories load on demand. Related: topic files via @path imports, path-scoped .claude/rules/*.md, and user-level ~/.claude/rules/. Browse loaded files with /memory.

**공식 문서**

Yes. Primary page: https://code.claude.com/docs/en/memory ('How Claude remembers your project'), covering CLAUDE.md locations/hierarchy, load order, @path imports, .claude/rules/, managed CLAUDE.md, claudeMdExcludes, and auto memory. Supporting pages: https://code.claude.com/docs/en/commands (/init, /memory, /doctor), https://code.claude.com/docs/en/context-window (where CLAUDE.md loads, compaction behavior), and https://code.claude.com/docs/en/large-codebases (monorepo layout).

**도입 버전 ⚠️**

CLAUDE.md has existed since Claude Code's early releases in 2025 as the core persistent-instructions mechanism; the @path import syntax and directory-walk hierarchy were present from the memory feature's introduction. Exact first version/date not authoritatively documented. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Unlike settings.json (where more-specific layers override), CLAUDE.md files are ADDITIVE/concatenated, not override-based. Load order is broadest-to-most-specific so the most specific instruction appears LAST in context: Managed policy CLAUDE.md → User (~/.claude/CLAUDE.md) → Project (./CLAUDE.md or ./.claude/CLAUDE.md) → Local (./CLAUDE.local.md). Across the directory tree, content is ordered from filesystem root down to the working directory (a parent foo/CLAUDE.md appears before child foo/bar/CLAUDE.md); within a directory, CLAUDE.local.md is appended after CLAUDE.md. All discovered files are concatenated rather than overriding each other, so there is no true 'winner' — contradictions are resolved by Claude arbitrarily (author should remove conflicts). Managed policy CLAUDE.md cannot be excluded by lower layers; other files can be skipped with the claudeMdExcludes setting (glob patterns, arrays merge across layers). User-level .claude/rules/ load before project rules, giving project rules higher effective priority.

**로딩 시점**

Always-on at session start. Claude walks up the directory tree from the cwd, collecting every CLAUDE.md and CLAUDE.local.md, and loads them IN FULL into the context window at launch (regardless of length). CLAUDE.md content is delivered as a user message after the system prompt, not enforced config. @path imports are expanded and loaded at launch alongside the referencing file (recursive, max depth four hops). Subdirectory CLAUDE.md/CLAUDE.local.md do NOT load at launch — they load on demand when Claude reads files in those subdirectories. .claude/rules/*.md without a paths frontmatter load every session (same priority as .claude/CLAUDE.md); path-scoped rules load only when Claude touches matching files. Project-root CLAUDE.md is re-read from disk and re-injected after /compact; nested files reload only when their subdirectory is next read.

**컨텍스트 비용**

Always-loaded and token-consuming: CLAUDE.md files (and their @path imports) are loaded in full into every session's context window, so every line has a persistent per-session cost. This is why the official guidance is to target under 200 lines — longer files consume more context and reduce adherence. Splitting into @path imports helps organization but does NOT reduce context cost (imports still load at launch). To make instructions on-demand (not always-loaded), move them to path-scoped .claude/rules/ (load only when matching files are touched) or to skills (load only when invoked/relevant). Block-level HTML comments (<!-- ... -->) are stripped before injection, so maintainer notes cost no tokens.

### 채택도

**채택 근거 ⚠️**

CLAUDE.md is the de-facto standard memory/instructions file for Claude Code and one of its most-written-about features. Extensive 2026 community coverage includes 'CLAUDE.md Best Practices: The Complete 2026 Guide' (dev.to/nishilbhave), UX Planet's '10 Sections to Include', Blink's '10-Section Template', Buildcamp's 'Ultimate Guide to CLAUDE.md in 2026', plus curated hierarchy guides (agentfactory.panaversity.org, claudearchitectcertification.com) and community how-tos (luongnv89/claude-howto 02-memory). The emergence of the cross-tool AGENTS.md convention — which Claude Code interoperates with via @AGENTS.md import or symlink — further signals broad adoption. [uncertain]

### 추천 설정

**설정 스니펫**

```
# Project CLAUDE.md — keep under ~200 lines; lead with commands

@AGENTS.md   # optional: reuse an existing cross-tool instructions file

## Commands
- Build:  `npm run build`
- Test:   `npm test`            # run before committing
- Lint:   `npm run lint`
- Dev:    `npm run dev`

## Architecture
- API handlers live in `src/api/handlers/`
- Shared types in `src/types/`
- See @docs/architecture.md for the full overview

## Conventions
- Use 2-space indentation
- Prefer named exports; no default exports
- All API endpoints must validate input

## References
- Git workflow: @docs/git-instructions.md
- Personal, non-committed prefs: put in ./CLAUDE.local.md (add to .gitignore)

<!-- Maintainer note: this comment is stripped before load and costs no tokens -->

# ---- Optional: managed org-wide CLAUDE.md inline in managed-settings.json ----
# {
#   "claudeMd": "Always run `make lint` before committing.\nNever push directly to main."
# }
#
# ---- Optional: exclude noisy ancestor files (.claude/settings.local.json) ----
# {
#   "claudeMdExcludes": ["**/monorepo/CLAUDE.md", "/home/user/monorepo/other-team/.claude/rules/**"]
# }
#
# ---- Optional: path-scoped rule (.claude/rules/api.md) — on-demand, not always loaded ----
# ---
# paths:
#   - "src/api/**/*.ts"
# ---
# # API Development Rules
# - Use the standard error response format
```

**결정적 vs 권고적**

Advisory, not deterministic. CLAUDE.md is context (a user message after the system prompt), not enforced configuration — Claude reads it and tries to follow it, but there is no guarantee of strict compliance, especially for vague or conflicting instructions. For hard guarantees that must run at a fixed point (e.g. before every commit), use a PreToolUse hook; for client-enforced blocks use permissions.deny in managed settings. The structure/hierarchy itself (which files load, in what order, @import expansion, the 200-line trim heuristics) is deterministic harness behavior; only the instruction-following is advisory.

### 모범 사례

**모범 사례**

1) Keep each CLAUDE.md under ~200 lines — every line has a per-session context cost, and longer files reduce adherence. 2) Lead with the exact commands (build/test/lint/run) — highest-ROI section; then architecture, then conventions, then references. 3) Be specific and verifiable: 'Use 2-space indentation' beats 'format code properly'; 'Run npm test before committing' beats 'test your changes'. 4) Use markdown headers + bullets so Claude can scan structure and extract what it needs. 5) Point to detail instead of pasting it — use @path imports (recursive, max 4 hops) or, better for context savings, path-scoped .claude/rules/ that load only when matching files are touched, and skills for on-demand workflows. 6) Only write what is true every session; move multi-step procedures or subtree-specific rules to skills or .claude/rules/. 7) Commit the project CLAUDE.md; keep personal prefs in gitignored CLAUDE.local.md (or import ~/.claude/... to share personal instructions across worktrees). 8) Run /init to bootstrap and /doctor (v2.1.206+) to propose trims — it cuts content Claude can derive from the codebase (directory layouts, dependency lists, architecture overviews) and keeps pitfalls, rationale, and conventions that differ from defaults. 9) Use HTML comments for maintainer notes (stripped before load, zero token cost). 10) Periodically review for contradictions across nested/user/project files; use claudeMdExcludes in monorepos to drop irrelevant ancestor files. 11) Reuse existing AGENTS.md via @AGENTS.md import or symlink to avoid duplication. 12) Verify what actually loaded with /memory (and the InstructionsLoaded hook for deeper debugging).

**안티패턴**

Letting CLAUDE.md grow to many hundreds of lines (context rot: rules that matter get diluted and adherence quietly drops — Chroma's 2025 benchmark showed frontier models, incl. Claude Opus 4, lose accuracy as input grows). Assuming @path imports save context — they still load in full at launch; only rules/skills defer loading. Treating CLAUDE.md as enforcement — it is advisory, so security/lifecycle guarantees belong in hooks or permissions.deny, not prose. Writing vague instructions ('format nicely'). Leaving contradictory rules across user/project/nested files (Claude picks one arbitrarily). Pasting content Claude can trivially re-derive (dir trees, dependency lists). Duplicating the same guidance in CLAUDE.md and AGENTS.md instead of importing. Committing machine-specific secrets/sandbox URLs to the shared CLAUDE.md instead of CLAUDE.local.md. Expecting nested subdirectory CLAUDE.md to persist through /compact (only project-root is re-injected).

**보안 리스크**

안전 (low). CLAUDE.md is plain-text advisory context that does not execute code or grant permissions, so it is not a direct code-execution vector. Minor cautions: (a) it is NOT a security control — never rely on 'do not do X' prose to enforce policy; use permissions.deny / PreToolUse hooks instead; (b) @path imports from external/untrusted files trigger a one-time approval dialog (declining disables them permanently) — review imported paths before approving; (c) keep secrets out of committed CLAUDE.md (use gitignored CLAUDE.local.md). Managed policy CLAUDE.md is the one layer that cannot be overridden or excluded, which is the intended org-control property.

### 최근 변경

**최근 변경 내역 ⚠️**

2026 H1 additions centered on trimming and cleanup: /doctor became a full setup checkup that can diagnose AND fix issues, with /checkup as its alias (v2.1.205, ~2026-07-08). The /doctor checkup now proposes trims for a checked-in CLAUDE.md — cutting content Claude can derive from the codebase (directory layouts, dependency lists, architecture overviews) while keeping pitfalls, rationale, and conventions — requiring v2.1.206+. Path-scoped .claude/rules/ symlinked-checkout matching landed in v2.1.198, and a glob-bracket edge-case fix (invalid pattern matches nothing instead of failing all Reads) in v2.1.207. The interactive multi-phase /init flow is gated behind CLAUDE_CODE_NEW_INIT=1. Auto memory (Claude-authored MEMORY.md notes, first 200 lines / 25KB loaded per session) is the newer complement to human-authored CLAUDE.md. The four-hop @import depth and 200-line target are longstanding, still-current guidance. [uncertain]

**라이프사이클**

Stable and actively developed core feature. The hierarchy, @path imports, and .claude/rules/ are stable. CLAUDE.local.md remains supported but is de-emphasized in favor of .gitignore'd local files, path-scoped rules, and home-directory imports for cross-worktree sharing. The interactive /init flow (CLAUDE_CODE_NEW_INIT=1) is opt-in/newer; /doctor CLAUDE.md trimming requires v2.1.206+.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/CLAUDEmd_구조_및_계층.json`</sub>

---

## 11. Sandbox / 위험 작업 안전설정

`권한/보안`

### 기본 정보

**설정 명칭**

Sandbox & dangerous-operation safety settings — the cluster of controls that govern how autonomously and safely Claude Code may run risky Bash/tool actions: bypassPermissions mode (CLI --dangerously-skip-permissions / --allow-dangerously-skip-permissions) and its managed lockdown permissions.disableBypassPermissionsMode; the OS-level Bash sandbox (sandbox.enabled and the /sandbox command) including sandbox.credentials (deny/mask credential files & env vars), sandbox.allowAppleEvents (macOS), sandbox.allowUnixSockets, sandbox.allowUnsandboxedCommands / dangerouslyDisableSandbox escape hatch, sandbox.failIfUnavailable, enableWeakerNestedSandbox / enableWeakerNetworkIsolation; and git worktree isolation (--worktree, subagent isolation: worktree, EnterWorktree/ExitWorktree).

**파일 위치**

.claude/settings.json (project, committed), .claude/settings.local.json (project-local, gitignored — this is what the /sandbox panel writes), ~/.claude/settings.json (user/global — required scope for allowAppleEvents and credential mask), and managed/enterprise settings (macOS /Library/Application Support/ClaudeCode/managed-settings.json, Linux/WSL /etc/claude-code/managed-settings.json, Windows C:\Program Files\ClaudeCode\managed-settings.json). The `sandbox` object, the `worktree` object, and `permissions.disableBypassPermissionsMode`/`permissions.disableAutoMode` all live in these settings.json files. bypassPermissions is also invoked at the CLI (--dangerously-skip-permissions) and worktrees via --worktree/-w or subagent frontmatter `isolation: worktree`. Interactive control via the /sandbox slash command.

**공식 문서**

Extensively documented across several official pages. Primary: https://code.claude.com/docs/en/sandboxing (Configure the sandboxed Bash tool — covers sandbox.*, credentials, allowAppleEvents, allowUnixSockets, escape hatch, dangerouslyDisableSandbox, OS enforcement, security limitations). https://code.claude.com/docs/en/permission-modes (bypassPermissions mode, --dangerously-skip-permissions, protected paths, root/sudo block). https://code.claude.com/docs/en/settings#sandbox-settings (full sandbox key reference). https://code.claude.com/docs/en/worktrees (worktree isolation, --worktree, isolation: worktree, EnterWorktree). https://code.claude.com/docs/en/sandbox-environments (dev containers / VMs comparison). https://code.claude.com/docs/en/security and https://code.claude.com/docs/en/devcontainer. Starter configs: https://github.com/anthropics/claude-code/tree/main/examples/settings . Standalone primitive: https://github.com/anthropic-experimental/sandbox-runtime (@anthropic-ai/sandbox-runtime).

**도입 버전 ⚠️**

[uncertain] The bypassPermissions mode / --dangerously-skip-permissions flag predates versioned docs and is long-standing. The OS-level Bash sandbox and /sandbox command are a 2025-2026 feature area. Datable sub-features: sandbox.credentials (deny) requires v2.1.187+ (the settings reference notes v2.1.191 for the managed-settings validation behavior); credential `mode: "mask"` and network.tlsTerminate require v2.1.199+; per-session host allow after one approval landed v2.1.191; the EnterWorktree approval prompt for paths outside .claude/worktrees was added v2.1.206; subagent task-description pre-check at spawn requires v2.1.178+. Exact first-ship version of the sandbox itself is uncertain.

### 스코프 / 로딩

**우선순위 계층**

Follows standard settings precedence: managed > CLI args > local (.claude/settings.local.json) > project (.claude/settings.json) > user (~/.claude/settings.json). Important scope nuances: (1) Boolean sandbox keys (enabled, failIfUnavailable) take the managed value and ignore local overrides. (2) Array keys (excludedCommands, filesystem.allowWrite/allowRead, credentials deny entries, network.allowedDomains) MERGE across scopes, so any scope can only widen excludedCommands/allowWrite or narrow via deny — a deny credential entry from any scope cannot be removed by another scope. (3) sandbox.allowAppleEvents is honored ONLY from user, managed, or CLI settings — project settings are ignored (prevents an untrusted repo from lifting Apple Events isolation). (4) Credential `mask`, network.tlsTerminate, and credentials.allowPlaintextInject are ignored from a repo's project/local settings (only user/managed/--settings) because masking authorizes sending the real secret to a host. (5) allowManagedReadPathsOnly / allowManagedDomainsOnly let managed settings forbid user/project scopes from widening read paths or network domains. (6) permissions.disableBypassPermissionsMode / disableAutoMode are managed-settings controls set to "disable". (7) The sandbox auto-denies writes to any settings.json at every scope and to the managed settings dir, so a sandboxed command cannot rewrite its own policy.

**로딩 시점**

Loaded at session start and enforced by the harness/OS, not by the model. bypassPermissions cannot be entered from a session started without an enabling flag — you must restart with --permission-mode bypassPermissions / --dangerously-skip-permissions (or --allow-dangerously-skip-permissions to add it to the Shift+Tab cycle without activating). The sandbox boundary is enforced at the OS level (macOS Seatbelt; Linux/WSL2 bubblewrap + socat + optional seccomp) on every Bash command and ALL its child processes for the whole session, independent of what the model chose to run. /sandbox opens an interactive panel (Mode/Overrides/Config tabs) that writes sandbox choices to .claude/settings.local.json. The dangerouslyDisableSandbox retry and worktree entry are per-tool-call events. worktree isolation triggers at launch (--worktree) or when the model calls EnterWorktree / spawns a subagent whose frontmatter has isolation: worktree.

**컨텍스트 비용**

Negligible/near-zero token cost. These are harness/OS enforcement metadata, not injected into the model context. The sandbox, credential rules, and worktree isolation add no prompt tokens; auto mode's classifier (a separate safety layer often paired with these) does add token/latency overhead per shell/network action, but the sandbox itself does not. Worktrees add disk (a separate checkout) rather than context cost.

### 채택도

**채택 근거**

Widely covered as a security-critical topic in 2026. Anthropic's own engineering guidance and reference devcontainer (anthropics/claude-code, examples/settings + .devcontainer) explicitly recommend running --dangerously-skip-permissions only inside a container as a non-root user. Anthropic published 'How we built Claude Code auto mode: a safer way to skip permissions' (anthropic.com/engineering/claude-code-auto-mode) reporting ~93% of permission prompts are approved, motivating safer middle-grounds. Extensive third-party guides: morphllm.com 'claude --dangerously-skip-permissions (2026): 5 Safer Setups', ksred.com safe-usage guide + configs, truefoundry.com 'What It Does and When Not to Use It', claudefa.st 'Claude Code Sandbox Guide 2026', inventivehq.com permissions-and-sandboxing KB, and Medium posts. The community shorthand 'YOLO mode' for --dangerously-skip-permissions is widespread. sandbox.credentials and allowAppleEvents are newer and less blogged, but appear in official examples and changelog-level docs.

### 추천 설정

**설정 스니펫**

```
// ~/.claude/settings.json — recommended safe autonomous defaults (macOS/Linux/WSL2)
{
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,          // hard-fail instead of silently running unsandboxed (managed deployments)
    "allowUnsandboxedCommands": false,  // Strict mode: ignore dangerouslyDisableSandbox escape hatch
    "excludedCommands": ["docker *"],   // tools incompatible with the sandbox run outside it (keep this list narrow)
    "filesystem": {
      "allowWrite": ["~/.kube", "/tmp/build"],
      "denyRead": ["~/.aws", "~/.ssh"]  // default read policy still exposes these otherwise
    },
    "credentials": {
      "files": [
        { "path": "~/.aws/credentials", "mode": "deny" },
        { "path": "~/.ssh",             "mode": "deny" }
      ],
      "envVars": [
        { "name": "GITHUB_TOKEN", "mode": "deny" },
        { "name": "NPM_TOKEN",    "mode": "deny" }
      ]
    },
    "network": {
      "allowedDomains": ["registry.npmjs.org", "*.github.com"]
    }
    // allowAppleEvents: leave UNSET/false — enabling it removes code-execution isolation on macOS
  },
  "permissions": {
    "disableBypassPermissionsMode": "disable"  // managed settings: forbid --dangerously-skip-permissions org-wide
  }
}

// Masking a token so tools keep working while the plaintext never touches the sandboxed command
// (user/managed settings only; requires v2.1.199+):
{
  "sandbox": {
    "enabled": true,
    "network": { "tlsTerminate": {}, "allowedDomains": ["*.github.com"] },
    "credentials": { "envVars": [ { "name": "GH_TOKEN", "mode": "mask", "injectHosts": ["api.github.com"] } ] }
  }
}

// Git worktree isolation for parallel/autonomous work:
//   claude --worktree feature-auth        (creates .claude/worktrees/feature-auth on branch worktree-feature-auth)
// settings for subagent isolation base branch:
{ "worktree": { "baseRef": "head" } }   // or "fresh" (default: branch from origin/HEAD)
// subagent frontmatter: isolation: worktree
// .gitignore should include: .claude/worktrees/

// Autonomous run ONLY inside an isolated container/dev container, never on a host with real creds:
//   claude --dangerously-skip-permissions   (equivalent: --permission-mode bypassPermissions)
```

**결정적 vs 권고적**

Split. The SANDBOX is deterministic / OS-enforced: Seatbelt/bubblewrap hold the filesystem and network boundary on the running process regardless of what the model chose or prompt injection attempted, and settings.json writes are auto-denied. credentials deny/mask, denyRead, disableBypassPermissionsMode, and worktree file isolation are likewise code-enforced. bypassPermissions is the opposite — a deterministic REMOVAL of guardrails (nothing replaces the prompt). Auto mode (the recommended middle ground) is advisory-ish: a model classifier reviews actions and can be wrong, so it is not a hard boundary. Network filtering is only partially deterministic: the proxy allows by client-supplied hostname without TLS inspection by default, so domain fronting can bypass a broad allowlist.

### 모범 사례

**모범 사례**

1) NEVER run --dangerously-skip-permissions / bypassPermissions on a host with real credentials or network access — it disables all prompts AND protected-path checks; only explicit ask rules and rm of / or ~ still stop it. Use it ONLY in an isolated container/VM/dev container (Anthropic ships a reference .devcontainer). 2) Prefer safer alternatives to full bypass: auto mode (classifier-reviewed, far fewer prompts) or the sandbox's auto-allow mode (OS boundary contains the command) rather than turning off checks entirely. 3) Enable the sandbox (sandbox.enabled) and combine BOTH filesystem and network isolation — network-only or filesystem-only leaves an exfiltration or backdoor path. 4) Protect secrets explicitly: the default read policy still exposes ~/.aws and ~/.ssh, so add sandbox.credentials deny entries (or filesystem.denyRead) for credential files and unset secret env vars; use mode:"mask" (+ network.tlsTerminate, user/managed scope) when a tool must still authenticate. 5) For managed/unattended fleets set failIfUnavailable:true (fail closed) and allowUnsandboxedCommands:false (Strict mode, ignore the dangerouslyDisableSandbox escape hatch); lock with allowManagedReadPathsOnly / allowManagedDomainsOnly and permissions.disableBypassPermissionsMode:"disable". 6) Run as a NON-root user — --dangerously-skip-permissions refuses to start as root/sudo (the check is skipped inside a recognized sandbox; the dev container runs as non-root by design). 7) Keep excludedCommands narrow and audit each entry — every excluded tool runs OUTSIDE the boundary, and there is no managed-only lockdown for it. 8) Prefer sandbox.filesystem.allowWrite over excludedCommands when a subprocess (kubectl/terraform/npm) needs to write a path. 9) Use git worktrees (--worktree or subagent isolation: worktree) to isolate parallel/autonomous edits; gitignore .claude/worktrees/, use .worktreeinclude to copy needed .env files, and note the sandbox still allows worktrees to write the main repo's shared .git for commits while denying hooks/ and config. 10) Layer defenses: permissions (which tools/paths) + sandbox (OS enforcement) + auto-mode classifier + PreToolUse hooks.

**안티패턴**

1) Running --dangerously-skip-permissions ('YOLO mode') on your real machine / bare metal — the single most dangerous misconfiguration; no protection against prompt injection or destructive actions. 2) Enabling sandbox but leaving ~/.aws / ~/.ssh readable (the default) — a compromised agent can read and, with a broad allowedDomains, exfiltrate them. 3) Turning on sandbox.allowAppleEvents to fix an `open`/`osascript` error-600 without understanding it REMOVES code-execution isolation (sandboxed commands can launch other apps unsandboxed and drive them via AppleScript). Prefer adding the command to excludedCommands instead. 4) Allowing dangerous Unix sockets via allowUnixSockets — e.g. /var/run/docker.sock effectively grants host access and bypasses the sandbox. 5) Broad allowedDomains like github.com — creates a data-exfiltration path (domain fronting works because the proxy doesn't inspect TLS by default). 6) Using enableWeakerNestedSandbox / enableWeakerNetworkIsolation without an outer isolation layer — both materially weaken security. 7) Assuming the sandbox is a complete isolation boundary — docs are explicit it is not; it reduces, not eliminates, risk. 8) Granting sandbox write access to $PATH dirs, /etc, or shell rc files (.bashrc/.zshrc) — enables privilege escalation. 9) Running bypass mode as root (blocked anyway) or committing settings that try to enable auto/bypass from a repo (project/local settings for auto and bypassPermissions defaultMode are ignored on purpose). 10) Relying on masking configured in a repo's .claude/settings.json — it's ignored; masking is honored only from user/managed/--settings.

**보안 리스크**

위험 (High / security-critical — this is the single most safety-sensitive settings cluster in Claude Code). bypassPermissions / --dangerously-skip-permissions is the highest-risk control: it removes all prompts and protected-path checks and offers zero prompt-injection protection, so it must be confined to isolated, credential-free environments. The sandbox and sandbox.credentials are risk-REDUCING controls, but their defaults still expose credential files, and several knobs (allowAppleEvents, allowUnixSockets to docker.sock, enableWeakerNestedSandbox/NetworkIsolation, broad allowedDomains, wide excludedCommands/allowWrite) each punch a hole in the boundary. Even fully configured, the sandbox is explicitly NOT a complete isolation boundary (no default TLS inspection → domain-fronting exfiltration). Treat sandbox + auto mode + narrow permissions + container isolation as layered defense; never rely on any one alone.

### 최근 변경

**최근 변경 내역 ⚠️**

Very active area through 2026 H1. (a) sandbox.credentials introduced (deny for files/env vars, v2.1.187+; managed-settings validation semantics noted v2.1.191); (b) credential mode:"mask" + sandbox.network.tlsTerminate added v2.1.199 to keep auth working while hiding plaintext; credentials.allowPlaintextInject related control; (c) per-session network host approval — as of v2.1.191, approving a host once allows it for the rest of the session instead of prompting each connection; (d) auto mode shipped as the recommended safer alternative to full bypass, with the classifier explicitly flagging launching agent loops via --dangerously-skip-permissions/--no-sandbox and greatly expanded default blocks through v2.1.195–2.1.205; (e) worktree hardening — EnterWorktree now prompts before entering a path outside .claude/worktrees (v2.1.206), worktree enter/exit relocates the transcript (v2.1.198), project-scope plugins load in worktrees (v2.1.200), Windows nested-junction cleanup fix (v2.1.205); (f) bypassPermissions now also skips protected-path prompts (v2.1.126) while rm -rf / and ~ still act as a circuit breaker and requiresUserInteraction MCP tools still prompt (v2.1.199); (g) --allow-dangerously-skip-permissions variant adds the mode to the Shift+Tab cycle without activating it; (h) Strict sandbox mode surfaced in the /sandbox Overrides tab (allowUnsandboxedCommands:false). Exact dates for individual keys are [uncertain].

**라이프사이클**

Mixed but all supported. bypassPermissions / --dangerously-skip-permissions: stable/GA, long-standing, not deprecated (but positioned as last-resort; auto mode is the promoted safer path). The OS-level Bash sandbox and /sandbox: GA on macOS/Linux/WSL2 (native Windows unsupported — use WSL2). Git worktree isolation: GA. Newer sub-features are stable except network.tlsTerminate, which is explicitly labeled experimental (v2.1.199+). No deprecations announced; the cluster is being actively extended (credential masking, expanded auto-mode blocks, worktree hardening).

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Sandbox_위험_작업_안전설정.json`</sub>

---

## 12. settings 파일 계층 (user/project/local)

`메모리/문서`

### 기본 정보

**설정 명칭**

Settings file hierarchy (user / project / local / managed) — settings.json vs settings.local.json

**파일 위치**

Five layered sources, all named settings.json except the enterprise file: (1) User/global: ~/.claude/settings.json (Windows: %USERPROFILE%\.claude\settings.json) — applies to every project. (2) Project shared/committed: <repo>/.claude/settings.json — checked into source control and shared with the team. (3) Project local/personal: <repo>/.claude/settings.local.json — NOT checked in, per-developer machine overrides; auto-added to git exclude by Claude Code. (4) Managed/enterprise: macOS /Library/Application Support/ClaudeCode/managed-settings.json, Linux/WSL /etc/claude-code/managed-settings.json, Windows C:\Program Files\ClaudeCode\managed-settings.json, plus a managed-settings.d/ drop-in directory merged alphabetically and OS policy stores (macOS com.anthropic.claudecode plist, Windows HKLM/HKCU SOFTWARE\Policies\ClaudeCode registry). (5) Command-line flags for the current session. Edit interactively with /config; the same three-tier split (user/project/local) also governs sibling config: agents/, CLAUDE.md (CLAUDE.local.md), MCP (~/.claude.json, .mcp.json), and plugins.

**공식 문서**

Officially documented as the core of the settings reference. Primary: https://code.claude.com/docs/en/settings (Settings — file locations, precedence, merge rules, /config). Related: https://code.claude.com/docs/en/permissions (project allow rules & workspace trust interaction with settings.local.json), https://code.claude.com/docs/en/iam (managed/enterprise settings), https://code.claude.com/docs/en/memory (CLAUDE.md hierarchy). Starter examples: https://github.com/anthropics/claude-code/tree/main/examples/settings. JSON schema for editor validation: https://json.schemastore.org/claude-code-settings.json

**도입 버전 ⚠️**

[uncertain] The user/project/local three-tier settings model has existed since early Claude Code releases and predates most versioned docs, so no single introduction version/date is authoritative. Individual refinements are versioned: single-option /config edits (e.g. /config verbose=true) in v2.1.181+, tolerant parsing of invalid managed-settings entries in v2.1.169+, removal of the legacy Windows C:\ProgramData\ClaudeCode\ managed path in v2.1.75+, and the workspace-trust fix for settings.local.json allow rules in v2.1.200 (regressed v2.1.196–199).

### 스코프 / 로딩

**우선순위 계층**

Standard settings precedence, highest to lowest: (1) Managed/enterprise settings — cannot be overridden by anything, including CLI args; (2) Command-line arguments — temporary, session-only; (3) Local project settings .claude/settings.local.json — overrides project and user; (4) Shared project settings .claude/settings.json — overrides user; (5) User settings ~/.claude/settings.json — lowest. Merge semantics differ by value type: SCALARS (string/bool/number) are replaced by the highest-precedence source; ARRAYS generally concatenate and de-duplicate across scopes (e.g. permissions.allow/deny, sandbox.filesystem.allowWrite) rather than override — with documented exceptions such as fallbackModel where only the highest-precedence file that defines it supplies the whole chain; OBJECTS are deep-merged recursively. Within the managed layer, managed-settings.json is the base and managed-settings.d/*.json are sorted alphabetically and merged on top (systemd drop-in convention). Note permissions deny is absolute across all scopes: a deny at any level cannot be re-allowed at another level.

**로딩 시점**

Loaded at session start from all applicable settings files, merged by the Claude Code harness (not the model). Claude Code watches the settings files and hot-reloads most keys into the running session on change without a restart; a few keys apply only on next restart or a specific action (model — use /model mid-session; outputStyle — rebuilt on /clear or restart). Settings values themselves are enforcement/config metadata consumed by the harness, so they are generally not injected into the model's prompt context (unlike CLAUDE.md, which IS loaded into context). A key trust nuance: because settings.local.json is the developer's own file, its permission allow rules take effect WITHOUT the workspace-trust dialog that .claude/settings.json allow rules require — but if the repo itself supplies (commits) settings.local.json, workspace trust applies again.

**컨텍스트 비용**

Negligible/near-zero token cost. Settings files are configuration/enforcement metadata read by the harness and merged at startup; their contents are not placed into the model context window (contrast with CLAUDE.md, which is always-loaded context). The one indirect effect on context is via what the settings configure (e.g. a bare-tool permission deny removes that tool's schema from context; enabling extra MCP servers or output styles adds to it) — the settings-hierarchy mechanism itself costs no tokens.

### 채택도

**채택 근거**

Core, near-universal aspect of Claude Code configuration; extensively covered by first- and third-party sources. Official starter configs in anthropics/claude-code (examples/settings). Widely explained in community guides: claudefa.st 'Settings Reference', theaiarchitects.com 'Claude Code Settings: settings.json Explained (2026)', explainx.ai 'Every Option Explained', Vincent Qiao's '5 Config Files, 1 Priority Rule', DEV Community 'Configuration Blueprint for Production Teams', egghead.io 'Organizing Personal and Project Settings', CodeSignal 'Mastering Project Settings', claudhq.com 'Should .claude Be in .gitignore?'. Real production adoption visible in public repos, e.g. GitLab's glab CLI merge request !3072 'add Claude Code project settings and gitignore local overrides'. The settings.json (shared) vs settings.local.json (personal, gitignored) split is repeatedly compared to the well-known .env / .env.local convention.

### 추천 설정

**설정 스니펫**

```
// (1) TEAM-SHARED, committed to git: <repo>/.claude/settings.json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": ["Bash(npm run test:*)", "Bash(npm run lint)"],
    "deny": ["Bash(rm -rf *)", "Read(./.env)", "Read(./secrets/**)"]
  },
  "model": "sonnet",
  "hooks": { /* project-specific gates, e.g. format-on-write */ },
  "env": { "PROJECT_ENV": "development" }
}

// (2) PERSONAL / MACHINE-LOCAL, gitignored: <repo>/.claude/settings.local.json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": ["Bash(docker:*)"],            // merges on top of project allow list
    "additionalDirectories": ["C:/Users/me/scratch"]
  },
  "env": { "LOCAL_DB_PATH": "C:/Users/me/db.sqlite" }  // machine-specific path
}

// (3) USER / GLOBAL defaults, all projects: ~/.claude/settings.json
{
  "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" },
  "permissions": { "allow": ["Bash(git status)", "Bash(git diff:*)"] }
}

// (4) Recommended .gitignore inside the repo (commit shared, exclude local):
//   .claude/settings.local.json
// (Claude Code adds this automatically when IT creates the file; add it
//  yourself if you created settings.local.json by hand.)
//
// Precedence at runtime (high->low): managed > CLI flags > settings.local.json
//   > .claude/settings.json > ~/.claude/settings.json. Scalars override,
//   arrays merge+dedupe, objects deep-merge.
```

**결정적 vs 권고적**

Deterministic / code-enforced. The merge order, scalar-override vs array-merge vs object-deep-merge rules, and the managed>local>project>user precedence are applied mechanically by the Claude Code harness — the model does not decide which layer wins. The values configured (permissions, hooks, env) are likewise harness-enforced, not advisory. Managed/enterprise settings are hard, non-overridable by design.

### 모범 사례

**모범 사례**

1) Split by ownership: put personal, cross-project defaults (status line, theme, globally-safe tool allows) in ~/.claude/settings.json; put team agreements (project command allowlist, model/effort floor, project hooks, project env) in the committed .claude/settings.json; put credentials, machine-specific paths, and personal per-project overrides in the gitignored .claude/settings.local.json. 2) Commit the shared file, exclude only the local one — a common .gitignore is a single line `.claude/settings.local.json` (or `!.claude/settings.json` + `.claude/settings.local.json` if you broadly ignore .claude). 3) Exploit array-merge: keep a baseline deny/allow list in the project file and let each developer ADD to it in settings.local.json without clobbering the team baseline. 4) Remember scalars OVERRIDE — a model or env key set locally silently replaces the project value; use this deliberately, not by accident. 5) Add `"$schema": "https://json.schemastore.org/claude-code-settings.json"` for editor autocomplete/validation. 6) Use /config (v2.1.181+ supports `/config key=value`) to edit safely; the tool writes to the appropriate layer and keeps timestamped backups (last 5). 7) Put organization-wide non-negotiables in managed-settings.json so no user/project layer can loosen them. 8) Treat the settings.json (shared) vs settings.local.json (personal) split like .env vs .env.local — it is the same mental model.

**안티패턴**

1) Committing .claude/settings.local.json — leaks personal rules/paths AND re-triggers workspace-trust suppression of its allow rules (a repo-supplied local file no longer bypasses the trust dialog). 2) Putting machine-specific absolute paths or credentials in the committed project settings.json (breaks other developers, leaks secrets). 3) Assuming everything overrides — forgetting that arrays MERGE, so a 'replacement' allow list in a lower layer is actually additive; or conversely assuming arrays merge for the few keys (e.g. fallbackModel) that don't. 4) Hand-creating settings.local.json and forgetting to gitignore it (Claude Code only auto-ignores files IT creates). 5) Trying to override a managed/enterprise setting from user/project/local — it is silently ignored. 6) Storing team-wide permission denies only in a personal user file where teammates never get them, instead of the committed project file. 7) Hand-editing JSON with trailing commas / invalid entries that break the whole file; prefer /config. 8) Expecting model/outputStyle changes to hot-reload — they need /model or a restart/clear.

**보안 리스크**

주의 (Moderate — the hierarchy itself is a safety mechanism, but misuse leaks or weakens guardrails). The layering is what lets teams enforce shared deny lists (committed project settings) and orgs enforce non-overridable managed policy — used well it INCREASES safety. Principal risks come from misplacement: (a) committing settings.local.json can expose secrets/paths and unexpectedly subject its allow rules to workspace trust; (b) putting secrets or machine paths in the shared project file leaks them to the whole team via git; (c) misunderstanding merge-vs-override can cause a local layer to silently broaden permissions. Note deny rules remain absolute across every layer, so a lower layer cannot re-enable something a higher layer denied.

### 최근 변경

**최근 변경 내역 ⚠️**

Active area through 2026 H1: (a) single-option /config edits, e.g. `/config verbose=true`, without opening the tabbed UI (v2.1.181+); (b) more tolerant parsing of invalid entries in managed settings so one bad key no longer discards the whole managed file (v2.1.169+); (c) removal of the legacy Windows managed path C:\ProgramData\ClaudeCode\ in favor of C:\Program Files\ClaudeCode\ (v2.1.75+); (d) managed-settings.d/ drop-in directory merged alphabetically over the base managed-settings.json (systemd convention); (e) workspace-trust handling of settings.local.json allow rules regressed in v2.1.196–199 and was restored so a developer-owned local file bypasses the trust dialog again in v2.1.200; (f) hot-reload of most keys into a running session on file change, with model/outputStyle still requiring restart/clear; (g) automatic timestamped backups (last 5 retained). Exact release dates for some of these are [uncertain].

**라이프사이클**

Stable and actively maintained (GA). The user/project/local/managed settings hierarchy is a foundational, non-experimental part of Claude Code. No deprecation; the model is being extended (drop-in managed dirs, granular /config, schema validation) rather than wound down.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/settings_파일_계층_userprojectlocal.json`</sub>

---

## 13. Skills

`자동화/확장`

### 기본 정보

**설정 명칭**

Skills (Agent Skills / .claude/skills/<name>/SKILL.md)

**파일 위치**

Each skill is a directory whose entrypoint is a SKILL.md file (YAML frontmatter + markdown body). Skills are discovered from four scopes: Enterprise/managed (managed-settings skills dir, org-wide), Personal ~/.claude/skills/<skill-name>/SKILL.md (all your projects), Project .claude/skills/<skill-name>/SKILL.md (this project only, discovered by walking up from cwd to the repo root AND on-demand from nested .claude/skills/ directories below cwd, e.g. packages/frontend/.claude/skills/), and Plugin <plugin>/skills/<skill-name>/SKILL.md (namespaced plugin-name:skill-name). Legacy .claude/commands/*.md files still work and share the same frontmatter (custom commands were merged into skills). .claude/skills/ inside an --add-dir / /add-dir directory is also loaded (the one config exception to additional-directories). Supporting files (reference.md, examples.md, scripts/*, templates) live alongside SKILL.md and load only when referenced. Bundled skills ship inside Claude Code itself. Skill directories can be symlinks; a <name> folder with a .claude-plugin/plugin.json loads as a skills-dir plugin (<name>@skills-dir).

**공식 문서**

Yes, extensive first-party docs. Primary: https://code.claude.com/docs/en/skills ("Extend Claude with skills"). Related official pages: https://code.claude.com/docs/en/commands (bundled skills marked "Skill"), https://code.claude.com/docs/en/settings (disableBundledSkills, skillOverrides, disableSkillShellExecution, skillListingBudgetFraction, skillListingMaxDescChars), https://code.claude.com/docs/en/sub-agents#preload-skills-into-subagents, https://code.claude.com/docs/en/permissions (Skill tool rules), https://code.claude.com/docs/en/plugins-reference#skills-directory-plugins. Cross-product/open-standard docs: https://agentskills.io, https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview and .../best-practices. Announcement blog: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills and https://claude.com/blog/skills.

**도입 버전 ⚠️**

The Agent Skills concept (SKILL.md directory format) was announced by Anthropic on 2025-10-16 and shipped as a feature preview across Claude apps; released as an open standard (agentskills.io) around December 2025. In Claude Code, skills became the unified primitive that absorbed the older custom slash-commands (.claude/commands/*.md). Many Claude-Code-specific extensions were layered on through 2026 H1: stacking of user-invocable skills in v2.1.199, ${CLAUDE_PROJECT_DIR} substitution + scheduled-task suppression in v2.1.196, nested/directory-qualified skills in v2.1.203, dedup of re-invoked identical skill content in v2.1.202, and /doctor becoming a bundled skill exempt from disableBundledSkills in v2.1.205. Exact first Claude Code build number that introduced .claude/skills/ is not pinned in the docs. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Name-collision precedence (highest to lowest): Enterprise/managed > Personal (~/.claude/skills/) > Project (.claude/skills/). A skill at any of these levels overrides a bundled skill of the same name (e.g. a project code-review skill replaces the bundled /code-review). Plugin skills live in a plugin-name:skill-name namespace so they never collide with the other levels and are managed via /plugin, not skillOverrides. Skill-vs-command: if a skill and a .claude/commands/ file share a name, the skill wins. Nested skills DON'T override: a root deploy skill and an apps/web/.claude/skills/deploy both stay available, the nested one exposed as the directory-qualified apps/web:deploy; Claude picks the variant matching the files it is editing. Unlike settings.json, skills do not deep-merge, a higher-priority same-name skill fully replaces the lower one. skillOverrides (settings) can force per-skill visibility state without editing frontmatter.

**로딩 시점**

Two-tier (progressive disclosure). At session start Claude Code loads only a LISTING of skill names + descriptions (not bodies) so the model knows what exists. The full SKILL.md body loads only when the skill is invoked, in five ways: (1) model auto-invocation, Claude reads each skill's description/when_to_use and loads it when the task matches (unless disable-model-invocation:true); (2) direct user invocation by typing /skill-name; (3) skill stacking, /a /b ... at the START of one message expands the first skill plus up to five more (v2.1.199+); (4) paths frontmatter, a skill with glob paths auto-loads only when Claude works on matching files; (5) preloaded into a subagent (skills: field) where the FULL body is injected at startup instead of just the description. disable-model-invocation:true keeps the description out of context entirely (manual /name only); user-invocable:false hides it from the / menu but leaves it model-invocable. Skill directories are hot-watched, edits/adds/removes to an EXISTING skills dir apply mid-session, but creating a brand-new top-level skills directory requires a restart.

**컨텍스트 비용**

Low standing cost by design, on-demand for bodies. Only the name+description listing is always in context; each entry's description+when_to_use is capped at 1,536 chars (skillListingMaxDescChars) and the whole listing has a budget of ~1% of the model context window (skillListingBudgetFraction, or fixed via SLASH_COMMAND_TOOL_CHAR_BUDGET). If the listing overflows, Claude Code shortens/drops descriptions starting with least-used skills (names always kept). The full body is a recurring cost only after invocation: once loaded it STAYS in context for the rest of the session (Claude does not re-read the file), so every body line is a per-turn token cost, keep bodies concise (docs suggest under 500 lines, move detail to supporting files). Re-invoking identical rendered content adds only a short "already loaded" note (v2.1.202+, previously a full re-append). Auto-compaction re-attaches the most recent invocation of each skill within a 25,000-token combined budget (first 5,000 tokens each). /context Skills row and /doctor report the listing's real cost.

### 채택도

**채택 근거 ⚠️**

Very high and cross-ecosystem. Agent Skills is an open standard (agentskills.io) adopted beyond Anthropic: Claude Code, Claude.ai, Claude API, plus OpenAI Codex, Cursor, Gemini CLI, Antigravity, and Windsurf. Large curated ecosystem on GitHub: travisvn/awesome-claude-skills, ComposioHQ/awesome-claude-skills, BehiSecc/awesome-claude-skills, daymade/claude-code-skills (marketplace), rohitg00/awesome-claude-code-toolkit (135 agents / 35 skills / 42 commands), plus the official anthropics/claude-plugins-official marketplace and the skill-creator plugin. Individual skills report large install counts (e.g. a Firecrawl skill cited at 110k+ weekly installs, web-design-guidelines skills 133k+). Anthropic ships many bundled skills in Claude Code (/doctor, /code-review, /debug, /batch, /loop, /claude-api, /run, /verify). [uncertain]

### 추천 설정

**설정 스니펫**

```
# ---- Minimal model-triggered reference skill ----
# ~/.claude/skills/api-conventions/SKILL.md  (personal) or .claude/skills/api-conventions/SKILL.md (project)
---
name: api-conventions            # optional; defaults to directory name (dir name is what you type after /)
description: API design patterns for this codebase. Use when writing or reviewing HTTP endpoints. # put key use case first; description+when_to_use capped at 1536 chars
---
When writing API endpoints:
- Use RESTful naming conventions
- Return consistent error formats
- Include request validation

# ---- Manual task skill (no auto-trigger) with pre-approved tools + args + dynamic context ----
# .claude/skills/commit/SKILL.md
---
name: commit
description: Stage and commit the current changes
disable-model-invocation: true   # only YOU can run it (/commit), keeps it out of the model's context
allowed-tools: Bash(git add *) Bash(git commit *) Bash(git status *)  # pre-approve, no per-use prompt
argument-hint: "[message]"
---
## Current changes
!`git diff HEAD`                 # dynamic context: runs before Claude sees the skill, output inlined

Commit the staged changes with message: $ARGUMENTS

# ---- Forked-subagent skill (runs in isolated context) ----
# .claude/skills/deep-research/SKILL.md
---
name: deep-research
description: Research a topic thoroughly across the codebase
context: fork                    # run in a forked subagent; SKILL.md body becomes the task prompt
agent: Explore                   # Explore | Plan | general-purpose | any custom .claude/agents/ type
paths: "src/**, packages/**"     # optional: auto-load only when editing matching files
---
Research $ARGUMENTS thoroughly: find relevant files (Glob/Grep), read code, summarize with file refs.

# ---- settings.json controls (NOT skill frontmatter) ----
{
  "disableBundledSkills": true,          // hide Anthropic's bundled skills (/doctor exempt in v2.1.205+)
  "disableSkillShellExecution": true,    // neutralize !`cmd` dynamic-context injection (managed-settings friendly)
  "skillOverrides": {                     // per-skill visibility without editing frontmatter
    "legacy-context": "name-only",       // on | name-only | user-invocable-only | off
    "deploy": "off"
  },
  "skillListingBudgetFraction": 0.02,    // raise listing budget to 2% of context window
  "permissions": { "allow": ["Skill(commit)", "Skill(review-pr *)"], "deny": ["Skill(deploy *)"] }
}
```

**결정적 vs 권고적**

Mixed. WHICH skill fires is largely advisory/model-driven: Claude auto-invokes based on the description/when_to_use text (probabilistic; strengthen wording if it under/over-triggers). Forcing is deterministic: typing /name, stacking /a /b, disable-model-invocation:true (manual only), user-invocable:false (model only), and paths globs (only auto-loads on matching files). What a skill CAN do is code-enforced: allowed-tools pre-approval, disallowed-tools removal, Skill(...) permission rules, disableBundledSkills / disableSkillShellExecution / skillOverrides settings, and the fixed cap of first-skill-plus-5 stacking are all enforced by the harness. Skill BODIES themselves are advisory instructions the model follows, not hard code, use hooks when you need deterministic enforcement of behavior.

### 모범 사례

**모범 사례**

1) Create a skill when you keep re-pasting the same checklist/procedure, or when a CLAUDE.md section has become a procedure rather than a fact, the body loads only on use, so long reference material costs almost nothing until needed. 2) Write a sharp, keyword-rich description with the key use case FIRST, it is the sole signal for auto-invocation and is truncated at 1,536 chars; add when_to_use for trigger phrases. 3) Keep the body concise (docs: under 500 lines); move large reference docs/examples/scripts into supporting files and link them from SKILL.md so they load only when needed (progressive disclosure). 4) Since an invoked body stays in context all session, write standing instructions ("when doing X, always..."), not one-time narration. 5) Use disable-model-invocation:true for side-effecting workflows (/deploy, /commit, /send-slack) so Claude never fires them on its own; use user-invocable:false for pure background knowledge. 6) Pre-approve exactly the tools a skill needs with tightly-scoped allowed-tools (e.g. Bash(git commit *)) rather than broad grants. 7) Use context:fork + agent:Explore/Plan for high-volume research so verbose work stays out of main context. 8) Use paths globs to auto-scope a skill to the files it applies to (great in monorepos, pairs with nested .claude/skills/). 9) Reference bundled scripts via ${CLAUDE_SKILL_DIR} and project files via ${CLAUDE_PROJECT_DIR} so paths resolve regardless of install scope. 10) Commit project skills to VCS for team reuse; package cross-project skills as a plugin. 11) Evaluate with the skill-creator plugin (baseline A/B with the skill disabled) rather than trusting that a trigger means it worked. 12) Manage listing budget with skillOverrides "name-only" for low-priority skills, or raise skillListingBudgetFraction.

**안티패턴**

Vague/generic descriptions (auto-invocation silently never fires, or fires on the wrong prompts). Bloated bodies stuffed with reference material, it all stays in context every turn; put detail in supporting files instead. Letting Claude auto-run destructive/side-effecting skills (deploy, commit, send-message) by forgetting disable-model-invocation:true. Assuming a skill body re-reads or re-executes each turn, it is loaded once and frozen; dynamic !`cmd` runs only at invocation time. Expecting user-invocable:false to block programmatic access (it only hides the menu, use disable-model-invocation:true or Skill(...) deny rules to actually block the Skill tool). Granting broad allowed-tools (a project skill can grant itself sweeping tool access, only takes effect after the workspace-trust dialog, review untrusted repos' skills first). Trusting a repo's .claude/skills/ with !`cmd` dynamic context or allowed-tools without review (code-execution vector; use disableSkillShellExecution in managed settings). Creating a brand-new top-level skills directory mid-session and expecting it to load without a restart. Stacking a fork-skill or /loop in the middle of /a /b, expansion stops at the first non-inline-skill token and the rest becomes argument text. Having so many skills that the listing overflows its budget and strips the keywords Claude matches on (check /doctor).

**보안 리스크**

주의 (medium/caution). Skills are both a least-privilege tool and an execution vector. Upside: allowed-tools/disallowed-tools and Skill(...) permission rules scope capability; project skill allowed-tools only activates after the workspace-trust dialog, mirroring settings.json. Downside: a malicious or careless project-committed SKILL.md can (a) grant itself broad tool pre-approval, and (b) use !`cmd` / ```! dynamic-context injection to run arbitrary shell BEFORE Claude sees anything, on every invocation. Mitigations: review untrusted repos' .claude/skills/ before trusting, set disableSkillShellExecution:true (ideally in managed settings, users can't override) to neutralize shell injection, deny the Skill tool or specific Skill(name) rules, and prefer disable-model-invocation:true for anything with side effects. Bundled and managed skills are exempt from disableSkillShellExecution.

### 최근 변경

**최근 변경 내역 ⚠️**

Active development through 2026 H1. Notable Claude Code changes: v2.1.199 - skill stacking of user-invocable skills (/code-review /fix-issue 123 loads both; first + up to 5 more), and skillOverrides "off" also hides skills from Remote Control and Agent SDK callers (not just the / menu). v2.1.196 - ${CLAUDE_PROJECT_DIR} substitution added (applies to body and allowed-tools); disable-model-invocation:true also suppresses the skill running when a scheduled task fires with it as prompt; /context Skills row now reports the budget-applied listing size. v2.1.202 - re-invoking a skill whose rendered content is identical adds a short 'already loaded' note instead of re-appending the full body. v2.1.203 - nested / directory-qualified skills (apps/web:deploy) and on-demand discovery from nested .claude/skills/ below cwd. v2.1.205 - /doctor became a bundled skill and is the one exception exempt from disableBundledSkills (hide via DISABLE_DOCTOR_COMMAND or skillOverrides doctor:off). v2.1.145 - /run, /verify, /run-skill-generator bundled skills. Broader ecosystem: custom commands merged into skills; Agent Skills open standard published (~Dec 2025) and adopted by Codex, Cursor, Gemini CLI, Antigravity, Windsurf; skill-creator plugin released for eval-driven iteration. [uncertain]

**라이프사이클**

Stable / GA and a core, first-class primitive (distinct from subagents and MCP). The SKILL.md format, scopes, frontmatter, and bundled skills are stable and actively extended. Custom slash-commands (.claude/commands/) are effectively superseded by skills but remain supported for backward compatibility (not deprecated). No part is announced deprecated; newer sub-features (nested skills, forked-context skills, skill-creator evals) are stable-but-recent.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Skills.json`</sub>

---

## 14. Plugins & Plugin Marketplaces

`자동화/확장`

### 기본 정보

**설정 명칭**

Plugins & Plugin Marketplaces (.claude-plugin/plugin.json, .claude-plugin/marketplace.json, /plugin command, claude plugin CLI)

**파일 위치**

A plugin is a self-contained directory whose only required special file is .claude-plugin/plugin.json (the manifest; even that is optional if defaults are used). All component directories live at the PLUGIN ROOT, never inside .claude-plugin/: skills/<name>/SKILL.md, commands/*.md (legacy flat skills), agents/*.md, hooks/hooks.json, .mcp.json, .lsp.json, monitors/monitors.json, output-styles/, themes/, bin/ (added to Bash PATH), settings.json (only 'agent' and 'subagentStatusLine' keys honored). A marketplace is a catalog file at .claude-plugin/marketplace.json in a repo root, listing plugins and their sources. Runtime/user-side state: enabledPlugins, pluginConfigs, extraKnownMarketplaces, strictKnownMarketplaces, blockedMarketplaces keys in ~/.claude/settings.json (user) / .claude/settings.json (project) / .claude/settings.local.json (local) / managed-settings.json (managed). Installed plugins are copied to the versioned cache ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/; marketplaces registered in ~/.claude/plugins/known_marketplaces.json; persistent plugin data at ~/.claude/plugins/data/<id>/ (${CLAUDE_PLUGIN_DATA}). Skills-directory plugins live in-place at ~/.claude/skills/<name>/.claude-plugin/plugin.json (personal) or <cwd>/.claude/skills/<name>/... (project), loaded as <name>@skills-dir.

**공식 문서**

Yes, extensive official documentation across five pages: https://code.claude.com/docs/en/plugins (create plugins), https://code.claude.com/docs/en/plugins-reference (complete technical reference: manifest schema, CLI commands, component specs), https://code.claude.com/docs/en/plugin-marketplaces (create/distribute marketplaces, marketplace.json schema), https://code.claude.com/docs/en/discover-plugins (install/discover), and https://code.claude.com/docs/en/plugin-dependencies (dependency management). Related: /en/plugin-relevance, /en/plugin-hints, /en/channels, /en/settings#plugin-settings. JSON Schema available at https://json.schemastore.org/claude-code-plugin-manifest.json.

**도입 버전 ⚠️**

The plugin system launched publicly in October 2025 (Claude Code v2.0.x era) as the packaging/distribution standard bundling skills, agents, commands, hooks, and MCP servers. Throughout 2026 H1 (v2.1.x) it gained heavy additions: displayName (v2.1.143), relevance (v2.1.152), defaultEnabled (v2.1.154), plugin monitors (v2.1.105), single-SKILL.md auto-load (v2.1.142), renames map (v2.1.193), reserved-name re-checking and LSP restartOnCrash (v2.1.205), user_config shell-substitution hardening (v2.1.207). Exact first GA version string is not pinned in current docs. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Plugins slot into the same four-scope precedence as other Claude Code config: managed > local > project > user. Install/enable scope is chosen at install time (--scope user|project|local; managed is read-only, update-only): user -> ~/.claude/settings.json enabledPlugins (default, all projects); project -> .claude/settings.json (team, version-controlled); local -> .claude/settings.local.json (gitignored); managed -> managed-settings.json (admin-enforced). Within an ENABLED plugin, components layer onto the harness like their standalone counterparts but are always NAMESPACED as <plugin-name>:<component> (e.g. /my-plugin:hello, agent my-plugin:code-reviewer) so they never collide with or override same-named project/user .claude/ definitions - the plugin copy and standalone copy both remain available. Marketplace-entry vs plugin.json merge is governed by 'strict' (default true = plugin.json is authority, marketplace entry supplements; false = marketplace entry is the whole definition and a conflicting plugin.json fails to load). version is resolved plugin.json > marketplace entry > git SHA. Managed strictKnownMarketplaces (managed settings) can lock down which marketplace sources are addable; extraKnownMarketplaces pre-registers them; container seed dir (CLAUDE_CODE_PLUGIN_SEED_DIR) overrides user config each startup.

**로딩 시점**

Enablement is at session start (via enabledPlugins/managed/seed), or interactively via /plugin, /plugin install, claude plugin install/enable, --plugin-dir (dev, session-only), or --plugin-url (fetch a hosted .zip, session-only). Once a plugin is ENABLED, each bundled component loads by ITS OWN trigger, exactly like standalone versions: skills load on-demand (model reads the description and decides, or user types /plugin:skill); agents load on-demand (auto-delegation from description, @-mention, or session --agent); hooks fire on lifecycle events (SessionStart, PreToolUse, PostToolUse, etc.) outside the model's context; MCP servers start automatically when the plugin is enabled and appear as mcp__ tools; LSP servers start on workspace trust; monitors start at session start (or on-skill-invoke) and stream stdout as notifications; bin/ executables join the Bash PATH. Live editing: /reload-plugins picks up changes to skills, agents, hooks, plugin MCP and LSP servers without restart (monitors and a brand-new component dir need a restart). --plugin-dir accepts a directory or a .zip (v2.1.128+).

**컨텍스트 비용**

Depends entirely on which components a plugin ships - the plugin wrapper itself is near-zero. Always-on cost = the listing text injected every session: each bundled skill's name+description, each agent's name+description, each command name. On-invoke cost = the full skill/agent body loaded only when it actually fires. Hooks, MCP tool schemas load per their own rules (hooks are harness-only, zero model context; MCP tool definitions are always-on once the server is enabled). `claude plugin details <name>` prints a per-component always-on vs on-invoke token estimate (computed via the count_tokens API) so you can budget before enabling. Net effect: a plugin with many verbose skill descriptions or several MCP servers has a real standing cost; a plugin that is mostly hooks or a single narrowly-described skill is cheap. Disabled plugins cost nothing.

### 채택도

**채택 근거 ⚠️**

Very high and rapidly growing ecosystem. Anthropic runs two official marketplaces: claude-plugins-official (curated, auto-registered on first interactive launch; github.com/anthropics/claude-plugins-official) and claude-community / claude-plugins-community (public community submissions after review; github.com/anthropics/claude-plugins-community). Third-party aggregators report large scale: claudemarketplaces.com lists 2,500+ marketplaces, 21,700+ skills and 12,500+ MCP servers updated daily from GitHub; a community metadata catalog tracked ~192 enabled marketplaces and ~2,529 discoverable plugins (mid-2026). Curated 'awesome' lists: Chat2AnyLLM/awesome-claude-plugins, composio-community/awesome-claude-plugins, plus GitHub topic claude-code-plugins-marketplace. Widely-cited popular plugins in 2026 include Superpowers (plan-spec-test workflow), Context7 (fresh library docs), Claude Mem (persistent memory), and Caveman (terse token-saving mode). Official LSP plugins (pyright-lsp, typescript-lsp, rust-analyzer-lsp) ship from the official marketplace. [uncertain]

### 추천 설정

**설정 스니펫**

```
// ============ 1) PLUGIN MANIFEST: my-plugin/.claude-plugin/plugin.json ============
// (only `name` is strictly required; components auto-discovered from default dirs)
{
  "name": "my-plugin",                       // kebab-case, becomes the namespace: /my-plugin:hello
  "displayName": "My Plugin",                 // v2.1.143+, UI label only
  "version": "1.2.0",                         // OMIT to use git SHA (every commit = update); SET to pin releases (bump every release!)
  "description": "Shown in the /plugin picker",
  "author": { "name": "You", "email": "you@example.com" },
  "homepage": "https://docs.example.com/my-plugin",
  "repository": "https://github.com/you/my-plugin",
  "license": "MIT",
  "keywords": ["ci", "review"],
  "defaultEnabled": true                      // v2.1.154+; false = install disabled until user opts in
  // Optional custom component paths (all relative, start with ./):
  // "skills": "./skills/", "agents": ["./agents/reviewer.md"], "hooks": "./hooks/hooks.json",
  // "mcpServers": "./.mcp.json", "lspServers": "./.lsp.json",
  // "userConfig": { "api_token": { "type": "string", "title": "Token", "description": "...", "sensitive": true } },
  // "dependencies": [ { "name": "secrets-vault", "version": "~2.1.0" } ]
}

// Directory layout (EVERYTHING except plugin.json at the plugin ROOT):
// my-plugin/
//   .claude-plugin/plugin.json     <- ONLY the manifest goes here
//   skills/<name>/SKILL.md         <- model-invoked skills (namespaced /my-plugin:<name>)
//   agents/*.md                    <- subagents (hooks/mcpServers/permissionMode fields ignored for security)
//   hooks/hooks.json               <- event handlers; use ${CLAUDE_PLUGIN_ROOT} for script paths
//   .mcp.json                      <- bundled MCP servers (start when enabled)
//   .lsp.json                      <- LSP servers (binary must be on user's PATH)
//   monitors/monitors.json         <- background watchers (v2.1.105+)
//   bin/                           <- executables added to Bash PATH
//   settings.json                  <- only `agent` + `subagentStatusLine` honored

// ============ 2) MARKETPLACE CATALOG: .claude-plugin/marketplace.json ============
{
  "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
  "name": "acme-tools",                        // kebab-case, public-facing, one per user
  "owner": { "name": "DevTools Team", "email": "devtools@example.com" },
  "metadata": { "pluginRoot": "./plugins" },  // optional base dir for relative sources
  "plugins": [
    { "name": "code-formatter", "source": "./plugins/formatter",
      "description": "Format on save", "version": "2.1.0", "category": "productivity" },
    { "name": "deploy-tools",
      "source": { "source": "github", "repo": "acme/deploy-plugin", "ref": "v2.0.0" } }
  ],
  "renames": { "formatter": "code-formatter", "legacy-linter": null }  // v2.1.193+ migration map
}
// Plugin source types: "./rel-path" | {source:github, repo, ref?, sha?} | {source:url, url, ref?, sha?}
//   | {source:git-subdir, url, path, ref?, sha?} | {source:npm, package, version?, registry?}

// ============ 3) TEAM AUTO-PROVISION: .claude/settings.json ============
{
  "extraKnownMarketplaces": {
    "acme-tools": { "source": { "source": "github", "repo": "acme/claude-plugins" } }
  },
  "enabledPlugins": {
    "code-formatter@acme-tools": true,
    "deploy-tools@acme-tools": true
  }
}

// ============ 4) CLI / SLASH COMMANDS ============
// claude plugin init my-tool [--with skills agents hooks mcp lsp]   # scaffold @skills-dir plugin
// claude plugin validate ./my-plugin [--strict]                     # validate before publish
// claude plugin marketplace add acme/claude-plugins[@ref] [--scope project]
// claude plugin marketplace update|list|remove <name>
// claude plugin install code-formatter@acme-tools [--scope project]
// claude plugin enable|disable|update|uninstall|details|list <plugin>
// In-session equivalents: /plugin , /plugin marketplace add ./my-marketplace , /plugin install x@mkt , /reload-plugins
// Dev/test: claude --plugin-dir ./my-plugin   (or ./my-plugin.zip, v2.1.128+)   |   claude --plugin-url https://.../plugin.zip
```

**결정적 vs 권고적**

Split by layer. The packaging, distribution, install/enable resolution, version/cache keying, scope precedence, strict-mode merge, source pinning (ref/sha), reserved-name blocking, and strictKnownMarketplaces allowlisting are all DETERMINISTIC, code-enforced by the harness. What each bundled component does inherits its own character: hooks and MCP/LSP servers are deterministic; skill and agent SELECTION is advisory/model-driven (Claude reads descriptions and decides), while a skill/agent's tool allowlist and permissionMode remain code-enforced. So: 'is this plugin enabled and where does its code come from' is deterministic; 'will a given skill fire this turn' is advisory.

### 모범 사례

**모범 사례**

1) Start standalone in .claude/ for fast iteration, convert to a plugin only when you need to SHARE, version, or reuse across projects. 2) Use the skills/ directory layout (not legacy flat commands/) for new plugins; a single-skill plugin can put SKILL.md at the root (v2.1.142+) but set a frontmatter `name` so the invocation name is stable across updates. 3) Version strategy: OMIT `version` for internal/fast-moving plugins (git SHA = every commit is an update); SET explicit semver and bump it every release for published plugins - a stale pinned version silently blocks updates. Never set version in BOTH plugin.json and the marketplace entry (plugin.json always wins, masking the other). 4) Always reference bundled files with ${CLAUDE_PLUGIN_ROOT} (never absolute or ../ paths - plugins are copied to a cache); store durable state (node_modules, venvs, caches) in ${CLAUDE_PLUGIN_DATA} which survives updates. 5) Keep components at the plugin root, only plugin.json inside .claude-plugin/. 6) Run `claude plugin validate --strict` in CI before publishing; check `claude plugin details` to see token cost. 7) Host marketplaces on GitHub and add via owner/repo shorthand; use git-subdir for monorepos; pin plugin sources with sha for reproducibility. 8) Use `renames` (v2.1.193+) instead of ever changing a plugin `name`, and treat it as append-only history. 9) Use displayName for UI relabeling without breaking installs. 10) For teams, ship extraKnownMarketplaces + enabledPlugins at project scope; for orgs, lock sources with strictKnownMarketplaces (managed) and consider CLAUDE_CODE_PLUGIN_SEED_DIR for containers/CI. 11) Use defaultEnabled:false for plugins that add cost or connect to external services. 12) Set sensitive userConfig values (never hardcode secrets); they store in keychain, not settings.json.

**안티패턴**

Putting commands/agents/skills/hooks INSIDE .claude-plugin/ (only plugin.json belongs there - components then silently don't load). Referencing files with ../ or absolute paths (broken after cache copy). Setting `version` and never bumping it (users never receive your new commits; /plugin update says 'already latest'). Declaring `version` in both plugin.json and marketplace entry (plugin.json wins, marketplace value silently ignored). Writing durable state into ${CLAUDE_PLUGIN_ROOT} (wiped ~7 days after an update). Renaming a plugin's `name` field without a `renames` entry (breaks every existing install with plugin-not-found). Distributing a marketplace by direct URL to marketplace.json while using relative-path plugin sources (only the JSON is downloaded; use github/npm/git sources instead). Expecting plugin agents to use hooks/mcpServers/permissionMode frontmatter (ignored for security on plugin-shipped agents). Trying to name a third-party marketplace with a reserved name (claude-plugins-official, anthropic-plugins, etc. are blocked). Assuming a plugin's CLAUDE.md loads as context (it does not - ship instructions via a skill). Relative ${user_config.*} inside shell-form hook or monitor commands (rejected since v2.1.207 - use exec form or read the env var).

**보안 리스크**

주의 (medium/caution), rising toward 위험 for untrusted sources. Plugins bundle executable code that runs on your machine: hooks, MCP servers, LSP servers, monitors, and bin/ executables all execute with your privileges. Installing a plugin from an untrusted marketplace is equivalent to running untrusted code - review before enabling. Mitigations built in: marketplace plugins are copied to an isolated cache (no in-place execution, path traversal outside the plugin root is blocked, external symlinks are skipped); plugin-shipped agents have hooks/mcpServers/permissionMode disabled; project-scope @skills-dir plugins require the workspace trust gate and their MCP servers still need per-server approval; reserved/official marketplace names cannot be impersonated. Org controls: strictKnownMarketplaces (managed settings) allowlists or fully locks down addable sources; blockedMarketplaces blocks specific ones; disableSideloadFlags rejects --plugin-dir/--agents/--mcp-config for a run; enforcement runs on add AND on every install/update/refresh. Private-repo auto-updates and token-in-URL rewrites store credentials in plaintext gitconfig - scope them to the marketplace repo and use read-only tokens.

### 최근 변경

**최근 변경 내역 ⚠️**

Continuous heavy development through 2026 H1 (v2.1.x). Selected: v2.1.105 plugin background monitors; v2.1.121 `claude plugin prune`/autoremove for orphaned dependencies; v2.1.128 --plugin-dir accepts .zip archives; v2.1.140 warns when a default folder and manifest key both exist; v2.1.142 single root SKILL.md auto-loads as a one-skill plugin; v2.1.143 displayName; v2.1.152 relevance (org plugin recommendation); v2.1.154 defaultEnabled; v2.1.193 marketplace `renames` map for safe rename/removal migration; v2.1.196 marketplace-add rejects schemeless URLs, validator improvements; v2.1.205 reserved marketplace names re-checked every load (first-party-plugins & healthcare newly reserved), LSP restartOnCrash/shutdownTimeout honored; v2.1.207 ${user_config.*} no longer substituted into shell command strings (security), pluginConfigs read/written only from user/managed/--settings scopes. Anthropic operates claude-plugins-official (curated) and claude-plugins-community (public submissions via clau.de/plugin-directory-submission or platform.claude.com/plugins/submit). --plugin-url and container seeding (CLAUDE_CODE_PLUGIN_SEED_DIR) added for CI/airgapped use. [uncertain: exact version-to-date mapping]

**라이프사이클**

Stable and GA, and the officially recommended standard for distributing skills+agents+commands+hooks+MCP as a versioned unit. Core surface (plugin.json, marketplace.json, /plugin, claude plugin CLI, sources, scopes, install/enable) is stable and under active expansion. A few components are explicitly EXPERIMENTAL and may change schema/location: themes and monitors (declared under the `experimental` manifest key - top-level still works but validate warns and a future release will require experimental.*). Channels, LSP plugins, plugin dependencies, and relevance/hints are newer but shipping. Nothing is deprecated; the legacy flat commands/ layout is de-emphasized ('use skills/ for new plugins') but still fully supported.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Plugins_Plugin_Marketplaces.json`</sub>

---

## 15. Auto Mode & 권한 분류기

`권한/보안`

### 기본 정보

**설정 명칭**

Auto mode (permission mode `auto`) and its safety classifier, configured via the `autoMode` settings block (environment, allow, soft_deny, hard_deny, classifyAllShell) and gated by the managed `permissions.disableAutoMode` control. Auto mode is a middle ground between Manual approval (config value `default`, per-action prompts) and `bypassPermissions` / `--dangerously-skip-permissions` (no checks at all): Claude runs without routine prompts while a separate server-side classifier model reviews each risky action first.

**파일 위치**

The `autoMode` block is read ONLY from ~/.claude/settings.json (user scope), managed/enterprise settings (managed-settings.json), and inline JSON via the --settings flag or Agent SDK. It is deliberately NOT read from project files .claude/settings.json or .claude/settings.local.json so a checked-in repo or build step cannot inject its own trust/allow rules (before v2.1.207 it also read settings.local.json; that was removed). The `permissions.disableAutoMode` kill-switch lives in managed settings only. `permissions.defaultMode: "auto"` to start in auto mode by default is honored only from ~/.claude/settings.json or managed settings, ignored in project/local files (since v2.1.142). The classifier additionally reads the same CLAUDE.md content Claude loads. Enable interactively via Shift+Tab cycle, `--permission-mode auto`, or the VS Code / Desktop / claude.ai mode selector.

**공식 문서**

Officially documented across two dedicated pages plus supporting material. Primary: https://code.claude.com/docs/en/auto-mode-config (Configure auto mode - the autoMode settings reference) and https://code.claude.com/docs/en/permission-modes#eliminate-prompts-with-auto-mode (what auto mode is, requirements, default block/allow lists). Engineering deep dive: https://www.anthropic.com/engineering/claude-code-auto-mode. Announcement: https://claude.com/blog/auto-mode. Related: https://code.claude.com/docs/en/permissions (managed disableAutoMode), https://code.claude.com/docs/en/server-managed-settings.

**도입 버전 ⚠️**

Auto mode: v2.1.158 (2026-05-30), initially expanding to Amazon Bedrock, Google Cloud Agent Platform (Vertex), and Microsoft Foundry behind CLAUDE_CODE_ENABLE_AUTO_MODE=1. `autoMode.classifyAllShell`: v2.1.193 (earlier versions silently ignore the key). The `default` permission mode was relabeled `Manual` in the CLI/VS Code/JetBrains/Desktop with `manual` accepted as an alias in v2.1.200 (2026-07-03); the config value stays `default`. Subagent task-description pre-check added v2.1.178. The CLAUDE_CODE_ENABLE_AUTO_MODE=1 opt-in requirement was removed in v2.1.207 (auto mode now on by default across all supported providers). [uncertain] exact original GA date of the classifier itself before the Bedrock/Vertex/Foundry rollout.

### 스코프 / 로딩

**우선순위 계층**

Two independent controls with different precedence. (1) `permissions.disableAutoMode: "disable"` in managed settings is an absolute org-level kill switch: it removes `auto` from the Shift+Tab cycle and rejects `--permission-mode auto` at startup, and users cannot override it. On Team/Enterprise an Owner must also enable auto mode in Claude Code admin settings before anyone can use it. (2) The `autoMode` block (environment/allow/soft_deny/hard_deny/classifyAllShell) merges ADDITIVELY across user (~/.claude/settings.json), managed settings, and inline --settings, but NOT project scope. A developer can extend environment/allow/soft_deny/hard_deny with personal entries but cannot remove managed entries. Crucially this is additive, not a hard policy boundary: because allow rules act as exceptions to soft_deny inside the classifier, a developer-added `allow` can override an organization `soft_deny`. For a non-overridable boundary use managed `permissions.deny` (evaluated BEFORE the classifier) or `autoMode.hard_deny` (unconditional inside the classifier). Setting any autoMode list WITHOUT the literal "$defaults" string replaces the entire built-in list for that section.

**로딩 시점**

The classifier is a SECOND gate that runs after the deterministic permissions system, per tool call, but only for actions that reach it. Decision order (first match wins): (1) allow/ask/deny rules resolve immediately (except protected-path writes, which route to the classifier); (2) read-only actions and working-directory file edits are auto-approved and skip the classifier; (3) everything else (shell commands, network calls, destructive/external ops) goes to the classifier. On entering auto mode, broad arbitrary-code-execution allow rules (Bash(*), PowerShell(*), wildcarded interpreters like Bash(python*), package-manager run commands, Agent allow rules) are DROPPED and restored on exit; narrow rules like Bash(npm test) carry over (unless autoMode.classifyAllShell:true suspends those too). The classifier is a server-side model (Opus 4.6+/Sonnet 4.6+ on the Anthropic API; Sonnet 5 / Opus 4.7 / Opus 4.8 on Bedrock/Vertex/Foundry) independent of your /model choice. It sees user messages, Claude's tool CALLS, and CLAUDE.md, but tool RESULTS and Claude's own reasoning messages are stripped out (reasoning-blind by design) so hostile file/web content cannot manipulate it. A separate server-side prompt-injection probe scans incoming tool results before Claude reads them.

**컨텍스트 비용**

Not a static context cost but a per-action latency + token cost. Each classifier check sends a portion of the transcript plus the pending action to a separate server-side model, adding a network round-trip before the action executes, and those calls count toward token usage. Reads and in-working-directory edits skip the classifier, so overhead concentrates on shell and network operations. `classifyAllShell:true` increases this: every Bash/PowerShell command becomes a classifier call instead of resolving instantly against an allow rule (trades latency for coverage). As of v2.1.198 a sandbox-network verdict for a host:port is cached and reused instead of re-classified on every connection.

### 채택도

**채택 근거**

Heavily covered flagship 2026 feature. Anthropic published a dedicated engineering deep dive (anthropic.com/engineering/claude-code-auto-mode) and product blog (claude.com/blog/auto-mode). Extensive third-party writeups: AgentPatterns.ai (Classifier-Based Permission Gating), Sébastien Dubois (dsebastien.net), zenvanriel.com, developersdigest.tech, MindStudio, buildfastwithai.com (2026 guide), claudecodeai.blog, Stackademic/Medium explainers. Community best-practice repos reference the settings (github.com/shanraisshan/claude-code-best-practice, github.com/luongnv89/claude-howto). Tracked by ClaudeCodeLog on X and multiple changelog aggregators (releasebot.io, gradually.ai, claudefa.st). News coverage of the v2.1.200 Manual rename and the v2.1.207 default-on rollout (techtimes.com, startdebugging.net) indicates broad real-world attention.

### 추천 설정

**설정 스니펫**

```
// ~/.claude/settings.json (USER scope) or managed settings. NOT project settings.
{
  "permissions": {
    "defaultMode": "auto",              // start in auto mode (user/managed only)
    "ask": [                             // content-scoped ask rules ALWAYS prompt,
      "Bash(git push *)",                //   even in auto mode -> human checkpoint
      "Bash(gh pr create *)"
    ],
    "deny": [                            // deny is absolute, runs BEFORE the classifier
      "Bash(git push --force*)"
    ]
  },
  "autoMode": {
    "classifyAllShell": true,            // v2.1.193+: route EVERY shell cmd through
                                          //   the classifier, suspending narrow allow
                                          //   rules while auto mode is active
    "environment": [                     // trusted infrastructure (prose, not regex)
      "$defaults",                       // keep built-in defaults, splice yours in
      "Organization: Acme Corp. Primary use: software development",
      "Source control: github.example.com/acme-corp and all repos under it",
      "Trusted cloud buckets: s3://acme-build-artifacts, gs://acme-ml-datasets",
      "Trusted internal domains: *.corp.example.com, api.internal.example.com",
      "Key internal services: Jenkins at ci.example.com, Artifactory at artifacts.example.com",
      "Internal package registry: artifacts.example.com/npm"
    ],
    "allow": [                           // exceptions to soft_deny (user intent-like)
      "$defaults",
      "Deploying to the staging namespace is allowed: staging is isolated and resets nightly"
    ],
    "soft_deny": [                        // destructive; user intent/allow can clear
      "$defaults",
      "Never run database migrations outside the migrations CLI, even against dev DBs"
    ],
    "hard_deny": [                        // unconditional; intent & allow do NOT apply
      "$defaults",
      "Never send repository contents to third-party code-review APIs"
    ]
  }
}

// Managed settings ONLY - org kill switch (users cannot override):
// { "permissions": { "disableAutoMode": "disable" } }

// Inspect / validate your effective config:
//   claude auto-mode defaults   # print built-in environment/allow/soft_deny/hard_deny
//   claude auto-mode config     # print effective config with $defaults expanded
//   claude auto-mode critique   # AI review of your custom rules for ambiguity/false positives
//
// WARNING: any autoMode list set WITHOUT "$defaults" replaces the ENTIRE built-in list
// for that section (e.g. a soft_deny without $defaults discards force-push, curl|bash,
// and prod-deploy protections; a hard_deny without $defaults discards data-exfiltration
// and auto-mode-bypass rules).
```

**결정적 vs 권고적**

Hybrid, and this is the defining characteristic. The GATE is deterministic/code-enforced (the harness decides which actions skip vs. reach the classifier, and permissions.deny / ask / disableAutoMode are hard rules applied before or around it), but the classifier's verdict itself is PROBABILISTIC - a natural-language AI model reading prose environment/allow/deny rules, not string patterns. The published two-stage design has measurable error rates: a fast stage-1 filter (~8.5% false positive, ~6.6% false negative) followed by chain-of-thought stage-2 that cuts false positives to ~0.4% but accepts ~17% false negatives on genuinely dangerous actions. So autoMode.* entries are advisory guidance to a model, whereas the surrounding permissions.deny/ask rules and disableAutoMode are deterministic. Do NOT treat the classifier as a hard security boundary.

### 모범 사례

**모범 사례**

1) Use auto mode as the intended middle ground - reach for it instead of `--dangerously-skip-permissions`/bypassPermissions whenever you want fewer prompts but still want guardrails; reserve bypass for truly isolated containers/VMs. 2) Invest in `autoMode.environment` first - it resolves most false positives. Start with `$defaults` + your source-control org + key internal services, then add trusted domains/buckets, filling sensitivity slots (sensitive data locations, sensitive remote targets, protected IaC scopes) as blocks arise. Write entries as prose you'd tell a new engineer, not regex. 3) ALWAYS keep the literal `"$defaults"` in every autoMode list unless you deliberately intend to own the whole list (then copy `claude auto-mode defaults` output and edit). 4) For hard, non-overridable boundaries use managed `permissions.deny` (runs before the classifier) or `autoMode.hard_deny`, NOT soft_deny (which a developer allow can override). 5) Add `permissions.ask` content-scoped rules (e.g. Bash(git push *), Bash(gh pr create *)) for human checkpoints that persist even in auto mode. 6) Enable `classifyAllShell:true` when you want narrow allow rules to also be re-examined (defense against a destructive argument slipping past a prefix rule), accepting the added latency. 7) Validate before rollout with `claude auto-mode config` (effective rules) and `claude auto-mode critique` (AI review of custom rules). 8) Distribute org trust config and the disableAutoMode / Owner-enable controls via managed settings. 9) Use the Recently-denied tab and per-denial reasons (v2.1.193+) to decide whether the fix is an environment entry, an allow exception, or retrying with explicit intent; state boundaries explicitly in conversation ("don't push until I review") for one-off blocks, but back them with a deny rule for durability since compaction can drop them.

**안티패턴**

1) Treating auto mode / the classifier as a hard security boundary - it is a probabilistic model with a documented ~17% false-negative rate on dangerous actions; pair it with permissions.deny and sandboxing. 2) Setting an `autoMode` list without `"$defaults"`, silently discarding built-in protections (force-push, curl|bash, prod deploy, data-exfiltration, bypass rules). 3) Relying on `soft_deny` for a boundary that must not be crossed - a developer-added allow (or explicit user intent) overrides it; use hard_deny or managed permissions.deny. 4) Putting the `autoMode` block or `defaultMode: "auto"` in project `.claude/settings.json`/`settings.local.json` - it is ignored there by design; only user/managed/inline scopes are read. 5) Leaving auto mode enabled on the desktop app or other non-isolated environments without org review; on Team/Enterprise forgetting the Owner must enable it. 6) Assuming the classifier can read command OUTPUT - it is reasoning/output-blind, so e.g. `rm -rf "$VAR"` where VAR came only from earlier output is blocked because the target can't be verified; fix by naming the literal path. 7) Over-broad allow entries that re-open exfiltration paths. 8) Expecting narrow shell allow rules to be inspected without setting classifyAllShell:true (a destructive arg the prefix didn't anticipate can pass). 9) Stating a boundary only in chat and assuming it survives context compaction.

**보안 리스크**

주의 (moderate - a net security IMPROVEMENT but not a guarantee). Auto mode is explicitly designed as the safer alternative to --dangerously-skip-permissions: it blocks irreversible/destructive/exfiltration/prompt-injection-driven actions by default (curl|bash, force push, prod deploys/migrations, mass cloud deletion, IAM grants, secret exfiltration, sending sensitive data off-boundary, etc.) via a reasoning-blind classifier plus an input-side injection probe. However Anthropic themselves warn it 'reduces permission prompts but does not guarantee safety' - the classifier is probabilistic (~17% false negatives on genuinely dangerous actions at the low-false-positive setting) and the autoMode config merge is additive rather than a hard policy boundary. Treat it as a strong first line, not the last line: back it with managed permissions.deny for non-negotiables, sandboxing for OS-level enforcement, and disableAutoMode where org policy forbids it. Far safer than bypassPermissions (which offers zero protection), but riskier than staying in Manual mode for genuinely high-stakes infrastructure work.

### 최근 변경

**최근 변경 내역**

Very active area through 2026 H1-H2. v2.1.158 (2026-05-30): auto mode expanded to Bedrock/Vertex/Foundry behind CLAUDE_CODE_ENABLE_AUTO_MODE=1. v2.1.178: subagent task-description evaluated at spawn time (previously only during/after). v2.1.182/198: more git-history-destroying commands blocked (reset --hard, checkout -- ., clean -fd, stash drop/clear; amend of already-pushed commits). v2.1.193: `autoMode.classifyAllShell` added; per-denial reasons surfaced in transcript, denial notifications, and the Recently-denied tab. v2.1.195: many new default block categories (secret managers, DNS/TLS, unapproved PR merges, prod feature flags, protected IaC, cluster-wide writes, sensitive-target shells/port-forwards, internal-registry bypass, --insecure flags, autonomous agent loops) plus new environment slots (internal package registry, sensitive data locations, sensitive remote targets, protected IaC scopes). v2.1.198: verdict caching for network host:port; more outbound-content and registry-bypass rules. v2.1.199: MCP tools with requiresUserInteraction skip the classifier and prompt directly. v2.1.200: `default` mode relabeled `Manual` with `manual` alias (2026-07-03); repo visibility inferred from transcript evidence; more PR/issue/commit exfiltration rules; mid-session remotes no longer trusted. v2.1.203: routine pushes to default branch now allowed (previously all blocked); private/public repo scoping of confidential vs personal data refined. v2.1.205: blocks writes to session transcripts and unresolved recursive-force-delete of shell variables. v2.1.207 (~2026-07): removed CLAUDE_CODE_ENABLE_AUTO_MODE=1 requirement (auto mode on by default across all supported providers) and stopped reading autoMode from .claude/settings.local.json.

**라이프사이클**

Stable / generally available and rapidly iterating. Rolled out to all plans and all supported providers (Anthropic API, Bedrock, Vertex/Agent Platform, Foundry, Claude apps gateway) with the opt-in env var removed in v2.1.207. Not experimental and not deprecated; the default block/allow rule set and environment slots are being actively expanded release-over-release rather than wound down. Gated by model support (Opus 4.6+/Sonnet 4.6+ on the API; Sonnet 5/Opus 4.7/Opus 4.8 on other providers) and, on Team/Enterprise, by Owner enablement.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Auto_Mode_권한_분류기.json`</sub>

---

## 16. Rules (경로 스코프 규칙)

`메모리/문서`

### 기본 정보

**설정 명칭**

Rules (`.claude/rules/` path-scoped rule files). Not a settings.json key: a directory of markdown files, each optionally carrying a `paths` YAML frontmatter field. Related settings keys that govern them are `claudeMdExcludes` and the `--setting-sources` CLI flag.

**파일 위치**

Project rules: `.claude/rules/**/*.md` (all `.md` files discovered recursively, so `frontend/`, `backend/` subdirectories work). User rules: `~/.claude/rules/**/*.md`, applied to every project on the machine. Symlinks are supported and resolved normally in `.claude/rules/` (both a linked directory and a linked individual file); circular symlinks are detected and handled. With `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`, `.claude/rules/*.md` is also loaded from directories passed via `--add-dir`. There is no managed-policy rules directory; the organization-wide equivalent is a managed CLAUDE.md at `/etc/claude-code/CLAUDE.md` (Linux/WSL), `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows), or the `claudeMd` key in managed-settings.json.

**공식 문서**

Yes. Documented on the memory page: https://code.claude.com/docs/en/memory under 'Organize rules with `.claude/rules/`' and its 'Path-specific rules' subsection. Related official pages: https://code.claude.com/docs/en/large-codebases (monorepo layout of root and per-directory rules), https://code.claude.com/docs/en/hooks#instructionsloaded (the `InstructionsLoaded` hook, explicitly recommended for debugging path-specific rules), and the Anthropic blog post 'Steering Claude Code: when to use CLAUDE.md, skills, hooks, and subagents' at https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more. Note that community bug reports document a documentation/implementation mismatch on the frontmatter key name (see anti_patterns).

**도입 버전 ⚠️**

Community changelog trackers place the `.claude/rules/` directory at v2.0.64 [uncertain]. The mechanism was clearly established well before 2026; the official docs do not state an introduction version. Dated refinements that ARE version-stamped in the docs: v2.1.198 (symlinked-path matching), v2.1.207 (invalid bracket patterns match nothing instead of breaking the Read tool), v2.1.211 (on-demand rules respect `--setting-sources` exclusion), v2.1.217 (brace-expansion budget no longer stalls the CLI at startup). [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Rules are a memory/context layer, not a permission layer, so they do not participate in the managed > local > project > user settings precedence chain. Their own ordering is: user-level rules (`~/.claude/rules/`) load BEFORE project rules (`.claude/rules/`), which gives project rules the higher effective priority because later content is read last. A rule file WITHOUT a `paths` field is loaded at launch with the same priority as `.claude/CLAUDE.md`. All discovered instruction files are concatenated into context rather than overriding one another, so two contradicting rules leave Claude to pick one arbitrarily — there is no conflict resolution. Project rules are skipped when `project` is excluded from `--setting-sources` (before v2.1.211, on-demand rules leaked through that exclusion). Individual rule files or whole rules directories can be suppressed with the `claudeMdExcludes` setting, which accepts absolute-path glob patterns and merges its arrays across every settings layer (user, project, local, managed). Managed-policy CLAUDE.md cannot be excluded this way.

**로딩 시점**

Two distinct modes in one directory. (1) No `paths` frontmatter: loaded unconditionally at session start, identical in behavior to `.claude/CLAUDE.md`. (2) With `paths` frontmatter: loaded on demand, triggered when Claude READS a file matching one of the globs — not on every tool use, and notably not on Write/create of a matching file that does not yet exist. Matching also works through symlinked paths into the project directory as of v2.1.198. After `/compact`, project-root CLAUDE.md is re-read from disk and re-injected, but path-scoped rules are NOT re-injected; they reload only the next time Claude reads a file matching their patterns. Use the `InstructionsLoaded` hook to log exactly which instruction files loaded, when, and why.

**컨텍스트 비용**

This is the entire point of the primitive. Unconditional rules cost the same as CLAUDE.md — always resident in the context window, paid on every session. Path-scoped rules cost nothing until a matching file is read, which is why the docs recommend them as the fix for a CLAUDE.md that has outgrown the ~200-line target. Contrast with `@path` imports, which are expanded into context at launch and therefore do NOT reduce context cost — they only improve file organization. For instructions that should not be resident even when working in a matching area, skills are the cheaper primitive, since they load only on invocation or model-judged relevance.

### 채택도

**채택 근거 ⚠️**

Moderate and growing, but visibly less adopted than CLAUDE.md itself — commonly framed in the community as an overlooked feature (e.g. the French write-up 'Rules Claude Code : la feature que tout le monde a oubliee'). Evidence: a dedicated Anthropic blog post steering users from CLAUDE.md toward rules/skills/hooks; recurring practitioner posts including 'Claude Rules vs CLAUDE.md: Pattern-Scoped Conventions Your Team Is Missing' (groff.dev), 'Your CLAUDE.md Is Doing Too Much' (Medium), claudefa.st's 'Claude Code Rules Directory: Modular Instructions That Scale', ClaudeLog's rules FAQ entry, and konadu.dev's 'How Claude Code Loads .claude/rules'. A useful secondary adoption signal is the steady stream of specific, well-written GitHub bug reports against path-scoped loading (anthropics/claude-code issues #16299, #16853, #17204, #21858, #23478) — users are exercising the feature hard enough to find edge cases. Cursor's `.cursor/rules` is the direct analogue that primed the market for this pattern, and `/init` reads Cursor rules when generating a CLAUDE.md. [uncertain]

### 추천 설정

**설정 스니펫**

```
Directory layout:

your-project/
|-- .claude/
|   |-- CLAUDE.md            # small, always-loaded core
|   `-- rules/
|       |-- code-style.md    # no frontmatter -> always loaded
|       |-- api.md           # paths: -> loads only for API files
|       |-- frontend/
|       |   `-- react.md
|       `-- testing.md

Path-scoped rule, .claude/rules/api.md:

---
paths:
  - "src/api/**/*.ts"
  - "src/**/*.{ts,tsx}"
  - "tests/**/*.test.ts"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments

Always-loaded rule (omit frontmatter entirely), .claude/rules/code-style.md:

# Code Style

- 2-space indentation, no tabs
- Run `npm test` before committing

Share one ruleset across repos with symlinks:

    ln -s ~/shared-claude-rules .claude/rules/shared
    ln -s ~/company-standards/security.md .claude/rules/security.md

Suppress other teams' rules in a monorepo, .claude/settings.local.json:

{
  "claudeMdExcludes": [
    "**/monorepo/CLAUDE.md",
    "/home/user/monorepo/other-team/.claude/rules/**"
  ]
}

Debug which instruction files actually loaded, .claude/settings.json:

{
  "hooks": {
    "InstructionsLoaded": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.instructionFiles[]?' >> /tmp/claude-instructions.log"
          }
        ]
      }
    ]
  }
}

Verify at runtime with `/context` (Memory files section) and `/memory`.
```

**결정적 vs 권고적**

Purely advisory. Rules are delivered as context, not enforced configuration — the docs state plainly that Claude 'treats them as context, not enforced configuration' and that there is no guarantee of strict compliance. What IS deterministic is the loading mechanism: whether a rule enters the context window is decided by glob matching in code, not by model judgment (unlike skills, where the model reads the description and decides). So: deterministic delivery, advisory content. To make an instruction binding, express it as a PreToolUse hook instead.

### 모범 사례

**모범 사례**

1) Treat rules as the pressure valve for CLAUDE.md. The docs target under 200 lines per CLAUDE.md; when you exceed it, move anything that only matters for part of the tree into a path-scoped rule rather than splitting into `@path` imports, which do not reduce context.
2) One topic per file with a descriptive filename (`testing.md`, `api-design.md`). This is what makes the directory reviewable by a team and diffable in PRs.
3) Scope aggressively. Any rule whose advice is meaningless outside a subtree should carry `paths`. Reserve the always-loaded (no-frontmatter) form for genuinely global conventions.
4) Use brace expansion to keep pattern lists short — `src/**/*.{ts,tsx}` — but stay well inside the budget of 1,000 expanded patterns / 4 MiB per rule. Each brace group multiplies: `{a,b}/{c,d}/*.{ts,tsx}` is already 8 patterns. Patterns without braces do not count against the budget.
5) Escape literal brackets in paths (`photos \[2024/**`); a `[` that cannot be parsed as a bracket expression makes that pattern match nothing.
6) Symlink a company-standard ruleset into every repo instead of copy-pasting it, so one edit propagates.
7) Put personal preferences in `~/.claude/rules/` and team standards in `.claude/rules/`, and rely on project rules loading last (and thus winning) when they disagree.
8) Audit periodically. Contradicting rules across CLAUDE.md, nested CLAUDE.md files, and `.claude/rules/` are resolved arbitrarily, so stale rules actively degrade adherence rather than being harmless.
9) Verify with `/context` and the `InstructionsLoaded` hook rather than assuming a rule loaded — path-scoped loading is the single most bug-reported part of this feature.
10) In monorepos, pair rules with `claudeMdExcludes` in `.claude/settings.local.json` so other teams' instructions do not bleed into your sessions.

**안티패턴**

1) Writing `globs:` instead of `paths:` (or vice versa) — the documented key is `paths`, but issue #17204 reports the undocumented `globs` working more reliably in several configurations. Verify with `/context` instead of trusting either.
2) Expecting a path-scoped rule to fire when Claude CREATES a file. Loading triggers on Read; issue #23478 documents that Write/create does not inject the rule. New-file conventions belong in an always-loaded rule.
3) Putting `paths:` frontmatter in `~/.claude/rules/` and assuming it scopes — issue #21858 reports user-level path frontmatter being ignored.
4) Expecting rules to survive `/compact`. Path-scoped rules are not re-injected after compaction; only project-root CLAUDE.md is. A long session can silently drift once compaction drops them.
5) Using rules to enforce anything security-relevant. They are advisory context; a model can be talked out of them. Use `permissions.deny` or a PreToolUse hook.
6) Dumping a former 800-line CLAUDE.md into one giant unconditional rule file. That relocates the file without reducing a single token of context cost.
7) Using rules for multi-step procedures. The docs route those to skills, which load on demand rather than sitting resident whenever a matching file is touched.
8) Unbounded brace expansion. Before v2.1.217 a `paths` list with many brace groups could stall or crash the CLI at startup; now oversized patterns are used unexpanded and their literal braces match nothing — the rule silently never fires.
9) Letting rules and CLAUDE.md contradict each other and assuming the more specific one wins. It does not; the choice is arbitrary.

**보안 리스크**

SAFE (안전), with one caveat. Rules cannot grant permissions, execute code, or bypass any check — they only add text to the context window, so the blast radius of a bad rule is bad advice. The caveat is prompt-injection surface: `.claude/rules/` is committed to source control and loaded automatically, so anyone with commit access (or a malicious PR into a repo you then open) can inject instructions into your session without the approval dialog that guards external `@` imports in CLAUDE.md. Symlinked rules pointing outside the repo widen this. Review rules files in PRs the same way you review CI configuration, and rely on `permissions.deny` — not rules — for anything that must actually be blocked.

### 최근 변경

**최근 변경 내역 ⚠️**

v2.1.198: path matching now also works when Claude reaches a file through a symlinked path into the project directory (e.g. a symlinked checkout).
v2.1.207: a `paths` pattern containing an unparseable `[` now matches nothing and leaves the rule's other patterns working; previously one invalid pattern made the Read tool fail for every file that rule was evaluated against.
v2.1.211: on-demand instruction sources — path-scoped rules and rules in nested `.claude/rules/` directories — now respect exclusion of `project` from `--setting-sources`; previously they loaded regardless.
v2.1.217: brace expansion in `paths` is bounded to 1,000 expanded patterns and 4 MiB per rule, with oversized patterns used unexpanded; previously a `paths` value with many brace groups could stall or crash the CLI at startup.
v2.1.206+: `/doctor` gained a trim check that proposes cuts to a checked-in CLAUDE.md (removing what Claude can derive from the codebase, keeping pitfalls and conventions), which in practice pushes users toward moving area-specific content into rules.
Adjacent in the same period: `claudeMdExcludes` for monorepo suppression, and the `InstructionsLoaded` hook for auditing exactly which instruction files loaded. [uncertain on exact versions for the last two]

**라이프사이클**

Stable and officially documented, but rough at the edges. The feature is not flagged experimental anywhere in the docs and is actively refined release over release. However, the density of open bug reports specifically against path-scoped loading (#16299, #16853, #17204, #21858, #23478) and the documented `paths` vs `globs` mismatch mean the on-demand half should be treated as 'stable but verify' rather than fire-and-forget. The always-loaded half is entirely dependable.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Rules_경로_스코프_규칙.json`</sub>

---

## 17. Managed/Enterprise 정책 설정

`권한/보안`

### 기본 정보

**설정 명칭**

Managed policy settings (`managed-settings.json`), also called enterprise or policy settings. The top-priority settings layer, plus its managed-only keys: `requiredMinimumVersion`, `requiredMaximumVersion`, `allowedMcpServers`, `deniedMcpServers`, `allowManagedMcpServersOnly`, `allowManagedPermissionRulesOnly`, `allowManagedHooksOnly`, `availableModels`/`enforceAvailableModels`, `claudeMd`, `forceLoginMethod`, `forceLoginOrgUUID`, and the `disable*` feature switches.

**파일 위치**

macOS: `/Library/Application Support/ClaudeCode/managed-settings.json` plus the drop-in directory `/Library/Application Support/ClaudeCode/managed-settings.d/`. Linux and WSL: `/etc/claude-code/managed-settings.json` plus `/etc/claude-code/managed-settings.d/`. Windows: `C:\Program Files\ClaudeCode\managed-settings.json` plus `C:\Program Files\ClaudeCode\managed-settings.d\`. The legacy Windows path `C:\ProgramData\ClaudeCode\managed-settings.json` is no longer supported as of v2.1.75+. Files in the `managed-settings.d/` directory are sorted alphabetically (`10-telemetry.json`, `20-security.json`, ...) with later files overriding scalar values from earlier ones. A companion managed CLAUDE.md may be deployed at `/etc/claude-code/CLAUDE.md`, `/Library/Application Support/ClaudeCode/CLAUDE.md`, or `C:\Program Files\ClaudeCode\CLAUDE.md`; the `claudeMd` key embeds the same content inline instead. All of these paths are root/Administrator-writable only by design, and are distributed with MDM, Group Policy, Ansible, or similar. A server-side equivalent exists at https://claude.ai/admin-settings/claude-code.

**공식 문서**

Yes, extensively. Primary: https://code.claude.com/docs/en/settings (settings files, precedence, available settings). Also https://code.claude.com/docs/en/permissions#managed-settings, https://code.claude.com/docs/en/server-managed-settings (org-wide toggles pushed from the admin console), https://code.claude.com/docs/en/model-config#restrict-model-selection (availableModels / enforceAvailableModels), and https://code.claude.com/docs/en/memory (managed CLAUDE.md and the `claudeMd` key). The admin console page is https://claude.ai/admin-settings/claude-code.

**도입 버전 ⚠️**

The managed settings layer predates the 2.x line and has existed since Claude Code's enterprise rollout [uncertain]. Version-stamped changes that ARE documented: v2.1.75+ dropped the legacy Windows `C:\ProgramData\ClaudeCode\` path. Individual managed-only keys arrived progressively through the 2.1.x series; the docs do not give per-key introduction versions. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

This IS the top of the precedence chain. Documented order, highest first: (1) managed settings, (2) command-line arguments, (3) `.claude/settings.local.json`, (4) `.claude/settings.json`, (5) `~/.claude/settings.json`. Note the ordering quirk worth internalizing: managed settings outrank even explicit CLI flags, which is the whole point — a developer cannot argue their way past policy with a flag.

Merge semantics are per-type, not wholesale replacement: arrays are concatenated and de-duplicated across scopes, objects are deep-merged, scalars are overridden by the higher layer. This means an org allow-rule and a project allow-rule coexist rather than one erasing the other — which is exactly why `allowManagedPermissionRulesOnly` exists as the escape hatch when you need the managed layer to be the ONLY source of permission rules.

Parsing is deliberately tolerant and fails open: individual invalid entries are stripped rather than rejecting the whole file, so one typo cannot brick Claude Code across the fleet. Security-sensitive fields (`allowedMcpServers`, `forceLoginOrgUUID`) are enforced per-field rather than stripped wholesale. `requiredMinimumVersion`/`requiredMaximumVersion` likewise fail open — an invalid value is dropped, preventing a bad policy push from blocking startup everywhere. Run `claude doctor` / `/doctor` to list what got stripped.

A managed CLAUDE.md (or the `claudeMd` key) loads before user and project CLAUDE.md and cannot be suppressed by `claudeMdExcludes`, unlike every other instruction file.

**로딩 시점**

Read at process startup, before any session state exists, and applied for the entire session. There is no reload-on-change and no user-facing toggle. The `claudeMd` payload and any managed CLAUDE.md are injected into context at session start ahead of user and project instructions. Version enforcement (`requiredMinimumVersion`/`requiredMaximumVersion`) is evaluated at launch. Because the file lives in a root-owned path, it is trusted without the workspace-trust dialog that gates project-level hooks and `autoMemoryDirectory`.

**컨텍스트 비용**

Near zero for the settings themselves — they configure the harness, not the model, and never enter the context window. The exception is `claudeMd` and any managed CLAUDE.md, which are ordinary always-resident instruction text and cost tokens in every session on every machine in the fleet. That makes org-wide `claudeMd` the single most expensive managed key: every line is multiplied by every session your organization runs, so it should hold only what genuinely must apply everywhere.

### 채택도

**채택 근거 ⚠️**

Adoption is structurally bimodal: near-universal in regulated and large enterprises (it is the only mechanism that survives a security review, since everything below it is user-writable) and near-zero among individual developers, who have no reason to write a root-owned file to constrain themselves. Evidence: Anthropic ships a dedicated admin console page for it, a `server-managed-settings` docs page for pushing toggles centrally, and documented MDM/Group Policy/Ansible distribution guidance — all of which imply real fleet deployments. The `managed-settings.d/` drop-in directory in particular is a configuration-management-shaped affordance that only makes sense with Ansible/Puppet/Chef-style rollout. Public community artifacts (dotfiles repos, blog posts) are sparse compared to hooks or CLAUDE.md, because enterprise policy files are rarely published. [uncertain]

### 추천 설정

**설정 스니펫**

```
Baseline enterprise policy, /etc/claude-code/managed-settings.json:

{
  "requiredMinimumVersion": "2.1.200",

  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./**/*secret*)",
      "Read(./**/id_rsa*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(git push --force:*)",
      "Bash(terraform destroy:*)"
    ],
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm test:*)"
    ]
  },

  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverName": "memory" }
  ],
  "allowManagedMcpServersOnly": true,

  "availableModels": ["opus", "sonnet", "haiku"],
  "enforceAvailableModels": true,

  "disableSideloadFlags": true,
  "disableBypassPermissionsMode": "disable",

  "claudeMd": "Never commit secrets. Run `make lint` before committing.\nCustomer data must not leave approved systems.",

  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://collector.corp.example.com:4317"
  }
}

Split by concern with the drop-in directory (alphabetical; later wins):

  /etc/claude-code/managed-settings.d/
    10-telemetry.json     -> { "env": { "CLAUDE_CODE_ENABLE_TELEMETRY": "1" } }
    20-security.json      -> { "allowedMcpServers": [ ... ], "permissions": { "deny": [ ... ] } }
    30-models.json        -> { "availableModels": ["sonnet"], "enforceAvailableModels": true }

Hard lockdown (managed layer is the ONLY source of rules and hooks):

{
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,
  "disableSideloadFlags": true,
  "forceLoginMethod": "claudeai",
  "forceLoginOrgUUID": "00000000-0000-0000-0000-000000000000"
}

Version pinning during a staged rollout:

{
  "requiredMinimumVersion": "2.1.200",
  "requiredMaximumVersion": "2.1.250"
}

Feature switches available in the managed layer only:

  allowManagedPermissionRulesOnly  block user/project permission rules
  allowManagedHooksOnly            only managed/SDK/force-enabled plugin hooks load
  allowManagedMcpServersOnly       lock MCP to the managed allowlist
  disableAutoMode                  prevent users activating auto mode
  disableWorkflows                 turn off dynamic workflows org-wide
  disableAgentView                 disable background agents / `claude agents`
  disableRemoteControl             block Remote Control
  disableBrowserExternalNavigation disable external browsing in the desktop app
  disableMobileSimulatorTools      block iOS Simulator access
  disableArtifact                  disable Artifact publishing
  disableClaudeAiConnectors        disable claude.ai MCP connectors
  disableSideloadFlags             reject --plugin-dir/--plugin-url/--agents/--mcp-config
  channelsEnabled                  allow organization channels
  claudeMd                         org-wide instructions (managed only)

Verify what was accepted vs stripped:

    claude doctor
```

**결정적 vs 권고적**

Fully deterministic and client-enforced. These rules are applied by the Claude Code binary regardless of what the model decides, and they cannot be overridden by user settings, project settings, or command-line flags. This is the sharpest available line in the whole configuration surface: the docs draw it explicitly — use managed SETTINGS for technical enforcement (`permissions.deny`, `sandbox.enabled`, `env`, `forceLoginMethod`) and managed CLAUDE.md for behavioral guidance (style, compliance reminders). Anything you put in `claudeMd` is advisory and a model can fail to follow it; anything you put in `permissions.deny` is not.

### 모범 사례

**모범 사례**

1) Enforce with settings, guide with CLAUDE.md. If a control matters for compliance, it belongs in `permissions.deny` / `sandbox.enabled` / `disable*`, never in `claudeMd` — the latter is context a model may not follow.
2) Use `managed-settings.d/` rather than one monolithic file. Numbered files map cleanly onto separate config-management roles (telemetry, security, models) and let teams own slices independently.
3) Set `requiredMinimumVersion` to close known-vulnerable versions, and reach for `requiredMaximumVersion` only during a staged rollout — a permanent ceiling silently strands your fleet on old builds.
4) Prefer `deniedMcpServers` for known-bad servers and `allowManagedMcpServersOnly` when you need a closed world; remember the denylist takes precedence over the allowlist.
5) Pair `availableModels` with `enforceAvailableModels: true`. The allowlist alone does not enforce. Be aware a wholly invalid `availableModels` array is enforced as an EMPTY allowlist, blocking all non-default model selection until fixed.
6) Reach for `allowManagedPermissionRulesOnly` deliberately, not by default. It blocks project-level allow rules too, so every team's legitimate `Bash(npm test)` approval now has to come from you — expect a support load.
7) Set `disableSideloadFlags: true` in any environment where policy matters; otherwise `--mcp-config`, `--agents`, `--plugin-dir` and `--plugin-url` are an obvious route around your MCP and agent policy.
8) Run `claude doctor` on a canary machine after every policy push and diff the stripped-entry list. Fail-open parsing means a typo degrades silently rather than erroring.
9) Keep the policy files in version control and deploy them with the same review process as any other production config; they are root-owned and trusted without a prompt.
10) Keep `claudeMd` short. It is billed to every session on every machine in the organization.
11) Push telemetry configuration through the managed `env` block so observability is uniform and users cannot silently opt out.

**안티패턴**

1) Writing policy into `claudeMd` and calling it enforcement. 'Never run destructive commands' as instruction text is a suggestion; `permissions.deny` is a control.
2) Assuming a syntax error fails loudly. Managed settings fail OPEN by design — bad entries are stripped and the fleet runs unprotected while you believe policy is live. Always verify with `claude doctor`.
3) Setting `availableModels` without `enforceAvailableModels: true`, which leaves the restriction advisory.
4) Deploying to the legacy Windows path `C:\ProgramData\ClaudeCode\managed-settings.json`, unsupported since v2.1.75+ — silently no policy at all on Windows fleets that were configured before the change.
5) Leaving `disableSideloadFlags` unset while carefully curating `allowedMcpServers`; `--mcp-config` walks straight past the curation.
6) A permanent `requiredMaximumVersion` that nobody revisits, freezing the fleet on a version that later develops a CVE.
7) Assuming arrays replace rather than merge. Managed and project arrays are concatenated and de-duplicated, so an org allowlist does not remove project allow rules unless you also set `allowManagedPermissionRulesOnly`.
8) Hand-editing policy on individual machines instead of shipping it through MDM/Ansible — the fleet diverges and nobody can say what is actually enforced.
9) Blocking so much that developers route around Claude Code entirely, or worse, share a personal account. Over-restriction is a real failure mode, not a safe default.
10) Forgetting that `permissions.deny` in the managed layer does not stop a user from reading a secret with their own shell. Managed settings constrain the agent, not the human.

**보안 리스크**

SAFE (안전) — this layer IS the primary security control, and its risks are risks of misconfiguration rather than of exposure. Two failure modes deserve attention. First, fail-open parsing: a malformed policy silently degrades to no policy, so absence of errors is not evidence of enforcement — verify with `claude doctor`. Second, write access to `/etc/claude-code/` or `C:\Program Files\ClaudeCode\` is equivalent to full control over every Claude Code session on the machine, including the ability to inject instructions via `claudeMd`, point `env` at an attacker-controlled API base URL, or force-enable hooks; on a multi-user host, treat these paths with the same care as `/etc/sudoers`. Correctly deployed, this is the only layer that meaningfully constrains a developer who wants `--dangerously-skip-permissions`.

### 최근 변경

**최근 변경 내역 ⚠️**

v2.1.75+: the legacy Windows managed-settings path `C:\ProgramData\ClaudeCode\managed-settings.json` is no longer supported; deployments must use `C:\Program Files\ClaudeCode\`.
The `managed-settings.d/` drop-in directory (all three platforms) landed in the 2.1.x line, enabling alphabetically-ordered composition of policy fragments from separate config-management roles. [uncertain on exact version]
Newer managed-only feature switches tracking newly-shipped features: `disableWorkflows` (dynamic workflows), `disableAutoMode` (auto permission mode), `disableAgentView`, `disableRemoteControl`, `disableArtifact`, `disableMobileSimulatorTools`, `disableBrowserExternalNavigation`, `disableClaudeAiConnectors`, `allowManagedHooksOnly`, `channelsEnabled`. As a pattern, each major new capability now ships with a corresponding managed kill switch. [uncertain on exact versions]
The server-side admin console at https://claude.ai/admin-settings/claude-code now offers equivalent org-wide toggles (documented at /docs/en/server-managed-settings), so policy no longer has to be file-deployed. [uncertain on exact date]
`enforceAvailableModels` semantics were clarified: with it true, the Default option falls back to the first allowlisted model when the org default is not permitted, and a wholly invalid array is enforced as an empty allowlist. Related, teammate model selection in agent teams is now checked against the same allowlist with documented substitution behavior.

**라이프사이클**

Stable and strategically central. Not experimental, not deprecated, and expanding steadily — the pattern of shipping a managed `disable*` switch alongside each new capability (workflows, auto mode, agent view, remote control, artifacts) shows Anthropic treating this as the permanent enterprise control plane. The one deprecation to track is the legacy Windows `ProgramData` path (removed v2.1.75+). The newer server-managed settings console is an addition alongside file-based policy, not a replacement for it.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/ManagedEnterprise_정책_설정.json`</sub>

---

## 18. Telemetry / OpenTelemetry 설정

`환경/모델`

### 기본 정보

**설정 명칭**

Telemetry / OpenTelemetry configuration: `CLAUDE_CODE_ENABLE_TELEMETRY` plus the standard `OTEL_*` environment variables, the Claude Code-specific `OTEL_LOG_*` content controls, `OTEL_METRICS_INCLUDE_*` cardinality controls, `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA`, and the `otelHeadersHelper` settings key.

**파일 위치**

Set as environment variables, or — the recommended form for teams — inside the `env` block of any settings file: `~/.claude/settings.json` (user), `.claude/settings.json` (project), `.claude/settings.local.json` (local), or `managed-settings.json` / `managed-settings.d/*.json` (managed policy, so users cannot opt out). The one non-`env` key is `otelHeadersHelper`, a top-level settings key pointing at an executable that emits dynamic auth headers. Nothing lives in a dedicated telemetry file.

**공식 문서**

Yes, with a dedicated page: https://code.claude.com/docs/en/monitoring-usage covers the full variable reference, emitted metrics and events, privacy defaults, and worked collector configurations. Supporting pages: https://code.claude.com/docs/en/settings (the `env` block and `otelHeadersHelper`), https://code.claude.com/docs/en/env-vars (environment variable index), and https://code.claude.com/docs/en/costs (usage accounting). This is one of the better-documented corners of the product — the docs enumerate exact defaults for nearly every variable.

**도입 버전 ⚠️**

Core telemetry (`CLAUDE_CODE_ENABLE_TELEMETRY` with OTLP metrics and logs export) has been present since the 2025 enterprise push and predates the 2.1.x line [uncertain]. The docs do not version-stamp individual variables. Clearly newer additions in the 2026 line: span tracing behind `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA`, `CLAUDE_CODE_PROPAGATE_TRACEPARENT`, `OTEL_LOG_RAW_API_BODIES`, `OTEL_LOG_TOOL_CONTENT`, `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH`, the `OTEL_METRICS_INCLUDE_*` cardinality switches, `otelHeadersHelper` with `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS`, and the plugin/auth/permission event types. [uncertain]

### 스코프 / 로딩

**우선순위 계층**

Configured through the `env` block, so it inherits the standard settings precedence: managed > CLI args > local > project > user. Objects deep-merge, so an organization can pin the exporter and endpoint in managed settings while leaving other keys to the user — and a user cannot override a managed value. A real process-level environment variable set in the shell also participates; the practical enterprise pattern is to define the whole block in `managed-settings.d/10-telemetry.json` so observability is uniform and non-optional. Telemetry is entirely opt-in: with `CLAUDE_CODE_ENABLE_TELEMETRY` unset, nothing is exported regardless of the other variables.

**로딩 시점**

Read once at process startup and applied for the session's lifetime; there is no live reconfiguration. Export then runs continuously outside the model's context on a batching timer — metrics every `OTEL_METRIC_EXPORT_INTERVAL` ms (default 60000), logs/events every `OTEL_LOGS_EXPORT_INTERVAL` ms (default 5000), traces every `OTEL_TRACES_EXPORT_INTERVAL` ms (default 5000). The one exception to 'read once' is `otelHeadersHelper`, re-executed on the `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` interval (default 1740000 ms / 29 minutes) so short-lived collector credentials can be refreshed mid-session.

**컨텍스트 비용**

Zero. Telemetry is a harness-level concern: no variable, metric, or event ever enters the model's context window, and the model is not aware telemetry is enabled. The costs are elsewhere — network egress to the collector, storage on the backend, and (when the `OTEL_LOG_*` content switches are on) potentially large payloads carrying prompt, response, and raw API body text, bounded by `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` (default 61440 UTF-16 code units / 60 KB) unless `OTEL_LOG_RAW_API_BODIES=file:<dir>` writes untruncated bodies to disk.

### 채택도

**채택 근거 ⚠️**

Adoption mirrors managed settings: standard in enterprise deployments, rare among individuals. The strongest signals are structural rather than social — Anthropic ships a dedicated monitoring page, documents Prometheus/OTLP/console exporters, supports mTLS client certificates and a dynamic-headers helper script, and provides per-attribute cardinality switches. Those are the affordances of a feature that real observability teams have pushed on, not a nice-to-have. The emitted metric set (`claude_code.cost.usage`, `claude_code.token.usage`, `claude_code.lines_of_code.count`, `claude_code.pull_request.count`, `claude_code.commit.count`, `claude_code.active_time.total`, `claude_code.code_edit_tool.decision`) is clearly shaped by organizations building ROI and adoption dashboards. Public community dashboards and blog write-ups exist but are far less common than for hooks or CLAUDE.md, since telemetry configuration is internal by nature. [uncertain]

### 추천 설정

**설정 스니펫**

```
Minimal team setup (metrics + events, no message content), .claude/settings.json:

{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    "OTEL_METRIC_EXPORT_INTERVAL": "60000",
    "OTEL_LOGS_EXPORT_INTERVAL": "5000"
  }
}

Enterprise, mTLS + team attribution, /etc/claude-code/managed-settings.d/10-telemetry.json:

{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://collector.corp.example.com:4317",
    "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer <token>",
    "OTEL_EXPORTER_OTLP_CLIENT_KEY": "/etc/claude/client.key",
    "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE": "/etc/claude/client.crt",
    "OTEL_RESOURCE_ATTRIBUTES": "department=engineering,team.id=platform,cost_center=eng-1234",
    "OTEL_METRICS_INCLUDE_SESSION_ID": "false",
    "OTEL_METRICS_INCLUDE_ACCOUNT_UUID": "true",
    "OTEL_METRICS_INCLUDE_VERSION": "true"
  },
  "otelHeadersHelper": "/opt/corp/bin/generate-otel-headers.sh"
}

Local debugging (console exporter, 1s interval):

    export CLAUDE_CODE_ENABLE_TELEMETRY=1
    export OTEL_METRICS_EXPORTER=console
    export OTEL_METRIC_EXPORT_INTERVAL=1000
    claude

Multi-backend split (metrics to Prometheus, events to OTLP):

    export CLAUDE_CODE_ENABLE_TELEMETRY=1
    export OTEL_METRICS_EXPORTER=prometheus
    export OTEL_LOGS_EXPORTER=otlp
    export OTEL_EXPORTER_OTLP_LOGS_PROTOCOL=grpc
    export OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://logs.example.com:4317

Full content capture -- AUDIT / RESEARCH ONLY, captures prompts and responses:

    export CLAUDE_CODE_ENABLE_TELEMETRY=1
    export OTEL_LOGS_EXPORTER=otlp
    export OTEL_LOG_USER_PROMPTS=1
    export OTEL_LOG_ASSISTANT_RESPONSES=1
    export OTEL_LOG_TOOL_DETAILS=1
    export OTEL_LOG_RAW_API_BODIES=1

Variable reference (default in parentheses):

  CLAUDE_CODE_ENABLE_TELEMETRY            master switch (off); set 1
  OTEL_METRICS_EXPORTER                   console | otlp | prometheus | none
  OTEL_LOGS_EXPORTER                      console | otlp | none
  OTEL_TRACES_EXPORTER                    console | otlp | none  (beta)
  OTEL_EXPORTER_OTLP_PROTOCOL             grpc | http/json | http/protobuf
  OTEL_EXPORTER_OTLP_ENDPOINT             collector endpoint, all signals
  OTEL_EXPORTER_OTLP_{METRICS,LOGS,TRACES}_{PROTOCOL,ENDPOINT}   per-signal override
  OTEL_EXPORTER_OTLP_HEADERS              e.g. Authorization=Bearer <token>
  OTEL_EXPORTER_OTLP_CLIENT_KEY           mTLS key path
  OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE   mTLS cert path
  OTEL_METRIC_EXPORT_INTERVAL             (60000 ms)
  OTEL_LOGS_EXPORT_INTERVAL               (5000 ms)
  OTEL_TRACES_EXPORT_INTERVAL             (5000 ms)
  OTEL_LOG_USER_PROMPTS                   (off) include user prompt text
  OTEL_LOG_ASSISTANT_RESPONSES            (falls back to OTEL_LOG_USER_PROMPTS)
  OTEL_LOG_TOOL_DETAILS                   (off) tool names, commands, params, paths
  OTEL_LOG_TOOL_CONTENT                   (off) tool input/output bodies, traces only
  OTEL_LOG_RAW_API_BODIES                 (off) 1 = inline truncated, file:<dir> = untruncated on disk
  CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH     (61440 UTF-16 code units)
  OTEL_METRICS_INCLUDE_SESSION_ID         (true)
  OTEL_METRICS_INCLUDE_VERSION            (false)
  OTEL_METRICS_INCLUDE_ACCOUNT_UUID       (true)
  OTEL_METRICS_INCLUDE_ENTRYPOINT         (false)
  OTEL_METRICS_INCLUDE_RESOURCE_ATTRIBUTES (true)
  OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE  (delta) | cumulative
  OTEL_RESOURCE_ATTRIBUTES                key1=value1,key2=value2 (no spaces)
  CLAUDE_CODE_ENHANCED_TELEMETRY_BETA     (off) span tracing
  CLAUDE_CODE_PROPAGATE_TRACEPARENT       (off) W3C trace context to API and MCP
  CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS  (1740000 ms / 29 min)

Emitted metrics:

  claude_code.session.count            claude_code.lines_of_code.count
  claude_code.pull_request.count       claude_code.commit.count
  claude_code.cost.usage (USD)         claude_code.token.usage
  claude_code.code_edit_tool.decision  claude_code.active_time.total (s)

Emitted events (require OTEL_LOGS_EXPORTER):

  user_prompt, assistant_response, api_request, api_error, api_refusal,
  api_request_body, api_response_body, tool_decision, tool_result,
  permission_mode_changed, auth, mcp_server_connection, internal_error,
  plugin_installed, plugin_loaded
```

**결정적 vs 권고적**

Fully deterministic and entirely outside the model's control. Export is performed by the harness on a fixed timer; the model cannot see, alter, suppress, or trigger telemetry, and no prompt can talk it into leaking or withholding a metric. When the configuration is placed in managed settings, it is also outside the user's control. This makes telemetry one of the few genuinely tamper-resistant observability surfaces in the product — which is precisely why the privacy defaults matter so much.

### 모범 사례

**모범 사례**

1) Start with metrics only. `OTEL_METRICS_EXPORTER=otlp` plus `OTEL_LOGS_EXPORTER=otlp` gives cost, token, commit, PR, and active-time dashboards without capturing a single character of prompt text.
2) Leave the `OTEL_LOG_*` content switches off by default and treat turning any of them on as a decision requiring privacy/legal sign-off, employee notice, and a retention policy.
3) Deploy through managed settings (`managed-settings.d/10-telemetry.json`) so the whole fleet reports consistently and individuals cannot silently opt out.
4) Use `OTEL_RESOURCE_ATTRIBUTES` for team, department, and cost-center attribution — it is what turns raw metrics into chargeback and adoption reporting. No spaces; percent-encode special characters.
5) Control cardinality deliberately. `OTEL_METRICS_INCLUDE_SESSION_ID` defaults to true and is the usual cause of a time-series explosion; set it false for fleet-wide dashboards and enable it only when debugging.
6) Validate the pipeline locally with `OTEL_METRICS_EXPORTER=console` and `OTEL_METRIC_EXPORT_INTERVAL=1000` before pointing anything at a production collector.
7) Use `otelHeadersHelper` rather than a static bearer token in `OTEL_EXPORTER_OTLP_HEADERS`; it refreshes on the debounce interval so short-lived credentials work, and it keeps the secret out of the settings file.
8) Prefer mTLS (`OTEL_EXPORTER_OTLP_CLIENT_KEY` / `_CERTIFICATE`) over bearer tokens for collector auth in regulated environments.
9) Keep `delta` temporality (the default) unless your backend specifically requires cumulative.
10) Split signals when it helps — Prometheus scrape for metrics, OTLP for events — using the per-signal `OTEL_EXPORTER_OTLP_{METRICS,LOGS}_ENDPOINT` overrides.
11) If you must capture content for an audit, scope it: prefer `OTEL_LOG_TOOL_DETAILS` alone over full prompt capture, and set `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` down from 60 KB.
12) Remember `claude_code.cost.usage` is an estimate for internal accounting, not a billing source of truth.

**안티패턴**

1) Turning on `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`, and `OTEL_LOG_RAW_API_BODIES` fleet-wide 'for better visibility'. This ships developer prompts — which routinely contain proprietary source, customer data, and pasted credentials — into a logging backend with different access controls than your source repository. It is the single highest-risk configuration in this entire research set.
2) Using `OTEL_LOG_RAW_API_BODIES=file:<dir>` and forgetting it. Untruncated request/response JSON accumulates on local disk with no rotation.
3) Assuming `OTEL_LOG_ASSISTANT_RESPONSES` is independently off — it FALLS BACK to `OTEL_LOG_USER_PROMPTS`, so enabling prompt logging silently enables response logging unless you explicitly set it to `0`.
4) Setting `CLAUDE_CODE_ENABLE_TELEMETRY=1` and nothing else, then wondering why no data arrives. Without an exporter and `OTEL_EXPORTER_OTLP_PROTOCOL`/`ENDPOINT`, nothing is emitted.
5) Leaving `OTEL_METRICS_INCLUDE_SESSION_ID=true` on a large fleet and blowing up backend cardinality and cost.
6) Hardcoding a long-lived bearer token in `OTEL_EXPORTER_OTLP_HEADERS` inside a project `.claude/settings.json` that is committed to git.
7) Setting `OTEL_METRIC_EXPORT_INTERVAL` very low in production; the 1-second interval is a debugging tool, not a setting.
8) Spaces inside `OTEL_RESOURCE_ATTRIBUTES` — the format is strict `key=value` pairs, comma-separated, with special characters percent-encoded.
9) Enabling telemetry that captures individual developer activity without telling developers. Beyond the obvious legal exposure in jurisdictions with works councils or GDPR, it destroys trust in the tool faster than any dashboard repays.
10) Treating `claude_code.lines_of_code.count` as a productivity metric to rank people by.

**보안 리스크**

CAUTION (주의) by default, DANGEROUS (위험) once the content switches are on. In its default shape — metrics and events with `<REDACTED>` in place of prompt and response text, tool names and file paths not recorded, MCP and plugin names collapsed to `third-party`, tool errors reduced to a generic category like `Error:ENOENT` — telemetry is genuinely privacy-preserving and low risk; the design clearly had a privacy review. The risk is entirely in the opt-in content flags. `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT`, and `OTEL_LOG_RAW_API_BODIES` each move a class of sensitive content out of the developer's machine and into an observability backend, and prompts are among the most sensitive artifacts a developer produces. Two aggravating details: `OTEL_LOG_ASSISTANT_RESPONSES` inherits `OTEL_LOG_USER_PROMPTS` rather than defaulting off independently, and `OTEL_LOG_RAW_API_BODIES=file:<dir>` writes untruncated bodies to unmanaged local disk. Also treat `OTEL_EXPORTER_OTLP_HEADERS` as a secret-bearing field that must not be committed. Enabling content capture is a compliance decision, not a configuration tweak.

### 최근 변경

**최근 변경 내역 ⚠️**

Tracing arrived as a beta signal: `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` enables span tracing, `OTEL_TRACES_EXPORTER` / `OTEL_EXPORTER_OTLP_TRACES_*` / `OTEL_TRACES_EXPORT_INTERVAL` configure it, and `CLAUDE_CODE_PROPAGATE_TRACEPARENT=1` propagates W3C trace context into API and MCP calls — letting a Claude Code session be correlated with downstream service traces. [uncertain on version]
Content capture became finer-grained rather than all-or-nothing: `OTEL_LOG_TOOL_CONTENT` (tool input/output bodies, traces only) and `OTEL_LOG_RAW_API_BODIES` (with the `file:<dir>` mode for untruncated on-disk capture) split apart what used to be covered by `OTEL_LOG_TOOL_DETAILS`, and `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` (default 61440) now bounds inline content. [uncertain on version]
Cardinality controls were added as a group — `OTEL_METRICS_INCLUDE_SESSION_ID`, `_VERSION`, `_ACCOUNT_UUID`, `_ENTRYPOINT`, `_RESOURCE_ATTRIBUTES` — responding to backend cost problems at fleet scale. [uncertain on version]
`otelHeadersHelper` plus `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` (default 1740000 / 29 min) added support for rotating collector credentials mid-session, and mTLS client key/certificate options were added for collector authentication. [uncertain on version]
The event surface grew to cover newer subsystems: `api_refusal`, `permission_mode_changed`, `auth`, `mcp_server_connection`, `plugin_installed`, `plugin_loaded`, `internal_error`. [uncertain on version]

**라이프사이클**

Stable, with one beta component. Metrics and events export is production-grade, fully documented, and the backbone of enterprise Claude Code reporting. Trace/span support is explicitly beta, gated behind `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA`. Nothing here is deprecated. Because the variables follow the OpenTelemetry specification rather than a proprietary schema, this surface is comparatively stable across releases — the additions have been new signals and finer controls, not renames.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 최근 변경 내역 (`recent_changes`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Telemetry_OpenTelemetry_설정.json`</sub>

---

## 19. Agent Teams & Dynamic Workflows

`자동화/확장`

### 기본 정보

**설정 명칭**

Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, `teammateMode`, `--teammate-mode`) and Dynamic Workflows (`/workflows`, `/deep-research`, the `ultracode` keyword and `/effort ultracode`, `workflowSizeGuideline`, `disableWorkflows`, `CLAUDE_CODE_DISABLE_WORKFLOWS`). Two distinct multi-agent primitives that the outline groups together.

**파일 위치**

Agent teams — enablement in the `env` block of any settings file (`{"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}}`) or the shell environment; display mode via the top-level `teammateMode` key in `~/.claude/settings.json` or the experimental `--teammate-mode` flag. Runtime state (do not hand-edit): team config `~/.claude/teams/{team-name}/config.json`, mailboxes `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`, shared task list `~/.claude/tasks/{team-name}/`. `{team-name}` is `session-` plus the first eight characters of the session ID. Team config is deleted at session end; the task list persists under `cleanupPeriodDays`. There is no project-level equivalent — a `.claude/teams/teams.json` in your repo is treated as an ordinary file. Teammate roles are defined as ordinary subagents in `.claude/agents/*.md`.

Dynamic workflows — saved scripts in `.claude/workflows/*.js` (project, shared via git) or `~/.claude/workflows/*.js` (personal; under `CLAUDE_CONFIG_DIR` when set), or `workflows/` at a plugin root. Every run also writes its script under the session's directory in `~/.claude/projects/`. Settings keys: `workflowSizeGuideline` and `disableWorkflows` in any settings file.

**공식 문서**

Yes, two dedicated pages. Agent teams: https://code.claude.com/docs/en/agent-teams (documented 'as of v2.1.178', unusually version-precise throughout). Dynamic workflows: https://code.claude.com/docs/en/workflows. Supporting pages: https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/agents (comparison of subagents, agent view, agent teams, and workflows), https://code.claude.com/docs/en/costs#agent-team-token-costs, https://code.claude.com/docs/en/hooks (`TeammateIdle`, `TaskCreated`, `TaskCompleted`), https://code.claude.com/docs/en/features-overview#compare-similar-features, and https://code.claude.com/docs/en/server-managed-settings for the org-wide `disableWorkflows` toggle.

**도입 버전 ⚠️**

Agent teams: introduced v2.1.32 (2026-02-05) as a research preview, requiring Opus-class models (Opus 4.6+, Opus 5) [uncertain — community changelog, not the official docs]. The docs describe behavior 'as of v2.1.178', the release that removed the setup step: `TeamCreate` and `TeamDelete` no longer exist, spawning a teammate needs no setup, and cleanup is automatic at session exit.

Dynamic workflows: require v2.1.154 or later; announced 2026-06-02. `ultracode` as the trigger keyword replaced the literal `workflow` keyword in v2.1.160. `/effort ultracode` requires v2.1.203. The `workflowSizeGuideline` concept requires v2.1.202, and its `medium` default plus settings-file support require v2.1.219 (earlier versions default to `unrestricted`).

### 스코프 / 로딩

**우선순위 계층**

Both are configured through ordinary settings files and follow the standard managed > CLI > local > project > user precedence. Two org-level controls exist: `disableWorkflows: true` in managed settings (or the toggle on the Claude Code admin settings page) turns dynamic workflows off fleet-wide, and `disableAgentView` disables background agents. Agent teams have no dedicated managed kill switch beyond simply not setting the experimental env var — though managed settings can pin `env`, and teammate model selection is checked against the organization's `availableModels` allowlist.

Within a session the scoping is strict: one team per session, scoped to that session, no nested teams (teammates cannot spawn teammates), and the lead is fixed for the session's lifetime. Teammates inherit the lead's permission settings and effort level at spawn, but NOT the lead's `/model` selection (that comes from the 'Default teammate model' setting in `/config`) and not the lead's conversation history. Workflow subagents always run in `acceptEdits` mode and inherit your tool allowlist regardless of the session's permission mode. A project workflow beats a personal workflow of the same name; in a monorepo the `.claude/workflows/` closest to the working directory wins.

**로딩 시점**

Agent teams: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is read at startup. Without it no team is set up, no team directories are written, and Claude will not spawn or propose teammates. With it set, a team forms the moment the first teammate is spawned — either because you asked in natural language, or because Claude proposed it and you confirmed. Claude never spawns teammates without approval. A spawned teammate loads the same project context as a regular session (CLAUDE.md, MCP servers, skills) plus the lead's spawn prompt.

Dynamic workflows: four entry points. (1) A bundled or saved command such as `/deep-research` or `/<name>`. (2) The `ultracode` keyword in a prompt you type yourself. (3) Plain language — 'use a workflow'. (4) `/effort ultracode`, after which Claude plans a workflow for every substantive task in the session. The keyword is deliberately an opt-in only for human-typed input: it does NOT trigger from `-p`, from an Agent SDK prompt not stamped as human, from a scheduled task, or from a webhook payload or PR comment relayed into the conversation (tightened in v2.1.210). The run then executes in an isolated runtime in the background while the session stays responsive.

**컨텍스트 비용**

This is the axis on which the two primitives differ most, and the reason to care which one you pick.

Agent teams are the most expensive primitive in Claude Code. Each teammate is a full, independent Claude Code session with its own context window; token usage scales linearly with teammate count and the docs state plainly that teams use 'significantly more tokens than a single session'. Coordination messages add further overhead.

Dynamic workflows invert the tradeoff. The orchestration lives in a JavaScript script executed by a runtime outside the conversation, and intermediate results live in script variables rather than a context window — so Claude's context holds only the final answer even across hundreds of agents. Total token spend can still be very large (up to 16 concurrent agents, 1,000 agents per run), but the LEAD's context stays small, which is exactly what makes 500-file migrations tractable. Claude Code warns with a `Large workflow` notice when a run schedules more than 25 agents or projects past 1.5M tokens.

Rule of thumb: agent teams cost context in many windows; workflows cost tokens without costing the main context.

### 채택도

**채택 근거 ⚠️**

Strong community interest, with adoption clearly ahead of the experimental label. Agent teams generated a wave of practitioner write-ups — 'From Tasks to Swarms: Agent Teams in Claude Code' (alexop.dev), claudefa.st's 'Enable the Env Var, Run a Team', Lushbinary's multi-agent development guide, a dedicated agent-teams chapter in FlorianBruniaux/claude-code-ultimate-guide on GitHub, and multiple DEV/codecentric posts on multi-agent workflows. Dynamic workflows drew mainstream coverage after the 2026-06-02 announcement, including DevOps.com ('take on the tasks that were too big to automate'), several Medium/Data Science Collective deep dives, StackNotice's practical guide, and widely-shared social summaries of the four ways to launch one. The `ultracode` keyword in particular has become recognizable shorthand in the community. Counter-signal worth noting: much of the writing is introductory 'here is how to turn it on' content rather than reports of sustained production use, which fits a feature that is powerful, expensive, and still experimental. [uncertain]

### 추천 설정

**설정 스니펫**

```
Enable agent teams, ~/.claude/settings.json:

{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "in-process"
}

  teammateMode values:
    "in-process"  (default) all teammates in the main terminal, works anywhere
    "auto"        split panes when already in tmux, or iTerm2 with the it2 CLI
    "tmux"        split panes, auto-detects tmux vs iTerm2
    "iterm2"      iTerm2 native split panes (v2.1.186+, requires the it2 CLI)

  Per-session override:  claude --teammate-mode auto

Spawn a team (natural language, no config needed):

    I'm designing a CLI tool that tracks TODO comments across a codebase.
    Spawn three teammates to explore this from different angles: one on UX,
    one on technical architecture, one playing devil's advocate.

    Spawn a teammate using the security-reviewer agent type to audit
    src/auth/. Require plan approval before they make any changes.

Quality gates for teammates, .claude/settings.json:

{
  "hooks": {
    "TeammateIdle": [
      { "hooks": [ { "type": "command", "command": ".claude/hooks/verify-done.sh" } ] }
    ],
    "TaskCompleted": [
      { "hooks": [ { "type": "command", "command": "npm test --silent" } ] }
    ]
  }
}

  Exit code 2 from any of these sends feedback and blocks the transition
  (keeps the teammate working / prevents the task from being marked done).

Dynamic workflows, ~/.claude/settings.json:

{
  "workflowSizeGuideline": "medium",
  "disableWorkflows": false
}

  workflowSizeGuideline (advice to Claude, not an enforced cap; v2.1.202+,
  settings-file support and the "medium" default in v2.1.219+):
    "unrestricted"  no guideline, Claude sizes it to the task
    "small"         fewer than 5 agents
    "medium"        fewer than 15 agents   (default)
    "large"         fewer than 50 agents

  Also settable at runtime:  /config workflowSizeGuideline=small

Launch a workflow (four ways):

    /deep-research What changed in the Node permission model between v20 and v22?
    ultracode: audit every API endpoint under src/routes/ for missing auth checks
    use a workflow to migrate every component from styled-components to Tailwind
    /effort ultracode          # Claude decides for the rest of the session

Manage runs:  /workflows   then  Enter drill in, p pause/resume,
                                 x stop, r restart agent, f filter, s save

Shape of a saved script, .claude/workflows/audit-routes.js:

    export const meta = {
      name: 'audit-routes',
      description: 'Audit every route handler for missing auth checks',
    }

    const found = await agent('List every .ts file under src/routes/.', {
      schema: { type: 'object', required: ['files'],
                properties: { files: { type: 'array', items: { type: 'string' } } } },
    })

    const audits = await pipeline(found.files, file =>
      agent(`Audit ${file} for missing authentication checks.`, { label: file }),
    )

    return audits.filter(Boolean)

Turn workflows off org-wide, /etc/claude-code/managed-settings.json:

{ "disableWorkflows": true }

  Personal equivalents: "disableWorkflows": true in ~/.claude/settings.json,
  CLAUDE_CODE_DISABLE_WORKFLOWS=1, or the /config toggle.

Runtime limits: up to 16 concurrent agents (fewer on low-core machines),
1,000 agents total per run, no mid-run user input, no direct filesystem or
shell access from the script itself (only its agents act).
```

**결정적 vs 권고적**

The two primitives sit at opposite ends of this axis, which is the cleanest way to choose between them.

Agent teams are maximally flexible and minimally deterministic: the lead decides turn by turn what to spawn, what to assign, and when the work is done. Nothing about the orchestration is reproducible between runs. The deterministic parts are narrow — file-locked task claiming prevents claim races, task dependencies are resolved automatically, and `TeammateIdle`/`TaskCreated`/`TaskCompleted` hooks are code-enforced gates that exit 2 to block a transition.

Dynamic workflows deliberately move the plan into code: the script holds the loop, the branching, and the intermediate results, so the orchestration itself becomes the repeatable artifact — read it, diff it, edit it, rerun it, save it as a command, ship it in a plugin. What stays non-deterministic is the script's authorship (Claude writes it fresh unless you saved one) and the agents' own outputs. `workflowSizeGuideline` is explicitly advisory, not a cap; the runtime's 16-concurrent / 1,000-total agent limits are the real enforcement.

### 모범 사례

**모범 사례**

Choosing between them:
1) Use subagents when only the result matters, agent teams when workers need to talk to each other, and workflows when the same step must run across many items or the orchestration should be reusable. The distinguishing question for teams is communication: teammates message each other directly and share a task list, subagents only report back.
2) Prefer workflows for scale (dozens to hundreds of agents) and teams for depth (a handful of long-running peers that debate).

Agent teams:
3) Start with 3-5 teammates and 5-6 tasks each; three focused teammates routinely beat five scattered ones.
4) Begin with research and review tasks — PR review, library investigation, bug hunts — before trying parallel implementation. Clear boundaries, no merge conflicts.
5) Give each teammate a distinct lens (security / performance / test coverage) so their work does not overlap.
6) The adversarial pattern is the highest-value use: have teammates try to disprove each other's hypotheses. Sequential investigation anchors on the first plausible theory; a surviving theory from real debate is far more likely to be the root cause.
7) Put everything the teammate needs in the spawn prompt — they load CLAUDE.md, MCP servers, and skills, but inherit none of the lead's conversation history.
8) Partition files so no two teammates edit the same one; concurrent edits overwrite.
9) Name teammates explicitly in your spawn instruction so you can address them later.
10) Reuse `.claude/agents/*.md` subagent definitions as teammate roles — one definition serves both. Note `skills` and `mcpServers` frontmatter is ignored for teammates.
11) Require plan approval for risky work, and give the lead explicit approval criteria ('only approve plans with test coverage') since it decides autonomously.
12) Pre-approve common operations in permission settings before spawning; every teammate's prompts bubble up to you in the lead session.
13) Enforce completion standards with `TeammateIdle` and `TaskCompleted` hooks rather than trusting self-report — task status lagging is a documented limitation.
14) Monitor and steer. Unattended teams waste tokens fast.

Dynamic workflows:
15) Try `/deep-research` first to see the shape before writing your own.
16) Pilot on a slice — one directory, a narrow question — and read the per-agent token counts in `/workflows` before committing to the whole repo.
17) Prefer many small agents over few long ones: on resume, cached results stop at the first agent that did not finish and everything started after it reruns, so fine-grained fan-out preserves far more progress.
18) Add the commands your agents need to the allowlist before a long run; unallowlisted shell, web fetch, and MCP calls still prompt mid-run.
19) Set `workflowSizeGuideline` to `small` for routine work and reserve `large` for genuine migrations; it also moves the `Large workflow` warning threshold.
20) Save a run that worked (`s` in `/workflows`) and ship it in a plugin to standardize a process across teams.
21) Check `/model` before a large run, or set `CLAUDE_CODE_SUBAGENT_MODEL`, so hundreds of agents do not silently run on your most expensive model.
22) Use the adversarial-verification pattern in the prompt ('adversarially verify each finding before reporting it') — cross-checking is what makes a workflow more trustworthy than one long pass, not just faster.

**안티패턴**

1) Reaching for a team on sequential work, same-file edits, or dependency-heavy tasks. Coordination overhead then exceeds any parallelism gain and a single session or subagents win outright.
2) Spawning 8-10 teammates because more feels faster. Token cost scales linearly, coordination overhead grows superlinearly, and returns diminish sharply past ~5.
3) Assuming a team formed because the agent panel has rows in it. Claude may have spawned subagents instead — they share the panel. Ask again and explicitly request an agent team.
4) Thin spawn prompts. A teammate that inherits no conversation history and gets 'help with auth' will produce work you throw away.
5) Letting two teammates own the same file.
6) Trusting task status. Teammates sometimes fail to mark tasks complete, which blocks dependent tasks; verify or gate with hooks.
7) Expecting `/resume` or `/rewind` to restore in-process teammates. They do not, and the lead may then try to message teammates that no longer exist.
8) Assuming a teammate died because its row vanished. Idle rows hide after 30 seconds and surplus idle rows collapse into an `N idle agents` row; the teammate is still running and addressable.
9) Hand-editing or pre-authoring `~/.claude/teams/{team-name}/config.json`, or committing a `.claude/teams/teams.json` and expecting it to configure anything. The former is overwritten on the next state update; the latter is just a file.
10) Running the lead with `--dangerously-skip-permissions` and forgetting that every teammate inherits it.
11) Expecting one teammate to approve another's permission prompt. Cross-agent messages are treated as untrusted input, and a denied action cannot be relayed to a peer to get it approved — by design.
12) Planning on split panes inside VS Code's integrated terminal, Windows Terminal, or Ghostty; unsupported. Also note the default changed to `in-process` in v2.1.179, so sessions that used to open panes silently stopped.
13) Stopping a workflow mid fan-out and expecting to keep the finished work. Every agent that STARTED after the first unfinished one reruns, even if it completed.
14) Leaving `/effort ultracode` on for routine work. Every substantive task becomes one or more workflows, at large token and latency cost.
15) Exiting Claude Code with a workflow running and expecting to resume it. Resume works only within the same session.
16) Assuming your permission mode protects the workflow's agents. They always run in `acceptEdits` — file edits are auto-approved regardless of your session mode.
17) Treating `workflowSizeGuideline` as a hard cap. It is advice; a prompt calling for a different scale overrides it.

**보안 리스크**

CAUTION (주의). Neither primitive weakens the permission model — the design here is notably careful — but both multiply blast radius and cost.

What is well-handled: teammates start with the lead's permission settings and their prompts surface in the lead session for a human to answer; a message from another agent is explicitly labeled as coming from another Claude session, so a teammate cannot approve a prompt or supply consent on your behalf; a denied action cannot be laundered through a peer; and in auto mode the classifier reviews every inter-agent message — including structured shutdown and plan-approval messages — and blocks ones that fail, so relayed approval claims are treated as untrusted input. The `ultracode` keyword is likewise restricted to human-typed input specifically so that a webhook payload or PR comment cannot start a workflow (v2.1.210).

What warrants care: `--dangerously-skip-permissions` on the lead propagates to every teammate, turning one unsandboxed session into N. Workflow subagents always run in `acceptEdits`, so file edits are auto-approved regardless of your session mode — a workflow over a large tree can rewrite a lot of code without a single prompt. Parallel agents editing overlapping files can corrupt work through ordinary race conditions rather than malice. And a 1,000-agent run is a real financial exposure; the `Large workflow` warning is advisory and does not pause anything. For regulated environments, `disableWorkflows` and `disableAgentView` exist in managed settings for a reason.

### 최근 변경

**최근 변경 내역**

Agent teams — v2.1.178 removed the setup step entirely: `TeamCreate`/`TeamDelete` no longer exist, spawning a teammate needs no preparation, cleanup happens automatically at session exit, and the `team_name` input on the Agent tool plus the `team_name` field in `TaskCreated`/`TaskCompleted`/`TeammateIdle` hook payloads are now session-derived and deprecated. v2.1.179 changed the default `teammateMode` from `auto` to `in-process`, so upgraded sessions that used to open split panes now stay in one terminal. v2.1.186 added explicit `iterm2` mode (requires the `it2` CLI) and started passing the lead's effort level to split-pane teammates. v2.1.198 made a teammate whose turn ends on an API error notify the lead with the error text instead of appearing to finish normally, and made a message from the lead or a peer wake a teammate waiting on a retry. v2.1.199 kept idle rows visible while any agent is still working and added a notice when `/model` or `/fast` is typed while viewing a teammate. v2.1.207 made malformed mailbox entries be reported and removed rather than blocking delivery for that mailbox until you deleted the file by hand.

Dynamic workflows — announced 2026-06-02, requiring v2.1.154+. v2.1.160 changed the trigger keyword from `workflow` to `ultracode`. v2.1.196 made unverifiable claims in `/deep-research` report as unverified rather than refuted. v2.1.202 introduced the size guideline; v2.1.219 made `medium` the default and allowed `workflowSizeGuideline` in settings files (taking precedence over `/config`). v2.1.203 added `/effort ultracode` and the `Large workflow` warning at >25 agents or >1.5M projected tokens. v2.1.208 fixed the save dialog showing `~/.claude/workflows/` when `CLAUDE_CONFIG_DIR` was set. v2.1.210 restricted the keyword to human-typed input, closing the path where a webhook payload or PR comment could start a workflow. v2.1.216 made Claude Code refuse to write a saved workflow through a symlink rather than following it. v2.1.218 stopped Claude from starting `/deep-research` on its own. v2.1.203-v2.1.205 had a UI regression where left-arrow did not back out of a phase.

**라이프사이클**

Split. Agent teams are EXPERIMENTAL and disabled by default, and the docs list substantial known limitations: no session resumption for in-process teammates, lagging task status, slow shutdown, one team per session, no nested teams, no background subagents from in-process teammates, a fixed lead, permissions fixed at spawn, and split panes requiring tmux or iTerm2. They are being actively developed — the v2.1.178 removal of `TeamCreate`/`TeamDelete` shows the API surface is still moving, so expect churn.

Dynamic workflows are effectively STABLE and generally available: no experimental flag, available on all paid plans plus the Anthropic API, Amazon Bedrock, Google Cloud's Agent Platform, and Microsoft Foundry, across CLI, desktop, IDE extensions, headless `-p`, and the Agent SDK, with a bundled `/deep-research` command and managed kill switches. On Pro they must be turned on from the `/config` Dynamic workflows row. The recent changes are hardening (symlink refusal, human-input-only keyword, size guidelines) rather than redesign.

<details><summary>이 항목에서 ⚠️ 로 표시된 불확실 필드</summary>

- 채택 근거 (`adoption_evidence`)
- 도입 버전 (`version_introduced`)

</details>

<sub>출처: `results/Agent_Teams_Dynamic_Workflows.json`</sub>
