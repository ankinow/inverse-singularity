#!/usr/bin/env python3
"""Joint-trajectory reader over the three trend time-series (Q = φ/κ + ε seen whole).

Read-only. The ε-thread, κ-Proliferation thread, and CURIOSITY self-bloat thread each
built an append-only time-series with a `--trend` reader, and each trends ONE face of
the core equation in isolation:

  * ε_code  — `epsilon_code_trend.py --trend`        (the compressible UNKNOWN% gap)
  * κ / Q   — `kappa_proliferation_timeseries.py --trend`  (κ_raw/κ_eff and Q=φ/κ)
  * self-κ  — `curiosity_kappa_trend.py --trend`     (the runtime's own φ/κ bloat)

The CURIOSITY synthesis kept returning to one framing — *"the same κ-over-φ curve from
different angles"* — but no instrument ever looked at the three faces at once. The core
equation Q = φ/κ + ε ties them: ε_code is the compressible remainder of `+ ε`, and κ is
the denominator of `φ/κ`. A healthy runtime *compresses ε_code* (UNKNOWN% → 0, never
guessing) **without** letting κ (tool-count/entropy) grow to swamp the φ it unlocks.
Those two compressible terms could trade off invisibly if each is trended alone — ε
falling while κ balloons is a lie dressed as discipline.

This instrument is the synthesis: it **imports the three existing readers' low-level
functions** (single source of truth, never re-implements a measure — the `_load_rows` +
`compute_trend`/`trend` surfaces that each sibling already owns) and reports the joint
read:

  * `--trend` (`schema axiom-joint-trend/v1`) loads each series' verdict, then emits a
    **`joint`** verdict about the *relative* drift of the two compressible terms:
      - `compress-coherent`   ε_code improving while κ not-collapsing (healthy)
      - `compress-paradox`    ε_code improving WHILE κ worsens (the trade-off — the
                              UNKNOWN% fell only because the kit ballooned: a ketosis,
                              not a diet)
      - `kappa-and-eps-collapse`  both compressible terms drifting the wrong way (A2 alarm)
      - `self-bloat`          κ + ε stable while the runtime's own φ/κ worsens
      - `abstain`             any series below 2 samples (honest; no guessing)
    It never prescribes: the verdict is a read, and `--selftest` manufactures synthetic
    series to prove the fire logic, but it gates nothing.

The Goodhart safeguard is identical to its siblings: read-only, no append, no decision
path, no prescriptive consumer. It merely makes the *joint* trajectory visible — the
one thing each single-face trend structurally cannot see.

Modes:
  * `--trend`    (default) — print the full JSON joint read, exit 0 always.
  * `--check`    — report-only read: **silent** (exit 0) on a healthy joint verdict
    (`compress-coherent` / `stable` / `abstain`), and prints a compact `ALARM:` line + the
    JSON and exits 1 on the two alarm verdicts (`kappa-and-eps-collapse`, `compress-paradox`).
    The exit code is a *reporting* mechanism (so a cron delivery surfaces the alarm),
    NOT a gate on any action — nothing edits, prunes, or prescribes (the same contract
    as `a5_constraint_provenance.py --check`).
  * `--selftest` — prove the fire/abstain logic; exits non-zero on failure.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# source of truth: the three existing readers' low-level surfaces, imported — never
# re-implemented. (The `trend()` wrappers print-to-stdout and return exit codes, so we
# import the data functions they wrap, which return dicts.)
import epsilon_code_trend as eps  # noqa: E402
import kappa_proliferation_timeseries as kappa  # noqa: E402
import curiosity_kappa_trend as ckappa  # noqa: E402

SCHEMA = "axiom-joint-trend/v1"

# The joint verdicts that a report-only watchdog should surface. Everything else
# (`compress-coherent`, `stable`, `abstain`) is a healthy read and stays silent.
# This is a *reporting* classification, never a gate: nothing acts on it.
ALARM_VERDICTS = ("kappa-and-eps-collapse", "compress-paradox")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"
EPS_DB = DATA / "epsilon_code_trend.sqlite"
KAPPA_DB = DATA / "kappa_timeseries.sqlite"
CKAPPA_DB = DATA / "curiosity_kappa_trend.sqlite"


def _eps_verdict(db=EPS_DB):
    """ε_code UNKNOWN% verdict. `eps.trend(out_db)` returns a dict directly."""
    r = eps.trend(str(db))
    return r.get("verdict", "abstain"), r.get("samples", 0)


def _kappa_verdict(db=KAPPA_DB):
    """κ/Q verdict. Reuses the sibling's own `_load_rows` + `compute_trend` (single
    source of truth) rather than the print-to-stdout `trend()` wrapper."""
    rows = kappa._load_rows(str(db))  # noqa: SLF001  (deliberate source-of-truth import)
    tr = kappa.compute_trend(rows, metric="Q_eff")
    collapse = tr.get("collapse")
    n = tr.get("n", 0)
    if collapse is None:
        return "abstain", n
    return ("worsening" if collapse else "stable"), n


def _ckappa_verdict(db=CKAPPA_DB):
    """CURIOSITY self-bloat verdict. Reuses the sibling's `_load_rows` + `compute_trend`."""
    rows = ckappa._load_rows(str(db))  # noqa: SLF001
    tr = ckappa.compute_trend(rows)
    worsening = tr.get("worsening")
    n = tr.get("n", 0)
    if worsening is None:
        return "abstain", n
    return ("worsening" if worsening else "stable"), n


