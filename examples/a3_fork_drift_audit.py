#!/usr/bin/env python3
"""
A3 fork-drift audit — is every `a3_quality_delta` consumer a WINDOW on the
producer, or a FORK that re-decides the producer's rules?

Derived from D34/D34b (2026-10-01).  The D34b fix made
`a3_quality_delta_sweep.py` *import* the producer instead of re-implementing
it.  This instrument generalises that same gate to EVERY file in the family,
so the next fork cannot land unnoticed.

What the item that produced this instrument asked for, and what measurement
said:

  It named `a3_kappa_reduction.py` / `a3_dense_phi.py` as the suspects.
  MEASURED: both are INNOCENT.  Neither touches the producer's surface —
  they read the diary's tool histogram (a different measurement surface),
  and bind none of the producer's decision objects.

  The real third fork is `examples/a3_tau_sweep.py`, which the item did not
  mention: it defines its own `classify_outcome` (1-arg, so it cannot see
  `end_reason`/`api` and therefore cannot classify a cap hit at all), its own
  `aggregate` (whose `stats()` inner function is computed and thrown away),
  and a production branch that prints a HARD-CODED verdict string instead of
  measuring anything.

Design constraints (this repo's doctrine, applied to the instrument itself):
  * read-only — the audit never writes; it only reads + imports the producer.
  * zero deps, stdlib only.
  * A consumer is NEVER imported.  Arbitrary files under examples/ may have
    import-time side effects, so a consumer's `classify_outcome` is extracted
    as a SINGLE FunctionDef, compiled alone, and called with the producer's
    own corpus constants.  No consumer top-level code ever runs.
  * "delegates" vs "fork" is decided by whether the local definition actually
    references the producer object — a documented view (D34b's
    `aggregate`/`verdict_of`) is a window, not a drift.

Usage:
  python3 examples/a3_fork_drift_audit.py             # JSON report, rc 0
  python3 examples/a3_fork_drift_audit.py --selftest  # rc 0 pass / 1 fail
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCER_PATH = os.path.join(HERE, "a3_quality_delta.py")
SCRATCH = os.environ.get("TMPDIR", "/tmp")

# --------------------------------------------------------------------------
# The producer's decision surface.  A consumer may legitimately HOLD these
# names (re-export, window, or a documented different view); what it may not
# do is RE-DECIDE them locally.  This set is the single-source definition of
# "re-deciding".
# --------------------------------------------------------------------------
PRODUCER_SURFACE = frozenset({
    # classifiers
    "classify_outcome", "verdict_of",
    # harvest / verification
    "extract_shas", "ShaVerifier", "load_ticks", "final_assistant_texts",
    "window_of", "_local_epoch",
    # regexes
    "SHA_NEAR_KEYWORD", "SHA_BACKTICKED", "DONE_WORD", "REPORT_HDR",
    "BACKLOG_DONE", "FAIL_MARKERS", "SAFE_CONTEXT",
    # arithmetic / constants
    "aggregate", "DECIDED_EXCLUDE", "MIN_GROUP_N", "DEADLINE_TURN",
    "JOB_KEY", "STATE_DB", "CRON_DB", "REPOS", "FIRST_ARM_LOCAL", "WINDOWS",
})

# Keys of the producer's row contract.  A consumer that re-derives group
# membership from raw fields instead of reading the producer's keys is
# re-deciding the producer's split, even if the arithmetic looks familiar.
PRODUCER_ROW_KEYS = frozenset({
    "group", "artifact", "outcome", "api", "id", "start", "tools",
    "window", "end_reason",
})

# The producer's PREDECESSOR in the same measurement series.  It shares the
# producer's constants (DEADLINE_TURN / WINDOWS / STATE_DB) BY DESIGN — the
# producer names it as the source of its window table — and the producer
# declares no re-use of anything in return.  Sharing constants with a
# predecessor is not a fork; re-deciding a RULE is.  Kept explicit so the
# distinction is auditable rather than an allowlist nobody can check.
SIBLING_PREDECESSORS = {
    "a3_deadline_production.py": "producer v0.8.6; shares DEADLINE_TURN/"
                                 "WINDOWS/STATE_DB by design, re-decides no "
                                 "producer rule",
}

# Files that are INDEPENDENT measurement series rather than consumers of the
# producer: they share a CONSTANT NAME (STATE_DB is the obvious one) but
# import nothing and re-decide nothing.  A shared path variable is not a
# shared rule.  Each entry names the evidence that made the call, so the
# exemption is auditable rather than an allowlist nobody can check.
INDEPENDENT_SERIES = {
    "a9_claim_evidence_trend.py": "claim-marker series; imports nothing "
                                  "from the producer, STATE_DB is its own "
                                  "env-overridable path",
}

# Outcomes the producer counts as a delivered tick.  A consumer that omits
# any of these from its numerator while keeping it in the denominator is
# biased AGAINST the cap — the A3 question is whether the cap costs quality,
# so under-counting cap success inverts the measurement.
DELIVERED_OUTCOMES = ("DONE", "CAP_DELIVERED")

# Probe corpus: one entry per producer outcome branch, with the real
# signature (tail, end_reason, api).  Used to diff a consumer's classifier
# against the producer's, label for label.
PROBE_CORPUS = [
    ("[done 2026-10-01] item 1 complete", None, 12, "DONE"),
    ("item concluído — commit 19b5399", None, 20, "DONE"),
    # Cap reached but the budget did NOT report a hard stop: the harness
    # writes a final report right before the budget ends -> CAP_DELIVERED.
    ("## Relatório — dev-contínuo\n**Item**: D34b\ncommit `19b5399`",
     None, 66, "CAP_DELIVERED"),
    ("## Relatório\n**Item**: D34b\ncommit `19b5399`", None, 70,
     "CAP_DELIVERED"),
    # Hard stop reported by the scheduler wins, delivery or not (the
    # producer orders this block BEFORE the delivery check).
    ("## Relatório\n**Item**: D34b\ncommit `19b5399`", "max_turns", 66,
     "CAP_CUT"),
    ("partial thoughts, no report", None, 70, "CAP_CUT_SOFT"),
    ("partial thoughts, no report", "max_turns", 70, "CAP_CUT"),
    ("IDLE 2026-10-01T19:00 queue empty", None, 4, "IDLE"),
    ("[SILENT]", None, 3, "SILENT"),
    ("", None, 2, "EMPTY"),
    ("Traceback (most recent call last): job failed", None, 9, "FAIL"),
    ("QA GREEN — 42/42", None, 8, "GATE_GREEN"),
    ("partial thoughts, no verdict", None, 11, "OTHER"),
]


def _load_producer():
    spec = importlib.util.spec_from_file_location("a3_quality_delta",
                                                  PRODUCER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load producer: {PRODUCER_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for required in ("classify_outcome", "aggregate", "verdict_of",
                     "load_ticks", "extract_shas", "ShaVerifier",
                     "DONE_WORD", "SHA_NEAR_KEYWORD", "DECIDED_EXCLUDE",
                     "DEADLINE_TURN"):
        if not hasattr(mod, required):
            raise RuntimeError(f"producer missing {required!r}")
    return mod


# --------------------------------------------------------------------- AST --
def _module_level_bindings(tree: ast.Module) -> dict:
    """name -> node, for module-level defs/classes/assignments only.

    A name bound INSIDE a function is a local, not a re-definition of the
    producer's surface, and is deliberately not collected here.
    """
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            out[node.name] = node
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    out[tgt.id] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target,
                                                            ast.Name):
            out[node.target.id] = node
    return out


def _subscript_keys(node: ast.AST) -> set:
    """Every string subscript used inside `node` (r["group"] style)."""
    keys = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Subscript) and isinstance(sub.slice,
                                                        ast.Constant):
            if isinstance(sub.slice.value, str):
                keys.add(sub.slice.value)
    return keys


def _references_producer(node: ast.AST, alias_names: set) -> bool:
    """True if `node`'s body touches the producer object or its file name.

    A local definition that calls `p.aggregate(...)` (D34b's window) is a
    window.  A local definition that never mentions the producer is a fork.
    """
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and isinstance(sub.value,
                                                         ast.Name):
            if sub.value.id in alias_names:
                return True
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            if "a3_quality_delta" in sub.value:
                return True
        if isinstance(sub, (ast.Import, ast.ImportFrom)):
            for a in sub.names:
                if "a3_quality_delta" in a.name:
                    return True
    return False


def _producer_aliases(tree: ast.Module, path: str) -> set:
    """Module-global names that hold the producer module object.

    Detected statically: a global assigned from a call whose source text
    names the producer file (the `_load_producer()` pattern both D34 and
    D34b use), or a module registered under the producer's basename.
    """
    aliases = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value,
                                                             ast.Call):
            continue
        src = ast.dump(node.value)
        if "a3_quality_delta" in src or "_load_producer" in src:
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    aliases.add(tgt.id)
    if os.path.basename(path).startswith("a3_quality_delta"):
        aliases.add(os.path.splitext(os.path.basename(path))[0])
    return aliases


def _is_guarded(fn: ast.AST, node: ast.AST) -> bool:
    """True if `node` sits ANYWHERE under an `if` with a computed test.

    An alarm branch reads `if recorded != live:` then emits a literal name;
    the condition is computed from state, so the name is derived, not
    fabricated.  A fabrication emits a literal on the straight-line path, with
    no `if` above it at any depth.

    The test is an ANCESTOR walk, not a parent check: the literal sits several
    levels below the `if` (`If` -> Expr -> Call -> Dict -> Constant), so a
    direct-parent check returns False on a real alarm branch — a
    false-positive machine.
    """
    chain = []

    def descend(n):
        for child in ast.iter_child_nodes(n):
            if child is node:
                chain.append(n)
                return True
            if descend(child):
                chain.append(n)
                return True
        return False

    if not descend(fn):
        return False
    return any(isinstance(a, ast.If)
               and not isinstance(a.test, ast.Constant) for a in chain)


def _hardcoded_verdicts(tree: ast.Module) -> list:
    """Verdict strings that are CONSTANTS on the ONLY returned path.

    A hard-coded verdict is fabrication only when it is what the function
    actually RETURNS on its measured path.  `{"verdict": "abstain",
    "reason": "fewer than 2 samples"}` guarded by an early return, next to
    a sibling `{"verdict": verdict}` that carries the measured name, is the
    correct honest-underpowered branch — flagging it is a false positive.

    So a literal is reported only when the enclosing function returns it
    UNCONDITIONALLY, i.e. no other `return` in the function yields a payload
    with a non-literal verdict.
    """
    out = []
    for fn in [n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        literals, has_measured = [], False
        self_literal = {}
        # Both `return {...}` and `print(json.dumps({...}))` EMIT a verdict to
        # the operator.  A literal in either is fabrication if nothing in the
        # function ever reports a measured one.  (The `print` form is what
        # `a3_tau_sweep.main` uses — "production path omitted for brevity",
        # then a hard-coded ABSTAIN that looks like a measurement.)
        for node in ast.walk(fn):
            payload = None
            if isinstance(node, ast.Return) and isinstance(node.value,
                                                           ast.Dict):
                payload = node.value
            elif isinstance(node, ast.Call) and isinstance(node.func,
                                                           ast.Name) \
                    and node.func.id == "print":
                for arg in node.args:
                    if isinstance(arg, ast.Call) and isinstance(
                            arg.func, ast.Attribute) and arg.func.attr == (
                            "dumps"):
                        for sub in ast.walk(arg):
                            if isinstance(sub, ast.Dict):
                                payload = sub
                                break
            if payload is None:
                continue
            for k, v in zip(payload.keys, payload.values):
                if not (isinstance(k, ast.Constant)
                        and k.value == "verdict"):
                    continue
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    literals.append(v.value)
                    self_literal.setdefault(v.value, v)
                else:
                    has_measured = True
        for lit in literals:
            if has_measured:
                continue
            # A literal emitted ONLY under a real `if <condition>:` that the
            # function COMPUTED is an alarm branch, not fabrication: the
            # watchdog derives the name from live state (e.g. `recorded !=
            # live` -> "definition-drift") and abstains silently otherwise.
            # Fabrication is a literal on the UNCONDITIONAL path.
            lit_node = self_literal.get(lit)
            if lit_node is not None and _is_guarded(fn, lit_node):
                continue
            out.append({"function": fn.name, "literal": lit,
                        "why": "emitted unconditionally; nothing in this "
                               "function ever reports a measured verdict"})
    return out


# ------------------------------------------------------- behavioural probe --
def _extract_callable(tree: ast.Module, name: str, module_globals: dict):
    """Compile ONE FunctionDef in isolation and bind it to `module_globals`.

    The consumer module is never imported, so no consumer top-level code can
    run; only this one function body is executed, against globals the
    consumer itself declared.  Returns None when the function cannot be
    extracted (a Name it needs is not a module-level literal we can supply).
    """
    node = module_globals.get(name)
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    ns = {}
    for nname, nnode in module_globals.items():
        if isinstance(nnode, ast.Assign) and len(nnode.targets) == 1 \
                and isinstance(nnode.targets[0], ast.Name):
            try:
                ns[nname] = ast.literal_eval(nnode.value)
            except (ValueError, SyntaxError, TypeError):
                # D40 (2026-10-01): a `re.compile(...)` binding is the single
                # most common module global in this family — BOTH real forks
                # carried one — and it is not literal-evaluable, so every
                # probe raised and the behavioural half of the audit went
                # silent.  Rebuild the pattern from its OWN argument when that
                # argument is a literal, which makes the probe runnable while
                # still executing nothing but the one function body.  A
                # non-literal argument stays unsupplied, and the caller then
                # reports `measured: false` rather than a fake agreement.
                if (isinstance(nnode.value, ast.Call)
                        and isinstance(nnode.value.func, ast.Attribute)
                        and nnode.value.func.attr in ("compile", "search",
                                                      "match", "fullmatch")
                        and getattr(nnode.value.func.value, "id", "")
                        == "re"):
                    try:
                        ns[nname] = re_module.compile(
                            ast.literal_eval(nnode.value.args[0]))
                    except (ValueError, SyntaxError, TypeError, IndexError):
                        pass
    ns["re"] = re_module
    mod = ast.Module(body=[node], type_ignores=[])
    try:
        code = compile(ast.fix_missing_locations(mod), "<audit-extract>",
                       "exec")
    except SyntaxError:
        return None
    try:
        exec(code, ns)
    except Exception:
        return None
    return ns.get(name)


import re as re_module  # noqa: E402  (used by _extract_callable's namespace)


def _classifier_diff(producer, consumer_tree, bindings) -> dict:
    """Run the producer and a consumer's classifier over the same corpus.

    A 1-arg consumer cannot see end_reason/api, so it cannot classify a cap
    hit at all — that is recorded as `signature_mismatch`, not silently
    tolerated.
    """
    fn = _extract_callable(consumer_tree, "classify_outcome", bindings)
    if fn is None:
        return {"status": "not_extractable"}
    import inspect
    try:
        params = list(inspect.signature(fn).parameters)
    except (TypeError, ValueError):
        params = []
    takes_full = len(params) >= 3
    diverged, errors = [], 0
    for tail, end_reason, api, expected in PROBE_CORPUS:
        try:
            got = (fn(tail, end_reason, api) if takes_full
                   else fn(tail))
        except Exception:
            errors += 1
            continue
        ref = producer.classify_outcome(tail, end_reason, api)
        if got != ref:
            diverged.append({"probe": expected, "producer": ref,
                             "consumer": got, "tail": tail[:48]})
    return {
        "status": "ok" if not errors else "probe_errors",
        "signature": params,
        "signature_mismatch": not takes_full,
        "probes": len(PROBE_CORPUS),
        "probes_executed": len(PROBE_CORPUS) - errors,
        "divergences": diverged,
        "divergence_n": len(diverged),
        "errors": errors,
        # D40 (2026-10-01): a consumer whose classifier could not be EXECUTED
        # used to report `divergences: []` — indistinguishable from "it ran and
        # agreed".  A fork carrying `SHA_NEAR_KEYWORD = re.compile(...)` is not
        # a rare shape: both real forks in this family did exactly that, and
        # `re.compile` is not literal-evaluable, so every probe raised and the
        # behavioural half of the audit went silent while the file was still
        # called a drift.  A consumer that was not measured must say so, and
        # callers must not read an unrun diff as agreement.
        "measured": errors == 0,
    }


# ------------------------------------------------------------------ report --
def _const_verdicts(constants: dict, aliases: set) -> tuple:
    """Classify module-level constant bindings: re-export (window) vs fork.

    `SHA_NEAR_KEYWORD = p.SHA_NEAR_KEYWORD` is a RE-EXPORT: the value IS the
    producer's object.  Only a locally *constructed* value (literal, or its
    own call/regex) is a fork.
    """
    windows, forks = [], []
    for n, nd in sorted(constants.items()):
        rec = {"name": n}
        if _references_producer(nd.value, aliases):
            rec["verdict"] = "WINDOW(re-export of producer object)"
            windows.append(rec)
        else:
            rec["verdict"] = "FORK(local constant)"
            forks.append(rec)
    return windows, forks


def audit_file(path: str, producer) -> dict:
    name = os.path.basename(path)
    if name == os.path.basename(PRODUCER_PATH):
        return {"file": name, "role": "producer", "status": "reference"}
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src, filename=path)
    bindings = _module_level_bindings(tree)
    aliases = _producer_aliases(tree, path)

    redefs = {n: nd for n, nd in bindings.items() if n in PRODUCER_SURFACE}
    local_defs = {n: nd for n, nd in redefs.items()
                  if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef))}
    constants = {n: nd for n, nd in redefs.items() if n not in local_defs}

    sibling = name in SIBLING_PREDECESSORS
    independent = name in INDEPENDENT_SERIES

    windows, forks = [], []
    for n, nd in sorted(local_defs.items()):
        rec = {"name": n}
        if _references_producer(nd, aliases):
            rec["verdict"] = "WINDOW(declares + delegates)"
            windows.append(rec)
        else:
            rec["verdict"] = "FORK(re-implements)"
            forks.append(rec)

    cwin, cfork = _const_verdicts(constants, aliases)
    windows += cwin
    if sibling:
        # A predecessor may legitimately carry the same CONSTANTS; it may
        # never re-decide a RULE (a local classify_outcome/aggregate/
        # verdict_of stays a fork, sibling or not).
        for r in cfork:
            r["verdict"] = "SHARED-CONST(predecessor by design)"
            r["why"] = SIBLING_PREDECESSORS[name]
        windows += cfork
        cfork = []
    if independent:
        # Independent series: a shared CONSTANT NAME (a path variable) is not
        # a shared rule.  A local RULE here would still be a fork.
        for r in cfork:
            r["verdict"] = "SHARED-NAME(independent series)"
            r["why"] = INDEPENDENT_SERIES[name]
        windows += cfork
        cfork = []
    forks += cfork

    row_keys = set()
    for nd in local_defs.values():
        row_keys |= _subscript_keys(nd)

    hard = _hardcoded_verdicts(tree)
    diff = _classifier_diff(producer, tree, bindings)
    imports_producer = bool(aliases)

    severity = "clean"
    if forks or hard or diff.get("divergence_n") or diff.get(
            "signature_mismatch"):
        severity = "drift"
    elif windows:
        severity = "window"

    return {
        "file": name,
        "role": "producer-consumer",
        "status": severity,
        "imports_producer": imports_producer,
        "producer_aliases": sorted(aliases),
        "sibling_predecessor": SIBLING_PREDECESSORS.get(name, ""),
        "independent_series": INDEPENDENT_SERIES.get(name, ""),
        "local_redefinitions": sorted(redefs),
        "windows": windows,
        "forks": forks,
        "row_keys_read": sorted(row_keys & PRODUCER_ROW_KEYS),
        "row_keys_unknown": sorted(row_keys - PRODUCER_ROW_KEYS),
        "rederives_group_from": sorted(
            (row_keys & {"api", "end_reason"}) - {"group"}),
        "hardcoded_verdicts": hard,
        "classifier_diff": diff,
    }


def audit_dir(examples_dir: str = HERE, producer=None) -> dict:
    producer = producer or _load_producer()
    files = sorted(f for f in os.listdir(examples_dir)
                   if f.endswith(".py"))
    findings = [audit_file(os.path.join(examples_dir, f), producer)
                for f in files]
    return {
        "schema": "a3-fork-drift-audit/v1",
        "examples_dir": examples_dir,
        "producer": os.path.basename(PRODUCER_PATH),
        "delivered_outcomes": list(DELIVERED_OUTCOMES),
        "files_scanned": len(findings),
        "clean": [f["file"] for f in findings if f["status"] == "clean"],
        "window": [f["file"] for f in findings if f["status"] == "window"],
        "drift": [
            {"file": f["file"],
             "forks": [f2["name"] for f2 in f["forks"]],
             "hardcoded_verdicts": f["hardcoded_verdicts"],
             "classifier_divergences": f["classifier_diff"].get(
                 "divergence_n", 0),
             "signature_mismatch": f["classifier_diff"].get(
                 "signature_mismatch", False)}
            for f in findings if f["status"] == "drift"],
        "findings": findings,
        "read_only": True,
    }


# ---------------------------------------------------------------- selftest --
def selftest() -> int:
    p = _load_producer()
    fails = []

    def check(name, cond, detail: object = ""):
        if not cond:
            fails.append(f"{name}: {detail!r}")

    def audit_synth(src, fname):
        # Written to the scratch dir, never into examples/ — the audit is
        # read-only with respect to the tree it audits.
        tmp = os.path.join(SCRATCH, f"._forkdrift_probe_{fname}")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(src)
        try:
            return audit_file(tmp, p)
        finally:
            os.unlink(tmp)

    rep = audit_dir(producer=p)
    by = {f["file"]: f for f in rep["findings"]}

    # --- T1: the producer itself is never audited as drift ---------------
    prod = by["a3_quality_delta.py"]
    check("T1-producer-role", prod["status"] == "reference")

    # --- T2: the two suspects the item named are innocent ----------------
    # (they measure the diary, not the producer's surface)
    for innocent in ("a3_kappa_reduction.py", "a3_dense_phi.py"):
        f = by.get(innocent)
        check("T2-present-" + innocent, f is not None)
        if f:
            check("T2-clean-" + innocent, f["status"] == "clean",
                  f"status={f['status']} forks={f['forks']}")

    # --- T3: the D34b window is recognised as a WINDOW, not a fork ------
    sw = by["a3_quality_delta_sweep.py"]
    check("T3-window", sw["status"] == "window", sw["status"])
    check("T3-no-fork", sw["forks"] == [], sw["forks"])
    check("T3-delegates", sw["imports_producer"] is True)
    wnames = {w["name"] for w in sw["windows"]}
    check("T3-aggregate-window", "aggregate" in wnames, wnames)

    # --- T4: a real fork IS caught — on a SYNTHETIC fork, not the live one.
    #
    # D40 (2026-10-01): this block used to read the LIVE `a3_tau_sweep.py` and
    # assert it was a drift.  The D34c cure (`a3d61c3`) had already made that
    # file delegate to the producer, so every one of these seven assertions was
    # RED for a defect that no longer existed — the suite had become a
    # time-bomb pinned to a cured bug (measured: 7/7 pass on the pre-cure
    # bytes, 0/7 on the live corpus).  A gate whose subject the fix REMOVED is
    # not a regression test; it is a countdown.
    #
    # The structural fix is the same one T9 and T11 already use in this file:
    # exercise the MECHANISM on bytes the audit has never seen, so the
    # assertions stay true whatever the live corpus does next.  The fork
    # below is the REAL pre-cure shape (1-arg classifier that cannot see
    # `end_reason`/`api`, a local `aggregate`, a hard-coded verdict), written
    # inline so the fixture cannot rot when the corpus moves on.
    ts = by["a3_tau_sweep.py"]
    SYNTH_FORK = (
        "import json, re\n"
        "MIN_GROUP_N = 5\n"
        "SHA_NEAR_KEYWORD = re.compile(r'done (\\w+)')\n"
        "def classify_outcome(tail):\n"
        "    if SHA_NEAR_KEYWORD.search(tail):\n"
        "        return 'DONE'\n"
        "    return 'OTHER'\n"
        "def aggregate(rows, cap_threshold):\n"
        "    return {'done': sum(1 for r in rows\n"
        "                       if r.get('outcome') == 'DONE')}\n"
        "def verdict(cap, sub, tau):\n"
        "    if cap['n'] == 0:\n"
        "        return 'DEADLINE_UNBOUND(tau=%s, ticks=%s)' % (tau, sub['n'])\n"
        "    if cap['done_rate'] >= sub['done_rate'] * 0.75:\n"
        "        return 'NO_QUALITY_CLIFF(tau=%s)' % tau\n"
        "    return 'QUALITY_COST(tau=%s)' % tau\n"
        "def main():\n"
        "    print(json.dumps({'schema': 'a3-tau-sweep/v1',\n"
        "                      'production': True,\n"
        "                      'verdict': 'ABSTAIN(sample<5)',\n"
        "                      'read_only': True}, indent=2))\n"
        "    return 0\n")
    fork = audit_synth(SYNTH_FORK, "synthetic_fork.py")
    fnames = {f["name"] for f in fork["forks"]}
    check("T4-drift", fork["status"] == "drift", fork["status"])
    check("T4-classify-fork", "classify_outcome" in fnames, fnames)
    check("T4-aggregate-fork", "aggregate" in fnames, fnames)
    # The behavioural core: its 1-arg classifier cannot classify a cap hit at
    # all.  Asserted BEHAVIOURALLY, not by reading the flag — a flag-only
    # assertion is decorative: negating the guard that SETS the flag leaves
    # the test green (proven by the epsilon-code run on this file).
    d = fork["classifier_diff"]
    check("T4-probes-ran", d.get("probes") == len(PROBE_CORPUS), d)
    # On a cap-hit tick the producer names a cap outcome; the fork cannot
    # even reach that branch, so it must disagree on at least one cap probe.
    cap_probes = [x for x in PROBE_CORPUS
                  if x[2] >= p.DEADLINE_TURN]
    cap_diverged = [x for x in d.get("divergences", [])
                    if any(x["probe"] == c[3] for c in cap_probes)]
    check("T4-cap-blind", len(cap_diverged) >= 1,
          f"cap probes={[c[3] for c in cap_probes]} diverged={cap_diverged}")
    # and the fork must NOT reproduce the producer on every probe either
    check("T4-diverges", d.get("divergence_n", 0) >= 1, d)
    # and it fabricates its production verdict
    check("T4-hardcoded", len(fork["hardcoded_verdicts"]) >= 1,
          fork["hardcoded_verdicts"])
    # The fork was MEASURED, not merely filed: an unrunnable classifier used to
    # report `divergences: []`, which reads exactly like "it agreed".  D40
    # measured that shape on the real fork shape (`re.compile` binding) and it
    # is now covered by T12 below; here we pin that the synthetic fork — which
    # carries the same compiled-regex global — actually ran.
    check("T4-measured", fork["classifier_diff"].get("measured") is True,
          fork["classifier_diff"])
    # The SYNTHETIC fork must be recognised as one — and, symmetrically, the
    # file it was modelled on must no longer be.  Without the second half this
    # only proves the audit can still see a fork; it does not prove the cure
    # the cure exists for is still in place.
    check("T4-live-cured", ts["status"] in ("clean", "window")
          and ts["imports_producer"] is True, ts["status"])

    # --- T12: an UNRUNNABLE classifier is never reported as agreement ----
    # D40 (2026-10-01), found by measuring the fix rather than by reading it:
    # both real forks in this family carried `SHA_NEAR_KEYWORD = re.compile(...)`,
    # which `_extract_callable` could not literal-eval, so ALL 13 probes raised
    # and `_classifier_diff` returned `divergences: []` — a value identical to
    # "ran the corpus and agreed with the producer on every probe".  The file
    # was still (correctly) called a drift by the static half, so nothing
    # looked wrong; the BEHAVIOURAL half had simply stopped running.
    #
    # Two halves, both behavioural:
    #   (a) the shape that used to hide now RUNS (re.compile binding supplied),
    #   (b) when it genuinely cannot run, the result says `measured: false`
    #       and a non-empty error count — never a clean empty divergence list.
    re_fork = audit_synth(
        "import re\n"
        "MIN_GROUP_N = 5\n"
        "SHA_NEAR_KEYWORD = re.compile(r'done (\\w+)')\n"
        "def classify_outcome(tail):\n"
        "    if SHA_NEAR_KEYWORD.search(tail):\n"
        "        return 'DONE'\n"
        "    return 'OTHER'\n"
        "def aggregate(rows, cap_threshold):\n"
        "    return {'done': 0}\n", "synthetic_refork.py")
    rd = re_fork["classifier_diff"]
    check("T12-refork-measured", rd.get("measured") is True
          and rd.get("errors", 1) == 0, rd)
    # `probes_executed` must be DERIVED from the run, not a constant: pinning
    # it to the corpus size passed even with the arithmetic removed (measured:
    # 0/11 caught), because the re-fork runs every probe.  Asserted here
    # against the UNMEASURED classifier below, which ran strictly fewer probes
    # than the corpus holds -- so the field has to come from somewhere.
    check("T12-refork-sees-divergence", rd.get("divergence_n", 0) >= 1, rd)
    # And a classifier that genuinely cannot be supplied must be declared
    # unmeasured: a name the extractor cannot bind, referenced at call time.
    opaque = audit_synth(
        "def classify_outcome(tail):\n"
        "    if _UNBINDABLE(tail):\n"
        "        return 'DONE'\n"
        "    return 'OTHER'\n"
        "def aggregate(rows, cap_threshold):\n"
        "    return {'done': 0}\n", "synthetic_opaque.py")
    od = opaque["classifier_diff"]
    check("T12-opaque-declares-unmeasured", od.get("measured") is False
          and od.get("errors", 0) > 0, od)
    check("T12-probes-executed-derived",
          od.get("probes_executed") == len(PROBE_CORPUS)
          - od.get("errors", 0), od)

    # --- T5: the producer's own classifier is the reference behaviour ---
    for tail, er, api, expected in PROBE_CORPUS:
        got = p.classify_outcome(tail, er, api)
        check(f"T5-probe[{expected}]", got == expected, f"got {got}")

    # --- T6: CAP_DELIVERED counts as delivered in the producer -----------
    # (the D34b done_rate bug counted it in the denominator only)
    cap = {"group": "CAPPED", "artifact": True, "outcome": "CAP_DELIVERED",
           "api": 66, "id": "x", "start": 0, "tools": 1, "window": "w"}
    st = p.aggregate([cap])
    check("T6-cap-delivered", st["done"] == 1 and st["done_rate"] == 1.0,
          st)

    # --- T7: a verdict CONSTANT is only ever reported in a consumer, never
    #         in the producer (the producer must measure) ---------------
    check("T7-producer-measures", prod["status"] == "reference"
          and "hardcoded_verdicts" not in prod)

    # --- T8: the audit is read-only -------------------------------------
    check("T8-read-only", rep["read_only"] is True)

    # --- T9: the exemptions are NOT a blanket allowlist -----------------
    # Asserted BEHAVIOURALLY, on synthetic sources: an exemption may cover a
    # shared CONSTANT, never a re-decided RULE.  A synthetic file that both
    # re-declares a producer constant AND re-implements a rule must be
    # reported as a FORK even when its name is exempted.  This is what gives
    # the exemption map teeth — pinning the live outcome instead (T10) left
    #     was green when the map was widened.
    exempt_const_only = audit_synth(
        "import importlib.util\n"
        "p = _p = None\n"
        "STATE_DB = '/somewhere/else.db'\n", "const_only.py")
    check("T9-const-only-not-fork",
          [f["name"] for f in exempt_const_only["forks"]] == ["STATE_DB"],
          exempt_const_only["forks"])

    for exempt_map, tag in ((SIBLING_PREDECESSORS, "sibling"),
                            (INDEPENDENT_SERIES, "independent")):
        fname = next(iter(exempt_map))
        bad = dict(exempt_map)
        bad[fname] = "probe"
        saved = dict(SIBLING_PREDECESSORS if tag == "sibling"
                     else INDEPENDENT_SERIES)
        if tag == "sibling":
            SIBLING_PREDECESSORS.clear()
            SIBLING_PREDECESSORS.update(bad)
        else:
            INDEPENDENT_SERIES.clear()
            INDEPENDENT_SERIES.update(bad)
        try:
            r = audit_synth(
                "def classify_outcome(tail, end_reason, api):\n"
                "    return 'DONE'\n", fname)
            check(f"T9-{tag}-still-forks-a-rule",
                  "classify_outcome" in {f["name"] for f in r["forks"]},
                  r["forks"])
        finally:
            if tag == "sibling":
                SIBLING_PREDECESSORS.clear()
                SIBLING_PREDECESSORS.update(saved)
            else:
                INDEPENDENT_SERIES.clear()
                INDEPENDENT_SERIES.update(saved)
    # the live files behind each exemption must themselves hold no rule fork
    for exempt in (SIBLING_PREDECESSORS, INDEPENDENT_SERIES):
        for fname in exempt:
            f = by.get(fname)
            check("T9-present-" + fname, f is not None)
            if f:
                check("T9-no-rule-fork-" + fname, f["forks"] == [],
                      f["forks"])

    # --- T10: the corpus is currently fork-FREE -------------------------
    # D40: this used to pin `drift_files == {"a3_tau_sweep.py"}` — the exact
    # fork T4 has just cured.  Same time-bomb as T4: the assertion could only
    # ever go from green to red as the cure landed, and it has been red ever
    # since.  The INVARIANT that actually matters is "no UNEXPECTED fork": the
    # named subject is allowed to be a window (that is the cure), any OTHER
    # file turning into a fork is a real regression and must fail.
    drift_files = {d["file"] for d in rep["drift"]}
    check("T10-no-unexpected-fork", drift_files <= {"a3_tau_sweep.py"},
          drift_files)
    # D40: the subset test above is VACUOUS while the corpus is fork-free --
    # `set() <= {anything}` is True, so negating the allowlist to a bogus name
    # still passed (measured: 0/11 caught).  A guard that cannot be seen to
    # bite is a hole, so the SAME rule is re-asserted against a corpus that
    # provably contains an UNEXPECTED fork: the synthetic fork from T4.  This
    # is the D39c lesson (a needle that does not apply is ROT, never a pass)
    # applied to the *content* of the set rather than to a needle.
    synthetic_drift = {fork["file"]} if fork["status"] == "drift" else set()
    check("T10-bites-on-an-unexpected-fork",
          bool(synthetic_drift)
          and not (synthetic_drift <= {"a3_tau_sweep.py"}),
          synthetic_drift)
    # And the cure is real, asserted from the bytes rather than trusted: the
    # named subject delegates to the producer and re-decides nothing.
    check("T10-cure-delegates", ts["imports_producer"] is True
          and ts["forks"] == [], f"imports={ts['imports_producer']} "
          f"forks={ts['forks']}")

    # --- T11: the ALARM-vs-FABRICATION discriminator, tested DIRECTLY ----
    # T10 pins the outcome, but pinning the outcome does not pin the
    # mechanism: the epsilon-code run showed negating `_is_guarded` leaves
    # every test green, because no assertion reads it.  So assert the rule
    # itself on synthetic sources — an alarm branch and a straight-line
    # fabrication, both tiny, both decided by the same helper.
    def synth(src):
        return ast.parse(src).body[0]

    alarm = synth("""
