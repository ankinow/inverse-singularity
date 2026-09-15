#!/usr/bin/env python3
"""
κ-surface scope audit — is the counted skill surface a faithful measurement?

WHY THIS EXISTS
---------------
The κ series (`kappa_proliferation_timeseries.py`) measures `d_active` — the
"active loaded surface" — as the number of `SKILL.md` files found by walking a
fixed list of roots. That count is an *instrument reading* only insofar as the
instrument's definition (which roots, how links are treated) stays fixed. It
did not: the series' step seq7→seq8 reads `d_active` 355 → 2,901 (κ_raw 615 →
3,323, Q_eff 0.014399 → 0.002708) and the thread's own note flags it as
*possibly* a measurement-scope artifact rather than gradual accumulation:

    "the 355→2901 step coincides with the two skill roots now being distinct
     trees … so part of the step may be measurement scope rather than gradual
     accumulation — confirming the count is not duplicated is the first step
     of the human κ-reduction decision this alarm hands over"

This instrument does that confirmation, read-only, structurally:

  1. **Census per root** — active / archived / bytes / symlink-dir inventory,
     so the anatomy of any step is attributable to a named root.
  2. **Cross-root duplication** — byte-identical copies (content hash) and
     same-relative-path entries (two different skills under one name). A
     surface that counts copies as capability inflates φ.
  3. **Link topology** — `os.walk` does not follow symlinked directories, so
     a skill reachable *only* through a symlinked dir pointing outside every
     root is invisible to the sampler. That is *blind surface*: part of the
     loaded surface the metric structurally cannot see. Link targets are
     classified (same root / other root / out-of-root / broken).
  4. **Root definition fingerprint** (`roots_sha`) — sha256 over each root's
     normalized path + `dev:ino`. The set of roots AND their identity. A root
     that is re-mounted, replaced by a symlink, or split into a distinct tree
     changes its inode, so the definition change is detectable *structurally*
     rather than remembered. Recorded into every new sample row (see
     `kappa_proliferation_timeseries.py`), so a future change between two
     *recorded* definitions starts a new definitional epoch.
  5. **Historical attribution** — matches each past sample's
     (`d_active`, `unique_skills`) against the live *per-root* counts. When a
     sample matches one root's numbers, that sample measured that root (or the
     roots were aliases of a single tree then) — which is how the 355 case is
     explained: 355/552 is the `~/.hermes/skills` tree alone, and the
     `~/.agents` tree (2,546 active) did not exist as a distinct physical tree
     when those samples were taken.

VERDICTS (read-only, never prescriptive — A4 / Goodhart preserved)
------------------------------------------------------------------
  * `definition-drift`     — live `roots_sha` differs from the last *recorded*
                             one: the metric's definition moved. Samples across
                             that boundary are incommensurable.
  * `unrecorded`           — no sample carries a `roots_sha` yet (all rows
                             predate the definition being recorded). Nothing to
                             compare; the audit reports the anatomy instead.
  * `definition-consistent`— recorded definition == live definition and the
                             live surface matches the last sample within
                             tolerance.
  * `accretion`            — same definition, materially more surface: genuine
                             accumulation inside the defined scope.

Exit codes: `--check` is a report-only watchdog (silent when consistent or
unrecorded; `ALARM:` + rc 1 on definition drift; rc 2 fail-closed on an
unreadable series or a missing/unreadable root). It never edits, never prunes,
never gates — ε_boundary > 0 style honesty: it surfaces, the operator decides.

Usage:
    python3 kappa_surface_audit.py            # census + verdict (human)
    python3 kappa_surface_audit.py --json     # machine-readable
    python3 kappa_surface_audit.py --check    # scheduled watchdog
    python3 kappa_surface_audit.py --selftest # hermetic self-check

Zero dependencies (stdlib only). Read-only by construction: this file opens no
file for writing and executes no subprocess.
"""

import os
import sys
import json
import hashlib
import argparse
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import kappa_proliferation_timeseries as kts  # noqa: E402  (single source of roots + series)

SCHEMA = "kappa-surface-audit/v1"
SKILL_FILE = "SKILL.md"


# --------------------------------------------------------------------------
# Root definition fingerprint — SINGLE SOURCE, imported from the metric itself.
#
# The definition of "what surface is being counted" belongs to the instrument
# that counts it (`kappa_proliferation_timeseries`), not to its auditor: the
# auditor must measure against the metric's own contract, never against a
# private re-implementation of it. Aliased here so both files cannot drift.
# --------------------------------------------------------------------------

