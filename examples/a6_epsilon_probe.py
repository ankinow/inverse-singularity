#!/usr/bin/env python3
"""A6 ε-probe — measure the runtime's own remainder (the ε as the Sovereignty Term).

CURIOSITY thread "ε as the Sovereignty Term" (Simmering, HIGH salience) asks two
falsifiable questions that every prior instrument left un-measured:

  1. "does ε = 0 violate A4, or does it mean the system was never sovereign to begin with?"
  2. "is the boundary between ε_code and ε_system itself an ε?"

Every Q instrument (a3_*, a4_action_typing) measures Q = φ/κ but NONE reads the ε
remainder — the gap between what the runtime's constraints prescribe and what it
actually did. This probe is the first to read ε out of the production diary instead
of theorizing about it, decomposing it along the thread's own axis:

  ε_code   (accidental — compressible by discipline):
      * untyped ambiguous calls — `>T:` tool lines whose tool is ambiguous
        (terminal and other non-read/non-write kinds) with no `⊗S:` typing,
        i.e. actions the producer could not classify (the enforcement gap).
      * mislabels — a `⊗S:mutation` whose tool-kind is observe-only (or the
        inverse): intent recorded but wrongly. Closeable by better classification.

  ε_system (irreducible — the chosen remainder, must be protected):
      * honesty marks — `⊗Er:` / `⊗RCA:` (honest error + root-cause) and the
        decision family `!Dc:` / `!Dm:` / `⊗RES:`. These are the residue of REAL
        work the agent chose to record — the signature of a system that "could
        have done otherwise" (ε > 0). Their ABSENCE at scale is the SS7
        transparency gap (errors under-reported): the system claiming ε = 0,
        which the thread says collapses the meaning of Q = φ/κ + ε.

Read-only, never acts. Selftest proves each verdict path fires deterministically.

Verdicts:
  NO-EPSILON    ε_code=0 AND ε_system=0  → claimed-perfect (A4-questionable)
  CODE-HEAVY    ε_code>0 AND ε_system=0  → enforcement-gap only, SS7 under-report
  SOVEREIGN     ε_system>0               → a recording, could-have-done-otherwise
"""

import os
import re
import sys

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")

# Canonical tool families (matches a4_action_typing doctrine §2).
MUTATION_TOOLS = {"patch", "write_file", "execute_code"}
OBSERVE_TOOLS = {
    "read_file", "skill_view", "search_files", "web_search", "web_extract",
    "memory", "process", "browser_exec", "tool_search", "tool_describe", "tool_call",
    "web_extract", "delegate_task",
}
AMBIGUOUS_TOOLS = {"terminal"}
# honesty / decision family = the *chosen* residue (ε_system)
HONESTY = ("⊗Er:", "⊗RCA:", "⊗RES:", "!Dc:", "!Dm:")

_RE_TOOL = re.compile(r"^>T:([a-zA-Z_]+)")
_RE_TYPED = re.compile(r"^⊗S:(mutation|observe)\b")


def _is_mutation_tool(tool):
    return tool in MUTATION_TOOLS


def _is_observe_tool(tool):
    return tool in OBSERVE_TOOLS


