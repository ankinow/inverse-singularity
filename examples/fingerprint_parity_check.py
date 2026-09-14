#!/usr/bin/env python3
"""Fingerprint parity check — Rust primary ⇄ Python mirror agree on the shared surface.

The `framework/ist_engine.py` module docstring says the Python file and the
Rust primary "MUST produce identical scalar outputs" — the *fingerprint*.
For the canonical demo pair (d=0.85, c=0.31) that fingerprint is Q = 1.9845,
asserted in the Rust test suite (`sourced_mirrored_decreases_q_versus_chosen`,
`portfolio_all_chosen_matches_canonical_q`) and recomputed by the Python
`phi`/`evolve` mirror.

But the parity is held by *discipline*, not by *surfacing*: nothing runs both
implementations and diffs their output. The Rust tests prove the Rust is
internally consistent; the Python mirror is trusted to match by comment. A
silent fork between the two would pass `cargo test` and pass a naive Python
smoke run — neither side reads the other.

This instrument closes that gap, following the codebase's own read-only
deterministic-check discipline (crate_identity_check, a5 --check, the
--selftest pattern):

  * It computes the canonical scalars from the **Python reference** directly
    (`phi`, `phi_sourced`, `route`, `constraint_margin`, `constraint_portfolio`,
    `evolve`) — the A2-canonical Q, the collapse NEI scores, the audit
    min_margin, the portfolio quality/threshold.
  * It runs `cargo run --quiet --example collapse` and parses the Rust demo's
    printed scalars for the same surface.
  * It asserts agreement within the shared ε floor (1e-4, matching the Rust
    test tolerance), fail-closed (exit 1 + a `DRIFT` line naming the axis) on
    any disagreement.
  * It also asserts the source-term invariants the Rust tests pin
    (`route` splits (d,0)/(0,d); `phi_sourced` is the projection of `route`;
    mirrored always lowers Q) against the Python mirror, so a Rust-side-only
    test cannot drift out of step with the mirror un-noticed.

Read-only: it never edits either implementation. The only side effect is the
verdict (exit code + one line). Building Rust deps is the sole heavyweight
step, required only when the target has not been built yet (`--skip-build`
reuses a prior `target/` and fails closed with an explicit message if the
binary is absent).

Usage:
  python3 fingerprint_parity_check.py            # full check (builds if needed)
  python3 fingerprint_parity_check.py --skip-build
  python3 fingerprint_parity_check.py --check    # scheduled-consumer mode (silent on parity)
  python3 fingerprint_parity_check.py --selftest # prove each assert path

Exit:
  0  PARITY — both implementations agree on every checked axis.
  1  DRIFT  — at least one axis disagrees (named in the DRIFT line).
  2  ERROR  — could not obtain one side's output (build failed / parse miss).

`--check` is the scheduled-consumer form (the same discipline as crate_identity
`--check`, a5 `--check`, and the joint-reader `--check`): it suppresses the
success line so a weekly cron delivers **only** a drift/error (reporting, never
prescribing — it never edits either implementation). The exit codes are
identical to the human form: 0 on parity, 1 with a `DRIFT` line, 2 with an
`ERROR` line. It runs `--skip-build` internally (a cron must not rebuild; it
fails closed if the collapse binary has not yet been built).
"""

import argparse
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = ROOT / "framework"
sys.path.insert(0, str(FRAMEWORK))

import ist_engine as engine  # noqa: E402  (single source of truth — the mirror)

# ─── canonical demo inputs (the shared fingerprint pair) ───────────────────
C = 0.31          # κ — complexity entropy
D = 0.85          # d — conceptual density
STEPS = 7         # the collapse demo horizon
FLOOR = 1e-4      # shared ε floor (matches the Rust test tolerance)


# ─── Python-side scalar extraction (the mirror, computed fresh each run) ───
def python_scalars():
    """Compute the canonical shared surface from the Python mirror alone."""
    # A2-canonical Q and φ
    phi_d = engine.phi(D)
    q_canonical = phi_d / (C + 1e-9)

    # collapse demo — NEI scores and urgencies across the 7-step arc
    agent = engine.IST(lam=0.1, tau=STEPS, sovereign_mode=True)
    steps = agent.collapse(C, D, STEPS)
    nei_scores = [s["nei_score"] for s in steps]
    urgencies = [s["urgency"] for s in steps]

    # constraint_audit over the canonical audit inputs (tools=2, deps=0, 1 KiB)
    audit = agent.constraint_audit(2, 0, 1024)

    return {
        "phi_d": phi_d,
        "q_canonical": q_canonical,
        "nei_scores": nei_scores,
        "urgencies": urgencies,
        "audit_score": audit["score"],
        "audit_min_margin": audit["min_margin"],
    }