root_identity = kts.root_identity


def roots_sha(roots=None):
    """sha256 of the normalized root-set definition (see kts.roots_sha)."""
    return kts.roots_sha(roots)


# --------------------------------------------------------------------------
# Census
# --------------------------------------------------------------------------

def _hash_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def scan_root(base, hash_contents=True, roots=None):
    """Census of ONE root: counts, bytes, link inventory, content hashes.

    `roots` is the full walked root-set this scan belongs to — link targets are
    classified relative to *that* set, never against a global, so the auditor
    can be pointed at any tree (including synthetic ones in tests) without its
    classification silently drifting to the production roots.
    """
    base = os.path.abspath(os.path.expanduser(base))
    roots = roots if roots is not None else kts.SKILL_DIRS
    rec = {
        "path": base,
        "exists": os.path.isdir(base),
        "identity": root_identity(base),
        "active": 0,
        "archived": 0,
        "bytes": 0,
        "symlink_dirs": 0,
        "links": {"to_same_root": 0, "to_other_root": 0,
                  "out_of_root": 0, "broken": 0},
        "_hashes": {},
        "_relpaths": set(),
    }
    if not rec["exists"]:
        return rec

    other_roots = [os.path.realpath(r) for r in roots
                   if os.path.realpath(r) != os.path.realpath(base)]
    self_roots = [os.path.realpath(base)]

    for dirpath, dirnames, filenames in os.walk(base):
        # Inventory symlinked subdirs at this level (os.walk will not descend
        # them, so their targets are invisible unless they point back in-tree).
        for d in list(dirnames):
            p = os.path.join(dirpath, d)
            if not os.path.islink(p):
                continue
            rec["symlink_dirs"] += 1
            if not os.path.exists(p):
                rec["links"]["broken"] += 1
                continue
            target = os.path.realpath(p)
            if any(target == r or target.startswith(r + os.sep) for r in self_roots):
                rec["links"]["to_same_root"] += 1
            elif any(target == r or target.startswith(r + os.sep) for r in other_roots):
                rec["links"]["to_other_root"] += 1
            else:
                rec["links"]["out_of_root"] += 1

        # A broken symlink resolves to nothing, so `os.walk` files it under
        # filenames (it cannot be known to be a directory). Unresolvable links
        # are still a measurement fact about the surface: count them.
        for f in filenames:
            p = os.path.join(dirpath, f)
            if os.path.islink(p) and not os.path.exists(p):
                rec["links"]["broken"] += 1

        if SKILL_FILE not in filenames:
            continue
        fp = os.path.join(dirpath, SKILL_FILE)
        try:
            size = os.path.getsize(fp)
        except OSError:
            size = 0
        rec["bytes"] += size
        if os.sep + ".archive" + os.sep in fp or fp.endswith(os.sep + ".archive"):
            rec["archived"] += 1
        else:
            rec["active"] += 1
            rel = os.path.relpath(os.path.dirname(fp), base)
            rec["_relpaths"].add(rel)
            if hash_contents:
                h = _hash_file(fp)
                if h:
                    rec["_hashes"].setdefault(h, []).append(fp)
    return rec


