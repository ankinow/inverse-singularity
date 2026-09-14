#!/usr/bin/env python3
"""Joint-trajectory reader over the SEVEN trend time-series (Q = φ/κ + ε seen whole).

Read-only. Every face of the core equation grew its own append-only time-series with a
`--trend` reader, and each trends ONE face in isolation:

  * ε_code (compressible) — `epsilon_code_trend.py --trend`             (the UNKNOWN% gap)
  * κ / Q (denominator)   — `kappa_proliferation_timeseries.py --trend` (κ_raw/κ_eff, Q=φ/κ)
  * self-κ (own φ/κ)      — `curiosity_kappa_trend.py --trend`          (the runtime's own bloat)
  * ε_code↔ε_system edge  — `a7_boundary_trend.py --trend`              (does the floor move?)
  * ε_system (sovereignty)— `a8_epsilon_system_trend.py --trend`        (the residue to protect)
  * layer-3 evidence      — `a9_claim_evidence_trend.py --trend`        (⟦CLAIM:…⟧ emission)
  * ⊗S: producer (typed)  — `a4_action_typing_trend.py --trend`         (typed intent blocks)

The CURIOSITY synthesis kept returning to one framing — *"the same κ-over-φ curve from
different angles"* — but no instrument ever looked at the faces at once. The core
equation Q = φ/κ + ε ties them: ε_code is the compressible remainder of `+ ε`, κ the
denominator of `φ/κ`, ε_system the residue that must NOT be compressed away, and the last
two faces are the *producers of the evidence* every other face is computed from. A
healthy runtime compresses ε_code (UNKNOWN% → 0, never guessing) **without** (i) letting
κ balloon to swamp the φ it unlocks, (ii) eating ε_system while claiming compression, or
(iii) letting the `⊗S:` / claim producers die while every aggregate still reads flat.

This instrument **imports each sibling's own low-level surface** (single source of truth,
never re-implements a measure) and reports the joint read:

  * `--trend` (`schema axiom-joint-trend/v1`) loads all seven faces and emits a **`joint`
    verdict**. Beyond the three original single-face trade-offs it carries the cross-face
    CONTRADICTIONS the four newer series made possible — each of which the three-face
    reader silently called healthy, because it never looked at those faces:

      - `compress-coherent`       ε_code improving while κ not-collapsing (healthy)
      - `compress-paradox`        ε_code improving WHILE κ worsens (the trade-off — the
                                  UNKNOWN% fell only because the kit ballooned: a ketosis,
                                  not a diet)
      - `kappa-and-eps-collapse`  both compressible terms drifting the wrong way (A2 alarm)
      - `sovereignty-paradox`     ε_code improving WHILE ε_system erodes — the compression
                                  is paid for with the sovereignty residue (the Boundary
                                  Paradox read across two faces; the old reader called
                                  this `compress-coherent` by construction)
      - `producer-dead-letter`    the `⊗S:` producer erodes while κ reads stable — the
                                  machine that writes the intent blocks every κ-over-φ
                                  curve is built from is dying, so those readings
                                  silently lose their floor
      - `evidence-dead-letter`    layer-3 claim emission erodes while κ reads stable — the
                                  opaque, non-LLM verifier is fed by nobody
      - `self-bloat`              κ + ε stable while the runtime's own φ/κ worsens
      - `stable`                  nothing moving
      - `abstain`                 the two compressible-term faces are below 2 samples

    Honest abstention is **per series**: a contradiction whose legs are too sparse is
    reported in `unevaluable` and can never fire — it is never treated as "healthy". The
    headline `abstain` is reserved for the case where the compressible-term faces
    themselves (ε_code, κ) cannot be read — then the joint has no headline to give.

    It never prescribes: the verdict is a read, and `--selftest` manufactures synthetic
    series to prove the fire logic, but it gates nothing.

The Goodhart safeguard is identical to its siblings: read-only, no append, no decision
path, no prescriptive consumer. It merely makes the *joint* trajectory visible — the one
thing each single-face trend structurally cannot see.

Modes:
  * `--trend`    (default) — print the full JSON joint read, exit 0 always.
  * `--check`    — report-only read: **silent** (exit 0) on a healthy joint verdict
    (`compress-coherent` / `stable` / `self-bloat` / `abstain`), and prints a compact
    `ALARM:` line + the JSON and exits 1 on the five alarm verdicts. The exit code is a
    *reporting* mechanism (so a cron delivery surfaces the alarm), NOT a gate on any
    action — nothing edits, prunes, or prescribes (the same contract as
    `a5_constraint_provenance.py --check`).
  * `--selftest` — prove the fire/abstain logic on synthetic series; exits non-zero on
    failure.
"""

