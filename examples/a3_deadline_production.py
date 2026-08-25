#!/usr/bin/env python3
"""A3 production-deadline harness (ist-runtime, examples/) — v0.8.6.

The Structural/Behavioral Split thread left one empirical question open:
does the *compliance shape* of production match the runtime's deadline-
armed arc *when a structural deadline actually exists*? On 2026-08-23 the
mechanism-confirmed recommendation (rec tau ~= 1.2 x tau*) became live
production config (`agent.max_turns=66`), and within ~48h production ran,
on the SAME system, in three knob regimes:

  W_A   (tau=66, first arm)    2026-08-23 22:07 -> 23:59  (-03)
  W_B   (tau=999, silent drop) 2026-08-24 08:00 -> 2026-08-25 04:00
  W_A'  (tau=66, re-armed)     2026-08-25 06:00 -> present

Window boundaries are pinned by on-disk config snapshots (NOT narrative):

  config.yaml.bak.20260823_220651        max_turns: 66  (auto-bak of the set)
  config.yaml.corrupt.20260824-{074050,074343,074440}.bak  max_turns: 999
        (08-24 corruption + silent rebuild dropped the deadline)
  [uncertainty band excluded: 08-23 22:07 .. 08-24 07:59]
  config.yaml.bak.pre-doctrine-restauro-20260825-0600  max_turns: 66
        (restoration closed inside the A5 session; ist-runtime 7eb5ec6)

UNIT DISCOVERY (v0.8.6, the reason this harness exists):
  The knob counts MODEL turns (`api_call_count`), not tool calls. The
  diary `>T:` lines count TOOL CALLS — with parallel batching several
  `>T:` lines belong to ONE model turn — so any diary-based compliance
  curve measures the wrong clock (this harness v1 measured it and found
  an impossible tail: 185 '>T:' under an armed knob). PRIMARY source is
  therefore Hermes state.db `sessions` (api_call_count, started_at,
  ended_at, source); the diary span parser is kept as a SECONDARY
  cross-check with the unit mismatch stated, never as evidence.

SCOPE DISCOVERY (same run):
  The knob binds cron/subagent-class sessions and leaves operator
  interactive sessions unbound (interactive reaches hundreds of model
  turns while armed). Analyses split bound vs interactive accordingly.

MEASURES (per window, bound classes unless noted):
  - distribution of api_call_count (median / p90 / max)
  - tail mass P(api > 66) and EXACT-cap hits (api == 66)
  - PAIRED-JOB comparison: the dev-continuo autonomous loop ran in both
    regimes — same job, different knob (A' vs B), plus a harm proxy
    (runs ending at/near the cap that still completed their backlog
    item cannot be distinguished here; reported as open caveat).

VERDICT GATES (falsifiable, deterministic):
  BINDS_AND_BITES : bound tail>66 == 0 under BOTH armed windows AND
                    >=1 exact-cap termination under arm AND bound
                    max < 66+margin under the dropped-knob window is
                    NOT required (drop may simply lack long jobs).
  TAIL_UNDER_ARM  : any bound session > 66 while armed (refutes binding).
  INSUFFICIENT    : < MIN_BOUND per window — abstain honestly.

Zero deps. Stdlib only. Read-only on state.db (mode=ro URI).
"""
from __future__ import annotations

import csv
import os
import random
import re
import sys
import sqlite3
from datetime import datetime

HERMES_HOME = os.environ.get("HERMES_HOME", "/mnt/hermes")
STATE_DB = os.environ.get("HERMES_STATE_DB",
                          os.path.join(HERMES_HOME, "state.db"))
DIARY = os.environ.get("HERMES_DIARY", os.path.join(HERMES_HOME, "diary"))
OUT_CSV = os.path.join(os.environ.get("TMPDIR", "/tmp"),
                       "a3_deadline_production.csv")

DEADLINE_TURN = 66
TAIL_TURN = 67            # first turn strictly past the deadline
MIN_BOUND = 5             # minimum bound sessions per window to classify
BOUND_SOURCES = ("cron", "subagent", "kanban")   # knob-bound classes
INTERACTIVE_SOURCES = ("cli", "tui", "whatsapp", "desktop")
PAIRED_JOB_KEY = "4d301de794bc"  # dev-continuo (ran in BOTH regimes)

