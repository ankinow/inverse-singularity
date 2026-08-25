#!/usr/bin/env python3
"""A2 tool-retention auditor — the deliberate κ-reduction intervention (ist-runtime).

Closes the other half of the κ-Proliferation thread's central question. The whole
v0.7.7/v0.7.8/v0.7.9 instrument family *measures* κ (tool-count + entropy per
session, φ-execution density, action-typing coverage). None of them *intervened* —
none answered the thread's explicit open question (first raised 2026-06-12):

  "what does a deliberate κ-reduction intervention look like — pruning skills,
   collapsing overlapping tools, enforcing a hard tool budget? This is A2 applied
   to the agent's own runtime environment."

This harness is the *decision* side, not another measurement: it asks, per tool
in the production diary, whether retaining that tool adds kit-complexity (κ)
without proportional association with execution work (φ). It transposes the
Delegation Gateway's own decision function (`Q_delegated > (1+gain)·Q_local`,
src/gateway.rs) to the *retention* decision at the single-agent level:

  RETAIN tool t  ⇔  its association with mutating work >= kit baseline
  PRUNE (candidate)
                   ⇔  tool is enriched in non-mutating (scan-only) sessions
                      past an A2 tolerance

Metric (per tool t, over diary sessions):
  n_t     = sessions using t
  m_t     = sessions using t that are *mutation-sessions*
            (a session with >= 1 patch/write_file/execute_code call — the
             A2-productive execution block, φ-relevant)
  p_kit   = mutation-sessions / all sessions          (kit mutation base rate)
  lift_t  = P(non-mutating session uses t) / P(mutating session uses t)
          = (nonmut_t / nonmut_n)   /   (mut_t / mut_n)
  lift_t > 1   ⇒ tool relatively enriched in scan-only sessions → κ-drag signal
  lift_t ≤ 1   ⇒ tool at least as associated with mutation → retained

Candidate (read-only flag, never prunes) iff, with enough signal:
  n_t >= MIN_USE          (a near-one-off has partial information — don't flag it)
  mut_n >= MIN_MUTATING   (the mutation-rate signal must be populated)
  lift_t >= DRAG_LIFT     (the A2 tolerance on scan-enrichment)

Honesty guards (same discipline as v0.7.7 .. v0.7.9, read-only / Goodhart-safe):
  - This is a *candidate* detector, not an execution order. It never prunes a
    tool and never touches a skill; it only reports which tools are, on the
    diary's own evidence, disproportionately found where no mutation happens.
  - `terminal` is deliberately EXCLUDED from the mutation-set signal's "watch"
    side issues by not counting it as mutation for lift purposes (it can be
    verification → ambiguous, per the action-typing doctrine). patch/write_file/
    execute_code are unambiguously mutation.
  - Uses the same session/tool parser as a3_dense_phi.py so numbers trace to the
    same `>T:` lines (no fabrication; every figure has a diary provenance).
  - ABSTAINS below the signal floor (MIN_MUTATING) rather than reporting a
    seductive but artifact-driven drag list.
  - A bundled `--selftest` manufactures a known drag tool (present in many
    non-mutating sessions) that MUST be flagged, and a healthy tool (used
    uniformly across mutating/non-mutating) that MUST NOT be — proving the
    detector fires precisely, not as a catch-all.

Zero deps. Stdlib only. Reads /mnt/hermes/diary (HERMES_DIARY override).

Output:
  - Per-tool table: n_t, mut_t, lift_t, kappa_marginal (kit-entropy contribution),
    and whether it is a drag candidate (read-only flag).
  - Verdict line + candidate list (blatant honesty: candidate == "worth an
    operator's second look", never an action).
  - exit 0 = self-check PASS, 1 = self-check FAIL.
"""

from __future__ import annotations

import csv
import math
import os
import re
import sys
from collections import Counter

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")
MIN_TOOL_TURNS = 8            # sessions need >= 8 tool turns to carry a kit signal
MIN_USE = 2                   # a tool needs >= 2 sessions of use to be evaluated
MIN_MUTATING = 10             # >= 10 mutation-sessions before a drag claim is ok
DRAG_LIFT = 1.50              # lift >= 1.5x scan-enrichment counts as A2 drag

# Unambiguously mutation-evidence tools (the φ-relevant execution block).
MUTATION_TOOLS = {"patch", "write_file", "execute_code"}

