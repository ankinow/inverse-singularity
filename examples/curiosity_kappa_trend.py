#!/usr/bin/env python3
"""curiosity_kappa_trend.py — append-only time-series for CURIOSITY.md self-bloat.

The sibling instrument `curiosity_kappa.py` (v0.8.13) makes the "cure and
disease share a file" self-bloat recursion FALSIFIABLE as a point-in-time
verdict: it flags any *answered* CURIOSITY.md thread whose dispatch-history
byte κ exceeds the median history of still-*open* threads. Its open residue is
the same gap the κ-Proliferation thread closed with `kappa_proliferation_
timeseries.py --trend` (v0.8.9): *a read-only instrument that reports a verdict
once cannot make the verdict's `trend` visible.* A one-shot SELF-BLOAT read is
a snapshot; a self-bloat that *grows* across weeks is the disease the thread
named ("the starter re-fed after the bread is done", compounding).

This harness closes that residue by the same discipline:

  * it does NOT re-implement the parser — it imports `curiosity_kappa`'s
    `parse_curiosity` / `compute` (single source of truth, no drift);
  * each run appends one row {ts, threads, total_bytes, open/resolved/closed,
    largest_thread, bloated[], verdict} to an append-only SQLite series
    (`seq INTEGER PRIMARY KEY AUTOINCREMENT` — the v0.8.9 write-safety shape);
  * `--trend` reads the self-bloat gradient (bloat_count, bloated_bytes,
    total_bytes) over the series and reports a `worsening` verdict only on a
    genuine monotone rise past a peak — read-only, never acts;
  * `--selftest` proves the compute wrap, append-does-not-replace, trend
    verdicts, and an abstain-on-tiny-sample control.

Zero dependencies. Stdlib only. Read-only with respect to CURIOSITY.md (only
the series DB is written, and only ever appended). Goodhart preserved: the
metric flags and trends, never prescribes a decay or moves a thread.

Usage:
    python3 curiosity_kappa_trend.py            # sample + append
    python3 curiosity_kappa_trend.py --show     # print the stored series
    python3 curiosity_kappa_trend.py --trend    # print the self-bloat gradient
    python3 curiosity_kappa_trend.py --selftest # deterministic self-check
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

# --- runtime-root + sibling-instrument resolution (relocation-tolerant) ------
_RUNTIME_CANDIDATES = [
    os.environ.get("IST_RUNTIME"),
    "/run/media/lermf/DADOS_STORAGE/@projetos/Projetos/ist-runtime",
    "/mnt/projetos/Projetos/ist-runtime",
    os.path.expanduser("~/ist-runtime"),
]
RUNTIME_ROOT = next(
    (c for c in _RUNTIME_CANDIDATES if c and os.path.isdir(os.path.expanduser(c))),
    os.path.expanduser("~/ist-runtime"),
)

# DB path is overridable for tests (never touches production data).
DB_PATH = os.environ.get("IST_CURIOSITY_KAPPA_DB") or os.path.join(
    os.path.expanduser(RUNTIME_ROOT), "data", "curiosity_kappa_trend.sqlite")


def _load_sibling():
    """Import curiosity_kappa.py's parse/compute (single source of truth)."""
    sibling = os.path.join(RUNTIME_ROOT, "examples", "curiosity_kappa.py")
    if not os.path.isfile(sibling):
        # fall back to next-to-self resolution
        here = os.path.dirname(os.path.abspath(__file__))
        sibling = os.path.join(here, "curiosity_kappa.py")
    spec = importlib.util.spec_from_file_location("curiosity_kappa", sibling)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load sibling instrument: {sibling}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["curiosity_kappa"] = mod
    spec.loader.exec_module(mod)
    return mod


SIBLING = _load_sibling()


