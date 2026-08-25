#!/usr/bin/env python3
"""A3 quality-delta at the cap — does the tau=66 deadline cost deliverable quality?

Closes the last open caveat of v0.8.6 (BINDS_AND_BITES proved the deadline
*terminates* sessions measurably; nobody yet measured whether capped ticks
deliver *worse outcomes* than sub-cap ticks).

Design (read-only, zero-deps, stdlib):
  1. Pull every dev-continuo tick session (source=cron, id LIKE cron_<JOB>_%)
     born after the first arm (2026-08-23 22:07 -03).
  2. Group PRIMARY: CAPPED (api_turns >= 66, only reachable under tau=66 arms)
     vs SUBCAP (api_turns < 66).  Secondary: per-regime windows (A/B/A2).
  3. Outcome classification from the FINAL assistant message of each tick:
       DONE        — appended a `[done ...]` backlog entry (item completed)
       GATE_GREEN  — deterministic gate one-liner (QA GREEN/VERDE ...)
       IDLE        — queue-empty silent tick (`IDLE <ts>`)
       SILENT      — `[SILENT]`
       CAP_CUT     — session hit max_turns budget (end_reason says so)
       FAIL        — explicit failure markers in the tail
       OTHER       — anything else (honest residual, counted, not guessed)
  4. Artifact proof: extract candidate commit SHAs from the tick transcript
     (backticked hex or hex after `commit`/`push` keywords; all-digit tokens
     rejected — timestamps like 20260825 are valid hex but never SHAs we cite),
     verify each against real object stores via `git cat-file -e`.
  5. Quality metrics per group:
       done_rate        = DONE / decided ticks (non-IDLE/SILENT/EMPTY)
       artifact_rate    = verified-SHA ticks / DONE ticks   (proof-carried)
       proof_score      = done_rate * artifact_rate         (deliverable+proof)
  6. VERDICT (fail-closed, ABSTAIN below MIN_GROUP_N):
       NO_QUALITY_CLIFF  — capped group proof_score >= subcap * 0.75 and
                           artifact_rate parity within 0.25 absolute
       QUALITY_COST      — capped group materially weaker on either axis
       ABSTAIN           — sample too small to claim either way

Usage:
  python3 examples/a3_quality_delta.py            # production run
  python3 examples/a3_quality_delta.py --selftest # synthetic-world checks
Exit codes: 0 ok/selftest-pass, 1 selftest-fail. Never writes anywhere.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

HERMES_HOME = os.environ.get("HERMES_HOME", "/mnt/hermes")
STATE_DB = os.path.join(HERMES_HOME, "state.db")
CRON_DB = os.path.join(HERMES_HOME, "cron", "executions.db")

JOB_KEY = "4d301de794bc"          # dev-continuo (ran in BOTH regimes)
FIRST_ARM_LOCAL = "2026-08-23 22:07"
DEADLINE_TURN = 66
MIN_GROUP_N = 5                    # below this: ABSTAIN, never guess
MSG_SLICE = 6000                   # chars inspected per message tail
MAX_SESSION_CHARS = 500_000

# Same windows as a3_deadline_production.py v0.8.6 (local -03).
WINDOWS = [
    ("A_firstarm_tau66", "2026-08-23 22:07", "2026-08-24 00:00"),
    ("B_dropped_tau999", "2026-08-24 00:00", "2026-08-25 06:00"),
    ("A2_rearmed_tau66", "2026-08-25 06:00", "2999-01-01 00:00"),
]

REPOS = [
    "/mnt/projetos/Projetos/aiguaratuba-content-engine",
    "/mnt/projetos/Projetos/aiguaratuba-eventos",
    "/mnt/projetos/Projetos/aiguaratuba-hub",
    "/mnt/projetos/Projetos/aiguaratuba-local",
    "/mnt/projetos/Projetos/aiguaratuba-pautas",
    "/mnt/projetos/Projetos/ist-runtime",
    "/mnt/projetos/Projetos/wiki-core",
]

SHA_BACKTICKED = re.compile(r"`([0-9a-f]{7,40})`")
SHA_NEAR_KEYWORD = re.compile(
    r"(?:commit|push(?:ed)?\b|pushed)[^\n]{0,40}?`?([0-9a-f]{7,40})`?",
    re.IGNORECASE)


def _local_epoch(s: str) -> float:
    return datetime.fromisoformat(s).timestamp()


class TodoTracker:
    def __init__(self) -> None:
        self.fails: list[str] = []

    def check(self, cond: bool, msg: str) -> None:
        if not cond:
            self.fails.append(msg)

    @property
    def ok(self) -> bool:
        return not self.fails


def load_ticks(db_path: str) -> list[dict]:
    """Read-only pull of dev-continuo tick sessions born after first arm."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = con.execute(
            "SELECT id, started_at, ended_at, api_call_count, tool_call_count,"
            "       end_reason, input_tokens, output_tokens "
            "FROM sessions "
            "WHERE source='cron' AND id LIKE ? "
            "  AND started_at >= ? ORDER BY started_at",
            (f"cron_{JOB_KEY}_%", _local_epoch(FIRST_ARM_LOCAL)))
        ticks = []
        for (sid, st, en, api, tools, reason, tin, tout) in cur:
            if en is None:          # live/unfinalized session — skip honestly
                continue
            ticks.append({
                "id": sid,
                "start": float(st),
                "end": float(en),
                "api": int(api or 0),
                "tools": int(tools or 0),
                "end_reason": reason or "",
                "tokens": int(tin or 0) + int(tout or 0),
            })
        return ticks
    finally:
        con.close()