# Inherently read-only / observe tools (per theory/action-typing.md, the
# `⊗S:observe` family). A retrieval tool being scan-heavy is its *function*,
# not a κ-drag signal — so drag detection is scoped to tools OUTSIDE this set
# (capabilities that *could* mutate but are found where no mutation happens).
OBSERVE_TOOLS = {
    "read_file", "search_files", "skill_view", "memory", "process",
    "web_search", "web_extract", "browser_exec", "list", "poll",
}


class TodoTracker:
    """Tiny in-harness assertions so the run self-verifies (no fabric)."""

    def __init__(self) -> None:
        self._fails: list[str] = []

    def check(self, cond: bool, msg: str) -> None:
        if not cond:
            self._fails.append(msg)

    @property
    def ok(self) -> bool:
        return not self._fails


def shannon_entropy(counts: Counter) -> float:
    """Entropy in bits of a frequency distribution; 0 for empty/single."""
    total = sum(counts.values())
    if total <= 1:
        return 0.0
    h = 0.0
    for n in counts.values():
        if n <= 0:
            continue
        p = n / total
        h -= p * math.log2(p)
    return h


def parse_diary(diary_dir: str) -> list[dict]:
    """Return sessions with >= MIN_TOOL_TURNS, each with tool histogram."""
    sessions: list[dict] = []
    files = sorted(f for f in os.listdir(diary_dir) if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", f))

    for fname in files:
        path = os.path.join(diary_dir, fname)
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()

        cur: dict | None = None
        tool_hist: Counter = Counter()
        sid = "?"
        for raw in lines:
            s = raw.lstrip()
            if s.startswith("!Sd/on"):
                if cur is not None:
                    sessions.append(cur)
                mo = re.search(r"sid=(\S+)", s)
                sid = mo.group(1) if mo else f"{fname}-unknown"
                cur = {"date": fname, "sid": sid, "tools": Counter()}
                tool_hist = cur["tools"]
                continue
            if s.startswith("!Sd/off"):
                if cur is not None:
                    sessions.append(cur)
                    cur = None
                continue
            if cur is None:
                continue
            m = re.match(r"^>T:([a-zA-Z_]+)", s)
            if m:
                tool_hist[m.group(1)] += 1
        if cur is not None:
            sessions.append(cur)

    return [s for s in sessions if s["tools"].total() >= MIN_TOOL_TURNS]


def tool_lift_table(sessions: list[dict]) -> tuple[dict[str, dict], int, int, Counter]:
    """Per-tool retention table over sessions.

    A session is *mutating* iff it has >= 1 MUTATION_TOOLS call. For each tool t:
      n_t   = sessions using t
      mut_t = sessions using t that are mutating
      lift_t = (nonmut_t/nonmut_n) / (mut_t/mut_n)  — scan-enrichment ratio
    Returns (table, mut_n, nonmut_n, agg_histogram).
    """
    mut_n = sum(1 for s in sessions if any(s["tools"].get(t) for t in MUTATION_TOOLS))
    nonmut_n = len(sessions) - mut_n

    use = Counter()
    mut_use = Counter()
    for s in sessions:
        is_mut = any(s["tools"].get(t) for t in MUTATION_TOOLS)
        seen = set(s["tools"])
        for t in seen:
            use[t] += 1
            if is_mut:
                mut_use[t] += 1

    # aggregate tool histogram across sessions (for entropy + frequency display)
    agg: Counter = Counter()
    for s in sessions:
        agg.update(s["tools"])

    table: dict[str, dict] = {}
    for t, n_t in use.items():
        mut_t = mut_use[t]
        if n_t >= MIN_USE and mut_n > 0 and nonmut_n > 0:
            p_nonmut = (n_t - mut_t) / nonmut_n
            p_mut = mut_t / mut_n
            lift = (p_nonmut / p_mut) if p_mut > 0 else float("inf")
        else:
            lift = float("nan")
        table[t] = {
            "n_t": n_t,
            "mut_t": mut_t,
            "lift": lift,
            "count": agg.get(t, 0),
        }
    return table, mut_n, nonmut_n, agg


def marginal_entropy(tool: str, agg: Counter) -> float:
    """Kit-entropy contribution of tool t: H(all) - H(all without t)."""
    base = Counter(agg)
    base[tool] = 0
    return shannon_entropy(agg) - shannon_entropy(base)


def players(rows: list[dict]) -> tuple[bool, int, list[tuple[str, dict, float]]]:
    """Verdict engine (shared main/selftest). Returns
    (abstain, mut_n, candidates[(tool, row, lift)]) with lift sorted desc."""
    sessions = rows  # rows already carry 'tools' dict

    table, mut_n, _nonmut, agg = tool_lift_table(sessions)

    if mut_n < MIN_MUTATING:
        return True, mut_n, []

    cands = []
    for t, row in table.items():
        if t in OBSERVE_TOOLS:
            continue  # scan-heavy retrieval is observe-function, not drag
        lift = row["lift"]
        if math.isnan(lift):
            continue
        if lift >= DRAG_LIFT:
            me = marginal_entropy(t, agg)
            cands.append((t, row, lift))
    cands.sort(key=lambda x: x[2], reverse=True)
    return False, mut_n, cands


def report(sessions: list[dict]) -> str:
    n = len(sessions)
    table, mut_n, nonmut_n, agg = tool_lift_table(sessions)

    lines: list[str] = []
    lines.append("=== A2 tool-retention auditor — deliberate κ-reduction intervention ===")
    lines.append(f"diary_dir        : {DIARY}")
    lines.append(f"sessions (≥{MIN_TOOL_TURNS} tool turns): {n}  "
                 f"(mutating {mut_n}, non-mutating {nonmut_n})")
    if not table:
        lines.append("VERDICT: NO-DATA — no tools met the minimum-use floor.")
        return "\n".join(lines)

    # per-tool table (sorted by count desc, top 25 for readability)
    lines.append(f"{'tool':<24} {'sessions':>8} {'mut_t':>5} {'lift_t':>7} "
                 f"{'ΔH(bits)':>9}  drag?")
    ordered = sorted(table.items(), key=lambda kv: (kv[1]['count'], kv[1]['n_t']),
                     reverse=True)
    for t, row in ordered[:25]:
        me = marginal_entropy(t, agg)
        if t in OBSERVE_TOOLS:
            cand = "observe"
        else:
            cand = ("CANDIDATE" if (not math.isnan(row["lift"]) and
                                    row["lift"] >= DRAG_LIFT and
                                    mut_n >= MIN_MUTATING)
                    else ("—" if math.isnan(row["lift"]) else "retain"))
        lift_s = f"{row['lift']:.2f}" if not math.isnan(row['lift']) else "  n/a"
        lines.append(f"{t:<24} {row['count']:>8} {row['mut_t']:>5} {lift_s:>7} "
                     f"{me:>9.3f}  {cand}")

    abstain, _m, cands = players(sessions)
    if abstain:
        lines.append(f"VERDICT: ABSTAIN — only {mut_n} mutation-sessions "
                     f"(< {MIN_MUTATING}): drag detection needs a populated "
                     f"mutation signal to be defensible.")
    elif not cands:
        lines.append("VERDICT: NO KAPPA-DRAG — every retained tool is at least as "
                     "associated with mutating work as the kit baseline "
                     "(no scan-enrichment past DRAG_LIFT).")
    else:
        lines.append("VERDICT: KAPPA-DRAG CANDIDATES FLAGGED (read-only — never "
                     "auto-prune). Tools disproportionately found in non-mutating "
                     "(scan-only) sessions; worth an operator's second look "
                     f"({len(cands)} of {len(ordered)} tools met DRAG_LIFT={DRAG_LIFT:.2f}):")
        for t, _row, lift in cands:
            lines.append(f"  - {t:<22} lift={lift:.2f} (scan-enrichment past tolerance)")
    lines.append("NOTE: a flag is a *second look*, not an action. This instrument "
                 "never prunes a tool or touches a skill — it only reports that the "
                 "diary's own evidence associates the tool with non-mutation work.")
    return "\n".join(lines)


def _evaluate(rows: list[dict]) -> tuple[bool, int, list]:
    """Verdict for selftest: (abstain, mut_n, candidates)."""
    return players(rows)


def make_session(sid: str, tools: Counter) -> dict:
    return {"date": "synthetic.md", "sid": sid, "tools": tools}


def selftest() -> int:
    """Prove the detector fires precisely, not as a catch-all.

    drag:   30 sessions; 20 are non-mutating and every one uses a synthetic
            'meta_philosopher' tool; the 10 mutating sessions never use it.
            → MUST flag as drag.
    healthy: same split, but a synthetic 'core_engine' tool is used by BOTH
            mutating and non-mutating sessions proportionally → MUST NOT flag.
    sparse: a tiny sample (2 mutating sessions < MIN_MUTATING) with an
            obviously-enriched tool → MUST ABSTAIN, never fire.
    """
    ta = TodoTracker()

    # --- drag case ---
    sessions_drag = []
    # 10 mutating sessions (patch/write_file present), no meta_philosopher
    for i in range(10):
        sessions_drag.append(make_session(f"drag-mut-{i}", Counter(
            {"patch": 12, "write_file": 9, "execute_code": 3, "read_file": 30})))
    # 20 non-mutating sessions that all use meta_philosopher (pure scan)
    for i in range(20):
        sessions_drag.append(make_session(f"drag-scan-{i}", Counter(
            {"read_file": 40, "search_files": 10, "meta_philosopher": 5})))
    abstain, mut_n, cands = _evaluate(sessions_drag)
    drag_tools = {t for t, _r, _l in cands}
    ta.check(not abstain, f"drag case: expected non-abstain, got abstain (mut_n={mut_n})")
    ta.check("meta_philosopher" in drag_tools,
             f"drag case: expected meta_philosopher flagged, got {sorted(drag_tools)}")
    ta.check("patch" not in drag_tools and "read_file" not in drag_tools,
             f"drag case: read_file/patch must NOT be drag here — got {sorted(drag_tools)}")
    print(f"  selftest[drag  ] mut_n={mut_n} candidates={sorted(drag_tools)} (expect "
          f"{{'meta_philosopher'}} only)")

    # --- healthy case ---
    sessions_healthy = []
    for i in range(10):
        sessions_healthy.append(make_session(f"h-mut-{i}", Counter(
            {"patch": 12, "write_file": 9, "core_engine": 4, "read_file": 30})))
    for i in range(20):
        sessions_healthy.append(make_session(f"h-scan-{i}", Counter(
            {"read_file": 40, "search_files": 10, "core_engine": 2})))
    abstain, mut_n, cands = _evaluate(sessions_healthy)
    healthy_flags = {t for t, _r, _l in cands}
    ta.check(not abstain, f"healthy case: expected non-abstain, got abstain (mut_n={mut_n})")
    ta.check("core_engine" not in healthy_flags,
             f"healthy case: core_engine must NOT be flagged, got {sorted(healthy_flags)}")
    print(f"  selftest[health] mut_n={mut_n} candidates={sorted(healthy_flags)} "
          f"(expect no drag)")

    # --- sparse / abstain case ---
    rows_sparse = [make_session("s-mut", Counter({"patch": 9, "write_file": 7,
                                                   "spy_tool": 3, "read_file": 20})),
                   make_session("s-scan", Counter({"read_file": 40, "spy_tool": 8}))]
    abstain, mut_n, cands = _evaluate(rows_sparse)
    ta.check(abstain, f"sparse case: expected ABSTAIN (mut_n={mut_n} < "
                      f"{MIN_MUTATING}) but got candidates={sorted(cands)}")
    print(f"  selftest[sparse] mut_n={mut_n} (expect ABSTAIN, no candidates) "
          f"candidates={len(cands)}")

    print(f"SELFTEST: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


def main() -> int:
    ta = TodoTracker()
    sessions = parse_diary(DIARY)
    ta.check(sessions != [], "no diary sessions with >= MIN_TOOL_TURNS")

    print(report(sessions))

    # CSV of per-tool retention table (for downstream / operator review)
    table, mut_n, nonmut_n, agg = tool_lift_table(sessions)
    out_path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "a3_kappa_reduction.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tool", "count", "sessions", "mut_sessions", "lift",
                    "delta_entropy_bits", "drag_candidate"])
        for t, row in sorted(table.items(), key=lambda kv: kv[1]["count"], reverse=True):
            me = marginal_entropy(t, agg)
            lift = row["lift"]
            cand = "YES" if (not math.isnan(lift) and lift >= DRAG_LIFT
                             and mut_n >= MIN_MUTATING) else "no"
            w.writerow([t, row["count"], row["n_t"], row["mut_t"],
                        f"{lift:.3f}" if not math.isnan(lift) else "n/a",
                        f"{me:.4f}", cand])
    print(f"csv         : {out_path}")

    # --- self-check integrity ---
    ta.check(sessions != [], "no rows produced")
    for s in sessions:
        for t in s["tools"]:
            if t and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", t):
                ta.check(False, f"invalid tool token '{t}' in session {s['sid']}")
    # mutation-set sanity: if no session is mutating, the lift is undefined —
    # must be an abstain, which report() already handles via the floor guard.
    ta.check(mut_n >= 0, "negative mutation-session count")
    print(f"SELF-CHECK: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())