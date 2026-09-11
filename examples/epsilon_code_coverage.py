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
version-controlled copy of the producer `session-scribe/action_typing.py`).

Exit 0 always (read-only; it reports, never gates).
"""

import json
import sqlite3
import sys
import collections
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import action_typing_classifier as at  # noqa: E402

DB = "/mnt/hermes/state.db"


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


def main():
    cmds = load_commands(DB)
    results = collections.Counter()
    for tool, cmd in cmds:
        key = "command" if tool == "terminal" else "code"
        results[at.classify(tool, {key: cmd})] += 1
    total = len(cmds)
    unknown = results[""]
    coverage = (total - unknown) * 100.0 / total
    print(f"commands measured : {total}")
    print(f"  mutation        : {results['mutation']:5d}  ({results['mutation']*100.0/total:.1f}%)")
    print(f"  observe         : {results['observe']:5d}  ({results['observe']*100.0/total:.1f}%)")
    print(f"  UNKNOWN (ε_code): {unknown:5d}  ({unknown*100.0/total:.1f}%)")
    print(f"\n  classifier coverage (typed / total) = {coverage:.1f}%")
    print(f"  (ε_code compressible surface = {unknown*100.0/total:.1f}% of ambiguous commands)")
    print(f"\n(read-only — the classifier's UNKNOWN% is measured, never acted upon.")


if __name__ == "__main__":
    main()