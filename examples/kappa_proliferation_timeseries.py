#!/usr/bin/env python3
"""
kappa_proliferation_timeseries.py — read-only φ/κ/Q diagnostic instrument.

Implements the CURIOSITY thread "κ Proliferation in Agent Ecosystems" (HIGH).
Measures the agent's own runtime as A2:  Q(M) = φ(d) / κ(M).

Design constraint (from the thread itself): Q is READ-ONLY — it flags, never
acts. This script only samples and appends; it triggers no decisions. The
Goodhart safeguard is structural: no code path consumes this metric as a gate.
`--trend` additionally *reads* the dQ/dt gradient the thread left open — it
reports the slope sign and a collapse verdict, but never acts on it.

Zero dependencies. Stdlib only.

Usage:
    python3 kappa_proliferation_timeseries.py            # sample + append
    python3 kappa_proliferation_timeseries.py --show     # print the series
    python3 kappa_proliferation_timeseries.py --trend    # print dQ/dt gradient
    python3 kappa_proliferation_timeseries.py --selftest # deterministic self-check
"""

import os
import json
import sqlite3
import sys
import argparse
from math import log
from datetime import datetime, timezone

RUNTIME = os.environ.get("IST_RUNTIME") or os.path.expanduser("~/ist-runtime")

# Resolve runtime root across the known relocations.
_CANDIDATES = [
    RUNTIME,
    os.path.expanduser("~/ist-runtime"),
    "/run/media/lermf/DADOS_STORAGE/@projetos/Projetos/ist-runtime",
    "/mnt/projetos/Projetos/ist-runtime",
]
RUNTIME_ROOT = next((c for c in _CANDIDATES if c and os.path.isdir(os.path.expanduser(c))), None)
if RUNTIME_ROOT is None:
    RUNTIME_ROOT = os.path.expanduser("~/ist-runtime")

# Database path is overridable for tests (never touches production data).
DB_PATH = os.environ.get("IST_KAPPA_DB") or os.path.join(
    os.path.expanduser(RUNTIME_ROOT), "data", "kappa_timeseries.sqlite")

SKILL_DIRS = [
    os.path.expanduser("~/.hermes/skills"),
    os.path.expanduser("~/.agents/skills"),
]
PLUGIN_DIR = os.path.expanduser("~/.hermes/plugins")


def count_skills(skill_dirs=None):
    """Count SKILL.md files, split active vs archived (dead κ)."""
    dirs = skill_dirs if skill_dirs is not None else SKILL_DIRS
    active = 0
    archived = 0
    total_bytes = 0
    seen = set()
    for base in dirs:
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for f in filenames:
                if f != "SKILL.md":
                    continue
                fp = os.path.join(dirpath, f)
                real = os.path.realpath(fp)
                if real in seen:
                    continue
                seen.add(real)
                try:
                    total_bytes += os.path.getsize(fp)
                except OSError:
                    pass
                if ".archive" in fp:
                    archived += 1
                else:
                    active += 1
    return active, archived, total_bytes, len(seen)


def count_plugins(plugin_dir=None):
    d = plugin_dir if plugin_dir is not None else PLUGIN_DIR
    if not os.path.isdir(d):
        return 0
    return len([x for x in os.listdir(d)
                if os.path.isdir(os.path.join(d, x))
                and not x.startswith(".")])


def count_toolsets(hermes_bin="hermes"):
    """Count enabled/disabled Hermes toolsets via `hermes tools list` (subprocess)."""
    import subprocess, re
    try:
        r = subprocess.run([hermes_bin, "tools", "list"],
                           capture_output=True, text=True, timeout=60)
        out = r.stdout or ""
    except Exception:
        return None, None
    enabled = len(re.findall(r"✓ enabled", out))
    disabled = len(re.findall(r"✗ disabled", out))
    return enabled, disabled


def count_mcp(hermes_bin="hermes"):
    """Count registered MCP servers (enabled vs disabled) via `hermes mcp list`."""
    import subprocess, re
    try:
        r = subprocess.run([hermes_bin, "mcp", "list"],
                           capture_output=True, text=True, timeout=60)
        out = r.stdout or ""
    except Exception:
        return None, None
    enabled = len(re.findall(r"✓ enabled", out))
    disabled = len(re.findall(r"✗ disabled", out))
    return enabled, disabled


