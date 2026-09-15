#!/usr/bin/env python3
"""
kappa_proliferation_timeseries.py — read-only φ/κ/Q diagnostic instrument.

Implements the CURIOSITY thread "κ Proliferation in Agent Ecosystems" (HIGH).
Measures the agent's own runtime as A2:  Q(M) = φ(d) / κ(M).

Design constraint (from the thread itself): Q is READ-ONLY — it flags, never
acts. This script only samples and appends; it triggers no decisions. The
Goodhart safeguard is structural: no code path consumes this metric as a gate.
`--trend` additionally *reads* the dQ/dt gradient the thread left open — it
reports the slope sign and a collapse verdict, but never acts on it. `--check`
is the *scheduled consumer* of that verdict (report-only): silent when healthy,
`ALARM:` + exit 1 on an epoch-local collapse — it surfaces the movement as a
cron delivery, never edits or prescribes anything.

Zero dependencies. Stdlib only.

Usage:
    python3 kappa_proliferation_timeseries.py            # sample + append
    python3 kappa_proliferation_timeseries.py --show     # print the series
    python3 kappa_proliferation_timeseries.py --trend    # print dQ/dt gradient
    python3 kappa_proliferation_timeseries.py --check    # watchdog: ALARM + exit 1 on collapse
    python3 kappa_proliferation_timeseries.py --selftest # deterministic self-check
"""

import os
import json
import hashlib
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


def root_identity(base):
    """Stable per-root identity: normalized path + `dev:ino` (or absence).

    The fingerprint's structural half. A root that is re-mounted, replaced by
    a symlink to another tree, split into a distinct directory, or simply
    removed changes its identity — which is exactly the event that makes two
    samples incommensurable (the same failure class the toolsets/MCP rebase
    demonstrated, caught then only because `ALTER TABLE` left NULLs behind).
    """
    base = os.path.abspath(os.path.expanduser(base))
    if not os.path.isdir(base):
        return "%s|absent" % base
    try:
        st = os.stat(base)
        return "%s|%d:%d" % (base, st.st_dev, st.st_ino)
    except OSError:
        return "%s|unreadable" % base


def roots_sha(skill_dirs=None):
    """sha256 of the walked root-set definition (order-independent).

    Recorded into every new sample so a *future* change of the metric's
    definition is detectable structurally, instead of being remembered.
    """
    dirs = skill_dirs if skill_dirs is not None else SKILL_DIRS
    joined = "\n".join(sorted(root_identity(d) for d in dirs))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def surface_detail(skill_dirs=None, hash_contents=True):
    """Walk the roots and return the full surface record, not just counts.

    Traversal contract (unchanged from `count_skills`): `os.walk` without
    following symlinked directories, realpath-deduped. What is *added* is the
    fidelity half — because a count is only a measurement insofar as its
    definition is recorded:

      * `roots_sha`         — the definition itself (root set + identities).
      * `dup_content`       — byte-identical copies across roots: the same
                              skill counted twice inflates φ without adding
                              capability (measured, never pruned).
      * `dup_path`          — same relative path under two roots (one name,
                              two bodies): the name-level collision count.
      * `symlink_dirs`      — symlinked dirs found in the walk (not descended).
      * `out_of_root_links` — those pointing outside every root: their target
                              content is *blind surface*, loaded by the runtime
                              and structurally invisible to this metric.
    """
    dirs = skill_dirs if skill_dirs is not None else SKILL_DIRS
    seen = set()
    active = 0
    archived = 0
    total_bytes = 0
    hashes = {}
    rel_by_root = {}
    symlink_dirs = 0
    out_of_root_links = 0
    real_roots = [os.path.realpath(d) for d in dirs]

    for base in dirs:
        if not os.path.isdir(base):
            continue
        rels = rel_by_root.setdefault(base, set())
        for dirpath, dirnames, filenames in os.walk(base):
            for d in list(dirnames):
                p = os.path.join(dirpath, d)
                if not os.path.islink(p):
                    continue
                symlink_dirs += 1
                if not os.path.exists(p):
                    continue
                target = os.path.realpath(p)
                if not any(target == r or target.startswith(r + os.sep)
                           for r in real_roots):
                    out_of_root_links += 1
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
                    continue
                active += 1
                rels.add(os.path.relpath(dirpath, base))
                if hash_contents:
                    h = _sha256_file(fp)
                    if h:
                        hashes.setdefault(h, 0)
                        hashes[h] += 1

    dup_content = sum(v - 1 for v in hashes.values() if v > 1) if hashes else 0
    # Name-level collision: the same relative path under more than one root —
    # one skill name, two bodies (or two copies under different bytes).
    by_name = {}
    for base, rels in rel_by_root.items():
        for rel in rels:
            by_name.setdefault(rel, []).append(base)
    dup_path = sum(1 for owners in by_name.values() if len(owners) > 1)
    return {
        "active": active,
        "archived": archived,
        "total_bytes": total_bytes,
        "unique": len(seen),
        "roots_sha": roots_sha(dirs),
        "dup_content": dup_content,
        "dup_path": dup_path,
        "symlink_dirs": symlink_dirs,
        "out_of_root_links": out_of_root_links,
    }


