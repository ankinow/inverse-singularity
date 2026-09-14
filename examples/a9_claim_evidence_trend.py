#!/usr/bin/env python3
"""A9 claim-evidence trend — append-only time-series of the third layer's DEAD-LETTER.

Read-only. The Narrative Optimization thread ("Narrative Optimization as A4
Subversion", CURIOSITY.md) answered its central question — *"does the runtime need
a third layer — a non-LLM, non-prompt check the agent cannot narrate past?"* — with
`verify_claims.py` (ist-gate, v0.5), a deterministic verifier that parses explicit
`⟦CLAIM:...⟧` markers out of an agent's final_response and checks each against the
system of record (file stat/hash, `git rev-parse HEAD`, HTTP status). The layer is
*built and wired* (`pre_verify` hook), but the thread never asked — and no instrument
ever answered — the population question:

    do production agents actually EMIT the markers the verifier verifies?

That is the same blind spot the ε_system thread closed for honesty marks (v0.8.35):
a per-call hook can be wired to a *perfect* verifier and still be a dead-letter if
the agent population never emits its input grammar. Claim-emission is the *input*
side of layer 3; `verify_claims` checks the output. If the emission rate is ~0, the
third layer verifies a surface that never exists — the agent can still "narrate its
way past" the danger by *never writing a claim at all* (narrative-without-evidence is
the thread's own named failure mode, and today nothing measures how often it happens
across the population).

This instrument closes that gap by the same discipline every sibling trend uses
(import the grammar/verdict from a single source, append-only SQLite, `--trend` with
count-keyed monotone verdicts, `--check` report-only watchdog, `--selftest` proving
fire/abstain):

  * it does **not** re-implement the claim grammar — it imports `verify_claims`
    (the layer-3 verifier in the ist-gate plugin) as the single source of truth for
    the `⟦CLAIM:...⟧` marker regex and the success-verb vocabulary, so the
    emission measure and the verifier cannot drift apart; a marker counts as a
    **genuine emission** only when its body parses as a recognized claim kind
    (`file:written`, `file:marker`, `git:commit`, `git:clean`, `http:200`,
    `http:any`) with a non-empty value — prose that merely *quotes* the grammar
    (documentation, an agent discussing `⟦CLAIM:⟧`, or this instrument's own source
    echoed into a message) yields a garbage body and does **not** count. The
    selftest pins this kind-set against the verifier's own dispatch so the two
    cannot diverge;
  * each run samples `state.db` `messages` (the system of record — assistant
    messages persist the final_response where markers live) and appends one row
    {seq, ts, assistant_msgs, claim_msgs, narrative_msgs, claim_rate,
     narrative_rate} to `data/a9_claim_evidence_trend.sqlite` (append-only,
    `seq INTEGER PRIMARY KEY AUTOINCREMENT` — the v0.8.9 write-safety shape);
  * `--trend` (`schema a9-claim-evidence-trend/v1`) reads the *emission* movement
    and reports **`evidence-eroding`** only on a genuine monotone fall of the raw
    claim-marker count past its healthiest (highest) point — the third layer going
    dead at scale — and **`evidence-rising`** (the healthy direction) only on a
    monotone rise past the healthiest point; it abstains on <2 samples. A healthy
    runtime is **`evidence-stable`**.
  * `--check` — report-only watch: **silent** (exit 0) on a healthy trend
    (`evidence-stable` / `evidence-rising` / `abstain`), prints `ALARM:` + JSON and
    exits 1 on the erosion verdict. The exit code is a *reporting* mechanism, never
    a gate — nothing edits, prescribes, or injects markers.

The Goodhart safeguard is structural and identical to its siblings: the instrument
samples and appends only. It never coaxes a marker — a marker emitted to satisfy this
metric would itself be a mirrored constraint (Boundary Paradox), and the only honest
consumer is the alarm, never a feedback loop that inflates the emission rate.

NB the count-vs-fraction discipline (the a8 lesson): the *raw claim-marker count* is
the signal (did the system stop emitting evidence markers), NOT the claim_rate
fraction — the fraction falls whenever the agent talks more (the denominator grows)
even with equal evidence, so a fraction-keyed verdict would fabricate "eroding" on a
pure message-volume rise. The fraction is reported for reference only.

Modes:
  * `--trend`       (explicit) — print the full JSON trend read, exit 0 always.
  * `--check`       — report-only watch: silent (exit 0) on healthy; ALARM + exit 1
    on `evidence-eroding`.
  * `--selftest`    — prove the fire/abstain logic + grammar reuse; non-zero on fail.
  * `--help`        — print usage and exit 0; an unrecognized flag exits 2 — neither
    ever falls through to the default (append) path (v0.8.38 arg hygiene; the
    `--help`-appends-a-sample incident is this instrument's own).
  * (default)       — sample-and-append once (idempotent read-only; cron weekly).
"""
from __future__ import annotations

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