def compute_sample(active, archived, plugins,
                   ts_enabled, ts_disabled, mcp_enabled, mcp_disabled,
                   total_bytes, unique):
    """Derive the κ/φ/Q record from raw counts (pure, no I/O)."""
    d = active                      # density = active loaded surface (skills)
    ts = (ts_enabled or 0) + (ts_disabled or 0)   # total toolsets
    mcp = (mcp_enabled or 0) + (mcp_disabled or 0)

    # κ = every capability ever registered (raw) vs effective (post-prune active)
    kappa_raw = active + archived + plugins + ts + mcp
    kappa_eff = active + plugins + (ts_enabled or 0) + (mcp_enabled or 0)

    phi_d = log(1 + d)              # φ(d) = ln(1+d)
    Q_raw = phi_d / kappa_raw if kappa_raw else 0.0       # Q = φ/κ (A2)
    Q_eff = phi_d / kappa_eff if kappa_eff else 0.0

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "d_active": d,
        "archived": archived,
        "plugins": plugins,
        "toolsets_enabled": ts_enabled,
        "toolsets_disabled": ts_disabled,
        "mcp_enabled": mcp_enabled,
        "mcp_disabled": mcp_disabled,
        "unique_skills": unique,
        "skill_bytes": total_bytes,
        "phi": round(phi_d, 6),
        "kappa_raw": kappa_raw,
        "kappa_eff": kappa_eff,
        "Q_raw": round(Q_raw, 6),
        "Q_eff": round(Q_eff, 6),
    }


def sample(skill_dirs=None, plugin_dir=None, hermes_bin="hermes"):
    active, archived, total_bytes, unique = count_skills(skill_dirs)
    plugins = count_plugins(plugin_dir)
    ts_enabled, ts_disabled = count_toolsets(hermes_bin)
    mcp_enabled, mcp_disabled = count_mcp(hermes_bin)
    return compute_sample(active, archived, plugins,
                          ts_enabled, ts_disabled, mcp_enabled, mcp_disabled,
                          total_bytes, unique)


def init_db(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS samples (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            d_active INTEGER,
            archived INTEGER,
            plugins INTEGER,
            unique_skills INTEGER,
            skill_bytes INTEGER,
            phi REAL,
            kappa_raw INTEGER,
            kappa_eff INTEGER,
            Q_raw REAL,
            Q_eff REAL
        )"""
    )
    # Schema migration: add κ-terms for toolsets + MCP (introduced later).
    existing = {row[1] for row in conn.execute("PRAGMA table_info(samples)")}
    for col in ("toolsets_enabled", "toolsets_disabled",
                "mcp_enabled", "mcp_disabled"):
        if col not in existing:
            conn.execute(f"ALTER TABLE samples ADD COLUMN {col} INTEGER")

    # Migration: pre-9/11 tables used `ts` as PRIMARY KEY (no `seq`), so
    # `INSERT OR REPLACE` collated a re-sample onto the prior row instead of
    # appending. Rebuild those into the append-only `seq`-keyed shape,
    # preserving every historical sample ordered by its timestamp.
    if "seq" not in existing:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(samples)")]
        conn.execute("ALTER TABLE samples RENAME TO samples_old")
        conn.execute(
            """CREATE TABLE samples (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                d_active INTEGER,
                archived INTEGER,
                plugins INTEGER,
                unique_skills INTEGER,
                skill_bytes INTEGER,
                phi REAL,
                kappa_raw INTEGER,
                kappa_eff INTEGER,
                Q_raw REAL,
                Q_eff REAL
            )"""
        )
        # Re-add the κ-term columns to the fresh table first.
        mig_existing = {row[1] for row in conn.execute("PRAGMA table_info(samples)")}
        for col in ("toolsets_enabled", "toolsets_disabled",
                    "mcp_enabled", "mcp_disabled"):
            if col not in mig_existing:
                conn.execute(f"ALTER TABLE samples ADD COLUMN {col} INTEGER")
        # Copy any columns that exist in both, ordered by ts.
        dest = [row[1] for row in conn.execute("PRAGMA table_info(samples)")]
        shared = [c for c in cols if c in dest and c != "seq"]
        colsel = ", ".join(shared)
        conn.execute(
            f"INSERT INTO samples ({colsel}) "
            f"SELECT {colsel} FROM samples_old ORDER BY ts"
        )
        conn.execute("DROP TABLE samples_old")
    conn.commit()


def append(s, db_path=None):
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    init_db(conn)
    conn.execute(
        """INSERT INTO samples
           (ts, d_active, archived, plugins, unique_skills, skill_bytes,
            phi, kappa_raw, kappa_eff, Q_raw, Q_eff,
            toolsets_enabled, toolsets_disabled, mcp_enabled, mcp_disabled)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (s["ts"], s["d_active"], s["archived"], s["plugins"],
         s["unique_skills"], s["skill_bytes"], s["phi"],
         s["kappa_raw"], s["kappa_eff"], s["Q_raw"], s["Q_eff"],
         s.get("toolsets_enabled"), s.get("toolsets_disabled"),
         s.get("mcp_enabled"), s.get("mcp_disabled")),
    )
    conn.commit()
    conn.close()


