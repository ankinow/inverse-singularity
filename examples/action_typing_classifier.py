# action_typing.py — step-intent emitter for the diary work-blocks

"""Emits the doctrine marker `⊗S:mutation` / `⊗S:observe` next to each `>T:` line.

Closes the loop `theory/action-typing.md` (ist-runtime v0.7.9) names as the thread's
honest gap: the read-only harness `a4_action_typing.py` can only compute the
mutation-rate curve once PRODUCTION LOGGING carries per-step intent. This module is
the producer half: the scribe's post_tool_call hook appends one typed line after
every `>T:tool` line, so typed coverage climbs past the 15% floor and the curve
becomes computable on recorded (not classified) intent.

Typing rules follow the doctrine's canonical tool→intent mapping (§2):
  - unambiguous tools get their canonical type directly;
  - `terminal`/`execute_code`/`browser_exec` are ambiguous by design — the command
    string is inspected with conservative regexes; a state-changing verb or a
    write-redirect wins over an observe prefix (fail-safe direction);
  - anything else stays UNKNOWN (never guessed) and emits no marker line.

ε_code compression (A6 forward-only, 2026-09-11): the terminal-shape classifier was
extended to resolve the dominant UNKNOWN clusters measured in production state.db —
pure-read status commands (systemctl is-active/show, df/du/free/lsblk/ps/ss/stat/
sha256sum/journalctl/uptime/nproc/uname/hostname/id/whoami/mount/findmnt), print-only
`sed -n` (no `-i`), `python3 <script> --help|-h`, `rsync --dry-run/-ani`, read-only
`hermes`/`omarchy` subcommands, and `git` read forms. A prefix normalizer strips
`cd <path>`/`sudo`/`sudo -S` so the actual verb is visible; `tee`, real `rsync -a`,
`omarchy hook install`/`update`, and profile-prefixed `hermes config set` joined the
mutation side. Each added shape is pinned by a selftest case below.
"""

from __future__ import annotations

import re

# --- Canonical tool → intent mapping (doctrine §2) ----------------------------

MUTATE_TOOLS = {"patch", "write_file", "delegate_task", "browser_post"}
OBSERVE_TOOLS = {
    "read_file", "search_files", "session_search", "skill_view", "web_search",
    "web_action", "web_extract", "memory", "vision_analyze", "todo",
}
AMBIGUOUS_TOOLS = {"terminal", "execute_code", "browser_exec"}

# --- Command normalization -----------------------------------------------------
# Strip leading navigation/auth prefixes so the *verb* is matched, not the prefix.
# Conservative: only strips a pure `sudo`/`sudo -S`/`cd <path>` chain joined by `&&`
# or `;`; the remainder is re-classified. Anything non-trivial (redirections,
# pipes into the prefix) is left intact.

_CD_SEG = re.compile(r"(?:^|[;&]\s*)cd\s+\S+")
_SUDO_SEG = re.compile(r"(?:^|[;&]\s*)sudo(?:\s+-\S+)*\s+")


def _normalize(command: str) -> str:
    """Strip leading cd/sudo segments so the mutation/observe verb is visible."""
    s = command.strip()
    # only normalize when the prefix is a clean chain (no pipes or input redirects
    # that would make the suffix ambiguous).
    if "|" in s or "<<<" in s or "< " in s:
        return s  # pipes/input-redirects: leave intact, never guess
    prev = None
    while prev != s:
        prev = s
        s = _CD_SEG.sub("", s, count=1).strip()
        s = _SUDO_SEG.sub("", s, count=1).strip()
        s = re.sub(r"^&&\s*", "", s).strip()
        s = re.sub(r"^;\s*", "", s).strip()
    # recurse at most through the first chain token: keep it single-pass safe
    return s


# --- Conservative terminal/execute_code heuristics -----------------------------
# Order matters: mutation wins over observe when both match (fail-safe direction).