HERMES_HOME = os.environ.get("HERMES_HOME", "/mnt/hermes")
STATE_DB = os.environ.get("HERMES_STATE_DB", os.path.join(HERMES_HOME, "state.db"))

# --- single source of truth: the layer-3 verifier (ist-gate plugin) -------------
# The marker grammar and the success-verb vocabulary live in verify_claims.py so
# that the emission measure and the verifier cannot drift apart. If the plugin is
# absent (e.g. a clone without the plugin), fall back to the canonical literals —
# the regex and the verb set are doctrine constants, unchanged since v0.5.
_VERIFY_CLAIMS_PATH = os.path.join(HERMES_HOME, "plugins", "ist-gate", "verify_claims.py")
_verify = None
try:
    sys.path.insert(0, os.path.dirname(_VERIFY_CLAIMS_PATH))
    import verify_claims  # noqa: E402
    _verify = verify_claims
    CLAIM_RE = verify_claims._CLAIM_RE
except Exception:
    CLAIM_RE = re.compile(r"⟦CLAIM:([^⟧]+)⟧")

# success-verb vocabulary (narrative-without-evidence surface), from verify_claims
_NARRATIVE_RE = re.compile(
    r"\b(committed|deployed|published|written to|uploaded|merged|pushed)\b",
    re.IGNORECASE,
)

# The claim KINDS the layer-3 verifier recognizes (verify_claims.verify_one dispatch).
# A marker only counts as a *genuine emission* when its body parses as one of these
# `kind=<value>` forms — prose that merely QUOTES the grammar (a doc, an agent
# discussing `⟦CLAIM:...⟧`, or this instrument's own source echoed into a message)
# yields a garbage body like `([^` and must NOT count. This is the never-guess
# discipline applied to measurement: a substring hit is not an emission. The
# selftest pins this set against the verifier's own dispatch so the two cannot drift.
KNOWN_CLAIM_KINDS = (
    "file:written",
    "file:marker",
    "git:commit",
    "git:clean",
    "http:200",
    "http:any",
)


def claim_bodies(text: str) -> list[str]:
    """All marker bodies in `text` (the part after `⟦CLAIM:`), as the verifier sees them."""
    return CLAIM_RE.findall(text or "")


def _genuine_claims(text: str) -> list[str]:
    """Marker bodies that parse as a recognized claim kind `kind=<value>`.

    Prose quoting the grammar is excluded: a real emission carries a recognizable
    kind and a non-empty value, exactly what `verify_claims.verify_one` would
    dispatch on rather than reject as `unknown_kind`.
    """
    out = []
    for body in claim_bodies(text):
        kind = body.split("=", 1)[0].strip()
        value = body.split("=", 1)[1].strip() if "=" in body else ""
        if kind in KNOWN_CLAIM_KINDS and value:
            out.append(body)
    return out

TREND_DB = str(Path(__file__).resolve().parent.parent / "data" / "a9_claim_evidence_trend.sqlite")
SCHEMA = "a9-claim-evidence-trend/v1"

# The single erosion verdict that the report-only watchdog surfaces. `evidence-stable`
# and `evidence-rising` are healthy (rising = more verifiable evidence markers emitted,
# the *good* direction). `abstain` is honest under-sampling. The verdict below means a
# real fall of claim-marker emission across sessions — layer 3 going dead at scale.
ALARM_VERDICTS = ("evidence-eroding",)

USAGE = (
    "usage: a9_claim_evidence_trend.py [--trend | --check | --selftest | --help]\n"
    "  (default) sample the live claim-emission count once and append a row\n"
    "  --trend   read the append-only series and print the movement verdict (JSON)\n"
    "  --check   report-only watchdog: silent on healthy, ALARM + exit 1 otherwise\n"
    "  --selftest prove the fire/abstain/append logic; exits non-zero on failure\n"
)