def sample(path=None):
    """Read CURIOSITY.md, compute the κ/φ self-bloat shape, stamp a record.

    Pure read of the thread file; no mutation of it. The record's `ts` is
    stamped at compute time (the series clock, not the file's mtime).
    """
    curiosity_path = path or SIBLING._find_root(None)
    with open(curiosity_path, "r", encoding="utf-8") as f:
        text = f.read()
    records = SIBLING.parse_curiosity(text)
    verdict = SIBLING.compute(records)

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "threads": verdict["threads"],
        "total_bytes": verdict["total_bytes"],
        "open_threads": verdict["open_threads"],
        "resolved_threads": verdict["resolved_threads"],
        "closed_threads": verdict["closed_threads"],
        "largest_title": verdict["largest_thread"]["title"],
        "largest_bytes": verdict["largest_thread"]["bytes"],
        "largest_phi_state": verdict["largest_thread"]["phi_state"],
        "bloat_count": len(verdict["bloated"]),
        "bloated_bytes": sum(b["bytes"] for b in verdict["bloated"]),
        "bloated": json.dumps(verdict["bloated"], ensure_ascii=False),
        "verdict": verdict["verdict"],
    }
    return record


def init_db(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS samples (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            threads INTEGER,
            total_bytes INTEGER,
            open_threads INTEGER,
            resolved_threads INTEGER,
            closed_threads INTEGER,
            largest_title TEXT,
            largest_bytes INTEGER,
            largest_phi_state TEXT,
            bloat_count INTEGER,
            bloated_bytes INTEGER,
            bloated TEXT,
            verdict TEXT
        )"""
    )
    conn.commit()


def append(s, db_path=None):
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    init_db(conn)
    conn.execute(
        """INSERT INTO samples
           (ts, threads, total_bytes, open_threads, resolved_threads,
            closed_threads, largest_title, largest_bytes, largest_phi_state,
            bloat_count, bloated_bytes, bloated, verdict)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (s["ts"], s["threads"], s["total_bytes"], s["open_threads"],
         s["resolved_threads"], s["closed_threads"], s["largest_title"],
         s["largest_bytes"], s["largest_phi_state"], s["bloat_count"],
         s["bloated_bytes"], s["bloated"], s["verdict"]),
    )
    conn.commit()
    conn.close()