def parse_dir(diary_dir):
    """Tally, across all diary files, the ε-relevant counts (canonical regexes).

    Pairing (matches the producer scribe_core.tool_call): a `>T:tool` line is
    appended FIRST, then a `⊗S:intent` marker labels the tool directly ABOVE it.
    So a `⊗S:` pairs with the most recent `>T:` line, not the next one.
    """
    files = sorted(f for f in os.listdir(diary_dir) if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", f))
    typed = {"mutation": 0, "observe": 0}
    untyped_ambiguous = 0
    mislabels = 0
    honesty = 0
    total_tools = 0
    prev_tool = None  # most recent unscored `>T:` tool, awaiting its `⊗S:` label
    for fname in files:
        with open(os.path.join(diary_dir, fname), encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                s = raw.strip()
                mt = _RE_TYPED.match(s)
                if mt:
                    intent = mt.group(1)
                    typed[intent] += 1
                    if prev_tool is not None:
                        # score the tool this marker labels
                        if prev_tool in AMBIGUOUS_TOOLS:
                            pass  # typed ambiguous is fine (already counted in typed)
                        elif intent == "mutation" and _is_observe_tool(prev_tool):
                            mislabels += 1
                        elif intent == "observe" and _is_mutation_tool(prev_tool):
                            mislabels += 1
                    prev_tool = None
                    continue
                mh = re.search("|".join(re.escape(m) for m in HONESTY), s)
                if mh:
                    honesty += 1
                    continue
                mg = _RE_TOOL.match(s)
                if not mg:
                    continue
                tool = mg.group(1).lower()
                total_tools += 1
                if prev_tool is not None:
                    # previous tool got no `⊗S:` label → it was untyped
                    if prev_tool in AMBIGUOUS_TOOLS:
                        untyped_ambiguous += 1
                prev_tool = tool

    # trailing untyped tool at EOF (no closing marker)
    if prev_tool is not None and prev_tool in AMBIGUOUS_TOOLS:
        untyped_ambiguous += 1

    return {
        "typed_mutation": typed["mutation"],
        "typed_observe": typed["observe"],
        "untyped_ambiguous": untyped_ambiguous,
        "mislabels": mislabels,
        "honesty": honesty,
        "total_tools": total_tools,
    }


def compute(tally):
    typed_total = tally["typed_mutation"] + tally["typed_observe"]
    denom = max(typed_total, 1)
    eps_code = (tally["untyped_ambiguous"] + tally["mislabels"]) / denom
    eps_system = tally["honesty"] / denom
    return eps_code, eps_system


def verdict(eps_code, eps_system):
    if eps_code == 0.0 and eps_system == 0.0:
        return "NO-EPSILON (claimed-perfect; A4-questionable: could-not-have-done-otherwise)"
    if eps_code > 0 and eps_system == 0.0:
        return "CODE-HEAVY (enforcement-gap only; ε_system absent = SS7 under-report at scale)"
    if eps_system > 0:
        if eps_code > eps_system:
            return "SOVEREIGN-CODE (ε_system present but ε_code dominates: partially recording)"
        return "SOVEREIGN (ε_system present: a recording, could-have-done-otherwise system)"
    return "UNCLASSIFIED"


def _parse_text(text):
    """Parse a synthetic in-memory diary through the same (corrected) tally logic."""
    typed = {"mutation": 0, "observe": 0}
    untyped_ambiguous = 0
    mislabels = 0
    honesty = 0
    total_tools = 0
    prev_tool = None
    for raw in text.splitlines():
        s = raw.strip()
        mt = _RE_TYPED.match(s)
        if mt:
            intent = mt.group(1)
            typed[intent] += 1
            if prev_tool is not None:
                if prev_tool in AMBIGUOUS_TOOLS:
                    pass
                elif intent == "mutation" and _is_observe_tool(prev_tool):
                    mislabels += 1
                elif intent == "observe" and _is_mutation_tool(prev_tool):
                    mislabels += 1
            prev_tool = None
            continue
        if re.search("|".join(re.escape(m) for m in HONESTY), s):
            honesty += 1
            continue
        mg = _RE_TOOL.match(s)
        if not mg:
            continue
        tool = mg.group(1).lower()
        total_tools += 1
        if prev_tool is not None and prev_tool in AMBIGUOUS_TOOLS:
            untyped_ambiguous += 1
        prev_tool = tool
    if prev_tool is not None and prev_tool in AMBIGUOUS_TOOLS:
        untyped_ambiguous += 1
    return {
        "typed_mutation": typed["mutation"], "typed_observe": typed["observe"],
        "untyped_ambiguous": untyped_ambiguous, "mislabels": mislabels,
        "honesty": honesty, "total_tools": total_tools,
    }


def _selftest():
    # 1: NO-EPSILON — typed calls (via `>T:` then `⊗S:` after), no ambiguity, no honesty
    d1 = """>T:write_file foo
⊗S:mutation
>T:read_file bar
⊗S:observe
"""
    # 2: CODE-HEAVY — an untyped ambiguous call + a mislabel, no honesty
    #    `>T:terminal` with no following marker = untyped;
    #    `>T:read_file x` then `⊗S:mutation` = mislabel (mutation on observe tool)
    d2 = """>T:terminal
>T:read_file x
⊗S:mutation
"""
    # 3: SOVEREIGN — a typed mutation + honesty marks
    d3 = """>T:patch x
⊗S:mutation
⊗Er: patch rejected by curator guard
!Dc: chose the aggressive option
>T:read_file y
⊗S:observe
"""
    cases = [
        ("no-epsilon", d1, "NO-EPSILON"),
        ("code-heavy", d2, "CODE-HEAVY"),
        ("sovereign", d3, "SOVEREIGN"),
    ]
    ok = True
    for name, raw, want in cases:
        ec, es = compute(_parse_text(raw))
        got = verdict(ec, es).split(" ")[0]
        ok &= got == want
        print(f"  selftest[{name:11s}] {'PASS' if got == want else f'FAIL (want {want})'}  "
              f"ε_code={ec:.2f} ε_system={es:.2f}")
    # math: ε non-negative
    ec, es = compute(_parse_text(d3))
    assert ec >= 0 and es >= 0
    print("  selftest[math     ] PASS (ε ≥ 0)")
    return ok


def main():
    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

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


if __name__ == "__main__":
    main()