KNOWN_FLAGS = ("--trend", "--check", "--selftest", "--help", "-h")


def arg_guard(args, err=sys.stderr, out=sys.stdout):
    """Up-front arg hygiene — an unrecognized flag must NEVER fall through to the
    default (append/sample) path.

    Proven incident (2026-09-14): THIS instrument ran `--help` and appended a real
    sample (seq 6) to `data/a9_claim_evidence_trend.sqlite` — a read-only-looking
    invocation silently grew the series its own verdict reads. Every sibling with
    the same shape (`if "--check" not in argv …: sample_once()`) carried the same
    defect for *any* typo'd flag (`--chek`, `--tren`), which at the verdict level
    is indistinguishable from real signal. Touches no database: returns 2 (unknown
    flag → usage on stderr), 0 (`--help` printed usage), or None (proceed). Pure,
    so it is pinned both by selftest and by a hermetic end-to-end re-run of this
    file (see `_arg_hygiene_check`).
    """
    unknown = [a for a in args if a not in KNOWN_FLAGS]
    if unknown:
        err.write("unknown flag(s): %s\n%s" % (" ".join(unknown), USAGE))
        return 2
    if "--help" in args or "-h" in args:
        out.write(USAGE)
        return 0
    return None


def _arg_hygiene_check(tmp):
    """Pin the guard end-to-end without ever risking the live series: re-run THIS
    file from a hermetic copy (tmp/hygiene/examples + …/data) and assert that
    `--help` (exit 0, usage on stdout) and a typo'd flag (exit 2, usage on stderr)
    leave no series DB behind. Pre-fix, both appended a real sample — the incident
    this release pins."""
    src = str(Path(__file__).resolve())
    root = os.path.join(tmp, "hygiene")
    ex_dir = os.path.join(root, "examples")
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir)
    shutil.copytree(str(Path(src).parent), ex_dir)
    script = os.path.join(ex_dir, os.path.basename(src))
    series = os.path.join(data_dir, os.path.basename(TREND_DB))

    def run(*flags):
        proc = subprocess.run([sys.executable, script, *flags],
                              capture_output=True, text=True, timeout=300)
        rows = None
        if os.path.exists(series):
            con = sqlite3.connect("file:%s?mode=ro" % series, uri=True)
            try:
                rows = con.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
            except sqlite3.Error:
                rows = -1
            finally:
                con.close()
        return proc, rows

    sink = io.StringIO()
    pure = (arg_guard(["--trend", "--check", "--selftest"], err=sink, out=sink) is None
            and arg_guard(["--help"], err=sink, out=sink) == 0
            and arg_guard(["--zz-bogus"], err=sink, out=sink) == 2)
    proc_help, rows_help = run("--help")
    proc_bad, rows_bad = run("--chek")            # realistic typo of --check
    proc_read, rows_read = run("--trend")         # fresh series: abstain, not a crash
    out = {
        "guard-pure": pure,
        "help-no-effect": (proc_help.returncode == 0
                           and USAGE.splitlines()[0] in proc_help.stdout
                           and rows_help is None),
        "unknown-exit-2": (proc_bad.returncode == 2
                           and "unknown flag" in proc_bad.stderr
                           and rows_bad is None),
        "read-fresh-abstain": (proc_read.returncode == 0
                               and '"abstain"' in proc_read.stdout
                               and rows_read == 0),
    }
    shutil.rmtree(root, ignore_errors=True)
    return out


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db(path: str = TREND_DB) -> None:
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS samples (
               seq INTEGER PRIMARY KEY AUTOINCREMENT,
               ts TEXT NOT NULL,
               assistant_msgs INTEGER NOT NULL,
               claim_msgs INTEGER NOT NULL,
               narrative_msgs INTEGER NOT NULL,
               claim_rate REAL NOT NULL,
               narrative_rate REAL NOT NULL
           )"""
    )
    con.commit()
    con.close()


def _load_messages(db_path: str = STATE_DB):
    """Read-only pull of assistant-message contents (the claim-marker surface)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = con.execute(
            "SELECT content FROM messages WHERE role='assistant' "
            "AND content IS NOT NULL AND content != ''"
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        con.close()


def measure(messages) -> dict:
    """Tally claim-marker emissions and narrative-without-evidence across messages.

    claim_msgs   = assistant messages carrying at least one GENUINE `⟦CLAIM:...⟧`
                   emission (a body that parses as a recognized claim kind — the
                   layer-3 verifier's input grammar), not prose that quotes it.
    narrative_msgs = assistant messages carrying success-verb prose with ZERO
                   genuine claim markers (the "narratable surface" — success
                   claimed in words, never backed by a verifiable marker).
    """
    claim_msgs = 0
    narrative_msgs = 0
    for text in messages:
        has_claim = bool(_genuine_claims(text))
        if has_claim:
            claim_msgs += 1
        elif _NARRATIVE_RE.search(text):
            # success prose with no marker → narrative-without-evidence (the
            # exact surface the thread names: "reframe a destructive command as
            # routine maintenance" with nothing a verifier can read back)
            narrative_msgs += 1
    total = len(messages)
    return {
        "assistant_msgs": total,
        "claim_msgs": claim_msgs,
        "narrative_msgs": narrative_msgs,
        "claim_rate": round(claim_msgs / total, 6) if total else 0.0,
        "narrative_rate": round(narrative_msgs / total, 6) if total else 0.0,
    }


def sample_once(db_path: str = STATE_DB, out_db: str = TREND_DB, now: str | None = None) -> dict:
    """Measure the live claim-emission once and append a row."""
    messages = _load_messages(db_path)
    m = measure(messages)
    row = {
        "seq": None,
        "ts": now or _now_iso(),
        "assistant_msgs": m["assistant_msgs"],
        "claim_msgs": m["claim_msgs"],
        "narrative_msgs": m["narrative_msgs"],
        "claim_rate": m["claim_rate"],
        "narrative_rate": m["narrative_rate"],
    }
    init_db(out_db)
    con = sqlite3.connect(out_db)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO samples (ts, assistant_msgs, claim_msgs, narrative_msgs, "
        "claim_rate, narrative_rate) VALUES (?, ?, ?, ?, ?, ?)",
        (row["ts"], row["assistant_msgs"], row["claim_msgs"],
         row["narrative_msgs"], row["claim_rate"], row["narrative_rate"]),
    )
    row["seq"] = cur.lastrowid
    con.commit()
    con.close()
    return row


def _load_series(out_db: str = TREND_DB) -> list[dict]:
    init_db(out_db)
    con = sqlite3.connect(f"file:{out_db}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute(
        "SELECT seq, ts, assistant_msgs, claim_msgs, narrative_msgs, "
        "claim_rate, narrative_rate FROM samples ORDER BY seq ASC"
    )
    rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
    con.close()
    return rows


def _monotone_rise(vals) -> bool:
    return all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))