_MUTATION_VERB_PATTERNS = (
    r"\b(git\s+(push|commit|merge|rebase|cherry-pick|reset|checkout\s+-b|stash\s+(apply|pop|drop|clear)))\b",
    r"\b(npm\s+(i\b|install\b|ci\b|uninstall|update)|bun\s+(add\b|remove\b|install\b)|"
    r"pacman\s+-[A-Za-z]*S|pip3?\s+install|pipx\s+install|cargo\s+install)\b",
    # npm mutation (audit fix rewrites lockfile/deps; publish/link/pack mutate registry)
    r"\bnpm\s+(audit\s+fix|publish|link|pack)\b",
    # NOTE: cargo build/test are NOT here — doctrine §2 classifies build/test checks
    # as observe (they write derived artifacts, not the managed system).
    r"\b(mv|cp)\s+\S",
    r"\brm\b|\bmkdir\b|\brmdir\b|\bchmod\b|\bchown\b|\bln\s+-s\b|\btruncate\b|\bdd\b|\btee\b",
    r"\bsed\s+(-[A-Za-z]*i|--in-place)\b",
    r"\b((npx\s+)?wrangler\s+(deploy|d1 execute|kv:key put|r2 object put))\b",
    r"\bhermes\s+config set\b",
    r"\bhermes\s+(--profile|-p)\s+\S+\s+config set\b",
    r"\bhermes\s+cron\s+(run|create|update|delete|resume|disable|enable)\b",
    r"\bhermes\s+gateway\s+restart\b",
    r"\bhermes\s+kanban\s+(claim|complete|block|archive|assign)\b",
    r"\b(curl|wget)\b[^|;&]*\s(-d\b|--data\b|-T\b|-X\s*(POST|PUT|PATCH|DELETE)\b)",
    r"\bsystemctl\s+(start|stop|restart|enable|disable|reload|mask|unmask|set-property|daemon-reload)\b",
    r"\bkill\b|\bpkill\b|\breboot\b|\bshutdown\b",
    # known system-image writes (bootloader initramfs/generators)
    r"\b(mkinitcpio|limine-\S*|grub-(install|mkconfig)|update-grub|dracut)\b",
    # rsync that actually copies (no dry-run / list-only / itemize-only flag)
    r"\brsync\b(?![^|;&]*(?:--?(?:dry-run|list-only|itemize-changes))\b)",
    # omarchy real mutations
    r"\bomarchy\s+(hook\s+install|update|install|enable|disable|set|pkg\s+(add|remove)|menu\s+summon)\b",
    # python-ish mutation payloads (execute_code): write-mode opens / Path writes / shutil
    r"\bopen\s*\([^)]*['\"][waxa+]?['\"]\s*\)",
    r"\.write_text\s*\(|\.write_bytes\s*\(|\.mkdir\s*\(|\.unlink\s*\(|\.rmdir\s*\(",
    r"\bshutil\s*\.\s*(copy|copytree|move|rmtree)\b",
)
# write-redirects: > file and >> append mutate the fs even via echo/cat. Guard
# against false positives: the target must look like a path (word/dot/slash/tilde/$)
# so `->` arrows inside quoted strings and `>/dev/null` discards don't count.
_WRITE_REDIRECT = re.compile(r"(>>|>)\s*(?!/dev/null)(?=[\w.~/\\$])")

_OBSERVE_PREFIX_PATTERNS = (
    # git read forms (added for ε_code compression)
    r"\bgit\s+(status|log|diff|show|branch|rev-parse|remote|stash\s+list|tag|ls-files|describe|reflog)\b",
    r"\bls\b|\bcat\b|\bpwd\b|\bwhich\b|\bwg\b|\becho\b|\bdate\b",
    r"\bgrep\b|\brg\b|\bfind\b|\bwc\b|\bhead\b|\btail\b|\bjq\b",
    # print-only sed (no -i / --in-place): reads and prints, does not mutate
    r"\bsed\b(?![\s\S]*--?i\b|\b-i\b)",
    r"\bpython3?\s+-c\b|\bnode\b(-v)?\b|\bbun\b",
    # build/test/lint checks are observation per doctrine §2 (derived artifacts only)
    r"\bcargo\s+(build|test|check|run|clippy|fmt\s+--check)\b",
    r"\bnpm\s+run\s+(build|test|check|lint)\b|\bpytest\b|\bvitest\b|\bnode\s+--test\b",
    # pure-read system/status commands (the dominant UNKNOWN cluster)
    r"\bsystemctl\s+(?:--user\s+|--system\s+)?(is-active|is-enabled|is-failed|list-units|list-unit-files|list-dependencies|show|status|cat)\b",
    r"\b(df|du|free|lscpu|lsblk|blkid|ps|ss|stat|sha1sum|sha256sum|md5sum)\b",
    r"\b(journalctl|uptime|nproc|uname|hostname|id|whoami|groups|getent)\b",
    r"\b(mount|findmnt|lsusb|lspci|printenv|env)\b",
    r"\bip\s+(a|addr|link|route|addr\s+show)\b",
    # python3 running a script with --help / -h only
    r"\bpython3?\s+\S+\s+(-h|--help)\b",
    # rsync dry-run / itemize-only (does not copy)
    r"\brsync\b[^|;&]*\s--?(dry-run|list-only|itemize-changes)\b",
    # npm read forms (registry view / audit report / version)
    r"\bnpm\s+(?:(--version|-v)\b|view\b|outdated\b|ls\b|list\b|audit\b(?!\s+fix))",
    # omarchy read forms
    r"\bomarchy\s+(version|debug\b|theme\s+(current|list)|font\s+(current|list)|commands\b|commands\s+--(all|json|check))",
    # read-only hermes subcommands
    r"\bhermes\s+(doctor|model|config\s+get|config\s+check|profile\s+(list|show)|cron\s+(list|status|doctor|incidents|runs|edit\s+--help)|"
    r"gateway\s+(status|list|--help)|mcp\s+(list|test)|kanban\s+(status|stats|list|show|view))\b",
    r"\bhermes\s+(--profile|-p)\s+\S+\s+config\s+get\b",
    # read-only omarchy subcommands
    r"\bomarchy\s+(system\s+stats|menu\b[^|;&]*--print|update\s+--help|hook\s+install\s+--help|--help|--version)\b",
)