def _resolve_joint(eps_v, eps_n, kap_v, kap_n, ckap_v, ckap_n):
    """Relative drift of the two compressible terms (ε_code vs κ), with self-κ as the
    tertiary signal. Never guesses — abstains where any series is too sparse."""
    sparse = [name for name, n in (("epsilon_code", eps_n), ("kappa", kap_n),
                                   ("curiosity_kappa", ckap_n)) if n < 2]
    if sparse:
        return "abstain", {"sparse": sparse}

    eps_improving = eps_v == "improving"
    eps_worsening = eps_v == "worsening"
    kap_worsening = kap_v == "worsening"
    ckap_worsening = ckap_v == "worsening"

    if eps_worsening and kap_worsening:
        verdict = "kappa-and-eps-collapse"   # both compressible terms drifting — A2 alarm
    elif eps_improving and kap_worsening:
        verdict = "compress-paradox"         # UNKNOWN% fell only while κ ballooned — ketosis
    elif not eps_worsening and not kap_worsening and ckap_worsening:
        verdict = "self-bloat"               # the runtime's own φ/κ is the only worsening face
    elif eps_improving and not kap_worsening:
        verdict = "compress-coherent"        # ε compressed, κ held — healthy
    else:
        verdict = "stable"

    return verdict, {
        "epsilon_code": eps_v,
        "kappa": kap_v,
        "curiosity_kappa": ckap_v,
    }


def trend(eps_db=EPS_DB, kap_db=KAPPA_DB, ckap_db=CKAPPA_DB):
    eps_v, eps_n = _eps_verdict(eps_db)
    kap_v, kap_n = _kappa_verdict(kap_db)
    ckap_v, ckap_n = _ckappa_verdict(ckap_db)
    verdict, detail = _resolve_joint(eps_v, eps_n, kap_v, kap_n, ckap_v, ckap_n)
    return {
        "schema": SCHEMA,
        "samples": {
            "epsilon_code": eps_n,
            "kappa": kap_n,
            "curiosity_kappa": ckap_n,
        },
        "verdicts": {
            "epsilon_code": eps_v,
            "kappa": kap_v,
            "curiosity_kappa": ckap_v,
        },
        "joint_verdict": verdict,
        "detail": detail,
    }


