#!/usr/bin/env python3
"""A3-productive-τ harness (ist-runtime, examples/).

Closes the actionable gap left by the empirical discovery of 2026-08-23
(`a3_diary_compliance.py`, v0.7.3): production Hermes/IST sessions decay
Gamage-style (survival curve holds ~100% to turn ~30, collapses toward
40% by turn ~71, half-life ~turn 57). The runtime's current budget knob
(`agent.max_turns`) is a *weak* τ: it only delays collapse, it never
teaches the agent to converge before it decays.

The open question this harness answers (A3 inverted — the thread in
CURIOSITY.md: "does an agent that knows its own half-life make different
choices?"): **what is the effective productive τ, and what should the
budget knob be set to so the agent converges BEFORE the decay curve
bites?**

Method:
  1. Re-derive the session survival curve from the real diary (same
     parser / `!Sd/on..!Sd/off` segmentation as `a3_diary_compliance.py`,
     import reused — no duplicate parsing logic).
  2. Compute the empirical semi-collapse turn τ* (the survival
     half-life, the turn where alive fraction crosses 0.5) straight
     from the data — this is the *effective productive horizon*: beyond
     it more than half of production sessions have already rotted.
  3. Read the live budget knob from the Hermes config (agent.max_turns
     and goals.max_turns if present) and express the *gap* as a ratio.
  4. Recommend a **self-adaptive τ** (A3-inverse): not a static upper
     cap but a budget that is *re-derived mid-curve* — the agent set to
     an upcoming deadline at its own half-life, so convergence pressure
     (the thing A3 needs) exists instead of a distant ceiling.

Deliverable: a running stdlib harness + a quantitative recommendation +
the reasoning chain documented. Exit 0 on success (any shape); the
verdict/recommendation columns carry the finding.

Zero deps. Stdlib only (doutrina).
"""
from __future__ import annotations

import csv
import os
import re
import sys
from dataclasses import dataclass

# reuse the validated diary parser from the sibling harness (no drift)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a3_diary_compliance import parse_diary, MIN_TOOL_TURNS  # noqa: E402

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")
CONFIG = os.environ.get("HERMES_CONFIG", "/mnt/hermes/config.yaml")
# window cap for survival analysis (sparse tail beyond ~turn 128)
MAX_TURNS = 200


@dataclass
class HalfLife:
    turn: int          # first absolute turn where survivors < 0.5 of start
    frac_at_hl: float  # fraction still alive AT the half-life turn
    start_frac: float  # fraction alive at turn 1
    total: int         # number of sessions analyzed


def survival_curve(sessions: list[dict], max_turns: int) -> list[int]:
    """Return n_at[k] = number of sessions that reached turn k (1-based)."""
    n_at = [0] * (max_turns + 1)
    for sess in sessions:
        reached = len(sess["order"])
        for k in range(1, min(reached, max_turns) + 1):
            n_at[k] += 1
    return n_at


def compute_half_life(n_at: list[int], total: int) -> HalfLife | None:
    """Empirical semi-collapse turn: first turn where survivors < half.**"""
    for k in range(1, len(n_at)):
        frac = n_at[k] / total if total else 0.0
        if frac < 0.5:
            return HalfLife(turn=k, frac_at_hl=frac, start_frac=n_at[1] / total if total else 0.0, total=total)
    return None