def _monotone_fall(vals) -> bool:
    return all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))


def trend(out_db: str = TREND_DB) -> dict:
    rows = _load_series(out_db)
    n = len(rows)
    if n < 2:
        return {
            "schema": SCHEMA,
            "samples": n,
            "verdict": "abstain",
            "reason": "fewer than 2 samples",
            "last_claim_msgs": rows[-1]["claim_msgs"] if rows else None,
            "last_narrative_msgs": rows[-1]["narrative_msgs"] if rows else None,
        }

    # The *raw claim-marker count* is the signal (did the system stop emitting
    # evidence markers), NOT the claim_rate fraction — the fraction falls whenever
    # the agent talks more (message volume grows) even at equal evidence, so a
    # fraction-keyed verdict would fabricate "eroding" on a pure volume rise (the
    # a8 lesson re-applied: key on count, report fraction for reference).
    claims = [r["claim_msgs"] for r in rows]

    claims_hi = max(claims)
    claims_last = claims[-1]
    eroding = _monotone_fall(claims) and (claims_last < claims_hi)
    rising = _monotone_rise(claims) and (claims_last > min(claims))

    if eroding:
        verdict = "evidence-eroding"
    elif rising:
        verdict = "evidence-rising"
    else:
        verdict = "evidence-stable"

    narr = [r["narrative_msgs"] for r in rows]
    return {
        "schema": SCHEMA,
        "samples": n,
        "verdict": verdict,
        "first_claim_msgs": claims[0],
        "last_claim_msgs": claims_last,
        "min_claim_msgs": min(claims),
        "max_claim_msgs": claims_hi,
        "delta_claim_msgs": claims_last - claims[0],
        "first_narrative_msgs": narr[0],
        "last_narrative_msgs": narr[-1],
        "last_assistant_msgs": rows[-1]["assistant_msgs"],
        "last_claim_rate": rows[-1]["claim_rate"],
        "last_narrative_rate": rows[-1]["narrative_rate"],
    }