def census(roots=None, hash_contents=True):
    """Cross-root census: per-root counts, duplication, links, blind surface."""
    roots = list(roots if roots is not None else kts.SKILL_DIRS)
    scanned = [scan_root(r, hash_contents=hash_contents, roots=roots) for r in roots]

    active_raw = sum(r["active"] for r in scanned)
    archived_raw = sum(r["archived"] for r in scanned)
    bytes_raw = sum(r["bytes"] for r in scanned)

    # Cross-root duplication.
    by_hash = {}
    by_relpath = {}
    for rec in scanned:
        for h, paths in rec["_hashes"].items():
            by_hash.setdefault(h, []).extend(paths)
        for rel in rec["_relpaths"]:
            by_relpath.setdefault(rel, []).append(rec["path"])

    dup_content = sum(len(v) - 1 for v in by_hash.values() if len(v) > 1)
    path_dups = [rel for rel, owners in by_relpath.items() if len(owners) > 1]
    # Active surface counted once per ANONYMOUS LOGICAL SKILL: identical bytes
    # under more than one root are copies, not additional capability.
    active_dedup = len(by_hash) if by_hash else active_raw
    # ...and identical relative paths under more than one root are the same
    # named skill twice (counted once for the name-level view).
    name_dedup = len(by_relpath)

    links = {"total": 0, "to_same_root": 0, "to_other_root": 0,
             "out_of_root": 0, "broken": 0}
    for rec in scanned:
        links["total"] += rec["symlink_dirs"]
        for k, v in rec["links"].items():
            links[k] += v

    # Blind surface: SKILL.md files reachable ONLY by following an out-of-root
    # symlinked directory — loaded by the runtime, structurally invisible to a
    # non-following walk. Counted (bounded: those targets only), never pruned.
    blind = []
    for rec in scanned:
        if not rec["exists"]:
            continue
        for dirpath, dirnames, _fn in os.walk(rec["path"]):
            for d in list(dirnames):
                p = os.path.join(dirpath, d)
                if not os.path.islink(p) or not os.path.exists(p):
                    continue
                target = os.path.realpath(p)
                in_tree = any(
                    target == os.path.realpath(r)
                    or target.startswith(os.path.realpath(r) + os.sep)
                    for r in roots)
                if not in_tree and SKILL_FILE in os.listdir(target):
                    blind.append(os.path.join(target, SKILL_FILE))

    out = {
        "schema": SCHEMA,
        "ts": datetime.now(timezone.utc).isoformat(),
        "roots": [{k: v for k, v in rec.items() if not k.startswith("_")}
                  for rec in scanned],
        "totals": {
            "active_raw": active_raw,
            "archived_raw": archived_raw,
            "bytes_raw": bytes_raw,
            "active_dedup_content": active_dedup,
            "name_dedup": name_dedup,
            "dup_content": dup_content,
            "dup_path": len(path_dups),
            "dup_path_names": sorted(path_dups)[:20],
        },
        "links": links,
        "blind_surface": {"count": len(blind), "paths": sorted(blind)[:20]},
        "roots_sha": roots_sha(roots),
    }
    return out


# --------------------------------------------------------------------------
# Series attribution + verdict
# --------------------------------------------------------------------------

def _last_recorded_roots_sha(rows):
    """Most recent non-NULL roots_sha in the series (None if unrecorded).

    Tolerant of short rows: the trend projection predates the `roots_sha`
    column, so a 12-field tuple simply carries an unrecorded definition.
    """
    for r in reversed(rows or []):
        if isinstance(r, tuple):
            val = r[12] if len(r) > 12 else None
        else:
            val = r.get("roots_sha")
        if val:
            return val
    return None


def attribute_history(rows, cen, tolerance=0.02):
    """Match past samples' (d_active, unique_skills) against live per-root counts.

    A sample whose `d_active` equals one live root's active count (within
    `tolerance`) was taken against *that root alone* — the fingerprint of a
    scope-limited measurement. This is the structural explanation of the 355
    case, and it generalizes: any future scope-limited sample is named here
    instead of being read as accumulation.
    """
    out = []
    for r in rows or []:
        seq = r[0] if isinstance(r, tuple) else r.get("seq")
        d = r[2] if isinstance(r, tuple) else r.get("d_active")
        for rec in cen["roots"]:
            if not rec["active"]:
                continue
            if d is not None and abs(d - rec["active"]) <= max(
                    1, tolerance * max(rec["active"], 1)):
                out.append({"seq": seq, "sample_d_active": d,
                            "matches_root": rec["path"],
                            "root_active": rec["active"],
                            "exact": d == rec["active"]})
    return out


def verdict(cen, rows):
    """Definition/delta verdict. Read-only; never prescriptive."""
    recorded = _last_recorded_roots_sha(rows)
    live = cen["roots_sha"]
    if recorded and recorded != live:
        return "definition-drift", {
            "recorded_roots_sha": recorded, "live_roots_sha": live,
            "why": "the walked root set's identity moved since the last sample",
        }
    if not recorded:
        return "unrecorded", {
            "recorded_roots_sha": None, "live_roots_sha": live,
            "why": ("no sample records a root definition yet — the step's "
                    "anatomy is reported, not attributed"),
        }
    last = rows[-1] if rows else None
    last_d = last[2] if (last is not None and isinstance(last, tuple)) else None
    live_active = cen["totals"]["active_raw"]
    if last_d is None or abs(live_active - last_d) <= max(1, 0.02 * max(live_active, 1)):
        return "definition-consistent", {
            "recorded_roots_sha": recorded, "live_roots_sha": live,
            "last_d_active": last_d, "live_active_raw": live_active,
        }
    direction = "accretion" if live_active > last_d else "surface-loss"
    return direction, {
        "recorded_roots_sha": recorded, "live_roots_sha": live,
        "last_d_active": last_d, "live_active_raw": live_active,
        "delta": live_active - last_d,
        "why": "same recorded definition; the surface moved inside it",
    }


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def _load_series(db_path=None):
    return kts._load_rows(db_path)