def read_budget_knob(cfg_path: str) -> dict:
    """Read agent.max_turns (and goals.max_turns if present) from config.

    Parses only the scalar keys that matter; returns placeholder sentinels
    for anything missing. This is NOT a full YAML parse (zero-deps rule) —
    it scans the lines and captures `agent: max_turns:` / `goals: max_turns:`
    indented scalars, which is the whole scope of the budget gap.
    """
    result = {"agent_max_turns": None, "goals_max_turns": None, "source": cfg_path}
    if not os.path.exists(cfg_path):
        return result
    with open(cfg_path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    # track current top-level section
    section = None
    for raw in lines:
        s = raw.rstrip()
        indent = len(s) - len(s.lstrip())
        stripped = s.strip()
        if indent == 0 and stripped.endswith(":") and not stripped.startswith((" ", "-", "#")):
            section = stripped[:-1]
            continue
        if indent > 0 and re.match(r"^max_turns:", stripped):
            val = re.sub(r"[^0-9]", "", stripped.split(":", 1)[1])
            if section == "agent":
                result["agent_max_turns"] = int(val) if val else None
            elif section == "goals":
                result["goals_max_turns"] = int(val) if val else None
    return result


def recommend(hl_turn: int, budget: dict) -> dict:
    """A3-inverse recommendation from the empirical half-life.

    Self-adaptive τ = a budget that tracks the half-life: the agent should
    be *given* an upcoming deadline at ~its own half-life (convergence
    pressure) rather than a distant/or absent ceiling. Two regimes:

      gap_ratio = budget / hl_turn   (>2 budget is a weak τ in practice)

    If the budget knob is effectively unbounded relative to the half-life
    (gap_ratio large, e.g. ∞ because knob absent, or > 2.5), the harness
    recommends a self-adaptive deadline at hl_turn with mid-curve re-derive.
    """
    knob = budget.get("goals_max_turns") or budget.get("agent_max_turns")
    nd = budget.get("agent_max_turns")  # the canonical agent-level knob
    if knob:
        gap_ratio = knob / max(hl_turn, 1)
    elif nd:
        gap_ratio = nd / max(hl_turn, 1)
    else:
        gap_ratio = float("inf")

    weak = gap_ratio is None or gap_ratio == float("inf") or gap_ratio > 2.5
    recommended = int(round(hl_turn * 1.2))  # a small headroom above half-life
    return {
        "half_life_turn": hl_turn,
        "current_budget": knob,
        "current_budget_ratio": gap_ratio,
        "weak_tau": weak,
        "recommendation_tau": recommended,
        "mechanism": "self-adaptive: set a deadline at ~own half-life (%d), "
                     "re-derived every diary compaction (mid-curve), so the "
                     "agent converges before the decay curve bites; the "
                     "existing knob (ratio %.2g) is a weak τ that only "
                     "delays collapse." % (hl_turn, gap_ratio),
    }


def main() -> int:
    ta = type("T", (), {"ok": True, "msg": []})()
    fails: list[str] = []

    sessions = parse_diary(DIARY)
    long_sessions = [s for s in sessions if len(s["order"]) >= MIN_TOOL_TURNS]
    if not long_sessions:
        fails.append("no diary sessions reached spec (>=30 tool turns)")
        print("SELF-CHECK: FAIL — no sessions")
        return 1

    n_at = survival_curve(long_sessions, MAX_TURNS)
    total = len(long_sessions)
    hl = compute_half_life(n_at, total)
    budget = read_budget_knob(CONFIG)
    if hl is None:
        fails.append("survival never dropped below 0.5 within window — nothing to derive")
        hl_turn = MAX_TURNS
    else:
        hl_turn = hl.turn

    rec = recommend(hl_turn, budget)

    # write CSV
    out_path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "a3_productive_tau.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["turn", "sessions_at_turn", "survival_frac"])
        for k in range(1, MAX_TURNS + 1):
            w.writerow([k, n_at[k], f"{(n_at[k] / total) if total else 0.0:.4f}"])

    # report
    print("=== A3-productive-τ harness (empirical half-life vs budget knob) ===")
    print(f"diary_dir        : {DIARY}")
    print(f"sessions analyzed: {total} (>= {MIN_TOOL_TURNS} tool turns)")
    if hl:
        print(f"survival t=1     : {hl.start_frac:.2f}")
        print(f"semi-collapse τ* : turn {hl.turn} (survivors {hl.frac_at_hl:.2f})")
    print(f"budget knob      : agent.max_turns={budget['agent_max_turns']} "
          f"goals.max_turns={budget['goals_max_turns']} (from {budget['source']})")
    print(f"gap ratio        : {rec['current_budget_ratio']:.2f}x of τ*"
          if isinstance(rec['current_budget_ratio'], float) and rec['current_budget_ratio'] != float('inf')
          else f"gap ratio        : unbounded (rocket knob = weak τ)")
    print(f"weak τ?          : {'YES' if rec['weak_tau'] else 'no'}")
    print(f"rec τ (self-adj) : {rec['recommendation_tau']} (~1.2 × half-life)")
    print(f"mechanism        : {rec['mechanism']}")
    print(f"csv              : {out_path}")

    # self checks
    if os.path.exists(out_path):
        pass
    else:
        fails.append("csv not written")
    if hl is not None and not (1 <= hl.turn <= MAX_TURNS):
        fails.append("half-life turn out of range")
    if rec["recommendation_tau"] <= 0:
        fails.append("non-positive recommendation τ")
    if fails:
        print("SELF-CHECK: FAIL")
        for m in fails:
            print(f"  [check fail] {m}")
        return 1
    print("SELF-CHECK: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())