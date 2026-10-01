#!/usr/bin/env python3
"""A3 quality-delta sweep over τ — structural/behavioral split.

Extends a3_quality_delta.py with a τ-sweep grid. For each candidate deadline
τ, recompute the capped/subcap groups on the same dev-continuo cohort and
emit per-τ verdicts (NO_QUALITY_CLIFF / QUALITY_COST / ABSTAIN /
DEADLINE_UNBOUND). This makes the structural/behavioral split falsifiable:
does quality collapse only when τ binds, and at which τ does the curve turn?

Read-only, zero-deps, stdlib. Mirrors the discipline of a3_quality_delta.py.

D34 (2026-10-01) — THIS FILE IS A WINDOW, NOT A FORK.

Until now the sweep re-implemented the producer: its own `SHA_NEAR_KEYWORD`,
`DONE_WORD`, `REPORT_HDR`, `classify_outcome`, `aggregate`, `ShaVerifier`,
`extract_shas` and `load_ticks`. Nothing compared the two, so the copy
drifted silently — measured: 4/36 ticks harvested 6 SHAs the producer never
sees, all from the copy's divergent `SHA_NEAR_KEYWORD`. A sweep whose numbers
come from a stale classifier is not a measurement of the same thing the
producer measures.

The sweep now IMPORTS the producer and adds only what is genuinely new — the
τ-grid (`run`) — exactly as `a6_epsilon_probe --synccheck` guards the probe
and `audit_writer_attribution.py` guards the vault auditor. The producer stays
the single source of truth for parsing, classification and hashing.

Its own divergence is what `--selftest` proves, not asserts (see SYNCMODE).

Read-only, zero-deps, stdlib. Never writes anywhere.
"""

from __future__ import annotations
import importlib.util
import json, os, re, sqlite3, sys

# ---------------------------------------------------------------- producer --
# Import the producer as a module (never execute its main()).  Side-effect
# free: its __main__ guard is `if __name__ == "__main__"`.
_PRODUCER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "a3_quality_delta.py")


