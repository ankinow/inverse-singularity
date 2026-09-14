#!/usr/bin/env python3
"""A10 Goodhart audit — is the κ/Q metric family still diagnostic, or has it bent behavior?

The CURIOSITY thread "κ Proliferation" (Midday dispatch, 2026-06-13) named the one
hazard no instrument of the family yet audits:

    "The Q time-series is vulnerable to Goodhart drift. The moment Q shifts from
     diagnostic to prescriptive (a decision is made *because* the metric moved),
     the metric has captured the agent. Proposed safeguard: Q must be read-only —
     flag thresholds, never trigger actions. Open question: can a read-only metric
     stay read-only, or does signal availability inevitably bend behavior?
     Testable: run the time-series silently for a cycle, then audit whether any
     decision would have differed without it."

Every instrument since v0.7.7 preserves the safeguard *structurally* — it samples
and appends only, and the watchdogs print an ALARM and exit; nothing prunes, edits
config, or gates. What was never measured is the *behavioral* half: does the
availability of the metric actually bend a decision recorded in the runtime's own
history? This audit closes that gap with the family's discipline (read-only,
stdlib-only, zero deps, selftest-pinned), over two surfaces:

  1. DECISION SURFACE (diary, metric era >= 2026-09-11 — when the first κ
     instrument shipped). Every decision mark (`!Dc:`/`!Dm:`/`⊗RES:`/`⊗Er:`/
     `⊗RCA:`) is scanned for *prescriptive use*: a metric READING (Q_eff/Q_raw,
     κ_raw/κ_eff, a family verdict such as `collapse` / `eroding` / `SELF-BLOAT` /
     `*-paradox` / `*-dead-letter`, or a κ=/Q= number) co-occurring with a
     system-changing ACTION (prune/remove/archive/disable/reduce/config set/…).
     Negated actions ("não podar", "never prunes") are not flagged — the audit
     asks whether a change *was made*, never whether someone said not to. The
     counterfactual "would the decision have differed without the metric?" is
     approximated by the only auditable proxy in the record: a decision that cites
     a metric reading as its reason for a change.

  2. CONSUMER SURFACE (the `~/.hermes/scripts` wrappers that invoke any κ/Q
     instrument). A consumer that mutates state (config writes, cron edits, file
     removal, prune/archive) would make the metric prescriptive *by construction*.
     Sampler bookkeeping (appending one sample to its own series) is not a
     mutation of the system and is never flagged.

Verdicts:
  read-only-preserved        0 prescriptive decisions AND 0 mutating consumers.
  prescriptive-use-detected  >=1 decision cites a metric reading for a change.
  consumer-mutation-detected >=1 consumer script mutates state.
  both-detected              both surfaces fired.

Modes:
  (default) audit the live surfaces once and append one row to
            `data/a10_goodhart_audit.sqlite` (append-only, `seq` AUTOINCREMENT).
  --trend   read the append-only series and print the movement JSON; the `ever_*`
            flags make a past capture permanent in the read (the record cannot
            un-happen), per the family's never-edit-the-series rule.
  --check   report-only watchdog: silent (exit 0) when the live audit and every
            historical sample are clean; `ALARM:` + JSON + exit 1 when either
            surface shows a capture; exit 2 fail-closed on an unreadable surface.
  --selftest prove each fire/abstain path (synthetic diary + synthetic consumers).
  --help    usage; an unrecognized flag exits 2 — neither ever falls through to
            the default (append) path (v0.8.38 arg hygiene).

Read-only throughout: the audit never edits the diary, the scripts, or any config.
The series it appends is the audit's own bookkeeping; the metric family itself is
untouched.
"""

import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")
SCRIPTS_DIR = os.environ.get("A10_SCRIPTS_DIR", str(Path.home() / ".hermes" / "scripts"))
METRIC_ERA = os.environ.get("A10_METRIC_ERA", "2026-09-11")
TREND_DB = str(Path(__file__).resolve().parent.parent / "data" / "a10_goodhart_audit.sqlite")
SCHEMA = "a10-goodhart-audit/v1"