def _load_rows(db_path=None):
    path = db_path or DB_PATH
    if not os.path.exists(path):
        return []
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS samples (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            threads INTEGER, total_bytes INTEGER, open_threads INTEGER,
            resolved_threads INTEGER, closed_threads INTEGER,
            largest_title TEXT, largest_bytes INTEGER, largest_phi_state TEXT,
            bloat_count INTEGER, bloated_bytes INTEGER, bloated TEXT,
            verdict TEXT
        )"""
    )
    rows = conn.execute(
        "SELECT seq, ts, threads, total_bytes, open_threads, resolved_threads, "
        "closed_threads, largest_title, largest_bytes, largest_phi_state, "
        "bloat_count, bloated_bytes, verdict FROM samples ORDER BY seq"
    ).fetchall()
    conn.close()
    return rows


def show(db_path=None):
    rows = _load_rows(db_path)
    if not rows:
        print("empty series — run once to seed")
        return
    print(f"{'#':>3} {'ts':32} {'thr':>4} {'B':>7} {'open':>4} {'res':>4} "
          f"{'cls':>4} {'bloat':>5} {'bloatB':>7} {'verdict'}")
    for r in rows:
        print(f"{r[0]:>3} {r[1]:32} {r[2]:>4} {r[3]:>7} {r[4]:>4} {r[5]:>4} "
              f"{r[6]:>4} {r[10]:>5} {r[11]:>7} {r[12]}")


def compute_trend(rows, window=None):
    """Read-only self-bloat gradient over the series.

    The disease the thread named is a self-bloat that *compounds*: bloat_bytes
    (or bloat_count) rising monotonically past a peak across samples. `worsening`
    fires only when the last sample is strictly above the first sample (a
    genuine growth) AND strictly above the running minimum (a rise past the
    healthiest point) — never on a flat or improving series. Read-only: never
    mutates CURIOSITY.md or the series.
    """
    if len(rows) < 2:
        return {
            "n": len(rows),
            "first_bloat_bytes": rows[0][11] if rows else None,
            "last_bloat_bytes": rows[-1][11] if rows else None,
            "first_total_bytes": rows[0][3] if rows else None,
            "last_total_bytes": rows[-1][3] if rows else None,
            "worsening": None,
            "reason": "insufficient samples (<2)",
        }

    first_bloat = rows[0][11]
    last_bloat = rows[-1][11]
    first_total = rows[0][3]
    last_total = rows[-1][3]

    # Monotone rise past the running minimum (= the healthiest point so far).
    running_min = rows[0][11]
    rose_past_min = False
    for r in rows[1:]:
        if r[11] > running_min:
            rose_past_min = True
        else:
            running_min = r[11]

    worsening = (last_bloat > first_bloat) and rose_past_min

    return {
        "n": len(rows),
        "first_bloat_bytes": first_bloat,
        "last_bloat_bytes": last_bloat,
        "delta_bloat_bytes": last_bloat - first_bloat,
        "first_total_bytes": first_total,
        "last_total_bytes": last_total,
        "delta_total_bytes": last_total - first_total,
        "worsening": worsening,
    }


def trend(db_path=None):
    rows = _load_rows(db_path)
    if not rows:
        print(json.dumps({"error": "no series yet"}, ensure_ascii=False, indent=2))
        return 1
    out = {
        "schema": "curiosity-kappa-trend/v1",
        "sample_count": len(rows),
        "self_bloat": compute_trend(rows),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _selftest():
    import tempfile

    def check(name, cond):
        assert cond, name

    # 1. compute wrap: the sibling's compute over a synthetic thread file.
    synthetic = (
        "## Active\n\n"
        "### Thread A\n**First raised:** x\n**Last dispatched:** y\n"
        + ("history " * 100) + "\n"   # large open thread
        "\n### Thread B\n**First raised:** x\n**Last dispatched:** y\n"
        + ("history " * 10) + "\n"
        "RESOLVED (2026-01-01) answer\n\n"
        + ("history " * 100) + "\n"   # small-base but huge resolved history
        "\n"
    )
    recs = SIBLING.parse_curiosity(synthetic)
    v = SIBLING.compute(recs)
    check("synthetic parses 2 threads", v["threads"] == 2)
    check("synthetic has a bloated resolved thread", len(v["bloated"]) >= 1)

    # 2. sample() over a temp CURIOSITY.md file.
    with tempfile.TemporaryDirectory() as td:
        cf = os.path.join(td, "CURIOSITY.md")
        with open(cf, "w", encoding="utf-8") as f:
            f.write(synthetic)
        s = sample(path=cf)
    for k in ("ts", "threads", "total_bytes", "open_threads", "resolved_threads",
              "closed_threads", "bloat_count", "bloated_bytes", "verdict",
              "largest_title", "largest_bytes", "largest_phi_state"):
        check(f"record field {k}", k in s)
    check("bloat_count >= 1", s["bloat_count"] >= 1)

    # 3. append-does-not-replace roundtrip (seq monotonic, both preserved).
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "t.sqlite")
        a = dict(s); a["ts"] = "2026-01-01T00:00:00+00:00"
        b = dict(s); b["ts"] = "2026-01-02T00:00:00+00:00"; b["bloated_bytes"] += 100
        append(a, db_path=db)
        append(b, db_path=db)
        rows = _load_rows(db_path=db)
        check("append yields 2 rows", len(rows) == 2)
        check("seq monotonic", rows[0][0] < rows[1][0])
        check("both timestamps preserved", rows[0][1] != rows[1][1])

        # 4. trend on worsening synthetic (rising bloat_bytes).
        tr = compute_trend(rows)
        check("worsening on rising bloat", tr["worsening"] is True)

        # 5. trend on flat/falling → not worsening.
        c = dict(s); c["ts"] = "2026-01-03T00:00:00+00:00"; c["bloated_bytes"] -= 200
        append(c, db_path=db)
        rows2 = _load_rows(db_path=db)
        # last sample now below first → worsening must be False.
        tr2 = compute_trend(rows2)
        check("no worsening on falling tail", tr2["worsening"] is False)

    # 6. single-sample abstain.
    tr3 = compute_trend([(1, "t1", 9, 100, 4, 3, 2, "x", 100, "r", 2, 200, "SELF-BLOAT")])
    check("single sample abstains", tr3["worsening"] is None)

    print(json.dumps({"schema": "curiosity-kappa-trend-selftest",
                      "passed": 6, "ok": True}, ensure_ascii=False))
    return 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--trend", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.show:
        show()
        return 0
    if args.trend:
        return trend()
    if args.selftest:
        return _selftest()
    s = sample()
    append(s)
    print(json.dumps(s, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())