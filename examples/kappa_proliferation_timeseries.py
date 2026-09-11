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


def count_toolsets():
    """Count enabled/disabled Hermes toolsets via `hermes tools list` (subprocess)."""
    import subprocess, re
    try:
        r = subprocess.run(["hermes", "tools", "list"],
                           capture_output=True, text=True, timeout=60)
        out = r.stdout or ""
    except Exception:
        return None, None
    enabled = len(re.findall(r"✓ enabled", out))
    disabled = len(re.findall(r"✗ disabled", out))
    return enabled, disabled


def count_mcp():
    """Count registered MCP servers (enabled vs disabled) via `hermes mcp list`."""
    import subprocess, re
    try:
        r = subprocess.run(["hermes", "mcp", "list"],
                           capture_output=True, text=True, timeout=60)
        out = r.stdout or ""
    except Exception:
        return None, None
    enabled = len(re.findall(r"✓ enabled", out))
    disabled = len(re.findall(r"✗ disabled", out))
    return enabled, disabled


def sample():
    active, archived, total_bytes, unique = count_skills()
    plugins = count_plugins()
    ts_enabled, ts_disabled = count_toolsets()
    mcp_enabled, mcp_disabled = count_mcp()

    d = active                      # density = active loaded surface (skills)
    ts = (ts_enabled or 0) + (ts_disabled or 0)   # total toolsets
    mcp = (mcp_enabled or 0) + (mcp_disabled or 0)

    # κ = every capability ever registered (raw) vs effective (post-prune active)
    kappa_raw = active + archived + plugins + ts + mcp
    kappa_eff = active + plugins + (ts_enabled or 0) + (mcp_enabled or 0)

    phi_d = log(1 + d)              # φ(d) = ln(1+d)
    Q_raw = phi_d / kappa_raw       # Q = φ/κ (A2)
    Q_eff = phi_d / kappa_eff

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
    # Schema migration: add κ-terms for toolsets + MCP (introduced later).
    existing = {row[1] for row in conn.execute("PRAGMA table_info(samples)")}
    for col in ("toolsets_enabled", "toolsets_disabled",
                "mcp_enabled", "mcp_disabled"):
        if col not in existing:
            conn.execute(f"ALTER TABLE samples ADD COLUMN {col} INTEGER")
    conn.commit()


def append(s):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    conn.execute(
        """INSERT OR REPLACE INTO samples
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


def show():
    if not os.path.exists(DB_PATH):
        print("no series yet — run once to seed")
        return
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT ts, d_active, archived, kappa_raw, kappa_eff, Q_raw, Q_eff, "
        "toolsets_enabled, toolsets_disabled, mcp_enabled, mcp_disabled "
        "FROM samples ORDER BY ts"
    ).fetchall()
    if not rows:
        print("empty")
        return
    print(f"{'ts':32} {'d':>4} {'arch':>5} {'κraw':>5} {'κeff':>5} "
          f"{'Qraw':>8} {'Qeff':>8} {'ts:on/off':>9} {'mcp:on/off':>10}")
    for r in rows:
        ts_on = f"{r[7]}/{r[8]}" if r[7] is not None else "-"
        mcp_on = f"{r[9]}/{r[10]}" if r[9] is not None else "-"
        print(f"{r[0]:32} {r[1]:>4} {r[2]:>5} {r[3]:>5} {r[4]:>5} "
              f"{r[5]:>8.5f} {r[6]:>8.5f} {ts_on:>9} {mcp_on:>10}")
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