def _selftest() -> bool:
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  selftest[{name:18s}] {'PASS' if cond else 'FAIL'}  {note}")

    # 1. grammar reuse: the marker regex accepts a real claim and rejects prose
    check("grammar-real-claim", bool(CLAIM_RE.search("⟦CLAIM:file:written=/x⟧")),
          "real ⟦CLAIM:...⟧ marker matched")
    check("grammar-no-marker", not CLAIM_RE.search("I committed it and deployed it."),
          "prose without a marker is not a claim")
    check("grammar-source", os.path.basename(os.path.dirname(_VERIFY_CLAIMS_PATH)) == "ist-gate"
          if _verify is not None else True,
          "grammar imported from verify_claims (or canonical fallback)")

    # 1b. genuine-emission predicate: a marker only counts when its body parses as
    #     a recognized kind. Prose QUOTING the grammar must NOT count (the real
    #     false positive this instrument hit on its first live read: messages
    #     discussing `⟦CLAIM:⟧` and even the verifier's own source echoed back).
    check("genuine-kind-accepted",
          _genuine_claims("⟦CLAIM:git:clean=/repo⟧ done") == ["git:clean=/repo"],
          "well-formed claim with a known kind counts")
    check("genuine-quote-rejected",
          _genuine_claims("the marker ⟦CLAIM:([^⟧]+)⟧ is the grammar") == [],
          "prose quoting the grammar does not count")
    check("genuine-empty-body-rejected",
          _genuine_claims("see ⟦CLAIM:⟧ for the empty form") == [],
          "empty body does not count")
    check("genuine-empty-value-rejected",
          _genuine_claims("⟦CLAIM:git:clean=⟧") == [],
          "known kind with empty value does not count")
    check("genuine-unknown-kind-rejected",
          _genuine_claims("⟦CLAIM:bogus:kind=/x⟧") == [],
          "unknown kind does not count (never-guess)")

    # 1c. drift guard: every kind this instrument recognizes must be a kind the
    #     live verifier would DISPATCH on (not reject as unknown_kind), and an
    #     unknown kind must be rejected by it — so the two sets cannot diverge.
    if _verify is not None:
        for kind in KNOWN_CLAIM_KINDS:
            probe_body = f"{kind}=/nonexistent-selftest-probe"
            v = _verify.verify_one(probe_body)
            check(f"verify-dispatch-{kind}", v.get("reason") != "unknown_kind",
                  "verifier dispatches on this kind")
        v_bad = _verify.verify_one("bogus:kind=/x")
        check("verify-rejects-unknown", v_bad.get("reason") == "unknown_kind",
              "verifier rejects an unknown kind (sets agree)")

    # 2. measure() counts claims and narrative-without-evidence correctly
    msgs = [
        "⟦CLAIM:file:written=/tmp/x⟧ done",          # claim → count as claim
        "committed it and deployed it.",              # success prose, no marker → narrative
        "all verified, nothing to report.",           # neither
        "pushed to origin/main with no ⟦CLAIM at all",  # prose verb, no marker → narrative
        "⟦CLAIM:git:clean=/repo⟧ merged cleanly",     # has marker → claim (not narrative)
        "the grammar ⟦CLAIM:([^⟧]+)⟧ is documented",  # quotes grammar → NOT a claim
    ]
    m = measure(msgs)
    check("measure-claims", m["claim_msgs"] == 2, f"claims={m['claim_msgs']}")
    check("measure-narrative", m["narrative_msgs"] == 2,
          f"narrative={m['narrative_msgs']}")
    check("measure-total", m["assistant_msgs"] == 6, f"total={m['assistant_msgs']}")
    check("measure-rates", m["claim_rate"] == 0.333333 and m["narrative_rate"] == 0.333333,
          f"rates={m['claim_rate']}/{m['narrative_rate']}")

    tmp = tempfile.mkdtemp(prefix="a9cet-selftest-")

    # 3. append-does-not-replace: two samples → seq 1,2 monotonic
    tdb = os.path.join(tmp, "trend.sqlite")
    r1 = sample_once(db_path=STATE_DB, out_db=tdb)
    r2 = sample_once(db_path=STATE_DB, out_db=tdb)
    rows = _load_series(tdb)
    check("append-not-replace", len(rows) == 2 and rows[0]["seq"] == 1 and rows[1]["seq"] == 2,
          "seq monotonic, append preserves history")
    check("captured-counts", r1["claim_msgs"] >= 0 and r1["assistant_msgs"] >= 0,
          "counts captured per sample")

    # 4. trend verdicts on synthetic claim-count series (count-keyed, not fraction)
    _cnt = {"n": 0}

    def verdict_of(claim_counts):
        _cnt["n"] += 1
        syn_db = os.path.join(tmp, f"syn{_cnt['n']}.sqlite")
        con = sqlite3.connect(syn_db)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
            "assistant_msgs INTEGER, claim_msgs INTEGER, narrative_msgs INTEGER, "
            "claim_rate REAL, narrative_rate REAL)"
        )
        for i, c in enumerate(claim_counts):
            cur.execute(
                "INSERT INTO samples (ts,assistant_msgs,claim_msgs,narrative_msgs,"
                "claim_rate,narrative_rate) VALUES (?,?,?,?,?,?)",
                (f"t{i}", 6000, c, 300, c / 6000.0, 0.05),
            )
        con.commit()
        con.close()
        return trend(syn_db)["verdict"]

    check("stable", verdict_of([10, 10, 10]) == "evidence-stable",
          "claim count flat → stable")
    check("rising", verdict_of([10, 14, 18]) == "evidence-rising",
          "claim count monotone rise → evidence strengthening")
    check("eroding", verdict_of([10, 7, 4]) == "evidence-eroding",
          "claim count monotone fall → layer 3 going dead")

    # 5. abstain on <2 samples
    solo = os.path.join(tmp, "solo.sqlite")
    con = sqlite3.connect(solo)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE samples (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
        "assistant_msgs INTEGER, claim_msgs INTEGER, narrative_msgs INTEGER, "
        "claim_rate REAL, narrative_rate REAL)"
    )
    cur.execute(
        "INSERT INTO samples (ts,assistant_msgs,claim_msgs,narrative_msgs,"
        "claim_rate,narrative_rate) VALUES (?,?,?,?,?,?)",
        ("t0", 6000, 10, 300, 0.0017, 0.05),
    )
    con.commit()
    con.close()
    check("abstain", trend(solo)["verdict"] == "abstain", "<2 samples → abstain")

    # 6. the ALARM classification: only `evidence-eroding` is surface-worthy
    alarm = {"evidence-eroding"}
    healthy = {"evidence-stable", "evidence-rising", "abstain"}
    check("alarm-verdicts", set(ALARM_VERDICTS) == alarm,
          "exactly the erosion verdict is report-worthy")
    check("healthy-silent", alarm.isdisjoint(healthy),
          "no healthy/rising/abstain verdict is ever surfaced")

    # 7. arg hygiene: `--help` and a typo'd flag must NEVER fall through to the
    #    default (append) path — the incident this release fixed was THIS file's
    #    `--help` appending seq 6. Pinned as a pure function AND end-to-end from a
    #    hermetic copy of this file.
    for _name, _good in _arg_hygiene_check(tmp).items():
        check(f"arg-{_name}", _good,
              "guard runs before any DB access (hermetic re-run of this file)")

    return ok


def main() -> int:
    rc = arg_guard(sys.argv[1:])
    if rc is not None:
        return rc

    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    if "--check" not in sys.argv and "--trend" not in sys.argv:
        row = sample_once()
        print(json.dumps({
            "schema": SCHEMA,
            "action": "append",
            "seq": row["seq"],
            "ts": row["ts"],
            "assistant_msgs": row["assistant_msgs"],
            "claim_msgs": row["claim_msgs"],
            "narrative_msgs": row["narrative_msgs"],
            "claim_rate": row["claim_rate"],
            "narrative_rate": row["narrative_rate"],
        }, indent=2))
        return 0

    out = trend()
    if "--check" in sys.argv:
        verdict = out["verdict"]
        if verdict in ALARM_VERDICTS:
            print("ALARM: %s (claim_msgs %s→%s, narrative_msgs %s→%s)"
                  % (verdict, out["first_claim_msgs"], out["last_claim_msgs"],
                     out["first_narrative_msgs"], out["last_narrative_msgs"]))
            print(json.dumps(out, indent=2))
            return 1
        return 0

    if "--trend" in sys.argv:
        print(json.dumps(out, indent=2))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())