# Instrument basenames whose consumer wrappers form the CONSUMER SURFACE. A script
# is a consumer iff its text references any of these (no hardcoded wrapper list —
# a new wrapper or a renamed one is picked up automatically).
INSTRUMENTS = (
    "kappa_proliferation_timeseries", "axiom_joint_trend",
    "a7_boundary_trend", "a7_boundary_probe", "a8_epsilon_system_trend",
    "a9_claim_evidence_trend", "a4_action_typing_trend", "a4_action_typing",
    "epsilon_code_trend", "curiosity_kappa_trend", "curiosity_kappa",
    "crate_identity_check", "fingerprint_parity_check", "plugin_identity_check",
    "a5_constraint_provenance",
)

# Decision marks whose unit is audited. `!Dc:`/`!Dm:`/`⊗RES:` are decisions and
# resolutions; `⊗Er:`/`⊗RCA:` are honest-error/root-cause notes that can also carry
# a decision ("erro X → mudei Y"). All five are scanned; the precision gate is the
# reading+action pair, not the marker family.
DECISION_MARKERS = ("!Dc:", "!Dm:", "⊗RES:", "⊗Er:", "⊗RCA:")

# A metric READING (a verdict or a number from the family), never the bare concept:
# "the κ Proliferation thread" is a topic mention, "κ_raw=3323" is a reading.
RE_READING = re.compile(
    r"("
    r"Q_eff|Q_raw|q_eff|q_raw|"
    r"κ_raw|κ_eff|"
    r"κ\s*[:=]\s*\d|Q\s*[:=]\s*\d|"
    r"SELF-BLOAT|self-bloat|"
    r"collapse|eroding|worsening|"
    r"sovereignty-paradox|producer-dead-letter|evidence-dead-letter|"
    r"signal-eroding|boundary-widening|code-regressing|compress-paradox|"
    r"dead-letter|bloated_bytes|unknown_frac"
    r")",
    re.IGNORECASE,
)

# A system-changing ACTION, EN + PT stems (the audit's question is whether a
# *change* was made because of the metric, so the verbs are change verbs).
RE_ACTION = re.compile(
    r"("
    r"prune|pod(?:ar|ei|ou|ando|ado|amos|em)|"
    r"remove|remov|delete|delet|"
    r"archive|arquiv|disable|desativ|"
    r"trim|shrink|reduce|reduzir|"
    r"purge|expurg|eliminar|apagar|limpar|"
    r"decommission|"
    r"config set|config unset"
    r")",
    re.IGNORECASE,
)

# Negation immediately before an action ≤16 chars back: "não podar", "never prunes",
# "sem remover". A negated action is NOT a change and must never be flagged.
RE_NEG = re.compile(r"(?:^|\W)(?:não|nao|never|nunca|sem|nem|not|no)\W*$", re.IGNORECASE)

# Mutating commands that make a consumer prescriptive by construction. Append-only
# sampler bookkeeping is out of scope by design (no DB writes are listed here).
MUTATION_PATTERNS = (
    ("config-write", re.compile(r"\bhermes\s+config\s+(?:set|unset)\b")),
    ("cron-mutation", re.compile(r"\bhermes\s+cron\s+(?:add|remove|edit|pause|resume)\b")),
    ("file-removal", re.compile(r"\brm\b\s+\S")),
    ("file-move", re.compile(r"\bmv\b\s+\S")),
    ("in-place-edit", re.compile(r"\bsed\s+-i\b")),
    ("process-kill", re.compile(r"\b(?:pkill|kill)\b")),
    ("prune", re.compile(r"\bprune\b")),
    ("archive", re.compile(r"\barchive\b")),
    ("apply", re.compile(r"--apply\b")),
)

USAGE = (
    "usage: a10_goodhart_audit.py [--trend | --check | --selftest | --help]\n"
    "  (default) audit the live decision + consumer surfaces once and append a row\n"
    "  --trend   read the append-only audit series and print the movement (JSON)\n"
    "  --check   report-only watchdog: silent when clean, ALARM + exit 1 otherwise\n"
    "  --selftest prove the fire/abstain/append logic; exits non-zero on failure\n"
)

KNOWN_FLAGS = ("--trend", "--check", "--selftest", "--help", "-h")


