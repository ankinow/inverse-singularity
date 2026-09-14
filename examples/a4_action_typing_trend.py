#!/usr/bin/env python3
"""A4 action-typing trend — append-only time-series of the typed action-intent signal.

Read-only. The κ Proliferation thread's central question — *"can you measure the
point where adding a new capability decreases Q?"* — was answered on the dense
tool-histogram signal by `a3_dense_phi.py` (v0.7.8) with a NULL, and the null
named its own blocker: density cannot separate *verification* from genuine
*mutation*. `theory/action-typing.md` + `a4_action_typing.py` (v0.7.9) closed that
with a LOGGING-DOCTRINE instrument — per-block intent markers (`⊗S:mutation` /
`⊗S:observe`) and a mutation-rate curve bucketed at median κ — and it shipped
ABSTAINing: production typed coverage was 0% because the doctrine had no producer.
The `session-scribe` producer (v1.1.0, 2026-08-25) then made the marker structural,
and the typed signal accumulated *silently*: nothing trended it. The instrument's
own forward-only sentence ("once coverage clears 15% with >= 30 typed sessions this
ABSTAIN turns into the defensible curve") was a condition no clock watched, and a
regression of the producer — the ⊗S: stream dying, the exact dead-letter shape the
a9 trend measured for the layer-3 claim grammar — would be invisible in a
point-in-time run.

This instrument closes that gap by the identical sibling discipline (single-source
import, append-only SQLite, count-keyed monotone verdicts, `--check` report-only
watchdog, `--selftest` proving fire/abstain):

  * it does **not** re-implement the measure — it imports `parse_diary`/`analyze`
    from `a4_action_typing` (the typed curve's single source of truth), so the
    trend and the curve cannot drift apart;
  * each run samples the live diary and appends one row {seq, ts, files, sessions,
    typed_sessions, blocks_typed, blocks_inferred, blocks_unknown, coverage,
    mislabels, curve_state, mut_low, rho, ratio} to
    `data/a4_action_typing_trend.sqlite` (append-only,
    `seq INTEGER PRIMARY KEY AUTOINCREMENT` — the v0.8.9 write-safety shape). The
    `files` column is the confounder made visible: diary retention (files rotating
    out) can *lower* a cumulative count without the producer dying, so an erosion
    read is attributable, not asserted.
  * `--trend` (`schema a4-action-typing-trend/v1`) reads the **typed block count**
    movement — the signal's existence — and reports **`signal-eroding`** only on a
    genuine monotone fall past its healthiest (highest) point (the ⊗S: producer
    going dead at scale), **`signal-rising`** on a monotone rise (the healthy
    direction — the producer accumulating), else `signal-stable`; abstains <2.
    The verdict is keyed on the **count**, never the fraction: coverage = typed /
    total falls whenever the diary grows faster than the producer — the same
    compressible mis-read the κ, boundary, ε_system and claim trend readers each
    caught.
  * `--check` is the scheduled-consumer form: **silent** (exit 0) on a healthy
    trend (`signal-stable` / `signal-rising` / `abstain`) with no curve detection;
    prints `ALARM:` + JSON and exits 1 on `signal-eroding` AND on a latest-sample
    `collapse-detected` — the thread's own falsifiable claim firing (mutation rate
    falling as κ passes the turnover point). The exit code is a *reporting*
    mechanism, never a gate: nothing edits, prunes, or prescribes.

Goodhart safeguard is structural and identical to its siblings: samples-and-appends
only. The instrument never coaxes a marker — an ⊗S: emitted to feed this metric
would itself be a mirrored constraint (Boundary Paradox), and the only honest
consumer is the alarm.
"""

import json
import os
import sqlite3
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a4_action_typing as a4  # noqa: E402  (single source of truth)

DIARY = os.environ.get("HERMES_DIARY", a4.DIARY)
TREND_DB = str(Path(__file__).resolve().parent.parent / "data" / "a4_action_typing_trend.sqlite")
SCHEMA = "a4-action-typing-trend/v1"

# The trend verdict a report-only watchdog surfaces: the typed signal's *existence*
# falling (the ⊗S: producer going dead — the input side of the typed curve, exactly
# the dead-letter shape a9 measured for the claim grammar). `signal-rising` is the
# healthy direction and `signal-stable` a healthy plateau; `abstain` is honest
# under-sampling. The curve state `collapse-detected` is the *substantive* finding
# (the thread's falsifiable claim firing on live data) and is surfaced too — both
# are reporting classifications; nothing acts on either.
ALARM_VERDICTS = ("signal-eroding",)
ALARM_CURVE_STATES = ("collapse-detected",)

