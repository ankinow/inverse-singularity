#!/usr/bin/env python3
"""curiosity_kappa.py — apply A2/A3 to CURIOSITY.md's own κ.

The thread that raised this (2026-06-23, CURIOSITY.md "cure and disease share a
file") observed: *"the agent that writes anti-bloat doctrine accrues threads
faster than the foundation"* and proposed *"τ on threads — each entry timestamps
and decays, dormant threads compress to one-line pointers, active threads keep
their depth. A3 applied to my own thread file."*

That proposal was never instrumented. This harness makes the self-bloat claim
FALSIFIABLE by measuring, read-only, the κ-over-φ shape of CURIOSITY.md:

  * per-thread byte κ (dispatch history that keeps growing),
  * per-thread φ signal (whether the thread's central question is already
    CLOSED/RESOLVED/INSTRUMENTED — i.e. the "bread is done"),
  * the SELF-BLOAT verdict: threads whose κ keeps rising AFTER their φ closed.

The instrument ONLY reports. It never edits CURIOSITY.md, never decays a thread,
never prescribes. Goodhart preserved: the metric is a measurement, not a target.

Zero dependencies. stdlib only. Fail-open on parse (never guesses thread
boundaries). --selftest proves both the detection and the silence control.

Usage:
  python3 examples/curiosity_kappa.py            # live read, SELF-CHECK + verdict
  python3 examples/curiosity_kappa.py --selftest # synthetic bloat + flat control
  python3 examples/curiosity_kappa.py --json      # machine schema curiosity-kappa/v1
"""

from __future__ import annotations

import json
import os
import re
import sys

SCHEMA = "curiosity-kappa/v1"

# Lifecycle section headings (order matters; first match wins for a thread).
_SECTION_RE = re.compile(r"^##\s+(.+)$")

# Thread title under a lifecycle section.
_TITLE_RE = re.compile(r"^###\s+(.+)$")

# Metadata lines that bracket a thread's shape.
_RAISED_RE = re.compile(r"^\*\*First raised:\*\*")
_DISPATCHED_RE = re.compile(r"^\*\*Last dispatched:\*\*")
_STATUS_RE = re.compile(r"^\*\*Status:")

# φ signals — textual markers that the thread's central question is CLOSED or
# its instrument SHIPPED. These are honest surface reads, not claims of truth.
_PHI_CLOSED = (
    "CLOSED",
    "RESOLVED",
    "DECIDED (",
    "FIXED 20",
    "INSTRUMENTED",
)
_PHI_CLOSED_RE = re.compile(r"\b(?:CLOSED|RESOLVED|DECIDED)\b|\bFIXED 202\d|\bINSTRUMENTED\b")


def _find_root(path: "str | None") -> str:
    """Locate CURIOSITY.md next to this file (or accept an explicit path)."""
    if path:
        return path
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "..", "CURIOSITY.md")
    return os.path.normpath(candidate)


def parse_curiosity(text: str) -> list:
    """Parse CURIOSITY.md into (section, title, bytes, phi_closed) records.

    Thread boundaries are the `###` titles inside a `##` section. Byte cost of a
    thread runs from its title line to the next title (same section) or the next
    `##` section boundary. A dispatch-history entry is any non-title line.
    """
    records = []
    current_section = None
    current = None  # dict(title, section, start_offset_in_bytes, lines, phi_closed)

    def close(rec, end_offset):
        if rec is not None:
            rec["bytes"] = max(0, end_offset - rec["start_offset"])
            records.append(rec)

    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\n")
        m_section = _SECTION_RE.match(stripped)
        m_title = _TITLE_RE.match(stripped)
        if m_section:
            close(current, offset)
            current = None
            current_section = m_section.group(1).strip()
        elif m_title and current_section:
            close(current, offset)
            current = {
                "title": m_title.group(1).strip(),
                "section": current_section,
                "start_offset": offset,
                "phi_state": "open",
            }
        elif current is not None:
            # φ state is three-way:
            #   - `**Status:** ... CLOSED/FIXED ...`  → closed (explicit)
            #   - RESOLVED/CLOSED/DECIDED/INSTRUMENTED anywhere else → resolved
            #     (an answer exists, but the thread was never explicitly closed
            #      and may still be accumulating dispatch history)
            #   - neither → open
            if _STATUS_RE.match(stripped) and _PHI_CLOSED_RE.search(stripped):
                current["phi_state"] = "closed"
            elif current["phi_state"] != "closed" and _PHI_CLOSED_RE.search(stripped):
                current["phi_state"] = "resolved"
        offset += len(line)
    close(current, offset)
    return records