def _ensure_schema(db_path=None):
    """Idempotently migrate/create the samples schema before any read/write."""
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    init_db(conn)
    conn.close()


def _load_rows(db_path=None):
    path = db_path or DB_PATH
    if not os.path.exists(path):
        return []
    _ensure_schema(path)
    conn = sqlite3.connect(path)
    rows = conn.execute(
        "SELECT seq, ts, d_active, archived, kappa_raw, kappa_eff, Q_raw, Q_eff, "
        "toolsets_enabled, toolsets_disabled, mcp_enabled, mcp_disabled "
        "FROM samples ORDER BY seq"
    ).fetchall()
    conn.close()
    return rows


def show(db_path=None):
    rows = _load_rows(db_path)
    if not rows:
        print("empty series — run once to seed")
        return
    print(f"{'#':>3} {'ts':32} {'d':>4} {'arch':>5} {'κraw':>5} {'κeff':>5} "
          f"{'Qraw':>8} {'Qeff':>8} {'ts:on/off':>9} {'mcp:on/off':>10}")
    for r in rows:
        ts_on = f"{r[8]}/{r[9]}" if r[8] is not None else "-"
        mcp_on = f"{r[10]}/{r[11]}" if r[10] is not None else "-"
        print(f"{r[0]:>3} {r[1]:32} {r[2]:>4} {r[3]:>5} {r[4]:>5} {r[5]:>5} "
              f"{r[6]:>8.5f} {r[7]:>8.5f} {ts_on:>9} {mcp_on:>10}")


def compute_trend(rows, metric="Q_eff", window=None):
    """
    Read-only dQ/dt computation over the series.

    Args:
        rows: iterable of (seq, ts, ... Q_raw, Q_eff ...) tuples or dicts.
        metric: 'Q_raw' or 'Q_eff'.
        window: optional int — only the last N samples are considered.

    Returns a dict {n, first_q, last_q, dq, slope_sign, monotone_drops,
    collapse} where `collapse` is True iff the LAST sample is strictly below
    BOTH the first sample AND the running maximum (a genuine dQ/dt<0 turn),
    per the thread's "collapse pattern predicted at scale". Read-only: this
    never mutates and never gates anything.
    """
    if isinstance(metric, str):
        if metric == "Q_eff":
            col = lambda r: r[7] if isinstance(r, tuple) else r["Q_eff"]
        elif metric == "Q_raw":
            col = lambda r: r[6] if isinstance(r, tuple) else r["Q_raw"]
        else:
            raise ValueError("metric must be Q_raw or Q_eff")
    else:
        col = metric

    vals = [col(r) for r in rows]
    if window and len(vals) > window:
        vals = vals[-window:]

    if len(vals) < 2:
        return {"n": len(vals), "metric": (metric if isinstance(metric, str) else "custom"),
                "first_q": vals[0] if vals else None,
                "last_q": vals[-1] if vals else None,
                "dq": None, "slope_sign": None, "monotone_drops": 0,
                "collapse": None}

    first_q = vals[0]
    last_q = vals[-1]
    dq = last_q - first_q
    slope_sign = "up" if dq > 0 else ("down" if dq < 0 else "flat")

    running_max = vals[0]
    monotone_drops = 0
    for v in vals[1:]:
        if v < running_max:
            monotone_drops += 1
        else:
            running_max = v

    # collapse = last sample strictly below both first and the running max
    collapse = (last_q < first_q) and (last_q < running_max)

    return {"n": len(vals), "metric": (metric if isinstance(metric, str) else "custom"),
            "first_q": first_q, "last_q": last_q, "dq": round(dq, 6),
            "slope_sign": slope_sign, "monotone_drops": monotone_drops,
            "collapse": collapse}


