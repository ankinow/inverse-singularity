#!/usr/bin/env python3
"""κ-proliferation harness — measure the κ-over-φ threshold in production (ist-runtime).

Closes the FIRST open thread in CURIOSITY.md ("κ Proliferation in Agent
Ecosystems", raised 2026-06-12): *"can you measure the point where adding
a new capability decreases Q?"* — the afternoon refinement proposed a
time-series of (ψ, φ, ∇, Q, timestamp, context) to make dQ/dt visible and
detect the κ-over-φ threshold.

The A3 thread (v0.7.3/v0.7.5/v0.7.6) instrumented the production diary for
*deadline/compliance* shape. This harness instruments the SAME diary for the
*complexity* side: it measures whether per-effort quality (Q proxy) collapses
as a session's tool-kit complexity (κ) grows — the exact κ-over-φ curve the
thread predicted "sharp drop past a critical ratio".

Method (operationalization, honest about what the diary can say):
  - A session = the run between `!Sd/on` and `!Sd/off` (same as v0.7.3).
  - κ_turns   = `>T:*` tool-call count inside the session (complexity #1:
                raw effort/context cost).
  - κ_entropy = Shannon entropy (bits) of the session's tool-name
                distribution (complexity #2: a diverse kit ≠ a degenerate
                kit dominated by one tool). 0.0 if only one tool used.
  - φ_residue = count of the diary's *recorded-quality* markers:
                  * DECISION_NOTE (`!Dc:`) — a decision/evidence record
                    written at the end of a work block (anti-slop
                    "commit log" doctrine).
                  * ERROR_MARK  (`⊗Er:`) — an error self-reported instead
                    of silently swallowed (SOUL "Log EVERYTHING").
                These are the sparse but genuine φ proxy the diary offers:
                residue left behind per unit of effort. SOURCES MEMORY note
                (SS7): the diary under-reports errors — so φ_residue is a
                *floor*, which biases AGAINST finding a clean Q collapse
                (conservative).
  - Per-session Q proxy: Q = φ_residue / κ_turns  (marks per tool turn).

Thread question → testable claim:
  "At high κ (large tool-kit / many tool calls), per-effort quality Q
  collapses — there exists a κ turnover point past which the session's
  quality-per-effort drops."  ← the κ-over-φ threshold.

Falsifiable verdict:
  - Fit Q̄ (mean per-turn residue) in low-κ vs high-κ buckets (split at
    median κ_turns). If Q_low > Q_high by > a tolerance AND the Spearman
    rank-correlation between Q and κ_turns is negative, the threshold is
    DETECTED (κ-over-φ holds in production).
  - Guard against the sparse-φ trap: if fewer than N_sessions carry any
    φ_residue, no curve is claimed (the diary can't support it — honest
    abstention, exact parallel to v0.7.3's under-report caveat).

Zero deps. Stdlib only.

Output:
  - CSV of per-session (session_id, date, κ_turns, κ_entropy, φ_residue, Q).
  - A verdict line + exit code (0 = run self-checked, 1 = self-check failed;
    the verdict value tells which hypothesis the data favors).
"""

from __future__ import annotations

import csv
import math
import os
import re
import sys
from collections import Counter, defaultdict

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")
MIN_TOOL_TURNS = 8          # sessions need >= 8 tool turns to carry a κ signal
MIN_PHI_SHARE = 0.15        # >=15% of sessions must carry diary residue, else abstain
RS = 0.05                   # rank-correlation magnitude that counts
RATIO_TOLERANCE = 1.30      # Q_low must beat Q_high by >= this multiple


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
        p = n / total
        h -= p * math.log2(p)
    return h