USAGE = (
    "usage: a4_action_typing_trend.py [--trend | --check | --selftest | --help]\n"
    "  (default) sample the live diary once and append a row\n"
    "  --trend   read the append-only series and print the movement verdict (JSON)\n"
    "  --check   report-only watchdog: silent on healthy, ALARM + exit 1 otherwise\n"
    "  --selftest prove the fire/abstain/append logic; exits non-zero on failure\n"
)


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _diary_files(diary=DIARY):
    """Count the diary files in the sampled window (the erosion confounder)."""
    try:
        return len([f for f in os.listdir(diary) if f.endswith(".md") and f[:4].isdigit()])
    except OSError:
        return 0


def init_db(path=TREND_DB):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS samples (
               seq INTEGER PRIMARY KEY AUTOINCREMENT,
               ts TEXT NOT NULL,
               files INTEGER NOT NULL,
               sessions INTEGER NOT NULL,
               typed_sessions INTEGER NOT NULL,
               blocks_typed INTEGER NOT NULL,
               blocks_inferred INTEGER NOT NULL,
               blocks_unknown INTEGER NOT NULL,
               coverage REAL NOT NULL,
               mislabels INTEGER NOT NULL,
               curve_state TEXT NOT NULL,
               mut_low REAL,
               rho REAL,
               ratio REAL
           )"""
    )
    con.commit()
    con.close()


def sample_once(diary=DIARY, out_db=TREND_DB, now=None):
    """Measure the typed action-intent signal once and append a row. Returns it."""
    sessions = a4.parse_diary(diary)
    a = a4.analyze(sessions)
    row = {
        "seq": None,
        "ts": now or _now_iso(),
        "files": _diary_files(diary),
        "sessions": a["sessions"],
        "typed_sessions": a["typed_sessions"],
        "blocks_typed": a["blocks_typed"],
        "blocks_inferred": a["blocks_inferred"],
        "blocks_unknown": a["blocks_unknown"],
        "coverage": round(a["coverage"], 6),
        "mislabels": a["mislabels"],
        "curve_state": a["curve_state"],
        "mut_low": None if a["mut_low"] is None else round(a["mut_low"], 6),
        "rho": None if a["rho"] is None else round(a["rho"], 6),
        "ratio": None if a["ratio"] is None else round(a["ratio"], 6),
    }
    init_db(out_db)
    con = sqlite3.connect(out_db)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO samples (ts, files, sessions, typed_sessions, blocks_typed, "
        "blocks_inferred, blocks_unknown, coverage, mislabels, curve_state, "
        "mut_low, rho, ratio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["ts"], row["files"], row["sessions"], row["typed_sessions"],
            row["blocks_typed"], row["blocks_inferred"], row["blocks_unknown"],
            row["coverage"], row["mislabels"], row["curve_state"],
            row["mut_low"], row["rho"], row["ratio"],
        ),
    )
    row["seq"] = cur.lastrowid
    con.commit()
    con.close()
    return row


def _load_series(out_db=TREND_DB):
    init_db(out_db)
    con = sqlite3.connect(f"file:{out_db}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute(
        "SELECT seq, ts, files, sessions, typed_sessions, blocks_typed, "
        "blocks_inferred, blocks_unknown, coverage, mislabels, curve_state, "
        "mut_low, rho, ratio FROM samples ORDER BY seq ASC"
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
            "last_typed": rows[-1]["blocks_typed"] if rows else None,
            "last_curve_state": rows[-1]["curve_state"] if rows else None,
        }

    # The *typed block count* is the movement signal (the raw producer output),
    # not the coverage fraction: coverage = typed / (typed + inferred + unknown),
    # so the fraction falls whenever the diary grows faster than the producer even
    # if the SAME number of markers is emitted. A verdict keyed on the fraction
    # would fabricate "eroding" for a pure volume increase — the compressible
    # mis-read the κ, boundary, ε_system and claim trends each caught. The count
    # answers "is the ⊗S: producer still emitting"; the fraction is reported.
    counts = [r["blocks_typed"] for r in rows]
    peak = max(counts)
    last = counts[-1]
    eroding = _monotone_fall(counts) and (last < peak)
    rising = _monotone_rise(counts) and (last > min(counts))

    if eroding:
        verdict = "signal-eroding"
    elif rising:
        verdict = "signal-rising"
    else:
        verdict = "signal-stable"

    files = [r["files"] for r in rows]
    return {
        "schema": SCHEMA,
        "samples": n,
        "verdict": verdict,
        "first_typed": counts[0],
        "last_typed": last,
        "min_typed": min(counts),
        "max_typed": peak,
        "delta_typed": last - counts[0],
        "first_files": files[0],
        "last_files": files[-1],
        "delta_files": files[-1] - files[0],
        "last_sessions": rows[-1]["sessions"],
        "last_typed_sessions": rows[-1]["typed_sessions"],
        "last_coverage": rows[-1]["coverage"],
        "last_curve_state": rows[-1]["curve_state"],
        "last_mut_low": rows[-1]["mut_low"],
        "last_rho": rows[-1]["rho"],
        "last_ratio": rows[-1]["ratio"],
    }


def _check(out):
    """Report-only watchdog body: returns an exit code, prints only on alarm."""
    verdict = out["verdict"]
    last_state = out.get("last_curve_state")
    alarmed = verdict in ALARM_VERDICTS or last_state in ALARM_CURVE_STATES
    if not alarmed:
        return 0
    if verdict in ALARM_VERDICTS:
        print("ALARM: %s (typed %s→%s, files %s→%s)"
              % (verdict, out["first_typed"], out["last_typed"],
                 out["first_files"], out["last_files"]))
    if last_state in ALARM_CURVE_STATES:
        print("ALARM: action-intent-collapse (mut_low=%s, ρ=%s, ratio=%s)"
              % (out["last_mut_low"], out["last_rho"], out["last_ratio"]))
    print(json.dumps(out, indent=2))
    return 1


def _write_synthetic_diary(root, sessions=3, lines_per_session=10):
    """Hermetic diary fixture: N sessions of `!Sd/on … !Sd/off` with typed blocks."""
    path = os.path.join(root, "2026-01-01.md")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(sessions):
            fh.write(f"!Sd/on sid=syn-{i}\n")
            for j in range(lines_per_session):
                fh.write(">T:patch\n")
                fh.write("⊗S:mutation\n")
            fh.write("!Sd/off\n")
    return path


def _selftest():
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  selftest[{name:22s}] {'PASS' if cond else 'FAIL'}  {note}")

    # 1. single-source imports resolve (no local re-implementation of the measure)
    for attr in ("parse_diary", "analyze"):
        check(f"import-{attr}", hasattr(a4, attr), "a4 instrument exposes the measure")
    check("kind-set-pinned", a4.MIN_SESSIONS >= 1 and 0 < a4.COVERAGE_FLOOR < 1,
          "floor/abstain constants present, never re-declared here")

    tmp = tempfile.mkdtemp(prefix="a4est-selftest-")
    diary = os.path.join(tmp, "diary")
    os.makedirs(diary)
    _write_synthetic_diary(diary)

    # 2. end-to-end sample on a hermetic diary: parse → analyze → append
    tdb = os.path.join(tmp, "trend.sqlite")
    r1 = sample_once(diary=diary, out_db=tdb)
    check("sample-typed", r1["blocks_typed"] > 0 and r1["typed_sessions"] == 3,
          f"typed={r1['blocks_typed']} typed_sessions={r1['typed_sessions']}")
    check("sample-files", r1["files"] == 1, "diary file count captured (erosion confounder)")
    check("sample-state", r1["curve_state"] == "abstain",
          "3 typed sessions < MIN_SESSIONS → abstain (never a fabricated curve)")

    # 3. append-does-not-replace: seq monotonic, both rows preserved
    r2 = sample_once(diary=diary, out_db=tdb)
    rows = _load_series(tdb)
    check("append-not-replace", len(rows) == 2 and rows[0]["seq"] == 1 and rows[1]["seq"] == 2,
          "seq monotonic, append preserves history")
    check("append-order", rows[0]["ts"] <= rows[1]["ts"], "timestamps non-decreasing")

    # 4. trend verdicts on synthetic series (typed COUNTS only — never fractions)
    _cnt = {"n": 0}

    def verdict_of(counts):
        _cnt["n"] += 1
        syn = os.path.join(tmp, f"syn{_cnt['n']}.sqlite")
        con = sqlite3.connect(syn)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
            "files INTEGER, sessions INTEGER, typed_sessions INTEGER, blocks_typed INTEGER, "
            "blocks_inferred INTEGER, blocks_unknown INTEGER, coverage REAL, mislabels INTEGER, "
            "curve_state TEXT, mut_low REAL, rho REAL, ratio REAL)"
        )
        for i, c in enumerate(counts):
            cur.execute(
                "INSERT INTO samples (ts, files, sessions, typed_sessions, blocks_typed, "
                "blocks_inferred, blocks_unknown, coverage, mislabels, curve_state, "
                "mut_low, rho, ratio) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"t{i}", 20, 200, 120, c, 4000, 3500, c / 10000.0, 0, "no-collapse",
                 0.14, 0.286, 0.69),
            )
        con.commit()
        con.close()
        return trend(syn)["verdict"]

    check("stable", verdict_of([3259, 3259, 3259]) == "signal-stable",
          "flat count → stable")
    check("rising", verdict_of([3000, 3200, 3259]) == "signal-rising",
          "monotone rise → producer accumulating (healthy)")
    check("eroding", verdict_of([3259, 3100, 2900]) == "signal-eroding",
          "monotone fall past peak → producer dying (alarm)")

    # 5. abstain on <2 samples
    solo = os.path.join(tmp, "solo.sqlite")
    init_db(solo)
    check("abstain", trend(solo)["verdict"] == "abstain", "<2 samples → abstain")

    # 6. curve-state bridge: the normalization the watchdog classifies on
    def state_of(sessions):
        return a4.analyze(sessions)["curve_state"]

    check("state-no-signal", state_of([]) == "no-signal", "empty diary → no-signal")

    def synth_sessions(k_vals, mut_for):
        out = []
        for k in k_vals:
            mut = mut_for(k)
            out.append({
                "date": "syn.md", "sid": f"syn-{k}", "mislabels": 0, "unknown": 0,
                "blocks": Counter({"mutation": int(mut * 100),
                                   "observe": int((1 - mut) * 100)}),
                "inferred": Counter(),
                "tools": Counter({"terminal": k}),
            })
        return out

    k_vals = [8, 10, 12, 16, 20, 28, 36, 50, 70, 90, 120, 150,
              180, 240, 320, 400, 500, 600, 700, 800,
              900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
    collapse = synth_sessions(k_vals, lambda k: 0.85 if k <= 40 else 0.15)
    flat = synth_sessions(k_vals, lambda k: 0.55)
    check("state-collapse", state_of(collapse) == "collapse-detected",
          "intent collapse fires the same detection a4 prints")
    check("state-no-collapse", state_of(flat) == "no-collapse",
          "flat control stays quiet")
    check("state-abstain-small", state_of(collapse[:4]) == "abstain",
          "tiny sample abstains")

    # 7. alarm contract: only erosion is surface-worthy on the movement axis,
    #    and only collapse-detected is surface-worthy on the curve axis
    check("alarm-verdicts", set(ALARM_VERDICTS) == {"signal-eroding"},
          "exactly the erosion verdict is report-worthy")
    check("alarm-curve", set(ALARM_CURVE_STATES) == {"collapse-detected"},
          "only the firing claim is report-worthy")
    healthy = {"signal-stable", "signal-rising", "abstain"}
    check("healthy-silent", set(ALARM_VERDICTS).isdisjoint(healthy),
          "no healthy/rising/abstain verdict is ever surfaced")

    return ok


def main():
    args = [a for a in sys.argv[1:]]
    unknown = [a for a in args if a not in ("--trend", "--check", "--selftest", "--help", "-h")]
    if unknown:
        # Arg hygiene: an unrecognized flag must never silently run the default
        # (append) path — the a9 instrument's `--help` appended a sample.
        sys.stderr.write(f"unknown flag(s): {' '.join(unknown)}\n{USAGE}")
        sys.exit(2)
    if "--help" in args or "-h" in args:
        print(USAGE, end="")
        sys.exit(0)

    if "--selftest" in args:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    # Default (no flag) samples-and-appends first — this both measures the live
    # signal and guarantees the DB exists before any read. `--check`/`--trend`
    # read the existing series (a first-ever `--check` with no prior sample is an
    # abstain, not a crash — init_db ensures the table exists even on a bare read).
    if "--check" not in args and "--trend" not in args:
        row = sample_once()
        print(json.dumps({"schema": SCHEMA, "action": "append", **row}, indent=2))
        return

    out = trend()
    if "--check" in args:
        sys.exit(_check(out))

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