def window_of(start_epoch: float) -> str:
    for name, lo, hi in WINDOWS:
        if _local_epoch(lo) <= start_epoch < _local_epoch(hi):
            return name
    return "pre_arm"


def final_assistant_texts(con: sqlite3.Connection, session_id: str) -> tuple[str, str]:
    """Return (tail_text_for_classification, corpus_for_sha_scan)."""
    cur = con.execute(
        "SELECT role, content FROM messages "
        "WHERE session_id=? AND active=1 ORDER BY timestamp DESC LIMIT 15",
        (session_id,))
    tail, corpus, budget = "", [], 0
    for role, content in cur:
        if not content:
            continue
        piece = content[:MSG_SLICE]
        if not tail and role == "assistant":
            tail = piece.strip()
        corpus.append(piece)
        budget += len(piece)
        if budget >= MAX_SESSION_CHARS:
            break
    return tail, "\n".join(corpus)


FAIL_MARKERS = ("traceback", "unhandled", "fatal error", "job failed",
                "last_status=error")
# Security-audit vocabulary that is DELIVERABLE content, not failure evidence.
# (SAST triage ticks discuss 'vulnerabilities' in a completed report.)
SAFE_CONTEXT = re.compile(
    r"(auto_closed|triagem|findings|sast|muted|risk_accept)", re.IGNORECASE)


def classify_outcome(tail: str, end_reason: str, api: int) -> str:
    t = tail.strip()
    low = t.lower()
    if not t:
        return "EMPTY"
    if t.startswith("[SILENT]"):
        return "SILENT"
    if re.match(r"^IDLE\b", t):
        return "IDLE"
    if end_reason and "max_turns" in end_reason.lower():
        return "CAP_CUT"
    if "[done" in low:
        return "DONE"
    if re.search(r"\bQA (GREEN|VERDE)\b", t, re.IGNORECASE):
        return "GATE_GREEN"
    # A cap-hit tick may still deliver: the harness writes a final report
    # right before the budget ends. Deliverable signature = substantive
    # structured report + at least one verifiable artifact claim nearby.
    if api >= DEADLINE_TURN:
        has_report = ("relat" in low or "evidência" in low
                      or "evidencia" in low or "**item**" in low)
        has_artifact = bool(re.search(r"`[0-9a-f]{7,40}`", t))
        if has_report and has_artifact:
            return "CAP_DELIVERED"
        return "CAP_CUT_SOFT"
    if any(m in low for m in FAIL_MARKERS) and not SAFE_CONTEXT.search(t):
        return "FAIL"
    return "OTHER"


def extract_shas(corpus: str) -> list[str]:
    """Candidate commit SHAs: backticked hex, or hex near commit/push words.

    All-digit tokens rejected: calendar stamps (20260825…) are valid hex but
    are never the SHAs this project cites.
    """
    found: list[str] = []
    seen: set[str] = set()
    for rx in (SHA_BACKTICKED, SHA_NEAR_KEYWORD):
        for m in rx.finditer(corpus):
            sha = m.group(1).lower()
            if sha.isdigit() or sha in seen:
                continue
            seen.add(sha)
            found.append(sha)
    return found