import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# source of truth: every sibling reader's low-level surface, imported — never
# re-implemented. (The `trend()` wrappers print-to-stdout or return exit codes, so we
# import the data functions they wrap, which return dicts/tuples.)
import epsilon_code_trend as eps  # noqa: E402
import kappa_proliferation_timeseries as kappa  # noqa: E402
import curiosity_kappa_trend as ckappa  # noqa: E402
import a7_boundary_trend as bnd  # noqa: E402
import a8_epsilon_system_trend as esys  # noqa: E402
import a9_claim_evidence_trend as clmt  # noqa: E402
import a4_action_typing_trend as atyped  # noqa: E402

SCHEMA = "axiom-joint-trend/v1"

# The joint verdicts a report-only watchdog should surface. Everything else
# (`compress-coherent`, `stable`, `self-bloat`, `abstain`) is a healthy read and stays
# silent. This is a *reporting* classification, never a gate: nothing acts on it.
ALARM_VERDICTS = (
    "kappa-and-eps-collapse",
    "compress-paradox",
    "sovereignty-paradox",
    "producer-dead-letter",
    "evidence-dead-letter",
)
HEALTHY_VERDICTS = ("compress-coherent", "stable", "self-bloat", "abstain")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"
# plain-string paths (the sibling instruments' convention — the readers take str)
EPS_DB = str(DATA / "epsilon_code_trend.sqlite")
KAPPA_DB = str(DATA / "kappa_timeseries.sqlite")
CKAPPA_DB = str(DATA / "curiosity_kappa_trend.sqlite")
BND_DB = str(DATA / "a7_boundary_trend.sqlite")
ESYS_DB = str(DATA / "a8_epsilon_system_trend.sqlite")
CLAIM_DB = str(DATA / "a9_claim_evidence_trend.sqlite")
TYPED_DB = str(DATA / "a4_action_typing_trend.sqlite")

# the seven faces, in the order they appear in the report
FACE_ORDER = ("epsilon_code", "kappa", "curiosity_kappa", "boundary",
              "epsilon_system", "claims", "typed")

# the two compressible-term faces — the legs of the base synthesis (and the legs whose
# unreadability makes the joint abstain rather than guess)
BASE_LEGS = ("epsilon_code", "kappa")

KNOWN_FLAGS = ("--trend", "--check", "--selftest", "--help", "-h")

USAGE = """axiom_joint_trend — joint read of the seven Q = φ/κ + ε trend series (read-only)

  --trend      (default) print the joint JSON read (exit 0 always)
  --check      report-only: SILENT (exit 0) on a healthy verdict; prints the ALARM line
               + JSON and exits 1 on any of the five alarm verdicts
  --selftest   prove the fire/abstain logic on synthetic series (exit 0/1)
  --help, -h   this text (exit 0)

Alarm verdicts:  kappa-and-eps-collapse, compress-paradox, sovereignty-paradox,
                 producer-dead-letter, evidence-dead-letter
Healthy (silent): compress-coherent, stable, self-bloat, abstain
"""


# ---------------------------------------------------------------------------
# arg hygiene — an unrecognized flag must never read (or, worse, mutate) anything
# ---------------------------------------------------------------------------
def arg_guard(args, err=sys.stderr, out=sys.stdout):
    """Up-front arg hygiene (the v0.8.38 family pattern).

    This instrument is read-only, but its `--check` alarm is only ever seen through a
    wrapper: a typo'd flag (`--chek`) would otherwise fall through to the default print
    path, exit 0, and *silently disable the alarm*. Touches no database: returns 2
    (unknown flag → usage on stderr), 0 (`--help` printed usage), or None (proceed).
    """
    unknown = [a for a in args if a not in KNOWN_FLAGS]
    if unknown:
        err.write("unknown flag(s): %s\n%s" % (" ".join(unknown), USAGE))
        return 2
    if "--help" in args or "-h" in args:
        out.write(USAGE)
        return 0
    return None


# ---------------------------------------------------------------------------
# the seven face readers — each one is the sibling's own surface, never a copy
# ---------------------------------------------------------------------------
def _eps_face(db=EPS_DB):
    """ε_code UNKNOWN% face. `eps.trend(out_db)` returns a dict directly."""
    r = eps.trend(str(db))
    return {
        "verdict": r.get("verdict", "abstain"),
        "samples": r.get("samples", 0),
        "evidence": {"last_frac": r.get("last_frac"), "delta_frac": r.get("delta_frac"),
                     "last_total": r.get("last_total")},
    }


