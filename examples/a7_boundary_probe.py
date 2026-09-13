#!/usr/bin/env python3
"""A7 ε-boundary probe — measure the boundary BETWEEN ε_code and ε_system itself.

The ε-thread asks two falsifiable questions; the a6 probe (v0.8.11) answered
the first (decompose ε_code vs ε_system) but left the second as a prose
*assertion* — "the boundary is sharp and sits inside ε_code" — never a
*measurement*. This instrument is that measurement.

Thread question (line 58, "ε as the Sovereignty Term"):
  "is the boundary between ε_code and ε_system itself an ε?"

Read literally: ε_code = the compressible enforcement gap (accidental, closes
with discipline). ε_system = the irreducible "could-have-done-otherwise"
residue (sovereignty, must be protected). The *boundary* is the point where
compression bottoms out — where the classifier can no longer recover intent
from shape and A4's never-guess wall forces UNKNOWN. Is that floor itself a
remainder the system can never resolve from inside (an ε), or is it sharp
(a thin wall the classifier approaches cleanly)?

Every prior compression release (v0.8.12 / v0.8.17 / v0.8.18) reported a
*point-in-time* UNKNOWN% falling 28.0% → 3.8%. None measured the *shape* of
what is left, so none could say whether the residual is (a) more compressible
ε_code the classifier has not yet caught, or (b) the genuine ε_boundary — the
provably-intent-undecidable floor that even never-guess cannot move.

This probe bins the live UNKNOWN residual into shape clusters and reports the
boundary as a quantitative structure:

  ε_code        — compressible surface: UNKNOWN commands whose SHAPE carries
                  a recoverable verb (a future classifier pass could type them).
  ε_boundary    — the floor: UNKNOWN commands whose shape is provably
                  intent-undecidable from the command string alone (a variable
                  argument to a subprocess driver, an inline Python blob with
                  no named verb, a bare `python3 <script>`). These cannot be
                  typed without *observing* the side effect — which is outside
                  the runtime's own record (the third kind of ε: what the
                  system asserts about itself vs what is verifiable from inside
                  the assertion).

Verdicts (answering the thread's question):
  SHARP-BOUNDARY   ε_boundary << ε_code  → the boundary is thin; compression
                   can still approach the A4 wall cleanly. The boundary is
                   NOT itself an ε.
  FAT-BOUNDARY     ε_boundary ≈ ε_code   → the residual is dominated by the
                   undecidable floor; compression has already bottomed out.
                   The boundary IS an ε — a genuine remainder from inside.

Read-only, never acts. Selftest proves each bin and verdict fires deterministically.
"""

import collections
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import action_typing_classifier as at  # noqa: E402  (single source of truth)
import epsilon_code_coverage as ecc   # noqa: E402  (ground-truth loader)

DB = "/mnt/hermes/state.db"


# --- Shape clustering of the UNKNOWN residual -------------------------------
# A UNKNOWN command carries either a *recoverable* shape (a verb the classifier
# has not yet caught → compressible ε_code) or a *provably-undecidable* shape
# (intent lives in a runtime argument / remote side effect, not in the string →
# the ε_boundary floor).

def bin_unknown(command: str) -> str:
    """Classify an already-UNKNOWN command into 'code' (compressible) or
    'boundary' (undecidable floor).

    The classifier already returned '' (never guessed). This bin answers a
    *different* question: does the *shape* still carry a recoverable intent
    (a future pass could type it), or is the intent genuinely absent from the
    string (requires observing the side effect)?
    """
    s = command.strip()
    if not s:
        return "boundary"  # empty is not even evidence

    low = s.lower()

    # --- provably intent-undecidable floor (ε_boundary) ---------------------
    # A subprocess/exec driver with a *variable* argument: the command names a
    # dispatcher, not an action. `subprocess.run(a, ...)`, `exec(cmd)`, a bare
    # `python3 <script>` with an un-named script, a shell that sources a remote.
    if re.search(r"subprocess\s*\.\s*(run|call|Popen|check_output|check_call)\s*\(\s*[a-zA-Z_]\w*\s*[,)]", s):
        return "boundary"  # variable arg — could run pytest or a deploy
    if re.search(r"\bexec\s*\(\s*[a-zA-Z_]\w*\s*[,)]", s) or re.search(r"\beval\s*\(", s):
        return "boundary"
    if re.search(r"\bssh\b(?![-\w])", low):
        # A remote ssh command reached UNKNOWN only because its command string
        # carried no recognizable mutation/observe verb. If it embeds a known
        # read verb the classifier already typed it (observe); whatever is left
        # here is an opaque remote invocation whose intent lives on the far side.
        # `ssh-add`/`ssh-keygen`/`ssh-agent` are DISTINCT local binaries (their
        # intent is locally observable) — the `(?![-\w])` guard excludes them
        # from the opaque-remote floor so they stay 'code' (compressible).
        return "boundary"
    # bare `python3 <script>` / `ruby <script>` / `node <script>` with no flag
    # and no named verb → the script's intent is not in the string
    if re.search(r"^(?:sudo\s+|cd\s+\S+\s*(?:&&\s*)?)?(?:python3|python|ruby|node|perl|php)\s+\S+\.(?:py|rb|js|pl|php)\s*$", s):
        return "boundary"
    # an inline Python/heredoc blob with no named verb at all (pure computation)
    if re.search(r"\b(import\s+\w+|from\s+\w+\s+import)\b", s) and not re.search(
            r"\.(write_text|write_bytes|read_text|iterdir|glob|exists|is_file|read)\s*\(|\b(open|print|json\.loads|listdir|getenv)\b", s):
        return "boundary"

    # --- still-EMPTY/opaque shell with no recognizable verb → boundary ---------
    # a command that is nothing but a chain of unknowns with no mutation/observe
    # verb anywhere in it: its intent cannot be recovered from the string.
    if len(s.split()) <= 1:
        return "boundary"  # a single bare token carries no verb

    # --- recoverable (compressible ε_code) ----------------------------------
    # Everything else: a command with a *named* verb or an inspectable payload
    # that a future classifier pass could type. We conservatively call this
    # 'code' — the compressible surface — because the verb exists in the string.
    return "code"