def count_skills(skill_dirs=None):
    """Count SKILL.md files, split active vs archived (dead κ).

    Kept as the narrow 4-tuple contract for existing callers; the full surface
    record (duplication, link topology, definition fingerprint) lives in
    `surface_detail`, which this wraps without a second walk.
    """
    d = surface_detail(skill_dirs, hash_contents=False)
    return d["active"], d["archived"], d["total_bytes"], d["unique"]


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
                   total_bytes, unique, roots_sha_value=None,
                   dup_content=None, dup_path=None,
                   symlink_dirs=None, out_of_root_links=None):
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
        # The measurement's *definition* and its fidelity, recorded with the
        # reading — a count whose definition is not in the row can silently
        # change meaning between samples (exactly what seq7→seq8 did).
        "roots_sha": roots_sha_value,
        "dup_content": dup_content,
        "dup_path": dup_path,
        "symlink_dirs": symlink_dirs,
        "out_of_root_links": out_of_root_links,
    }


def sample(skill_dirs=None, plugin_dir=None, hermes_bin="hermes"):
    detail = surface_detail(skill_dirs, hash_contents=True)
    plugins = count_plugins(plugin_dir)
    ts_enabled, ts_disabled = count_toolsets(hermes_bin)
    mcp_enabled, mcp_disabled = count_mcp(hermes_bin)
    return compute_sample(detail["active"], detail["archived"], plugins,
                          ts_enabled, ts_disabled, mcp_enabled, mcp_disabled,
                          detail["total_bytes"], detail["unique"],
                          roots_sha_value=detail["roots_sha"],
                          dup_content=detail["dup_content"],
                          dup_path=detail["dup_path"],
                          symlink_dirs=detail["symlink_dirs"],
                          out_of_root_links=detail["out_of_root_links"])


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
    # Migration: record the measurement's *definition* + fidelity per sample
    # (v0.8.44). Pre-existing rows stay NULL, which downstream reads as
    # "definition unrecorded" — an unknown, never a break by itself. A break
    # requires *two recorded* definitions that disagree (same discipline as
    # the a5 classifier's UNVERIFIED: absence is never an accusation).
    if "roots_sha" not in existing:
        conn.execute("ALTER TABLE samples ADD COLUMN roots_sha TEXT")
    for col in ("dup_content", "dup_path", "symlink_dirs", "out_of_root_links"):
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
        if "roots_sha" not in mig_existing:
            conn.execute("ALTER TABLE samples ADD COLUMN roots_sha TEXT")
        for col in ("dup_content", "dup_path", "symlink_dirs",
                    "out_of_root_links"):
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
            toolsets_enabled, toolsets_disabled, mcp_enabled, mcp_disabled,
            roots_sha, dup_content, dup_path, symlink_dirs, out_of_root_links)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (s["ts"], s["d_active"], s["archived"], s["plugins"],
         s["unique_skills"], s["skill_bytes"], s["phi"],
         s["kappa_raw"], s["kappa_eff"], s["Q_raw"], s["Q_eff"],
         s.get("toolsets_enabled"), s.get("toolsets_disabled"),
         s.get("mcp_enabled"), s.get("mcp_disabled"),
         s.get("roots_sha"), s.get("dup_content"), s.get("dup_path"),
         s.get("symlink_dirs"), s.get("out_of_root_links")),
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
        "toolsets_enabled, toolsets_disabled, mcp_enabled, mcp_disabled, "
        "roots_sha, dup_content, dup_path, symlink_dirs, out_of_root_links "
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
          f"{'Qraw':>8} {'Qeff':>8} {'ts:on/off':>9} {'mcp:on/off':>10} {'roots':>8}")
    for r in rows:
        ts_on = f"{r[8]}/{r[9]}" if r[8] is not None else "-"
        mcp_on = f"{r[10]}/{r[11]}" if r[10] is not None else "-"
        rsha = r[12][:8] if len(r) > 12 and r[12] else "-"
        print(f"{r[0]:>3} {r[1]:32} {r[2]:>4} {r[3]:>5} {r[4]:>5} {r[5]:>5} "
              f"{r[6]:>8.5f} {r[7]:>8.5f} {ts_on:>9} {mcp_on:>10} {rsha:>8}")


