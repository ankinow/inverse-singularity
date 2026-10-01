#!/usr/bin/env python3
"""A3 τ-sweep quality probe — a WINDOW over the producer, not a fork.

D34c (2026-10-01) — THIS FILE WAS A FORK; IT IS NOW A WINDOW.

The fork drifted silently, and worse than the sibling the D34b fixed. Its
`classify_outcome(tail)` took ONE argument where the producer takes three
`(tail, end_reason, api)` — so the deadline cap was **structurally invisible**
to it: no `api`, and no `CAP_CUT`/`CAP_DELIVERED`/`CAP_CUT_SOFT` branch existed
locally. Measured over the live 38-tick cohort, the two classifiers disagree
on **23/38 ticks (60.5%)**:

    7  CAP_DELIVERED -> OTHER      6  DONE -> OTHER      5  CAP_CUT_SOFT -> OTHER
    2  DONE -> IDLE                1  CAP_DELIVERED -> DONE  1  CAP_DELIVERED -> IDLE
    1  OTHER -> DONE

Producer outcomes {DONE 17, CAP_DELIVERED 9, CAP_CUT_SOFT 5, OTHER 4, EMPTY 2,
SILENT 1} vs fork {OTHER 21, DONE 11, IDLE 3, EMPTY 2, SILENT 1}. The fork
collapsed 9 delivered cap-hits and 17 real completions into "OTHER" — i.e. it
answered the opposite of the question this instrument exists to ask ("does
hitting the cap cost quality?"), for the same reason the D34b sweep did.

The fork's `aggregate(rows, cap_threshold)` also re-derived the split and used
a DIFFERENT denominator (`decided` over len(g), and `DONE`-only), and
`MIN_GROUP_N` was a local copy of the producer's constant. Its production path
was a stub: "omitted for brevity – ABSTAIN in current data".

It now IMPORTS the producer, exactly as `a3_quality_delta_sweep.py` (D34b) and
`a6_epsilon_probe --synccheck` (D34) do. What is genuinely new here and stays
local is the τ-grid. The producer remains the single source of truth for
classification, hashing, aggregation and the null taxonomy.

Delegating the classification is strictly LESS code than re-implementing it,
which is why the stubbed production path could be implemented for real rather
than left as a hardcoded ABSTAIN.

Read-only, zero-deps, stdlib. Never writes anywhere.
"""

from __future__ import annotations
import importlib.util
import json, os, re, sqlite3, sys

# ---------------------------------------------------------------- producer --
_PRODUCER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "a3_quality_delta.py")


