#!/usr/bin/env python3
"""
kappa_proliferation_timeseries.py — read-only φ/κ/Q diagnostic instrument.

Implements the CURIOSITY thread "κ Proliferation in Agent Ecosystems" (HIGH).
Measures the agent's own runtime as A2:  Q(M) = φ(d) / κ(M).

Design constraint (from the thread itself): Q is READ-ONLY — it flags, never
acts. This script only samples and appends; it triggers no decisions. The
Goodhart safeguard is structural: no code path consumes this metric as a gate.

Zero dependencies. Stdlib only.

Usage:
    python3 kappa_proliferation_timeseries.py          # sample + append
    python3 kappa_proliferation_timeseries.py --show   # print the series
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

DB_PATH = os.path.join(os.path.expanduser(RUNTIME_ROOT), "data", "kappa_timeseries.sqlite")

SKILL_DIRS = [
    os.path.expanduser("~/.hermes/skills"),
    os.path.expanduser("~/.agents/skills"),
]
PLUGIN_DIR = os.path.expanduser("~/.hermes/plugins")


def count_skills():
    """Count SKILL.md files, split active vs archived (dead κ)."""
    active = 0
    archived = 0
    total_bytes = 0
    seen = set()
    for base in SKILL_DIRS:
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


def count_plugins():
    if not os.path.isdir(PLUGIN_DIR):
        return 0
    return len([d for d in os.listdir(PLUGIN_DIR)
                if os.path.isdir(os.path.join(PLUGIN_DIR, d))
                and not d.startswith(".")])


def sample():
    active, archived, total_bytes, unique = count_skills()
    plugins = count_plugins()

    d = active                      # density = active loaded surface
    kappa_raw = active + archived + plugins   # every capability ever registered
    kappa_eff = active + plugins              # post-prune effective surface

    phi_d = log(1 + d)              # φ(d) = ln(1+d)
    Q_raw = phi_d / kappa_raw       # Q = φ/κ (A2)
    Q_eff = phi_d / kappa_eff

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "d_active": d,
        "archived": archived,
        "plugins": plugins,
        "unique_skills": unique,
        "skill_bytes": total_bytes,
        "phi": round(phi_d, 6),
        "kappa_raw": kappa_raw,
        "kappa_eff": kappa_eff,
        "Q_raw": round(Q_raw, 6),
        "Q_eff": round(Q_eff, 6),
    }


def init_db(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS samples (
            ts TEXT PRIMARY KEY,
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
    conn.commit()


def append(s):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    conn.execute(
        """INSERT OR REPLACE INTO samples
           (ts, d_active, archived, plugins, unique_skills, skill_bytes,
            phi, kappa_raw, kappa_eff, Q_raw, Q_eff)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (s["ts"], s["d_active"], s["archived"], s["plugins"],
         s["unique_skills"], s["skill_bytes"], s["phi"],
         s["kappa_raw"], s["kappa_eff"], s["Q_raw"], s["Q_eff"]),
    )
    conn.commit()
    conn.close()


def show():
    if not os.path.exists(DB_PATH):
        print("no series yet — run once to seed")
        return
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT ts, d_active, archived, kappa_raw, kappa_eff, Q_raw, Q_eff "
        "FROM samples ORDER BY ts"
    ).fetchall()
    if not rows:
        print("empty")
        return
    print(f"{'ts':32} {'d':>4} {'arch':>5} {'κraw':>5} {'κeff':>5} {'Qraw':>9} {'Qeff':>9}")
    for r in rows:
        print(f"{r[0]:32} {r[1]:>4} {r[2]:>5} {r[3]:>5} {r[4]:>5} {r[5]:>9.6f} {r[6]:>9.6f}")
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="print the stored series")
    args = ap.parse_args()
    if args.show:
        show()
        return
    s = sample()
    append(s)
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()