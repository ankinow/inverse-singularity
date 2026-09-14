#!/usr/bin/env python3
"""A7 boundary trend — append-only time-series of the ε_code↔ε_system boundary SHAPE.

Read-only. The a7 probe (v0.8.29) measured the ε_code↔ε_system boundary *at a point*:
ε_code 2.33% (compressible surface) vs ε_boundary 1.51% (the undecidable floor) →
MIXED-BOUNDARY. That answered the thread's *static* question ("is the boundary
itself an ε?") with "partially — a compressible surface on an irreducible floor."
But a point-in-time verdict cannot answer the *temporal* face the thread implies:

  does the boundary *move*?

A single MIXED-BOUNDARY snapshot is silent on whether the undecidable floor is
genuinely irreducible (ε_boundary flat across time — the A4 wall, fixed because
never-guess is invariant) or a *moving target* (ε_boundary monotone-rising — the
floor fattening, meaning either the classifier over-extended and its guesses now
flow to the floor, or the runtime's command surface genuinely shifted toward
opaque-driver shapes). Equally, a silent regrowth of ε_code (the classifier's
compressible gap re-opening after the v0.8.12/0.8.17/0.8.18 compressions) is a
regression no point-read catches.

This instrument closes both gaps by the same discipline the κ-Proliferation thread
used for dQ/dt (`kappa_proliferation_timeseries.py --trend`, v0.8.9), the CURIOSITY
thread used for self-bloat (`curiosity_kappa_trend.py`, v0.8.14), and the ε-thread
used for its own residual (`epsilon_code_trend.py`, v0.8.20):

  * it does **not** re-implement the measurement — it imports `bin_unknown`,
    `measure`, `verdict` from `a7_boundary_probe` (single source of truth), so the
    trend and the point-in-time probe cannot drift apart;
  * each run appends one row {seq, ts, total, code, boundary, code_frac,
    boundary_frac, boundary_ratio, verdict} to `data/a7_boundary_trend.sqlite`
    (append-only, `seq INTEGER PRIMARY KEY AUTOINCREMENT` — the v0.8.9 write-safety
    shape);
  * `--trend` (`schema a7-boundary-trend/v1`) reads the *boundary movement* and
    reports a **`boundary-widening`** verdict only on a genuine monotone rise of the
    ε_boundary fraction past its healthiest (lowest) point, and a separate
    **`code-regressing`** verdict only on a genuine monotone rise of the ε_code
    fraction past its healthiest (lowest) point; it abstains on <2 samples. A
    healthy runtime is **`boundary-stable`** (floor flat, code compressing/holding).

The Goodhart safeguard is structural, identical to its siblings: the instrument
samples and appends only — no gate, no decision path, no prescriptive consumer.
ε_boundary > 0 is the signature of the A4 never-guess wall, not a defect to
optimize away; the trend *reads its movement*, never acts on it.

Modes:
  * `--trend`       (explicit) — print the full JSON trend read, exit 0 always.
  * `--check`       — report-only watch: **silent** (exit 0) on a healthy trend
    (`boundary-stable` / `boundary-receding` / `abstain`), and prints a compact
    `ALARM:` line + the JSON and exits 1 on the movement verdicts that mean a
    real regression (`boundary-widening`, `code-regressing`, `both-worsening`).
    The exit code is a *reporting* mechanism (so a cron delivery surfaces the
    movement), NOT a gate on any action — nothing edits or prescribes (the same
    contract as `axiom_joint_trend.py --check` and `a5_constraint_provenance.py
    --check`).
  * `--selftest`    — prove the fire/abstain logic; exits non-zero on failure.
  * `--help`        — print usage and exit 0; an unrecognized flag exits 2 — neither
    ever falls through to the default (append) path (v0.8.38 arg hygiene).
  * (default)       — sample-and-append once (idempotent read-only; cron weekly).
"""

import io
import json
import shutil
import sqlite3
import subprocess
import sys
import time
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a7_boundary_probe as probe  # noqa: E402  (single source of truth)

DB = "/mnt/hermes/state.db"
TREND_DB = str(Path(__file__).resolve().parent.parent / "data" / "a7_boundary_trend.sqlite")
SCHEMA = "a7-boundary-trend/v1"

# The trend verdicts that a report-only watchdog should surface. `boundary-stable`
# and `boundary-receding` are healthy reads (receding is the *good* direction — the
# floor shrinking as the classifier recovers more intent); `abstain` is honest
# under-sampling. The three below mean a real regression in the boundary shape.
# This is a *reporting* classification, never a gate: nothing acts on it.
ALARM_VERDICTS = ("boundary-widening", "code-regressing", "both-worsening")

