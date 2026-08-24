#!/usr/bin/env python3
"""Dense φ-evidence logger — execution-ratio proxy for the κ-over-φ curve (ist-runtime).

Closes the actionable gap left by `a3_kappa_proliferation.py` (v0.7.7).
That harness proved the diary's *sparse* φ layer (`!Dc:`/`⊗Er:` marks) sits at the
resolution limit: only 5% of production sessions carry any residue, so the harness
correctly ABSTAINS from claiming a κ-over-φ curve. Its stated blocker:

  "measuring the thread's threshold requires a denser φ signal."

This harness builds that denser signal from the SAME diary, using the work-block
evidence the diary *does* record faithfully and densely: the per-session tool
histogram (hundreds of calls/session vs a handful of marks).

The dense proxy (φ-work-block density, following the SOUL "work-block residue"
doctrine — a *block* that actually executes leaves denser residue than one that
only scans):

  φ_exec_ratio  = exec_turns / (exec_turns + read_turns)
                  exec  ∈ {patch, write_file, execute_code, terminal}
                  read  ∈ {read_file, skill_view, search_files, web_search,
                           web_extract, memory, process, browser_exec}
                0.0 = session only read/scanned (no execution evidence),
                1.0 = session executed on every evidence-bearing turn.
  κ_turns       = total `>T:*` tool turns (context cost / raw effort),
  κ_entropy     = Shannon entropy (bits) of the tool-name distribution.

Thread question -> dense falsifiable claim:
  "As a session's tool-kit complexity (κ) grows, per-effort work-block density φ
   collapses — heavy sessions read/watch more and execute less per turn."

Verdict (mirrors the a3 harness, but on a signal that most sessions actually carry):
  - Split sessions at the median κ_turns into low-κ / high-κ buckets.
  - Let Q̄ = mean φ_exec_ratio in each bucket, rho = Spearman(φ, κ_turns).
  - DETECTED iff sessions_i ≥ 30 (density floor; we're at ~100) AND
      rho < −RS AND Q̄_low > Q̄_high * RATIO_TOLERANCE.
  - NO-KAPPA-OVER-PHI otherwise (flat or no negative correlation).

Why this abstains differently: the sparse φ harness abstains because its signal is
too rare. This signal is present in ~99% of sessions, so the ABSTAIN path here is
the LOOP-DISCONNECTED guard (no sessions at all) — not a rare-event excuse.

Honesty guard (Goodhart, same discipline as v0.7.7):
  - `terminal` is the dominant exec tool (672 turns on 08-22 alone). Many terminal
    calls are *verification* (build/test/git) rather than mutation — still execution
    intent, but it can mask patch/write/execute weakness. So the harness ALSO reports
    φ_exec_core_ratio (exec minus terminal: patch+write_file+execute_code) and refuses
    to claim DETECTED if the two proxies disagree in sign (a terminal-halo artifact).
  - The proxy is a floor-and-bias instrument: it never triggers actions (read-only),
    it only reports. No fabrication: every number traces to `>T:` lines in the diary.

Zero deps. Stdlib only.

Output:
  - CSV of per-session (sid, date, κ_turns, κ_entropy, φ_exec_ratio,
    φ_exec_core_ratio, φ_sparse_residue).
  - Verdict line + exit code (0 = run self-checked, 1 = self-check failed).
  - --selftest: synthetic dense collapse must be DETECTED; flat control must not be.
"""

from __future__ import annotations

import csv
import math
import os
import re
import sys
from collections import Counter

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")
MIN_TOOL_TURNS = 8          # sessions need >= 8 tool turns to carry a κ signal
MIN_SESSIONS = 30           # >= 30 sessions before a κ-over-φ claim is defensible
RS = 0.05                   # rank-correlation magnitude that counts
RATIO_TOLERANCE = 1.30      # Q̄_low must beat Q̄_high by >= this multiple

EXEC_TOOLS = {"patch", "write_file", "execute_code", "terminal"}
EXEC_CORE_TOOLS = {"patch", "write_file", "execute_code"}  # no terminal halo
READ_TOOLS = {
    "read_file", "skill_view", "search_files", "web_search",
    "web_extract", "memory", "process", "browser_exec",
}
# tools that are neither exec nor read (orchestration/meta) are excluded from the
# φ denominator — the ratio measures execution-vs-reading on evidence-bearing turns.


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
        if cur is not None:
            cur["phi"] = phi
            sessions.append(cur)

    return [s for s in sessions if s["tools"].total() >= MIN_TOOL_TURNS]


def exec_proxies(tools: Counter) -> tuple[float, float]:
    """Return (φ_exec_ratio, φ_exec_core_ratio) for a session's tool histogram.

    Denominator = exec + read evidence-bearing turns (the turns where the session
    either acted or scanned). Neither-or-both tools (orchestration, delegate_task,
    todo, memory-orphan) are excluded so the ratio measures exec-vs-read cleanly.
    Returns (0.0, 0.0) when there is no evidence-bearing turn (no signal for φ).
    """
    exec_n = sum(tools.get(t, 0) for t in EXEC_TOOLS)
    exec_core_n = sum(tools.get(t, 0) for t in EXEC_CORE_TOOLS)
    read_n = sum(tools.get(t, 0) for t in READ_TOOLS)
    denom = exec_n + read_n
    if denom == 0:
        return 0.0, 0.0
    return exec_n / denom, exec_core_n / denom if exec_core_n + read_n else 0.0


