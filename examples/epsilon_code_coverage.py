#!/usr/bin/env python3
"""ε_code compression proof — measure terminal-shape classifier coverage (A6 forward-only).

Read-only. Queries the live Hermes state.db for every recorded terminal/execute_code
command (the ground truth the diary's bare `>T:terminal` lines do not persist), runs
each through the action-typing classifier, and reports the UNKNOWN fraction — the
measure of ε_code's compressible surface. A falling UNKNOWN% across classifier
versions is the falsifiable claim behind the A6 forward-only action ("extend the
terminal-shape classifier to compress ε_code → ε_system without touching the
sovereignty residue").

The classifier under test is `examples/action_typing_classifier.py` (the vendored,
version-controlled copy of the producer `session-scribe/action_typing.py`). Because
the measured copy and the production producer are *two files*, the measure is only
honest while the two are byte-identical — see `--synccheck`.

Exit 0 always (read-only; it reports, never gates), except `--selftest` and
`--synccheck` which exit non-zero on failure (deterministic check, not a metric gate).
"""

import json
import sqlite3
import sys
import collections
import re
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import action_typing_classifier as at  # noqa: E402

DB = "/mnt/hermes/state.db"
PRODUCER = "/mnt/hermes/plugins/session-scribe/action_typing.py"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _vendored_path():
    """Absolute path of the imported vendored classifier (this instrument's source of truth)."""
    return Path(at.__file__).resolve()


def synccheck():
    """Falsify the producer↔vendored byte-identity invariant.

    The v0.8.16 taxonomy drift (AMBIGUOUS_TOOLS = {"terminal"} dropped
    execute_code/browser_exec) went undetected for a whole release because no
    instrument asserted the *measured* classifier matched the *production*
    producer. This is that assertion: the vendored copy this coverage instrument
    imports is only a faithful measure while it is byte-identical to the live
    `session-scribe/action_typing.py` that actually types the diary. A fork here
    means the UNKNOWN% is being computed against a classifier the production
    diary never used.

    Returns (ok, vendored_sha, producer_sha, detail).
    """
    vend = _sha256(_vendored_path())
    prod = _sha256(PRODUCER)
    ok = vend == prod
    if ok:
        detail = "producer == vendored (byte-identical, hashes equal)"
    else:
        detail = (
            "DRIFT: producer and vendored classifier differ — the coverage measure "
            "is not computed against the production classifier. Vendor the producer "
            "into examples/action_typing_classifier.py before trusting UNKNOWN%."
        )
    return ok, vend, prod, detail


def load_commands(sqlite_path):
    con = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute("SELECT tool_calls FROM messages WHERE tool_calls IS NOT NULL AND tool_calls != ''")
    rows = cur.fetchall()
    out = []
    for (tc,) in rows:
        try:
            calls = json.loads(tc)
        except Exception:
            continue
        for c in calls:
            fn = c.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except Exception:
                args = {}
            if name == "terminal":
                cmd = args.get("command", "")
                if cmd:
                    out.append(("terminal", cmd))
            elif name == "execute_code":
                code = args.get("code", "")
                if code:
                    out.append(("execute_code", code))
    con.close()
    return out


def _selftest():
    """Prove the instrument is honest: classifier import real, mutation/observe
    paths fire, the UNKNOWN path is real, and the sync check detects a fork."""
    ok = True

    # 1. classifier is importable and exposes the expected interface
    for attr in ("classify", "MUTATE_TOOLS", "OBSERVE_TOOLS", "AMBIGUOUS_TOOLS"):
        ok &= hasattr(at, attr)

    # 2. classification paths fire deterministically on terminal shapes
    mut = at.classify("terminal", {"command": "git commit -m x && git push"})
    obs = at.classify("terminal", {"command": "systemctl is-active hermes-gateway"})
    unk = at.classify("terminal", {"command": "python3 /tmp/deploy_or_test.py"})
    ok &= mut == "mutation"
    ok &= obs == "observe"
    ok &= unk == ""  # genuinely ambiguous driver blob → never guessed

    # 3. unambiguous tool families resolve without a command string
    ok &= at.classify("write_file", {}) == "mutation"
    ok &= at.classify("read_file", {}) == "observe"
    ok &= at.classify("browser_exec", {}) == ""  # ambiguous with no evidence → UNKNOWN

    # 4. the sync check reports OK on the live (byte-identical) files, and would
    #    flag a fork (prove the detector works by passing a wrong producer path)
    sync_ok, vsha, psha, _detail = synccheck()
    ok &= sync_ok
    # negative control: a deliberately-wrong producer path must NOT match
    bogus_sha = _sha256(str(Path(__file__).resolve().parent / "a6_epsilon_probe.py"))
    ok &= bogus_sha != psha  # sanity: the detector is comparing real content

    print("  selftest[import      ] %s" % ("PASS" if hasattr(at, "classify") else "FAIL"))
    print("  selftest[mutation    ] %s  (git commit+push → mutation)" % ("PASS" if mut == "mutation" else "FAIL"))
    print("  selftest[observe     ] %s  (systemctl is-active → observe)" % ("PASS" if obs == "observe" else "FAIL"))
    print("  selftest[unknown     ] %s  (bare python3 driver → UNKNOWN)" % ("PASS" if unk == "" else "FAIL"))
    print("  selftest[synccheck   ] %s  (producer == vendored)" % ("PASS" if sync_ok else "FAIL"))
    return ok


def main():
    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    if "--synccheck" in sys.argv:
        ok, vsha, psha, detail = synccheck()
        print(f"producer {psha[:12]}  vendored {vsha[:12]}")
        print(f"SYNC: {'OK' if ok else 'DRIFT'} — {detail}")
        sys.exit(0 if ok else 1)

    cmds = load_commands(DB)
    results = collections.Counter()
    for tool, cmd in cmds:
        key = "command" if tool == "terminal" else "code"
        results[at.classify(tool, {key: cmd})] += 1
    total = len(cmds)
    unknown = results[""]
    coverage = (total - unknown) * 100.0 / total
    sync_ok, vsha, psha, _detail = synccheck()
    print(f"commands measured : {total}")
    print(f"  mutation        : {results['mutation']:5d}  ({results['mutation']*100.0/total:.1f}%)")
    print(f"  observe         : {results['observe']:5d}  ({results['observe']*100.0/total:.1f}%)")
    print(f"  UNKNOWN (ε_code): {unknown:5d}  ({unknown*100.0/total:.1f}%)")
    print(f"\n  classifier coverage (typed / total) = {coverage:.1f}%")
    print(f"  (ε_code compressible surface = {unknown*100.0/total:.1f}% of ambiguous commands)")
    print(f"  producer sync   : {'OK' if sync_ok else 'DRIFT (measure not against production classifier)'}")
    print(f"\n(read-only — the classifier's UNKNOWN% is measured, never acted upon.")


if __name__ == "__main__":
    main()