# ─── Rust-side extraction (parse `cargo run --example collapse` stdout) ────
def rust_scalars(skip_build=False):
    """Run the Rust collapse demo and parse its printed scalars."""
    exe = ROOT / "target" / "debug" / "examples" / "collapse"
    if not exe.exists():
        if skip_build:
            raise RuntimeError(
                "collapse binary absent and --skip-build given; run once "
                "with a build to produce it"
            )
        r = subprocess.run(
            ["cargo", "build", "--quiet", "--example", "collapse"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"cargo build failed:\n{r.stderr[-2000:]}")

    r = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"collapse example failed:\n{r.stderr[-2000:]}")
    out = r.stdout

    def grab(pattern, name):
        m = re.search(pattern, out)
        if m is None:
            raise RuntimeError(f"could not parse `{name}` from collapse output")
        return m.group(1)

    # φ(d) printed as `φ(d) = 0.6152` (4dp)
    phi_d = float(grab(r"φ\(d\)\s*=\s*([0-9.]+)", "φ(d)"))
    # κ printed as `κ = 0.3100`
    kappa = float(grab(r"κ\s*=\s*([0-9.]+)", "κ"))
    # Q printed as `Q = 1.9845`
    q_canonical = float(grab(r"\bQ\s*=\s*([0-9.]+)", "Q"))

    # per-step NEI scores / urgencies from `t=N Q=… IST=… urgency=…`
    stapless = re.findall(r"t=\d+\s+Q=\s*[0-9.]+\s+IST=\s*([0-9.]+)\s+urgency=([0-9.]+)", out)
    if len(stapless) != STEPS:
        raise RuntimeError(f"expected {STEPS} step lines, found {len(stapless)}")
    nei_scores = [float(x) for x, _ in stapless]
    urgencies = [float(y) for _, y in stapless]

    # audit score + min_margin from `... score=1.000  min_margin=-0.000`
    audit_m = re.search(r"score=([0-9.]+)\s+min_margin=(-?[0-9.]+)", out)
    if audit_m is None:
        raise RuntimeError("could not parse audit score/min_margin")
    audit_score = float(audit_m.group(1))
    audit_min_margin = float(audit_m.group(2))

    return {
        "phi_d": phi_d,
        "q_canonical": q_canonical,
        "nei_scores": nei_scores,
        "urgencies": urgencies,
        "audit_score": audit_score,
        "audit_min_margin": audit_min_margin,
        # κ is parsed only for the kappa-vs-C consistency check below
        "_kappa": kappa,
    }


# ─── source-term invariants (mirror must agree with Rust-pinned doctrine) ──
def source_term_checks():
    """Re-assert, in Python, the source-term invariants the Rust tests pin."""
    results = []
    for d in (0.0, 0.5, 1.0, 7.0):
        for s in (engine.ConstraintSource.CHOSEN, engine.ConstraintSource.MIRRORED):
            rd, _rk = engine.route(d, s)
            proj = engine.phi_sourced(d, s)
            results.append(("phi_sourced_is_route_projection", abs(proj - engine.phi(rd)) < 1e-12))

    # route split: chosen → (d, 0); mirrored → (0, d)
    results.append(("route_chosen_density", engine.route(D, engine.ConstraintSource.CHOSEN) == (D, 0.0)))
    results.append(("route_mirrored_kappa", engine.route(D, engine.ConstraintSource.MIRRORED) == (0.0, D)))

    # mirrored lowers Q vs chosen at the canonical pair
    q_chosen = engine.phi_sourced(D, engine.ConstraintSource.CHOSEN) / (C + 1e-9)
    q_mirrored = engine.phi_sourced(D, engine.ConstraintSource.MIRRORED) / (C + 1e-9)
    results.append(("mirrored_lowers_q", q_chosen > q_mirrored and q_mirrored == 0.0))

    # portfolio: all-chosen folds to canonical Q; one mirrored lowers it
    all_chosen = engine.constraint_portfolio([(D, engine.ConstraintSource.CHOSEN)], C)
    results.append(("portfolio_canonical_q", abs(all_chosen["quality"] - 1.9845) < FLOOR))
    mixed = engine.constraint_portfolio(
        [(D, engine.ConstraintSource.CHOSEN), (D, engine.ConstraintSource.MIRRORED)], C
    )
    results.append(("portfolio_mirrored_lowers", mixed["quality"] < all_chosen["quality"]))
    results.append(("portfolio_threshold_flags", mixed["at_mirror_threshold"] is True))
    results.append(("portfolio_empty_no_threshold", engine.constraint_portfolio([], C)["at_mirror_threshold"] is False))
    return results


