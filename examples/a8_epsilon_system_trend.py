#!/usr/bin/env python3
"""A8 ε_system trend — append-only time-series of the SOVEREIGNTY TERM itself.

Read-only. The a6 probe (v0.8.11) measured the runtime's own ε at a *point*,
decomposing it along the thread's axis: ε_code (the compressible enforcement gap,
1.32) vs ε_system (the chosen, could-have-done-otherwise residue, 0.021). That
answered the thread's *static* question — "does ε = 0 violate A4?" — with
"ε_system > 0 ⇒ the runtime is a recording system that could have done otherwise,
so A4 holds." But a point-in-time verdict leaves the thread's deepest face open:

  does ε_system COLLAPSE over time?

The thread's own phrasing carries the danger it names: ε_system is "the residue of
REAL work the agent chose to record — the signature of a system that 'could have
done otherwise'." Their ABSENCE at scale is the SS7 transparency gap (errors
under-reported): "the system claiming ε = 0, which the thread says collapses the
meaning of Q = φ/κ + ε." A production agent that stops emitting `⊗Er:`/`!Dc:`/`⊗RES:`
marks — under-reporting its honest residue — would let ε_system silently drift
toward zero across sessions. That drift is exactly the A4 violation the thread asks
about ("ε = 0 ⇒ never sovereign to begin with"), and today *no instrument tends it*:
ε_code has its trend (`epsilon_code_trend.py`, v0.8.20), the boundary has its trend
(`a7_boundary_trend.py`, v0.8.33) — but the sovereignty term itself, the one the
thread says must be *protected* (ε_system > 0 is the signature, not a defect), is
only ever read at a point.

This instrument closes that gap by the same discipline the ε-thread already used
for its other two faces (import a single source, append-only SQLite, `--trend`
reader with monotone-rise/past-healthiest verdicts, `--check` report-only watchdog):

  * it does **not** re-implement the measurement — it imports `parse_dir`,
    `compute`, `verdict` from `a6_epsilon_probe` (single source of truth), so the
    trend and the point-in-time probe cannot drift apart;
  * each run appends one row {seq, ts, typed, untyped_ambiguous, mislabels,
    honesty, eps_code, eps_system, probe_verdict} to
    `data/a8_epsilon_system_trend.sqlite` (append-only, `seq INTEGER PRIMARY KEY
    AUTOINCREMENT` — the v0.8.9 write-safety shape);
  * `--trend` (`schema a8-epsilon-system-trend/v1`) reads the *sovereignty term's
    movement* and reports **`sovereignty-eroding`** only on a genuine monotone fall
    of the honesty count (the raw ε_system numerator) past its healthiest (highest)
    point — the SS7 under-report going to scale; and **`sovereignty-rising`** (the
    healthy direction) only on a monotone rise past the healthiest point; it
    abstains on <2 samples. A healthy runtime is **`sovereignty-stable`**.
  * `--check` — report-only watch: **silent** (exit 0) on a healthy trend
    (`sovereignty-stable` / `sovereignty-rising` / `abstain`), and prints a compact
    `ALARM:` line + the JSON and exits 1 on the erosion verdict. The exit code is a
    *reporting* mechanism (cron delivery surfaces the movement), never a gate —
    nothing edits, prunes, or prescribes.

The Goodhart safeguard is structural and identical to its siblings: the instrument
samples and appends only. ε_system > 0 is preferred (A4: the could-have-done-
otherwise residue), but the instrument *reads its movement*, never coaxes an agent
into emitting marks — a mark emitted to satisfy a metric would itself be a mirrored
constraint (Boundary Paradox), so the only honest consumer is the alarm, never the
feedback loop.

Modes:
  * `--trend`       (explicit) — print the full JSON trend read, exit 0 always.
  * `--check`       — report-only watch: silent (exit 0) on healthy; ALARM+exit 1
    on `sovereignty-eroding`.
  * `--selftest`    — prove the fire/abstain logic; exits non-zero on failure.
  * `--help`        — print usage and exit 0; an unrecognized flag exits 2 — neither
    ever falls through to the default (append) path (v0.8.38 arg hygiene).
  * (default)       — sample-and-append once (idempotent read-only; cron weekly).
"""

import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a6_epsilon_probe as probe  # noqa: E402  (single source of truth)

DIARY = os.environ.get("HERMES_DIARY", probe.DIARY)
TREND_DB = str(Path(__file__).resolve().parent.parent / "data" / "a8_epsilon_system_trend.sqlite")
SCHEMA = "a8-epsilon-system-trend/v1"

# The trend verdicts that a report-only watchdog should surface. `sovereignty-stable`
# and `sovereignty-rising` are healthy reads (rising is the *good* direction — more
# honest residue recorded). `abstain` is honest under-sampling. The single verdict
# below means a real erosion of the sovereignty term (honesty marks falling across
# sessions — the SS7 under-report going to scale, ε_system → 0).
# This is a *reporting* classification, never a gate: nothing acts on it.
ALARM_VERDICTS = ("sovereignty-eroding",)