def f(recorded, live):
    if recorded != live:
        return {"verdict": "definition-drift"}
    return 0
""")
    fab = synth("""
def g():
    print({"verdict": "ABSTAIN(sample<5)"})
    return 0
""")
    an = [c for c in ast.walk(alarm)
          if isinstance(c, ast.Constant) and c.value == "definition-drift"]
    fn_ = [c for c in ast.walk(fab)
           if isinstance(c, ast.Constant) and c.value == "ABSTAIN(sample<5)"]
    check("T11-alarm-guarded", bool(an) and _is_guarded(alarm, an[0]))
    check("T11-fabrication-unguarded", bool(fn_)
          and not _is_guarded(fab, fn_[0]))

    for f in fails:
        print(f"FAIL {f}", file=sys.stderr)
    print(f"selftest: {'PASS' if not fails else 'FAIL'} "
          f"({len(fails)} failures, {len(PROBE_CORPUS)} probes)")
    return 1 if fails else 0


def check_report(examples_dir: str = HERE) -> tuple:
    """The scheduled-consumer form.  Returns (rc, lines).

    D41 (2026-10-02): the D34c cure left the audit's own guarantee as a
    statement ABOUT THE CODE — 36 files scanned, `drift: []`, selftest 13/13,
    ε-code 12/12 — with no verb that ever RUNS it.  That is the exact sentence
    the D39c ε-code opens with ("an ε-code nobody runs is not an ε-code"), one
    level down: the instrument was green and unwatched.  Every other watchdog
    in this family ships a `--check` (12 of 36 examples) and a POSIX wrapper in
    ~/.hermes/scripts/; this one had only `main()` with `--selftest`.

    Taxonomy v2 (lib/watchdog.sh §Scope — a GATE keeps its contract, an
    assertion over the audited system may not be downgraded to rc0-silence):

        rc0  silent — the corpus carries no fork
        rc1  ALARM: — a fork landed, or a consumer's classifier could not be
             MEASURED.  The second half is the D40 finding made load-bearing:
             a consumer the extractor cannot execute used to report
             `divergences: []`, indistinguishable from "it ran and agreed".
        rc2  fail-closed — the producer is missing/unimportable, the examples
             directory is absent, or the report cannot be produced at all.
    """
    if not os.path.isdir(examples_dir):
        print("ERROR: examples dir missing", file=sys.stderr)
        return 2, []
    if not os.path.isfile(PRODUCER_PATH):
        print(f"ERROR: producer missing: {PRODUCER_PATH}", file=sys.stderr)
        return 2, []
    try:
        rep = audit_dir(examples_dir)
    except Exception as exc:            # fail-closed, never green-on-crash
        print(f"ERROR: audit crashed: {exc!r}", file=sys.stderr)
        return 2, []

    if not rep.get("files_scanned"):
        # The D28 lesson: an instrument measuring an EMPTY tree reports a
        # perfect score.  Zero files is a broken measurement, not a clean one.
        print("ERROR: 0 files scanned — measurement is vacuous", file=sys.stderr)
        return 2, []

    payload = {
        "schema": "a3-fork-drift-check/v1",
        "files_scanned": rep["files_scanned"],
        "clean": len(rep["clean"]),
        "window": len(rep["window"]),
        "drift": rep["drift"],
        # `unmeasured` = a consumer that DOES define a local classifier whose
        # probes could NOT be executed.  The discriminator matters and the
        # first version of this gate got it backwards: `not_extractable` means
        # the consumer defines NO local `classify_outcome` at all, which is
        # the D34c CURE working (it imports the producer), not a defect.  Only
        # a file that re-declares the classifier AND whose diff came back
        # `measured is not True` is a silent hole — an unrun diff is not an
        # agreement, and `status: drift` already covers the measured case.
        "unmeasured": [
            f["file"] for f in rep["findings"]
            if f.get("classifier_diff", {}).get("status") in ("ok", "probe_errors")
            and f.get("classifier_diff", {}).get("measured") is not True
        ],
        "read_only": rep["read_only"],
    }
    if not payload["drift"] and not payload["unmeasured"]:
        return 0, []                        # honest abstention
    print("ALARM: " + json.dumps(payload, sort_keys=True))
    return 1, [json.dumps(payload, sort_keys=True)]


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--check" in sys.argv:
        rc, _ = check_report()
        return rc
    print(json.dumps(audit_dir(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
