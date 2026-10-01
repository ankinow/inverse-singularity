#!/usr/bin/env python3
"""Framework epsilon system module — computes the sovereignty term (ε_system) and ε_code from the diary.

This module provides the core parsing and computation logic for the ε-thread,
separated from the probe and trend instruments for reuse.

D34 (2026-10-01) — THE DRIFT THIS MODULE COULD NOT SEE BECAUSE IT RE-IMPLEMENTED
THE MEASURE. This file was an independent copy of the probe's tally logic, and
the copy carried two DOUBLE-ESCAPED regexes that match nothing in the real
corpus:

    _RE_TYPED = r"^⊗S:(mutation|observe)\\b"   # literal backslash-b
    file glob  = r"^\\d{4}-\\d{2}-\\d{2}\\.md$"  # literal backslash-d

Consequence, measured on the live diary: `parse_dir()` returned every counter
at ZERO, so the module printed

    ε_code   = 0.0000
    ε_system = 0.0000
    VERDICT: NO-EPSILON (claimed-perfect; A4-questionable: could-not-have-done-otherwise)

while the canonical `examples/a6_epsilon_probe.py` — on the SAME directory —
reported 16,122 tool lines, ε_code 0.0947, ε_system 0.0044, SOVEREIGN-CODE.
The failure is not a wrong number, it is the *opposite axiom*: this module
reported the A4-collapse reading (ε=0 ⇒ the system could not have done
otherwise) for a system that is demonstrably recording. A duplicated measure
is an unmonitored measure — the same class as the producer↔vendored fork the
ε-probe already guards with `--synccheck` (v0.8.19), except here nothing
guarded it at all.

The fix is structural, not cosmetic: this module no longer *implements* the
tally, it *delegates* to the single source of truth. `examples/a6_epsilon_probe.py`
owns `parse_dir` / `compute` / `verdict` and the canonical regexes; the framework
re-exports them. A drift is now impossible in the direction that mattered,
because there is only one copy left to drift.

This mirrors the discipline `scripts/audit_writer_attribution.py` uses in the
raw-vault (it IMPORTS `audit_id_collision.py` rather than re-parsing frontmatter,
so the causality count cannot lie) and the discipline `axiom_joint_trend.py`
uses across its seven faces (imports each sibling's surface; zero
re-implementation of any measure).

Functions (all re-exported from the probe — see the module docstring there):
    parse_dir(diary_dir) -> dict
        Tally, across all diary files, the ε-relevant counts (canonical regexes).
    compute(tally) -> tuple[float, float]
        Returns (ε_code, ε_system) from the tally.
    verdict(eps_code, eps_system) -> str
        Returns the verdict string based on ε_code and ε_system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Tuple

_EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
if str(_EXAMPLES) not in sys.path:
    sys.path.insert(0, str(_EXAMPLES))

# Single source of truth. A fallback that silently re-implements the tally would
# restore exactly the defect this release closes, so failure is loud instead.
try:
    import a6_epsilon_probe as _probe
except ImportError as _exc:  # pragma: no cover - structural, not behavioural
    raise ImportError(
        "framework/epsilon_system.py requires examples/a6_epsilon_probe.py "
        f"({_EXAMPLES}); refusing to re-implement the ε tally. ({_exc})"
    ) from _exc

# Canonical tool families (matches a4_action_typing doctrine §2 + producer's
# action_typing.py `AMBIGUOUS_TOOLS`). Re-exported so existing importers of
# these names keep working; the VALUES come from the probe, never from here.
MUTATION_TOOLS = _probe.MUTATION_TOOLS
OBSERVE_TOOLS = _probe.OBSERVE_TOOLS
AMBIGUOUS_TOOLS = _probe.AMBIGUOUS_TOOLS
# honesty / decision family = the *chosen* residue (ε_system)
HONESTY = _probe.HONESTY

_RE_TOOL = _probe._RE_TOOL
_RE_TYPED = _probe._RE_TYPED

parse_dir = _probe.parse_dir
compute = _probe.compute
verdict = _probe.verdict


def _selftest() -> int:
    """D34 guard: the framework tally must EQUAL the canonical probe tally.

    The pre-fix module returned all zeros. Pinning equality is the property
    that makes the delegation observable: a future re-implementation (or a
    probe rename that this shim silently absorbs) fails here instead of
    quietly reverting to a self-report.

    Also pins the negative control: the double-escaped patterns must still
    match nothing, so this test would catch a re-introduction of the defect
    even if the delegation were removed.
    """
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  selftest[{name:26s}] {'PASS' if cond else 'FAIL'}  {note}")

    diary = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")

    # 1. the defect's own signature, pinned
    check("typed-regex-live", _RE_TYPED.findall("⊗S:mutation") == ["mutation"],
          f"_RE_TYPED = {_RE_TYPED.pattern!r}")
    check("file-regex-live",
          bool(re.match(r"^\d{4}-\d{2}-\d{2}\.md$", "2026-10-01.md")),
          "dated-diary glob matches a real filename")
    check("dead-patterns-stay-dead",
          _RE_TYPED.findall("⊗S:mutation") != []
          and not re.match(r"^\\d{4}", "2026-10-01.md"),
          "the double-escaped forms still match nothing (control)")

    # 2. delegated identity (not merely equality by luck)
    check("delegated-parse-dir", parse_dir is _probe.parse_dir, "parse_dir IS the probe's")
    check("delegated-compute", compute is _probe.compute, "compute IS the probe's")
    check("delegated-verdict", verdict is _probe.verdict, "verdict IS the probe's")
    check("delegated-constants",
          AMBIGUOUS_TOOLS is _probe.AMBIGUOUS_TOOLS
          and MUTATION_TOOLS is _probe.MUTATION_TOOLS
          and HONESTY is _probe.HONESTY,
          "taxonomy constants are the probe's objects")

    # 3. behavioural equality on the live corpus
    if os.path.isdir(diary):
        mine = parse_dir(diary)
        theirs = _probe.parse_dir(diary)
        check("live-tally-equal", mine == theirs, f"total_tools={mine['total_tools']}")
        check("live-tally-nonempty", mine["total_tools"] > 0,
              "the diary is actually parsed (pre-fix this was 0)")
        ec, es = compute(mine)
        check("epsilon-system-nonzero", es > 0,
              f"ε_system={es:.4f} (pre-fix 0.0 = A4-collapse reading)")
        check("verdict-not-collapse", not verdict(ec, es).startswith("NO-EPSILON"),
              verdict(ec, es))
    else:
        check("diary-present", False, f"{diary} missing; run with HERMES_DIARY set")

    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    import re  # noqa: E402  (used by the selftest's escape-sensitive controls)
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    # Allow running as a script for quick testing (same as the probe's main but using this module)
    DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")
    tally = parse_dir(DIARY)
    ec, es = compute(tally)
    v = verdict(ec, es)
    print("=== A6 ε-probe — the runtime's own remainder (ε as the Sovereignty Term) ===")
    print(f"diary_dir        : {DIARY}")
    print(f"typed mutation   : {tally['typed_mutation']}")
    print(f"typed observe    : {tally['typed_observe']}")
    print(f"untyped ambiguous: {tally['untyped_ambiguous']}   (ε_code: unclassified actions)")
    print(f"mislabels        : {tally['mislabels']}   (ε_code: intent recorded wrong)")
    print(f"honesty marks    : {tally['honesty']}   (ε_system: ⊗Er/⊗RCA/!Dc/!Dm/⊗RES)")
    print(f"total tool lines : {tally['total_tools']}")
    print(f"\n  ε_code   = {ec:.4f}   (accidental, compressible)")
    print(f"  ε_system = {es:.4f}   (chosen, protect — the could-have-done-otherwise residue)")
    print(f"\n  VERDICT: {v}")
    print("\n(read-only probe — ε is reported, never acted upon. A4 prefers ε_system > 0.)")