USAGE = (
    "usage: a8_epsilon_system_trend.py [--trend | --check | --selftest | --help]\n"
    "  (default) sample the live ε_system (honesty residue) once and append a row\n"
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
               typed INTEGER NOT NULL,
               untyped_ambiguous INTEGER NOT NULL,
               mislabels INTEGER NOT NULL,
               honesty INTEGER NOT NULL,
               eps_code REAL NOT NULL,
               eps_system REAL NOT NULL,
               probe_verdict TEXT NOT NULL
           )"""
    )
    con.commit()
    con.close()


def sample_once(diary=DIARY, out_db=TREND_DB, now=None):
    """Measure the live ε_system once and append a row. Returns the row dict."""
    tally = probe.parse_dir(diary)
    eps_code, eps_system = probe.compute(tally)
    v = probe.verdict(eps_code, eps_system)
    row = {
        "seq": None,
        "ts": now or _now_iso(),
        "typed": tally["typed_mutation"] + tally["typed_observe"],
        "untyped_ambiguous": tally["untyped_ambiguous"],
        "mislabels": tally["mislabels"],
        "honesty": tally["honesty"],
        "eps_code": round(eps_code, 6),
        "eps_system": round(eps_system, 6),
        "probe_verdict": v,
    }
    init_db(out_db)
    con = sqlite3.connect(out_db)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO samples (ts, typed, untyped_ambiguous, mislabels, honesty, "
        "eps_code, eps_system, probe_verdict) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["ts"], row["typed"], row["untyped_ambiguous"], row["mislabels"],
            row["honesty"], row["eps_code"], row["eps_system"], v,
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
        "SELECT seq, ts, typed, untyped_ambiguous, mislabels, honesty, "
        "eps_code, eps_system, probe_verdict FROM samples ORDER BY seq ASC"
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
            "last_honesty": rows[-1]["honesty"] if rows else None,
            "last_eps_system": rows[-1]["eps_system"] if rows else None,
        }

    # The *honesty count* is the movement signal (the raw ε_system numerator),
    # not the fraction: ε_system = honesty / typed, so the fraction falls whenever
    # the agent types more actions (the denominator grows) even if it records the
    # SAME residue. A verdict keyed on the fraction would fabricate "sovereignty
    # eroding" for a pure typing-volume increase (more observed work, equal honesty)
    # — the same compressible mis-read the κ-thread caught when its own reader
    # mixed κ definitions and the boundary-trend caught when it switched from
    # fractions to counts. The count measures "did the system stop recording its
    # could-have-done-otherwise residue"; the fraction is reported for reference.
    honesty = [r["honesty"] for r in rows]

    # ε_system FALLING past its healthiest (highest) point = honesty residue
    # shrinking across sessions — the SS7 under-report going to scale (ε → 0).
    honesty_hi = max(honesty)
    honesty_last = honesty[-1]
    eroding = _monotone_fall(honesty) and (honesty_last < honesty_hi)

    # ε_system RISING past its healthiest point = more honest residue recorded
    # (the healthy direction — the could-have-done-otherwise signal strengthening).
    rising = _monotone_rise(honesty) and (honesty_last > min(honesty))

    if eroding:
        verdict = "sovereignty-eroding"
    elif rising:
        verdict = "sovereignty-rising"
    else:
        verdict = "sovereignty-stable"

    eps_sys = [r["eps_system"] for r in rows]
    eps_code = [r["eps_code"] for r in rows]
    return {
        "schema": SCHEMA,
        "samples": n,
        "verdict": verdict,
        "first_honesty": honesty[0],
        "last_honesty": honesty_last,
        "min_honesty": min(honesty),
        "max_honesty": honesty_hi,
        "delta_honesty": honesty_last - honesty[0],
        "first_eps_system": eps_sys[0],
        "last_eps_system": eps_sys[-1],
        "min_eps_system": min(eps_sys),
        "delta_eps_system": round(eps_sys[-1] - eps_sys[0], 6),
        "first_eps_code": eps_code[0],
        "last_eps_code": eps_code[-1],
        "last_probe_verdict": rows[-1]["probe_verdict"],
        "last_typed": rows[-1]["typed"],
    }


def _selftest():
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  selftest[{name:18s}] {'PASS' if cond else 'FAIL'}  {note}")

    # 1. single-source imports resolve (no drift between probe and trend)
    for attr in ("parse_dir", "compute", "verdict"):
        check(f"import-{attr}", hasattr(probe, attr), "a6 probe exposes the measure")

    tmp = tempfile.mkdtemp(prefix="a8est-selftest-")

    # 2. append-does-not-replace: two samples → seq 1,2 monotonic, order preserved
    tdb = os.path.join(tmp, "trend.sqlite")
    r1 = sample_once(diary="/mnt/hermes/diary", out_db=tdb)
    r2 = sample_once(diary="/mnt/hermes/diary", out_db=tdb)
    rows = _load_series(tdb)
    check("append-not-replace", len(rows) == 2 and rows[0]["seq"] == 1 and rows[1]["seq"] == 2,
          "seq monotonic, append preserves history")
    check("append-order", rows[0]["ts"] <= rows[1]["ts"], "timestamps non-decreasing")

    # 3. sample_once captures the point-in-time verdict + counts honestly
    check("verdict-captured", isinstance(r1["probe_verdict"], str) and r1["probe_verdict"],
          "point-in-time verdict stored per sample")
    check("counts-captured", r1["honesty"] >= 0 and r1["typed"] >= 0,
          "honesty/typed counts captured")

    # 4. trend verdicts on synthetic series (honesty counts only — not fractions)
    _cnt = {"n": 0}

    def verdict_of(honesty_counts):
        _cnt["n"] += 1
        syn_db = os.path.join(tmp, f"syn{_cnt['n']}.sqlite")
        con = sqlite3.connect(syn_db)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
            "typed INTEGER, untyped_ambiguous INTEGER, mislabels INTEGER, "
            "honesty INTEGER, eps_code REAL, eps_system REAL, probe_verdict TEXT)"
        )
        for i, h in enumerate(honesty_counts):
            cur.execute(
                "INSERT INTO samples (ts,typed,untyped_ambiguous,mislabels,honesty,"
                "eps_code,eps_system,probe_verdict) VALUES (?,?,?,?,?,?,?,?)",
                (f"t{i}", 5000, 6000, 30, h, 1.32, h / 5000.0, "SOVEREIGN"),
            )
        con.commit()
        con.close()
        return trend(syn_db)["verdict"]

    # healthy: honesty flat → sovereignty-stable
    check("stable",
          verdict_of([104, 104, 104]) == "sovereignty-stable",
          "honesty count flat → stable")
    # honesty rising → sovereignty-rising (healthy direction, not an alarm)
    check("rising",
          verdict_of([104, 120, 138]) == "sovereignty-rising",
          "honesty count monotone rise → sovereignty strengthening")
    # honesty falling → sovereignty-eroding (the SS7 under-report going to scale)
    check("eroding",
          verdict_of([104, 90, 78]) == "sovereignty-eroding",
          "honesty count monotone fall → ε_system collapsing toward 0")

    # 5. abstain on <2 samples
    solo = os.path.join(tmp, "solo.sqlite")
    con = sqlite3.connect(solo)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
        "typed INTEGER, untyped_ambiguous INTEGER, mislabels INTEGER, "
        "honesty INTEGER, eps_code REAL, eps_system REAL, probe_verdict TEXT)"
    )
    cur.execute(
        "INSERT INTO samples (ts,typed,untyped_ambiguous,mislabels,honesty,"
        "eps_code,eps_system,probe_verdict) VALUES (?,?,?,?,?,?,?,?)",
        ("t0", 5000, 6000, 30, 104, 1.32, 0.021, "SOVEREIGN"),
    )
    con.commit()
    con.close()
    check("abstain", trend(solo)["verdict"] == "abstain", "<2 samples → abstain")

    # 6. the ALARM classification (the --check report contract): only
    #    `sovereignty-eroding` is surface-worthy; healthy/rising/abstain are silent.
    alarm = {"sovereignty-eroding"}
    healthy = {"sovereignty-stable", "sovereignty-rising", "abstain"}
    check("alarm-verdicts", set(ALARM_VERDICTS) == alarm,
          "exactly the erosion verdict is report-worthy")
    check("healthy-silent", alarm.isdisjoint(healthy),
          "no healthy/rising/abstain verdict is ever surfaced")

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

    # Default (no flag) samples-and-appends first — this both measures the live
    # ε_system and guarantees the DB exists before any read. `--check`/`--trend`
    # read the existing series (a first-ever `--check` with no prior sample is an
    # abstain, not a crash — init_db ensures the table exists even on a bare read).
    if "--check" not in sys.argv and "--trend" not in sys.argv:
        row = sample_once()
        print(json.dumps({
            "schema": SCHEMA,
            "action": "append",
            "seq": row["seq"],
            "ts": row["ts"],
            "typed": row["typed"],
            "untyped_ambiguous": row["untyped_ambiguous"],
            "mislabels": row["mislabels"],
            "honesty": row["honesty"],
            "eps_code": row["eps_code"],
            "eps_system": row["eps_system"],
            "probe_verdict": row["probe_verdict"],
        }, indent=2))
        return

    out = trend()
    if "--check" in sys.argv:
        verdict = out["verdict"]
        if verdict in ALARM_VERDICTS:
            print("ALARM: %s (honesty %s→%s, ε_system %s→%s)"
                  % (verdict, out["first_honesty"], out["last_honesty"],
                     out["first_eps_system"], out["last_eps_system"]))
            print(json.dumps(out, indent=2))
            sys.exit(1)
        # Healthy (sovereignty-stable / sovereignty-rising) or abstain: silent.
        sys.exit(0)

    if "--trend" in sys.argv:
        print(json.dumps(out, indent=2))
        return


if __name__ == "__main__":
    main()