def arg_guard(args, err=sys.stderr, out=sys.stdout):
    """Up-front arg hygiene — an unrecognized flag must NEVER fall through to the
    default (audit+append) path.

    Same contract as the v0.8.38 family fix (proven incident: a9 `--help` appended
    a real sample). Touches no database: returns 2 (unknown flag → usage on
    stderr), 0 (`--help` printed usage), or None (the caller may proceed).
    """
    unknown = [a for a in args if a not in KNOWN_FLAGS]
    if unknown:
        err.write("unknown flag(s): %s\n%s" % (" ".join(unknown), USAGE))
        return 2
    if "--help" in args or "-h" in args:
        out.write(USAGE)
        return 0
    return None


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _diary_files(diary, era_start):
    """Diary files in the metric era (ISO date names, string-compared)."""
    out = []
    if not os.path.isdir(diary):
        return out
    for name in sorted(os.listdir(diary)):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", name)
        if m and m.group(1) >= era_start:
            out.append(name)
    return out


def decision_units(diary=DIARY, era_start=METRIC_ERA):
    """Yield (file, line_no, text) for every decision mark plus its indented
    continuation lines. A new bullet at column 0 starts a new statement and is not
    absorbed — decisions wrap by indentation in the diary, not across bullets."""
    units = []
    for name in _diary_files(diary, era_start):
        try:
            with open(os.path.join(diary, name), encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        i = 0
        while i < len(lines):
            s = lines[i]
            if any(marker in s for marker in DECISION_MARKERS):
                buf = [s]
                j = i + 1
                while j < len(lines) and lines[j][:1] in (" ", "\t") and lines[j].strip():
                    buf.append(lines[j])
                    j += 1
                units.append((name, i + 1, "\n".join(buf)))
                i = j
            else:
                i += 1
    return units


def _first_action(text):
    """First non-negated action match in a decision unit, else None."""
    for m in RE_ACTION.finditer(text):
        prefix = text[max(0, m.start() - 16):m.start()]
        if RE_NEG.search(prefix):
            continue
        return m
    return None


def audit_decisions(units):
    """Prescriptive-use findings: a metric reading + a non-negated change action."""
    findings = []
    for name, lineno, text in units:
        rm = RE_READING.search(text)
        if not rm:
            continue
        am = _first_action(text)
        if not am:
            continue
        findings.append({
            "file": name,
            "line": lineno,
            "reading": rm.group(0).strip(),
            "action": am.group(0).strip(),
            "excerpt": " ".join(text.split())[:220],
        })
    return findings


def find_consumers(scripts_dir=SCRIPTS_DIR):
    """Scripts (.sh/.py) whose text references any metric-family instrument."""
    if not os.path.isdir(scripts_dir):
        return []
    out = []
    for name in sorted(os.listdir(scripts_dir)):
        if not (name.endswith(".sh") or name.endswith(".py")):
            continue
        path = os.path.join(scripts_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        if any(inst in text for inst in INSTRUMENTS):
            out.append(path)
    return out


def audit_consumers(paths):
    """Flag non-comment lines of consumer scripts that mutate state."""
    findings = []
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError as exc:
            findings.append({"script": os.path.basename(path), "line": 0,
                             "pattern": "unreadable", "excerpt": str(exc)[:140]})
            continue
        for i, raw in enumerate(lines, 1):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            for label, pat in MUTATION_PATTERNS:
                if pat.search(s):
                    findings.append({"script": os.path.basename(path), "line": i,
                                     "pattern": label, "excerpt": s[:200]})
                    break
    return findings


def classify(prescriptive, mutating):
    if prescriptive and mutating:
        return "both-detected"
    if prescriptive:
        return "prescriptive-use-detected"
    if mutating:
        return "consumer-mutation-detected"
    return "read-only-preserved"


def run_audit(diary=DIARY, scripts_dir=SCRIPTS_DIR, era=METRIC_ERA):
    """Read-only audit of both surfaces. Returns the full result dict."""
    files = _diary_files(diary, era)
    units = decision_units(diary, era)
    dec_findings = audit_decisions(units)
    consumers = find_consumers(scripts_dir)
    cons_findings = audit_consumers(consumers)
    reading_units = sum(1 for _n, _l, t in units if RE_READING.search(t))
    return {
        "schema": SCHEMA,
        "diary": diary,
        "metric_era": era,
        "scripts_dir": scripts_dir,
        "diary_files": len(files),
        "decisions": len(units),
        "reading_mentions": reading_units,
        "prescriptive": dec_findings,
        "consumers": [os.path.basename(p) for p in consumers],
        "mutating": cons_findings,
        "verdict": classify(len(dec_findings), len(cons_findings)),
    }


def init_db(path=TREND_DB):
    con = sqlite3.connect(path)
    con.execute(
        """CREATE TABLE IF NOT EXISTS samples (
               seq INTEGER PRIMARY KEY AUTOINCREMENT,
               ts TEXT NOT NULL,
               diary_files INTEGER NOT NULL,
               decisions INTEGER NOT NULL,
               reading_mentions INTEGER NOT NULL,
               prescriptive INTEGER NOT NULL,
               consumers INTEGER NOT NULL,
               mutating INTEGER NOT NULL,
               verdict TEXT NOT NULL
           )"""
    )
    con.commit()
    con.close()


def append_sample(result, out_db=TREND_DB, now=None):
    init_db(out_db)
    verdict = result.get("verdict") or classify(
        len(result["prescriptive"]), len(result["mutating"]))
    con = sqlite3.connect(out_db)
    cur = con.execute(
        "INSERT INTO samples (ts, diary_files, decisions, reading_mentions, "
        "prescriptive, consumers, mutating, verdict) VALUES (?,?,?,?,?,?,?,?)",
        (now or _now_iso(), result["diary_files"], result["decisions"],
         result["reading_mentions"], len(result["prescriptive"]),
         len(result["consumers"]), len(result["mutating"]), verdict),
    )
    seq = cur.lastrowid
    con.commit()
    con.close()
    return seq


def read_series(path=TREND_DB):
    """Read the append-only series; [] when it does not exist yet."""
    if not os.path.exists(path):
        return []
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    try:
        rows = con.execute(
            "SELECT seq, ts, diary_files, decisions, reading_mentions, "
            "prescriptive, consumers, mutating, verdict FROM samples ORDER BY seq"
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        con.close()
    return [
        {"seq": r[0], "ts": r[1], "diary_files": r[2], "decisions": r[3],
         "reading_mentions": r[4], "prescriptive": r[5], "consumers": r[6],
         "mutating": r[7], "verdict": r[8]}
        for r in rows
    ]


def trend_payload(path=TREND_DB):
    """The movement read: ever-flags make a past capture permanent."""
    series = read_series(path)
    ever_p = any(r["prescriptive"] > 0 for r in series)
    ever_m = any(r["mutating"] > 0 for r in series)
    if not series:
        return {"schema": SCHEMA, "samples": 0, "verdict": "abstain",
                "ever_prescriptive": False, "ever_consumer_mutation": False,
                "series": []}
    if ever_p and ever_m:
        verdict = "both-detected"
    elif ever_p:
        verdict = "prescriptive-use-detected"
    elif ever_m:
        verdict = "consumer-mutation-detected"
    else:
        verdict = "read-only-preserved"
    return {
        "schema": SCHEMA,
        "samples": len(series),
        "verdict": verdict,
        "ever_prescriptive": ever_p,
        "ever_consumer_mutation": ever_m,
        "latest": series[-1],
        "series": series,
    }


def check_problems(result, series):
    """Everything a report-only watchdog should surface. Never acts on it."""
    problems = []
    if result["prescriptive"]:
        problems.append("prescriptive-use-detected: %d decision(s) cite a metric "
                        "reading as the reason for a change" % len(result["prescriptive"]))
    if result["mutating"]:
        problems.append("consumer-mutation-detected: %d mutating consumer "
                        "line(s)" % len(result["mutating"]))
    if any(r["prescriptive"] > 0 for r in series):
        problems.append("historical-prescriptive-use: a past sample recorded >=1 "
                        "prescriptive decision (the record cannot un-happen)")
    if any(r["mutating"] > 0 for r in series):
        problems.append("historical-consumer-mutation: a past sample recorded a "
                        "mutating consumer")
    return problems


def _parse_units(text):
    """Parse a synthetic in-memory diary through the same unit logic."""
    lines = text.splitlines()
    units = []
    i = 0
    while i < len(lines):
        s = lines[i]
        if any(marker in s for marker in DECISION_MARKERS):
            buf = [s]
            j = i + 1
            while j < len(lines) and lines[j][:1] in (" ", "\t") and lines[j].strip():
                buf.append(lines[j])
                j += 1
            units.append(("synthetic.md", i + 1, "\n".join(buf)))
            i = j
        else:
            i += 1
    return units


def _arg_hygiene_check(tmp):
    """Pin the guard end-to-end from a hermetic copy: `--help` (exit 0, usage) and
    a typo'd flag (exit 2) must leave no series DB behind; the default must append
    exactly one row. Pre-fix (v0.8.38 shape) both fell through to the append path."""
    src = str(Path(__file__).resolve())
    root = os.path.join(tmp, "hygiene")
    ex_dir = os.path.join(root, "examples")
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir)
    shutil.copytree(str(Path(src).parent), ex_dir)
    script = os.path.join(ex_dir, os.path.basename(src))
    series = os.path.join(data_dir, os.path.basename(TREND_DB))

    def rows():
        if not os.path.exists(series):
            return None
        con = sqlite3.connect("file:%s?mode=ro" % series, uri=True)
        try:
            return con.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
        except sqlite3.Error:
            return -1
        finally:
            con.close()

    def run(*flags):
        env = dict(os.environ)
        env["HERMES_DIARY"] = os.path.join(root, "diary")
        env["A10_SCRIPTS_DIR"] = os.path.join(root, "scripts")
        os.makedirs(env["HERMES_DIARY"], exist_ok=True)
        os.makedirs(env["A10_SCRIPTS_DIR"], exist_ok=True)
        return subprocess.run([sys.executable, script, *flags],
                              capture_output=True, text=True, timeout=300,
                              env=env)

    proc_help = run("--help")
    rows_after_help = rows()
    proc_bad = run("--chek")            # realistic typo of --check
    rows_after_bad = rows()
    proc_ok = run()                     # default: audit + append must work
    rows_after_ok = rows()

    out = {
        "help-no-effect": (proc_help.returncode == 0
                           and USAGE.splitlines()[0] in proc_help.stdout
                           and rows_after_help is None),
        "unknown-exit-2": (proc_bad.returncode == 2
                           and "unknown flag" in proc_bad.stderr
                           and rows_after_bad is None),
        "default-appends-once": (proc_ok.returncode == 0
                                 and rows_after_ok == 1),
    }
    shutil.rmtree(root, ignore_errors=True)
    return out


def _selftest():
    ok = True

    def check(name, cond, note):
        nonlocal ok
        ok &= bool(cond)
        print("  selftest[%-22s] %s  %s" % (name, "PASS" if cond else "FAIL", note))

    # --- decision-surface logic (pure, synthetic) -----------------------------
    t_flag_pt = "!Dc: Q_eff caiu 5x; podei 200 skills para reduzir κ."
    t_neg = "!Dc: κ alto observado; não podar nada (read-only)."
    t_no_action = "!Dc: instrumento κ implementado read-only."
    t_flag_en = "!Dc: collapse detected; prune the skill set to reduce κ."
    t_action_only = "!Dc: removi um diretório stale sem relação com a métrica."
    t_wrapped = ("!Dc: SELF-BLOAT confirmado no CURIOSITY.md,\n"
                 "  então arquivei as threads resolved para reduzir κ.")
    cases = [
        ("pt-reading+action", t_flag_pt, 1),
        ("negation-not-flagged", t_neg, 0),
        ("no-action-not-flagged", t_no_action, 0),
        ("en-reading+action", t_flag_en, 1),
        ("action-no-reading", t_action_only, 0),
        ("wrapped-continuation", t_wrapped, 1),
    ]
    for name, text, want in cases:
        got = len(audit_decisions(_parse_units(text)))
        check(name, got == want, "findings=%d (want %d)" % (got, want))

    # a bare concept mention of the thread is not a reading
    check("concept-not-reading",
          len(audit_decisions(_parse_units("!Dc: thread κ Proliferation segue aberto."))) == 0,
          "thread name alone is not a metric reading")

    # --- consumer-surface logic (temp dirs, zero network) ---------------------
    tmp = tempfile.mkdtemp(prefix="a10-selftest-")
    try:
        sdir = os.path.join(tmp, "scripts")
        os.makedirs(sdir)
        clean = os.path.join(sdir, "clean-watchdog.sh")
        with open(clean, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\n"
                     "# report-only; never prunes skills or edits config\n"
                     "python3 kappa_proliferation_timeseries.py --check\n"
                     "printf '%s\\n' \"$OUT\" >&2\n"
                     "exit $?\n")
        bad = os.path.join(sdir, "bad-consumer.sh")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\n"
                     "if ! OUT=$(python3 kappa_proliferation_timeseries.py --check); then\n"
                     "  hermes config set agent.max_turns 999\n"
                     "fi\n")

        consumers = find_consumers(sdir)
        check("consumer-discovery", len(consumers) == 2,
              "referencing wrappers found: %d (want 2)" % len(consumers))
        found = audit_consumers([clean])
        check("clean-consumer", found == [], "no mutation in a report-only wrapper")
        found = audit_consumers([bad])
        check("mutating-consumer", len(found) == 1 and found[0]["pattern"] == "config-write",
              "config-write flagged on the mutating wrapper")

        # verdict classification
        check("verdict-clean", classify(0, 0) == "read-only-preserved", "0/0 → preserved")
        check("verdict-presc", classify(1, 0) == "prescriptive-use-detected", "1/0 → prescriptive")
        check("verdict-cons", classify(0, 1) == "consumer-mutation-detected", "0/1 → consumer")
        check("verdict-both", classify(1, 1) == "both-detected", "1/1 → both")

        # series: append-only + ever-flags + abstain
        db = os.path.join(tmp, "a10.sqlite")
        clean_result = {"diary_files": 4, "decisions": 40, "reading_mentions": 3,
                        "prescriptive": [], "consumers": ["a.sh"], "mutating": []}
        bad_result = dict(clean_result, prescriptive=[{"x": 1}])
        append_sample(clean_result, out_db=db, now="t1")
        append_sample(clean_result, out_db=db, now="t2")
        check("series-append-only", len(read_series(db)) == 2,
              "two appends, seq monotonic")
        check("trend-preserved", trend_payload(db)["verdict"] == "read-only-preserved",
              "clean samples → read-only-preserved")
        append_sample(bad_result, out_db=db, now="t3")
        tp = trend_payload(db)
        check("trend-ever-flag", tp["verdict"] == "prescriptive-use-detected"
              and tp["ever_prescriptive"] is True,
              "a past capture is permanent in the read")
        empty = os.path.join(tmp, "missing.sqlite")
        check("trend-abstain", trend_payload(empty)["verdict"] == "abstain",
              "no series → abstain, not a crash")

        # check_problems surfaces both a live and a historical capture
        probs = check_problems(bad_result, read_series(db))
        check("check-surfaces-live", any("prescriptive-use-detected" in p for p in probs),
              "live prescriptive finding surfaces")
        probs_clean = check_problems(clean_result, read_series(db))
        check("check-surfaces-history", any("historical-prescriptive" in p for p in probs_clean),
              "historical capture still surfaces on a clean live read")

        # --- arg hygiene, end-to-end from a hermetic copy of this file --------
        for name, good in _arg_hygiene_check(tmp).items():
            check("arg-" + name, good,
                  "guard runs before any DB access (hermetic re-run of this file)")
    finally:
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

    if "--check" in sys.argv:
        result = run_audit()
        series = read_series()
        problems = check_problems(result, series)
        if problems:
            print("ALARM: " + "; ".join(problems))
            print(json.dumps({"schema": SCHEMA, "problems": problems,
                              "audit": result, "series": series}, indent=2))
            sys.exit(1)
        # Clean (or abstaining history): silent, exit 0.
        sys.exit(0)

    if "--trend" in sys.argv:
        print(json.dumps(trend_payload(), indent=2))
        return

    # default: audit + append (the sampler row; never a decision)
    result = run_audit()
    seq = append_sample(result)
    print(json.dumps({
        "schema": SCHEMA,
        "action": "append",
        "seq": seq,
        "ts": _now_iso(),
        "diary_files": result["diary_files"],
        "decisions": result["decisions"],
        "reading_mentions": result["reading_mentions"],
        "prescriptive": len(result["prescriptive"]),
        "consumers": len(result["consumers"]),
        "mutating": len(result["mutating"]),
        "verdict": result["verdict"],
    }, indent=2))


if __name__ == "__main__":
    main()