USAGE = (
    "usage: a7_boundary_trend.py [--trend | --check | --selftest | --help]\n"
    "  (default) sample the live ε_code/ε_boundary split once and append a row\n"
    "  --trend   read the append-only series and print the movement verdict (JSON)\n"
    "  --check   report-only watchdog: silent on healthy, ALARM + exit 1 otherwise\n"
    "  --selftest prove the fire/abstain/append logic; exits non-zero on failure\n"
)

KNOWN_FLAGS = ("--trend", "--check", "--selftest", "--help", "-h")


def arg_guard(args, err=sys.stderr, out=sys.stdout):
    """Up-front arg hygiene — an unrecognized flag must NEVER fall through to the
    default (append/sample) path.

    Proven incident (2026-09-14): `a9_claim_evidence_trend.py --help` appended a
    real sample (seq 6) to the live series, and every sibling sharing this file's
    shape (`if "--check" not in argv …: sample_once()`) had the same defect for
    *any* typo'd flag — a wrapper running `--chek` quietly grows the series the
    trend reads, which at the verdict level is indistinguishable from real signal.
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
    pure = (arg_guard(["--trend", "--check", "--selftest"], err=sink, out=sink) is None
            and arg_guard(["--help"], err=sink, out=sink) == 0
            and arg_guard(["--zz-bogus"], err=sink, out=sink) == 2)
    proc_help, rows_help = run("--help")
    proc_bad, rows_bad = run("--chek")            # realistic typo of --check
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
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db(path=TREND_DB):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS samples (
               seq INTEGER PRIMARY KEY AUTOINCREMENT,
               ts TEXT NOT NULL,
               total INTEGER NOT NULL,
               code INTEGER NOT NULL,
               boundary INTEGER NOT NULL,
               code_frac REAL NOT NULL,
               boundary_frac REAL NOT NULL,
               boundary_ratio REAL NOT NULL,
               verdict TEXT NOT NULL
           )"""
    )
    con.commit()
    con.close()


def sample_once(db=DB, out_db=TREND_DB, now=None):
    """Measure the live boundary once and append a row. Returns the row dict."""
    bins, total, code_frac, boundary_frac = probe.measure(db)
    code = bins["code"]
    boundary = bins["boundary"]
    # boundary_ratio is the verdict axis in the a7 probe: boundary/code (the floor
    # vs the compressible surface). Infinity when code==0 (all residual is floor).
    boundary_ratio = (boundary / code) if code > 0 else float("inf")
    v = probe.verdict(code, boundary)
    row = {
        "seq": None,
        "ts": now or _now_iso(),
        "total": total,
        "code": code,
        "boundary": boundary,
        "code_frac": round(code_frac, 6),
        "boundary_frac": round(boundary_frac, 6),
        "boundary_ratio": boundary_ratio,
        "verdict": v,
    }
    init_db(out_db)
    con = sqlite3.connect(out_db)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO samples (ts, total, code, boundary, code_frac, boundary_frac, "
        "boundary_ratio, verdict) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["ts"], row["total"], code, boundary,
            row["code_frac"], row["boundary_frac"], row["boundary_ratio"], v,
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
        "SELECT seq, ts, total, code, boundary, code_frac, boundary_frac, "
        "boundary_ratio, verdict FROM samples ORDER BY seq ASC"
    )
    rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
    con.close()
    return rows


def _monotone_rise(vals):
    return all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))


def _monotone_fall(vals):
    return all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))