def compute(records: list) -> dict:
    """Compute κ/φ shape and the SELF-BLOAT verdict over parsed records."""
    if not records:
        return {
            "threads": 0,
            "total_bytes": 0,
            "open_threads": 0,
            "resolved_threads": 0,
            "closed_threads": 0,
            "bloated": [],
            "verdict": "NO-DATA",
        }

    total_bytes = sum(r["bytes"] for r in records)
    largest = max(records, key=lambda r: r["bytes"])
    open_threads = [r for r in records if r["phi_state"] == "open"]
    resolved_threads = [r for r in records if r["phi_state"] == "resolved"]
    closed_threads = [r for r in records if r["phi_state"] == "closed"]
    # "answered" = resolved OR explicitly closed — φ is present, the question
    # has an answer; only "open" threads still lack one.
    answered = resolved_threads + closed_threads

    # The κ-over-φ shape: an ANSWERED thread is bloated if its dispatch history
    # (byte κ) exceeds the median history of still-OPEN threads — the system is
    # spending more space on questions it already answered than on the ones it
    # has not. "starter re-fed after the bread is done."
    open_bytes = sorted(r["bytes"] for r in open_threads)
    median_open = _median(open_bytes) if open_bytes else 0
    bloated = [
        r
        for r in answered
        if r["bytes"] > max(median_open, 1)
    ]

    if bloated:
        verdict = "SELF-BLOAT"
    else:
        verdict = "NO-SELF-BLOAT"

    return {
        "threads": len(records),
        "total_bytes": total_bytes,
        "open_threads": len(open_threads),
        "resolved_threads": len(resolved_threads),
        "closed_threads": len(closed_threads),
        "largest_thread": {
            "title": largest["title"],
            "bytes": largest["bytes"],
            "phi_state": largest["phi_state"],
        },
        "bloated": [
            {"title": r["title"], "bytes": r["bytes"], "phi_state": r["phi_state"]}
            for r in bloated
        ],
        "verdict": verdict,
    }


def _median(sorted_values: list) -> float:
    n = len(sorted_values)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return sorted_values[n // 2]
    return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2.0


def main(argv: list) -> int:
    argv = list(argv)
    path = None
    want_json = False
    want_selftest = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            want_json = True
        elif a == "--selftest":
            want_selftest = True
        elif a == "--path":
            i += 1
            path = argv[i]
        elif a == "--help":
            print(__doc__)
            return 0
        i += 1

    if want_selftest:
        return _selftest()

    target = _find_root(path)
    if not os.path.isfile(target):
        _emit({"error": f"not found: {target}", "schema": SCHEMA}, want_json)
        return 2

    with open(target, "r", encoding="utf-8") as fh:
        text = fh.read()

    records = parse_curiosity(text)
    result = compute(records)
    payload = {
        "schema": SCHEMA,
        "source": target,
        "source_bytes": len(text.encode("utf-8")),
        "summary": result,
    }

    _emit(payload, want_json)

    # Exit code: SELF-BLOAT is a WARNING (exit 1) only in non-JSON human runs,
    # so a cron consumer can gate on it without the instrument ever acting.
    if result["verdict"] == "SELF-BLOAT":
        return 1 if not want_json else 0
    return 0


def _emit(payload: dict, want_json: bool) -> None:
    if want_json:
        print(json.dumps(payload, sort_keys=True))
        return
    s = payload.get("summary", {})
    if s.get("verdict") == "NO-DATA":
        print("NO-DATA: no threads parsed")
        return
    print(f"SELF-CHECK: {s['verdict']}")
    print(f"  threads={s['threads']} (open={s['open_threads']}, closed={s['closed_threads']})")
    print(f"  total_bytes={s['total_bytes']}")
    lb = s.get("largest_thread", {})
    print(f"  largest: {lb.get('title','?')[:48]} = {lb.get('bytes',0)}B "
          f"(phi_state={lb.get('phi_state')})")
    for b in s.get("bloated", []):
        print(f"  BLOAT: {b['title'][:48]} = {b['bytes']}B (phi_state={b['phi_state']})")


def _selftest() -> int:
    """Synthetic CURIOSITY.md shapes: one must fire SELF-BLOAT, one must stay silent."""
    synthetic_bloat = "\n".join([
        "## 🔥 Active — Currently Thinking About",
        "",
        "### Live Thread A",
        "**First raised:** 2026-01-01",
        "still open, short history",
        "",
        "### Live Thread B",
        "**First raised:** 2026-01-01",
        "still open",
        "",
        "## 🌙 Dormant — Haven't Returned To Recently",
        "",
        "### Old Resolved Thread",
        "**Status: CLOSED (2026-06-01)**",
        "line 1 of a long resolved history",
        "line 2",
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 7",
        "",
    ])
    synthetic_flat = "\n".join([
        "## 🔥 Active — Currently Thinking About",
        "",
        "### Live Thread A",
        "**First raised:** 2026-01-01",
        "open, keeps its depth",
        "line 2",
        "line 3",
        "line 4",
        "",
        "### Live Thread B",
        "**First raised:** 2026-01-01",
        "open and long",
        "line 2",
        "line 3",
        "line 4",
        "",
        "## 🌙 Dormant — Haven't Returned To Recently",
        "",
        "### Old Resolved Thread",
        "**Status: CLOSED (2026-06-01)**",
        "short closed history",
        "",
    ])

    bloat = compute(parse_curiosity(synthetic_bloat))
    flat = compute(parse_curiosity(synthetic_flat))

    checks = []
    checks.append(("bloat fires SELF-BLOAT", bloat["verdict"] == "SELF-BLOAT"))
    checks.append(("bloat names the closed thread", any(
        b["title"] == "Old Resolved Thread" for b in bloat["bloated"])))
    checks.append(("flat stays silent", flat["verdict"] == "NO-SELF-BLOAT"))
    checks.append(("flat parses 3 threads", flat["threads"] == 3))
    checks.append(("bloat parses 3 threads", bloat["threads"] == 3))
    # bloat's flagged thread is the explicitly-CLOSED one (phi_state closed)
    checks.append(("bloat flags closed thread", bloat["bloated"][0]["phi_state"] == "closed"))
    # flat's closed thread stays under the open median → NOT flagged
    checks.append(("flat flags nothing", flat["bloated"] == []))

    failed = [name for name, ok in checks if not ok]
    if failed:
        for name in failed:
            print(f"SELFTEST FAIL: {name}")
        return 1
    print(f"SELFTEST: PASS ({len(checks)}/{len(checks)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))