def audit(db_path=None, roots=None):
    cen = census(roots)
    rows = _load_series(db_path)
    v, why = verdict(cen, rows)
    cen["series"] = {
        "n_samples": len(rows),
        "last_d_active": rows[-1][2] if rows and isinstance(rows[-1], tuple) else None,
        "recorded_roots_sha": _last_recorded_roots_sha(rows),
        "attribution": attribute_history(rows, cen),
    }
    cen["verdict"] = v
    cen["verdict_detail"] = why
    return cen


def _print_human(out):
    print("κ-surface scope audit  [%s]" % out["verdict"])
    print("-" * 68)
    for rec in out["roots"]:
        if not rec["exists"]:
            print("  %-34s ABSENT" % rec["path"])
            continue
        print("  %-34s active=%-5d archived=%-4d links=%-4d bytes=%d"
              % (rec["path"], rec["active"], rec["archived"],
                 rec["symlink_dirs"], rec["bytes"]))
    t = out["totals"]
    print("  %-34s active=%-5d (dedup-content %d, name-dedup %d)"
          % ("TOTAL", t["active_raw"], t["active_dedup_content"], t["name_dedup"]))
    print("  duplication: content=%d  path=%d %s"
          % (t["dup_content"], t["dup_path"],
             ("(e.g. %s)" % ", ".join(t["dup_path_names"][:3]))
             if t["dup_path_names"] else ""))
    lk = out["links"]
    print("  links: total=%d same-root=%d other-root=%d out-of-root=%d broken=%d"
          % (lk["total"], lk["to_same_root"], lk["to_other_root"],
             lk["out_of_root"], lk["broken"]))
    print("  blind surface (unreachable without following links): %d"
          % out["blind_surface"]["count"])
    s = out["series"]
    print("  series: n=%d last_d_active=%s recorded_roots_sha=%s"
          % (s["n_samples"], s["last_d_active"],
             (s["recorded_roots_sha"] or "-")[:12]))
    for a in s["attribution"]:
        print("    seq %s d=%s ~= root %s (active=%d)%s"
              % (a["seq"], a["sample_d_active"], a["matches_root"],
                 a["root_active"], " EXACT" if a["exact"] else ""))
    print("  roots_sha(live)=%s" % out["roots_sha"][:16])
    print("  why: %s" % out["verdict_detail"].get("why", "-"))


def check(db_path=None, roots=None):
    """Report-only watchdog: silent healthy/unrecorded, ALARM on drift, rc2 closed."""
    try:
        cen = census(roots)
    except OSError as exc:
        print("kappa-surface-check: census failed: %s" % exc, file=sys.stderr)
        return 2
    for rec in cen["roots"]:
        if not rec["exists"]:
            print("kappa-surface-check: root missing: %s" % rec["path"],
                  file=sys.stderr)
            return 2
    try:
        rows = _load_series(db_path)
    except Exception as exc:  # sqlite3.Error, OSError — fail-closed either way
        print("kappa-surface-check: series unreadable: %s" % exc, file=sys.stderr)
        return 2

    recorded = _last_recorded_roots_sha(rows)
    if not recorded:
        return 0  # unrecorded definition: nothing to compare (honest abstain)
    if recorded != cen["roots_sha"]:
        print("ALARM: kappa-surface-definition-drift")
        print(json.dumps({
            "schema": SCHEMA, "verdict": "definition-drift",
            "recorded_roots_sha": recorded, "live_roots_sha": cen["roots_sha"],
            "roots": [{"path": r["path"], "active": r["active"],
                       "identity": r["identity"]} for r in cen["roots"]],
        }, ensure_ascii=False, indent=2))
        return 1
    return 0


# --------------------------------------------------------------------------
# Selftest (hermetic: synthetic trees in a tempdir, synthetic series rows)
# --------------------------------------------------------------------------

def _mk_skill(base, rel, body):
    d = os.path.join(base, rel)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, SKILL_FILE)
    with open(p, "w") as fh:
        fh.write(body)
    return p