def _kappa_def_fingerprint(r):
    """
    Fingerprint of the κ-definition a sample was measured under.

    Two things can make two samples incommensurable:

    1. The **κ terms** grew (skills → +plugins → +toolsets → +MCP). A sample
       measured before toolsets/MCP entered κ has NULL in those columns (the
       ALTER TABLE migration left pre-term rows NULL); non-NULL marks the new
       definition. Structural signal already in the data.
    2. The **root set** the skill surface was walked over moved — recorded as
       `roots_sha` (root paths + identity) from v0.8.44 on. Rows before that
       are NULL: an *unrecorded* definition.

    Returns (term_definition, roots_sha_or_None). A NULL `roots_sha` is an
    unknown, never evidence of a change — only two *recorded* definitions that
    disagree constitute a break (the a5 classifier's UNVERIFIED discipline:
    absence is never an accusation).
    """
    if isinstance(r, tuple):
        # tuple layout: (seq, ts, d_active, archived, kappa_raw, kappa_eff,
        #                Q_raw, Q_eff, ts_en, ts_dis, mcp_en, mcp_dis, roots_sha…)
        ts_en = r[8]
        rsha = r[12] if len(r) > 12 else None
    else:
        ts_en = r.get("toolsets_enabled")
        rsha = r.get("roots_sha")
    term = "with-toolsets-mcp" if ts_en is not None else "pre-toolsets-mcp"
    return term, rsha


def _same_definition(a, b):
    """Are two fingerprints the SAME measurement definition?

    Term-definition mismatch is always a change. The root-set half only counts
    when BOTH sides recorded one — an unrecorded row cannot be compared (and a
    backfill must not fabricate an epoch boundary, which would silently mute the
    live collapse verdict on the current series).
    """
    if a[0] != b[0]:
        return False
    if a[1] and b[1]:
        return a[1] == b[1]
    return True


def _definitional_breaks(rows):
    """
    Detect κ-definition breaks between adjacent samples (ordered by seq).

    Returns a list of 1-based sample indices (in the given `rows` order) that
    START a new definitional epoch — i.e. index i (1-based) is a break when
    rows[i] has a different κ-definition than rows[i-1]. The first row always
    starts epoch 1 (index 1).
    """
    if not rows:
        return []
    breaks = [1]
    prev = _kappa_def_fingerprint(rows[0])
    for i in range(1, len(rows)):
        cur = _kappa_def_fingerprint(rows[i])
        if not _same_definition(cur, prev):
            breaks.append(i + 1)
        prev = cur
    return breaks


