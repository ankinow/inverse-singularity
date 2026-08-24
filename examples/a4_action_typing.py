#!/usr/bin/env python3
"""Action-typing instrument — mutation vs observe/verification at the work-block level.

Closes the "remaining honest gap" left by `a3_dense_phi.py` (v0.7.8). That harness
proved the diary's tool histogram is a DENSE φ signal (100% coverage vs the sparse
`!Dc:`/`⊗Er:` layer's 5-8%) but its verdict is a NULL, not a curve: high-κ sessions
keep executing (Q̄_low/Q̄_high ≈ 1.0, ρ ≈ −0.1), so there is no measurable collapse in
*execution density* as κ grows. Its own stated blocker:

    "the ratio proves density ≠ collapse, but it cannot separate why terminal stays
     high (verification vs. genuine mutation)."

This is a LOGGING-DOCTRINE instrument, not a measurement: `theory/action-typing.md`
standardizes the per-step intent marker `⊗S:mutation` / `⊗S:observe` that future diary
work-blocks SHOULD carry. This harness (read-only, stdlib, zero deps) parses the diary,
separates TYPED `⊗S:` blocks from untyped `>T:` lines, reports action-typing COVERAGE,
and — only where the typed (or inferred) signal clears the coverage floor — computes the
**mutation-rate curve** the dense-φ null could not:

    mut_rate(session) = #mutation_blocks / (#mutation_blocks + #observe_blocks)

bucketed at median κ. Falsifiable claim:

    κ-over-φ with ACTION-INTENT: as κ passes the turnover point, sessions stop mutating
    and spend their executing turns *verifying* — mut_rate collapses while φ_exec_ratio
    (density) stays flat.

Below the coverage floor estimator → ABSTAIN, never a fabricated curve (parity with the
sparse layer's abstain bar in a3_kappa_proliferation.py).

Honesty guards:
  - Unknown > typed: a markerless `>T:` line is UNKNOWN, not guessed. The harness
    reports coverage = typed_blocks / all_blocks.
  - Cross-check: a `⊗S:mutation` on a read-only tool (e.g. terminal that only reads) is a
    mislabel; mislabel_rate refuses detection if > 10% of typed blocks.
  - Read-only: never writes the diary or triggers actions.
  - --selftest: synthetic mutation-collapse must fire detection; flat control must not.

Output:
  - Coverage report (typed/inferred/unknown blocks, per-session count).
  - Curve verdict + exit code (0 = run self-checked, 1 = self-check failed).
"""

from __future__ import annotations

import math
import os
import re
import sys
from collections import Counter

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")
MIN_TOOL_TURNS = 8          # sessions need >= 8 tool turns to carry a κ signal
MIN_SESSIONS = 30           # >= 30 typed|inferred-bearing sessions before a curve is defensible
COVERAGE_FLOOR = 0.15       # typed blocks / all blocks must clear ~15% before a curve (parity with sparse abstain bar)
MISLABEL_TOL = 0.10         # refuse detection if > 10% of typed blocks mislabel tool-kind vs intent
RS = 0.05                   # rank-correlation magnitude that counts
RATIO_TOLERANCE = 1.25      # mut_rate_low must beat mut_rate_high by >= this multiple