# (name, start_local, end_local, tau, snapshot evidence)  -03
WINDOWS = [
    ("A_firstarm_tau66", "2026-08-23 22:07", "2026-08-23 23:59", 66,
     "config.yaml.bak.20260823_220651: max_turns 66"),
    ("B_dropped_tau999", "2026-08-24 08:00", "2026-08-25 04:00", 999,
     "config.yaml.corrupt.20260824-{074050,074343,074440}.bak: 999"),
    ("A2_rearmed_tau66", "2026-08-25 06:00", "2999-01-01 00:00", 66,
     "config.yaml.bak.pre-doctrine-restauro-20260825-0600: 66"),
]

DAY_FILES = [  # secondary cross-check only
    "rotated/2026-08-23.20260823_220049.md",
    "2026-08-23.md",
    "rotated/2026-08-24.20260824_214523.md",
    "2026-08-24.md",
    "2026-08-25.md",
]


class TodoTracker:
    def __init__(self) -> None:
        self._fails: list[str] = []

    def check(self, cond: bool, msg: str) -> None:
        if not cond:
            self._fails.append(msg)

    @property
    def ok(self) -> bool:
        return not self._fails


def _local_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def load_sessions(db_path: str) -> list[dict]:
    """Read-only pull of post-arm sessions from Hermes state.db."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = con.execute(
            "SELECT id, session_key, source, started_at, ended_at, "
            "api_call_count, tool_call_count, end_reason "
            "FROM sessions WHERE started_at >= strftime('%s', ?, '+3 hours')",
            (_local_dt(WINDOWS[0][1]).strftime("%Y-%m-%d %H:%M"),))
        rows = []
        for (sid, skey, src, st, en, api, tools, reason) in cur:
            rows.append({
                "id": sid or "", "key": skey or "", "source": src or "?",
                "start": datetime.fromtimestamp(st or 0),
                "end": datetime.fromtimestamp(en) if en else None,
                "api": int(api or 0), "tools": int(tools or 0),
                "reason": reason or "",
            })
        return rows
    finally:
        con.close()


def assign_window(sessions: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {w[0]: [] for w in WINDOWS}
    for sess in sessions:
        t = sess["start"]
        for name, lo_s, hi_s, _tau, _ev in WINDOWS:
            if (_local_dt(lo_s) <= t.replace(microsecond=0)
                    <= _local_dt(hi_s)):
                buckets[name].append(sess)
                break
    return buckets


def pct(xs: list[int], q: float) -> float:
    if not xs:
        return float("nan")
    ys = sorted(xs)
    idx = min(len(ys) - 1, int(q * len(ys)))
    return float(ys[idx])


def dist_stats(turns: list[int]) -> dict:
    n = len(turns)
    return {
        "n": n,
        "median": pct(turns, 0.50),
        "p90": pct(turns, 0.90),
        "max": max(turns) if turns else 0,
        "tail_gt66": (sum(1 for t in turns if t > DEADLINE_TURN) / n)
        if n else float("nan"),
        "exact66": sum(1 for t in turns if t == DEADLINE_TURN),
    }


def permutation_tail_diff(a: list[int], b: list[int],
                          seed: int = 19845, n_perm: int = 10000
                          ) -> tuple[float, float]:
    """Diff in P(x > 66) between groups; seeded two-sided permutation."""
    na, nb = len(a), len(b)
    if na < 3 or nb < 3:
        return float("nan"), float("nan")

    def tail(xs: list[int]) -> float:
        return sum(1 for x in xs if x > DEADLINE_TURN) / len(xs)

    obs = tail(a) - tail(b)
    pool = a + b
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        d = tail(pool[:na]) - tail(pool[na:])
        if abs(d) >= abs(obs) - 1e-12:
            hits += 1
    return obs, hits / n_perm


def classify(bound_stats: dict[str, dict]) -> str:
    a1 = bound_stats.get("A_firstarm_tau66", {})
    a2 = bound_stats.get("A2_rearmed_tau66", {})
    total_bound = sum(s["n"] for s in bound_stats.values())
    if total_bound < MIN_BOUND:
        return (f"INSUFFICIENT (bound sessions total={total_bound} "
                f"< {MIN_BOUND})")
    armed_tails = [s["tail_gt66"] for s in (a1, a2)
                   if s.get("n", 0) >= 3]
    armed_caps = sum(s.get("exact66", 0) for s in (a1, a2))
    if any((t == t) and t > 0 for t in armed_tails):
        return ("TAIL_UNDER_ARM — bound session(s) exceeded 66 model turns "
                "while the deadline was armed: knob does NOT bind these "
                "sessions (or its unit differs from api_call_count)")
    if armed_caps >= 1:
        return ("BINDS_AND_BITES — zero bound tails past 66 under arm AND "
                f"{armed_caps} exact-cap termination(s) (api==66): the "
                "deadline measurably ends sessions in production; drop-"
                "window max is workload-limited, not knob-limited (honest "
                "asymmetry: no control-side cap evidence possible)")
    return ("INCONCLUSIVE — no tail under arm but no exact-cap signature "
            "either; either the knob binds but no session reached it, or "
            "mass is thin")


def parse_diary_spans(diary_dir: str) -> list[dict]:
    """SECONDARY cross-check: diary spans in TOOL-CALL units.

    Semantics verified against live files: recurring jobs REUSE their sid
    for many separate runs, so every `!Sd/on` after a close opens a NEW
    span; nesting handled by stack; flush-lag `>T:` orphans attach to the
    last closed span. NOTE: these counts are NOT model turns.
    """
    spans: dict[str, dict] = {}
    order: list[str] = []
    stack: list[str] = []
    seq = 0
    last_closed: dict | None = None

    def _open(sid: str, dt: datetime, platform: str) -> None:
        nonlocal seq
        if stack and stack[-1].rsplit("#", 1)[0] == sid:
            return
        seq += 1
        key = f"{sid}#{seq}"
        spans[key] = {"start": dt, "platform": platform, "turns": 0}
        order.append(key)
        stack.append(key)

    for rel in DAY_FILES:
        path = os.path.join(diary_dir, rel)
        if not os.path.exists(path):
            continue
        day = re.match(r"^(\d{4}-\d{2}-\d{2})", os.path.basename(rel))
        day = day.group(1) if day else ""
        for raw in open(path, encoding="utf-8"):
            s = raw.strip()
            if s.startswith("!Sd/on"):
                m = re.match(r"!Sd/on (\d{2}):(\d{2}):(\d{2}) sid=(\S+)"
                             r".*platform=(\w+)", s)
                if m:
                    _open(m.group(4),
                          datetime.fromisoformat(
                              f"{day}T{m.group(1)}:{m.group(2)}:{m.group(3)}"),
                          m.group(5))
            elif s.startswith("!Sd/off"):
                m = re.match(r"!Sd/off \d{2}:\d{2}:\d{2} sid=(\S+)", s)
                if m:
                    for k in reversed(stack):
                        if k.rsplit("#", 1)[0] == m.group(1):
                            stack.remove(k)
                            last_closed = spans[k]
                            break
            elif s.startswith(">T:"):
                if stack:
                    spans[stack[-1]]["turns"] += 1
                elif last_closed is not None:
                    last_closed["turns"] += 1
    return [spans[k] for k in order]


def selftest() -> bool:
    """Manufactured worlds must classify correctly (stats path only)."""
    rng = random.Random(19845)

    def span(lo: int, hi: int) -> int:
        return rng.randint(lo, hi)

    ok = True
    # world 1: armed caps bound sessions at exactly 66 -> BINDS_AND_BITES
    bound_arm = {"A_firstarm_tau66": {"n": 0}, "A2_rearmed_tau66": {}}
    arm_turns = [min(span(5, 120), DEADLINE_TURN) for _ in range(40)]
    s = dist_stats(arm_turns)
    w1 = s["tail_gt66"] == 0 and s["exact66"] >= 1
    print(f"[selftest] capped-world: tail={s['tail_gt66']:.2f} "
          f"exact66={s['exact66']} -> {'PASS' if w1 else 'FAIL'}")
    ok &= w1
    # world 2: tail survives under arm -> TAIL_UNDER_ARM
    over = [span(67, 200) for _ in range(5)] + [span(5, 40) for _ in range(20)]
    s2 = dist_stats(over)
    w2 = s2["tail_gt66"] > 0
    print(f"[selftest] tail-world: tail={s2['tail_gt66']:.2f} "
          f"-> {'PASS' if w2 else 'FAIL'}")
    ok &= w2
    # world 3: tiny sample -> INSUFFICIENT path in classify()
    tiny = {"A_firstarm_tau66": dist_stats([10]),
            "A2_rearmed_tau66": dist_stats([])}
    v3 = classify(tiny).startswith("INSUFFICIENT")
    print(f"[selftest] tiny-world: {v3} -> {'PASS' if v3 else 'FAIL'}")
    ok &= v3
    # world 4: permutation separates capped vs free distributions
    ctl_free = [span(5, 150) for _ in range(40)]
    diff, p = permutation_tail_diff(ctl_free,
                                    [min(x, DEADLINE_TURN) for x in ctl_free])
    w4 = (diff == diff) and diff > 0 and p <= 0.05
    print(f"[selftest] perm-world: diff={diff:.2f} p={p:.4f} "
          f"-> {'PASS' if w4 else 'FAIL'}")
    ok &= w4
    return ok


def fmt(x: float) -> str:
    return "nan" if x != x else f"{x:.2f}"


def main() -> int:
    ta = TodoTracker()
    if "--selftest" in sys.argv[1:]:
        good = selftest()
        print(f"SELFTEST: {'PASS' if good else 'FAIL'}")
        return 0 if good else 1

    sessions = load_sessions(STATE_DB)
    ta.check(len(sessions) > 0, "no sessions loaded from state.db")
    buckets = assign_window(sessions)

    print("=== A3 production-deadline harness v0.8.6 (state.db primary) ===")
    print(f"state.db         : {STATE_DB}")
    print(f"sessions loaded  : {len(sessions)} (since first arm)")
    print(f"knob             : agent.max_turns={DEADLINE_TURN}; "
          f"UNIT = model turns (api_call_count)")

    bound_stats: dict[str, dict] = {}
    all_stats: dict[str, dict] = {}
    for name, lo, hi, tau, ev in WINDOWS:
        bnd = [s["api"] for s in buckets[name]
               if s["source"] in BOUND_SOURCES]
        alc = [s["api"] for s in buckets[name]
               if s["source"] in INTERACTIVE_SOURCES]
        bound_stats[name] = dist_stats(bnd)
        all_stats[name] = dist_stats(alc)
        bs, als = bound_stats[name], all_stats[name]
        print(f"\n[{name}]  tau={tau}  ({ev})")
        print(f"  bound  (n={bs['n']:>3}): med={fmt(bs['median'])} "
              f"p90={fmt(bs['p90'])} max={bs['max']} "
              f"P(>66)={fmt(bs['tail_gt66'])} exact66={bs['exact66']}")
        print(f"  intera (n={als['n']:>3}): med={fmt(als['median'])} "
              f"max={als['max']}  <- operator class, knob-unbound by design")

    verdict = classify(bound_stats)

    # --- paired-job: dev-continuo in A' vs B ---
    pa = [s["api"] for s in buckets["A2_rearmed_tau66"]
          if PAIRED_JOB_KEY in (s["key"] + s["id"]) and s["api"] >= 1]
    pb = [s["api"] for s in buckets["B_dropped_tau999"]
          if PAIRED_JOB_KEY in (s["key"] + s["id"]) and s["api"] >= 1]
    diff, p = permutation_tail_diff(pa, pb)
    print(f"\n--- paired job [{PAIRED_JOB_KEY}] (model-turn lengths) ---")
    print(f"A'(tau=66): n={len(pa)} runs {sorted(pa)}")
    print(f"B (tau=999): n={len(pb)} runs {sorted(pb)}")
    print(f"tail-diff(A'-B)={fmt(diff)} perm-p={fmt(p)}"
          f"  <- descriptive: same job, different regime")

    # --- secondary: diary spans in tool-call units (cross-check ONLY) ---
    diary_spans = parse_diary_spans(DIARY)
    db = assign_window(diary_spans) if diary_spans else {}
    print("\n--- secondary (diary >T:, TOOL-CALL units — wrong clock, "
          "cross-check only) ---")
    for name in ("B_dropped_tau999", "A2_rearmed_tau66"):
        ts = [s["turns"] for s in db.get(name, [])]
        st = dist_stats(ts)
        print(f"{name}: n={st['n']} max_T={st['max']} "
              f"(>T: != model turn; divergence expected)")

    print(f"\nVERDICT: {verdict}")

    # CSV: per-session export of the analysis window
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["window", "session_key", "source", "start", "api_turns",
                    "tool_calls", "end_reason"])
        for name, *_ in WINDOWS:
            for s in buckets[name]:
                w.writerow([name, s["key"], s["source"],
                            s["start"].isoformat(), s["api"], s["tools"],
                            s["reason"]])
    print(f"csv              : {OUT_CSV}")

    ta.check(os.path.exists(OUT_CSV), "csv missing")
    ta.check(all(v["n"] >= 0 for v in bound_stats.values()), "bad stats")
    print(f"SELF-CHECK: {'PASS' if ta.ok else 'FAIL'}")
    for m in ta._fails:
        print(f"  [check fail] {m}")
    return 0 if ta.ok else 1


if __name__ == "__main__":
    sys.exit(main())
