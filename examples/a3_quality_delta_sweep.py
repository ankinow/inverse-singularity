#!/usr/bin/env python3
"""A3 quality-delta sweep over τ — structural/behavioral split.

Extends a3_quality_delta.py with a τ-sweep grid. For each candidate deadline
τ, recompute the capped/subcap groups on the same dev-continuo cohort and
emit per-τ verdicts (NO_QUALITY_CLIFF / QUALITY_COST / ABSTAIN /
DEADLINE_UNBOUND). This makes the structural/behavioral split falsifiable:
does quality collapse only when τ binds, and at which τ does the curve turn?

Read-only, zero-deps, stdlib. Mirrors the discipline of a3_quality_delta.py.
"""

from __future__ import annotations
import json, os, re, sqlite3, sys
from collections import defaultdict
from datetime import datetime

HERMES_HOME = os.environ.get("HERMES_HOME", "/mnt/hermes")
STATE_DB = os.path.join(HERMES_HOME, "state.db")
CRON_DB = os.path.join(HERMES_HOME, "cron", "executions.db")

JOB_KEY = "4d301de794bc"
FIRST_ARM_LOCAL = "2026-08-23 22:07"
MIN_GROUP_N = 5
MSG_SLICE = 6000
MAX_SESSION_CHARS = 500_000

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
    "/run/media/lermf/DADOS_STORAGE/@projetos/Projetos/ist-runtime",
    "/mnt/projetos/Projetos/wiki-core",
]

SHA_BACKTICKED = re.compile(r"`([0-9a-f]{7,40})`")
SHA_NEAR_KEYWORD = re.compile(r"(?:commit|push(?:ed)?\b)[^\n]{0,40}?`?([0-9a-f]{7,40})`?", re.IGNORECASE)

def _local_epoch(s: str) -> float:
    return datetime.fromisoformat(s).timestamp()

def load_ticks(db_path: str):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = con.execute(
            "SELECT id, started_at, ended_at, api_call_count, tool_call_count, end_reason, input_tokens, output_tokens FROM sessions WHERE source='cron' AND id LIKE ? AND started_at >= ? ORDER BY started_at",
            (f"cron_{JOB_KEY}_%", _local_epoch(FIRST_ARM_LOCAL)))
        ticks = []
        for sid, st, en, api, tools, reason, tin, tout in cur:
            if en is None: continue
            ticks.append({"id": sid, "start": float(st), "end": float(en), "api": int(api or 0), "tools": int(tools or 0), "end_reason": reason or "", "tokens": int(tin or 0)+int(tout or 0)})
        return ticks
    finally:
        con.close()

def final_assistant_texts(con, session_id):
    cur = con.execute("SELECT role, content FROM messages WHERE session_id=? AND active=1 ORDER BY timestamp DESC LIMIT 15", (session_id,))
    tail, corpus, budget = "", [], 0
    for role, content in cur:
        if not content: continue
        piece = content[:MSG_SLICE]
        if not tail and role == "assistant":
            tail = piece.strip()
        corpus.append(piece)
        budget += len(piece)
        if budget >= MAX_SESSION_CHARS: break
    return tail, "\n".join(corpus)

FAIL_MARKERS = ("traceback","unhandled","fatal error","job failed","last_status=error")
SAFE_CONTEXT = re.compile(r"(auto_closed|triagem|findings|sast|muted|risk_accept)", re.IGNORECASE)
DONE_WORD = re.compile(r"\b(item|task|mission|tick|work)\b[^.!?\n]{0,40}\b(done|complete[dt]?|conclu[ií]d[oa]|trabalhad[oa]|finished|entregu[ea])\b", re.IGNORECASE)
REPORT_HDR = re.compile(r"(##\s*relat[oó]rio|^\*\*item\*\*:|\breport\s+delivered\b|\bfinal\s+summary\b)", re.IGNORECASE|re.MULTILINE)
BACKLOG_DONE = re.compile(r"\bbacklog[^.!?\n]{0,60}\b(updated|update|atualizad[oa])\b", re.IGNORECASE)

def classify_outcome(tail, end_reason, api):
    t = tail.strip()
    if not t: return "EMPTY"
    if t.startswith("[SILENT]"): return "SILENT"
    low = t.lower()
    if "idle" in low and "queue is empty" in low: return "IDLE"
    if "gate green" in low or "gate verde" in low: return "GATE_GREEN"
    if "max_turns" in str(end_reason).lower() or "max_turns" in low: return "CAP_CUT"
    if any(m in low for m in FAIL_MARKERS) and not SAFE_CONTEXT.search(t): return "FAIL"
    if DONE_WORD.search(t) or REPORT_HDR.search(t) or BACKLOG_DONE.search(t): return "DONE"
    return "OTHER"

