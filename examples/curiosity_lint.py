#!/usr/bin/env python3
"""Typed, deterministic ledger/linter for CURIOSITY.md.

The source stays human-authored Markdown. This tool projects each ``###`` thread
into a small typed record and rejects contradictions that prose can hide:

* the same logical thread appearing in more than one lifecycle section;
* an explicitly closed thread still living under Active;
* empty thread bodies;
* index drift between Markdown and the checked-in JSON projection.

The tool is read-only unless ``--write-index`` is passed explicitly. It uses
only the Python standard library and never decides which open thread to close.

Usage:
  python3 examples/curiosity_lint.py CURIOSITY.md
  python3 examples/curiosity_lint.py CURIOSITY.md --json
  python3 examples/curiosity_lint.py CURIOSITY.md --write-index CURIOSITY.index.json
  python3 examples/curiosity_lint.py CURIOSITY.md --check-index CURIOSITY.index.json
  python3 examples/curiosity_lint.py --selftest

Exit codes: 0 clean (or warnings without --strict), 1 policy/index findings,
2 malformed input/CLI. The default run never mutates files.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SCHEMA = "ist-curiosity-ledger/v1"
SECTION_NAMES = ("active", "simmering", "dormant")
LEVEL2_RE = re.compile(r"^##(?!#)\s+(.+?)\s*$")
THREAD_RE = re.compile(r"^###\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(?P<run>`{3,}|~{3,})(?P<rest>.*)$")
META_RE = re.compile(
    r"^\*\*(First raised|Last dispatched|Salience):\*\*\s*(.+?)\s*$",
    re.IGNORECASE,
)
STATUS_RE = re.compile(r"^\*\*Status:\s*(.+?)\*\*\s*$", re.IGNORECASE)
# Only lifecycle/status suffixes are removed. Semantic em-dash subtitles such as
# "The Delegation Boundary — A4 at the Fan-Out Layer" remain part of the key.
STATUS_SUFFIX_RE = re.compile(
    r"\s+[—–-]\s+(?:(?:EMPIRICAL|PRODUCTION|RUNTIME|IMPLEMENTATION)\s+)?"
    r"(?:TEST\s+RUN|CLOSED|RESOLVED|DECIDED|FIXED)\b.*$",
    re.IGNORECASE,
)
TERMINAL_STATUS_RE = re.compile(r"^(?:closed|resolved|fixed|decided)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ThreadRecord:
    id: str
    key: str
    title: str
    section: str
    status: str
    line_start: int
    line_end: int
    bytes: int
    first_raised: str | None
    last_dispatched: str | None
    salience: str | None
    status_note: str | None


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    lines: tuple[int, ...]


FenceState = tuple[str, int] | None


def fence_step(line: str, state: FenceState) -> tuple[FenceState, bool]:
    """Advance CommonMark-like fence state; return (state, line_is_hidden)."""
    match = FENCE_RE.match(line)
    if state is None:
        if not match:
            return None, False
        run = match.group("run")
        return (run[0], len(run)), True

    if match:
        run = match.group("run")
        char, opening_len = state
        if run[0] == char and len(run) >= opening_len and not match.group("rest").strip():
            return None, True
    return state, True


def section_name(line: str) -> str | None:
    """Return an exact lifecycle token from a level-2 heading."""
    match = LEVEL2_RE.match(line)
    if not match:
        return None
    words = set(re.findall(r"[a-z]+", match.group(1).casefold()))
    return next((name for name in SECTION_NAMES if name in words), None)


def normalize_title(title: str) -> str:
    """Stable Unicode identity key while preserving semantic subtitles."""
    title = unicodedata.normalize("NFC", title.strip())
    title = STATUS_SUFFIX_RE.sub("", title).replace("`", "").casefold()
    # Keep Greek symbols and accented letters (κ/ε/ã are semantic here); turn
    # punctuation into separators and collapse whitespace deterministically.
    return " ".join("".join(ch if ch.isalnum() else " " for ch in title).split())


def explicit_status(title: str, status_note: str | None) -> str:
    if status_note and TERMINAL_STATUS_RE.match(status_note.strip()):
        return "closed"
    if STATUS_SUFFIX_RE.search(title):
        return "closed"
    return "open"


def parse_threads(text: str) -> tuple[list[ThreadRecord], list[Finding]]:
    """Parse Markdown into typed thread records without inferring from prose."""
    raw_lines = text.splitlines(keepends=True)
    lines = [line.rstrip("\r\n") for line in raw_lines]
    starts: list[tuple[int, str, str]] = []
    heading_boundaries: list[int] = []
    section: str | None = None
    fence_state: FenceState = None
    parse_findings: list[Finding] = []

    for idx, line in enumerate(lines, start=1):
        fence_state, hidden = fence_step(line, fence_state)
        if hidden:
            continue
        level2 = LEVEL2_RE.match(line)
        if level2:
            heading_boundaries.append(idx)
            section = section_name(line)  # unrelated H2 resets lifecycle to None
            continue
        match = THREAD_RE.match(line)
        if not match:
            continue
        lifecycle = section or "unknown"
        if section is None:
            parse_findings.append(
                Finding(
                    "THREAD_OUTSIDE_LIFECYCLE",
                    "error",
                    f"thread heading outside Active/Simmering/Dormant: {match.group(1)}",
                    (idx,),
                )
            )
        starts.append((idx, match.group(1).strip(), lifecycle))

    if fence_state is not None:
        parse_findings.append(
            Finding("UNCLOSED_FENCE", "error", "Markdown code fence is not closed", ())
        )
    if not starts:
        parse_findings.append(
            Finding("NO_THREADS", "error", "no level-3 thread headings found", ())
        )

    records: list[ThreadRecord] = []
    for pos, (start, title, lifecycle) in enumerate(starts):
        next_thread = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines) + 1
        next_heading = next(
            (line_no for line_no in heading_boundaries if line_no > start),
            len(lines) + 1,
        )
        end = min(next_thread, next_heading) - 1
        # Separators belong to the document structure, not to either thread.
        while end > start and lines[end - 1].strip() in {"", "---"}:
            end -= 1
        body = lines[start:end]
        metadata: dict[str, str] = {}
        status_note: str | None = None
        body_fence: FenceState = None
        for line in body:
            body_fence, hidden = fence_step(line, body_fence)
            if hidden:
                continue
            meta = META_RE.match(line)
            if meta:
                metadata[meta.group(1).casefold()] = meta.group(2).strip()
                continue
            status = STATUS_RE.match(line)
            if status:
                status_note = status.group(1).strip()

        key = normalize_title(title)
        record_bytes = len("".join(raw_lines[start - 1 : end]).encode("utf-8"))
        records.append(
            ThreadRecord(
                id=hashlib.sha256(key.encode("utf-8")).hexdigest()[:12],
                key=key,
                title=title,
                section=lifecycle,
                status=explicit_status(title, status_note),
                line_start=start,
                line_end=end,
                bytes=record_bytes,
                first_raised=metadata.get("first raised"),
                last_dispatched=metadata.get("last dispatched"),
                salience=metadata.get("salience"),
                status_note=status_note,
            )
        )
    return records, parse_findings


def lint(
    records: Iterable[ThreadRecord],
    parse_findings: Iterable[Finding] = (),
    max_thread_bytes: int = 0,
) -> list[Finding]:
    findings = list(parse_findings)
    rows = list(records)
    by_key: dict[str, list[ThreadRecord]] = {}
    for row in rows:
        by_key.setdefault(row.key, []).append(row)

        if row.line_end <= row.line_start:
            findings.append(
                Finding(
                    "EMPTY_THREAD",
                    "error",
                    f"thread has no body: {row.title}",
                    (row.line_start,),
                )
            )
        if row.section == "active" and row.status == "closed":
            findings.append(
                Finding(
                    "ACTIVE_EXPLICITLY_CLOSED",
                    "error",
                    f"explicitly closed thread remains Active: {row.title}",
                    (row.line_start,),
                )
            )
        if row.section == "active" and not row.first_raised:
            findings.append(
                Finding(
                    "ACTIVE_MISSING_FIRST_RAISED",
                    "warning",
                    f"Active thread lacks First raised metadata: {row.title}",
                    (row.line_start,),
                )
            )
        if row.section == "active" and not row.salience:
            findings.append(
                Finding(
                    "ACTIVE_MISSING_SALIENCE",
                    "warning",
                    f"Active thread lacks Salience metadata: {row.title}",
                    (row.line_start,),
                )
            )
        if max_thread_bytes > 0 and row.bytes > max_thread_bytes:
            findings.append(
                Finding(
                    "THREAD_OVER_BUDGET",
                    "warning",
                    f"thread exceeds byte budget ({row.bytes}>{max_thread_bytes}): {row.title}",
                    (row.line_start,),
                )
            )

    for key, group in sorted(by_key.items()):
        if len(group) < 2:
            continue
        lifecycle = ", ".join(f"{r.section}@L{r.line_start}" for r in group)
        findings.append(
            Finding(
                "DUPLICATE_THREAD",
                "error",
                f"logical thread '{key}' appears {len(group)} times ({lifecycle})",
                tuple(r.line_start for r in group),
            )
        )

    return sorted(findings, key=lambda f: (0 if f.severity == "error" else 1, f.lines, f.code))


def build_document(
    source: Path,
    raw_source: bytes,
    records: list[ThreadRecord],
    findings: list[Finding],
) -> dict[str, object]:
    errors = sum(f.severity == "error" for f in findings)
    warnings = sum(f.severity == "warning" for f in findings)
    section_counts = {name: sum(r.section == name for r in records) for name in SECTION_NAMES}
    return {
        "schema": SCHEMA,
        "source": source.name,
        "source_sha256": hashlib.sha256(raw_source).hexdigest(),
        "source_bytes": len(raw_source),
        "ok": errors == 0,
        "summary": {
            "threads": len(records),
            "sections": section_counts,
            "errors": errors,
            "warnings": warnings,
            "largest_thread_bytes": max((r.bytes for r in records), default=0),
        },
        "threads": [asdict(r) for r in records],
        "findings": [asdict(f) for f in findings],
    }


def canonical_json(doc: dict[str, object]) -> str:
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def write_index_atomic(source: Path, target: Path, rendered: str) -> None:
    """Write a sibling regular file atomically; reject collisions and links."""
    source_real = source.resolve(strict=True)
    parent_real = target.parent.resolve(strict=True)
    target_real = parent_real / target.name
    if parent_real != source_real.parent:
        raise ValueError("index must be written beside its source")
    if target.is_symlink():
        raise ValueError("index target must not be a symlink")
    if target_real == source_real or (target.exists() and os.path.samefile(source_real, target)):
        raise ValueError("index target collides with source")

    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{target.name}.",
            dir=parent_real,
            delete=False,
        ) as handle:
            tmp_name = handle.name
            handle.write(rendered.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, target_real)
        tmp_name = None
    finally:
        if tmp_name is not None:
            Path(tmp_name).unlink(missing_ok=True)


def run_lint(
    source: Path,
    *,
    max_thread_bytes: int = 0,
    strict: bool = False,
    json_output: bool = False,
    write_index: Path | None = None,
    check_index: Path | None = None,
) -> int:
    try:
        raw_source = source.read_bytes()
        text = raw_source.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"curiosity-lint: cannot read {source}: {exc}", file=sys.stderr)
        return 2

    records, parse_findings = parse_threads(text)
    findings = lint(records, parse_findings, max_thread_bytes=max_thread_bytes)
    doc = build_document(source, raw_source, records, findings)
    rendered = canonical_json(doc)
    errors = int(doc["summary"]["errors"])  # type: ignore[index]
    warnings = int(doc["summary"]["warnings"])  # type: ignore[index]
    policy_failed = bool(errors or (strict and warnings))

    if check_index is not None:
        try:
            expected = check_index.read_bytes()
        except OSError as exc:
            print(f"curiosity-lint: cannot read index {check_index}: {exc}", file=sys.stderr)
            return 2
        if expected != rendered.encode("utf-8"):
            if json_output:
                print(rendered, end="")
            else:
                print(f"ERROR INDEX_DRIFT: {check_index} does not match {source}")
            return 1

    if write_index is not None:
        if policy_failed:
            print("curiosity-lint: refusing to write a policy-failing index", file=sys.stderr)
            return 1
        try:
            write_index_atomic(source, write_index, rendered)
        except (OSError, ValueError) as exc:
            print(f"curiosity-lint: cannot write index {write_index}: {exc}", file=sys.stderr)
            return 2

    if json_output:
        print(rendered, end="")
    else:
        summary = doc["summary"]
        print(
            f"CURIOSITY-LINT {'FAIL' if policy_failed else 'PASS'} "
            f"threads={summary['threads']} errors={errors} warnings={warnings} "
            f"bytes={doc['source_bytes']}"
        )
        for finding in findings:
            where = ",".join(str(n) for n in finding.lines)
            print(f"{finding.severity.upper()} {finding.code} L{where}: {finding.message}")
        if write_index is not None and not policy_failed:
            print(f"INDEX_WRITTEN {write_index}")
        if check_index is not None and not policy_failed:
            print(f"INDEX_MATCH {check_index}")

    return 1 if policy_failed else 0


def selftest() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, condition: bool) -> None:
        checks.append((name, bool(condition)))

    good = (
        "# CURIOSITY\n"
        "## Active — Currently Thinking About\n"
        "### Alpha — Semantic subtitle\n"
        "**First raised:** 2026-01-01\n"
        "**Salience:** HIGH\n"
        "Body.\n"
        "## Dormant — Later\n"
        "### Beta\n"
        "**Status: CLOSED — FIXED 2026-01-02**\n"
        "Body.\n"
    )
    good_rows, good_parse = parse_threads(good)
    good_findings = lint(good_rows, good_parse)
    check("good.clean", not [f for f in good_findings if f.severity == "error"])
    check("good.semantic_dash_preserved", good_rows[0].key == "alpha semantic subtitle")
    check("good.lifecycle_boundary", good_rows[0].line_end == 6)
    check("good.closed_status", good_rows[1].status == "closed")
    check("good.unicode_key", normalize_title("κ e Cordão") == "κ e cordão")
    check(
        "good.unicode_nfc_equivalence",
        normalize_title("Cordão") == normalize_title("Corda\u0303o"),
    )

    duplicate = (
        "# C\n"
        "## Active\n"
        "### Quantum Library vs. Context Degradation\n"
        "**First raised:** 2026-01-01\n"
        "**Salience:** HIGH\n"
        "Open.\n"
        "## Dormant\n"
        "### Quantum Library vs. Context Degradation "
        "— EMPIRICAL TEST RUN (2026-02-01)\n"
        "**Status: CLOSED (N=1)**\n"
        "Closed.\n"
    )
    dup_rows, dup_parse = parse_threads(duplicate)
    dup_findings = lint(dup_rows, dup_parse)
    check("duplicate.same_key", dup_rows[0].key == dup_rows[1].key)
    check("duplicate.detected", any(f.code == "DUPLICATE_THREAD" for f in dup_findings))

    active_closed = (
        "# C\n## Active\n### Finished\n"
        "**First raised:** now\n**Salience:** LOW\n"
        "**Status: CLOSED**\nDone.\n"
    )
    ac_rows, ac_parse = parse_threads(active_closed)
    ac_findings = lint(ac_rows, ac_parse)
    check(
        "active_closed.detected",
        any(f.code == "ACTIVE_EXPLICITLY_CLOSED" for f in ac_findings),
    )

    lifecycle_reset = (
        "# C\n## Active\n### Kept\n"
        "**First raised:** now\n**Salience:** HIGH\nBody.\n"
        "## Notes\n### Orphan\nBody.\n"
        "## Inactive\n### Also orphan\nBody.\n"
    )
    reset_rows, reset_parse = parse_threads(lifecycle_reset)
    reset_outside = [f for f in reset_parse if f.code == "THREAD_OUTSIDE_LIFECYCLE"]
    check(
        "lifecycle.unrelated_h2_resets",
        reset_rows[0].line_end == 6
        and reset_rows[1].section == "unknown"
        and len(reset_outside) == 2,
    )
    check("lifecycle.inactive_not_active", reset_rows[2].section == "unknown")

    missing_meta = """# C\n## Active\n### Metadata-free\nBody.\n"""
    mm_rows, mm_parse = parse_threads(missing_meta)
    mm_findings = lint(mm_rows, mm_parse)
    check(
        "missing_meta.warning_first",
        any(f.code == "ACTIVE_MISSING_FIRST_RAISED" for f in mm_findings),
    )
    check(
        "missing_meta.warning_salience",
        any(f.code == "ACTIVE_MISSING_SALIENCE" for f in mm_findings),
    )
    check("missing_meta.no_error", not [f for f in mm_findings if f.severity == "error"])

    oversized = lint(good_rows, good_parse, max_thread_bytes=1)
    check("budget.warning", any(f.code == "THREAD_OVER_BUDGET" for f in oversized))

    empty_rows, empty_parse = parse_threads("# CURIOSITY\n## Active\n")
    empty_findings = lint(empty_rows, empty_parse)
    check("empty_source.error", any(f.code == "NO_THREADS" for f in empty_findings))

    fenced = (
        "# C\n## Active\n### Real\n"
        "**First raised:** now\n**Salience:** HIGH\n"
        "```md\n### Fake\n## Dormant\n```\nBody.\n"
    )
    fenced_rows, fenced_parse = parse_threads(fenced)
    check("fence.headings_ignored", len(fenced_rows) == 1 and not fenced_parse)
    _, unclosed_parse = parse_threads(fenced.removesuffix("```\nBody.\n"))
    check("fence.unclosed_error", any(f.code == "UNCLOSED_FENCE" for f in unclosed_parse))

    long_fence = (
        "# C\n## Active\n### Real\n"
        "**First raised:** now\n**Salience:** HIGH\n"
        "````md\n**Status: CLOSED**\n```\n### Fake\n## Dormant\n````\nBody.\n"
    )
    long_rows, long_parse = parse_threads(long_fence)
    check(
        "fence.shorter_closer_and_metadata_ignored",
        len(long_rows) == 1
        and not long_parse
        and long_rows[0].status == "open"
        and long_rows[0].first_raised == "now",
    )

    crlf_rows, crlf_parse = parse_threads(good.replace("\n", "\r\n"))
    crlf_span = "".join(good.replace("\n", "\r\n").splitlines(keepends=True)[2:6])
    check(
        "bytes.crlf_exact_span",
        not crlf_parse and crlf_rows[0].bytes == len(crlf_span.encode("utf-8")),
    )

    with tempfile.TemporaryDirectory(prefix="curiosity-lint-") as tmp:
        root = Path(tmp)
        repo = root / "repo"
        repo.mkdir()
        src = repo / "CURIOSITY.md"
        idx = repo / "CURIOSITY.index.json"
        src.write_text(good, encoding="utf-8")
        captured_out = io.StringIO()
        captured_err = io.StringIO()
        with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
            write_rc = run_lint(src, write_index=idx)
            index_mode = idx.stat().st_mode & 0o777
            match_rc = run_lint(src, check_index=idx)

            src.write_text(good + "\n", encoding="utf-8")
            drift_rc = run_lint(src, check_index=idx)
            src.write_text(good, encoding="utf-8")

            src.write_bytes(good.replace("\n", "\r\n").encode("utf-8"))
            crlf_source_drift_rc = run_lint(src, check_index=idx)
            src.write_text(good, encoding="utf-8")

            idx.write_bytes(idx.read_bytes().removesuffix(b"\n") + b"\r\n")
            crlf_index_drift_rc = run_lint(src, check_index=idx)
            restore_rc = run_lint(src, write_index=idx)

            warning_src = repo / "WARN.md"
            warning_idx = repo / "WARN.index.json"
            warning_src.write_text(missing_meta, encoding="utf-8")
            strict_write_rc = run_lint(
                warning_src,
                strict=True,
                write_index=warning_idx,
            )

            source_before = src.read_bytes()
            collision_rc = run_lint(src, write_index=src)
            collision_unchanged = src.read_bytes() == source_before

            outside = root / "outside.json"
            outside_rc = run_lint(src, write_index=outside)

            victim = repo / "victim.txt"
            victim.write_text("untouched", encoding="utf-8")
            linked = repo / "linked.json"
            linked.symlink_to(victim.name)
            symlink_rc = run_lint(src, write_index=linked)
            victim_unchanged = victim.read_text(encoding="utf-8") == "untouched"

            hardlink = repo / "hardlink.json"
            os.link(src, hardlink)
            hardlink_rc = run_lint(src, write_index=hardlink)
            hardlink_unchanged = src.read_bytes() == source_before

        check("index.write", write_rc == 0 and idx.exists())
        check("index.mode_0644", index_mode == 0o644)
        check("index.match", match_rc == 0)
        check("index.drift", drift_rc == 1)
        check("index.source_crlf_is_drift", crlf_source_drift_rc == 1)
        check("index.own_crlf_is_drift", crlf_index_drift_rc == 1)
        check("index.restore", restore_rc == 0)
        check("strict.no_write_on_warning", strict_write_rc == 1 and not warning_idx.exists())
        check("write.source_collision_blocked", collision_rc == 2 and collision_unchanged)
        check("write.outside_parent_blocked", outside_rc == 2 and not outside.exists())
        check("write.symlink_blocked", symlink_rc == 2 and victim_unchanged)
        check("write.hardlink_blocked", hardlink_rc == 2 and hardlink_unchanged)

    failed = [name for name, ok in checks if not ok]
    print(
        json.dumps(
            {
                "schema": "ist-curiosity-ledger/selftest-v1",
                "passed": len(checks) - len(failed),
                "failed": len(failed),
                "failures": failed,
            },
            sort_keys=True,
        )
    )
    return 1 if failed else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", nargs="?", default="CURIOSITY.md")
    p.add_argument("--json", action="store_true", dest="json_output")
    p.add_argument("--strict", action="store_true", help="warnings also fail")
    p.add_argument("--max-thread-bytes", type=int, default=0, metavar="N")
    p.add_argument("--write-index", type=Path)
    p.add_argument("--check-index", type=Path)
    p.add_argument("--selftest", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.selftest:
        return selftest()
    if args.max_thread_bytes < 0:
        print("curiosity-lint: --max-thread-bytes must be >= 0", file=sys.stderr)
        return 2
    if args.write_index and args.check_index:
        print(
            "curiosity-lint: --write-index and --check-index are mutually exclusive",
            file=sys.stderr,
        )
        return 2
    return run_lint(
        Path(args.source),
        max_thread_bytes=args.max_thread_bytes,
        strict=args.strict,
        json_output=args.json_output,
        write_index=args.write_index,
        check_index=args.check_index,
    )


if __name__ == "__main__":
    raise SystemExit(main())