# --- Emitter -------------------------------------------------------------------


def _command_of(args: dict | None) -> str:
    """Best-effort extraction of the shell-ish payload from tool args."""
    if not isinstance(args, dict):
        return ""
    for key in ("command", "cmd", "code", "script"):
        value = args.get(key)
        if isinstance(value, str):
            return value
    # execute_code-style nested payloads: {"lang": {...}}
    for value in args.values():
        if isinstance(value, dict):
            inner = _command_of(value)
            if inner:
                return inner
    return ""


def _scored(command: str, patterns) -> bool:
    """Return True if any compiled pattern matches the command."""
    return any(p.search(command) for p in patterns)


_MUTATION_VERBS = tuple(re.compile(p, re.IGNORECASE) for p in _MUTATION_VERB_PATTERNS)
_OBSERVE_PREFIXES = tuple(re.compile(p, re.IGNORECASE) for p in _OBSERVE_PREFIX_PATTERNS)


def classify(tool_name: str, args: dict | None) -> str:
    """Return 'mutation', 'observe' or '' (UNKNOWN — never guessed)."""
    tool = str(tool_name or "").strip()
    if not tool:
        return ""

    if tool in MUTATE_TOOLS:
        return "mutation"

    if tool in AMBIGUOUS_TOOLS:
        command = _command_of(args)
        if not command.strip():
            return ""  # no evidence -> UNKNOWN
        norm = _normalize(command)
        if not norm.strip():
            return ""
        for pattern in _MUTATION_VERBS:
            if pattern.search(norm):
                return "mutation"
        if _WRITE_REDIRECT.search(norm):
            return "mutation"  # > file / >> append mutate the fs even via echo/cat
        for pattern in _OBSERVE_PREFIXES:
            if pattern.search(norm):
                return "observe"
        return ""  # ambiguous command with no recognizable shape stays UNKNOWN

    if tool == "process":
        # read-only lifecycle actions are observation; anything that feeds stdin
        # (write/submit/close/kill) may drive external state -> never guessed
        return "observe" if str((args or {}).get("action", "")).lower() in {
            "poll", "log", "list", "wait",
        } else ""

    if tool in OBSERVE_TOOLS:
        return "observe"

    return ""  # unknown tool family -> never guess


def marker_line(intent: str) -> str:
    """One dedicated diary line per typed block (the format the harness parses).

    The parser anchors on `^⊗S:(mutation|observe)` — a standalone line, NOT an
    inline suffix on the `>T:` line.
    """
    if intent not in ("mutation", "observe"):
        return ""
    return f"⊗S:{intent}"


def emit_line(tool_name: str, args: dict | None) -> str:
    """Convenience for the scribe hook: full line to append ('' when UNKNOWN)."""
    return marker_line(classify(tool_name, args))


# --- Selftest (deterministic, stdlib-only) --------------------------------------


