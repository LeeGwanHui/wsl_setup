#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse guard — the one control that --dangerously-skip-permissions cannot bypass.

A PreToolUse "deny" fires before any permission-mode check, so these rules hold in
manual mode, auto mode, and bypassPermissions alike. permissions.deny does NOT:
bypass mode removes all prompts and protected-path checks. That asymmetry is the
whole reason this file exists.

Contract (see the Hooks section of report.md):
  stdin   JSON with .tool_name and .tool_input
  deny    print hookSpecificOutput JSON on stdout, exit 0
  allow   print nothing, exit 0
Anything unexpected exits 0 silently — a broken guard must never wedge the session.

Scope: this is a blunt backstop for irreversible damage, not a security boundary.
It reads a command string, so it cannot see through `bash -c "$(...)"`, aliases, or
a script it never inspects. Treat it as a seatbelt.
"""

import json
import re
import sys

# (compiled pattern, reason) — matched against the Bash command string.
BASH_RULES = [
    (r"\brm\s+(-[a-zA-Z]*\s+)*-?[a-zA-Z]*[rf][a-zA-Z]*\s+(-[a-zA-Z]+\s+)*(/|~|\$HOME)\s*($|;|&)",
     "Recursive delete of / or $HOME."),
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r",
     "rm -rf. If you meant it, run it yourself."),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard discards uncommitted work."),
    (r"\bgit\s+clean\s+-[a-zA-Z]*[fd]", "git clean deletes untracked files."),
    (r"\bgit\s+push\s+.*(--force\b|-f\b)", "Force push rewrites published history."),
    (r"\bgit\s+checkout\s+--\s+\.", "Discards all working-tree changes."),
    (r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba|z|)sh\b",
     "Piping a download straight into a shell."),
    (r"\bdd\b[^\n]*\bof=/dev/", "dd writing to a raw device."),
    (r"\bmkfs(\.|\s)", "Filesystem format."),
    (r">\s*/dev/(sd|nvme|hd)", "Redirect onto a raw block device."),
    (r"\bchmod\s+(-[a-zA-Z]+\s+)*777\s+(/|~|\$HOME)\s*($|;|&)",
     "chmod 777 on / or $HOME."),
    (r"\b(shutdown|reboot|halt|poweroff)\b", "Machine power state."),
    (r":\s*\(\s*\)\s*\{.*\|.*&.*\}\s*;\s*:", "Fork bomb."),
    (r"\bhistory\s+-c\b", "Clearing shell history."),
]

# Paths that must not be read, edited, or written regardless of mode.
PATH_RULES = [
    # A leading boundary of start-of-string, "/" or whitespace, so these match both a
    # bare file_path ("/srv/app/.env") and a token inside a command ("cat .env").
    (r"(^|/|\s)\.env(rc)?($|\.|\s)", "Environment/secret file."),
    (r"(^|/|\s)id_(rsa|ed25519|ecdsa)($|\.|\s)", "Private SSH key."),
    (r"/\.ssh/", "SSH directory."),
    (r"/\.aws/credentials", "AWS credentials."),
    (r"/\.config/gh/hosts\.yml", "GitHub CLI token store."),
    (r"(^|/|\s)\.npmrc($|\s)", "npm token store."),
]

COMPILED_BASH = [(re.compile(p, re.I), r) for p, r in BASH_RULES]
COMPILED_PATH = [(re.compile(p, re.I), r) for p, r in PATH_RULES]


def deny(reason):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[guard.py] {reason}",
        }
    }, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    tool = payload.get("tool_name") or ""
    args = payload.get("tool_input") or {}
    if not isinstance(args, dict):
        return

    if tool == "Bash":
        command = args.get("command") or ""
        for pattern, reason in COMPILED_BASH:
            if pattern.search(command):
                deny(reason)
        for pattern, reason in COMPILED_PATH:
            if pattern.search(command):
                deny(f"{reason} Touching it from a shell command.")
        return

    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        path = args.get("file_path") or args.get("notebook_path") or ""
        for pattern, reason in COMPILED_PATH:
            if pattern.search(path):
                deny(reason)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