def compute_trend(rows, metric="Q_eff", window=None):
    """
    Read-only dQ/dt computation over the series.

    Args:
        rows: iterable of (seq, ts, ... Q_raw, Q_eff ...) tuples or dicts.
        metric: 'Q_raw' or 'Q_eff'.
        window: optional int — only the last N samples are considered.

    Returns a dict {n, first_q, last_q, dq, slope_sign, monotone_drops,
    collapse, provisioned, current_epoch} where `collapse` is True iff the
    LAST sample is strictly below BOTH the first sample AND the running
    maximum (a genuine dQ/dt<0 turn), per the thread's "collapse pattern
    predicted at scale".

    The collapse verdict is computed ONLY over the *current definitional
    epoch* (the contiguous suffix of samples sharing the latest κ-definition).
    A κ-definition break (new term added to the metric) makes earlier samples
    incommensurable — their κ is smaller by construction, so comparing across
    the break fabricates a collapse that is really a redefinition, not
    proliferation. The reader still *reports* the breaks (`provisioned`) and
    the full-span naive read (`full_span`), but the headline `collapse` answer
    is epoch-local: it only fires when κ genuinely rose *within* one
    definition. Read-only: this never mutates and never gates anything.
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

    # Full-span naive collapse over the WHOLE series (the pre-fix answer, kept
    # as `full_span` so consumers can see the fabricated-vs-real distinction).
    full_span_collapse = (last_q < first_q) and (last_q < running_max)

    # Epoch-local collapse: only compare within the current κ-definition.
    breaks = _definitional_breaks(rows)
    current_epoch_start = breaks[-1] - 1  # 0-based index of the epoch start
    epoch_rows = rows[current_epoch_start:]
    epoch_vals = [col(r) for r in epoch_rows]

    if len(epoch_vals) < 2:
        # Single-sample epoch: no within-definition history yet → abstain.
        collapse = None
        current_epoch = {
            "start_index": current_epoch_start + 1,
            "n_samples": len(epoch_vals),
            "first_q": epoch_vals[0],
            "last_q": epoch_vals[0],
            "collapse": None,
        }
    else:
        e_first = epoch_vals[0]
        e_last = epoch_vals[-1]
        e_max = e_first
        for v in epoch_vals[1:]:
            if v > e_max:
                e_max = v
        collapse = (e_last < e_first) and (e_last < e_max)
        current_epoch = {
            "start_index": current_epoch_start + 1,
            "n_samples": len(epoch_vals),
            "first_q": e_first,
            "last_q": e_last,
            "collapse": collapse,
        }

    return {"n": len(vals), "metric": (metric if isinstance(metric, str) else "custom"),
            "first_q": first_q, "last_q": last_q, "dq": round(dq, 6),
            "slope_sign": slope_sign, "monotone_drops": monotone_drops,
            "collapse": collapse,
            "provisioned": {"definitional_breaks": breaks,
                            "break_count": max(len(breaks) - 1, 0)},
            "current_epoch": current_epoch,
            "full_span_collapse": full_span_collapse}


def _trend_payload(rows):
    """Single source of the trend read — shared by `--trend` and `--check`."""
    return {
        "schema": "kappa-trend/v1",
        "sample_count": len(rows),
        "Q_raw": compute_trend(rows, metric="Q_raw"),
        "Q_eff": compute_trend(rows, metric="Q_eff"),
    }


def trend(db_path=None):
    rows = _load_rows(db_path)
    if not rows:
        print(json.dumps({"error": "no series yet"},
                         ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(_trend_payload(rows), ensure_ascii=False, indent=2))
    return 0


def check_trend(db_path=None):
    """Report-only watchdog over the dQ/dt series (κ Proliferation thread).

    Silent (exit 0) when healthy: no series yet, fewer than 2 samples, or no
    epoch-local collapse in either metric. Prints `ALARM:` + the JSON trend and
    exits 1 when the epoch-local `collapse` verdict is True for Q_raw or Q_eff —
    the genuine dQ/dt<0 turn past a peak *within one κ-definition* ("the
    collapse pattern predicted at scale"). Never mutates, never gates: the exit
    code is a *reporting* mechanism for the cron consumer only (the same
    contract as `axiom_joint_trend.py --check` and the sibling watchdogs).
    """
    try:
        rows = _load_rows(db_path)
    except (sqlite3.Error, OSError) as exc:
        # Fail-closed: an unreadable series is a signal, not a silent pass.
        print("kappa-check: series unreadable: %s" % exc, file=sys.stderr)
        return 2
    if len(rows) < 2:
        # Honest abstain: fewer than 2 samples cannot contain a trend.
        return 0
    out = _trend_payload(rows)
    collapsing = [name for name in ("Q_eff", "Q_raw")
                  if out[name].get("collapse") is True]
    if collapsing:
        print("ALARM: kappa-collapse (%s)" % ", ".join(collapsing))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1
    return 0


_SET_DB = None


def _selftest():
    import tempfile

    passed = []

    def check(name, cond):
        assert cond, name
        passed.append(name)

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

    # 9. definitional break: a NULL-kappa sample followed by a with-toolsets
    #    sample is a break; the epoch-local collapse must NOT fire across it.
    #    Naive full-span would say "collapse" (Q 0.015 → 0.010), but that is a
    #    redefinition, not proliferation — the headline collapse abstains/false.
    break_rows = [
        (1, "t1", 0, 0, 380, 380, 0.01018, 0.01546, None, None, None, None),
        (2, "t2", 0, 0, 380, 380, 0.01018, 0.01546, None, None, None, None),
        (3, "t3", 0, 0, 408, 408, 0.00955, 0.01440, 24, 9, 4, 1),
        (4, "t4", 0, 0, 408, 408, 0.00955, 0.01440, 24, 9, 4, 1),
    ]
    trb = compute_trend(break_rows, metric="Q_eff")
    check("break detected", trb["provisioned"]["break_count"] == 1)
    check("break at index 3", trb["provisioned"]["definitional_breaks"] == [1, 3])
    check("full-span would collapse", trb["full_span_collapse"] is True)
    # epoch-local over the with-toolsets suffix (samples 3-4) is FLAT:
    check("epoch collapse is False (flat post-break)", trb["collapse"] is False)
    check("epoch n_samples 2", trb["current_epoch"]["n_samples"] == 2)

    # 10. single-sample current epoch abstains (collapse is None).
    single_epoch_rows = [
        (1, "t1", 0, 0, 380, 380, 0.01018, 0.01546, None, None, None, None),
        (2, "t2", 0, 0, 408, 408, 0.00955, 0.01440, 24, 9, 4, 1),
    ]
    trs = compute_trend(single_epoch_rows, metric="Q_eff")
    check("single-sample epoch abstains", trs["collapse"] is None)
    check("break detected single", trs["provisioned"]["break_count"] == 1)

    # 11. --check: epoch-local collapse → rc 1 with ALARM, never silent.
    with tempfile.TemporaryDirectory() as td:
        import io
        import contextlib
        cdb = os.path.join(td, "collapse.sqlite")
        for i, (q, e) in enumerate([
                (0.0100, 0.0150), (0.0102, 0.0152),
                (0.0101, 0.0149), (0.0100, 0.0149)]):
            row = dict(s)
            row["ts"] = "t%d" % i
            row["Q_raw"] = q
            row["Q_eff"] = e
            append(row, db_path=cdb)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check_trend(db_path=cdb)
        check("check collapse rc1", rc == 1)
        check("check alarm line", buf.getvalue().startswith("ALARM:"))

        # 12. --check: flat series → silent rc 0 (nothing to report).
        fdb = os.path.join(td, "flat.sqlite")
        for i in range(3):
            row = dict(s)
            row["ts"] = "f%d" % i
            row["Q_raw"] = 0.0100
            row["Q_eff"] = 0.0150
            append(row, db_path=fdb)
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc2 = check_trend(db_path=fdb)
        check("check flat silent", rc2 == 0 and buf2.getvalue() == "")

        # 13. --check: fresh/absent series → silent abstain rc 0 (no crash).
        buf3 = io.StringIO()
        with contextlib.redirect_stdout(buf3):
            rc3 = check_trend(db_path=os.path.join(td, "fresh.sqlite"))
        check("check fresh abstain", rc3 == 0 and buf3.getvalue() == "")

        # 14. --check: exactly one sample → silent abstain rc 0 (<2 samples).
        sdb = os.path.join(td, "single.sqlite")
        row = dict(s)
        row["ts"] = "s0"
        append(row, db_path=sdb)
        buf4 = io.StringIO()
        with contextlib.redirect_stdout(buf4):
            rc4 = check_trend(db_path=sdb)
        check("check single abstain", rc4 == 0 and buf4.getvalue() == "")

        # 15. --check: unreadable series → fail-closed rc 2 (never a silent pass).
        rc5 = check_trend(db_path=td)
        check("check error rc2", rc5 == 2)

    # 16-18. root-set definition (v0.8.44): a NULL→recorded transition is a
    #        BACKFILL, not a break — otherwise merely starting to record the
    #        definition would reset the epoch and silently mute the live
    #        collapse verdict. Only two RECORDED definitions that disagree
    #        start a new epoch (absence is never an accusation).
    backfill_rows = [
        (1, "t1", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, None),
        (2, "t2", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, None),
        (3, "t3", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, "a" * 64),
    ]
    check("backfill is not a break",
          _definitional_breaks(backfill_rows) == [1])

    moved_rows = [
        (1, "t1", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, "a" * 64),
        (2, "t2", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, "a" * 64),
        (3, "t3", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, "b" * 64),
    ]
    check("recorded→different recorded IS a break",
          _definitional_breaks(moved_rows) == [1, 3])
    check("same recorded definition holds the epoch",
          _definitional_breaks(moved_rows[:2]) == [1])
    # ...and a break still cannot be inferred across an unrecorded row.
    gap_rows = [
        (1, "t1", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, "a" * 64),
        (2, "t2", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, None),
        (3, "t3", 0, 0, 615, 408, 0.0095, 0.0144, 24, 9, 4, 1, "b" * 64),
    ]
    check("no break across an unrecorded row",
          _definitional_breaks(gap_rows) == [1])

    # 19. roots_sha: order-independent, set-sensitive, identity-sensitive.
    with tempfile.TemporaryDirectory() as td:
        ra = os.path.join(td, "ra")
        rb = os.path.join(td, "rb")
        os.makedirs(ra)
        os.makedirs(rb)
        check("roots_sha order-independent", roots_sha([ra, rb]) == roots_sha([rb, ra]))
        check("roots_sha set-sensitive", roots_sha([ra, rb]) != roots_sha([ra]))
        absent = os.path.join(td, "nope")
        check("roots_sha marks absence",
              roots_sha([absent]) != roots_sha([ra]))

    # 20. surface_detail: the fidelity half is measured, not assumed —
    #     byte-identical copies, name collisions, link topology, and the
    #     invariant that the walk's deduped total equals active+archived.
    with tempfile.TemporaryDirectory() as td:
        ra = os.path.join(td, "r1")
        rb = os.path.join(td, "r2")
        outside = os.path.join(td, "ext", "skill-x")
        for d in (os.path.join(ra, "a"), os.path.join(rb, "b"),
                  os.path.join(rb, "a"), outside):
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "SKILL.md"), "w") as fh:
                fh.write("body-A" if d.endswith(("a", "skill-x")) else "body-B")
        arch = os.path.join(ra, ".archive", "old")
        os.makedirs(arch)
        with open(os.path.join(arch, "SKILL.md"), "w") as fh:
            fh.write("dead")
        os.symlink(outside, os.path.join(ra, "link-out"))
        os.symlink(os.path.join(rb, "b"), os.path.join(ra, "link-in"))

        detail = surface_detail([ra, rb])
        check("surface: dup_content counts the byte-identical pair",
              detail["dup_content"] == 1)
        check("surface: dup_path counts the shared name", detail["dup_path"] == 1)
        check("surface: archived classified", detail["archived"] == 1)
        check("surface: active counted", detail["active"] == 3)
        check("surface: unique == active+archived",
              detail["unique"] == detail["active"] + detail["archived"])
        check("surface: symlink dirs inventoried", detail["symlink_dirs"] == 2)
        check("surface: out-of-root link flagged",
              detail["out_of_root_links"] == 1)
        check("surface: definition recorded",
              detail["roots_sha"] == roots_sha([ra, rb]))

        # 21. the record carries its own definition + fidelity (the wiring that
        #     makes a future redefinition detectable instead of remembered).
        rec = compute_sample(detail["active"], detail["archived"], 0,
                             0, 0, 0, 0, detail["total_bytes"], detail["unique"],
                             roots_sha_value=detail["roots_sha"],
                             dup_content=detail["dup_content"],
                             dup_path=detail["dup_path"],
                             symlink_dirs=detail["symlink_dirs"],
                             out_of_root_links=detail["out_of_root_links"])
        for k in ("roots_sha", "dup_content", "dup_path", "symlink_dirs",
                  "out_of_root_links"):
            check(f"record carries {k}", rec.get(k) is not None)

        # 22. roundtrip: the new fields survive append → _load_rows (indices
        #     12..16), so an epoch's definition is readable from the series.
        db = os.path.join(td, "roundtrip.sqlite")
        append(rec, db_path=db)
        rows = _load_rows(db_path=db)
        check("roundtrip roots_sha at index 12", rows[0][12] == detail["roots_sha"])
        check("roundtrip dup_content at index 13", rows[0][13] == 1)
        check("roundtrip fingerprint reads it",
              _kappa_def_fingerprint(rows[0])[1] == detail["roots_sha"])

    print(json.dumps({"schema": "kappa-trend-selftest",
                      "passed": len(passed), "ok": True}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="print the stored series")
    ap.add_argument("--trend", action="store_true", help="print the dQ/dt gradient")
    ap.add_argument("--check", action="store_true",
                    help="report-only watchdog: silent healthy, ALARM+exit 1 on collapse")
    ap.add_argument("--selftest", action="store_true", help="deterministic self-check")
    args = ap.parse_args()
    if args.show:
        show()
        return
    if args.trend:
        return trend()
    if args.check:
        return check_trend()
    if args.selftest:
        return _selftest()
    s = sample()
    append(s)
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    sys.exit(main())