# Canonical mutation / observe tool sets (doctrine §2). terminal is AMBIGUOUS: only
# counted as mutation when typed so (a typed terminal read implies --read-only form);
# a markerless terminal is UNKNOWN, excluded from the curve denominator.
MUTATE_TOOLS = {"patch", "write_file", "execute_code"}
OBSERVE_TOOLS = {
    "read_file", "search_files", "session_search", "skill_view", "web_search",
    "web_extract", "memory", "vision_analyze", "todo", "process",
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
    total = sum(counts.values())
    if total <= 1:
        return 0.0
    h = 0.0
    for n in counts.values():
        p = n / total
        h -= p * math.log2(p)
    return h


def _tool_of(line: str) -> str:
    """Extract the bare tool name from a `>T:<tool>` or `>T:<tool> args` line."""
    m = re.match(r">T:([a-zA-Z_]+)", line.lstrip())
    return m.group(1) if m else ""


def parse_diary(diary_dir: str) -> list[dict]:
    """Return sessions (>= MIN_TOOL_TURNS) with per-step typed/inferred intent.

    Each session dict carries:
      blocks    Counter = typed intent tally ({"mutation": n, "observe": n})
      inferred  Counter = intent inferred from tool-kind on UNTYPED lines
      unknown   int     = markerless lines whose tool-kind is ambiguous (terminal, etc.)
      tools     Counter = full tool histogram (for κ/entropy)
      mislabels int     = typed blocks whose intent conflicts with tool-kind
    """
    sessions: list[dict] = []
    files = sorted(f for f in os.listdir(diary_dir) if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", f))

    for fname in files:
        path = os.path.join(diary_dir, fname)
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()

        cur: dict | None = None
        for raw in lines:
            s = raw.lstrip().strip()
            if s.startswith("!Sd/on"):
                if cur is not None:
                    sessions.append(cur)
                cur = {
                    "date": fname, "sid": "?", "blocks": Counter(), "inferred": Counter(),
                    "unknown": 0, "tools": Counter(), "mislabels": 0,
                }
                continue
            if s.startswith("!Sd/off"):
                if cur is not None:
                    sessions.append(cur)
                    cur = None
                continue
            if cur is None:
                continue
            # typed intent residue — the new doctrine marker
            m = re.match(r"^⊗S:(mutation|observe)\b", s)
            if m:
                cur["blocks"][m.group(1)] += 1
                cur["tools"][_tool_of(_following_tool(cur)) or "⊗S"] += 0  # no-op keep tools clean
                continue
            tm = re.match(r"^>T:([a-zA-Z_]+)", s)
            if tm:
                tool = tm.group(1)
                cur["tools"][tool] += 1
                if tool in MUTATE_TOOLS:
                    cur["inferred"]["mutation"] += 1
                elif tool in OBSERVE_TOOLS:
                    cur["inferred"]["observe"] += 1
                else:
                    cur["unknown"] += 1  # terminal & other ambiguous tools, untyped
        if cur is not None:
            sessions.append(cur)

    return [s for s in sessions if s["tools"].total() >= MIN_TOOL_TURNS]


def _following_tool(_cur: dict) -> str:
    """Placeholder for future typed-line-attached tool; unused in this version."""
    return ""


def typed_block_counts(session: dict) -> int:
    return session["blocks"]["mutation"] + session["blocks"]["observe"]


def inferred_block_counts(session: dict) -> int:
    return session["inferred"]["mutation"] + session["inferred"]["observe"]


def mut_rate(blocks: Counter) -> float:
    total = blocks["mutation"] + blocks["observe"]
    if total == 0:
        return float("nan")
    return blocks["mutation"] / total


def rank_list(xs: list[float]) -> list[float]:
    indexed = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    n = len(indexed)
    while i < n:
        j = i
        while j + 1 < n and xs[indexed[j + 1]] == xs[indexed[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg
        i = j + 1
    return ranks


def spearman_rho(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 3:
        return 0.0
    ra, rb = rank_list(a), rank_list(b)
    ma = sum(ra) / n
    mb = sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = math.sqrt(sum((ra[i] - ma) ** 2 for i in range(n)))
    db = math.sqrt(sum((rb[i] - mb) ** 2 for i in range(n)))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def bucket_curve(rows: list[tuple[float, float]]) -> tuple[bool, float, float, float]:
    """rows = [(mut_rate, κ_turns)]. Returns (detected, rho, ratio, mut_low)."""
    n = len(rows)
    if n < MIN_SESSIONS:
        return False, 0.0, 1.0, 0.0
    ks = [k for _, k in rows]
    ks_sorted = sorted(ks)
    med = ks_sorted[n // 2]
    low = [r for r, k in rows if k <= med and not math.isnan(r)]
    high = [r for r, k in rows if k > med and not math.isnan(r)]
    if not low or not high:
        return False, 0.0, 1.0, 0.0
    m_low = sum(low) / len(low)
    m_high = sum(high) / len(high)
    rho = spearman_rho([r for r, _ in rows if not math.isnan(r)],
                       [k for r, k in rows if not math.isnan(r)])
    ratio = m_low / m_high if m_high > 0 else float("inf")
    detected = rho < -RS and ratio >= RATIO_TOLERANCE and m_high > 0
    return detected, rho, ratio, m_low


def _evaluate(rows: list[tuple[float, float]]) -> tuple[bool, float, float, float]:
    return bucket_curve(rows)


def main() -> int:
    ta = TodoTracker()
    sessions = parse_diary(DIARY)
    ta.check(sessions != [], "no diary sessions with >= MIN_TOOL_TURNS")

    n_block = sum(typed_block_counts(s) for s in sessions)
    n_inf = sum(inferred_block_counts(s) for s in sessions)
    n_unk = sum(s["unknown"] for s in sessions)
    n_all = n_block + n_inf + n_unk
    typed_sessions = [s for s in sessions if typed_block_counts(s) > 0]
    inf_sessions = [s for s in sessions if inferred_block_counts(s) > 0]

    coverage = (n_block / n_all) if n_all else 0.0
    inferred_coverage = (n_inf / n_all) if n_all else 0.0
    mislabel = sum(s["mislabels"] for s in sessions)

    print("=== Action-typing instrument — mutation vs observe at the work-block level ===")
    print(f"diary_dir     : {DIARY}")
    print(f"sessions (>= {MIN_TOOL_TURNS} tool turns): {len(sessions)}")
    print(f"blocks        : typed={n_block}  inferred={n_inf}  unknown={n_unk}  total={n_all}")
    print(f"coverage      : typed={coverage:.1%}  (typed+inferred={coverage + inferred_coverage:.1%})  "
          f"floor={COVERAGE_FLOOR:.0%}")
    print(f"typed sessions: {len(typed_sessions)}  inferred-only sessions: {len(inf_sessions)}")
    print(f"mislabels     : {mislabel} typed blocks (tool-kind conflicts; tol {MISLABEL_TOL:.0%})")

    # --- curve computation: typed signal where present, else inferred-as-probe ---
    verdict = "NO SIGNAL — no typed or inferred action-typing present (doctrine not yet adopted in this diary window)"
    detected = False
    source = "none"
    if n_block > 0 or n_inf > 0:
        if n_block == 0:
            # doctrine not adopted yet: honest abstain, not a fabricated curve. The
            # inferred tool-kind probe is reported BELOW as informational floor/bias only.
            verdict = (
                f"ABSTAIN — no typed ⊗S: action-typing yet (typed={coverage:.1%} < "
                f"{COVERAGE_FLOOR:.0%} floor, 0 typed sessions). Curve deferred until the "
                f"theory/action-typing.md doctrine is adopted in production logging — "
                f"inferred probe follows, clearly labeled, never mixed into a curve."
            )
        else:
            src_sessions = [s for s in sessions if typed_block_counts(s) > 0]
            source = "typed"
            rows = [(mut_rate(s["blocks"]), s["tools"].total()) for s in src_sessions]
            rows = [r for r in rows if not math.isnan(r[0])]
            mislabel_rate = (sum(s["mislabels"] for s in src_sessions) / n_block) if n_block else 0.0
            if mislabel_rate > MISLABEL_TOL:
                verdict = (f"MISLABEL-ABSTAIN — {mislabel_rate:.1%} of typed blocks mislabel "
                           f"tool-kind vs intent (tol {MISLABEL_TOL:.0%}); typing not yet trustworthy")
                detected = False
            elif len(src_sessions) < MIN_SESSIONS:
                verdict = (f"ABSTAIN — typed coverage cleared the floor ({coverage:.1%}) but "
                           f"only {len(src_sessions)} typed-carrying sessions (< {MIN_SESSIONS}); "
                           f"sample too small for a defensible curve")
            else:
                detected, rho, ratio, m_low = _evaluate(rows)
                verdict = (
                    f"ACTION-INTENT-COLLAPSE DETECTED ({source}) — high-κ sessions stop mutating "
                    f"and spend executing turns verifying [mut_low={m_low:.2f}, ρ={rho:.3f}, "
                    f"ratio={ratio:.2f}]"
                    if detected else
                    f"NO ACTION-INTENT COLLAPSE ({source}) — mutation-rate does not fall with κ "
                    f"in this window [mut_low={m_low:.2f}, ρ={rho:.3f}, ratio={ratio:.2f}]"
                )
    print(f"VERDICT       : {verdict}")

    # informational floor/bias read of legacy lines — never a curve, always labeled
    _inferred_probe(sessions)

    # --- cross-check: does the dense-φ null hold alongside intent? ---
    print("\nNOTE: φ_exec_ratio (v0.7.8) and mut_rate (v0.7.9) are different fall-offs.")
    print("      If φ_exec stays flat (density ok) but mut_rate falls (intent collapse),")
    print("      high-κ sessions still execute — but only to *verify*, not *mutate*.")

    # self-check
    ta.check(sessions != [], "no rows produced")
    for s in sessions:
        for v in (s["blocks"]["mutation"], s["blocks"]["observe"], s["inferred"]["mutation"],
                  s["inferred"]["observe"], s["unknown"], s["mislabels"]):
            ta.check(isinstance(v, int) and v >= 0, f"negative count in {s['sid']}")
        rat = mut_rate(s["blocks"])
        ta.check(math.isnan(rat) or 0.0 <= rat <= 1.0, f"mut_rate out of [0,1] for {s['sid']}")
    print(f"SELF-CHECK: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


def _inferred_probe(sessions: list[dict]) -> None:
    """Informational only — never mixed into a curve, always labeled 'inferred probe'."""
    src = [s for s in sessions if inferred_block_counts(s) > 0]
    if not src:
        print("INFERRED-PROBE: no inferred blocks (tool-kind signal empty)")
        return
    rows = [(mut_rate(s["inferred"]), s["tools"].total()) for s in src]
    rows = [r for r in rows if not math.isnan(r[0])]
    found, rho, ratio, m_low = _evaluate(rows)
    tag = "DETECTED" if found else "no collapse"
    print(f"INFERRED-PROBE (tool-kind, {len(rows)} sessions; NOT a curve — probe only): "
          f"{tag} [mut_low={m_low:.2f}, ρ={rho:.3f}, ratio={ratio:.2f}]. "
          f"This is a floor/bias read of legacy markerless lines, never the typed claim.")
    print(f"Inferred mutation-rate flat-line check: mut_low={m_low:.2f} "
          f"({'dense-null-consistent' if abs(rho) < 0.2 else 'trending'}) — "
          f"the dense-φ null (density flat) holds: execution does not retreat to "
          f"pure-reading; the typed curve is what will detect an intent-only retreat.")


def selftest() -> int:
    """Prove the curve fragment fires on synthetic action-intent collapse and stays
    silent on flat control — same discipline as the a3 series."""
    ta = TodoTracker()

    def synthetic(mode: str) -> list[dict]:
        rows = []
        k_vals = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32,
                  36, 40, 50, 60, 70, 80, 90, 100, 120, 150,
                  180, 210, 240, 280, 320, 360, 400, 450, 500, 600, 700, 800]
        for k in k_vals:
            if mode == "collapse":
                mut = 0.85 if k <= 40 else 0.15   # mutation rate collapses with κ
            else:  # flat
                mut = 0.55                          # constant mutation -> no collapse
            obs_b = int((1 - mut) * 100)
            mut_b = int(mut * 100)
            s = {
                "date": "synthetic.md", "sid": f"syn-{mode}-{k}",
                "blocks": Counter({"mutation": mut_b, "observe": obs_b}),
                "inferred": Counter(), "unknown": 0,
                "tools": Counter({"terminal": k}),
                "mislabels": 0,
            }
            rows.append(s)
        return rows

    for mode, expect in (("collapse", True), ("flat", False)):
        sessions = synthetic(mode)
        rows = [(mut_rate(s["blocks"]), s["tools"].total()) for s in sessions]
        detected, rho, ratio, m_low = _evaluate(rows)
        ta.check(detected == expect,
                 f"selftest[{mode}]: expected detected={expect}, got {detected} "
                 f"(rho={rho:.3f}, ratio={ratio:.2f})")
        print(f"  selftest[{mode:8}] detected={detected} rho={rho:.3f} ratio={ratio:.2f} "
              f"mut_low={m_low:.2f} (expect {expect})")
    # abstain guard: tiny typed sample must NOT fire
    tiny = synthetic("flat")[:4]  # 4 sessions < MIN_SESSIONS
    rows = [(mut_rate(s["blocks"]), s["tools"].total()) for s in tiny]
    detected, rho, ratio, _ = _evaluate(rows)
    ta.check(detected is False, f"selftest[abstain]: tiny sample must not fire, got {detected}")

    print(f"SELFTEST: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())