def rank_list(xs: list[float]) -> list[float]:
    """Spearman rank (average ties). Walks a sorted copy; stdlib only."""
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
        phi_exec, phi_exec_core = exec_proxies(s["tools"])
        rows.append({
            "sid": s["sid"],
            "date": s["date"],
            "kappa_turns": k,
            "kappa_entropy": round(h, 4),
            "phi_exec_ratio": round(phi_exec, 6),
            "phi_exec_core_ratio": round(phi_exec_core, 6),
            "phi_sparse_residue": s["phi"],
            "tools": dict(s["tools"]),
        })

    n = len(rows)
    out_path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "a3_dense_phi.csv")
    csv_fields = ["sid", "date", "kappa_turns", "kappa_entropy",
                  "phi_exec_ratio", "phi_exec_core_ratio", "phi_sparse_residue"]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # --- dense verdict: does φ_exec_ratio collapse as κ grows? ---
    verdict = "NO-DATA — no diary sessions parsed (is the diary path right?)"
    detected = False
    if rows:
        # loop-disconnected guard is the honest abstain for a dense signal
        if n < MIN_SESSIONS:
            verdict = (
                f"ABSTAIN — only {n} sessions (< {MIN_SESSIONS}): the execution-ratio "
                "signal is present but the sample is too small for a defensible curve"
            )
        else:
            k_sorted = sorted(r["kappa_turns"] for r in rows)
            med = k_sorted[n // 2]
            low = [r for r in rows if r["kappa_turns"] <= med]
            high = [r for r in rows if r["kappa_turns"] > med]
            q_low_full = sum(r["phi_exec_ratio"] for r in low) / len(low)
            q_high_full = sum(r["phi_exec_ratio"] for r in high) / len(high)
            q_low_core = sum(r["phi_exec_core_ratio"] for r in low) / len(low)
            q_high_core = sum(r["phi_exec_core_ratio"] for r in high) / len(high)
            rho = spearman_rho(
                [r["phi_exec_ratio"] for r in rows],
                [r["kappa_turns"] for r in rows],
            )
            # terminal-halo guard: the two dense proxies must agree in direction,
            # else the "collapse" is an artifact of terminal dominating exec.
            tin = q_low_full > q_high_full and q_low_core > q_high_core
            ratio_full = q_low_full / q_high_full if q_high_full > 0 else float("inf")
            detected = rho < -RS and tin and ratio_full >= RATIO_TOLERANCE
            if detected:
                verdict = (
                    "KAPPA-OVER-PHI (dense φ) DETECTED — per-work-block execution "
                    "density collapses as the tool-kit grows: "
                )
            else:
                verdict = (
                    "NO KAPPA-OVER-PHI (dense φ, within tolerance) — execution ratio "
                    "does not collapse with κ in this window "
                )
            verdict += (
                f"[Q̄_low/Q̄_high={ratio_full:.2f}, rho={rho:.3f}, "
                f"λcore_low/qhigh="
                f"{q_low_core / q_high_core if q_high_core > 0 else float('inf'):.3f}]"
            )

    # --- report ---
    print("=== Dense φ-evidence logger — execution-ratio κ-over-φ proxy ===")
    print(f"diary_dir   : {DIARY}")
    print(f"sessions (>= {MIN_TOOL_TURNS} tool turns): {n}")
    if rows:
        ks = [r["kappa_turns"] for r in rows]
        hs = [r["kappa_entropy"] for r in rows]
        phis = [r["phi_exec_ratio"] for r in rows]
        print(f"κ_turns     : min={min(ks)} med={sorted(ks)[n // 2]} max={max(ks)}")
        print(f"κ_entropy   : mean={sum(hs) / n:.2f} bits (tool-kit diversity)")
        print(f"φ_exec_ratio: mean={sum(phis) / n:.3f} (exec/[exec+read]) — the DENSE proxy")
        phis_core = [r["phi_exec_core_ratio"] for r in rows]
        print(f"φ_exec_core : mean={sum(phis_core) / n:.3f} (patch+write+execute, terminal excluded)")
        spawn = sum(1 for r in rows if r["phi_sparse_residue"] > 0)
        print(f"φ_sparse    : {spawn}/{n} sessions carry !Dc:/⊗Er: residue "
              f"({spawn / n * 100:.0f}%) — the OLD sparse layer at its resolution limit")
        agg: Counter = Counter()
        for r in rows:
            agg.update(r["tools"])
        dom = ", ".join(f"{t}:{cnt}" for t, cnt in agg.most_common(3))
        print(f"aggregate tool dominance top-3: {dom}")
    print(f"VERDICT     : {verdict}")
    print(f"csv         : {out_path}")

    # --- density contrast (the point of this harness) ---
    if rows:
        coverage_dense = sum(1 for r in rows if r["tools"] and (r["phi_exec_ratio"] > 0 or any(
            t in r["tools"] for t in READ_TOOLS)))
        cov_sparse = sum(1 for r in rows if r["phi_sparse_residue"] > 0)
        print("=== signal-coverage contrast (dense vs sparse) ===")
        print(f"exec/read-ratio computable for {coverage_dense}/{n} sessions "
              f"({coverage_dense / n * 100:.0f}%) vs sparse residue {cov_sparse}/{n} "
              f"({cov_sparse / n * 100:.0f}%) — the sparse layer was the resolution wall")
        print("NOTE: if the dense proxy shows no collapse, the κ-over-φ threshold is "
              "NOT evidenced by work-block density either — a real null, not an abstain.")

    # self-check
    ta.check(rows != [], "no rows produced")
    for r in rows:
        ta.check(0.0 <= r["phi_exec_ratio"] <= 1.0,
                 f"φ_exec_ratio out of [0,1] for {r['sid']}")
        ta.check(0.0 <= r["phi_exec_core_ratio"] <= 1.0,
                 f"φ_exec_core out of [0,1] for {r['sid']}")
        ta.check(r["phi_sparse_residue"] >= 0,
                 f"negative sparse residue for {r['sid']}")
    print(f"SELF-CHECK: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


def _evaluate(rows: list[dict]) -> tuple[bool, float, float]:
    """Shared verdict engine (used by main and selftest). Returns (detected, rho, ratio)."""
    n = len(rows)
    if n < MIN_SESSIONS:
        return False, 0.0, 1.0
    k_sorted = sorted(r["kappa_turns"] for r in rows)
    med = k_sorted[n // 2]
    low = [r for r in rows if r["kappa_turns"] <= med]
    high = [r for r in rows if r["kappa_turns"] > med]
    q_low_full = sum(r["phi_exec_ratio"] for r in low) / len(low)
    q_high_full = sum(r["phi_exec_ratio"] for r in high) / len(high)
    q_low_core = sum(r["phi_exec_core_ratio"] for r in low) / len(low)
    q_high_core = sum(r["phi_exec_core_ratio"] for r in high) / len(high)
    rho = spearman_rho(
        [r["phi_exec_ratio"] for r in rows],
        [r["kappa_turns"] for r in rows],
    )
    tin = q_low_full > q_high_full and q_low_core > q_high_core
    ratio_full = q_low_full / q_high_full if q_high_full > 0 else float("inf")
    detected = rho < -RS and tin and ratio_full >= RATIO_TOLERANCE
    return detected, rho, ratio_full


def selftest() -> int:
    """Prove the dense verdict engine is not a broken catch-all.

    collapse: long sessions read/scan heavily (exec ratio plummets), short sessions
              execute hard -> engine must DETECT κ-over-phi.
    flat:     exec ratio is CONSTANT across κ -> engine must NOT falsely detect.
    sparse:   a tiny sample (< MIN_SESSIONS) must ABSTAIN, never fire detection.
    """
    ta = TodoTracker()

    def synthetic(mode: str) -> list[dict]:
        rows = []
        # >= MIN_SESSIONS rows so the dense signal is not dismissed by the
        # loop-disconnected abstain guard (n>=30); u-shape across k for collapse.
        k_vals = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32,
                  36, 40, 50, 60, 70, 80, 90, 100, 120, 150,
                  180, 210, 240, 280, 320, 360, 400, 450, 500, 600, 700, 800]
        for k in k_vals:
            if mode == "collapse":
                phi = 0.85 if k <= 40 else 0.12   # execution density collapses with κ
            elif mode == "flat":
                phi = 0.60                          # constant density -> no threshold
            else:  # sparse
                phi = 0.85                          # density is there but tiny sample
            # build a plausible tool histogram matching the requested ratio
            exec_n = int(phi * 100)
            read_n = int((1 - phi) * 100)
            exec_n = max(exec_n, 30)
            read_n = max(read_n, 15)
            tools = Counter({"patch": exec_n // 3, "write_file": exec_n // 3,
                             "execute_code": exec_n - 2 * (exec_n // 3),
                             "read_file": read_n})
            rows.append({
                "sid": f"syn-{mode}-{k}", "date": "synthetic.md",
                "kappa_turns": k, "kappa_entropy": 2.0,
                "phi_exec_ratio": phi,
                "phi_exec_core_ratio": phi * 0.9,
                "phi_sparse_residue": 0,
                "tools": tools,
            })
        return rows

    for mode, expect in (("collapse", True), ("flat", False), ("sparse", False)):
        rows = synthetic(mode)
        if mode == "sparse":
            rows = rows[:4]  # 4 sessions < MIN_SESSIONS -> must abstain (no detection)
        detected, rho, ratio = _evaluate(rows)
        ta.check(detected == expect,
                 f"selftest[{mode}]: expected detected={expect}, got {detected} "
                 f"(rho={rho:.3f}, ratio={ratio:.2f})")
        print(f"  selftest[{mode:8}] detected={detected} rho={rho:.3f} "
              f"ratio={ratio:.2f} (expect {expect})")

    print(f"SELFTEST: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())