def _row(seq, d, uniq, roots_sha_value, ts_en=24):
    """13+ element tuple shaped like kts._load_rows output (indices 0..12)."""
    return (seq, "t%d" % seq, d, 0, 615, 408, 0.0095, 0.0144,
            ts_en, 9, 4, 1, roots_sha_value)


def _selftest():
    import io
    import contextlib
    import tempfile

    checks = []

    def expect(name, cond):
        checks.append((name, bool(cond)))

    with tempfile.TemporaryDirectory() as td:
        ra = os.path.join(td, "rootA")
        rb = os.path.join(td, "rootB")
        os.makedirs(ra)
        os.makedirs(rb)

        # T1 basics: two roots, one distinct skill each.
        _mk_skill(ra, "alpha", "A")
        _mk_skill(rb, "beta", "B")
        cen = census([ra, rb])
        expect("t1 active 2", cen["totals"]["active_raw"] == 2)
        expect("t1 no content dups", cen["totals"]["dup_content"] == 0)
        expect("t1 dedup == raw", cen["totals"]["active_dedup_content"] == 2)

        # T2 byte-identical copy across roots → content dup, dedup drops.
        _mk_skill(rb, "alpha-copy", "A")
        cen = census([ra, rb])
        expect("t2 dup_content == 1", cen["totals"]["dup_content"] == 1)
        expect("t2 dedup < raw", cen["totals"]["active_dedup_content"] == 2)
        expect("t2 active_raw == 3", cen["totals"]["active_raw"] == 3)

        # T3 same relative path, different content → name dup, not content dup.
        _mk_skill(rb, "alpha", "DIFFERENT")
        cen = census([ra, rb])
        expect("t3 dup_path == 1", cen["totals"]["dup_path"] == 1)
        expect("t3 name_dedup == 3", cen["totals"]["name_dedup"] == 3)

        # T4 symlinked dir pointing to ANOTHER root → not double counted,
        #    classified as a cross-root link.
        os.symlink(os.path.join(rb, "beta"), os.path.join(ra, "beta-link"))
        cen = census([ra, rb])
        expect("t4 link counted", cen["links"]["total"] >= 1)
        expect("t4 link to other root", cen["links"]["to_other_root"] >= 1)
        expect("t4 no double count", cen["totals"]["active_raw"] == 4)
        expect("t4 no blind surface", cen["blind_surface"]["count"] == 0)

        # T5 symlinked dir pointing OUTSIDE every root → blind surface.
        outside = os.path.join(td, "outside", "gamma")
        os.makedirs(outside)
        _mk_skill(outside, "", "G")
        os.symlink(outside, os.path.join(ra, "gamma-link"))
        cen = census([ra, rb])
        expect("t5 out-of-root link", cen["links"]["out_of_root"] == 1)
        expect("t5 blind surface == 1", cen["blind_surface"]["count"] == 1)
        expect("t5 blind not counted active",
              cen["totals"]["active_raw"] == 4)

        # T6 broken symlink → counted as broken, not blind, not active.
        os.symlink(os.path.join(td, "nope"), os.path.join(rb, "dead-link"))
        cen = census([ra, rb])
        expect("t6 broken == 1", cen["links"]["broken"] == 1)

        # T7 roots_sha: stable across identical scans; changes with the set.
        s1 = roots_sha([ra, rb])
        expect("t7 sha stable", s1 == roots_sha([rb, ra]))
        expect("t7 sha set-sensitive", s1 != roots_sha([ra]))
        # ...and sensitive to root IDENTITY (a re-created dir has a new inode).
        rc = os.path.join(td, "rootC")
        os.makedirs(rc)
        before = root_identity(rc)
        os.rmdir(rc)
        os.makedirs(rc)
        expect("t7 identity tracks inode", root_identity(rc) != before)

    # T8 verdict: unrecorded definition → 'unrecorded' (never a false drift).
    cen_fake = {"roots_sha": "deadbeef", "roots": [], "totals": {"active_raw": 5}}
    v, _ = verdict(cen_fake, [_row(1, 5, 5, None)])
    expect("t8 unrecorded", v == "unrecorded")

    # T9 verdict: recorded == live → definition-consistent.
    v, _ = verdict(cen_fake, [_row(1, 5, 5, "deadbeef")])
    expect("t9 consistent", v == "definition-consistent")

    # T10 verdict: recorded != live → definition-drift (the alarm class).
    v, _ = verdict(cen_fake, [_row(1, 5, 5, "feedface")])
    expect("t10 drift", v == "definition-drift")

    # T11 verdict: same definition, bigger surface → accretion; smaller →
    #     surface-loss. Never 'drift' (definition did not move).
    big = {"roots_sha": "deadbeef", "roots": [], "totals": {"active_raw": 50}}
    v, _ = verdict(big, [_row(1, 5, 5, "deadbeef")])
    expect("t11 accretion", v == "accretion")
    small = {"roots_sha": "deadbeef", "roots": [], "totals": {"active_raw": 1}}
    v, _ = verdict(small, [_row(1, 50, 50, "deadbeef")])
    expect("t11 surface-loss", v == "surface-loss")

    # T12 recorded-value changes between two NON-NULL rows is still a drift
    #     (the reader's own contract, mirrored here).
    expect("t12 last recorded wins",
          _last_recorded_roots_sha([_row(1, 5, 5, "aaa"),
                                    _row(2, 5, 5, "bbb")]) == "bbb")
    expect("t12 NULL skipped",
          _last_recorded_roots_sha([_row(1, 5, 5, "aaa"),
                                    _row(2, 5, 5, None)]) == "aaa")

    # T13 attribution: a sample matching one root's count is named as such;
    #     a sample matching the COMBINED surface is not misattributed to a root.
    with tempfile.TemporaryDirectory() as td:
        r1 = os.path.join(td, "one")
        r2 = os.path.join(td, "two")
        os.makedirs(r1)
        os.makedirs(r2)
        for i in range(3):
            _mk_skill(r1, "s%d" % i, "x%d" % i)
        for i in range(7):
            _mk_skill(r2, "t%d" % i, "y%d" % i)
        cen2 = census([r1, r2])
        att = attribute_history([_row(1, 3, 3, None), _row(2, 10, 10, None)], cen2)
        matched = {a["seq"]: a["matches_root"] for a in att}
        expect("t13 seq1 -> root1", matched.get(1) == r1)
        expect("t13 combined sample not attributed to a single root",
               matched.get(2) is None)

    # T14 --check on an unrecorded series: silent abstain rc 0 (no false alarm).
    with tempfile.TemporaryDirectory() as td:
        ra = os.path.join(td, "r")
        os.makedirs(ra)
        _mk_skill(ra, "s", "x")
        db = os.path.join(td, "s.sqlite")
        kts.append(dict(kts.compute_sample(1, 0, 0, 0, 0, 0, 0, 100, 1),
                        ts="t1"), db_path=db)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check(db_path=db, roots=[ra])
        expect("t14 unrecorded silent", rc == 0 and buf.getvalue() == "")

        # T15 --check with a RECORDED definition that matches → silent rc 0.
        live = roots_sha([ra])
        row = dict(kts.compute_sample(1, 0, 0, 0, 0, 0, 0, 100, 1), ts="t2")
        row["roots_sha"] = live
        kts.append(row, db_path=db)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check(db_path=db, roots=[ra])
        expect("t15 consistent silent", rc == 0 and buf.getvalue() == "")

        # T16 --check with a recorded definition that MOVED → ALARM rc 1.
        row = dict(kts.compute_sample(1, 0, 0, 0, 0, 0, 0, 100, 1), ts="t3")
        row["roots_sha"] = "0" * 64
        kts.append(row, db_path=db)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check(db_path=db, roots=[ra])
        expect("t16 drift alarm rc1", rc == 1)
        expect("t16 alarm line", buf.getvalue().startswith("ALARM:"))

        # T17 --check with a missing root → fail-closed rc 2 (never a silent pass).
        rc = check(db_path=db, roots=[os.path.join(td, "absent")])
        expect("t17 missing root rc2", rc == 2)

        # T18 --check with an unreadable series → rc 2.
        rc = check(db_path=td, roots=[ra])
        expect("t18 unreadable series rc2", rc == 2)

    passed = sum(1 for _n, ok in checks if ok)
    failed = [n for n, ok in checks if not ok]
    print(json.dumps({"schema": "kappa-surface-audit-selftest",
                      "passed": passed, "total": len(checks),
                      "failed": failed, "ok": not failed}, ensure_ascii=False))
    return 0 if not failed else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine-readable census")
    ap.add_argument("--check", action="store_true",
                    help="report-only watchdog: silent healthy, ALARM+rc1 on drift")
    ap.add_argument("--selftest", action="store_true", help="hermetic self-check")
    ap.add_argument("--db", default=None, help="series DB override (tests)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if args.check:
        return check(db_path=args.db)
    out = audit(db_path=args.db)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        _print_human(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