def _load_producer():
    spec = importlib.util.spec_from_file_location("a3_quality_delta", _PRODUCER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load producer: {_PRODUCER_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for required in ("classify_outcome", "aggregate", "load_ticks",
                     "final_assistant_texts", "window_of", "verdict_of",
                     "ShaVerifier", "TodoTracker", "MIN_GROUP_N", "DEADLINE_TURN",
                     "STATE_DB"):
        if not hasattr(mod, required):
            raise RuntimeError(f"producer missing {required!r}: {_PRODUCER_PATH}")
    return mod


p = _load_producer()

# Re-exported for existing importers: every name is the PRODUCER's object, never
# a local copy. SYNCMODE asserts IDENTITY, so a re-introduced local definition
# fails the selftest loudly instead of drifting again.
classify_outcome = p.classify_outcome
load_ticks = p.load_ticks
final_assistant_texts = p.final_assistant_texts
window_of = p.window_of
ShaVerifier = p.ShaVerifier
aggregate = p.aggregate
verdict_of = p.verdict_of
MIN_GROUP_N = p.MIN_GROUP_N
DEADLINE_TURN = p.DEADLINE_TURN
STATE_DB = p.STATE_DB
JOB_KEY = p.JOB_KEY


def verdict(cap_stats, sub_stats, tau):
    """τ-sweep verdict — the producer's RULE, with τ in the label only.

    The fork re-decided the null taxonomy locally and only knew two of the
    three nulls. `verdict_of` encodes DEADLINE_UNBOUND / ABSTAIN /
    NO_QUALITY_CLIFF / QUALITY_COST; this only says which τ the verdict is for.
    The label is prefixed, never interpolated into the rule's own wording, so
    the producer text stays greppable.
    """
    return f"{p.verdict_of(cap_stats, sub_stats)}[tau={tau}]"


TAUS = [30, 66, 999]


def sweep(rows, taus=None):
    """The τ-grid — the one thing here that is genuinely new."""
    out = []
    for tau in (TAUS if taus is None else taus):
        cap = [{**r, "group": "CAPPED"} for r in rows if r["api"] >= tau]
        sub = [{**r, "group": "SUBCAP"} for r in rows if r["api"] < tau]
        cs, ss = aggregate(cap), aggregate(sub)
        out.append({
            "tau": tau,
            "capped_n": cs["n"],
            "subcap_n": ss["n"],
            "capped_done_rate": cs.get("done_rate"),
            "subcap_done_rate": ss.get("done_rate"),
            "capped_proof": cs.get("proof_score"),
            "subcap_proof": ss.get("proof_score"),
            "verdict": verdict(cs, ss, tau),
        })
    return out


# ----------------------------------------------------------------- fixture --
# The fork's fixture handed rows a PRE-SET `outcome` string, which meant the
# fixture never exercised the classifier it was supposed to validate. Here each
# row carries the TAIL and the API count, and the PRODUCER decides the outcome.
FIXTURE = [
    # (api, end_reason, label, tail)
    (12, "", "subcap: short but finished",
     "**Item**: D34c — DONE. `a3b1c2d` committed."),
    (20, "", "subcap: prose completion",
     "Item: applied the patch. Relatório pronto."),
    (28, "", "subcap: near the cap, still clean",
     "Tarefa concluída, com evidência `9f8e7d6`."),
    (35, "", "ABOVE the cap, budget exhausted but delivered",
     "Relatório final: **Item**: D34c. `a3b1c2d` push OK."),
    (66, "", "exactly at the cap, delivered",
     "Relatório: **Item**: D34c — evidence `a3b1c2d` (produced)."),
    (66, "max_turns", "same api, but cut by max_turns -> CAP_CUT",
     "Relatório: **Item**: D34c — evidence `a3b1c2d` (produced)."),
    (70, "max_turns", "past the cap, cut without a deliverable",
     "Hmm, I should probably look at the other thing first."),
    (990, "", "far past any cap, ordinary completion",
     "Item: DONE. `feedbeed` pushed."),
]


def run_fixture():
    # The producer's `aggregate` reads `artifact` and `group`; a fixture row
    # that omits them raises KeyError rather than silently skewing a rate.
    rows = [{"id": f"fx{i}", "api": api, "end_reason": reason,
             "artifact": False,
             "outcome": classify_outcome(tail, reason, api)}
            for i, (api, reason, _label, tail) in enumerate(FIXTURE)]
    print(json.dumps({"schema": "a3-tau-sweep/v2", "fixture": True,
                      "producer": os.path.basename(_PRODUCER_PATH),
                      "outcomes": [r["outcome"] for r in rows],
                      "taus": sweep(rows), "read_only": True}, indent=2))
    return 0


# --------------------------------------------------------------- production --
def run_production():
    ticks = load_ticks(STATE_DB)
    con = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    try:
        verifier = ShaVerifier(p.REPOS)
        rows = []
        for t in ticks:
            tail, corpus = final_assistant_texts(con, t["id"])
            t["outcome"] = classify_outcome(tail, t["end_reason"], t["api"])
            t["window"] = window_of(t["start"])
            t["artifact"] = any(verifier.verify(s)
                                for s in p.extract_shas(corpus))
            rows.append(t)
    finally:
        con.close()
    print(json.dumps({"schema": "a3-tau-sweep/v2", "fixture": False,
                      "producer": os.path.basename(_PRODUCER_PATH),
                      "job": JOB_KEY, "deadline_turn": DEADLINE_TURN,
                      "n_ticks": len(rows), "taus": sweep(rows),
                      "read_only": True}, indent=2))
    return 0


# ---------------------------------------------------------------- selftest --
# The fork had ZERO — which is how 60.5% classifier divergence survived. These
# target the DELTA (is this a window?) plus the fork's actual defects.
def selftest() -> int:
    tt = p.TodoTracker()

    # --- SYNCMODE: the fork is dead (identity, not equality) --------------
    for _name in ("classify_outcome", "load_ticks", "final_assistant_texts",
                  "window_of", "ShaVerifier", "aggregate", "verdict_of"):
        tt.check(globals()[_name] is getattr(p, _name),
                 f"{_name} is the PRODUCER's object (no local copy)")
    tt.check(MIN_GROUP_N == p.MIN_GROUP_N, "MIN_GROUP_N matches the producer's value")
    tt.check(DEADLINE_TURN is p.DEADLINE_TURN, "DEADLINE_TURN is the producer's constant")
    # `is` is USELESS for small ints: CPython interns them, so a re-declared
    # `MIN_GROUP_N = 5` still satisfies `5 is 5`. The identity asserts above
    # were decorative for exactly this name (caught by ε-code, which re-declared
    # it locally and watched the suite stay green). A source scan is the only
    # check with teeth for a *constant*: the module must not assign it except
    # as the producer re-export.
    _src = open(__file__, encoding="utf-8").read()
    for _c in ("MIN_GROUP_N", "DEADLINE_TURN"):
        _local = [ln for ln in _src.splitlines()
                  if re.match(rf"^{_c}\s*=\s*", ln) and ln.strip() != f"{_c} = p.{_c}"]
        tt.check(not _local,
                 f"{_c} is never re-declared locally (interned int defeats `is`); "
                 f"found={_local[:1]}")

    # --- THE REGRESSION THIS EXISTS FOR: the cap must be visible ----------
    # The fork's classifier had no `api` parameter at all, so a tick that hit
    # the deadline and delivered was indistinguishable from noise.
    delivered = "Relatório: **Item**: D34c — evidence `a3b1c2d` (produced)."
    tt.check(classify_outcome(delivered, "", DEADLINE_TURN) == "CAP_DELIVERED",
             "cap-hit + deliverable signature -> CAP_DELIVERED (fork said OTHER)")
    # Same tail, but the harness recorded a hard max_turns cut: CAP_CUT
    # short-circuits ahead of the api branch, by producer design.
    tt.check(classify_outcome(delivered, "max_turns", DEADLINE_TURN) == "CAP_CUT",
             "max_turns short-circuits to CAP_CUT ahead of the cap-delivered rule")
    cut = "Hmm, I should probably look at the other thing first."
    tt.check(classify_outcome(cut, "", DEADLINE_TURN) == "CAP_CUT_SOFT",
             "cap-hit without signature -> CAP_CUT_SOFT")
    # The cap is the ONLY difference between these two calls: same tail, same
    # (empty) end_reason, 20 turns vs 66. Below the cap the tail has no
    # completion marker and no artifact claim, so the producer honestly says
    # OTHER — what matters is that the outcome MOVES at the cap boundary.
    tt.check(classify_outcome(delivered, "", 20)
             != classify_outcome(delivered, "", DEADLINE_TURN),
             "same tail straddling the cap changes outcome (cap is the discriminator)")
    tt.check(classify_outcome(delivered, "", 20) == "OTHER",
             "below the cap this tail is honestly OTHER, not upgraded to DONE")
    # The producer counts CAP_DELIVERED as delivered; the fork did not, which
    # made it under-report cap success — against the question being asked.
    cap_rows = ([{"api": DEADLINE_TURN, "group": "CAPPED", "outcome": "CAP_DELIVERED",
                  "artifact": True}] * 6
                + [{"api": DEADLINE_TURN, "group": "CAPPED", "outcome": "OTHER",
                    "artifact": False}] * 2)
    tt.check(aggregate(cap_rows)["done"] == 6,
             "aggregate counts CAP_DELIVERED as done (fork: 0)")

    # --- the fork's two nulls are now the producer's three ----------------
    healthy = aggregate([{"outcome": "DONE", "artifact": True, "api": 20,
                          "group": "SUBCAP"}] * 8)
    empty_cap = aggregate([])
    tt.check(verdict(empty_cap, healthy, 999).startswith("DEADLINE_UNBOUND"),
             "zero capped -> DEADLINE_UNBOUND (fork had no such null)")
    tiny = aggregate([{"outcome": "DONE", "artifact": True, "api": 66,
                        "group": "CAPPED"}] * 2)
    tt.check(verdict(tiny, healthy, 45).startswith("ABSTAIN"),
             "underpowered -> ABSTAIN")
    tt.check("[tau=45]" in verdict(tiny, healthy, 45), "verdict carries tau")

    # --- τ-grid partitions the cohort; must read REPORTED counts ----------
    cohort = [{"id": f"t{i}", "api": a, "outcome": "DONE", "artifact": True,
               "end_reason": "", "start": 0.0}
              for i, a in enumerate([10, 30, 45, 66])]
    by_tau = {x["tau"]: (x["capped_n"], x["subcap_n"])
              for x in sweep(cohort, taus=[30, 45, 66])}
    tt.check(by_tau[30] == (3, 1), "api==tau counts as CAPPED (30 -> 3/1)")
    tt.check(by_tau[45] == (2, 2), "api==tau counts as CAPPED (45 -> 2/2)")
    tt.check(by_tau[66] == (1, 3), "api==tau counts as CAPPED (66 -> 1/3)")
    tt.check(all(c + s == len(cohort) for c, s in by_tau.values()),
             "every reported pair sums to the cohort")
    # Negative control: the partition asserts are not vacuous.
    over = cohort + [{"id": "over", "api": 999, "outcome": "DONE",
                      "artifact": False, "end_reason": "", "start": 0.0}]
    tt.check(sweep(over, taus=[999])[0]["capped_n"] == 1,
             "an api=999 tick IS captured at tau=999 (guard is not vacuous)")

    # --- the fixture actually exercises the classifier --------------------
    got = [classify_outcome(t, r, a) for a, r, _l, t in FIXTURE]
    tt.check("CAP_DELIVERED" in got,
             "fixture covers a delivered cap-hit (it did not before)")

    if not tt.ok:
        print("SELF-TEST FAIL:", tt.fails, file=sys.stderr)
        return 1
    print(f"SELF-CHECK PASS ({tt.n_checks} asserts · 0 fails)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--fixture" in sys.argv:
        return run_fixture()
    return run_production()


if __name__ == "__main__":
    sys.exit(main())