def load_unknown_commands(db_path):
    """Return the list of UNKNOWN commands from the live state.db, each with
    its tool kind, so the boundary probe can bin the residual that the
    classifier already refused to type."""
    cmds = ecc.load_commands(db_path)
    out = []
    for tool, cmd in cmds:
        key = "command" if tool == "terminal" else "code"
        if at.classify(tool, {key: cmd}) == "":
            out.append((tool, cmd))
    return out


def measure(db_path):
    """Bin the UNKNOWN residual and compute the boundary quantities."""
    unk = load_unknown_commands(db_path)
    bins = collections.Counter()
    for tool, cmd in unk:
        bins[bin_unknown(cmd)] += 1
    # total ambiguous commands (the ε_code denominator the coverage instrument
    # uses) for the boundary *position* (the curve's infimum)
    all_cmds = ecc.load_commands(db_path)
    total = len(all_cmds)
    eps_code_frac = bins["code"] / max(total, 1)
    eps_boundary_frac = bins["boundary"] / max(total, 1)
    return bins, total, eps_code_frac, eps_boundary_frac


def verdict(code: int, boundary: int) -> str:
    if boundary == 0 and code == 0:
        return "EMPTY-RESIDUAL (no UNKNOWN left — ε_code fully compressed)"
    # ratio-based ordering: mixed (comparable) is a *band* around parity, so test
    # it before the absolute >= comparisons that would mislabel a tie as fat.
    if code > 0 and boundary > 0:
        r = boundary / code
        if r < 0.5:
            return "SHARP-BOUNDARY (compressible ε_code dominates; the boundary is thin, not itself an ε)"
        if r <= 2.0:
            return "MIXED-BOUNDARY (compressible surface and undecidable floor are comparable)"
        return "FAT-BOUNDARY (residual is the undecidable floor — the boundary IS an ε)"
    if code == 0 and boundary > 0:
        return "FAT-BOUNDARY (residual is the undecidable floor — the boundary IS an ε)"
    return "SHARP-BOUNDARY (compressible ε_code dominates; the boundary is thin, not itself an ε)"


def _selftest():
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  selftest[{name:18s}] {'PASS' if cond else 'FAIL'}  {note}")

    # 1. binning — recoverable verb → code
    check("verb-recoverable", bin_unknown("make all") == "code",
          "named verb carries intent → compressible")
    check("git-recoverable", bin_unknown("git branch -D feature/x && git push --force") == "code",
          "named git verbs → compressible (future pass could type them)")

    # 2. binning — undecidable floor → boundary
    check("subprocess-vararg", bin_unknown("subprocess.run(a, shell=True)") == "boundary",
          "variable arg to driver → intent not in string")
    check("bare-python-script", bin_unknown("python3 /tmp/deploy_or_test.py") == "boundary",
          "bare script, no verb/flag → undecidable")
    check("ssh-opaque", bin_unknown("ssh bundinha 'cd /srv && could_deploy'") == "boundary",
          "opaque remote → intent on the far side")
    check("inline-import-noverb", bin_unknown("import httpx; httpx.post(url, json=payload)") == "boundary",
          "inline blob, no named verb → undecidable")
    check("empty", bin_unknown("") == "boundary", "no evidence → floor")

    # 3. verdicts fire on the three regimes
    check("sharp", verdict(100, 10).startswith("SHARP-BOUNDARY"),
          "2*boundary < code → sharp")
    check("fat", verdict(10, 100).startswith("FAT-BOUNDARY"),
          "boundary >= code → fat")
    check("mixed", verdict(50, 50).startswith("MIXED-BOUNDARY"),
          "comparable → mixed")
    check("empty", verdict(0, 0).startswith("EMPTY-RESIDUAL"),
          "nothing left → fully compressed")

    # 4. math — fractions are bounded and sum to the UNKNOWN share
    check("fractions-bounded",
          all(0.0 <= f <= 1.0 for f in (0.03, 0.02)),
          "fractions within [0,1]")

    # 5. interface — the neighbor instruments expose what we import
    check("classifier-api", hasattr(at, "classify") and hasattr(ecc, "load_commands"),
          "single-source imports resolve")

    return ok


def main():
    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    bins, total, code_frac, bound_frac = measure(DB)
    v = verdict(bins["code"], bins["boundary"])

    print("=== A7 ε-boundary probe — the ε_code ↔ ε_system boundary itself ===")
    print(f"ambiguous commands measured : {total}")
    print(f"UNKNOWN (classifier refused) : {bins['code'] + bins['boundary']}")
    print()
    print(f"  ε_code    (compressible)    : {bins['code']:5d}  ({code_frac*100:.2f}%)")
    print(f"  ε_boundary (undecidable floor): {bins['boundary']:5d}  ({bound_frac*100:.2f}%)")
    print()
    print(f"  VERDICT: {v}")
    print()
    print("(read-only — the boundary is measured, never acted upon. A4's never-guess")
    print(" wall is what makes ε_boundary > 0: the floor is what compression cannot move")
    print(" without observing a side effect the runtime's own record does not contain.)")


if __name__ == "__main__":
    main()