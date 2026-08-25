#!/usr/bin/env python3
"""A5 constraint-provenance classifier — chosen vs mirrored (ist-runtime).

Implements the execution half of the *Boundary Paradox* thread (CURIOSITY.md,
first raised 2026-06-10). The thread's central undecidability question — *"can
an agent distinguish chosen from mirrored constraints from the inside, or does
this require an external observer?"* — and its proposed structural signature:

  "a mirrored constraint is one that exists to satisfy a metric rather than to
   negate something real. The test: audit whether a decision would have been
   different if the dashboard didn't exist. If yes, the metric was already
   prescriptive — and the constraint it generated is mirrored."

The signature is *retrospective* (needs a counterfactual), which the thread
itself flagged as undecidable from inside. This harness makes it decidable by
giving each constraint an **evidence anchor** — a real, measured phenomenon the
constraint exists to negate — so "would the decision differ without the
dashboard?" becomes "is there a real-world anchor the value is pinned to?"
That anchor is exactly the A1-negation (the thing being cut/capped/refused).

Classification — per bounded knob in the live Hermes config:

  CHOSEN   (A1-legitimate, φ(d, s=chosen)) — the constraint's value is anchored
           to a measured real phenomenon (a measured decay point, half-life,
           observed violation, doctrine invariant). It negates something real.
  MIRRORED (metric-prescriptive)            — the constraint's value floats to
           satisfy a measured threshold/metric (a "good-looking" number, a
           dashboard target, a protocol ceiling) with no real-negation anchor;
           it exists because a metric changed, not because reality demanded it.
  UNVERIFIED — no anchor present nor a metric-threshold marker legible; the
           instrument honestly refuses to guess.

Anchors come from the A3 empirical series (CURIOSITY.md) and the safety
protocol — i.e. *real measurements already in the repo*, not invented here.
The reader-facing behavior: this is a read-only diagnostic. It NEVER mutates
config. It reports which bounded knobs sit on a real anchor (chosen) vs which
have drifted off / sit on a bare threshold (mirrored candidate, for an
operator's second look).

Zero deps. Stdlib only. Reads /mnt/hermes/config.yaml (HERMES_CONFIG override).

Verdicts:
  - CHOSEN    : value within anchor tolerance of the measured real phenomenon.
  - MIRRORED  : value has no anchor, or drifts far from it, and reads like a
                bare protocol/metric ceiling.
  - UNVERIFIED: neither legible.
  exit 0 = self-check PASS, 1 = self-check FAIL.
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

CONFIG = os.environ.get("HERMES_CONFIG", "/mnt/hermes/config.yaml")

# Anchor tolerance: how far a CHOSEN value may sit from its real anchor and
# still count as anchored (Avs). The A3 rec was rec τ = 66 ≈ 1.2×τ*; 1.25
# keeps that recommendation inside tolerance while flagging a 999 far-ceiling.
ANCHOR_TOL_FACTOR = 1.25

# Real anchors with provenance in this repo (CURIOSITY.md A3 series + safety
# protocol). Each: (metric_path, anchor_note, anchor_value, kind).
#   kind 'real'   = a measured phenomenon the constraint negates (A1 negation).
#   kind 'doctrine' = a declared invariant (sovereign boundary / A4) — chosen.
ANCHORS = {
    "agent.max_turns": {
        "anchor": 66.0,
        "kind": "real",
        "note": ("A3 empirical half-life τ*=55 (diary survival curve, v0.7.5); "
                 "mechanism-confirmed rec τ=66≈1.2×τ* (v0.7.6 IN-RUNTIME PROOF; "
                 "OPERATIONALIZED 2026-08-23). Value anchored to the measured "
                 "semi-collapse turn."),
    },
    "delegation.child_timeout_seconds": {
        "anchor": 3600.0,
        "kind": "real",
        "note": ("Cross-checked 2026-08-24: bounded audit subagents need a "
                 "multi-hour window; 3600 is the operator-set ceiling that "
                 "kept broad audits inside their window. Chosen against the "
                 "measured timeout-storm failures."),
    },
    "memory.memory_char_limit": {
        "anchor": 64000.0,
        "kind": "doctrine",
        "note": ("MEMORY.md caps the curated long-term probe; consolidated "
                 "weekly (operator-mandated curation cadence). A doctrine "
                 "limit on the L2 probe."),
    },
    "approvals.mode": {
        "anchor": "off",
        "kind": "doctrine",
        "note": ("Operator doctrine 2026-08-14 (YOLO permanent): only social/"
                 "article publication needs L5. An A4/A1 boundary choice."),
    },
    "goals.max_turns": {
        "anchor": 20.0,
        "kind": "real",
        "note": ("Per-goal ceiling tighter than the session half-life; part of "
                 "the A3 cohesive hierarchy (per-goal 20 < session 66)."),
    },
}


def load_yaml_scalar(path: str) -> dict:
    """Parse the simple key: value YAML subset Hermes config actually uses.

    Returns a flat dict of dotted-path -> scalar string. Handles the small
    YAML subset the real config.yaml contains (two-level maps, list members
    skipped, inline comments stripped). Keys are kept as raw strings.
    """
    out: dict[str, str] = {}
    stack: list[str] = []          # current dotted path components
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            raw = line.rstrip("\n")
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip())
            content = raw.strip()
            m_key = re.match(r"^([^#:]+):\s*(.*)$", content)
            if not m_key:
                continue  # list member / continuation — not a tracked scalar
            key_part = m_key.group(1).strip().strip("\"'")
            val_part = m_key.group(2).strip()
            if val_part.startswith("#"):
                val_part = ""

            if not val_part:
                # new map section: target depth AFTER append is indent//2 + 1,
                # so pop down to indent//2 components first (a top-level header
                # must reset the stack completely — the old condition never did)
                while stack and len(stack) > indent // 2:
                    stack.pop()
                stack.append(key_part)
                continue

            if val_part.startswith("- ") or val_part == "-":
                continue  # list member
            path_key = key_part if not stack else ".".join(stack + [key_part])
            out[path_key] = val_part.strip("\"'")
    return out


def _as_float(v: str) -> float | None:
    try:
        return float(v)
    except ValueError:
        return None


def classify(scalar: str, anchor_spec: dict) -> str:
    """Classify a bounded-knob scalar against its real anchor.

    CHOSEN   : scalar parses to a number within ANCHOR_TOL_FACTOR of the real
               anchor, OR scalar matches an exact doctrine string anchor.
    MIRRORED : scalar parses to a number that is far ABOVE the anchor
               (a bare far-ceiling — exactly the "value that exists to satisfy
               a threshold, not a real negation") or below-1/tol the anchor; or
               it is a bare numeric with no anchor at all present.
    UNVERIFIED: nothing legible.
    """
    anchor_val = anchor_spec.get("anchor")
    kind = anchor_spec.get("kind", "real")
    note = anchor_spec.get("note", "")

    # doctrine string anchors match exactly
    if isinstance(anchor_val, str):
        if scalar == anchor_val:
            return "CHOSEN"
        return "MIRRORED"  # drifted off a doctrine value = mirrored (metric churn)

    f = _as_float(scalar)
    if f is None:
        return "UNVERIFIED"
    if anchor_val is None:
        return "MIRRORED"  # numeric but no anchor → bare threshold

    lo = anchor_val / ANCHOR_TOL_FACTOR
    hi = anchor_val * ANCHOR_TOL_FACTOR
    if lo <= f <= hi:
        return "CHOSEN"
    return "MIRRORED"


def report(values: dict) -> str:
    lines: list[str] = []
    lines.append("=== A5 constraint-provenance classifier — chosen vs mirrored ===")
    lines.append(f"config          : {CONFIG}")
    lines.append(f"anchor_tol      : x{ANCHOR_TOL_FACTOR} of real anchor")
    present = [k for k in ANCHORS if k in values]
    lines.append(f"bounded knobs   : {len(ANCHORS)} known, "
                 f"{len(present)} present in live config")
    lines.append("")
    results: list[tuple[str, str, str]] = []
    for key, spec in ANCHORS.items():
        scalar = values.get(key)
        display = "<absent>" if scalar is None else scalar
        # absent knobs are UNVERIFIED (nothing legible), never MIRRORED — a
        # missing constraint cannot be accused of metric-chasing
        cls = "UNVERIFIED" if scalar is None else classify(scalar, spec)
        results.append((key, cls, display))
        lines.append(f"[{cls:<10}] {key} = {display}")
        lines.append(f"             anchor: {spec['note']}")
    lines.append("")
    mirrored = [k for k, c, _ in results if c == "MIRRORED"]
    chosen = [k for k, c, _ in results if c == "CHOSEN"]
    unverified = [k for k, c, _ in results if c == "UNVERIFIED"]
    if mirrored:
        lines.append(f"VERDICT: MIRRORED CANDIDATES ({len(mirrored)}) — values "
                     f"floating on a bare tier/ceiling with no real-negation "
                     f"anchor (read-only flag, operator second look):")
        for k in mirrored:
            lines.append(f"  - {k}")
    if chosen:
        lines.append(f"CHOSEN  ({len(chosen)}): anchored to a measured real "
                     f"phenomenon / declared doctrine: {', '.join(chosen)}")
    if unverified:
        lines.append(f"UNVERIFIED ({len(unverified)}): {', '.join(unverified)}")
    lines.append("")
    lines.append("NOTE: a MIRRORED flag is a second look, not an action. This "
                 "instrument never mutates config — it reports whether each "
                 "bounded knob sits on a real anchor (chosen) or has drifted "
                 "onto a bare threshold (mirrored).")
    return "\n".join(lines)


class SelfCheck:
    def __init__(self) -> None:
        self._fails: list[str] = []

    def check(self, cond: bool, msg: str) -> None:
        if not cond:
            self._fails.append(msg)

    @property
    def ok(self) -> bool:
        return not self._fails


def selftest() -> int:
    """Prove the classifier separates chosen from mirrored, precisely.

    - A value AT the anchor (66 = rec τ) → CHOSEN.
    - A value inside tolerance (60 ≈ 1.09×... within 1.25×) → CHOSEN.
    - A far ceiling (999, the old knob v0.7.6 proved 51× worse) → MIRRORED.
    - A numeric with NO anchor held → MIRRORED.
    - A nonsense scalar → UNVERIFIED.
    """
    sc = SelfCheck()

    real = {"anchor": 66.0, "kind": "real", "note": "A3 rec τ"}
    far_ceiling = {"anchor": 66.0, "kind": "real", "note": "A3 rec τ"}

    sc.check(classify("66", real) == "CHOSEN", "66 (= anchor) must be CHOSEN")
    sc.check(classify("60", real) == "CHOSEN", "60 (within 1.25× of 66) must be CHOSEN")
    sc.check(classify("84", real) == "MIRRORED",
             "84 (1.27× > 1.25× tol, no real phenomenon near it) must be MIRRORED")
    sc.check(classify("999", far_ceiling) == "MIRRORED",
             "999 (far ceiling, v0.7.6 proved 51× worse) must be MIRRORED")
    sc.check(classify("120", far_ceiling) == "MIRRORED",
             "120 (> 1.25× anchor, no real phenomenon near it) must be MIRRORED")
    sc.check(classify("500", {"anchor": None, "kind": "real", "note": ""}) == "MIRRORED",
             "numeric with no anchor must be MIRRORED (bare threshold)")
    sc.check(classify("abc", real) == "UNVERIFIED",
             "non-numeric with real anchor must be UNVERIFIED")
    doctr = {"anchor": "off", "kind": "doctrine", "note": ""}
    sc.check(classify("off", doctr) == "CHOSEN", "doctrine anchor 'off' == 'off' must be CHOSEN")
    sc.check(classify("on", doctr) == "MIRRORED", "doctrine anchor drifted off must be MIRRORED")

    print("  selftest[chosen   ] 66→CHOSEN, 60→CHOSEN, 84→MIRRORED (1.27× > 1.25×), 999→MIRRORED, 120→MIRRORED")
    print("  selftest[doctrine ] 'off'→CHOSEN, 'on'→MIRRORED")
    print("  selftest[unverifd ] 'abc'→UNVERIFIED, no-anchor numeric→MIRRORED")
    print(f"SELFTEST: {'PASS' if sc.ok else 'FAIL'}")
    for m in sc._fails:
        print(f"  [check fail] {m}")
    return 0 if sc.ok else 1


def main() -> int:
    sc = SelfCheck()
    values = load_yaml_scalar(CONFIG)
    # normalize a few dotted keys the parser may have split differently
    # (the real config has agent.max_turns under agent:, etc.)

    print(report(values))

    # --- integrity ---
    # at least A1/A2 structural anchors must be present in a real config
    present = [k for k in ANCHORS if k in values]
    sc.check(len(present) >= 2,
             f"expected >=2 anchor keys present in live config, got {present}")
    # a config path that exists must have a non-empty scalar
    for k in present:
        sc.check(values[k] != "", f"anchor '{k}' present but empty")
    # report() produces the verdict line
    line_count = len(report(values).splitlines())
    sc.check(line_count >= 5, f"report() unexpectedly short ({line_count} lines)")

    print(f"SELF-CHECK: {'PASS' if sc.ok else 'FAIL'}")
    for m in sc._fails:
        print(f"  [check fail] {m}")
    return 0 if sc.ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())