def _kappa_face(db=KAPPA_DB):
    """κ/Q face. Reuses the sibling's own `_load_rows` + `compute_trend` (single
    source of truth) rather than the print-to-stdout `trend()` wrapper."""
    rows = kappa._load_rows(str(db))  # noqa: SLF001  (deliberate source-of-truth import)
    tr = kappa.compute_trend(rows, metric="Q_eff")
    collapse = tr.get("collapse")
    n = tr.get("n", 0)
    if collapse is None:
        verdict = "abstain"
    else:
        verdict = "worsening" if collapse else "stable"
    return {
        "verdict": verdict,
        "samples": n,
        "evidence": {"last_q_eff": tr.get("last_q"), "dq": tr.get("dq"),
                     "epoch_samples": (tr.get("current_epoch") or {}).get("n_samples")},
    }


def _ckappa_face(db=CKAPPA_DB):
    """CURIOSITY self-bloat face. Reuses the sibling's `_load_rows` + `compute_trend`."""
    rows = ckappa._load_rows(str(db))  # noqa: SLF001
    tr = ckappa.compute_trend(rows)
    worsening = tr.get("worsening")
    n = tr.get("n", 0)
    if worsening is None:
        verdict = "abstain"
    else:
        verdict = "worsening" if worsening else "stable"
    return {
        "verdict": verdict,
        "samples": n,
        "evidence": {"last_bloat_bytes": tr.get("last_bloat_bytes"),
                     "delta_bloat_bytes": tr.get("delta_bloat_bytes")},
    }


def _boundary_face(db=BND_DB):
    """ε_code↔ε_system EDGE face (the a7 trend: does the undecidable floor move?)."""
    r = bnd.trend(str(db))
    return {
        "verdict": r.get("verdict", "abstain"),
        "samples": r.get("samples", 0),
        "evidence": {"last_code_count": r.get("last_code_count"),
                     "last_boundary_count": r.get("last_boundary_count"),
                     "last_total": r.get("last_total")},
    }


def _esys_face(db=ESYS_DB):
    """ε_system (sovereignty) face (the a8 trend: honesty-residue moving toward zero?)."""
    r = esys.trend(str(db))
    return {
        "verdict": r.get("verdict", "abstain"),
        "samples": r.get("samples", 0),
        "evidence": {"last_honesty": r.get("last_honesty"),
                     "delta_honesty": r.get("delta_honesty"),
                     "last_eps_system": r.get("last_eps_system")},
    }


def _claim_face(db=CLAIM_DB):
    """Layer-3 evidence face (the a9 trend: is ⟦CLAIM:…⟧ ever emitted?)."""
    r = clmt.trend(str(db))
    return {
        "verdict": r.get("verdict", "abstain"),
        "samples": r.get("samples", 0),
        "evidence": {"last_claim_msgs": r.get("last_claim_msgs"),
                     "last_narrative_msgs": r.get("last_narrative_msgs"),
                     "last_claim_rate": r.get("last_claim_rate")},
    }


def _typed_face(db=TYPED_DB):
    """⊗S: producer face (the a4 trend: is the typed-intent stream alive?)."""
    r = atyped.trend(str(db))
    return {
        "verdict": r.get("verdict", "abstain"),
        "samples": r.get("samples", 0),
        "evidence": {"last_typed": r.get("last_typed"),
                     "last_coverage": r.get("last_coverage"),
                     "last_curve_state": r.get("last_curve_state")},
    }


def _read_faces(eps_db=EPS_DB, kap_db=KAPPA_DB, ckap_db=CKAPPA_DB, bnd_db=BND_DB,
                esys_db=ESYS_DB, claim_db=CLAIM_DB, typed_db=TYPED_DB):
    return {
        "epsilon_code": _eps_face(eps_db),
        "kappa": _kappa_face(kap_db),
        "curiosity_kappa": _ckappa_face(ckap_db),
        "boundary": _boundary_face(bnd_db),
        "epsilon_system": _esys_face(esys_db),
        "claims": _claim_face(claim_db),
        "typed": _typed_face(typed_db),
    }


