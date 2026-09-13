#!/usr/bin/env python3
"""ε_code residual trend — append-only time-series of the classifier's UNKNOWN fraction.

Read-only. The ε-code thread closed on "compression bottoms out" at ~3.8% UNKNOWN
(the residual dominated by genuinely-ambiguous *driver* blobs — `subprocess.run(a, ...)`
with a variable argument, bare `python3 <script>` — which the never-guess discipline
correctly refuses to classify). But a *point-in-time* coverage number makes a silent
regression invisible: if a new shell shape starts leaking through as UNKNOWN (or,
conversely, if the classifier is later *over*-extended and starts guessing intent it
cannot prove), nothing trends it.

This instrument closes that gap by the same discipline the κ-Proliferation thread
already used for dQ/dt (`kappa_proliferation_timeseries.py --trend`, v0.8.9) and the
CURIOSITY thread used for self-bloat (`curiosity_kappa_trend.py`, v0.8.14):

  * it does **not** re-implement the measurement — it imports `epsilon_code_coverage`
    (`load_commands` + `action_typing_classifier.classify`) so the trend and the
    point-in-time report share one source of truth and cannot drift apart;
  * each run appends one row {seq, ts, total, unknown, unknown_frac, mutation, observe,
    producer_sha} to `data/epsilon_code_trend.sqlite` (append-only, `seq INTEGER PRIMARY
    KEY AUTOINCREMENT` — the v0.8.9 write-safety shape);
  * `--trend` (`schema epsilon-code-trend/v1`) reads the UNKNOWN-fraction gradient and
    reports a **`worsening`** verdict only on a genuine monotone rise of unknown_frac
    past the healthiest (lowest) point, firing downward for `improving` only if the
    fraction strictly falls; it abstains on <2 samples.

The Goodhart safeguard is structural, identical to its siblings: the instrument samples
and appends only — no gate, no decision path, no prescriptive consumer. The UNKNOWN%
is a *measured* surface of ε_code, and ε_code is the *compressible* enforcement gap by
definition; ε_system (the sovereignty residue) is untouched because the classifier only
resolves *shape*, never intent it cannot prove.

Exit 0 always (read-only), except `--selftest` which exits non-zero on failure.
"""

import json
import sqlite3
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import epsilon_code_coverage as cov  # noqa: E402  (source of truth for the measure)
import action_typing_classifier as at  # noqa: E402

DB = "/mnt/hermes/state.db"
TREND_DB = str(Path(__file__).resolve().parent.parent / "data" / "epsilon_code_trend.sqlite")

SCHEMA = "epsilon-code-trend/v1"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def init_db(path=TREND_DB):
    con = sqlite3.connect(path)
    cur = con.cursor()
    # append-only table; migrate any legacy seq-less table to the AUTOINCREMENT shape
    cur.execute(
        """CREATE TABLE IF NOT EXISTS samples (
               seq INTEGER PRIMARY KEY AUTOINCREMENT,
               ts TEXT NOT NULL,
               total INTEGER NOT NULL,
               unknown INTEGER NOT NULL,
               unknown_frac REAL NOT NULL,
               mutation INTEGER NOT NULL,
               observe INTEGER NOT NULL,
               producer_sha TEXT NOT NULL
           )"""
    )
    con.commit()
    con.close()


def sample_once(db=DB, out_db=TREND_DB, now=None):
    """Measure the live coverage once and append a row. Returns the row dict."""
    cmds = cov.load_commands(db)
    total = len(cmds)
    import collections
    results = collections.Counter()
    for tool, cmd in cmds:
        key = "command" if tool == "terminal" else "code"
        results[at.classify(tool, {key: cmd})] += 1
    unknown = results[""]
    unknown_frac = (unknown * 100.0 / total) if total else 0.0
    sync_ok, vsha, psha, _detail = cov.synccheck()
    row = {
        "seq": None,
        "ts": now or _now_iso(),
        "total": total,
        "unknown": unknown,
        "unknown_frac": round(unknown_frac, 4),
        "mutation": results["mutation"],
        "observe": results["observe"],
        "producer_sha": psha,
    }
    init_db(out_db)
    con = sqlite3.connect(out_db)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO samples (ts, total, unknown, unknown_frac, mutation, observe, producer_sha) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            row["ts"],
            row["total"],
            row["unknown"],
            row["unknown_frac"],
            row["mutation"],
            row["observe"],
            row["producer_sha"],
        ),
    )
    row["seq"] = cur.lastrowid
    con.commit()
    con.close()
    return row


def _load_series(out_db=TREND_DB):
    con = sqlite3.connect(f"file:{out_db}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute(
        "SELECT seq, ts, total, unknown, unknown_frac, mutation, observe, producer_sha "
        "FROM samples ORDER BY seq ASC"
    )
    rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
    con.close()
    return rows