class ShaVerifier:
    def __init__(self, repos):
        self.repos = repos
    def verify(self, sha):
        import subprocess
        for r in self.repos:
            if not os.path.isdir(r): continue
            try:
                subprocess.run(["git","-C",r,"cat-file","-e",sha], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue
        return False

def extract_shas(text):
    out=set()
    for m in SHA_BACKTICKED.finditer(text):
        out.add(m.group(1))
    for m in SHA_NEAR_KEYWORD.finditer(text):
        out.add(m.group(1))
    return list(out)

def aggregate(rows):
    n=len(rows)
    decided=[r for r in rows if r["outcome"] in ("DONE","GATE_GREEN","OTHER","CAP_CUT","CAP_DELIVERED","FAIL")]
    done=[r for r in rows if r["outcome"]=="DONE"]
    done_rate=len(done)/len(decided) if decided else None
    artifact_rate=None
    if done:
        verified=sum(1 for r in done if r.get("artifact"))
        artifact_rate=verified/len(done)
    proof_score=done_rate*artifact_rate if done_rate and artifact_rate else None
    mean_turns=sum(r["api"] for r in done)/len(done) if done else None
    capped=sum(1 for r in rows if r["api"]>=rows[0].get("_tau",0))
    return {"n":n,"decided":len(decided),"done_rate":done_rate,"artifact_rate":artifact_rate,"proof_score":proof_score,"mean_turns_done":mean_turns,"capped_n":capped}

def window_of(start_epoch):
    for name, lo, hi in WINDOWS:
        if _local_epoch(lo) <= start_epoch < _local_epoch(hi):
            return name
    return "pre_arm"

def verdict_of(cap_stats, sub_stats, tau):
    if cap_stats["n"]==0:
        return f"DEADLINE_UNBOUND(tau={tau}, ticks={sub_stats['n']}, 0 capped)"
    if cap_stats["n"]<MIN_GROUP_N or sub_stats["n"]<MIN_GROUP_N:
        return f"ABSTAIN(tau={tau}, sample< {MIN_GROUP_N})"
    ps_c=cap_stats.get("proof_score")
    ps_s=sub_stats.get("proof_score")
    ar_c=cap_stats.get("artifact_rate")
    ar_s=sub_stats.get("artifact_rate")
    if ps_c is None or ps_s is None: return f"ABSTAIN(tau={tau})"
    ar_par=(ar_c is not None and ar_s is not None and abs(ar_c-ar_s)<=0.25)
    if ps_c+1e-9 >= ps_s*0.75 and ar_par:
        return f"NO_QUALITY_CLIFF(tau={tau})"
    return f"QUALITY_COST(tau={tau})"

def run():
    ticks=load_ticks(STATE_DB)
    con=sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    verifier=ShaVerifier(REPOS)
    try:
        rows=[]
        for t in ticks:
            tail, corpus = final_assistant_texts(con, t["id"])
            t["outcome"]=classify_outcome(tail, t["end_reason"], t["api"])
            t["window"]=window_of(t["start"])
            shas=extract_shas(corpus)
            t["artifact"]=any(verifier.verify(s) for s in shas)
            rows.append(t)
        taus=[30,45,60,66,75,90,120,999]
        results=[]
        for tau in taus:
            tmp=[dict(r) for r in rows]
            for r in tmp:
                r["_tau"]=tau
                r["group"]="CAPPED" if r["api"]>=tau else "SUBCAP"
            cap=[r for r in tmp if r["group"]=="CAPPED"]
            sub=[r for r in tmp if r["group"]=="SUBCAP"]
            cap_stats=aggregate(cap)
            sub_stats=aggregate(sub)
            cap_stats["n"]=len(cap)
            sub_stats["n"]=len(sub)
            verdict=verdict_of(cap_stats, sub_stats, tau)
            results.append({
                "tau":tau,
                "capped_n":len(cap),
                "subcap_n":len(sub),
                "capped_done_rate":cap_stats.get("done_rate"),
                "subcap_done_rate":sub_stats.get("done_rate"),
                "capped_proof":cap_stats.get("proof_score"),
                "subcap_proof":sub_stats.get("proof_score"),
                "verdict":verdict
            })
        print(json.dumps({"schema":"a3-quality-delta-sweep/v1","job":JOB_KEY,"taus":results,"read_only":True}, indent=2))
        return 0
    finally:
        con.close()

if __name__=="__main__":
    sys.exit(run())