def _selftest() -> int:
    cases_mutate: list[tuple[str, dict]] = [
        ("terminal", {"command": "git commit -m 'x' && git push origin main"}),
        ("terminal", {"command": "npm run build && wrangler deploy --env production"}),
        ("terminal", {"command": "echo hi > /tmp/out.txt"}),
        ("terminal", {"command": "hermes config set agent.max_turns 66"}),
        ("terminal", {"command": "sed -i 's/a/b/' file.py"}),
        ("terminal", {"command": "sudo tee /etc/sudoers.d/99-x <<'EOF'\n%wheel ALL=(ALL) NOPASSWD: ALL\nEOF"}),
        ("terminal", {"command": "cd /tmp && git push origin main"}),
        ("terminal", {"command": "rsync -a --exclude='*.lock' /src/ dest:/dst/"}),
        ("terminal", {"command": "hermes --profile atelier config set model.default deepseek-v4-pro"}),
        ("terminal", {"command": "omarchy hook install post-boot /path/to/hook"}),
        ("terminal", {"command": "sudo limine-mkinitcpio"}),
        ("execute_code", {"code": "open('/tmp/x','w').write('y')"}),
        ("execute_code", {"code": "Path('/tmp/x').write_text('y')"}),
        ("execute_code", {"code": "shutil.move('/a','/b')"}),
        ("patch", {"path": "/tmp/x"}),
        ("write_file", {"path": "/tmp/y"}),
        ("delegate_task", {"goal": "build it"}),
        ("terminal", {"command": "curl -d '{\"a\":1}' https://api.example.com/x"}),
    ]
    cases_observe: list[tuple[str, dict]] = [
        ("read_file", {"path": "/tmp/x"}),
        ("search_files", {"pattern": "*.py"}),
        ("skill_view", {"name": "foo"}),
        ("web_search", {"query": "x"}),
        ("terminal", {"command": "git status && git log --oneline -3"}),
        ("terminal", {"command": "cargo test --release"}),
        ("terminal", {"command": "ls -la /mnt/hermes/diary | head -20"}),
        ("terminal", {"command": "grep -rn 'foo' . ; tail -5 f.md"}),
        ("terminal", {"command": "grep -n '->' table.md | head"}),  # arrow, not redirect
        ("terminal", {"command": "cargo test --release >/dev/null 2>&1"}),  # discard
        ("terminal", {"command": "systemctl is-active hermes-gateway.service"}),
        ("terminal", {"command": "systemctl show hermes-gateway -p User -p Environment"}),
        ("terminal", {"command": "systemctl --user is-enabled omarchy-sleep-lock.service"}),
        ("terminal", {"command": "df -h / /run/media/lermf; free -h; nproc; uname -a"}),
        ("terminal", {"command": "lsblk -f; sudo cryptsetup status root"}),
        ("terminal", {"command": "sha256sum /tmp/x; stat -c '%a' /tmp/x"}),
        ("terminal", {"command": "journalctl -u hermes-gateway -n 20"}),
        ("terminal", {"command": "ps aux | grep hermes; ss -tlnp"}),
        ("terminal", {"command": "uptime; id; whoami; groups"}),
        ("terminal", {"command": "mount | grep storage; ip addr show"}),
        ("terminal", {"command": "cd /tmp && sed -n '10,50p' file.py"}),
        ("terminal", {"command": "python3 /tmp/tool.py --help"}),
        ("terminal", {"command": "rsync -ani --dry-run /src/ /dst/"}),
        ("terminal", {"command": "hermes doctor"}),
        ("terminal", {"command": "hermes config get approvals.mode && hermes config get model"}),
        ("terminal", {"command": "hermes cron list; hermes kanban status"}),
        ("terminal", {"command": "hermes mcp test deep-thinker"}),
        ("terminal", {"command": "hermes --profile omp config get model"}),
        ("terminal", {"command": "omarchy system stats"}),
        ("terminal", {"command": "omarchy menu keybindings --print"}),
        ("terminal", {"command": "ssh -o BatchMode=yes bundinha 'df -h /; free -h; nproc'"}),
        ("terminal", {"command": "git stash list; git tag -l"}),
        ("process", {"action": "poll", "session_id": "abc"}),
    ]
    cases_unknown: list[tuple[str, dict]] = [
        ("terminal", {}),                       # no command evidence
        ("some_new_tool", {"x": 1}),            # unknown family
        ("terminal", {"command": "make all"}),  # unrecognized shape -> never guessed
        ("terminal", {"command": "python3 - <<'EOF'\nimport sqlite3\n# ambiguous inline\nEOF"}),
        ("terminal", {"command": "python3 /tmp/unknown_script.py"}),  # script w/o hint
    ]

    fails: list[str] = []
    for tool, args in cases_mutate:
        got = classify(tool, args)
        if got != "mutation":
            fails.append(f"expected mutation for {tool} {args}, got {got!r}")
    for tool, args in cases_observe:
        got = classify(tool, args)
        if got != "observe":
            fails.append(f"expected observe for {tool} {args}, got {got!r}")
    for tool, args in cases_unknown:
        if classify(tool, args) != "":
            fails.append(f"expected UNKNOWN for {tool} {args}, got {classify(tool, args)!r}")

    # emitter format matches the harness parser anchor ^⊗S:(mutation|observe)
    import re as _re
    for intent in ("mutation", "observe"):
        line = marker_line(intent)
        if not _re.match(r"^⊗S:(mutation|observe)\b", line):
            fails.append(f"marker line {line!r} does not match harness anchor")
    if marker_line("bogus") != "":
        fails.append("marker_line must be empty for non-doctrine intents")

    print(f"SELFTEST: {'PASS' if not fails else 'FAIL'} "
          f"(mutate={len(cases_mutate)}, observe={len(cases_observe)}, unknown={len(cases_unknown)})")
    for m in fails:
        print(f"  [fail] {m}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())