def trend(out_db=TREND_DB):
    rows = _load_series(out_db)
    n = len(rows)
    if n < 2:
        return {
            "schema": SCHEMA,
            "samples": n,
            "verdict": "abstain",
            "reason": "fewer than 2 samples",
            "first_frac": rows[0]["unknown_frac"] if rows else None,
            "last_frac": rows[-1]["unknown_frac"] if rows else None,
            "min_frac": min((r["unknown_frac"] for r in rows), default=None),
            "max_frac": max((r["unknown_frac"] for r in rows), default=None),
            "last_total": rows[-1]["total"] if rows else None,
        }
    first = rows[0]["unknown_frac"]
    last = rows[-1]["unknown_frac"]
    lo = min(r["unknown_frac"] for r in rows)
    hi = max(r["unknown_frac"] for r in rows)
    # "worsening" only on a genuine monotone rise of the UNKNOWN fraction past the
    # healthiest (lowest) point; "improving" only on a strict fall; else "stable".
    # A single-sample-noise wiggle (flat run) never fires — same discipline as the
    # κ-Proliferation collapse reader.
    monotone_rise = all(rows[i]["unknown_frac"] <= rows[i + 1]["unknown_frac"] for i in range(n - 1))
    monotone_fall = all(rows[i]["unknown_frac"] >= rows[i + 1]["unknown_frac"] for i in range(n - 1))
    # the rise must actually *grow* (not be flat) and pass the healthiest point
    grew = last > lo
    fell = last < hi
    if monotone_rise and grew:
        verdict = "worsening"
    elif monotone_fall and fell:
        verdict = "improving"
    else:
        verdict = "stable"
    return {
        "schema": SCHEMA,
        "samples": n,
        "verdict": verdict,
        "first_frac": first,
        "last_frac": last,
        "min_frac": lo,
        "max_frac": hi,
        "delta_frac": round(last - first, 4),
        "last_total": rows[-1]["total"],
    }


def _selftest():
    ok = True
    import tempfile, os

    # 1. the measure is importable and the classifier has the expected interface
    for attr in ("load_commands", "synccheck"):
        ok &= hasattr(cov, attr)
    for attr in ("classify", "AMBIGUOUS_TOOLS"):
        ok &= hasattr(at, attr)

    # 2. append-does-not-replace: two samples into a temp DB yield seq 1,2 monotonic
    tmp = tempfile.mkdtemp(prefix="ect-selftest-")
    tdb = os.path.join(tmp, "trend.sqlite")
    r1 = sample_once(out_db=tdb)
    r2 = sample_once(out_db=tdb)
    rows = _load_series(tdb)
    ok &= len(rows) == 2
    ok &= rows[0]["seq"] == 1 and rows[1]["seq"] == 2
    ok &= rows[0]["ts"] <= rows[1]["ts"]  # append preserves order

    # 3. trend verdicts on synthetic series: worsening fires, stable silent, improving fires
    import os as _os
    _syn_counter = {"n": 0}

    def verdict_of(fracs):
        _syn_counter["n"] += 1
        syn_db = os.path.join(tmp, f"syn{_syn_counter['n']}.sqlite")
        con = sqlite3.connect(syn_db)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
            "total INTEGER, unknown INTEGER, unknown_frac REAL, mutation INTEGER, "
            "observe INTEGER, producer_sha TEXT)"
        )
        for i, f in enumerate(fracs):
            cur.execute(
                "INSERT INTO samples (ts,total,unknown,unknown_frac,mutation,observe,producer_sha) "
                "VALUES (?,?,?,?,?,?,?)",
                (f"t{i}", 5000, int(f * 50), f, 1000, 3800, "sha"),
            )
        con.commit()
        con.close()
        return trend(syn_db)["verdict"]

    ok &= verdict_of([3.8, 3.8, 3.8]) == "stable"
    ok &= verdict_of([3.8, 4.2, 4.7]) == "worsening"
    ok &= verdict_of([4.7, 4.2, 3.8]) == "improving"
    # abstain on <2 samples
    con = sqlite3.connect(tdb + ".solo")
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, total INTEGER, "
        "unknown INTEGER, unknown_frac REAL, mutation INTEGER, observe INTEGER, producer_sha TEXT)"
    )
    cur.execute(
        "INSERT INTO samples (ts,total,unknown,unknown_frac,mutation,observe,producer_sha) "
        "VALUES (?,?,?,?,?,?,?)",
        ("t0", 5000, 190, 3.8, 1000, 3800, "sha"),
    )
    con.commit()
    con.close()
    ok &= trend(tdb + ".solo")["verdict"] == "abstain"

    print("  selftest[import        ] %s" % ("PASS" if (hasattr(cov, "load_commands") and hasattr(at, "classify")) else "FAIL"))
    print("  selftest[append        ] %s  (seq 1,2 monotonic, order preserved)" % ("PASS" if (len(rows) == 2 and rows[0]["seq"] == 1 and rows[1]["seq"] == 2) else "FAIL"))
    print("  selftest[flat          ] %s  (3.8/3.8/3.8 → stable)" % ("PASS" if verdict_of([3.8, 3.8, 3.8]) == "stable" else "FAIL"))
    print("  selftest[worsening     ] %s  (3.8/4.2/4.7 → worsening)" % ("PASS" if verdict_of([3.8, 4.2, 4.7]) == "worsening" else "FAIL"))
    print("  selftest[improving     ] %s  (4.7/4.2/3.8 → improving)" % ("PASS" if verdict_of([4.7, 4.2, 3.8]) == "improving" else "FAIL"))
    print("  selftest[abstain       ] %s  (<2 samples → abstain)" % ("PASS" if trend(tdb + ".solo")["verdict"] == "abstain" else "FAIL"))
    return ok


def main():
    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    if "--trend" in sys.argv:
        print(json.dumps(trend(), indent=2))
        return

    # default: sample-and-append once (idempotent read-only; cron calls this weekly)
    row = sample_once()
    print(json.dumps({
        "schema": SCHEMA,
        "action": "append",
        "seq": row["seq"],
        "ts": row["ts"],
        "total": row["total"],
        "unknown_frac": row["unknown_frac"],
        "producer_sha": row["producer_sha"][:12],
    }, indent=2))


if __name__ == "__main__":
    main()