# ---------------------------------------------------------------------------
# the joint predicate — pure, DB-independent
# ---------------------------------------------------------------------------
def _resolve(reads):
    """Cross-face contradiction resolution. Never guesses, never silently healthy.

    Priority (first match wins), then the base synthesis:

      1 `kappa-and-eps-collapse`  both compressible terms drifting  (A2 alarm)
      2 `sovereignty-paradox`     ε_code compressing WHILE ε_system erodes
      3 `compress-paradox`        ε_code compressing WHILE κ balloons (ketosis)
      4 `producer-dead-letter`    ⊗S: producer eroding, κ reading "stable"
      5 `evidence-dead-letter`    layer-3 emission eroding, κ reading "stable"
      6 `self-bloat`              own φ/κ worsening while κ + ε hold
      7 `compress-coherent`       ε_code compressing with κ held    (healthy)
      8 `stable`                  nothing moving

    A candidate whose legs are below 2 samples is *unevaluable*: it is listed and can
    never fire, but is never folded into "healthy". `abstain` is reserved for the two
    compressible-term faces (ε_code, κ) being unreadable — without them there is no
    headline to give.
    """
    verdicts = {f: reads[f]["verdict"] for f in FACE_ORDER}
    samples = {f: reads[f]["samples"] for f in FACE_ORDER}
    sparse = [f for f in FACE_ORDER if samples[f] < 2]
    usable = {f: samples[f] >= 2 for f in FACE_ORDER}

    v = verdicts
    candidates = (
        ("kappa-and-eps-collapse", ("epsilon_code", "kappa"),
         v["epsilon_code"] == "worsening" and v["kappa"] == "worsening"),
        ("sovereignty-paradox", ("epsilon_code", "epsilon_system"),
         v["epsilon_code"] == "improving" and v["epsilon_system"] == "sovereignty-eroding"),
        ("compress-paradox", ("epsilon_code", "kappa"),
         v["epsilon_code"] == "improving" and v["kappa"] == "worsening"),
        ("producer-dead-letter", ("kappa", "typed"),
         v["typed"] == "signal-eroding" and v["kappa"] != "worsening"),
        ("evidence-dead-letter", ("kappa", "claims"),
         v["claims"] == "evidence-eroding" and v["kappa"] != "worsening"),
        ("self-bloat", ("curiosity_kappa",),
         v["curiosity_kappa"] == "worsening" and v["epsilon_code"] != "worsening"
         and v["kappa"] == "stable"),
    )

    unevaluable = []
    fired = None
    fired_legs = None
    for name, legs, fires in candidates:
        missing = [f for f in legs if not usable[f]]
        if missing:
            unevaluable.append({"verdict": name, "sparse": missing})
            continue
        if fires:
            fired, fired_legs = name, legs
            break

    if fired is None:
        if not (usable["epsilon_code"] and usable["kappa"]):
            return "abstain", {"sparse": sparse}, sparse, unevaluable
        fired_legs = ("epsilon_code", "kappa")
        if v["epsilon_code"] == "improving" and v["kappa"] != "worsening":
            fired = "compress-coherent"
        else:
            fired = "stable"

    detail = {
        "legs": {f: verdicts[f] for f in (fired_legs or BASE_LEGS)},
        "evidence": {f: reads[f]["evidence"] for f in (fired_legs or BASE_LEGS)},
    }
    # the Boundary Paradox triangulated: when the compression/sovereignty contradiction
    # fires, the edge face says *which side moved* (floor widening vs code re-opening).
    if fired == "sovereignty-paradox" and usable["boundary"]:
        detail["boundary_context"] = dict(reads["boundary"]["evidence"],
                                          verdict=verdicts["boundary"])
    return fired, detail, sparse, unevaluable


def trend(eps_db=EPS_DB, kap_db=KAPPA_DB, ckap_db=CKAPPA_DB, bnd_db=BND_DB,
          esys_db=ESYS_DB, claim_db=CLAIM_DB, typed_db=TYPED_DB):
    reads = _read_faces(eps_db, kap_db, ckap_db, bnd_db, esys_db, claim_db, typed_db)
    verdict, detail, sparse, unevaluable = _resolve(reads)
    return {
        "schema": SCHEMA,
        "samples": {f: reads[f]["samples"] for f in FACE_ORDER},
        "verdicts": {f: reads[f]["verdict"] for f in FACE_ORDER},
        "joint_verdict": verdict,
        "detail": detail,
        "sparse": sparse,
        "unevaluable": unevaluable,
    }


def _check(out, stream=sys.stdout):
    """Report-only watchdog body: returns an exit code, prints only on alarm."""
    verdict = out["joint_verdict"]
    if verdict not in ALARM_VERDICTS:
        return 0
    legs = out.get("detail", {}).get("legs", {})
    stream.write("ALARM: %s (%s)\n"
                 % (verdict, " ".join("%s=%s" % (k, val) for k, val in legs.items())))
    stream.write(json.dumps(out, indent=2) + "\n")
    return 1