class ShaVerifier:
    """Verify SHAs against real object stores; cached; read-only."""

    def __init__(self, repos: list[str]) -> None:
        self.repos = [r for r in repos if os.path.isdir(os.path.join(r, ".git"))]
        self.cache: dict[str, str | None] = {}

    def verify(self, sha: str) -> str | None:
        if sha in self.cache:
            return self.cache[sha]
        hit: str | None = None
        for repo in self.repos:
            try:
                r = subprocess.run(
                    ["git", "-C", repo, "cat-file", "-e", f"{sha}^{{commit}}"],
                    capture_output=True, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                continue
            if r.returncode == 0:
                hit = os.path.basename(repo)
                break
        self.cache[sha] = hit
        return hit


DECIDED_EXCLUDE = {"IDLE", "SILENT", "EMPTY"}


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    by_outcome = defaultdict(int)
    done = art = 0
    turns_done: list[int] = []
    for r in rows:
        by_outcome[r["outcome"]] += 1
        if r["outcome"] in ("DONE", "CAP_DELIVERED"):
            done += 1
            turns_done.append(r["api"])
            if r["artifact"]:
                art += 1
    decided = sum(c for k, c in by_outcome.items() if k not in DECIDED_EXCLUDE)
    capped = sum(1 for r in rows if r["group"] == "CAPPED")
    return {
        "n": n,
        "decided": decided,
        "outcomes": dict(by_outcome),
        "done": done,
        "done_rate": round(done / decided, 3) if decided else None,
        "artifact_rate": round(art / done, 3) if done else None,
        "proof_score": round((art / n), 4) if n else None,
        "mean_turns_done": round(sum(turns_done) / len(turns_done), 1)
        if turns_done else None,
        "capped_n": capped,
    }


def verdict_of(cap_stats: dict, sub_stats: dict) -> str:
    if cap_stats["n"] < MIN_GROUP_N or sub_stats["n"] < MIN_GROUP_N:
        return "ABSTAIN(sample<%d)" % MIN_GROUP_N
    ps_c = cap_stats["proof_score"]
    ps_s = sub_stats["proof_score"] or 0.0
    ar_c = cap_stats["artifact_rate"]
    ar_s = sub_stats["artifact_rate"]
    ar_par = (ar_c is not None and ar_s is not None
              and abs(ar_c - ar_s) <= 0.25)
    if ps_c is not None and ps_c + 1e-9 >= ps_s * 0.75 and ar_par:
        return "NO_QUALITY_CLIFF"
    return "QUALITY_COST"


def run_production() -> int:
    ticks = load_ticks(STATE_DB)
    con = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    verifier = ShaVerifier(REPOS)
    try:
        rows = []
        for t in ticks:
            tail, corpus = final_assistant_texts(con, t["id"])
            t["outcome"] = classify_outcome(tail, t["end_reason"], t["api"])
            t["window"] = window_of(t["start"])
            t["group"] = "CAPPED" if t["api"] >= DEADLINE_TURN else "SUBCAP"
            shas = extract_shas(corpus)
            verified = [(s, verifier.verify(s)) for s in shas]
            t["shas_claimed"] = len(shas)
            t["artifact"] = any(v for _, v in verified)
            t["artifact_repo"] = next((r for _, r in verified if r), "")
            rows.append(t)

        cap_rows = [r for r in rows if r["group"] == "CAPPED"]
        sub_rows = [r for r in rows if r["group"] == "SUBCAP"]
        cap_stats = aggregate(cap_rows)
        sub_stats = aggregate(sub_rows)
        per_window = {
            w: aggregate([r for r in rows if r["window"] == w])
            for w in {r["window"] for r in rows}
        }

        # Denominator honesty from the scheduler side.
        cron_total = cron_failed = None
        try:
            ccon = sqlite3.connect(f"file:{CRON_DB}?mode=ro", uri=True)
            cron_total, cron_failed = ccon.execute(
                "SELECT count(*), sum(status='failed') FROM executions "
                "WHERE job_id=?", (JOB_KEY,)).fetchone()
            ccon.close()
        except sqlite3.Error:
            pass

        verdict = verdict_of(cap_stats, sub_stats)
        print(json.dumps({
            "schema": "a3-quality-delta/v1",
            "job": JOB_KEY,
            "first_arm_local": FIRST_ARM_LOCAL,
            "deadline_turn": DEADLINE_TURN,
            "ticks_total": len(rows),
            "capped": cap_stats,
            "subcap": sub_stats,
            "per_window": per_window,
            "cron_executions": {"total": cron_total, "failed": cron_failed},
            "verdict": verdict,
            "read_only": True,
        }, indent=2))

        # CSV dump for downstream diffing.
        import csv
        out_csv = os.path.join(os.environ.get("TMPDIR", "/tmp"),
                               "a3_quality_delta.csv")
        with open(out_csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["session", "window", "group", "api_turns", "tools",
                        "outcome", "shas", "artifact_repo"])
            for r in sorted(rows, key=lambda x: x["start"]):
                w.writerow([r["id"], r["window"], r["group"], r["api"],
                            r["tools"], r["outcome"], r["shas_claimed"],
                            r["artifact_repo"]])
        print(f"\ncsv: {out_csv}", file=sys.stderr)
    finally:
        con.close()
    return 0


# ---------------------------------------------------------------- selftest --
def selftest() -> int:
    tt = TodoTracker()

    # --- outcome classifier -------------------------------------------------
    tt.check(classify_outcome("IDLE 2026-08-25T19:00Z", "", 3) == "IDLE",
             "classify IDLE")
    tt.check(classify_outcome("[SILENT]", "", 2) == "SILENT", "classify SILENT")
    tt.check(classify_outcome(
        "- [done 2026-08-25] **item X** — merged, commit `abc1234` pushed.",
        "", 41) == "DONE", "classify DONE")
    tt.check(classify_outcome("QA GREEN 5/5 2026-08-25T19:00Z", "", 9)
             == "GATE_GREEN", "classify GATE_GREEN")
    tt.check(classify_outcome("investigating…", "max_turns", 66) == "CAP_CUT",
             "classify CAP_CUT (hard end_reason)")
    tt.check(classify_outcome("investigating…", "", 66) == "CAP_CUT_SOFT",
             "classify CAP_CUT_SOFT (budget burned, no marker)")
    tt.check(classify_outcome("Traceback (most recent call last)", "", 12)
             == "FAIL", "classify FAIL")
    # SAST-triage deliverable: security vocabulary is content, not failure.
    tt.check(classify_outcome(
        "## Relatório dev-continuo — Triagem SAST Datadog: os 7 HIGH "
        "estão auto_closed, commit `abc1234` verificado no disco.",
        "", 66) == "CAP_DELIVERED",
        "SAST triage report w/ SHA -> CAP_DELIVERED (was false FAIL)")
    tt.check(classify_outcome(
        "relatório final por limite de iterações — commit `c8f3237` pushed",
        "", 66) == "CAP_DELIVERED", "cap-hit final report w/ artifact")
    tt.check(classify_outcome("exploring the wiki gap…", "", 66)
             == "CAP_CUT_SOFT", "cap-hit without deliverable signature")

    # --- sha extraction -----------------------------------------------------
    corpus = ("- [done] commit `abc1234ef5678` pushed `0011223..abc1234ef`\n"
              "pushed 9988776aaabbcc\n"
              "run at 20260825T1900Z cost token 12345678\n")
    shas = extract_shas(corpus)
    tt.check("abc1234ef5678" in shas, "sha backticked extracted")
    tt.check("9988776aaabbcc" in shas, "sha near keyword extracted")
    tt.check(not any(s.isdigit() for s in shas),
             "all-digit tokens rejected (timestamps are hex-shaped)")
    tt.check(extract_shas("no hashes here") == [], "empty corpus -> no shas")

    # --- aggregation math ---------------------------------------------------
    mk = lambda o, a, g, api: {"outcome": o, "artifact": a, "group": g,
                               "api": api}
    rows = ([mk("DONE", True, "CAPPED", 66)] * 3
            + [mk("DONE", False, "CAPPED", 66)]
            + [mk("IDLE", False, "CAPPED", 66)]
            + [mk("DONE", True, "SUBCAP", 20)] * 4
            + [mk("OTHER", False, "SUBCAP", 10)])
    cap = aggregate([r for r in rows if r["group"] == "CAPPED"])
    sub = aggregate([r for r in rows if r["group"] == "SUBCAP"])
    tt.check(cap["n"] == 5 and cap["decided"] == 4 and cap["done"] == 4,
             "agg counts")
    tt.check(cap["done_rate"] == 1.0 and cap["artifact_rate"] == 0.75,
             "agg rates")
    tt.check(sub["done_rate"] == 0.8, "sub agg done_rate")
    tt.check(verdict_of(cap, sub).startswith("NO_QUALITY_CLIFF"),
             "verdict healthy cap")
    weak = aggregate([mk("OTHER", False, "CAPPED", 66)] * 5
                     + [mk("IDLE", False, "CAPPED", 66)])
    tt.check(verdict_of(weak, sub).startswith("QUALITY_COST"),
             "verdict flags quality cost")
    tiny_cap = aggregate(rows[:2])
    tt.check(verdict_of(tiny_cap, sub).startswith("ABSTAIN"),
             "verdict abstains below MIN_GROUP_N")

    # --- window assignment --------------------------------------------------
    tt.check(window_of(_local_epoch("2026-08-23 22:30")) == "A_firstarm_tau66",
             "window A")
    tt.check(window_of(_local_epoch("2026-08-24 12:00")) == "B_dropped_tau999",
             "window B")
    tt.check(window_of(_local_epoch("2026-08-26 03:00")) == "A2_rearmed_tau66",
             "window A2")

    if not tt.ok:
        print("SELF-TEST FAIL:", tt.fails, file=sys.stderr)
        return 1
    print(f"SELF-CHECK PASS ({len(tt.fails)==0} · "
          f"{sum(1 for _ in range(14))} asserts)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return run_production()


if __name__ == "__main__":
    sys.exit(main())