def _selftest():
    ok = True

    # 1. the three readers are importable and expose the expected low-level surfaces
    for mod, attrs in (
        (eps, ("trend",)),
        (kappa, ("_load_rows", "compute_trend")),
        (ckappa, ("_load_rows", "compute_trend")),
    ):
        for a in attrs:
            ok &= hasattr(mod, a)
            if not hasattr(mod, a):
                print("  selftest[import %s.%s] FAIL" % (mod.__name__, a))

    # 2. pure joint-resolution logic (the predicate is DB-independent)
    ok &= _resolve_joint("improving", 3, "stable", 3, "stable", 3)[0] == "compress-coherent"
    ok &= _resolve_joint("improving", 3, "worsening", 3, "stable", 3)[0] == "compress-paradox"
    ok &= _resolve_joint("worsening", 3, "worsening", 3, "stable", 3)[0] == "kappa-and-eps-collapse"
    ok &= _resolve_joint("stable", 3, "stable", 3, "worsening", 3)[0] == "self-bloat"
    ok &= _resolve_joint("worsening", 3, "stable", 3, "stable", 3)[0] == "stable"
    ok &= _resolve_joint("stable", 3, "stable", 3, "stable", 3)[0] == "stable"
    v, d = _resolve_joint("improving", 3, "stable", 1, "stable", 3)
    ok &= v == "abstain" and "kappa" in d["sparse"]
    v, d = _resolve_joint("improving", 1, "stable", 1, "stable", 3)
    ok &= v == "abstain" and "epsilon_code" in d["sparse"] and "kappa" in d["sparse"]

    # 3. the ALARM classification (the --check report contract): only the two dangerous
    #    verdicts are surface-worthy; everything healthy stays silent.
    ok &= all(v in ALARM_VERDICTS for v in
              ("kappa-and-eps-collapse", "compress-paradox"))
    ok &= all(v not in ALARM_VERDICTS for v in
              ("compress-coherent", "stable", "abstain", "self-bloat"))

    # 4. real-source verdicts: run the actual imported readers against the live DBs and
    #    confirm a joint verdict is produced (never asserting a particular value, since
    #    the live shape may legitimately be anything — the point is it runs end-to-end).
    try:
        out = trend()
        ok &= out["schema"] == SCHEMA
        ok &= isinstance(out["joint_verdict"], str)
    except Exception as e:  # noqa: BLE001
        print("  selftest[live-joint     ] FAIL (%s)" % e)
        ok = False

    print("  selftest[import            ] %s" % ("PASS" if (hasattr(kappa, "_load_rows") and hasattr(kappa, "compute_trend") and hasattr(ckappa, "_load_rows") and hasattr(ckappa, "compute_trend") and hasattr(eps, "trend")) else "FAIL"))
    print("  selftest[coherent          ] %s  (ε↑ κ= selfκ= → compress-coherent)" % ("PASS" if _resolve_joint("improving", 3, "stable", 3, "stable", 3)[0] == "compress-coherent" else "FAIL"))
    print("  selftest[paradox           ] %s  (ε↑ κ↓ → compress-paradox)" % ("PASS" if _resolve_joint("improving", 3, "worsening", 3, "stable", 3)[0] == "compress-paradox" else "FAIL"))
    print("  selftest[double-collapse   ] %s  (ε↓ κ↓ → kappa-and-eps-collapse)" % ("PASS" if _resolve_joint("worsening", 3, "worsening", 3, "stable", 3)[0] == "kappa-and-eps-collapse" else "FAIL"))
    print("  selftest[self-bloat        ] %s  (selfκ↓ only → self-bloat)" % ("PASS" if _resolve_joint("stable", 3, "stable", 3, "worsening", 3)[0] == "self-bloat" else "FAIL"))
    print("  selftest[stable            ] %s  (ε↓ only / all flat → stable)" % ("PASS" if (_resolve_joint("worsening", 3, "stable", 3, "stable", 3)[0] == "stable" and _resolve_joint("stable", 3, "stable", 3, "stable", 3)[0] == "stable") else "FAIL"))
    print("  selftest[abstain-sparse    ] %s  (κ n<2 → abstain lists κ)" % ("PASS" if _resolve_joint("improving", 3, "stable", 1, "stable", 3)[0] == "abstain" else "FAIL"))
    return ok


def main():
    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    out = trend()
    if "--check" in sys.argv:
        verdict = out["joint_verdict"]
        if verdict in ALARM_VERDICTS:
            print("ALARM: %s (ε_code=%s κ=%s self-κ=%s)"
                  % (verdict, out["verdicts"]["epsilon_code"],
                     out["verdicts"]["kappa"], out["verdicts"]["curiosity_kappa"]))
            print(json.dumps(out, indent=2))
            sys.exit(1)
        # Healthy (compress-coherent / stable / abstain): silent — nothing to deliver.
        sys.exit(0)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()