def trend(out_db=TREND_DB):
    rows = _load_series(out_db)
    n = len(rows)
    if n < 2:
        return {
            "schema": SCHEMA,
            "samples": n,
            "verdict": "abstain",
            "reason": "fewer than 2 samples",
            "last_code_count": rows[-1]["code"] if rows else None,
            "last_boundary_count": rows[-1]["boundary"] if rows else None,
        }

    # The *counts* are the movement signal, not the fractions: a fraction falls
    # when the denominator grows (unrelated observations swell `total`), but the
    # floor "receding" should mean the *undecidable count* actually shrank. Basing
    # the verdict on fractions would fabricate "floor receded" for a pure
    # count-dilution (same code/boundary counts, larger total) — the same
    # compressible mis-read the κ-thread caught when its own reader mixed κ
    # definitions. Counts measure "did the floor get bigger"; fractions are
    # reported for reference only.
    code_counts = [r["code"] for r in rows]
    bound_counts = [r["boundary"] for r in rows]

    # ε_code re-growing past its healthiest (lowest) point = classifier gap re-opening
    code_lo = min(code_counts)
    code_last = code_counts[-1]
    code_regressing = _monotone_rise(code_counts) and (code_last > code_lo)

    # ε_boundary re-growing past its healthiest (lowest) point = the floor is moving
    # (either classifier over-extension or genuine surface shift toward opaque shapes)
    bound_lo = min(bound_counts)
    bound_last = bound_counts[-1]
    boundary_widening = _monotone_rise(bound_counts) and (bound_last > bound_lo)

    # ε_boundary *shrinking* (the floor receding) is the healthy direction — the
    # classifier proving more intent recoverable than the prior floor assumed.
    boundary_receding = _monotone_fall(bound_counts) and (bound_last < max(bound_counts))

    if boundary_widening and code_regressing:
        verdict = "both-worsening"
    elif boundary_widening:
        verdict = "boundary-widening"
    elif code_regressing:
        verdict = "code-regressing"
    elif boundary_receding:
        verdict = "boundary-receding"
    else:
        verdict = "boundary-stable"

    code_fracs = [r["code_frac"] for r in rows]
    bound_fracs = [r["boundary_frac"] for r in rows]
    return {
        "schema": SCHEMA,
        "samples": n,
        "verdict": verdict,
        "first_code_count": code_counts[0],
        "last_code_count": code_last,
        "min_code_count": code_lo,
        "delta_code_count": code_last - code_counts[0],
        "first_boundary_count": bound_counts[0],
        "last_boundary_count": bound_last,
        "min_boundary_count": bound_lo,
        "delta_boundary_count": bound_last - bound_counts[0],
        "first_code_frac": code_fracs[0],
        "last_code_frac": code_fracs[-1],
        "min_code_frac": min(code_fracs),
        "delta_code_frac": round(code_fracs[-1] - code_fracs[0], 6),
        "first_boundary_frac": bound_fracs[0],
        "last_boundary_frac": bound_fracs[-1],
        "min_boundary_frac": min(bound_fracs),
        "delta_boundary_frac": round(bound_fracs[-1] - bound_fracs[0], 6),
        "last_verdict": rows[-1]["verdict"],
        "last_total": rows[-1]["total"],
    }


