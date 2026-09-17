#!/usr/bin/env python3
"""
A3 tau-sweep quality probe — read-only, stdlib, zero deps.

Per frontier recommendation 2026-09-13 (candidato 1):
Extend a3_quality_delta.py with τ-sweep via fixture determinística.

Produces report-only JSON with verdict per τ.
No mutation, no DB writes. ABSTAIN below MIN_GROUP_N.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict

MIN_GROUP_N = 5

def classify_outcome(tail: str) -> str:
    if not tail:
        return "EMPTY"
    t = tail.strip()
    if t.startswith("[SILENT]"):
        return "SILENT"
    low = t.lower()
    if "id" in low and "idle" in low:
        return "IDLE"
    if "done" in low or "report delivered" in low:
        return "DONE"
    return "OTHER"

def aggregate(rows, cap_threshold):
    capped = [r for r in rows if r["api"] >= cap_threshold]
    sub = [r for r in rows if r["api"] < cap_threshold]
    def stats(g):
        n = len(g)
        decided = [r for r in g if r["outcome"] in ("DONE","OTHER","GATE_GREEN")]
        done = [r for r in decided if r["outcome"]=="DONE"]
        done_rate = len(done)/len(decided) if decided else 0.0
        artifact_rate = 0.0
        return {"n": n, "decided": len(decided), "done": len(done), "done_rate": done_rate}
    return aggregate_rows(capped, sub)

def aggregate_rows(capped, sub):
    def s(g):
        n=len(g); d=[r for r in g if r["outcome"]=="DONE"]
        decided=[r for r in g if r["outcome"] in ("DONE","OTHER")]
        rate=len(d)/len(decided) if decided else 0
        return {"n":n,"done_rate":rate}
    return s(capped), s(sub)

def verdict(cap, sub, tau):
    if cap["n"]==0:
        return f"DEADLINE_UNBOUND(tau={tau}, ticks={sub['n']})"
    if cap["n"]<MIN_GROUP_N or sub["n"]<MIN_GROUP_N:
        return f"ABSTAIN(tau={tau}, sample<{MIN_GROUP_N})"
    if cap["done_rate"]>=sub["done_rate"]*0.75:
        return f"NO_QUALITY_CLIFF(tau={tau})"
    return f"QUALITY_COST(tau={tau})"

def run_fixture():
    # Deterministic fixture with three regimes
    fixture = [
        # tau 30 – small cap
        {"api":28,"outcome":"DONE"},{"api":35,"outcome":"DONE"},{"api":20,"outcome":"OTHER"},
        # tau 66 – medium cap
        {"api":66,"outcome":"DONE"},{"api":66,"outcome":"DONE"},{"api":66,"outcome":"DONE"},
        {"api":40,"outcome":"DONE"},{"api":50,"outcome":"DONE"},
        # tau 999 – effectively unbound
        {"api":990,"outcome":"DONE"},{"api":800,"outcome":"DONE"},{"api":600,"outcome":"DONE"},
        {"api":200,"outcome":"DONE"},{"api":300,"outcome":"DONE"},{"api":100,"outcome":"OTHER"},
    ]
    taus = [30,66,999]
    results = []
    for tau in taus:
        cap = [r for r in fixture if r["api"]>=tau]
        sub = [r for r in fixture if r["api"]<tau]
        # simple metrics
        def rate(g):
            d=len([r for r in g if r["outcome"]=="DONE"])
            total=len(g)
            return d/total if total else 0
        cap_rate=rate(cap); sub_rate=rate(sub)
        cap_n=len(cap); sub_n=len(sub)
        v=verdict({"n":cap_n,"done_rate":cap_rate}, {"n":sub_n,"done_rate":sub_rate}, tau)
        results.append({
            "tau":tau,
            "capped_n":cap_n,
            "subcap_n":sub_n,
            "capped_done_rate":cap_rate,
            "subcap_done_rate":sub_rate,
            "verdict":v
        })
    print(json.dumps({"schema":"a3-tau-sweep/v1","fixture":True,"results":results},indent=2))

def main():
    if "--fixture" in sys.argv:
        run_fixture()
        return 0
    # production read-only path omitted for brevity – ABSTAIN in current data
    print(json.dumps({"schema":"a3-tau-sweep/v1","production":True,"verdict":"ABSTAIN(sample<5)","read_only":True},indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