# ---------------------------------------------------------------------------
# selftest — synthetic series per contradiction, hermetic; live read last
# ---------------------------------------------------------------------------
def _mk(verdict, samples=3):
    """A fabricated face read, for the pure-predicate cases."""
    return {"verdict": verdict, "samples": samples, "evidence": {}}


def _fresh_faces(**over):
    """All seven faces healthy by default; `over` overrides per face."""
    base = {f: _mk("abstain", 3) for f in FACE_ORDER}
    base.update({
        "epsilon_code": _mk("stable"), "kappa": _mk("stable"),
        "curiosity_kappa": _mk("stable"), "boundary": _mk("boundary-stable"),
        "epsilon_system": _mk("sovereignty-stable"), "claims": _mk("evidence-stable"),
        "typed": _mk("signal-stable"),
    })
    base.update(over)
    return base


# --- synthetic series seeders (each mirrors the sibling's own schema) --------
def _seed_eps(path, fracs):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,"
                " total INTEGER NOT NULL, unknown INTEGER NOT NULL, unknown_frac REAL NOT NULL,"
                " mutation INTEGER NOT NULL, observe INTEGER NOT NULL, producer_sha TEXT NOT NULL)")
    for i, f in enumerate(fracs):
        con.execute("INSERT INTO samples (ts,total,unknown,unknown_frac,mutation,observe,"
                    "producer_sha) VALUES (?,?,?,?,?,?,?)",
                    ("t%d" % i, 5500, int(f * 55), f, 1000, 4000, "sha"))
    con.commit()
    con.close()


def _seed_kappa(path, q_vals):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,"
                " d_active INTEGER, archived INTEGER, plugins INTEGER, unique_skills INTEGER,"
                " skill_bytes INTEGER, phi REAL, kappa_raw INTEGER, kappa_eff INTEGER,"
                " Q_raw REAL, Q_eff REAL, toolsets_enabled INTEGER, toolsets_disabled INTEGER,"
                " mcp_enabled INTEGER, mcp_disabled INTEGER)")
    for i, q in enumerate(q_vals):
        con.execute("INSERT INTO samples (ts,d_active,archived,plugins,unique_skills,skill_bytes,"
                    "phi,kappa_raw,kappa_eff,Q_raw,Q_eff,toolsets_enabled,toolsets_disabled,"
                    "mcp_enabled,mcp_disabled) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("t%d" % i, 355, 197, 25, 2580, 900000, 1.25, 615, 408, 0.003, q,
                     24, 9, 4, 1))
    con.commit()
    con.close()


def _seed_ckappa(path, bloat_bytes):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,"
                " threads INTEGER, total_bytes INTEGER, open_threads INTEGER,"
                " resolved_threads INTEGER, closed_threads INTEGER, largest_title TEXT,"
                " largest_bytes INTEGER, largest_phi_state TEXT, bloat_count INTEGER,"
                " bloated_bytes INTEGER, bloated TEXT, verdict TEXT)")
    for i, b in enumerate(bloat_bytes):
        con.execute("INSERT INTO samples (ts,threads,total_bytes,open_threads,resolved_threads,"
                    "closed_threads,largest_title,largest_bytes,largest_phi_state,bloat_count,"
                    "bloated_bytes,bloated,verdict) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("t%d" % i, 9, 78000, 6, 3, 0, "κ Proliferation", 30000, "resolved",
                     2, b, "[]", "SELF-BLOAT"))
    con.commit()
    con.close()


def _seed_bnd(path, code_counts, bound_counts, total=5000):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT,"
                " total INTEGER, code INTEGER, boundary INTEGER, code_frac REAL,"
                " boundary_frac REAL, boundary_ratio REAL, verdict TEXT)")
    for i, (c, b) in enumerate(zip(code_counts, bound_counts)):
        con.execute("INSERT INTO samples (ts,total,code,boundary,code_frac,boundary_frac,"
                    "boundary_ratio,verdict) VALUES (?,?,?,?,?,?,?,?)",
                    ("t%d" % i, total, c, b, c / float(total), b / float(total),
                     (b / float(c) if c else float("inf")), "MIXED-BOUNDARY"))
    con.commit()
    con.close()