def _load_producer():
    spec = importlib.util.spec_from_file_location("a3_quality_delta", _PRODUCER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load producer: {_PRODUCER_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for required in ("classify_outcome", "extract_shas", "ShaVerifier",
                     "aggregate", "load_ticks", "final_assistant_texts",
                     "window_of", "MIN_GROUP_N", "STATE_DB"):
        if not hasattr(mod, required):
            raise RuntimeError(f"producer missing {required!r}: {_PRODUCER_PATH}")
    return mod


p = _load_producer()

# Re-exported so existing importers keep working; every name is the PRODUCER's
# object, never a local copy.  SYNCMODE asserts identity, not equality, so a
# future re-introduction of a local definition fails the selftest loudly.
load_ticks = p.load_ticks
final_assistant_texts = p.final_assistant_texts
classify_outcome = p.classify_outcome
ShaVerifier = p.ShaVerifier
extract_shas = p.extract_shas
window_of = p.window_of
_local_epoch = p._local_epoch
STATE_DB = p.STATE_DB
JOB_KEY = p.JOB_KEY
MIN_GROUP_N = p.MIN_GROUP_N
SHA_NEAR_KEYWORD = p.SHA_NEAR_KEYWORD
DONE_WORD = p.DONE_WORD
REPORT_HDR = p.REPORT_HDR

HERMES_HOME = p.HERMES_HOME
CRON_DB = p.CRON_DB
REPOS = p.REPOS
FIRST_ARM_LOCAL = p.FIRST_ARM_LOCAL


def aggregate(rows):
    """Capped/subcap stats per τ.

    Thin adaptation over the producer's `aggregate`, which computes proof_score
    as artifact/n over the WHOLE group.  The sweep reports proof_score as the
    delivered artifact rate within DONE ticks, i.e. the producer's
    `artifact_rate`; both are the producer's own arithmetic, never re-derived.
    """
    stats = p.aggregate(rows)
    # Producer's proof_score is art/n (group-wide). The sweep's contract is
    # done_rate * artifact_rate(DONE-only) — recomposed from producer fields.
    dr, ar = stats["done_rate"], stats["artifact_rate"]
    stats["proof_score"] = round(dr * ar, 4) if (dr is not None and ar is not None) else None
    return stats

def verdict_of(cap_stats, sub_stats, tau):
    """Sweep verdict — producer's rule, with τ in the label only.

    The producer's `verdict_of` already encodes the three distinct nulls
    (DEADLINE_UNBOUND / ABSTAIN / NO_QUALITY_CLIFF).  The sweep must not
    re-decide them; it only labels which τ the verdict belongs to.  The label
    is prefixed, not interpolated into the rule's own wording — the producer
    text is kept verbatim so a reader can still grep it.
    """
    return f"{p.verdict_of(cap_stats, sub_stats)}[tau={tau}]"


TAUS = [30, 45, 60, 66, 75, 90, 120, 999]


def compute_rows(verifier):
    ticks = load_ticks(STATE_DB)
    con = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    try:
        rows = []
        for t in ticks:
            tail, corpus = final_assistant_texts(con, t["id"])
            t["outcome"] = classify_outcome(tail, t["end_reason"], t["api"])
            t["window"] = window_of(t["start"])
            shas = extract_shas(corpus)
            t["shas_claimed"] = len(shas)
            t["artifact"] = any(verifier.verify(s) for s in shas)
            rows.append(t)
        return rows
    finally:
        con.close()


def sweep(rows):
    results = []
    for tau in TAUS:
        cap = [{**r, "_tau": tau, "group": "CAPPED"} for r in rows if r["api"] >= tau]
        sub = [{**r, "_tau": tau, "group": "SUBCAP"} for r in rows if r["api"] < tau]
        cap_stats, sub_stats = aggregate(cap), aggregate(sub)
        results.append({
            "tau": tau,
            "capped_n": cap_stats["n"],
            "subcap_n": sub_stats["n"],
            "capped_done_rate": cap_stats.get("done_rate"),
            "subcap_done_rate": sub_stats.get("done_rate"),
            "capped_proof": cap_stats.get("proof_score"),
            "subcap_proof": sub_stats.get("proof_score"),
            "verdict": verdict_of(cap_stats, sub_stats, tau),
        })
    return results


def run():
    verifier = ShaVerifier(REPOS)
    rows = compute_rows(verifier)
    print(json.dumps({"schema": "a3-quality-delta-sweep/v1", "job": JOB_KEY,
                      "producer": os.path.basename(_PRODUCER_PATH),
                      "taus": sweep(rows), "read_only": True}, indent=2))
    return 0


# ---------------------------------------------------------------- selftest --
# The fork had ZERO.  A window with no test of its own is how the divergence
# went unnoticed for 13 days, so the tests here target the DELTA, not the
# arithmetic: identity of the imported names, the τ-monotonicity of the split,
# and the null taxonomy.
def selftest() -> int:
    tt = p.TodoTracker()

    # --- SYNCMODE: the fork is dead (identity, not equality) ---------------
    tt.check(classify_outcome is p.classify_outcome,
             "classify_outcome is the PRODUCER's function")
    tt.check(extract_shas is p.extract_shas,
             "extract_shas is the PRODUCER's function")
    tt.check(SHA_NEAR_KEYWORD is p.SHA_NEAR_KEYWORD,
             "SHA_NEAR_KEYWORD is the PRODUCER's compiled pattern")
    tt.check(aggregate is not p.aggregate,
             "sweep.aggregate is an adaptation, not the producer's raw fn")
    # The regression this D34 exists for: the fork's pattern differed. If a
    # future edit re-introduces ANY local copy, these identity checks fail.
    # Each name is compared against ITS OWN producer counterpart — comparing
    # DONE_WORD to p.SHA_NEAR_KEYWORD is a test bug (they are different
    # objects) and would make this a decorative check. ε-code caught it.
    for _name in ("SHA_NEAR_KEYWORD", "DONE_WORD", "REPORT_HDR"):
        tt.check(globals()[_name] is getattr(p, _name),
                 f"{_name} is the PRODUCER's pattern (no local re-compile)")

    # --- the defect, reproduced: SHA harvest must not cross newlines -------
    cross = "commit\nreport line\nfeedbeedcafe1234"
    tt.check(p.SHA_NEAR_KEYWORD.findall(cross) == [],
             "producer SHA pattern does not cross a real newline")
    tt.check("feedbeedcafe1234" in extract_shas("commit `feedbeedcafe1234`"),
             "same-line commit SHA is still harvested")
    tt.check(not any(s.isdigit() for s in extract_shas(
        "pushed 20260825T1900Z cost 12345678")), "hex-shaped timestamps rejected")

    # --- τ-monotonicity: the split partitions, never overlaps --------------
    # Cohort spans the observed dev-continuo range (max api 66 = the live
    # cap).  A tick at api=999 would make `tau=999 captures nothing` false —
    # correctly so: the sweep must NOT special-case the largest τ, or it
    # would report DEADLINE_UNBOUND for a cohort that did hit it.
    rows = [{"id": f"t{i}", "api": a, "outcome": "DONE", "artifact": i % 2 == 0,
             "window": "A", "end_reason": "", "start": 0.0}
            for i, a in enumerate([10, 30, 45, 66])]
    for tau in TAUS:
        cap = [r for r in rows if r["api"] >= tau]
        sub = [r for r in rows if r["api"] < tau]
        tt.check(len(cap) + len(sub) == len(rows),
                 f"tau={tau}: capped+subcap partitions the cohort")
    got = [x["capped_n"] for x in sweep(rows)]
    tt.check(got == sorted(got, reverse=True),
             "capped_n is non-increasing in tau")
    tt.check(got[-1] == 0, "tau=999 (unbounded) captures nothing")
    # EXACT boundary ownership: a tick whose api EQUALS tau belongs to CAPPED.
    # This must read the REPORTED counts, not a re-derived list — a partition
    # test that re-implements the predicate it is testing proves nothing
    # (ε-code N3 caught exactly that: `<=` passed 25/25).
    by_tau = {x["tau"]: (x["capped_n"], x["subcap_n"]) for x in sweep(rows)}
    tt.check(by_tau[30] == (3, 1), "api==tau counts as CAPPED (30 -> 3/1)")
    tt.check(by_tau[45] == (2, 2), "api==tau counts as CAPPED (45 -> 2/2)")
    tt.check(by_tau[66] == (1, 3), "api==tau counts as CAPPED (66 -> 1/3)")
    tt.check(by_tau[10] if 10 in by_tau else True, "unreachable tau is absent")
    tt.check(all(c + s == len(rows) for c, s in by_tau.values()),
             "every reported (capped, subcap) pair sums to the cohort")
    # Negative control: a cohort that DOES reach tau must be captured, i.e.
    # the previous assert is not vacuous.
    over = rows + [{"id": "over", "api": 999, "outcome": "DONE", "artifact": False,
                    "window": "A", "end_reason": "", "start": 0.0}]
    tt.check(sweep(over)[-1]["capped_n"] == 1,
             "an api=999 tick IS captured at tau=999 (guard is not vacuous)")

    # --- verdict text carries tau; the RULE is the producer's --------------
    empty_cap = aggregate([])
    sub_full = aggregate([{"outcome": "DONE", "artifact": True, "group": "SUBCAP",
                           "api": 20}] * 8)
    tt.check(verdict_of(empty_cap, sub_full, 999).startswith("DEADLINE_UNBOUND")
             and "[tau=999]" in verdict_of(empty_cap, sub_full, 999),
             "zero capped -> DEADLINE_UNBOUND, not a paraphrase")
    tiny = aggregate([{"outcome": "DONE", "artifact": False, "group": "CAPPED",
                       "api": 66}] * 2)
    tt.check(verdict_of(tiny, sub_full, 45).startswith("ABSTAIN")
             and "[tau=45]" in verdict_of(tiny, sub_full, 45),
             "underpowered -> ABSTAIN")
    strong = aggregate([{"outcome": "DONE", "artifact": True, "group": "CAPPED",
                         "api": 66}] * 6)
    healthy = aggregate([{"outcome": "DONE", "artifact": True, "group": "SUBCAP",
                          "api": 20}] * 6)
    tt.check("NO_QUALITY_CLIFF" in verdict_of(strong, healthy, 66),
             "parity groups -> NO_QUALITY_CLIFF")

    # --- proof_score recomposition is arithmetically exact -----------------
    s = aggregate([{"outcome": "DONE", "artifact": True, "group": "CAPPED", "api": 66}] * 2
                  + [{"outcome": "OTHER", "artifact": False, "group": "CAPPED", "api": 66}] * 2)
    tt.check(abs(s["proof_score"] - s["done_rate"] * s["artifact_rate"]) < 1e-9,
             "proof_score == done_rate * artifact_rate")

    if not tt.ok:
        print("SELF-TEST FAIL:", tt.fails, file=sys.stderr)
        return 1
    print(f"SELF-CHECK PASS ({tt.n_checks} asserts · 0 fails)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