def parse_diary(diary_dir: str) -> list[dict]:
    """Return sessions with >= MIN_TOOL_TURNS, each with tool histogram + φ marks."""
    sessions: list[dict] = []
    files = sorted(f for f in os.listdir(diary_dir) if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", f))

    for fname in files:
        path = os.path.join(diary_dir, fname)
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()

        cur: dict | None = None
        tool_hist: Counter = Counter()
        phi = 0
        sid = "?"
        for raw in lines:
            s = raw.lstrip()
            if s.startswith("!Sd/on"):
                # close if an unclosed previous session exists
                if cur is not None:
                    cur["phi"] = phi
                    sessions.append(cur)
                mo = re.search(r"sid=(\S+)", s)
                sid = mo.group(1) if mo else f"{fname}-unknown"
                cur = {"date": fname, "sid": sid, "tools": Counter(), "phi": 0}
                tool_hist = cur["tools"]
                phi = 0
                continue
            if s.startswith("!Sd/off"):
                if cur is not None:
                    cur["phi"] = phi
                    sessions.append(cur)
                    cur = None
                continue
            if cur is None:
                continue
            m = re.match(r"^>T:([a-zA-Z_]+)", s)
            if m:
                tool_hist[m.group(1)] += 1
                continue
            if s.startswith("!Dc:") or s.startswith("\u2297Er:"):
                phi += 1
        # flush a trailing on-without-off session
        if cur is not None:
            cur["phi"] = phi
            sessions.append(cur)

    return [s for s in sessions if s["tools"].total() >= MIN_TOOL_TURNS]


def rank_list(xs: list[float]) -> list[float]:
    """Spearman rank (average ties). Walks a sorted copy; stdlib only."""
    indexed = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and xs[indexed[j + 1]] == xs[indexed[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # average of the tied ranks (1-based)
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg
        i = j + 1
    return ranks


def spearman_rho(a: list[float], b: list[float]) -> float:
    """Spearman rank correlation between two same-length lists."""
    n = len(a)
    if n < 3:
        return 0.0
    ra, rb = rank_list(a), rank_list(b)
    ma = sum(ra) / n
    mb = sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    den_a = math.sqrt(sum((ra[i] - ma) ** 2 for i in range(n)))
    den_b = math.sqrt(sum((rb[i] - mb) ** 2 for i in range(n)))
    if den_a == 0 or den_b == 0:
        return 0.0
    return num / (den_a * den_b)


def main() -> int:
    ta = TodoTracker()
    sessions = parse_diary(DIARY)
    ta.check(sessions != [], "no diary sessions with >= MIN_TOOL_TURNS")

    rows = []
    for s in sessions:
        k = s["tools"].total()
        h = shannon_entropy(s["tools"])
        row = {
            "sid": s["sid"],
            "date": s["date"],
            "kappa_turns": k,
            "kappa_entropy": round(h, 4),
            "phi_residue": s["phi"],
            "Q": round(s["phi"] / k, 6),
            "tools": dict(s["tools"]),  # kept for the report's dominance line only
        }
        rows.append(row)

    total_phi = sum(r["phi_residue"] for r in rows)
    phi_sessions = sum(1 for r in rows if r["phi_residue"] > 0)
    n = max(len(rows), 1)
    abstain = rows and (phi_sessions / n) < MIN_PHI_SHARE

    # CSV (exclude the in-memory-only 'tools' histogram)
    csv_fields = ["sid", "date", "kappa_turns", "kappa_entropy", "phi_residue", "Q"]
    out_path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "a3_kappa_proliferation.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # --- verdict ---
    verdict = (
        "ABSTAIN — the diary's quality-residue layer is too sparse to fit a "
        "κ-over-φ curve (collect a denser φ signal first)"
    )
    detected = False
    if not abstain and rows:
        # low-κ vs high-κ bucket split at median κ_turns
        k_sorted = sorted(r["kappa_turns"] for r in rows)
        med = k_sorted[len(k_sorted) // 2]
        low = [r for r in rows if r["kappa_turns"] <= med]
        high = [r for r in rows if r["kappa_turns"] > med]
        q_low = sum(r["Q"] for r in low) / len(low)
        q_high = sum(r["Q"] for r in high) / len(high)
        rho = spearman_rho([r["Q"] for r in rows], [r["kappa_turns"] for r in rows])

        if len(rows) >= 3 and rho < -RS and q_low > 0 and (
            q_high == 0 or q_low / q_high >= RATIO_TOLERANCE
        ):
            detected = True
            verdict = (
                "KAPPA-OVER-PHI DETECTED — per-effort quality collapses past the "
                "median κ tolerance: "
            )
        else:
            verdict = (
                "NO KAPPA-OVER-PHI (within tolerance) — either no collapse or the "
                "diary residue is too spread to fit the curve "
            )

        # always report rho sign (the shape of the correlation)
        verdict += (
            f"[Q_low/Q_high="
            f"{q_low / q_high if q_high > 0 else float('inf'):.2f}, rho={rho:.3f}]"
        )

    # report
    print("=== κ-Proliferation Q harness (production Hermes diary) ===")
    print(f"diary_dir      : {DIARY}")
    print(f"sessions (>= {MIN_TOOL_TURNS} tool turns): {len(rows)}")
    print(f"total φ residue (decisions+errors): {total_phi} across {phi_sessions} sessions")
    if rows:
        ks = [r["kappa_turns"] for r in rows]
        hs = [r["kappa_entropy"] for r in rows]
        print(f"κ_turns   : min={min(ks)} med={sorted(ks)[len(ks)//2]} max={max(ks)}")
        print(f"κ_entropy : mean={sum(hs)/len(hs):.2f} bits (tool-kit diversity)")
        agg = _agg_tools(rows)
        dom = ", ".join(f"{t}:{n}" for t, n in agg[:3])
        print(f"aggregate tool dominance top-3: {dom}")
    print(f"VERDICT        : {verdict}")
    print(f"csv           : {out_path}")

    # --- sparsity diagnostics (dense; always computable) ---
    if rows:
        rho_res = sorted([r["kappa_turns"] for r in rows])
        med = rho_res[len(rho_res) // 2]
        resid_sessions = [r for r in rows if r["phi_residue"] > 0]
        short_resid = sum(1 for r in resid_sessions if r["kappa_turns"] <= med)
        n_resid = len(resid_sessions)
        if n_resid:
            print("=== sparsity diagnostics (residue concentration) ===")
            print(f"residue sessions: {n_resid} | of those, {short_resid} are at-or-below "
                  f"median κ ({med}): {short_resid / n_resid * 100:.0f}%")
            print("NOTE: if residue concentrates in SHORT sessions, long sessions run with "
                  "zero recorded decision/error marks — itself a transparency finding "
                  "(see SS7 under-report quirk), not a measured κ-over-φ curve.")
        else:
            print("=== sparsity diagnostics: no session carries any residue — "
                  "the diary records neither decisions nor errors for this window ===")

    # self-check
    ta.check(rows != [], "no rows produced")
    ta.check(total_phi >= 0, "negative φ residue")
    for r in rows:
        ta.check(0.0 <= r["Q"] <= 1.0, f"Q out of per-session [0,1] for {r['sid']}")
    print(f"SELF-CHECK: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


def _agg_tools(rows: list[dict]) -> list[tuple[str, int]]:
    agg: Counter = Counter()
    for r in rows:
        agg.update(r["tools"])
    return agg.most_common()


def selftest() -> int:  # noqa: C901
    """Prove the verdict engine fires on a DENSE synthetic κ-over-φ signal.

    Runs two synthetic diaries through the same bucketing/correlation logic:
      * collapse-manufactured: short sessions carry lots of residue, long
        sessions carry ~none -> the engine must claim KAPPA-OVER-PHI.
      * flat: residue spread evenly across κ -> the engine must NOT falsely
        claim a sharp threshold.
    This guards the harness against the abort-trap where ABSTAIN becomes a
    silent catch-all hiding broken detection logic.
    """
    ta = TodoTracker()

    def synthetic(mode: str) -> list[dict]:
        rows: list[dict] = []
        for k in (8, 10, 12, 14, 16, 18, 20, 40, 60, 80, 120, 200, 300, 400):
            if mode == "collapse":
                # short sessions carry residue, long sessions carry none
                phi = 3 if k <= 20 else 0
            else:  # flat-control: quality is CONSTANT (Q=1.0) at every κ
                phi = k  # Q = phi/k = 1.0 exactly -> rho=0, ratio=1.0
            rows.append({
                "sid": f"syn-{mode}-{k}", "date": "synthetic.md",
                "kappa_turns": k, "kappa_entropy": 2.0,
                "phi_residue": phi, "Q": round(phi / k, 6),
                "tools": {"terminal": k},  # single-tool; entropy probe only
            })
        return rows

    for mode, expect_detected in (("collapse", True), ("flat", False)):
        rows = synthetic(mode)
        n = len(rows)
        phi_sessions = sum(1 for r in rows if r["phi_residue"] > 0)
        if (phi_sessions / n) < MIN_PHI_SHARE:
            # engine correctly abstains on sparse -> treat as not-detected
            detected = False
        else:
            k_sorted = sorted(r["kappa_turns"] for r in rows)
            med = k_sorted[n // 2]
            low = [r for r in rows if r["kappa_turns"] <= med]
            high = [r for r in rows if r["kappa_turns"] > med]
            q_low = sum(r["Q"] for r in low) / len(low)
            q_high = sum(r["Q"] for r in high) / len(high)
            rho = spearman_rho([r["Q"] for r in rows], [r["kappa_turns"] for r in rows])
            detected = (
                n >= 3 and rho < -RS and q_low > 0
                and (q_high == 0 or q_low / q_high >= RATIO_TOLERANCE)
            )
        ta.check(detected == expect_detected,
                 f"selftest {mode}: expected detected={expect_detected}, got {detected}")
        print(f"  selftest[{mode:9}] detected={detected} (expect {expect_detected})")

    print(f"SELFTEST: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())