def _seed_esys(path, honesty, typed=7151):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT,"
                " typed INTEGER, untyped_ambiguous INTEGER, mislabels INTEGER,"
                " honesty INTEGER, eps_code REAL, eps_system REAL, probe_verdict TEXT)")
    for i, h in enumerate(honesty):
        con.execute("INSERT INTO samples (ts,typed,untyped_ambiguous,mislabels,honesty,"
                    "eps_code,eps_system,probe_verdict) VALUES (?,?,?,?,?,?,?,?)",
                    ("t%d" % i, typed, 6000, 30, h, 1.32, h / float(typed), "SOVEREIGN"))
    con.commit()
    con.close()


def _seed_claims(path, claim_counts):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT,"
                " assistant_msgs INTEGER, claim_msgs INTEGER, narrative_msgs INTEGER,"
                " claim_rate REAL, narrative_rate REAL)")
    for i, c in enumerate(claim_counts):
        con.execute("INSERT INTO samples (ts,assistant_msgs,claim_msgs,narrative_msgs,"
                    "claim_rate,narrative_rate) VALUES (?,?,?,?,?,?)",
                    ("t%d" % i, 6000, c, 300, c / 6000.0, 0.05))
    con.commit()
    con.close()


def _seed_typed(path, counts):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT,"
                " files INTEGER, sessions INTEGER, typed_sessions INTEGER,"
                " blocks_typed INTEGER, blocks_inferred INTEGER, blocks_unknown INTEGER,"
                " coverage REAL, mislabels INTEGER, curve_state TEXT, mut_low REAL,"
                " rho REAL, ratio REAL)")
    for i, c in enumerate(counts):
        con.execute("INSERT INTO samples (ts, files, sessions, typed_sessions, blocks_typed,"
                    "blocks_inferred, blocks_unknown, coverage, mislabels, curve_state,"
                    "mut_low, rho, ratio) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("t%d" % i, 33, 202, 124, c, 4000, 3500, c / 10000.0, 0,
                     "no-collapse", 0.14, 0.286, 0.69))
    con.commit()
    con.close()


def _seed_joint(root, *, eps_fracs=(3.90, 3.87, 3.85), kap_q=(0.0144, 0.0144, 0.0144),
                ckap_bloat=(56000, 56000, 56000), bnd_code=(128, 128, 128),
                bnd_bound=(83, 83, 83), esys_honesty=(140, 140, 140),
                claim_counts=(10, 10, 10), typed_counts=(3259, 3259, 3259)):
    """Seed a hermetic 7-DB joint world and return the `trend()` kwargs for it."""
    d = tempfile.mkdtemp(prefix="joint-", dir=root)
    p = lambda n: os.path.join(d, n)  # noqa: E731
    _seed_eps(p("eps.sqlite"), eps_fracs)
    _seed_kappa(p("kappa.sqlite"), kap_q)
    _seed_ckappa(p("ckappa.sqlite"), ckap_bloat)
    _seed_bnd(p("bnd.sqlite"), bnd_code, bnd_bound)
    _seed_esys(p("esys.sqlite"), esys_honesty)
    _seed_claims(p("claims.sqlite"), claim_counts)
    _seed_typed(p("typed.sqlite"), typed_counts)
    return {"eps_db": p("eps.sqlite"), "kap_db": p("kappa.sqlite"),
            "ckap_db": p("ckappa.sqlite"), "bnd_db": p("bnd.sqlite"),
            "esys_db": p("esys.sqlite"), "claim_db": p("claims.sqlite"),
            "typed_db": p("typed.sqlite")}


def _arg_hygiene_check(tmp):
    """Pin the guard end-to-end from a hermetic copy (tmp/hygiene/examples + …/data):
    `--help` / a typo'd flag must exit before any series DB is created. The joint's
    `--check` is the alarm path a wrapper runs — a typo there would fall through to the
    default read, exit 0, and silently disable the alarm."""
    src = Path(__file__).resolve()
    root = os.path.join(tmp, "hygiene")
    ex_dir = os.path.join(root, "examples")
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir)
    shutil.copytree(str(src.parent), ex_dir)
    script = os.path.join(ex_dir, src.name)

    def run(*flags):
        proc = subprocess.run([sys.executable, script, *flags],
                              capture_output=True, text=True, timeout=300)
        return proc, sorted(os.listdir(data_dir))

    sink = io.StringIO()
    pure = (arg_guard(["--trend", "--check", "--selftest"], err=sink, out=sink) is None
            and arg_guard(["--help"], err=sink, out=sink) == 0
            and arg_guard(["--zz-bogus"], err=sink, out=sink) == 2)
    proc_help, files_help = run("--help")
    proc_bad, files_bad = run("--chek")            # realistic typo of --check
    proc_read, files_read = run("--trend")         # fresh world: abstain, not a crash
    out = {
        "guard-pure": pure,
        "help-no-effect": (proc_help.returncode == 0
                           and USAGE.splitlines()[0] in proc_help.stdout
                           and files_help == []),
        "unknown-exit-2": (proc_bad.returncode == 2
                           and "unknown flag" in proc_bad.stderr
                           and files_bad == []),
        "read-fresh-abstain": (proc_read.returncode == 0
                               and '"abstain"' in proc_read.stdout),
    }
    shutil.rmtree(root, ignore_errors=True)
    return out


