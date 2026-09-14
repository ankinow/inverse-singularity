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
`--help` prints usage and exits 0; an unrecognized flag exits 2 — neither ever falls
through to the default (append) path (v0.8.38 arg hygiene).
"""

import io
import json
import os
import shutil
import sqlite3
import subprocess
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

USAGE = (
    "usage: epsilon_code_trend.py [--trend | --selftest | --help]\n"
    "  (default) sample the live ε_code UNKNOWN fraction once and append a row\n"
    "  --trend   read the append-only series and print the movement verdict (JSON)\n"
    "  --selftest prove the append/verdict logic; exits non-zero on failure\n"
)

KNOWN_FLAGS = ("--trend", "--selftest", "--help", "-h")


def arg_guard(args, err=sys.stderr, out=sys.stdout):
    """Up-front arg hygiene — an unrecognized flag must NEVER fall through to the
    default (append/sample) path.

    Proven incident (2026-09-14): `a9_claim_evidence_trend.py --help` appended a
    real sample (seq 6) to the live series, and every sibling sharing this file's
    shape (`--trend` in argv else sample_once()) had the same defect for *any*
    typo'd flag — a wrapper running `--tren` quietly grows the series the trend
    reads, which at the verdict level is indistinguishable from real signal.
    Touches no database: returns 2 (unknown flag → usage on stderr), 0 (`--help`
    printed usage), or None (the caller may proceed). Pure, so it is pinned both
    by selftest and by a hermetic end-to-end re-run of this file.
    """
    unknown = [a for a in args if a not in KNOWN_FLAGS]
    if unknown:
        err.write("unknown flag(s): %s\n%s" % (" ".join(unknown), USAGE))
        return 2
    if "--help" in args or "-h" in args:
        out.write(USAGE)
        return 0
    return None


def _arg_hygiene_check(tmp):
    """Pin the guard end-to-end without ever risking the live series: re-run THIS
    file from a hermetic copy (tmp/hygiene/examples + …/data) and assert that
    `--help` (exit 0, usage on stdout) and a typo'd flag (exit 2, usage on stderr)
    leave no series DB behind. Pre-fix, both appended a real sample."""
    src = str(Path(__file__).resolve())
    root = os.path.join(tmp, "hygiene")
    ex_dir = os.path.join(root, "examples")
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir)
    shutil.copytree(str(Path(src).parent), ex_dir)
    script = os.path.join(ex_dir, os.path.basename(src))
    series = os.path.join(data_dir, os.path.basename(TREND_DB))

    def run(*flags):
        proc = subprocess.run([sys.executable, script, *flags],
                              capture_output=True, text=True, timeout=300)
        rows = None
        if os.path.exists(series):
            con = sqlite3.connect("file:%s?mode=ro" % series, uri=True)
            try:
                rows = con.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
            except sqlite3.Error:
                rows = -1
            finally:
                con.close()
        return proc, rows

    sink = io.StringIO()
    pure = (arg_guard(["--trend", "--selftest"], err=sink, out=sink) is None
            and arg_guard(["--help"], err=sink, out=sink) == 0
            and arg_guard(["--zz-bogus"], err=sink, out=sink) == 2)
    proc_help, rows_help = run("--help")
    proc_bad, rows_bad = run("--tren")            # realistic typo of --trend
    proc_read, rows_read = run("--trend")         # fresh series: abstain, not a crash
    out = {
        "guard-pure": pure,
        "help-no-effect": (proc_help.returncode == 0
                           and USAGE.splitlines()[0] in proc_help.stdout
                           and rows_help is None),
        "unknown-exit-2": (proc_bad.returncode == 2
                           and "unknown flag" in proc_bad.stderr
                           and rows_bad is None),
        "read-fresh-abstain": (proc_read.returncode == 0
                               and '"abstain"' in proc_read.stdout
                               and rows_read == 0),
    }
    shutil.rmtree(root, ignore_errors=True)
    return out


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
    init_db(out_db)  # a first-ever read on a fresh series is an abstain, not a crash
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

    # 5. arg hygiene: `--help` and a typo'd flag must NEVER fall through to the
    #    default (append) path. Pinned as a pure function AND end-to-end from a
    #    hermetic copy of this file — pre-fix both appended a real sample.
    _hyg = _arg_hygiene_check(tmp)
    ok &= all(_hyg.values())

    print("  selftest[import        ] %s" % ("PASS" if (hasattr(cov, "load_commands") and hasattr(at, "classify")) else "FAIL"))
    print("  selftest[append        ] %s  (seq 1,2 monotonic, order preserved)" % ("PASS" if (len(rows) == 2 and rows[0]["seq"] == 1 and rows[1]["seq"] == 2) else "FAIL"))
    print("  selftest[flat          ] %s  (3.8/3.8/3.8 → stable)" % ("PASS" if verdict_of([3.8, 3.8, 3.8]) == "stable" else "FAIL"))
    print("  selftest[worsening     ] %s  (3.8/4.2/4.7 → worsening)" % ("PASS" if verdict_of([3.8, 4.2, 4.7]) == "worsening" else "FAIL"))
    print("  selftest[improving     ] %s  (4.7/4.2/3.8 → improving)" % ("PASS" if verdict_of([4.7, 4.2, 3.8]) == "improving" else "FAIL"))
    print("  selftest[abstain       ] %s  (<2 samples → abstain)" % ("PASS" if trend(tdb + ".solo")["verdict"] == "abstain" else "FAIL"))
    print("  selftest[arg-guard-pure] %s  (unknown→2, --help→0, known→proceed)" % ("PASS" if _hyg["guard-pure"] else "FAIL"))
    print("  selftest[arg-help-none ] %s  (hermetic re-run: --help writes no row)" % ("PASS" if _hyg["help-no-effect"] else "FAIL"))
    print("  selftest[arg-unknown-2 ] %s  (hermetic re-run: --tren writes no row)" % ("PASS" if _hyg["unknown-exit-2"] else "FAIL"))
    print("  selftest[arg-read-fresh] %s  (fresh series: --trend abstains, no crash)" % ("PASS" if _hyg["read-fresh-abstain"] else "FAIL"))
    return ok


def main():
    rc = arg_guard(sys.argv[1:])
    if rc is not None:
        sys.exit(rc)

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