def trend(db_path=None):
    rows = _load_rows(db_path)
    if not rows:
        print(json.dumps({"error": "no series yet"},
                         ensure_ascii=False, indent=2))
        return 1
    out = {
        "schema": "kappa-trend/v1",
        "sample_count": len(rows),
        "Q_raw": compute_trend(rows, metric="Q_raw"),
        "Q_eff": compute_trend(rows, metric="Q_eff"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


_SET_DB = None


def _selftest():
    import tempfile

    def check(name, cond):
        assert cond, name

    # 1. canonical φ/κ math (thread's own canonical demo d=0.85,c=0.31 resident)
    #    → here use a synthetic active=1 (φ=ln2≈0.6931) with κ_raw=10.
    s = compute_sample(active=1, archived=0, plugins=0,
                       ts_enabled=0, ts_disabled=0, mcp_enabled=0, mcp_disabled=0,
                       total_bytes=100, unique=1)
    check("phi ln(1+1)", abs(s["phi"] - log(2)) < 1e-5)
    check("kappa_raw==1", s["kappa_raw"] == 1)
    check("Q_raw == phi/1", abs(s["Q_raw"] - log(2)) < 1e-5)

    # 2. φ/κ shape: the same density with a larger κ (more capability) yields
    #    strictly LOWER Q — the A2 collapse direction, in miniature.
    s_lo_k = compute_sample(active=1, archived=0, plugins=0,
                            ts_enabled=0, ts_disabled=0, mcp_enabled=0, mcp_disabled=0,
                            total_bytes=100, unique=1)
    s_hi_k = compute_sample(active=1, archived=9, plugins=0,
                            ts_enabled=0, ts_disabled=0, mcp_enabled=0, mcp_disabled=0,
                            total_bytes=100, unique=1)
    check("Q_raw decreases as κ rises", s_hi_k["Q_raw"] < s_lo_k["Q_raw"])

    # 3. field shape completeness
    for k in ("ts", "d_active", "archived", "plugins", "phi",
              "kappa_raw", "kappa_eff", "Q_raw", "Q_eff"):
        check(f"field {k}", k in s)

    # 4. append-then-read roundtrip: two samples must APPEND (seq monotonic),
    #    never replace — the write-safety regression guard.
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "t.sqlite")
        a = dict(s); a["ts"] = "2026-01-01T00:00:00+00:00"; a["Q_eff"] = 0.010
        b = dict(s); b["ts"] = "2026-01-02T00:00:00+00:00"; b["Q_eff"] = 0.009
        append(a, db_path=db)
        append(b, db_path=db)
        rows = _load_rows(db_path=db)
        check("append yields 2 rows", len(rows) == 2)
        check("seq monotonic", rows[0][0] < rows[1][0])
        check("both timestamps preserved", rows[0][1] != rows[1][1])

    # 5. trend on a synthetic collapse: rising then falling → collapse=True.
    seq_rows = [
        (1, "t1", 0, 0, 0, 0, 0.0100, 0.0150, None, None, None, None),
        (2, "t2", 0, 0, 0, 0, 0.0101, 0.0151, None, None, None, None),
        (3, "t3", 0, 0, 0, 0, 0.0102, 0.0152, None, None, None, None),
        (4, "t4", 0, 0, 0, 0, 0.0101, 0.0150, None, None, None, None),
        (5, "t5", 0, 0, 0, 0, 0.0100, 0.0149, None, None, None, None),
    ]
    tr = compute_trend(seq_rows, metric="Q_eff")
    check("collapse detected on falling tail", tr["collapse"] is True)
    check("slope down", tr["slope_sign"] == "down")
    check("monotone drops >= 2", tr["monotone_drops"] >= 2)

    # 6. trend on monotone rising → collapse=False, slope up.
    up_rows = [
        (1, "t1", 0, 0, 0, 0, 0.010, 0.0150, None, None, None, None),
        (2, "t2", 0, 0, 0, 0, 0.010, 0.0151, None, None, None, None),
        (3, "t3", 0, 0, 0, 0, 0.010, 0.0152, None, None, None, None),
    ]
    tr2 = compute_trend(up_rows, metric="Q_eff")
    check("no collapse on rising", tr2["collapse"] is False)
    check("slope up", tr2["slope_sign"] == "up")

    # 7. single sample → abstain (collapse is None, not True/False).
    tr3 = compute_trend(up_rows[:1], metric="Q_eff")
    check("single sample abstains", tr3["collapse"] is None)

    # 8. window clamps to last N.
    tr4 = compute_trend(seq_rows, metric="Q_eff", window=2)
    check("window clamps n", tr4["n"] == 2)

    print(json.dumps({"schema": "kappa-trend-selftest",
                      "passed": 8, "ok": True}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="print the stored series")
    ap.add_argument("--trend", action="store_true", help="print the dQ/dt gradient")
    ap.add_argument("--selftest", action="store_true", help="deterministic self-check")
    args = ap.parse_args()
    if args.show:
        show()
        return
    if args.trend:
        return trend()
    if args.selftest:
        return _selftest()
    s = sample()
    append(s)
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    sys.exit(main())