def _selftest():
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print("  selftest[%s] %s  %s" % (name.ljust(20), "PASS" if cond else "FAIL", note))

    # 1. the seven readers are importable and expose the expected low-level surfaces
    surfaces = ((eps, ("trend",)), (kappa, ("_load_rows", "compute_trend")),
                (ckappa, ("_load_rows", "compute_trend")), (bnd, ("trend",)),
                (esys, ("trend",)), (clmt, ("trend",)), (atyped, ("trend",)))
    missing = [m.__name__ + "." + a for m, attrs in surfaces for a in attrs
               if not hasattr(m, a)]
    check("imports-seven", not missing, "7 sibling surfaces imported: %s" % (missing or "ok"))

    # 2. the pure predicate: one case per contradiction + healthy + base synthesis
    v, d, sp, un = None, None, None, None

    def joint(**over):
        return _resolve(_fresh_faces(**over))[0]

    check("coherent", joint(epsilon_code=_mk("improving")) == "compress-coherent",
          "ε_code↑ κ= → compress-coherent")
    check("compress-paradox",
          joint(epsilon_code=_mk("improving"), kappa=_mk("worsening")) == "compress-paradox",
          "ε_code↑ κ↓ → compress-paradox (ketosis)")
    check("double-collapse",
          joint(epsilon_code=_mk("worsening"), kappa=_mk("worsening")) == "kappa-and-eps-collapse",
          "ε_code↓ κ↓ → kappa-and-eps-collapse (A2)")
    check("sovereignty-paradox",
          joint(epsilon_code=_mk("improving"),
                epsilon_system=_mk("sovereignty-eroding")) == "sovereignty-paradox",
          "ε_code↑ ε_system-eroding → sovereignty-paradox (was 'coherent')")
    check("producer-dead-letter",
          joint(typed=_mk("signal-eroding")) == "producer-dead-letter",
          "⊗S: eroding κ= → producer-dead-letter")
    check("evidence-dead-letter",
          joint(claims=_mk("evidence-eroding")) == "evidence-dead-letter",
          "⟦CLAIM⟧ eroding κ= → evidence-dead-letter")
    check("self-bloat", joint(curiosity_kappa=_mk("worsening")) == "self-bloat",
          "self-κ↓ only → self-bloat")
    check("stable", joint() == "stable", "all flat → stable")
    check("priority-collapse-first",
          joint(epsilon_code=_mk("worsening"), kappa=_mk("worsening"),
                typed=_mk("signal-eroding")) == "kappa-and-eps-collapse",
          "an alarm never hides behind another alarm")

    # 3. abstain is per series: an unevaluable contradiction is reported, never folded
    #    into "healthy"; the headline abstain is reserved for the compressible faces.
    v, d, sp, un = _resolve(_fresh_faces(epsilon_code=_mk("improving"),
                                        epsilon_system=_mk("sovereignty-eroding", 1)))
    check("per-series-abstain", v == "compress-coherent" and sp == ["epsilon_system"]
          and un == [{"verdict": "sovereignty-paradox", "sparse": ["epsilon_system"]}],
          "ε_system sparse → contradiction listed unevaluable, never 'healthy'")
    v, d, sp, un = _resolve(_fresh_faces(kappa=_mk("stable", 1)))
    check("headline-abstain", v == "abstain" and d.get("sparse") == ["kappa"],
          "κ unreadable → abstain (no headline)")
    v, _, _, _ = _resolve(_fresh_faces(epsilon_code=_mk("improving", 1), kappa=_mk("stable", 1)))
    check("abstain-lists-all", v == "abstain", "both compressible faces sparse → abstain")

    # 4. end-to-end on SYNTHETIC series: the real imported readers, hermetic DBs
    tmp = tempfile.mkdtemp(prefix="ajt-selftest-")
    w = _seed_joint(tmp)
    check("e2e-coherent", trend(**w)["joint_verdict"] == "compress-coherent",
          "healthy control (7 real readers on synthetic series)")
    w = _seed_joint(tmp, esys_honesty=(104, 90, 78))
    out = trend(**w)
    check("e2e-sovereignty-paradox", out["joint_verdict"] == "sovereignty-paradox",
          "ε_code↑ + ε_system honesty falling → sovereignty-paradox")
    check("e2e-paradox-context", out["detail"].get("boundary_context", {}).get("verdict")
          == "boundary-stable", "the edge face rides along as context")
    w = _seed_joint(tmp, typed_counts=(3259, 3100, 2900))
    check("e2e-producer-dead-letter", trend(**w)["joint_verdict"] == "producer-dead-letter",
          "typed blocks falling → producer-dead-letter")
    w = _seed_joint(tmp, claim_counts=(10, 7, 4))
    check("e2e-evidence-dead-letter", trend(**w)["joint_verdict"] == "evidence-dead-letter",
          "claim emission falling → evidence-dead-letter")
    w = _seed_joint(tmp, kap_q=(0.0144, 0.0130, 0.0120))
    check("e2e-compress-paradox", trend(**w)["joint_verdict"] == "compress-paradox",
          "κ collapsing with ε improving → compress-paradox")
    w = _seed_joint(tmp, eps_fracs=(3.80, 3.85, 3.90), kap_q=(0.0144, 0.0130, 0.0120))
    check("e2e-double-collapse", trend(**w)["joint_verdict"] == "kappa-and-eps-collapse",
          "both compressible terms drifting → collapse alarm")
    w = _seed_joint(tmp, eps_fracs=(3.85, 3.85, 3.85), ckap_bloat=(30000, 45000, 56000))
    check("e2e-self-bloat", trend(**w)["joint_verdict"] == "self-bloat",
          "self-κ bloating, κ+ε held → self-bloat")
    w = _seed_joint(tmp, eps_fracs=(3.85,))
    out = trend(**w)
    check("e2e-abstain", out["joint_verdict"] == "abstain"
          and out["sparse"] == ["epsilon_code"], "a one-sample face → abstain, no guessing")
    w = _seed_joint(tmp, esys_honesty=(140,))
    out = trend(**w)
    check("e2e-unevaluable", out["joint_verdict"] == "compress-coherent"
          and any(u["verdict"] == "sovereignty-paradox" for u in out["unevaluable"]),
          "sparse ε_system → the paradox is unevaluable, not healthy")

    # 5. alarm classification + the --check report contract (rc 0 silent / rc 1 ALARM)
    check("alarm-verdicts", set(ALARM_VERDICTS) == {
        "kappa-and-eps-collapse", "compress-paradox", "sovereignty-paradox",
        "producer-dead-letter", "evidence-dead-letter"},
        "exactly the five contradiction verdicts are report-worthy")
    check("healthy-disjoint", set(ALARM_VERDICTS).isdisjoint(HEALTHY_VERDICTS),
          "no healthy verdict is ever surfaced")
    silent = all(_check({"joint_verdict": h, "detail": {}}, stream=io.StringIO()) == 0
                 for h in HEALTHY_VERDICTS)
    check("check-healthy-silent", silent, "healthy → rc 0, no output")
    alarmed = True
    for a in ALARM_VERDICTS:
        buf = io.StringIO()
        rc = _check({"joint_verdict": a, "detail": {"legs": {"kappa": "stable"}}}, stream=buf)
        alarmed &= (rc == 1 and buf.getvalue().startswith("ALARM:"))
    check("check-alarm-rc1", alarmed, "every alarm verdict → ALARM line + rc 1")

    # 6. live read (asserting only that it runs end-to-end; the live shape is whatever
    #    it is — the point is the seven readers resolve against the production series)
    try:
        out = trend()
        ok &= out["schema"] == SCHEMA
        ok &= isinstance(out["joint_verdict"], str)
        ok &= sorted(out["samples"]) == sorted(FACE_ORDER)
        print("  selftest[%s] %s  live: %s (samples %s)"
              % ("live-read".ljust(20), "PASS",
                 out["joint_verdict"], list(out["samples"].values())))
    except Exception as e:  # noqa: BLE001
        print("  selftest[%s] FAIL (%s)" % ("live-read".ljust(20), e))
        ok = False

    # 7. arg hygiene, end-to-end from a hermetic copy
    for _name, _good in _arg_hygiene_check(tmp).items():
        check("arg-" + _name, _good, "guard runs before any DB access (hermetic re-run)")

    shutil.rmtree(tmp, ignore_errors=True)
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
        sys.exit(_check(out))

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