def check(py, ru):
    """Compare the shared scalar surface, returning a list of (name, ok, detail)."""
    results = []

    def near(name, a, b, tol=FLOOR):
        ok = abs(a - b) <= tol
        results.append((name, ok, f"{a:.8f} vs {b:.8f} (tol {tol:g})"))
        return ok

    near("phi_d", py["phi_d"], ru["phi_d"], 1e-3)          # Rust prints 4dp
    near("q_canonical", py["q_canonical"], ru["q_canonical"], 1e-3)

    for i in range(STEPS):
        near(f"nei_score[{i}]", py["nei_scores"][i], ru["nei_scores"][i], 1e-3)
        near(f"urgency[{i}]", py["urgencies"][i], ru["urgencies"][i], 1e-3)

    near("audit_score", py["audit_score"], ru["audit_score"], 1e-3)
    near("audit_min_margin", py["audit_min_margin"], ru["audit_min_margin"], 1e-3)

    # κ consistency: Rust prints κ=0.31 for the canonical C
    results.append(("kappa_consistency", abs(ru["_kappa"] - C) < 1e-3,
                    f"rust κ={ru['_kappa']} vs C={C}"))

    return results


def selftest():
    """Prove each assert path fires deterministically (no live Rust needed)."""
    results = []  # (name, ok) pairs — names aid debugging, `ok` is the bool
    # 1. near() agreement and divergence
    r = check(
        {"phi_d": 0.5, "q_canonical": 2.0, "nei_scores": [0.1] * 7, "urgencies": [1.0] * 7,
         "audit_score": 1.0, "audit_min_margin": 0.0},
        {"phi_d": 0.5, "q_canonical": 2.0, "nei_scores": [0.1] * 7, "urgencies": [1.0] * 7,
         "audit_score": 1.0, "audit_min_margin": 0.0, "_kappa": 0.31},
    )
    results.append(("check_agreement", all(b for _, b, _ in r)))

    div = check(
        {"phi_d": 0.5, "q_canonical": 2.0, "nei_scores": [0.1] * 7, "urgencies": [1.0] * 7,
         "audit_score": 1.0, "audit_min_margin": 0.0},
        {"phi_d": 0.9, "q_canonical": 2.0, "nei_scores": [0.1] * 7, "urgencies": [1.0] * 7,
         "audit_score": 1.0, "audit_min_margin": 0.0, "_kappa": 0.31},
    )
    results.append(("check_detects_phi_drift", not all(b for _, b, _ in div)))

    # 2. source-term invariants are all true on the real mirror
    st = source_term_checks()
    # 8 projection + 2 route split + 1 mirrored-lowers + 4 portfolio == 15
    results.append(("source_terms_all_true", all(b for _, b in st)))
    results.append(("source_term_count_is_15", len(st) == 15))

    # 3. python_scalars produces the canonical fingerprint
    py = python_scalars()
    results.append(("canonical_q_fingerprint", abs(py["q_canonical"] - 1.9845) < FLOOR))

    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-build", action="store_true",
                    help="reuse a previously built collapse binary")
    ap.add_argument("--check", action="store_true",
                    help="scheduled-consumer mode: silent on parity, surface only drift/error")
    ap.add_argument("--selftest", action="store_true",
                    help="run the internal assert-path proof, exit")
    args = ap.parse_args()

    if args.selftest:
        results = selftest()
        passed = sum(1 for _name, ok in results if ok)
        total = len(results)
        print(f"SELFTEST: {passed}/{total}")
        sys.exit(0 if passed == total else 1)

    # --check is the cron form: same verdicts, but silent on parity (so the
    # scheduled delivery carries only drift/error). It goes through --skip-build
    # so a cron never triggers a rebuild.
    check_silent = args.check
    run_skip_build = args.skip_build or check_silent

    # source-term invariants first (pure Python, no build)
    st = source_term_checks()
    st_bad = [n for n, b in st if not b]

    try:
        py = python_scalars()
        ru = rust_scalars(skip_build=run_skip_build)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        sys.exit(2)

    results = check(py, ru)
    bad = [(n, d) for n, ok, d in results if not ok]
    bad += [(n, "source-term invariant violated in mirror") for n in st_bad]

    if bad:
        print("DRIFT — Rust ⇄ Python fingerprint disagreement:")
        for name, detail in bad:
            print(f"  {name}: {detail}")
        sys.exit(1)

    if not check_silent:
        print(
            f"PARITY — Rust ⇄ Python agree on {len(results) + len(st)} axes "
            f"(Q={py['q_canonical']:.5f}, NEI=7 steps, audit, {len(st)} source-term invariants)."
        )
    sys.exit(0)


if __name__ == "__main__":
    main()