def _selftest():
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  selftest[{name:18s}] {'PASS' if cond else 'FAIL'}  {note}")

    # 1. single-source imports resolve (no drift between probe and trend)
    for attr in ("measure", "bin_unknown", "verdict"):
        check(f"import-{attr}", hasattr(probe, attr), "a7 probe exposes the measure")

    tmp = tempfile.mkdtemp(prefix="a7bt-selftest-")

    # 2. append-does-not-replace: two samples → seq 1,2 monotonic, order preserved
    tdb = os.path.join(tmp, "trend.sqlite")
    r1 = sample_once(out_db=tdb)
    r2 = sample_once(out_db=tdb)
    rows = _load_series(tdb)
    check("append-not-replace", len(rows) == 2 and rows[0]["seq"] == 1 and rows[1]["seq"] == 2,
          "seq monotonic, append preserves history")
    check("append-order", rows[0]["ts"] <= rows[1]["ts"], "timestamps non-decreasing")

    # 3. sample_once captures the point-in-time verdict string exactly once
    check("verdict-captured", isinstance(r1["verdict"], str) and r1["verdict"],
          "point-in-time verdict stored per sample")

    # 4. trend verdicts on synthetic series
    _cnt = {"n": 0}

    def verdict_of(code_fracs, bound_fracs):
        _cnt["n"] += 1
        syn_db = os.path.join(tmp, f"syn{_cnt['n']}.sqlite")
        con = sqlite3.connect(syn_db)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
            "total INTEGER, code INTEGER, boundary INTEGER, code_frac REAL, "
            "boundary_frac REAL, boundary_ratio REAL, verdict TEXT)"
        )
        for i, (cf, bf) in enumerate(zip(code_fracs, bound_fracs)):
            cur.execute(
                "INSERT INTO samples (ts,total,code,boundary,code_frac,boundary_frac,"
                "boundary_ratio,verdict) VALUES (?,?,?,?,?,?,?,?)",
                (f"t{i}", 5000, int(cf * 50), int(bf * 50), cf, bf,
                 (bf / cf if cf else float("inf")), "MIXED-BOUNDARY"),
            )
        con.commit()
        con.close()
        return trend(syn_db)["verdict"]

    # healthy: floor flat, code compressing → boundary-stable
    check("stable",
          verdict_of([2.33, 2.20, 2.10], [1.51, 1.51, 1.51]) == "boundary-stable",
          "floor flat + code compressing → healthy")
    # floor widening → boundary-widening
    check("widening",
          verdict_of([2.33, 2.30, 2.33], [1.51, 1.70, 1.92]) == "boundary-widening",
          "ε_boundary monotone rise → the floor moves")
    # code regressing → code-regressing
    check("code-regress",
          verdict_of([2.33, 2.60, 2.90], [1.51, 1.48, 1.51]) == "code-regressing",
          "ε_code monotone rise → classifier gap re-opens")
    # both → both-worsening
    check("both",
          verdict_of([2.33, 2.60, 2.90], [1.51, 1.70, 1.92]) == "both-worsening",
          "both faces rising together")
    # floor receding → boundary-receding (healthy direction)
    check("receding",
          verdict_of([2.33, 2.30, 2.25], [1.51, 1.30, 1.10]) == "boundary-receding",
          "ε_boundary fall → floor receding")

    # 5. abstain on <2 samples
    solo = os.path.join(tmp, "solo.sqlite")
    con = sqlite3.connect(solo)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
        "total INTEGER, code INTEGER, boundary INTEGER, code_frac REAL, "
        "boundary_frac REAL, boundary_ratio REAL, verdict TEXT)"
    )
    cur.execute(
        "INSERT INTO samples (ts,total,code,boundary,code_frac,boundary_frac,"
        "boundary_ratio,verdict) VALUES (?,?,?,?,?,?,?,?)",
        ("t0", 5000, 116, 75, 2.33, 1.51, 0.6465, "MIXED-BOUNDARY"),
    )
    con.commit()
    con.close()
    check("abstain", trend(solo)["verdict"] == "abstain", "<2 samples → abstain")

    # 6. the ALARM classification (the --check report contract): only the three
    #    regression verdicts are surface-worthy; every healthy/abstain read is silent.
    alarm = {"boundary-widening", "code-regressing", "both-worsening"}
    healthy = {"boundary-stable", "boundary-receding", "abstain"}
    check("alarm-verdicts", set(ALARM_VERDICTS) == alarm,
          "exactly the three regression verdicts are report-worthy")
    check("healthy-silent", alarm.isdisjoint(healthy),
          "no healthy/abstain verdict is ever surfaced")

    # 7. arg hygiene: `--help` and a typo'd flag must NEVER fall through to the
    #    default (append) path. Pinned as a pure function AND end-to-end from a
    #    hermetic copy of this file — pre-fix both appended a real sample.
    for _name, _good in _arg_hygiene_check(tmp).items():
        check(f"arg-{_name}", _good,
              "guard runs before any DB access (hermetic re-run of this file)")

    return ok


def main():
    rc = arg_guard(sys.argv[1:])
    if rc is not None:
        sys.exit(rc)

    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    out = trend()
    if "--check" in sys.argv:
        verdict = out["verdict"]
        if verdict in ALARM_VERDICTS:
            print("ALARM: %s (ε_code=%s→%s, ε_boundary=%s→%s)"
                  % (verdict, out["first_code_count"], out["last_code_count"],
                     out["first_boundary_count"], out["last_boundary_count"]))
            print(json.dumps(out, indent=2))
            sys.exit(1)
        # Healthy (boundary-stable / boundary-receding) or abstain: silent.
        sys.exit(0)

    if "--trend" in sys.argv:
        print(json.dumps(out, indent=2))
        return

    # default: sample-and-append once (idempotent read-only; cron calls this weekly)
    row = sample_once()
    print(json.dumps({
        "schema": SCHEMA,
        "action": "append",
        "seq": row["seq"],
        "ts": row["ts"],
        "total": row["total"],
        "code": row["code"],
        "boundary": row["boundary"],
        "code_frac": row["code_frac"],
        "boundary_frac": row["boundary_frac"],
        "boundary_ratio": ("inf" if row["boundary_ratio"] == float("inf")
                           else round(row["boundary_ratio"], 4)),
        "verdict": row["verdict"],
    }, indent=2))


if __name__ == "__main__":
    main()