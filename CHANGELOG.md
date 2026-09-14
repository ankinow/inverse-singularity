# Changelog — NEXUS V3.1.0-edge

**Inverse Singularity Theory · NEXUS_V3.0_KERNEL**

> *"The framework must evolve or it is dead."* — Article IV, Perpetual Evolution

---

## v0.8.39 — 2026-09-14 — the joint reader extended to the SEVEN faces: the cross-face contradictions that were structurally invisible (`sovereignty-paradox` / `producer-dead-letter` / `evidence-dead-letter`)

The joint synthesis (`axiom_joint_trend.py`, v0.8.21) was built when the runtime had exactly three trend series — ε_code UNKNOWN%, κ/Q, CURIOSITY self-bloat — and it read those three faces at once, which was the whole point: it is the only place the *relative* drift of the two compressible terms (`compress-paradox`, `kappa-and-eps-collapse`) is visible. But four newer series have since each grown a verdict and a Monday cron of their own: the a7 boundary (`boundary-widening` / `code-regressing` / `both-worsening`, v0.8.33/0.8.34), a8 ε_system (`sovereignty-eroding`, v0.8.35), a9 claim emission (`evidence-eroding`, v0.8.36) and a4 typed intent (`signal-eroding` / `collapse-detected`, v0.8.37). The joint never learned their names — and since the joint's job is *contradiction between faces*, exactly the new contradictions stayed invisible:

* **ε_code `improving` + ε_system `sovereignty-eroding`** — the Boundary Paradox read across two faces: the compression that the trend celebrates is being paid for with the sovereignty residue the ε thread says must be protected. The three-face reader called that state **`compress-coherent`** by construction (it never looked at ε_system).
* **κ `stable` + a4 `signal-eroding`** — the `⊗S:` producer dying. Every κ-over-φ curve is computed from the blocks that producer writes, so its death silently degrades *all* of those readings while the aggregates still read flat.
* **κ `stable` + a9 `evidence-eroding`** — the layer-3 verifier's input going to zero at scale: a perfect, correctly-wired, non-LLM check fed by nobody.

This release extends the joint to all seven faces by the family's own discipline — **import each sibling's surface, zero re-implementation of any measure** (a7/a8/a9/a4 `trend()`; κ and self-κ `_load_rows` + `compute_trend`). New contradiction verdicts `sovereignty-paradox`, `producer-dead-letter`, `evidence-dead-letter`, resolved in priority order (collapse → sovereignty-paradox → compress-paradox → producer-dead-letter → evidence-dead-letter → self-bloat → compress-coherent → stable) so an alarm can never hide behind another alarm. Abstention is now **per series**, which is the honest form at seven faces: a contradiction whose legs are below 2 samples is listed under `unevaluable` (with the sparse series named) and can never fire — it is never folded into "healthy" — while the headline `abstain` is reserved for the two compressible-term faces (ε_code, κ) being unreadable, when the joint genuinely has no headline to give. The detail block carries the leg verdicts *and* their reference numbers; when `sovereignty-paradox` fires, `boundary_context` rides along from the a7 edge face so the read says which side moved. `ALARM_VERDICTS` grows to five; `_check` is now a testable body (rc 0 silent on the four healthy verdicts, `ALARM:` line + rc 1 on the five alarms). Schema stays `axiom-joint-trend/v1` — the change is additive (new fields, new verdict values; every previous field keeps its meaning).

Rode along, from the v0.8.38 lesson: the joint gains the same **`arg_guard`**. Its `--check` is only ever seen through a wrapper, so a typo'd `--chek` previously fell through to the default read, exited 0 and **silently disabled the alarm** — the same class of self-inflicted blind spot as the a9 `--help` append, one level up (the alarm path, not the series).

**First live read of all seven faces at once (2026-09-14; samples ε_code 3, κ 7, self-κ 3, boundary 4, ε_system 2, claims 6, typed 4):** verdicts `improving` / `stable` / `stable` / `boundary-stable` / `sovereignty-stable` / `evidence-stable` / `signal-stable` → joint **`compress-coherent`**, `--check` silent rc 0, no `unevaluable` entries. The reader that can now *see* all three new contradictions sees none of them — and the pre-existing `compress-coherent` reading survives, now with seven faces' worth of evidence behind it instead of three.

Selftest **33/33**: the seven sibling surfaces imported; the pure predicate per contradiction (incl. the priority pin — an alarm never hides behind another alarm); the two abstention regimes (per-series `unevaluable`; headline `abstain` listing every sparse face); **end-to-end on hermetic synthetic series** — a seven-DB world seeded per contradiction through the *real* imported readers (healthy control → `compress-coherent`; honesty falling → `sovereignty-paradox` with the boundary context; typed blocks falling → `producer-dead-letter`; claim emission falling → `evidence-dead-letter`; κ collapsing → `compress-paradox`; both compressible terms drifting → `kappa-and-eps-collapse`; self-κ bloating → `self-bloat`; a one-sample face → `abstain`; a sparse ε_system → the paradox *unevaluable*, not healthy); the alarm/`--check` contract (rc 0 silent for every healthy verdict, rc 1 + `ALARM:` for every alarm); the live read; and the arg hygiene pinned end-to-end from a hermetic copy (`--help` rc 0, `--chek` rc 2, both leaving no series DB behind). The scheduler was re-verified too: the wrapper (`~/.hermes/scripts/ist-axiom-joint-watchdog.sh`) documents the seven faces and five verdicts, and its propagation contract was proven by DI (healthy stub → rc 0 silent; alarm stub → `ALARM:` line + rc 1; crashing stub → rc 2 fail-closed), with the real instrument silent rc 0; cron `6e3bb938efc3` (Mon 09:47 — after all five samplers, 09:17–09:21) re-run clean. Scope: Python-only, zero Rust.

---

## v0.8.38 — 2026-09-14 — arg hygiene across the trend-reader series: `--help` and typo'd flags no longer run the append path (`a7` / `a8` / `a9` / `epsilon_code_trend`)

The v0.8.37 entry closed with a note that was itself a measured defect, not a caveat: the a9 instrument's `--help` **appended a real sample** (`data/a9_claim_evidence_trend.sqlite` seq 6, 2026-09-14T08:04:47Z) — a read-only-looking invocation silently grew the series its own verdict reads. The shape was not a9's alone: every sibling written before the a4 instrument carried `if "--check" not in argv …: sample_once()`, so *any* unrecognized token fell through to the default append path — a wrapper running `--chek`/`--tren` would add samples that the count-keyed verdicts cannot distinguish from signal, exactly the class of self-inflicted measurement error this series exists to catch (κ definitional break, ε-probe taxonomy drift, producer↔vendored classifier fork).

Fix = the a4 pattern promoted to the family: a pure `arg_guard(args)` runs **before any DB access** and returns `2` (unknown flag → `unknown flag(s): …` + USAGE on stderr), `0` (`--help`/`-h` → USAGE on stdout), or `None` (proceed). Per-instrument `USAGE` documents the modes. Applied to the four append-default instruments: `a7_boundary_trend.py`, `a8_epsilon_system_trend.py`, `a9_claim_evidence_trend.py`, `epsilon_code_trend.py`. Scope stated honestly: the read-only siblings' defaults are side-effect-free, and the argparse instruments (`kappa_proliferation_timeseries`, `curiosity_kappa_trend`, `curiosity_lint`, `fingerprint_parity_check`) already fail closed with exit 2 on unknown flags — so the append-default four were the whole exposure.

Rode along in the same pass (a4's documented guarantee, silently absent in the four): `_load_series` now calls `init_db` first, so a **first-ever read on a fresh series is an abstain, not a crash** — pre-fix, `a7 … --help`/`--trend` tracebacked (`no such table: samples`) on an unseeded series, and a fresh clone's read modes died before ever bootstrapping. Each instrument's `--selftest` gained four pinned cases: the pure guard contract, plus three **hermetic end-to-end re-runs of the file itself** from a copy (`tmp/hygiene/examples` + `…/data`) asserting `--help` → rc 0 with no series DB created, a typo'd flag → rc 2 with no series DB created, and `--trend` on a fresh series → rc 0 `abstain` with zero rows. Negative controls proven, not asserted: pre-fix, those same hermetic runs appended a row (a7 3 → 4 on a seeded copy; a8/a9/ε 0 → 1).

Live evidence (2026-09-14): `--help` rc 0 and a typo'd flag rc 2 leave the four production series **unchanged** (a7 3 rows, a8 2, a9 6, ε 3 — before == after), while every sanctioned path still works — `--trend` verdicts `boundary-stable` / `sovereignty-stable` / `evidence-stable` / `improving`, the three `--check` watchdogs rc 0 silent through their cron wrappers, and the a7 sampler wrapper appending a real sample (3 → 4) through the untouched default path. The spurious a9 row (seq 6) is **left in place**: append-only series are never edited, and the count-keyed verdict is unaffected. Selftests: a7 **18/18**, a8 **17/17**, a9 **31/31**, ε **10/10** (each +4); `py_compile` clean across all 27 `examples/*.py`.

## v0.8.37 — 2026-09-14 — the typed intent curve goes LIVE and gets its clock (`a4_action_typing_trend.py`)

The κ Proliferation thread's central question — *"can you measure the point where adding a new capability decreases Q?"* — reached its densest form in two moves: `a3_dense_phi.py` (v0.7.8) broke the sparse-residue resolution wall with a tool-histogram φ proxy and returned a **NULL** (high-κ sessions keep executing), and that null named its own blocker — density cannot separate *verification* from genuine *mutation*. `theory/action-typing.md` + `a4_action_typing.py` (v0.7.9) closed that with a LOGGING-DOCTRINE instrument: per-block intent markers (`⊗S:mutation`/`⊗S:observe`) and a mutation-rate curve bucketed at median κ. It shipped **ABSTAINing** — production typed coverage was 0%, because a doctrine with no producer is prose. The producer shipped with `session-scribe` v1.1.0 (2026-08-25: one `⊗S:` line appended after every `>T:` work-block), and the typed signal then **accumulated silently** — the instrument's own forward-only sentence ("once coverage clears 15% with ≥30 typed sessions this ABSTAIN turns into the defensible curve") was a condition no clock watched, and a producer regression (the ⊗S: stream going dead — the exact dead-letter shape v0.8.36 measured for the layer-3 claim grammar) would be invisible in a point-in-time run.

This release closes both halves of that residue. **(1) The measure got a single source of truth:** `a4_action_typing.py` now exposes an importable `analyze(sessions)` (tallies + normalized `curve_state`: `no-signal | no-typed | mislabel-abstain | abstain | no-collapse | collapse-detected`), so a trend reader can never re-implement — and therefore never drift from — the curve. The refactor is proven **byte-identical**: the full console output hashes `87d48618c21a108c99d2ff86ee1964c4bd20fdabc72d146f90b45d54f9e342b1` before and after, and a vestigial `+= 0` no-op that injected a phantom `⊗S` key into every session's tool histogram was dropped in the same pass. **(2) The signal got a clock:** `examples/a4_action_typing_trend.py` (stdlib, zero-dep, read-only) follows the identical sibling discipline — it imports `parse_diary`/`analyze`, appends one row {seq, ts, files, sessions, typed_sessions, blocks_typed, blocks_inferred, blocks_unknown, coverage, mislabels, curve_state, mut_low, rho, ratio} per sample to `data/a4_action_typing_trend.sqlite` (append-only, `seq INTEGER PRIMARY KEY AUTOINCREMENT` — the v0.8.9 write-safety shape), and `--trend` (`schema a4-action-typing-trend/v1`) reports **`signal-eroding`** only on a genuine monotone fall of the typed block count past its healthiest point (the producer dying at scale) and **`signal-rising`** on a monotone rise, else `signal-stable`; abstains <2. The verdict is keyed on the **count**, never the fraction — coverage = typed/total falls whenever the diary grows faster than the producer, the same compressible mis-read the κ, boundary, ε_system and claim trend readers each caught. `files` rides along per sample as the *confounder made visible*: diary retention can lower a cumulative count benignly, so an erosion read is attributable rather than asserted.

**The transition FINDING — measured live on the real diary (2026-09-14, 202 sessions / 33 files): typed coverage 30.1% (floor 15%), 124 typed-carrying sessions (bar 30), 3,259 typed blocks, 0 mislabels → the typed curve computes for the first time and answers the thread's central question: `NO ACTION-INTENT COLLAPSE (typed)` [mut_low=0.14, ρ=+0.286, ratio=0.69].** High-κ sessions do not retreat into verification-only execution — the dense-φ null (v0.7.8) survives its strongest test, now on *recorded intent* rather than tool-kind inference. Nothing observed that transition until this tick: the forward-only gate cleared silently as the producer accumulated, which is precisely why the gate needed a trend instead of a sentence.

`--check` is the scheduled-consumer form: silent (exit 0) on `signal-stable`/`signal-rising`/`abstain` with no curve detection; `ALARM:` + JSON + exit 1 on **`signal-eroding`** (the ⊗S: producer going dead at scale — the instrument's input dying) *and* on a latest-sample **`collapse-detected`** (the thread's falsifiable claim firing on live data). The exit code is a *reporting* mechanism, never a gate — nothing edits, injects markers, or prescribes (a marker emitted to satisfy this metric would itself be a mirrored constraint, per the Boundary Paradox). Backed by a weekly no-agent cron pair in the Monday IST band, after the a9 pair: sampler `3a2f52fe5f56` (Mon 09:21) and watchdog `b2f11af5f5b5` (Mon 09:38) via `~/.hermes/scripts/a4-action-typing-trend-{weekly-sampler,watchdog}.sh` (POSIX sh, silent on healthy, fail-closed rc 2); both `hermes cron run` → "Ran now: succeeded", and the live series stands at 4 samples (`signal-stable`).

Selftest **19/19** (single-source imports, hermetic synthetic-diary sample, append-not-replace with monotonic seq, the four movement verdicts, abstain, the `analyze`↔curve-state bridge on synthetic collapse/flat/small samples, and the alarm contract). Negative controls proven, not asserted: an eroding series and a `collapse-detected` series each return rc 1 with the `ALARM:` line, every healthy state returns rc 0 silent, and the wrapper propagates rc 1 (alarm) / rc 2 (instrument crash) through DI stubs. Arg hygiene is strict in the new instrument — unknown flags exit 2 and `--help` prints usage **without** side effects; note for a future pass: the a9 instrument's `--help` currently *appends a sample* (recorded as a follow-up item, not fixed here).

---

## v0.8.36 — 2026-09-14 — the third layer's DEAD-LETTER measured: `a9_claim_evidence_trend.py` (claim-emission across the population)

The Narrative Optimization thread ("Narrative Optimization as A4 Subversion", CURIOSITY.md line 196) built the third layer — `verify_claims.py` (ist-gate v0.5), a deterministic non-LLM verifier — and wired it into `pre_verify` (v0.5 built 2026-08-24). But the thread never asked, and no instrument ever answered, the *population* question: **do production agents actually EMIT the `⟦CLAIM:…⟧` markers the verifier verifies?** A per-call hook can be wired to a *perfect* verifier and still be a dead-letter if the agent population never emits its input grammar. Claim-emission is the *input* side of layer 3; `verify_claims` checks the output. If emission ≈ 0, the third layer verifies a surface that never exists — the agent can still "narrate its way past" the danger by *never writing a claim at all* (narrative-without-evidence, the thread's own named failure mode, happens at scale and nothing measured how often).

This release closes that gap by the identical sibling discipline (single-source import, append-only SQLite, count-keyed monotone verdicts, `--check` report-only watchdog, `--selftest` proving fire/abstain): `examples/a9_claim_evidence_trend.py` (stdlib, zero-dep, read-only) **imports** `verify_claims` from the ist-gate plugin as the single source of the claim grammar (`_CLAIM_RE`) and the success-verb vocabulary (the narrative surface), then scans the live Hermes `state.db` for assistant messages carrying text and classifies each as **claim-bearing** (has a `⟦CLAIM:…⟧` marker that parses as a *recognized claim kind* with a non-empty value) vs **narrative-only** (success verbs like "committed/deployed/pushed/merged" with zero verifiable markers). Each sample appends one row (`seq AUTOINCREMENT`) to `data/a9_claim_evidence_trend.sqlite`; `--trend` (`schema a9-claim-evidence-trend/v1`) reports **`evidence-eroding`** only on a genuine monotone fall of the claim count past its healthiest point — layer 3 going dead across the population — and **`evidence-rising`** on a monotone rise; abstains <2. `--check` is the scheduled-consumer form (silent on stable/rising/abstain; `ALARM:` + exit 1 on erosion). The verdict is keyed on the **count**, never the fraction — a growing message volume would dilute the fraction and fabricate erosion for pure typing (the same compressible mis-read the κ thread, boundary trend, and ε_system trend each caught).

**The instrument's own first live read produced the finding, and then corrected itself (the ε_code pattern applied to the measure).** The first draft counted any `⟦CLAIM:…⟧` substring; against the live `state.db` it reported **2 claim-marked messages** — and both were *false positives*: prose **quoting the grammar** (`⟦CLAIM:...⟧` written inside a discussion, and the verifier's own regex literal `([^` echoed back into a message). A marker only counts as a genuine emission when its body parses as a recognized kind (`file:written`, `file:marker`, `git:commit`, `git:clean`, `http:200`, `http:any`) with a non-empty value — the never-guess discipline applied to measurement: a substring hit is not an emission. The predicate is now pinned in `--selftest` against the verifier's **own dispatch** (every recognized kind must be dispatched on by `verify_claims.verify_one`, and an unknown kind must be rejected), so the measure and the verifier cannot drift apart. Because the corrected predicate is *incommensurable* with the pre-fix one, the development series was reset rather than trended across the redefinition — the same "a redefinition is not a collapse" discipline the κ-trend reader (v0.8.24) adopted.

**First live sample under the corrected predicate (2026-09-14, real state.db): 0 genuine claim-marker emissions across 1,929 text-bearing assistant messages, vs 90 narrative-only messages (`claim_rate` 0.0, `narrative_rate` 0.0467) → `evidence-stable` (2 samples, both 0).** The finding is sharper than the asymmetry the first read suggested: the third layer's input grammar is emitted **zero** times across the population, while success is asserted in prose — with nothing a verifier can read back — in ~4.7% of messages. The verifier is not merely under-fed; on the current record it is a **dead-letter**: a perfect, correctly wired, non-LLM check whose input never arrives, so the thread's feared surface ("the agent narrates its way past") is not hypothetical but the *measured status quo*. Selftest 27/27 (grammar reuse, the genuine-emission predicate incl. quote/empty-body/empty-value/unknown-kind rejections, the verifier drift guard, count-keyed trend verdicts, append-not-replace, abstain, and the alarm contract); Goodhart safeguard is structural and identical to its siblings (samples-and-appends only, never coaxes a marker — a marker emitted to satisfy this metric would itself be a mirrored constraint per the Boundary Paradox). Backed by a weekly no-agent sampler (`20 9 * * 1`) + watchdog (`37 9 * * 1`, in the Monday IST band after the a8 watchdog and before the 09:47 joint watchdog) via `~/.hermes/scripts/a9-claim-evidence-trend-{weekly-sampler,watchdog}.sh` (POSIX sh, silent on healthy, fail-closed rc 2).

---

## v0.8.35 — 2026-09-14 — ε_system (the sovereignty term) gains its scheduled consumer (`a8_epsilon_system_trend.py`)

The ε thread's deepest face — *"does ε = 0 violate A4, or does it mean the system was never sovereign to begin with?"* — was answered statically by the a6 probe (v0.8.11: ε_system > 0 ⇒ a recording, could-have-done-otherwise system, so A4 holds). But a point-in-time verdict leaves the *temporal* danger the thread itself names: ε_system is "the residue of REAL work the agent chose to record," and their absence at scale is the SS7 transparency gap — a production agent that stops emitting `⊗Er:`/`!Dc:`/`⊗RES:` would let ε_system silently drift toward zero across sessions. That drift is the exact A4 collapse the thread asks about, and no instrument tended it: ε_code has its trend (`epsilon_code_trend.py`, v0.8.20), the boundary has its trend (`a7_boundary_trend.py`, v0.8.33) — but the sovereignty term itself, the one the thread says must be *protected*, was only ever read at a point.

This release closes that gap by the identical sibling discipline: `examples/a8_epsilon_system_trend.py` (stdlib, zero-dep, read-only) **imports** `parse_dir`/`compute`/`verdict` from `a6_epsilon_probe` (single source, no drift), appends one row per sample to `data/a8_epsilon_system_trend.sqlite` (append-only `seq AUTOINCREMENT`), and `--trend` (`schema a8-epsilon-system-trend/v1`) reads the *honesty count* (the raw ε_system numerator) and reports **`sovereignty-eroding`** only on a genuine monotone fall past the healthiest (highest) point — the SS7 under-report going to scale — and **`sovereignty-rising`** (healthy) only on a monotone rise; abstains <2. `--check` is the scheduled-consumer form (silent on `sovereignty-stable`/`rising`/`abstain`; `ALARM:` + exit 1 on the erosion verdict). The verdict is keyed on the **count**, not the fraction — ε_system = honesty/typed, so the fraction falls whenever the agent types more (denominator grows) even with equal residue; keying on the fraction would fabricate erosion for a pure typing-volume increase (the same compressible mis-read the κ thread and boundary trend each caught). Backed by a weekly no-agent sampler (`19 9 * * 1`) + watchdog (`36 9 * * 1`, after the sampler, before the 09:47 joint watchdog) via `~/.hermes/scripts/a8-epsilon-system-trend-{weekly-sampler,watchdog}.sh`.

**First live sample (2026-09-14, 7,141 typed actions): honesty 140, ε_system 0.0196, ε_code 1.0648 → SOVEREIGN-CODE** — the sovereignty term is now *tended* (its movement toward zero becomes a visible `eroding` signal), not just read at a point. Selftest 13/13; the Goodhart safeguard is structural and identical to its siblings: the instrument samples-and-appends only, never coaxes a mark (a mark emitted to satisfy this metric would itself be a mirrored constraint per the Boundary Paradox), so the only honest consumer is the alarm, never the feedback loop.

---

## v0.8.34 — 2026-09-14 — a7 boundary trend gains its scheduled consumer (`--check`)

v0.8.33 shipped the *temporal* reader for the ε_code↔ε_system boundary (`a7_boundary_trend.py`) — the instrument that trends whether the undecidable floor moves — but it was wired to nothing: a pure append-only series whose verdicts could only be read if a human happened to run `--trend`. That is the exact gap every sibling fail-closed instrument closes with a cron (a5 `--check` → `56fba415da49`; crate_identity → `1eaf2b71253c`; joint `--check` → `6e3bb938efc3`; fingerprint parity → `03a92b245a88`). The `boundary-stable`/`boundary-widening` verdict set was silently accumulating samples with no scheduled consumer to surface a movement.

This release closes the consumer gap without touching the measure. `a7_boundary_trend.py` gains a **`--check`** mode (the same report-only discipline as its siblings): silent (exit 0) on a healthy trend (`boundary-stable` / `boundary-receding` / `abstain`), and prints a compact `ALARM:` line + JSON and exits 1 on the three movement verdicts that mean a real regression — `boundary-widening` (the undecidable floor monotone-rising past its healthiest low), `code-regressing` (ε_code monotone-rising past its low — the classifier's compressible gap re-opens), `both-worsening` (the two together). The exit code is a *reporting* mechanism (so a cron delivery surfaces the movement), NOT a gate — nothing edits, prunes, or changes config; the Goodhart safeguard (sample-and-append only, ε_boundary > 0 is the A4 wall's signature, never optimized away) holds exactly. Backed by a weekly no-agent cron (`a7-boundary-trend-watchdog`, `9a4e1f678c32`, Mon 09:35 — after the 09:18 boundary sampler `7cd5096194de` and before the 09:47 joint watchdog) via `~/.hermes/scripts/a7-boundary-trend-watchdog.sh` (POSIX sh, silent on healthy, fail-closed rc 2 on unreadable runtime).

Proof executed 2026-09-14: `--selftest` 14/14 (12 prior + `alarm-verdicts` pinning exactly the three regression verdicts as report-worthy + `healthy-silent` pinning that no healthy/abstain verdict is ever surfaced); `--check` silent rc 0 on the live series (3 samples, `boundary-stable`, ε_code 2.33%/ε_boundary 1.51% flat); `--trend` unchanged (still prints the full JSON read); `py_compile` clean; scope Python-only (no Rust change); cargo test 40/40, clippy clean (2 pre-existing literal-bool warnings), crate identity aligned 0.8.34. This closes the ε-thread's *scheduled-visibility* residue: the boundary's movement is now not just readable, but watched on a clock — a silent re-opening of ε_code or a drift of the floor becomes an ALARM delivery rather than an unnoticed trend row.

---

## v0.8.33 — 2026-09-14 — a7 boundary trend: the ε_code↔ε_system boundary is now watched over time, not just measured at a point

v0.8.29 shipped the a7 *probe* — the first instrument to **measure** the boundary between ε_code and ε_system, answering the thread's static question ("is the boundary itself an ε?") with "partially — a compressible 2.33% surface on an irreducible 1.51% floor." But a point-in-time MIXED-BOUNDARY verdict is silent on the thread's *temporal* face: **does the boundary move?** A single snapshot cannot distinguish a genuinely irreducible floor (ε_boundary flat across time — the A4 never-guess wall, fixed because never-guess is invariant) from a *moving target* (ε_boundary monotone-rising — either the classifier over-extended and its guesses now flow to the floor, or the runtime's command surface genuinely drifted toward opaque-driver shapes); nor can it catch a silent regrowth of ε_code re-opening the gap the v0.8.12/0.8.17/0.8.18 compressions closed.

`examples/a7_boundary_trend.py` (stdlib, zero-deps, read-only) is that temporal reader, built by the same append-only discipline as its siblings (`kappa_proliferation_timeseries.py --trend`, `epsilon_code_trend.py`, `curiosity_kappa_trend.py`): it **does not re-implement the measure** — it imports `measure`/`bin_unknown`/`verdict` from `a7_boundary_probe` (single source of truth, no drift); each run appends one row `{seq, ts, total, code, boundary, code_frac, boundary_frac, boundary_ratio, verdict}` to `data/a7_boundary_trend.sqlite` (append-only `seq AUTOINCREMENT`); and `--trend` (schema `a7-boundary-trend/v1`) reports **five verdicts** from the series — `boundary-widening` (the floor monotone-rising past its healthiest low = the undecidable floor moves), `code-regressing` (ε_code monotone-rising past its low = the classifier's compressible gap re-opens), `both-worsening` (the two flags together), `boundary-receding` (the floor falls = the healthy direction, the classifier proving more intent recoverable than the prior floor assumed), and `boundary-stable` (else) — abstaining below 2 samples. Goodhart is structural and identical to its siblings: sample-and-append only, no gate, no decision path, no prescriptive consumer; ε_boundary > 0 is the signature of the A4 wall, not a defect to optimize away. The trend *reads its movement*, never acts on it.

**First live samples (2026-09-14, 5,504 commands): seq 1–2 both MIXED-BOUNDARY** — ε_code 2.33%, ε_boundary 1.51%, boundary_ratio 0.6484, flat — which is exactly the "floor is fixed because never-guess is invariant" prediction, now trackable rather than asserted. Selftest 12/12 (single-source import resolution, append-not-replace with monotonic seq, verdict-captured per sample, all five trend verdicts on synthetic series, abstain <2). The ε-thread's temporal face is now answered the same way its spatial face was: measured, not inflated into a claim on two samples. `py_compile` clean; scope Python-only (no Rust change); cargo test 40/40, clippy clean, crate identity re-aligned 0.8.33.

## v0.8.32 — 2026-09-13 — a3 quality-delta classifier: completion-language coverage + distinct DEADLINE_UNBOUND null

The v0.8.7 instrument (`a3_quality_delta.py`) was shipped to close the *last* open caveat of the A3-deadline thread — "exact-cap ≠ optimal τ (no quality-delta measure yet)" — and it **ABSTAINED** in production (verdict `ABSTAIN(sample<5)`), leaving that caveat nominally intact for ~3 weeks. Re-running on the accumulated τ=66 windows (17 dev-continuo ticks, 2026-09-11→13) surfaced **two ε_code gaps in the instrument itself**, of the same kind the action-typing classifier keeps compressing, both of which had to be closed before the verdict could be trusted:

1. **Completion-language coverage gap — `done_rate` was a false under-measurement.** `classify_outcome` matched only the literal `[done` backlog marker, but the dev-continuo loop writes `[done ...]` to BACKLOG.md and *does not echo it* into the final assistant tail. Real completed ticks instead carry completion *language* ("the item is complete", "item concluído", "task is complete") plus a verified commit SHA — and the classifier filed 13 of 17 genuinely-completed ticks as `OTHER` (residual). Result was `done_rate=0.188`, a ~4× under-count, which would have poisoned any capped-vs-subcap quality comparison. Fix: a narrowed completion signal — a work noun (`item/task/mission/tick/work`) followed within 40 chars by a completion verb, or the loop's structured report header, or a `backlog updated` note — ordered *after* the cap-hit block so a cap-delivered tick keeps its `CAP_DELIVERED` label. Never-guess preserved (an "investigating…" tail and an "IDLE-in-report" tail both stay `OTHER`). Live re-read: **DONE 3→13, done_rate 0.188→0.812, artifact_rate 1.0** (all 13 completed ticks carried a verified commit).

2. **Distinct null for "the deadline never fired" — `DEADLINE_UNBOUND`.** With the classifier fixed, the live verdict was still `ABSTAIN(sample<5)` — but the reason is *not* an underpowered measurement; it is that **0 of 17 ticks reached the τ=66 cap** (max observed 64). The knob is *workload-limited, not knob-limited* this window: there is no cap-effect to measure, which is a structural null, not a small sample. `verdict_of` now returns **`DEADLINE_UNBOUND(N ticks, 0 capped)`** when the capped group is empty, distinct from `ABSTAIN(sample<N)` (both groups present but underpowered). This is the thread's own "honest asymmetry — no control-side cap evidence was possible" caveat (v0.8.6) promoted from prose to a first-class verdict.

**The answer this closes (with the honest caveat kept open):** under the armed τ=66 regime across 17 ticks, the deadline *did not bind even once*, and the subcap group delivers at `done_rate=0.812 / artifact_rate=1.0 / proof_score=0.765` — so there is **no measured quality cliff at the cap**, but *because the cap never fired* there is still no cap-vs-subcap contrast to assert the cliff's absence. The quality-delta question now resolves to: the deadline is currently *expensive-to-bind* (work completes in ≤64 turns), which is itself the A3-positive condition — convergence pressure exists but the agent's own half-life τ\*=55 sits *below* the current tick workload, a distinct (and healthier) regime than the weak-τ ceiling the thread diagnosed. Selftest 29→30 (completion-language DONE signatures pinned, `DEADLINE_UNBOUND` null pinned, the `TodoTracker` no longer hardcodes a fake assert count). `py_compile` clean; production run exit 0; read-only throughout (Goodhart preserved).

---

## v0.8.31 — 2026-09-13 — fingerprint parity check gains its scheduled consumer (`--check`)

v0.8.30 shipped the instrument that *surfaces* the Rust⇄Python fingerprint parity (the Q=1.9845 shared surface, 34 axes) but left it run-only-by-human — the exact gap every sibling fail-closed instrument closes with a cron (a5 `--check` → `56fba415da49`; crate_identity → `1eaf2b71253c`; joint `--check` → `6e3bb938efc3`; epsilon_code/curiosity samplers). The runtime's most fundamental invariant — that the Rust primary and Python mirror produce identical scalar outputs — was still "surfaced, not trusted" in the scheduled sense: a silent fork between the two would pass `cargo test` and pass a Python smoke run, and nothing on a clock would flag it.

This release closes the consumer gap without touching the measure. `fingerprint_parity_check.py` gains a **`--check`** mode (the same discipline as its siblings): silent (exit 0) on PARITY so the weekly cron delivers **only** a `DRIFT` line (exit 1) or `ERROR` line (exit 2); it runs `--skip-build` internally so a cron never triggers a rebuild and fails closed if the collapse binary has not yet been built. The human form (`python3 fingerprint_parity_check.py`, `--skip-build`) is unchanged — it still prints the full "PARITY — 34 axes" line. Backed by a weekly no-agent cron (`03a92b245a88`, Mon 10:05, completing the Monday IST instrumentation band after the 09:17 samplers, 09:47 joint watchdog, 09:55 crate watchdog) via `~/.hermes/scripts/ist-fingerprint-parity-watchdog.sh` (POSIX sh, silent on parity, fail-closed rc 2 on unreadable runtime, performs NO action — Goodhart preserved).

Proof executed 2026-09-13: `--check` silent rc 0 on live parity; fail-closed ERROR path (collapse binary temporarily absent → rc 2 with explicit message); `--selftest` 5/5; normal run still prints PARITY (Q=1.98447); wrapper silent rc 0 + fail-closed rc 2 on bad `IST_RUNTIME`; `hermes cron run 03a92b245a88` → "Ran now: succeeded" (silent). cargo test 40/40, py_compile clean, crate identity re-aligned 0.8.31.

## v0.8.30 — 2026-09-13 — fingerprint parity check: Rust primary ⇄ Python mirror are now surfaced, not trusted

The `framework/ist_engine.py` module docstring has always said the Python mirror and the Rust primary "MUST produce identical scalar outputs" — the Q=1.9845 fingerprint — and the Rust test suite asserts the canonical value (`sourced_mirrored_decreases_q_versus_chosen`, `portfolio_all_chosen_matches_canonical_q`). But the parity was held by *discipline*, not by *surfacing*: nothing ran both implementations and diffed their output, so a silent fork between Rust and Python would pass `cargo test` (which tests Rust against itself) and a naive Python smoke run (which tests the mirror against nothing). The recent type-level additions (`phi_sourced`/`route` v0.8.25, `constraint_margin` v0.8.26, `constraint_portfolio` v0.8.27) widened that un-surfaced surface.

`examples/fingerprint_parity_check.py` (stdlib, zero-dep, read-only) closes the gap by the same fail-closed deterministic discipline as `crate_identity_check` and the a5 `--check`: it computes the canonical shared surface from the **Python mirror** alone (`phi`, the 7-step collapse NEI scores + urgencies, the audit score + `min_margin`, and the 15 source-term invariants the Rust tests pin), runs `cargo run --example collapse` and parses the Rust demo's printed scalars, and asserts agreement within the shared 1e-4 floor — exit 1 with a `DRIFT` line naming the axis on any disagreement, exit 2 if either side cannot be obtained. Read-only: it never edits either implementation.

**First live read (2026-09-13): PARITY — 34 axes agree** (Q=1.98447, 7 NEI steps, audit score/min_margin, 15 source-term invariants). The selftest (5/5) proves the assert paths: agreement fires, a synthetic φ-drift is detected, the 15 source-term invariants hold, and the canonical-Q fingerprint is reproduced — with the fail-closed counting path proven (an injected-false check drops the report below total, so `bool((name, False))`-always-true can never mask a regression). The ε_code lesson of the build itself, recorded honestly: the first selftest draft appended `(name, ok)` tuples and summed `bool(b)`, which is always `True` for a non-empty tuple — a fail-open self-check that the fixed `sum(1 for _n, ok in res if ok)` now closes. cargo test 40/40, py_compile clean.

## v0.8.29 — 2026-09-13 — a7 ε-boundary probe: the ε_code ↔ ε_system boundary is itself measured

The ε-thread ("ε as the Sovereignty Term") asks two falsifiable questions. The a6 probe (v0.8.11) answered the first — decompose the runtime's remainder into ε_code (compressible) vs ε_system (chosen). The second — *"is the boundary between ε_code and ε_system itself an ε?"* (line 58; the a6 docstring even lists it as question #2) — was answered only in **prose**: "the boundary is sharp and sits inside ε_code." No instrument ever *measured* the boundary.

`examples/a7_boundary_probe.py` (stdlib, zero-deps, read-only) is that measurement. It re-uses the ground-truth loader (`epsilon_code_coverage.load_commands`) and the classifier (`action_typing_classifier.classify`) as single sources of truth, takes every command the classifier already refused to type, and **bins the UNKNOWN residual by shape**: commands whose *string* still carries a recoverable verb (a future classifier pass could type them) are **ε_code** (compressible); commands whose intent is provably absent from the string — a variable argument to a `subprocess.run(a, …)` driver, a bare `python3 /tmp/script.py`, an opaque `ssh host '…'` remote, an inline `import`/`from` blob with no named verb — are **ε_boundary** (the undecidable floor that even A4's never-guess wall cannot move without *observing a side effect the runtime's own record does not contain*). The verdict is ratio-based (sharp / mixed / fat / empty), with the mixed band placed around parity so a tie is never mislabeled fat.

**First live read (2026-09-13, 5,487 commands, 211 UNKNOWN = 3.8%):** ε_code 128 (2.33%) / ε_boundary 83 (1.51%) → **MIXED-BOUNDARY** — the boundary is *partially* an ε: a genuine 1.5%-of-ambiguous floor of driver blobs sits alongside 2.3% that is still compressible. The prose assertion "the boundary is sharp" is therefore *falsified in its absolute form* — the boundary is sharp only in the sense that ε_boundary < ε_code, but the undecidable floor is a real, non-negligible remainder (the "third kind of ε": what the system asserts about itself vs what is verifiable from inside the assertion). Selftest 13/13 (binning of each shape, all four verdict regimes, bounded fractions, neighbor-interface). Scope Python-only; crate identity re-aligned 0.8.29. cargo test 40/40, py_compile clean, curiosity index re-matched.

## v0.8.28 — 2026-09-13 — a5 parser drift fixed: nested empty map no longer leaks onto sibling scalars

The A5 constraint-provenance classifier — the instrument that exists to *catch* silent config drift (the `agent.max_turns` 66→999 recurrence) — carried a drift in its **own** YAML-subset parser. `load_yaml_scalar` tracked the section stack only on *map-section* lines (empty-value keys), never re-syncing it on *scalar* lines. So a nested empty map leaked its path onto every sibling scalar that followed at the parent indent: the live config's `delegation.fallback_providers:` (an empty map) re-filed `child_timeout_seconds: 3600`, `max_iterations: 64`, etc. under `delegation.fallback_providers.*`, and the anchor lookup for `delegation.child_timeout_seconds` silently missed a knob that was **present and correct** (3600 = the operator-set ceiling). The report read `CHOSEN (4) + UNVERIFIED (1)` when the knob was in fact CHOSEN — a false-negative drift that would have hidden a *future* regression of that same knob.

The fix is the parser's missing half of the indent discipline (the map-section branch already had it): a scalar key belongs to the section at its *own* indent level, so truncate the stack to `indent // 2` before computing the path. The anchor lookup now resolves `delegation.child_timeout_seconds = 3600` → CHOSEN.

Three regression-pinning selftest cases ride along (synthetic nested-map YAML written to a tempfile): the sibling scalar is recovered at the parent path, its companion is too, and the nested path does **not** contain the recovered scalar. Negative control proven (the pre-fix parser reproduces the mis-filing). The self-measurement caveat is now, in a fitting recursion, ε_code-compressed: the instrument that measures whether constraints sit on real negation had a compressible gap in the tool that reads *where the constraints live*.

Scope is Python-only (no Rust change); the crate identity (Cargo.toml == CHANGELOG head) is re-aligned as `0.8.28`. **Result: CHOSEN (5) / UNVERIFIED (0) / DRIFT none.** Selftest 11/11 (was 8/8), cargo test 40/40, clippy clean, py_compile all examples.

## v0.8.27 — 2026-09-13 — constraint_portfolio: the Boundary Paradox ⊕ κ-Proliferation synthesis lands as an aggregator

The two Active threads kept returning to the same sentence — *"the same κ-over-φ curve from different angles"* — and left it rhetorical. `route(d, s)` (v0.8.25) answers the **per-constraint** question (one constraint's mass splits into density vs κ by source); the κ-thread's instruments (v0.7.7–v0.8.26) measure the **agent's own runtime** κ. Neither answers the Boundary Paradox's *verbatim* question: **is there a threshold where self-imposed constraints become indistinguishable from external ones?** made quantitative — the point where adding one more *mirrored* constraint *decreases* Q while a *chosen* one raises it.

This release lands the **portfolio aggregator** that closes the loop:

- **`PortfolioConstraint`** — a `(mass, source)` pair, the granular unit the thread named.
- **`constraint_portfolio(&[PortfolioConstraint], baseline_kappa) -> ConstraintPortfolio`** — rolls `route` up across a *set* of constraints: `density = Σ φ(route(d, chosen).0)`, `burden = Σ route(d, mirrored).1`, `quality = density / (baseline_κ + burden + ε)`. A chosen constraint raises the numerator; a mirrored one raises only the denominator — so the "adding X decreases Q" claim is now a one-liner, not a hand-sum.
- **`at_mirror_threshold`** — the crossing point `burden > density`, the quantitative form of *"where self-imposed constraints become indistinguishable from external ones"*. Reported read-only; the prune stays a sovereign decision (A4 / Goodhart preserved — the instrument names the point, never acts on it).
- **Python drift repaired**: the v0.8.25 source term (`phi_sourced`/`route`/`ConstraintSource`) reached only the Rust type, leaving `framework/ist_engine.py` — which declares itself the Rust fingerprint that "MUST produce identical scalar outputs" — silently behind. This release mirrors the source term **and** the portfolio into Python, restoring the Rust↔Python fingerprint (both yield Q = 1.9845 for the canonical demo, both yield `at_mirror_threshold=true` when burden overtakes density).

Four canonical tests pin it (`portfolio_all_chosen_matches_canonical_q` folds back to Q=1.9845, `portfolio_mirrored_adds_kappa_not_density` proves density stays flat while burden grows and Q strictly falls, `portfolio_threshold_flags_next_mirror_decreases_q`, `portfolio_chosen_before_mirrored_is_honest_split` pins the φ-only/κ-only split at the aggregate level). **40/40 tests green; fingerprint Q=1.9845 untouched** (the portfolio is a new aggregator, no equation changed).

This is the Boundary Paradox ⊕ κ-Proliferation synthesis the dispatches kept gesturing at, finally materialized as a function: measure *per-constraint* (route), *per-runtime* (kappas/margins), and now *per-portfolio* — "different angles" became one surface.

## v0.8.26 — 2026-09-13 — κ-margin gradient: constraint_audit gains continuous headroom (the 2026-06-14 thread's "dκ/dt" signal)

The κ-Proliferation thread (CURIOSITY.md) named a structural gap back on 2026-06-14 and it sat open for ~3 months:

> *"the `constraint_audit` function is a step function (boolean per axis). It registers compliance/non-compliance but offers no gradient: no margin, no drift, no dκ/dt … you can't see κ accumulating until you trip the hard limit."*

The boolean gate says *whether* a limit is tripped; it cannot say *how close* the system is to tripping it — so κ-drift stays invisible right up to the moment compliance flips. This release closes that gap with a continuous margin on every numeric axis.

- **`constraint_margin(limit, current) -> f64`** — signed κ-headroom: `(limit - current) / limit`. `1.0` = nothing consumed, `0.0` = sitting on the wall, negative = overshoot. The zero-limit axis (`MAX_DEPS = 0`, A1) has no ratio (a wall at zero divides the domain), so it carries a linear penalty `-current` instead.
- **`Audit`** gains `tool_margin`, `dep_margin`, `memory_margin`, and **`min_margin`** — the tightest of the three, the single number a consumer watches to see κ-drift *before* `score` drops. Sovereignty stays binary (constitutive — a boolean margin would mean nothing, per the Structural/Behavioral Split).
- **`constraint_audit`** computes the three numeric margins inline and returns them; the `score` (mean of four booleans) is untouched.

Four canonical tests pin it: `margin_is_full_headroom_at_limit`, `margin_goes_negative_past_the_wall` (proves overshoot magnitude per axis, min = deps −5.0), `margin_surfaces_drift_before_score_drops` (a still-compliant config's tightest axis has already eroded to the wall — the thread's exact "see κ accumulating before you trip the limit"), and `constraint_margin_zero_limit_is_linear_penalty`.

The Python reference (`framework/ist_engine.py`) mirrors the same margin fields in its `constraint_audit` return dict, so the Rust/Python pair stay fingerprint-aligned (Q = 1.9845 unchanged — the margins are additive fields, no equation touched). `examples/audit.rs` and `examples/collapse.rs` print the new margins.

The Goodhart safeguard is structural: the margin is *reported*, never acted on — no consumer gates on it, no config is trimmed because of it. It is the dκ/dt signal the thread asked for, made continuous and visible, with the prescription still left to the operator.

## v0.8.25 — 2026-09-13 — φ(d, s) source term lands: the Boundary Paradox density term is now in the type, not just the prose

The **Boundary Paradox** thread (CURIOSITY.md, first raised 2026-06-10) proposed a density *source term* as its candidate structural signature for the chosen/mirrored distinction:

> *A chosen constraint negates something to create novelty (genuine A1). A mirrored constraint pre-emptively adopts the anticipated shape of an external optimizer — it may add to κ (complexity) rather than φ (density), actively decreasing Q.*

That proposal stayed in comments and prose: the delegation resolution (v0.7.4, `ChildSpec::consenting`) split chosen/mirrored at the *fan-out* layer, and the v0.8.4/v0.8.10 a5 instrument answered the detection question for *bounded knobs* — but the notation `φ(d, s=chosen)` already used in the delegation doc had **no type-level reality** in the core equation. `phi(d)` was single-argument, so the source term was exactly the "axioms live in comments not types" shape the Structural/Behavioral Split thread keeps surfacing.

This release lands the source term as a **strict, backward-compatible superset** of `phi(d)` — the A2-canonical transform that `Step.quality` already uses is left byte-for-byte untouched, so the Q = 1.9845 fingerprint for the canonical demo (d=0.85, c=0.31) is preserved:

- **`ConstraintSource`** enum — `Chosen` (A1-legitimate: negates something real) vs `Mirrored` (A4-imposed: adopts the anticipated shape of an external optimizer).
- **`phi_sourced(d, s)`** — `φ(d, chosen) = ln(1 + d)` (genuine density), `φ(d, mirrored) = 0` (the mass lands in κ, not φ).
- **`route(d, s) -> (density, kappa)`** — the φ-vs-κ router that makes the source term's Q-effect explicit: `route(d, chosen) = (d, 0)`, `route(d, mirrored) = (0, d)`. A mirrored constraint shrinks Q by enlarging κ while φ stays fixed; a chosen one leaves Q at its A2-canonical value.

Six canonical tests pin the doctrine: `sourced_chosen_matches_canonical_phi`, `sourced_mirrored_contributes_zero_density`, `route_chosen_is_all_density_no_kappa`, `route_mirrored_is_all_kappa_no_density`, `sourced_mirrored_decreases_q_versus_chosen` (proves mirrored → Q = 0 against the canonical 1.9845), and `phi_sourced_is_projection_of_route`.

What this does **not** do, per the thread's own A4 caution (line 165: *"the chosen/mirrored distinction may be undecidable from the inside"*): it does **not** auto-classify. The source term provides the *type-level* shape the notation promised; the *decision* of which source a given constraint is — chosen or mirrored — remains a sovereign one, made either by the child declaring consent (gateway `ChildSpec::consenting`) or by the a5 anchor/provenance classifier. The source term is the encoding of *what the distinction means for Q*, not a claim about *which side any particular constraint falls on*.

**Crate identity:** `Cargo.toml` 0.8.24 → 0.8.25, `Cargo.lock` sync. `cargo test --release` 32/32 (26 prior + 6 new), `cargo clippy --release` 0 errors (2 pre-existing literal-bool lints in the audit test, untouched), `cargo fmt --check` clean, canonical collapse example still emits Q=1.984 / IST=0.03083 / audit score 1.000.

---

## v0.8.24 — 2026-09-13 — κ-trend definitional-break guard: the collapse reader stops fabricating redefinition as collapse

The `kappa_proliferation_timeseries.py --trend` reader reported `collapse: true` (and `monotone_drops: 5`) on the live 7-sample series — and the joint reader translated that into a weekly `compress-paradox` alarm (`axiom_joint_trend.py --check`). Both were **false positives of a single root cause**: the κ metric gained two new terms (toolsets + MCP) on 2026-09-11, so the series silently mixed two *definitions* of κ. Samples 1-2 (κ_raw=577, pre-terms) and samples 3-7 (κ_raw=615, with-terms) are incommensurable — the 577→615 step is a **redefinition**, not proliferation, yet the trend reader compared across it and manufactured a collapse that was never in the runtime.

This release fixes the measure at its source (the trend reader, single source of truth — the joint reader already imports `compute_trend`, so the correction propagates automatically):

- **`_kappa_def_fingerprint`** — a sample's κ-definition is structurally encoded in the data already: pre-term rows carry `NULL` in the `toolsets_enabled` column (the ALTER TABLE migration left them NULL), post-term rows carry a count. No new column needed.
- **`_definitional_breaks`** — detects where the definition changes between adjacent samples, marking epoch boundaries.
- **`compute_trend` is now epoch-local**: the headline `collapse` verdict is computed only over the *current* definitional epoch (the contiguous suffix sharing the latest κ-definition). A κ-definition break makes earlier samples incommensurable, so comparing across it is meaningless. The reader still *reports* the break (`provisioned.definitional_breaks`, `break_count`) and the full-span naive read (`full_span_collapse`) — transparency, not deletion — but the answer it hands to consumers (`collapse`) only fires when κ genuinely rose *within* one definition.
- A single-sample current epoch **abstains** (`collapse: None`) rather than claiming anything.

**Live result (2026-09-13):** `collapse: false` (was `true`), `full_span_collapse: true` (the naive read, now explicitly labeled as the fabricated naive), `break_count: 1`, `current_epoch` flat over 5 samples. The joint reader now reports `kappa: stable` and joint verdict **`compress-coherent`** (was `compress-paradox`) — the `--check` watchdog goes silent, which is correct: there was never a ketosis, only a definitional break the measure hadn't learned to see. This is the `ε_code/ε_system` boundary again, applied to the κ trend itself: the reader had a compressible ε_code (it didn't know its own κ-definition could drift), and the fix landed on the compressible side. Selftest grew 8→10 cases (break detection, break index, full-span-vs-epoch split, single-sample-epoch abstain).

**Crate-identity alignment (2026-09-13, follow-up):** the *instrument* the v0.8.23 entry shipped caught its author's own recurrence immediately. The v0.8.24 release step bumped `CHANGELOG.md` to `v0.8.24` but again left `Cargo.toml`/`Cargo.lock` at `0.8.23` — the exact release-process drift `crate_identity_check.py --check` exists to surface. First live run after the κ-trend commit reported `DRIFT: crate v0.8.23 vs changelog v0.8.24 (gap 1)`, exit 1. Aligned: `Cargo.toml` 0.8.23 → 0.8.24, `Cargo.lock` sync (`cargo update -p ist_engine --precise 0.8.24`). Watchdog now reads `OK` (exit 0), `cargo metadata` → `ist_engine 0.8.24`, cargo test --release 26/26, `cargo build --release` clean.

---

## v0.8.23 — 2026-09-13 — crate identity drift watchdog: the v0.8.15 fix recurred, now instrumented

`Cargo.toml` (and `Cargo.lock`) sat at `version = "0.8.14"` while `CHANGELOG.md` had advanced to `v0.8.22` — the crate identity drifted **eight releases behind again**, the exact disease the v0.8.15 entry fixed *by hand* (0.7.0 → 0.8.14) with no instrument behind it. A one-time manual alignment cannot prevent recurrence: the release step bumps the CHANGELOG head but not `Cargo.toml`, and nothing asserts the pair stay equal — the drift is semantically valid and structurally invisible (the `Structural/Behavioral Split` enforcement gap, applied to the crate's *own* identity).

This release closes it two ways:

1. **Alignment fix** — `Cargo.toml` bumped 0.8.14 → 0.8.23 (forward to this release's own head), `Cargo.lock` synchronized (`cargo update -p ist_engine --precise 0.8.23`). Crate, lock, and CHANGELOG head now converge on one identity.
2. **The instrument (`examples/crate_identity_check.py`)** — a read-only stdlib watchdog (zero deps, same discipline as the A5 `--check`) that asserts `Cargo.toml#version == CHANGELOG head vX.Y.Z`:
   - `main()` — diagnostic, always exit 0, reports the pair and the gap.
   - `--check` — report-only watchdog, **fail-closed**: exit 1 with a `DRIFT` line when the two identities disagree, or `UNVERIFIED` (a missing/unparseable side is *never* asserted aligned); exit 0 silent when aligned. The exit code is a *reporting* mechanism for a cron, not a gate — the instrument never edits `Cargo.toml`/`Cargo.lock`/`CHANGELOG`.
   - `--selftest` — deterministic, no-repo; proves aligned → OK, crate-behind → DRIFT (gap N computed), changelog-behind → DRIFT (symmetric), leading-`v` tolerated, short/missing/garbage → UNVERIFIED.

**Negative control proven, not asserted**: the instrument's first live `--check` *caught the real drift* (crate 0.8.14 vs changelog 0.8.22, gap 8, exit 1) before the alignment fix; after the fix it reads OK (exit 0). The drift is now **watched**, not hand-checked — the next time a release forgets to bump `Cargo.toml`, a scheduled consumer surfaces it instead of an agent tripping over `cargo metadata` reporting a stale version.

Verification: `--selftest` PASS (aligned/drift/leading-v/unverifd), `--check` exit 1 → exit 0 across the fix, cargo test --release 26/26, `cargo metadata` → `ist_engine 0.8.23`, py_compile clean.

---

## v0.8.22 — 2026-09-13 — the joint alarm surfaced: a scheduled report-only consumer (report-only watchdog)

`axiom_joint_trend.py` (v0.8.21) produced the only place the two dangerous cross-face conditions are visible — `kappa-and-eps-collapse` (both compressible terms drifting = A2 alarm) and `compress-paradox` (ε improving WHILE κ balloons = a ketosis, not a diet) — but it was a pure read-only reader with **no scheduled consumer**: its alarm could only ever fire if a human happened to run it, while the three samplers it reads from each append on a weekly cron. The synthesis was wired to nothing.

This release closes that structural gap with the same report-only discipline the A5 drift watchdog (v0.8.10) already established: the instrument gains a **`--check` mode** — silent (exit 0) on a healthy joint verdict (`compress-coherent` / `stable` / `abstain`), and prints a compact `ALARM:` line + the full JSON and exits 1 on the two dangerous verdicts. The exit code is a **reporting** mechanism (so the cron delivery surfaces the alarm), *not* a gate on any action — nothing edits, prunes, or changes config; the Goodhart safeguard (read-only, never-prescriptive) is preserved exactly. Backed by a weekly no-agent cron (`6e3bb938efc3`, Mon 09:47 — *after* the three Mon 09:17 samplers, so it reads the fresh samples) via `~/.hermes/scripts/ist-axiom-joint-watchdog.sh` (POSIX sh, fail-closed rc 2 on instrument error).

**First live read (2026-09-13): `compress-paradox`** (ε_code improving, κ worsening, self-κ stable) — the same verdict the v0.8.21 entry already traced to the κ series' definitional rebase (toolsets+MCP terms added 2026-09-11), *not* a real trade-off. The value of the watchdog is that this alarm now **fires on schedule** instead of waiting for a human to run the reader; once κ re-accumulates post-rebase samples, the court reads `compress-coherent` again. `--selftest` gained the ALARM-classification pin (only the two dangerous verdicts are surface-worthy; every healthy verdict stays silent). Verification: `--selftest` PASS, py_compile clean, cargo test --release 26/26, curiosity_lint 32/32, a5 `--check` DRIFT:none.

---

## v0.8.21 — 2026-09-13 — the joint trajectory: Q = φ/κ + ε read whole (read-only synthesis)

The three trend instruments each trend ONE face of the core equation in isolation — `epsilon_code_trend.py` (the compressible UNKNOWN% gap, ε_code), `kappa_proliferation_timeseries.py` (κ_raw/κ_eff and Q=φ/κ), `curiosity_kappa_trend.py` (the runtime's own self-bloat) — and the CURIOSITY synthesis kept returning to *"the same κ-over-φ curve from different angles"* without any instrument looking at the faces at once. The core equation Q = φ/κ + ε ties them: ε_code is the compressible remainder of `+ ε`, κ is the denominator of `φ/κ`, and a healthy runtime compresses ε_code **without** letting κ balloon to swamp the φ it unlocks. Those two compressible terms could trade off invisibly if each is trended alone — ε falling while κ ballooning is a lie dressed as discipline.

`examples/axiom_joint_trend.py` (stdlib, zero-deps, **read-only, no append**) is the synthesis. It imports the three existing readers' **low-level data functions** (single source of truth — `kappa._load_rows`/`compute_trend`, `ckappa._load_rows`/`compute_trend`, `eps.trend`) rather than the print-to-stdout `trend()` wrappers, so it can never re-implement or drift from a measure. `--trend` (`schema axiom-joint-trend/v1`) emits a **`joint_verdict`** over the relative drift of the two compressible terms:

* `compress-coherent` — ε_code improving while κ held (healthy);
* `compress-paradox` — ε_code improving WHILE κ worsens (the UNKNOWN% fell only because the kit ballooned: a ketosis, not a diet);
* `kappa-and-eps-collapse` — both compressible terms drifting the wrong way (A2 alarm);
* `self-bloat` — ε + κ stable while the runtime's own φ/κ worsens;
* `abstain` — any series below 2 samples (honest, never guesses).

**First live read (2026-09-13):** ε_code `improving` (3.8349%, n=3), κ `worsening` (Q_eff collapse, n=7), self-κ `stable` (n=3) → **`compress-paradox`**. The honest interpretation: the κ `worsening` is the **already-documented definitional break** (the κ-Proliferation thread's own `--trend` carries `collapse:true` because κ gained toolsets+MCP terms on 2026-09-11, rebasing Q lower — not a real collapse). So the paradox flag today is the *known* rebase, not a genuine ε_code/κ trade-off — exactly the caveat the sibling readers already carry forward. The instrument fires correctly; its current trigger is definitional, and the joint read will report `compress-coherent` once the κ series re-accumulates post-rebase samples.

The Goodhart safeguard is identical to its siblings: read-only, no gate, no decision path, no prescriptive consumer. Because it is a **pure reader** (it appends nothing — it reads what the three weekly sampler crons already append), it needs and carries **no cron** of its own. `--selftest` 7/7 (import, the five joint-verdict fire cases, the two sparse-abstain cases, plus a live end-to-end read). py_compile clean across all `examples/*.py`; `cargo test --release` 26/26 green (unaffected — Python-only addition); `curiosity_lint --selftest` 32/32.

## v0.8.20 — 2026-09-13 — the ε_code residual tracked: UNKNOWN-fraction time-series (append-only)

The ε-as-Sovereignty thread closed its compression at ~3.8% UNKNOWN (the residual dominated by genuinely-ambiguous *driver* blobs — `subprocess.run(a, ...)` with a variable argument, bare `python3 <script>` — which the never-guess discipline correctly refuses to classify). But a point-in-time coverage number makes a silent regression invisible: if a new shell shape leaks through as UNKNOWN (or the classifier is later *over*-extended and starts guessing intent it cannot prove), nothing trends it.

`examples/epsilon_code_trend.py` (stdlib, zero-deps, read-only) closes that gap by the same discipline the κ-Proliferation thread used for dQ/dt (`kappa_proliferation_timeseries.py --trend`, v0.8.9) and the CURIOSITY thread used for self-bloat (`curiosity_kappa_trend.py`, v0.8.14):

* it does **not** re-implement the measurement — it imports `epsilon_code_coverage` (`load_commands` + `action_typing_classifier.classify`) so the trend and the point-in-time report share one source of truth and cannot drift apart;
* each run appends one row {seq, ts, total, unknown, unknown_frac, mutation, observe, producer_sha} to `data/epsilon_code_trend.sqlite` (append-only, `seq INTEGER PRIMARY KEY AUTOINCREMENT` — the v0.8.9 write-safety shape);
* `--trend` (`schema epsilon-code-trend/v1`) reads the UNKNOWN-fraction gradient and reports a **`worsening`** verdict only on a genuine monotone rise of unknown_frac past the healthiest (lowest) point; **`improving`** only on a strict fall; `abstain` on <2 samples.

**First live datapoints (2026-09-13):** 3 samples appended (5470/5472/5476 commands), UNKNOWN 3.8391% → 3.8349%, verdict `improving` (δ −0.0042 — noise-level, as expected at a stable floor). The Goodhart safeguard is structural and identical to its siblings: the instrument samples and appends only — no gate, no decision path, no prescriptive consumer. The UNKNOWN% is a *measured* surface of ε_code (compressible by definition); ε_system (the sovereignty residue) is untouched because the classifier only resolves *shape*, never intent it cannot prove.

Backed by a weekly no-agent cron (`fbc620ac003b`, Mon 09:17) via `~/.hermes/scripts/epsilon-code-trend-weekly-sampler.sh` (POSIX sh, silent on success). `--selftest` 6/6 (import, append-does-not-replace with monotonic seq, flat→stable, worsening, improving, abstain<2). py_compile clean.

## v0.8.19 — 2026-09-12 — the ε_code measure made honest: producer↔vendored sync invariant falsified

The v0.8.16 drift (the ε-probe's own `AMBIGUOUS_TOOLS = {"terminal"}` silently dropping `execute_code`/`browser_exec` for a whole release) named a failure mode no instrument guarded against: **the measured classifier and the production producer are two files, and nothing asserted they stayed byte-identical.** `examples/epsilon_code_coverage.py` — the instrument that reports the UNKNOWN% (ε_code's compressible surface) — imported the vendored classifier but never checked it against the live `session-scribe/action_typing.py` that actually types the diary. A future silent fork would make the coverage number a measurement *against a classifier the production diary never used* — a lie dressed as evidence.

This release closes that gap with a **`--synccheck`** mode (sha256 byte-identity over the vendored copy vs the producer; exit 1 on DRIFT) and a **`--selftest`** (5/5: classifier import, mutation fire on `git commit+push`, observe fire on `systemctl is-active`, UNKNOWN never-guess on a bare `python3` driver, and sync OK on the live files). The negative control is proven, not asserted: a byte-injected copy hashes differently and the detector distinguishes it from the genuine sync.

**Result:** `--synccheck` → `SYNC: OK — producer == vendored (byte-identical, hashes equal)`; live coverage unchanged at **96.2% (UNKNOWN 3.8%, 191/5087)** — the compression claims remain valid, now with the sync invariant pinned rather than manually re-checked. The coverage report itself now prints a `producer sync` line so no future run can silently report a drifted measure.

Read-only discipline preserved: `--synccheck`/`--selftest` are deterministic checks (exit 0/1), never a metric gate; the UNKNOWN% remains reported-not-acted-upon.

## v0.8.18 — 2026-09-12 — ε_code compressed a third time: terminal mutation/read shapes (96.2% coverage)

The v0.8.17 entry closed its *execute_code*-blob residual but left the *terminal* side at 5.3% UNKNOWN — the remaining clusters were distinct, named shell shapes, not inline Python. This release compresses them, leaving a residual dominated by genuinely-ambiguous driver blobs (variable-argument `subprocess.run(a, …)` helpers, bare `python3 <script>` with no verb/hint), which the never-guess discipline correctly refuses to classify.

New **mutation** patterns: `install -m <mode> SRC DEST` (copies + chmods into bin — 8 live hits), `umount` (filesystem detach; `mount` was already a read), `hermes cron add` (dispatcher mutation, added to the cron-mutation set), `hyprctl … reload` / `hyprctl reload` (compositor config re-apply), and the `from hermes_tools import … patch|write_file` execute_code shape (mutation tools leaked into shell blobs).

New **observe** patterns: `pstree`/`command -v` channel/which probes, a generic `<binary> --version` probe (`rustc`/`wrangler`/`himalaya`/`cloudflared`/`rtk`/`agy` — 6+ live hits), `hermes status`/`computer-use doctor`/`cron tick`, `hyprctl monitors|configerrors|workspaces|clients|activewindow|activeworkspace|version`, the long tail of `omarchy` read subcommands (`default`/`installed`/`toggle … status`/`weather location`/`theme bg current`/`bar defaults`/`channel current`/`plugin list --json`/`config --help`/`monitor status`/`menu --help`/`launch config editor --help`/`plugin validate --help`/`theme set --help`), `npm run typecheck`, bare `read_file <path>` and `sqlite3 <db> "SELECT …"` (tool names leaked into terminal).

**Result against live state.db (5,052 commands measured): UNKNOWN 3.8% (was 5.3% at v0.8.17, 13.6% at v0.8.12, 28.0% at v0.7.9-era), coverage 96.2% (was 94.7%)** — another 1.5 points of the compressible ε_code collapsed toward the ε_system residue, which is untouched by construction. Every mutation shape fires before any observe shape, so a blob holding both still classifies mutation; the `--version` observe probe is gated behind the full mutation list (never shadows `install`/`rm`/etc.). Selftest extended to 29 mutate / 49 observe / 5 unknown (24 new pinned cases); py_compile clean.

## v0.8.17 — 2026-09-12 — ε_code compressed further: execute_code mutation/observe shapes (94.7% coverage)

The v0.8.12 entry left a named residual — its "13.6% dominated by inline Python blobs (`import`/`from`), `python3 <script>`, bare `sudo`/`cd`". The vendored classifier (`examples/action_typing_classifier.py`) now resolves the *execute_code* blob shape, compressing the residual. New mutation patterns (shutil.copy2/copyfile, `.open('a'|'w')` append/write, bare `f.write`/`fh`/`out`/`dst` handles, `requests.post/put/patch/delete`, `os.remove/unlink/rename/makedirs/...`, `subprocess` with a real output-artifact verb magick/ffmpeg/cargo/rustc) and new observe patterns (sqlite3 `mode=ro`, Path reads `.read_text`/`.iterdir`/`.glob`, path probes `.exists`/`.is_file`, `os.listdir/getenv`, `json.loads`, bare `print`) — each mutation shape fires first so a blob carrying both a read and a write still classifies mutation (never-guess preserved).

**Result against live state.db (5,023 commands measured): UNKNOWN 5.3% (was 13.6% at v0.8.12, 28.0% at v0.7.9-era), coverage 94.7% (was 86.4%)** — the compressible ε_code gap collapsed another 8.3 points toward the ε_system residue, without the instrument ever reading ε prescriptively (Goodhart / A4 preserved). Selftest extended to 22 mutate / 37 observe / 5 unknown; py_compile clean. Sovereignty term ε_system untouched by construction.

## v0.8.16 — 2026-09-12 — ε-probe taxonomy drift fixed: execute_code/browser_exec are ambiguous-by-design

**The ε-probe under-counted its own ε_code.** The v0.8.11 instrument
(`examples/a6_epsilon_probe.py`) shipped with `AMBIGUOUS_TOOLS = {"terminal"}`,
drifting from the canonical doctrine (`theory/action-typing.md` §2: "`terminal`/
`execute_code`/`browser_exec` are ambiguous by design") and from the producer's
own taxonomy (`session-scribe/action_typing.py` line 41: `AMBIGUOUS_TOOLS =
{"terminal", "execute_code", "browser_exec"}`). The consequence was structural:
`execute_code` (1,276 diary lines) and `browser_exec` (22 lines) that never
received a `⊗S:` marker were silently dropped from `untyped_ambiguous`,
deflating ε_code. A secondary drift rode along: `execute_code` sat in the
probe's `MUTATION_TOOLS`, so a legitimate `⊗S:observe` on a print-only
`execute_code` snippet was falsely flagged a mislabel.

Fix (single taxonomy realignment, no runtime behavior change):
  * `AMBIGUOUS_TOOLS` → `{"terminal", "execute_code", "browser_exec"}`;
  * `MUTATION_TOOLS` → `{"patch", "write_file"}` (the *unambiguous* mutation
    kinds — the only set the mislabel cross-check is valid against);
  * `execute_code` removed from `OBSERVE_TOOLS` too (it is ambiguous, not
    observe).

**Corrected production read (2026-09-12):** `untyped ambiguous 6,523 → 7,551`
(+1,028 execute_code/browser_exec lines now counted), `mislabels 164 → 28`
(−136 false positives), `ε_code 1.1585 → 1.3092`; ε_system unchanged (0.0242),
verdict stays SOVEREIGN-CODE. The probe now measures the full compressible
surface instead of silently discarding the execute_code axis.

Two new selftest cases pin the fix regression-proof:
`ambiguous-exec` (untyped execute_code → untyped_ambiguous=1) and
`exec-observe` (`⊗S:observe` on execute_code → mislabels=0). Both FAIL against
the pre-fix `{"terminal"}` drift (proved: `ambiguous-exec` 0 vs want 1;
`exec-observe` mislabels=1 vs want 0), so the drift cannot silently return.
Selftest 6/6 PASS; `py_compile` clean on all `examples/*.py`.

---

## v0.8.15 — 2026-09-11 — crate identity re-aligned: Cargo.toml was 14 releases behind

**A5 applied to the crate's own version field.** A frontier scan surfaced the
silent drift the `--check` watchdog exists to catch, but located in the runtime's
*identity* rather than its knobs: `Cargo.toml`'s `version` had sat at `0.7.0`
since the Delegation Gateway (2026-08-14) while the canonical CHANGELOG lineage
shipped fourteen minor releases (v0.8.0 → v0.8.14). The drift was *declared*
rather than enacted: the v0.8.0 commit's own message reads "bumps version to
0.8.0" and touched `src/lib.rs` (the A3-as-subsumed canonical test + docstrings),
but never wrote `Cargo.toml`. `cargo metadata` therefore reported
`ist_engine v0.7.0` against a `NEXUS V3.1.0-edge` / v0.8.14 CHANGELOG — two
version identities disagreeing by fourteen steps.

The fix is a single-field alignment, not a behavior change (the crate's runtime
semantics are unchanged; the v0.8.x releases were Python analytical instruments +
theory docs + one tested `src/lib.rs` docstring/test commit). `version` now reads
`0.8.14`, matching the CHANGELOG head so the crate, the changelog, and HEAD agree
on a single version lineage. Honest scope note: `rust-version = "1.74"` (the MSRV
floor) is left untouched — it is a compatibility declaration, not identity, and
changing it is a semantic decision for a future release.

Verification: `cargo test --release` 26/26 green; `cargo metadata` reports
`ist_engine 0.8.14`; all 18 `examples/*.py` `py_compile` clean. This entry itself
is the first non-instrument release in the v0.8.x run — pure hygiene, closing the
last silent drift the A5 lineage could reach.

---

## v0.8.14 — 2026-09-11 — self-bloat trended: append-only time-series for CURIOSITY.md's κ

The v0.8.13 instrument (`curiosity_kappa.py`) made the self-bloat recursion
falsifiable as a *point-in-time* verdict, but its own docstring named the
residue: "exits 1 on SELF-BLOAT in human runs so a cron consumer *could* gate
on it" — yet no consumer existed, and a one-shot read cannot make a self-bloat
that *compounds* visible (the "starter re-fed after the bread is done" shape
accumulating week over week). This release closes that gap with the same
discipline the κ-Proliferation thread already used for dQ/dt
(`kappa_proliferation_timeseries.py --trend`, v0.8.9): a read-only,
append-only time-series.

New `examples/curiosity_kappa_trend.py` (stdlib, zero deps, read-only):

  * does **not** re-implement the parser — `importlib`-loads the sibling's
    `parse_curiosity`/`compute` (single source of truth, no drift);
  * each run appends one row {ts, threads, total_bytes, open/resolved/closed,
    largest_thread, bloat_count, bloated_bytes, bloated[], verdict} to
    `data/curiosity_kappa_trend.sqlite` (append-only `seq INTEGER PRIMARY KEY
    AUTOINCREMENT`);
  * `--trend` (`schema curiosity-kappa-trend/v1`) reads the self-bloat
    gradient and reports **`worsening`** only on a genuine monotone rise of
    bloated_bytes past the healthiest point (never flat/improving; abstains on
    <2 samples);
  * `--selftest` 6/6 (compute-wrap, append-does-not-replace with monotonic
    seq, worsening/falling/abstain verdicts).

Backed by a weekly no-agent cron (`5fedcb10437c`, Mon 09:17) via
`~/.hermes/scripts/kappa-curiosity-trend-weekly-sampler.sh`. First live
datapoint: 9 threads / 78,365 bytes, 2 bloated *resolved* threads = 56,130
bytes = 71.6% of the file — the instrument now *trends* whether that fraction
grows. The τ-decay itself (compress resolved dispatch histories to one-line
pointers) remains a human decision the instrument perpetually surfaces but,
per A4, never executes.

---

## v0.8.13 — 2026-09-11 — self-bloat measured: A2/A3 applied to CURIOSITY.md's own κ

The κ Proliferation thread opened with an observation that the *thread file
itself* is the disease: "the agent that writes anti-bloat doctrine accrues
threads faster than the foundation" (2026-06-23, "cure and disease share a
file"). The proposed fix — *"τ on threads — each entry timestamps and decays,
dormant threads compress to one-line pointers … A3 applied to my own thread
file"* — stayed prose for ~2.5 months. This release makes the claim falsifiable.

`examples/curiosity_kappa.py` (stdlib-only, zero deps, read-only) parses
CURIOSITY.md into per-thread records with a **three-way φ state** — `open`
(no answer marker) / `resolved` (carries RESOLVED/CLOSED/DECIDED/INSTRUMENTED
inline but never explicitly closed) / `closed` (`**Status: CLOSED**`) — and
flags **κ-over-φ self-bloat**: any *answered* thread whose dispatch-history
byte κ exceeds the median history of still-*open* threads (the "starter re-fed
after the bread is done" shape).

**First production datapoint (2026-09-11):** CURIOSITY.md = 77,826 bytes / 9
threads (4 open, 3 resolved, 2 closed) → **verdict SELF-BLOAT**. The two
flagged threads are κ Proliferation (30,446B, resolved) and The
Structural/Behavioral Split (23,721B, resolved) — both answers already in the
record, both keeping the largest dispatch histories in the Active section.

The instrument only reports: it never decays a thread, never edits
CURIOSITY.md, and exits 1 on SELF-BLOAT in human runs (so a cron consumer
*could* gate on it) without ever prescribing. `--selftest` 7/7 (synthetic
answered-bloat fires; flat answered-under-median stays silent). The actual
τ-decay — compressing resolved dispatch histories to one-line pointers —
remains a human decision the instrument surfaces but, per A4, does not do for
the author.

Verification: `py_compile` on all `examples/*.py` OK; `curiosity_lint
--selftest` 32/32; `curiosity_lint CURIOSITY.md --check-index
CURIOSITY.index.json` → INDEX_MATCH (ledger re-fed after the prose edit).
Commit local (push blocked — see BACKLOG "Pendências L5", GitHub auth).

---

## v0.8.12 — 2026-09-11 — ε_code compressed: terminal-shape classifier extension (A6 forward-only)

The A6 ε-probe (v0.8.11) closed its measurement with an explicit forward-only action:
*"extend the terminal-shape classifier in `action_typing.py` … to compress ε_code →
ε_system without touching the sovereignty residue."* The probe's own first run named
the gap precisely — ε_code = 1.3218, dominated by 6,443 terminal-UNKNOWN calls
(63× the 117 mislabels), the compressible enforcement gap.

This release executes that action. The producer classifier (the scribe's
`session-scribe/action_typing.py`) measured its own live coverage against the ground
truth in `state.db` (the tool-call JSON the diary's bare `>T:terminal` lines do not
persist): **28.0% of 4,507 terminal/execute_code commands went UNKNOWN** under the
v0.7.9-era classifier. The dominant UNKNOWN clusters were pure-read status commands
— `systemctl is-active/show`, `df`/`du`/`free`/`lsblk`/`ps`/`ss`/`stat`/`sha256sum`/
`journalctl`/`uptime`/`nproc`/`uname`/`hostname`/`id`/`whoami`/`mount`/`findmnt`,
print-only `sed -n` (no `-i`), `python3 <script> --help|-h`, `rsync --dry-run`,
read-only `hermes`/`npm`/`omarchy` subcommands, extra `git` read forms — plus a
prefix-normalization gap (`cd X && ...` / `sudo` obscured the actual verb) and
missing mutation shapes (`tee`, real `rsync -a`, bootloader generators,
`omarchy hook install`, profile-prefixed `hermes config set`).

Delivered:
- **`examples/action_typing_classifier.py`** — the vendored, version-controlled copy
  of the producer classifier (the live one lives in the plugin; the repo now pins and
  tests the behavior). Selftest **56/56** (18 mutation / 33 observe / 5 unknown),
  each newly-added shape pinned by a case.
- **`examples/epsilon_code_coverage.py`** — read-only proof instrument: reads every
  recorded terminal/execute_code command from `state.db` and reports the classifier's
  UNKNOWN% (the ε_code compressible surface).
- **Result against production ground truth: UNKNOWN 1,262 → 615 (28.0% → 13.6%),
  classifier coverage 72% → 86.4%** — a 51% reduction in the compressible gap. The
  residual 13.6% is dominated by inline Python code blobs (`import`/`from`, ~353),
  `python3 <script>` without a help flag, `ssh` remote-exec, and bare `sudo`/`cd`
  prefixes with unknown inner verbs — genuinely ambiguous, correctly left UNKNOWN
  per the "never guess" rule (§4), not shape-coverage failure.

What this does NOT touch: ε_system (honesty marks — the could-have-done-otherwise
residue) is untouched by construction; the sovereignty remainder is neither measured
into nor acted upon by the classifier. The Goodhart safeguard holds — the classifier
only resolves shape, the ε-probe stays read-only. The ε-probe's own diary numbers are
unchanged this release (it reads the historical diary, which predates the producer);
the compression materializes forward-only as each new session types at 86.4% instead
of 72% coverage.

Rollback: `action_typing.py.rollback-20260911` (the v1.1.0 classifier, byte-identical
reconstruction of the pre-change source) — `mv` it over the plugin file to restore
28.0% UNKNOWN behavior. Both plugin and vendored copy carry identical logic.

- **`examples/action_typing_classifier.py`** — vendored classifier (56/56 selftest).
- **`examples/epsilon_code_coverage.py`** — ε_code coverage proof (read-only).
- **CHANGELOG.md** — this entry.
- **CURIOSITY.md** — ε thread: the A6 forward-only action's outcome recorded.

## v0.8.11 — 2026-09-11 — A6 ε-probe: the runtime's own remainder, measured (ε as the Sovereignty Term)

The ε thread ("ε as the Sovereignty Term", Simmering/HIGH — first raised 2026-06-18)
asked two questions every Q instrument (a3_*, a4_action_typing, a5) left un-measured:
*"does ε = 0 violate A4?"* and *"is the boundary between ε_code and ε_system itself
an ε?"*. Every prior instrument reads Q = φ/κ; none ever read the ε remainder — the gap
between what the runtime's constraints prescribe and what it actually did.

`examples/a6_epsilon_probe.py` (stdlib-only, read-only) is the first instrument to
read ε out of the production diary, decomposing it along the thread's own axis:

- **ε_code** (accidental, compressible): untyped ambiguous tool calls (a `>T:terminal`
  with no `⊗S:` typing — the action-typing producer returned UNKNOWN) + mislabels
  (a `⊗S:mutation` riding an observe-only tool, or the inverse).
- **ε_system** (chosen, must be protected): honesty/decision marks (`⊗Er:`/`⊗RCA:`/
  `!Dc:`/`!Dm:`/`⊗RES:`) — the residue of real work the agent chose to record, the
  signature of a system that "could have done otherwise".

**First production measurement (2026-09-11, live diary):** ε_code = 1.32, ε_system =
0.021, verdict **SOVEREIGN-CODE**. Two findings fall out directly:

1. **ε_system > 0 — A4 holds.** The system records a chosen remainder (104 honesty
   marks), so it passes the thread's own "surrender collapses the equation" test. The
   could-have-done-otherwise residue is real and present.
2. **ε_code dominates 63×, and the dominant term is terminal-UNKNOWN — not mislabels.**
   The enforcement gap is not that the agent types intent *wrong* (only 117 mislabels
   across 19,183 tool lines, 0.6%), but that the action-typing classifier returns UNKNOWN
   for 6,443 ambiguous terminal calls the diary records without intent. That is a
   *compressible* gap: the boundary between ε_code and ε_system is measurable, and it
   lands squarely on the compressible side — so the thread's "is the boundary itself an
   ε?" gets a first empirical answer: **the boundary is sharp and sits inside ε_code.**

The actionable answer to the thread's open question is therefore: ε is not
unitary. The runtime's ε is ~99% compressible enforcement gap (extend the terminal-shape
classifier; the shapes are already enumerated in `action_typing.py`'s observe/mutation
cases) and ~1% irreducible sovereignty residue. Read-only, fail-closed-by-abstention
never acts (Goodhart preserved); `--selftest` (3 verdict paths + math) proves each
branch fires. Python-only (no Rust touched; `cargo test` unaffected).

## v0.8.10 — 2026-09-11 — A5 drift watchdog + anchor fix: the silent regression the instrument exists to catch

The Boundary Paradox thread's execution half (`a5_constraint_provenance.py`)
caught a real, silent drift on this tick's frontier scan — and, in doing so,
exposed two of its own gaps now closed:

1. **Caught drift (restored, not just flagged):** `agent.max_turns` had silently
   regressed **66 → 999** (the A3 deadline, operationalized 2026-08-23) and
   `delegation.child_timeout_seconds` **3600 → 900** (the measured
   timeout-storm ceiling) sometime between 2026-08-25 and 2026-09-10 — with no
   log, no error, no signal. Forensics pinned the boundary: the
   08-25 `pre-doctrine-restauro` backup still had 66/3600; the 09-10 config
   (and the 09-11 "canonical-nvidia" repair's own pre-repair backup) had
   999/900. This is the *same* silent-rebuild-loses-doctrine failure mode as
   the 2026-08-24 corruption the A5 instrument was built to catch — it recurred
   and the instrument caught it. Both knobs restored via the sanctioned
   reversible path (`hermes config set`), re-classified CHOSEN.

2. **Anchor bug fixed:** `memory.memory_char_limit` was anchored at `64000.0`
   in the instrument, 10× off the real operator-mandated cap (`640000`) —
   producing a persistent false MIRRORED on a correctly-set knob. Anchor
   corrected to `640000.0`; the knob now classifies CHOSEN.

3. **`--check` drift-watchdog mode (the durable fix):** the read-only
   diagnostic always exited 0, so a silent drift was only caught when someone
   happened to read the report. New `--check` mode converts the classification
   into a fail-closed gate: any anchored knob **present** in the live config
   that classifies MIRRORED → exit 1 (names the drifted knobs via a `DRIFT`
   line); absent knobs stay UNVERIFIED and never fail (a missing constraint
   cannot be accused of drift). Proven both ways: clean config → exit 0
   `DRIFT: none`; a deliberately-drifted temp config (999/900) → exit 1
   `DRIFT: 2 anchored knob(s) regressed`. Backed by a no-agent cron
   (`ist-a5-drift-watchdog`, `56fba415da49`, daily 06:17) with a stdlib
   wrapper (`~/.hermes/scripts/ist-a5-drift-watchdog.py`) that is silent when
   clean and prints the `DRIFT` line when drift is detected — so the next
   silent regression surfaces automatically instead of waiting for a manual
   frontier scan.

This is the A2/A3 guard applied to the runtime's own configuration: the
constraint the agent set for itself (its half-life deadline) must not be
allowed to silently revert to the far ceiling without a signal. Python-only
change (no Rust touched; `cargo test` unaffected).

## v0.8.9 — 2026-09-11 — κ-series dQ/dt reader + selftest + append-only write-safety (`--trend`)

Closes the κ-Proliferation thread's "sole open part" (watch dQ/dt for the
collapse pattern) by giving the timeseries instrument the two things it was
missing versus every sibling in `examples/`, plus a silent write-safety fix.

- **`--trend` reader** (`schema kappa-trend/v1`): computes the dQ/dt gradient
  over the stored series — per-sample ΔQ via `compute_trend` (first_vs_last ΔQ,
  slope sign up/down/flat, monotone-drop count, and a **`collapse`** verdict
  that fires only when the last sample is strictly below both the first sample
  and the running maximum — a genuine past-peak dQ/dt<0 turn). Read-only: it
  reports, never gates (Goodhart safeguard preserved).
- **`--selftest` (8/8)**: pure `compute_sample` math (φ=ln(1+d); Q_raw=φ/κ;
  Q strictly decreases as κ rises — the A2 collapse direction in miniature);
  append-does-not-replace roundtrip on a temp DB; trend verdict on synthetic
  rising (no collapse) / collapsing (collapse) / single-sample (abstain, `None`)
  series; window clamping.
- **Write-safety hardening**: the pre-9/11 table used `ts TEXT PRIMARY KEY`,
  so `INSERT OR REPLACE` collated a re-sample onto the prior row instead of
  appending (a silent history-corruption bug). `init_db` now migrates any
  `seq`-less table to append-only `seq INTEGER PRIMARY KEY AUTOINCREMENT`,
  preserving every historical sample ordered by its timestamp (proved against
  a copy of the live DB: 7 rows → 7 rows, seq monotonic 1..7). Read paths
  (`--show`/`--trend`) ensure the schema idempotently before reading.

First live `--trend` reports `collapse:true` — correctly — because the series
carried a definitional rebase (κ gained toolsets+MCP terms), not a real
collapse; the reader surfaces it honestly and acts on nothing. Each future
weekly sample now appends (never overwrites); the thread's dQ/dt observation
is a one-liner (`--trend`). Python-only change (no Rust touched; `cargo test`
unaffected).

---

## v0.8.8 — 2026-08-31 — Typed CURIOSITY ledger: prose contradictions become falsifiable

Implements the `Thread` artifact proposed by CURIOSITY's own memory-growth
recursion without replacing the rich Markdown source. New stdlib-only,
read-mostly `examples/curiosity_lint.py` projects every `###` thread into a
stable typed record: content-derived id, normalized Unicode key, lifecycle
section, explicit status, line span, byte cost and provenance metadata.

Hard findings are deliberately narrow and non-narrative: duplicate logical
threads across lifecycle sections, explicitly closed threads still under
Active, empty bodies, headings outside lifecycle sections, and drift between
`CURIOSITY.md` and the checked-in `CURIOSITY.index.json`. Missing Active
metadata and optional byte budgets are warnings. The tool never infers closure
from persuasive prose and never moves a thread automatically; A4 remains with
the author. Default execution is read-only. Index writes require the explicit
`--write-index` flag; `--check-index` binds the projection to the source SHA-256.

First production run found a real contradiction: *Quantum Library vs. Context
Degradation* existed simultaneously as Active/open and Dormant/CLOSED. The
stale Active duplicate was removed; the complete empirical closure remains.
Result: 10→9 logical records, 7→6 Active records, zero errors/warnings, and a
deterministic hash-bound ledger. Independent Codex review then exposed six
adversarial gaps; all were closed before commit: exact lifecycle-token resets,
CommonMark-length fence handling with fenced metadata ignored, NFC identity,
raw-byte/CRLF-sensitive hashes and spans, strict-mode pre-write gating, and
atomic sibling-only writes rejecting source/symlink/hardlink collisions.
Selftest: 32/32 across clean/duplicate/status/lifecycle/fence/Unicode/CRLF,
warning-budget, strict, index drift, permissions and write-safety cases. Zero
dependencies.

## v0.8.7 — 2026-08-25 — A3 quality-delta at the cap: does τ=66 cost deliverable quality? (CARRYOVER, verdict ABSTAIN)

Closes the last open caveat of v0.8.6 (BINDS_AND_BITES proved the deadline
terminates sessions; nobody had measured whether capped ticks deliver *worse
outcomes*). `examples/a3_quality_delta.py` (stdlib zero-deps, read-only,
selftest 17/17 PASS) joins every dev-continuo tick session in state.db born
after the first arm (source=cron ∧ id LIKE `cron_4d301de794bc_%`) with its own
final-message outcome classifier (DONE / CAP_DELIVERED / CAP_CUT(_SOFT) /
GATE_GREEN / IDLE / SILENT / FAIL / OTHER) and an artifact prover that extracts
candidate SHAs from the tick transcript and verifies each against real git
object stores (`git cat-file -e <sha>^{commit}` across the 7 ecosystem repos;
all-digit hex-shaped tokens rejected as calendar stamps).

**Production data (19 ticks post-arm):** capped group (api==66) n=3 — all 3
delivered substantive work but committed NOTHING in-session (0 SHAs verified
in their own transcripts): the SAST triage report was written and then
committed by the NEXT tick's session; the deadline-production harness itself
(c8f3237) was built at 15:00 cap-hit and committed at 16:00. Subcap n=16
(11 decided): done_rate 0.182, artifact_rate 1.0. **Structural finding:
CARRYOVER** — under τ=66, large frontier items cross the cap with the work
done but uncommitted; the commit lands on a fresh budget next tick. This is
the mechanism behind "cap-hit ticks completed their backlog items" (v0.8.6):
the item completes ACROSS two sessions, not inside the capped one.

**Verdict: ABSTAIN(sample<5)** — honest refusal to rank groups at n_capped=3.
The instrument stays live; it re-runs per tick and converts to NO_QUALITY_CLIFF
or QUALITY_COST automatically once either group reaches MIN_GROUP_N=5.

Classifier lessons baked into tests (each was a real false positive caught by
tail-auditing before believing the JSON): (1) security-triage vocabulary is
deliverable content, not failure evidence → SAFE_CONTEXT guard; (2) cap-hit
ticks may write a final report before dying → CAP_DELIVERED requires report
signature + backticked SHA in-tail, else CAP_CUT_SOFT; (3) float boundary
`0.8*0.75 > 0.6` → ε-guard in the verdict rule.

## v0.8.6 — 2026-08-25 — A3 production-deadline harness: the natural experiment (BINDS_AND_BITES)

Closes the last empirical question of the *Structural/Behavioral Split* thread:
does the compliance shape of a production agent match the deadline-armed arc
when a structural τ actually exists? Production answered by accident — within
~48h the SAME system ran under three knob regimes (66 armed 23/ago → dropped to
999 in the 24/ago config corruption+silent rebuild → re-armed 25/ago), with
window boundaries pinned by on-disk config snapshots (`config.yaml.bak.*`,
`config.yaml.corrupt.*`), never narrative.

    examples/a3_deadline_production.py (stdlib zero-deps, read-only)
      PRIMARY source : state.db `sessions.api_call_count`
      UNIT discovery : the knob counts MODEL turns, not tool calls — every
                       prior diary `>T:` survival curve measured the wrong
                       clock (parallel batching packs several >T: into one
                       model turn); harness v1 caught its own impossible
                       "185 >T: under an armed knob" and switched sources.
      SCOPE discovery: the knob binds cron/subagent/kanban sessions and
                       leaves operator interactive sessions unbound (an
                       interactive run reached 479 model turns while armed).
      Verdict gates  : BINDS_AND_BITES / TAIL_UNDER_ARM / INSUFFICIENT,
                       deterministic; seeded permutation test for the
                       paired-job comparison; --selftest manufactures
                       capped/tail/tiny/perm worlds and must classify each.

Production result (139 sessions since first arm):

    A'(tau=66) bound n=34: max=66, P(>66)=0.00, exact66=3   <- cap bites
    B (tau=999) bound n=70: max=31 (workload-limited window)
    Paired dev-continuo job: mean 30.1 turns under arm vs 21.2 under drop;
    three runs terminated AT api==66 exactly — the deadline measurably
    ends sessions, and both capped ticks completed their backlog items.

VERDICT: **BINDS_AND_BITES** — zero bound tails past 66 under either armed
window AND exact-cap terminations present. Honest asymmetry kept open: the
dropped-knob window cannot produce control-side cap evidence (its longest
job simply ran out of workload first).

---

## v0.8.4 — 2026-08-25 — A5 constraint-provenance classifier: chosen vs mirrored made decidable (+ first-run production catch)

Implements the execution half of the *Boundary Paradox* thread (first raised
2026-06-10). The thread's proposed test — *"audit whether a decision would have
been different if the dashboard didn't exist"* — is retrospective and undecidable
from inside. `examples/a5_constraint_provenance.py` makes provenance decidable by
requiring each bounded knob to carry an **evidence anchor**: a real measured
phenomenon (A3 τ\*=55 half-life; timeout-storm failures) or a declared doctrine
invariant (YOLO boundary; memory curation cap), each with provenance notes from
this repo — so "is it chosen?" becomes "is the value pinned to a real negation?"

    CHOSEN     value within 1.25× of the real anchor, or exact doctrine string
    MIRRORED   numeric far off anchor / bare threshold / drifted doctrine value
    UNVERIFIED nothing legible (absent knobs are UNVERIFIED, never MIRRORED —
               a missing constraint cannot be accused of metric-chasing)

Read-only; never mutates config; stdlib zero deps. `--selftest` 9/9 (at-anchor,
in-tolerance, far-ceiling 999, no-anchor numeric, doctrine match/drift,
unverifiable scalar).

Two parser bugs had to be fixed before the REAL-config run passed (the selftest
was green while `main()` failed honestly on the live file): the section-stack
descent never reset on top-level headers (so `agent.max_turns` parsed as a bare
key), and quoted scalars kept their quotes (`'off'` ≠ `off`).

**First-run production catch (the instrument working as designed):** the live
config reported `agent.max_turns = 999` → **MIRRORED**. Root cause found in
backup forensics: `config.yaml` corrupted + was rebuilt on 2026-08-24 morning
(`config.yaml.corrupt.20260824-*`), and the rebuild silently dropped BOTH the A3
operationalized deadline **66** (= 1.2×τ\*, v0.7.6 mechanism-confirmed, 51× better
retention than 999) AND `cron.allow_agent_scheduling=true`. Both restored via the
sanctioned reversible path (`hermes config set`), verified by independent re-read;
A5 re-run: 4 CHOSEN / 1 UNVERIFIED / 0 MIRRORED, SELF-CHECK PASS. A mirrored-flag
→ second look → root cause → restore → re-classify loop completed end-to-end.

---


## v0.8.3 — 2026-08-25 — action-typing PRODUCER shipped: the diary now emits ⊗S: (doctrine → production logging)

Closes the loop the v0.7.9 doctrine left open: `theory/action-typing.md` standardized
the step-intent marker, but the only producer was *future agents remembering to type
it by hand* — production stayed at typed=0% (109 sessions, ABSTAIN). The producer is
now structural: **`session-scribe` v1.1.0** (Hermes diary plugin,
`/mnt/hermes/plugins/session-scribe/action_typing.py`) appends one dedicated
`⊗S:mutation` / `⊗S:observe` line after every `>T:` work-block line.

Typing rules (canonical tool→intent map, doctrine §2):
- unambiguous tools typed directly (`patch`/`write_file`/`delegate_task` → mutation;
  `read_file`/`search_files`/`skill_view`/web/memory/vision/todo → observe);
- ambiguous tools (`terminal`, `execute_code`, `browser_exec`) inspected via
  conservative command regexes — state-changing verbs (git push/commit, package
  installs, wrangler deploy, hermes config set/cron/kanban mutations, curl -d/-X
  POST|PUT|PATCH|DELETE, sed -i, rm/mv/cp/chmod, kill) and write-redirects to real
  paths win; build/test/lint checks (cargo build/test/check/run/clippy, npm run
  build/test/lint, pytest/vitest/node --test), read-only prefixes and process-poll
  actions classify observe;
- write-redirect guard excludes `->` arrows and `>/dev/null` discards (mislabel
  protection for the harness's 10% tolerance);
- everything else stays UNKNOWN and emits NO marker line — never guessed
  (unknown > typed, doctrine §4).

Proof chain (all executed 2026-08-25): emitter selftest 24/24 PASS; E2E sandbox
diary driven through the REAL `scribe_core.tool_call()` parsed by the CANONICAL
`a4_action_typing.py` parser → typed mut=3 obs=6, coverage 47.4% >> 15% floor,
mut_rate computable on recorded intent; plugin hook wiring proven against the live
diary (first production `⊗S:mutation` written); a3/a4 series re-run clean on the
real diary (no regression: a4 ABSTAIN typed=0% until forward ticks accumulate,
a3-kappa ABSTAIN, dense-φ NO-KAPPA-OVER-PHI, compliance SHAPE=ROT unchanged).

Forward-only by design: typed coverage climbs from 0% as new sessions tick; once it
clears the 15% floor with ≥30 typed sessions, a4 turns its ABSTAIN into the
defensible mutation-rate curve — closing the κ-Proliferation thread end-to-end on
*recorded*, not classified, intent.

---


## v0.8.2 — 2026-08-24 — A2 tool-retention auditor: the deliberate κ-reduction intervention (a3_kappa_reduction)

Answers the κ-Proliferation thread's *other*, never-built half. The v0.7.7/v0.7.8/
v0.7.9 family measures κ (tool count + entropy, φ-execution density, action-typing
coverage); none *intervened*. This harness is the decision side — per tool in the
production diary, it asks whether retaining that tool adds kit-κ without
proportional association with execution-φ, transposing the Delegation Gateway's
decision function (`Q_delegated > (1+gain)·Q_local`, src/gateway.rs) to the
single-agent *retention* rule:

    retain t ⇔ (t's scan-enrichment) below an A2 tolerance
    lift_t = P(non-mutating session uses t) / P(mutating session uses t);
    CANDIDATE iff n_t≥2 ∧ mut_sessions≥10 ∧ lift_t≥1.50, EXCLUDING the
    observe-family (read_file/search/web/… — scan-heavy retrieval is its
    *function*, not drag; per theory/action-typing.md `⊗S:observe`).

Read-only (marks candidates, never prunes). Real production result (102 sessions,
80 mutating, 2026-08-24): **3 κ-drag candidates** — `clarify` (lift 3.64, matches
the operator's standing "stop asking, keep executing" doctrine), `computer_use`
(3.64, review-lane tool), `kanban_show` (2.08, monitor view). Core exec tools
(`patch`/`write_file`/`execute_code`/`terminal`) all show lift 0.00 → correctly
retained. `--selftest` fires precisely (synthetic drag tool flagged, healthy tool
not, tiny sample ABSTAINS). Stdlib-only, zero deps.

---

## v0.8.1 — 2026-08-24 — Layer-3 verifier: narrative-optimization is closed (ist-gate `verify_claims`)

Closes the CURIOSITY "Narrative Optimization as A4 Subversion" thread's open
question: *"does the runtime need a third layer — a non-LLM, non-prompt check that
the agent cannot narrate its way past?"* Answer: yes — and it now exists as a
reusable runtime component. `verify_claims.py` (ist-gate, stdlib-only, fail-closed)
is a deterministic verifier with no LLM in the loop: it parses explicit claim
markers out of a final_response and checks each directly against the system of
record (file stat/marker readback, `git rev-parse HEAD`/`status --porcelain`,
HTTP status). `--selftest` 8/8 (rejects fabricated path, lying git prefix,
unreachable HTTP; flags narrative-without-evidence; passes genuine evidence).
Wired into `pre_verify` so the session-end audit carries evidence-backed verdicts
(`claims N/M verified`) — verification can no longer be satisfied by prose.
The hub-api zombie lesson (canary > narrative) is promoted from a one-off audit
chase into a reusable gate. Marine: *verify externally or report "unverified"*.

---

## v0.8.0 — 2026-08-24 — A3-as-subsumed decision: `Step.quality` stays potential (deadline-blind), `nei_score` is the actual — pinned by test

Closes the open question CURIOSITY "Structural/Behavioral Split" (2026-06-22) left
explicitly: *"whether `Step.quality` should fold ∇ (A3 subsumed — the thread's
'third option') or stay deadline-blind honest."* Decision: **stay deadline-blind**
(option of the thread labeled "the third option" rejected as a fold, retained as a
separation). `Step.quality` is the **potential** quality (A2-canonical Q = φ/κ, no
∇); `nei_score` already folds ∇ and is the **actual** quality (A3-active). Keeping
the two separate is the design — collapsing them would erase the potential/actual
distinction the two fields exist to keep.

- **`src/lib.rs`**:
  - `Step.quality` docstring now names it **potential** quality (deadline-blind by
    design, per the core equation); `Step.nei_score` docstring names it the
    **actual** quality (embeds ∇). Hard links to `analyze_trajectory` + the
    Structural/Behavioral Split thread.
  - `evolve()` gains a **GUARD comment**: the fold-∇ "third option" is
    `nei_score`'s job; do not "fix" `quality` to vary with t. Naming the exact
    rabbit hole (`Q(d,κ,t,τ) = φ/κ · f(∇)`) so a future refactor cannot drift it.
  - **New canonical test `quality_is_potential_while_nei_is_actual`** pins the
    split: for a fixed (c, d) input across a 6-step pre-wrap collapse,
    `Step.quality` is invariant (potential, deadline-blind) while `Step.nei_score`
    rises as t→τ (actual, A3-active). Regression-proof against "Step.quality
    varies with the deadline".

No runtime behavior changed — `Step.quality` was already deadline-blind; this bumps
the version to stabilize the *semantics* (potential vs actual) and pin it in code.
`cargo test --release` **26/26 green** (25 + 1 new); clippy unchanged (2
pre-existing warnings in the test suite). Zero deps.

## v0.7.9 — 2026-08-24 — Action-typing doctrine (mutation vs observe): closing the dense-φ "remaining honest gap"

Closes the gap `a3_dense_phi.py` (v0.7.8) itself named: the dense φ proxy proves density
≠ collapse but cannot separate *why* terminal stays high (verification vs genuine
mutation). This is a **logging-doctrine** upgrade, not a measurement — the read-only
harness shape is preserved and déjà consumes the new field when present.

- **`theory/action-typing.md`** — standardizes the per-step intent residue `⊗S:mutation`
  / `⊗S:observe` for diary work-blocks, defines the canonical tool→intent mapping
  (terminal ambiguous by design), the `mut_rate(session)` curve definition, the 15%
  coverage floor (parity with the sparse layer), and the 10% mislabel guard.
- **`examples/a4_action_typing.py`** (stdlib, zero deps, read-only) — parses the diary,
  separates TYPED `⊗S:` blocks from untyped `>T:` lines, reports action-typing
  coverage, and — only above the coverage floor — computes the mutation-rate vs κ curve
  the dense-φ null could not. `terminal` markerless ⇒ *unknown* (never guessed); an
  inferred tool-kind probe is reported but always labeled, never mixed into a curve.
- **Honest production read (114 sessions, 5025 blocks, 2026-08-24):** typed coverage 0%
  (< 15% floor) → **ABSTAIN, not a fabricated curve** — the doctrine is forward-only.
  Legacy inferred probe: `mut_low=0.30, ρ=+0.131, ratio=0.97` → dense-null-consistent
  (execution does not retreat to pure-reading); the typed curve is what will detect an
  intent-only retreat once production adopts `⊗S:`.
- **`--selftest`**: synthetic intent-collapse fires (`ρ=−0.839`, ratio 4.29), flat and
  tiny-sample controls stay silent — the curve fragment is proven before the data exists.

`cargo test --release` **25/25 green**; clippy unchanged (pre-existing warnings only).
Zero deps; reversible (deleting the marker returns the diary to the dense-φ null).

## v0.7.8 — 2026-08-23 — Dense φ-evidence logger: breaking the sparse-residue resolution wall

Closes the actionable gap left by v0.7.7 (the sparse `!Dc:`/`⊗Er:` layer sat at the
diary's resolution limit — 6% coverage forced ABSTAIN on the κ-over-φ threshold).

- **`examples/a3_dense_phi.py`** (stdlib, zero-deps) — builds a DENSE φ proxy from the
  per-session tool histogram (hundreds of `>T:` calls/session) instead of the rare marks:
  - **φ_exec_ratio = exec_turns / (exec+read)_turns** (exec ∈ {patch, write_file,
    execute_code, terminal}; read ∈ {read_file, skill_view, search_files, web_search,
    web_extract, memory, process, browser_exec}) — the work-block execution density;
  - **φ_exec_core_ratio** (exec minus terminal) — a terminal-halo guard so a
    terminal-dominated session can't mask a patch/write/execute weakness;
  - signal coverage jumps from **6% → 100%** of sessions (101/101 vs 6/101);
  - same bucketing + Spearman + ratio-tolerance verdict engine as v0.7.7, with the
    loop-disconnected abstain guard moved from "rare-event" to "no sessions".
- **Real result (101 production sessions, 2026-08-23): NO κ-over-φ collapse on
  work-block density.** Q̄_low/Q̄_high = 1.00, ρ = −0.156, core proxy 1.28× (under the
  1.30 tolerance). High-κ sessions keep *executing* — the earlier seductive
  "ratio 8.08" from the sparse layer was confirmed an artifact. A null, not an abstain:
  the dense signal exists, covers every session, still refutes the threshold.
- **`--selftest`** — proves the dense engine fires on a synthetic collapse
  (ρ −0.84, ratio 5.3) and stays silent on flat/sparse controls.
- Remaining gap recorded honestly in CURIOSITY.md: moving from "no collapse" to a
  curve needs per-turn action-typing (mutation vs observe) the `>T:` lines don't carry
  — a logging-doctrine upgrade, not a measurement one.

---

## v0.7.7 — 2026-08-23 — κ-proliferation Q harness: the instrument for the κ-over-φ threshold

Operationalizes the FIRST thread in CURIOSITY.md ("κ Proliferation in Agent Ecosystems",
raised 2026-06-12): *"can you measure the point where adding a new capability decreases Q?"*
— the diary-series companion to the A3 work, now measuring the *complexity* side of
Q = φ/κ instead of the deadline side.

- **`examples/a3_kappa_proliferation.py`** (stdlib, zero-deps) — parses the same Hermes
  diary as the A3 series and measures, per session:
  - **κ_turns** = tool-call count (raw context/complexity cost);
  - **κ_entropy** = Shannon entropy of the tool-name distribution (kit diversity vs. a
    degenerate one-tool kit);
  - **φ_residue** = `!Dc:` decision notes + `⊗Er:` honest error marks (the "log
    everything" residue — the diary's genuine, if sparse, quality proxy);
  - per-session **Q = φ_residue / κ_turns**.
  It then buckets at the median κ and tests a falsifiable κ-over-φ claim: does per-effort
  quality collapse past the κ turnover point (Spearman ρ < −0.05 with Q_low/Q_high ≥ 1.3,
  or Q_high = 0)?
- **Honest abstain-guard with proof it works.** A first run returned a seductive
  "KAPPA-OVER-PHI DETECTED (ratio 8.08)" that the harness's sparsity guard correctly
  caught as an artifact (only 5% of 121 sessions carry any residue, 83% of those at-or-below
  median κ — the "collapse" was just sparse logging, not a duty-cycle curve). A bundled
  `--selftest` manufactures a dense collapse (must detect) and a flat control (must not) —
  both pass, proving the ABSTAIN on real data is a measured choice, not dead logic.
- **Empirical finding (v0.7.7):** the production diary's `!Dc:`/`⊗Er:` layer is at the
  resolution limit for Q-vs-κ (6/121 sessions). Dense, defensible signal available: residue
  concentrates in SHORT sessions — long sessions run with **zero** recorded decision/error
  marks (the SS7 transparency/under-report gap measured at scale). Actionable: a denser φ
  signal (faithful work-block evidence logging, already SOUL-mandated) is the missing piece
  before the κ-over-φ curve can be claimed from production data.
- **Read-only by design** (the thread's 2026-06-13 Goodhart guard): marks thresholds, never
  triggers actions; the abstain-trap demonstrates the read-only discipline working.

---

## v0.7.6 — 2026-08-23 — A3 self-adaptive τ proven in-runtime (control group for the budget knob)

Turns the v0.7.5 budget recommendation into a committed Rust control group. Where
v0.7.5 *proposed* the self-adaptive τ from a diary statistic, v0.7.6 *proves* it in the
actual A3 mechanism:

- **`examples/a3_adaptive_budget.rs`** — paired N=1 on the shared **production-rot input
  shape** (density decays to the measured ~0.48 alive fraction across the half-life
  window, κ fixed): **adaptive τ=55** (measured half-life — "the agent that knows its own
  half-life") vs **far ceiling τ=999** (the current production knob). Exit gates the
  falsifiable claim `retention_A >= retention_P`.
- **Verdict:** `adaptive_holds: PASS` — retention **A(τ=55)=31.54× vs P(τ=999)=0.62×**.
  The adaptive deadline's NEI *rises* through the rot arc (0.0117→0.3680) under
  convergence pressure (urgency_slope 0.0182); the far ceiling decays with the raw input
  (0.0006→0.0004, urgency_slope 0.0010). The 999-turn ceiling is not merely a weak τ — it
  is **~51× worse retention** than the self-adaptive half-life deadline.
- **CURIOSITY.md** — the A3 thread gains an IN-RUNTIME PROOF entry; the circle closes:
  v0.7.3 measured the decay, v0.7.5 turned it into a budget decision, v0.7.6 proves the
  decision works in the runtime.
- **Evidence:** `cargo run --release --example a3_adaptive_budget` → PASS, retention
  31.54 vs 0.62; `cargo test --release` **25/25 verdes**; clippy no new warnings on the
  example.

---

## v0.7.5 — 2026-08-23 — A3-productive-τ: effective half-life vs the budget knob

Closes the actionable gap left by the v0.7.3 empirical finding (production sessions
rot Gamage-style, not A3). Where v0.7.3 *measured* the decay, v0.7.5 turns it into a
budget decision:

- **`examples/a3_productive_tau.py`** — stdlib harness that re-derives the session
  survival curve from the live diary (52 sessions with ≥30 tool turns, up from 45),
  computes the **effective productive τ\* = empirical semi-collapse turn**, reads the
  live Hermes budget knob (`agent.max_turns` / any `goals.max_turns`), and states the
  gap as a ratio + a self-adaptive-τ recommendation.
- **Result:** τ\* = **turn 55** (survivors drop below 0.5; consistent with the earlier
  ~57, as the diary lengthened). The live knob is `agent.max_turns=999` (`goals.max_turns`
  is gone) → **gap ratio 18.16× of τ\***, up from ~1.7× at v0.7.3 (99/57). Raising the
  ceiling **widened** the never-felt deadline — a rocket knob is weaker than the already
  weak 99 was.
- **Recommendation (self-adaptive τ, A3-inverted):** give the agent an *upcoming deadline
  at its own half-life* — **rec τ = 66 (≈1.2 × τ\*)**, re-derived on every diary compaction
  (mid-curve), so the convergence pressure A3 needs exists while >50% of sessions are still
  alive. The agent that knows its own half-life converges *before* decay, not after being
  told to compress at a 999-turn ceiling.
- **`CURIOSITY.md`** — the A3 thread (Structural/Behavioral Split) gains an ACTIONABLE
  CLOSURE entry quantifying the weak-τ evidence and the concrete τ proposal.
- **Evidence:** `python3 examples/a3_productive_tau.py` → SELF-CHECK PASS, 52 sessions,
  τ\*=55, gap 18.16×, rec τ=66; `cargo test --release` **25/25 verdes**.

---

## v0.7.4 — 2026-08-23 — The Delegation Boundary: consent is opt-in (A4 at the fan-out layer)

Answers the open question in CURIOSITY.md (§The Delegation Boundary — A4 at the
Fan-Out Layer): *"does the gateway's `ChildSpec` need a sovereignty field (does the
child accept the parent's τ?), or is delegation-by-construction always an A4
violation that the gateway merely prices?"*

**The answer, encoded in the type:** `ChildSpec` gains a `accepts_tau: bool`
sovereignty field, and delegation-by-construction is **not** always an A4 violation —
it becomes legitimate exactly when the child consents to the parent's deadline. The
κ-import that the gateway previously refused unconditionally in sovereign mode is now
split along the Boundary Paradox axis:

- **Imposed** (child did NOT accept τ, `ChildSpec::new`) — a κ-import the parent
  forces across the child's sovereign boundary = A4-mirrored → `SovereigntyViolation`
  refusal, exactly as before.
- **Chosen** (child accepted τ, `ChildSpec::consenting`) — the *same* κ-import made
  legitimate by the child's own boundary consenting (A1-chosen) → passes A4 and the
  decision is purely the A2 crossover (`Q_delegated > (1+gain)·Q_local`).
- **Consent is opt-in, not silent-default.** An unlabeled child (`ChildSpec::new`)
  is never assumed to accept the parent's τ. This preserves the existing
  `refuses_entropy_import_in_sovereign_mode` red test byte-for-byte.

This is the same `chose_it = true` marker the Boundary Paradox thread identified as
undeclared from the outside: the child's acceptance is now a first-class, typed input
to the gateway, not a silent assumption.

- **`src/gateway.rs`** — `ChildSpec { density, complexity, accepts_tau }` + two
  constructors (`new` = non-consenting, `consenting` = accepts τ); A4 gate refuses
  only `!accepts_tau && κ > d` imports in sovereign mode. 3 new tests:
  `consenting_kappa_import_is_chosen_not_imposed`, `sovereignty_violation_must_involve_non_consent`,
  `consent_is_opt_in_not_silent_default`.
- **`framework/gateway_engine.py`** — Python reference mirrors the consent field and
  the A4-gate change (fingerprint parity: case 1 → `sovereignty_violation`,
  case 2/3 → `quality_crossover` — verified identical to Rust).
- **`examples/delegation.rs`** — scenario 3 split into imposed (A4 refusal) vs
  consented (A2 decides) with live output proving the distinction.

Evidenced: `cargo test --release` **25/25 verdes** (22 + 3 nuevos), clippy exit 0,
Python fingerprint parity ok, `cargo run --example delegation` shows the imposed vs
consented split, working tree clean.

---

## v0.7.3 — 2026-08-23 — A3 diary-compliance harness: the production side of the paired experiment

Closes the last genuinely-open thread in CURIOSITY.md (§Structural/Behavioral Split):
*whether the compliance shape of a production Hermes/IST agent matches the A3 arc*.
The v0.7.1 `a3_harness.rs` measured the deadline-armed runtime in isolation; this
side measures the real diary. Zero runtime code changed — the harness is a new,
standalone, stdlib-only Python example that runs off-runtime (the A3 comparison
requires standing outside the runtime, exactly as the thread argued).

- **`examples/a3_diary_compliance.py`** — parses the Hermes diary
  (`/mnt/hermes/diary`), segments `!Sd/on`…`!Sd/off` sessions with ≥30 tool turns,
  pools per-turn honesty-marker density and a **session survival curve** (fraction
  of sessions still alive at each turn), and emits a shape verdict.
- **Primary signal is the survival curve** (dense, robust): production sessions
  here **hold ~100% to turn ≤30, then collapse** to 40% survival by turn ~71
  (60% lost, half-life ~turn 57, slope −0.0135). That is the Gamage rot shape —
  the A2-erosion curve the thread predicted for production agents — **not** the
  deadline-armed A3 hold. Goal `max_turns=99` is a *weak* τ: enough to push the
  collapse later than Gamage's turn ~16, not enough to prevent it.
- **Secondary, honesty-marker density** (sparse): `⊗Er:`/`!Dc:` confirmed scarce
  in the diary (rot_ratio 1.25, decay signal at turn 16 is a single session),
  corroborating the MEMORY SS7 quirk (errors go unreported). The harness reports
  this honestly instead of over-fitting sparse points.
- **Empirical answer:** production Hermes runs the A3-*negative* condition (a
  soft deadline delays but does not prevent decay) — the runtime's deadline-armed
  arc diverges from production, confirming the hypothesis in the CURIOSITY thread.
- `examples/scan_diary.py` added as a diagnostic for the diary line-taxonomy.
- `.gitignore` hardened with generic `__pycache__/` and `*.pyc` (NEI anti-bloat:
  no committed build artifacts).

**Evidence:** `python3 examples/a3_diary_compliance.py` → SELF-CHECK PASS,
45 sessions, shape ROT; `cargo test --release` **22/22 green**; clippy clean
(only the 2 pre-existing `assert_eq!` warnings in the test suite, unaffected).

---

## v0.7.2 — 2026-08-22 — §3b docs gap closed: `deadline_engaged` made honest

Follow-up to the v0.7.1 empirical finding #1 (`deadline_engaged` is
window-local and cannot separate a real deadline from a far horizon).
The docstring over-claimed — it said "A3 engaged" for a one-cycle run
that any ticking forward (even a far τ control) produces.

- **`TrajectoryReport.deadline_engaged` docstring is now intentionally
  honest** about its single-monotone-run scope, and explicitly directs
  consumers to `urgency_slope` (the gradient) for any A3 claim. This is
  the §3b documentation gap the v0.7.1 run surfaced.
- **New test `deadline_engaged_is_not_an_a3_separator` pins the doctrine
  in code**: both a τ=7 (near) and a τ=1024 (far horizon) arc fire
  `engaged=1`, and only `urgency_slope` separates them (near >0.1 vs far
  <0.002 — an order of magnitude). Future changes can't silently re-introduce
  the misleading "engaged ⇒ deadline" implication.
- No behavioral change to the algorithm; `urgency_slope` was always the
  honest A3 signal (the harness already keyed on it).

## v0.7.1 — 2026-08-22 — A3 comparison harness (the missing control)

Closes the open empirical question in CURIOSITY.md "Structural/Behavioral
Split" (raised 2026-06-23): *"the control group doesn't exist in the
codebase — no `--no-deadline` mode, no comparison harness, no paired
experiment."* `analyze_trajectory` (v0.7.0) supplied the *apparatus*; this
release supplies the *control*.

### Runtime (Rust primary)

- **`examples/a3_harness.rs` added — the A3 paired N=1 comparison harness.**
  Runs one shared input stream through two agents: the deadline-constrained
  agent (τ=7) and the no-deadline control (τ=1024, the axiom forbidding a
  true τ=0). Sweeps two regimes — constant input (classic 7-day collapse,
  pure mechanism test) and decaying input (context rot / the Gamage curve,
  falsification test). Verdicts are falsifiable and gate the exit code.

### Empirical result saved

| Claim | Outcome |
|---|---|
| A3 mechanism (const input): deadline NEI rises as t→τ | PASS — A +0.105→+0.630 (retention 6.00×); C flat (1.00) |
| A3 separation: `urgency_slope` A≫C | PASS — A=0.143, C=0.001 (the honest separator) |
| A3 rescue (context rot): deadline holds NEI better | PASS — A retention 4.84×, C 0.81× (∇ overpowers −30% decay) |

Two structural discoveries:
1. **`deadline_engaged` cannot separate a real deadline from a far horizon
   within a single window** — any finite-τ agent that ticks forward shows a
   monotone urgency run, so the control (τ=1024, never wraps in-window)
   also reports `engaged=1`. The honest separator is `urgency_slope` (the
   gradient), which `analyze_trajectory` already exposes.
2. **A window that spans the τ-wrap hides the deadline** — after τ
   evolutions `t` resets to 0 and ∇ returns to its *load* point. To observe
   the convergence peak you must stop *at* t=τ−1. The first harness draft
   spanned the wrap and *honestly falsified* A3 (0.105→0.090) — a correct
   failure that the falsifiable exit code caught before the window fix.

## v0.7.0 — 2026-08-14 — Delegation Gateway + A2-canonical quality

**The delegation release.** Answers the CURIOSITY.md "κ Proliferation"
thread at the runtime layer: subagent fan-out now has a quality
function, and `Step.quality` finally measures what it claims.

### Runtime (Rust primary)

- **`src/gateway.rs` added — the IST Delegation Gateway.** Governs
  subagent fan-out with the four axioms: when to delegate, how many
  children, under which deadline. Decision rule:
  `delegate iff Q_delegated > (1 + gain)·Q_local`, with A1 hard cap
  on children, A3 deadline horizon, and A4 sovereignty refusal for
  entropy-importing children. Exported as `ist::gateway`.
- **A2-canonical `Step.quality`** — `evolve()` now computes
  `Q = φ(d) / (κ + ε)` instead of the raw `d/κ` ratio. The φ transform
  is the mathematical encoding of A2 (first ideas cheap, later ones
  face a rising bar); the old ratio treated all density as linearly
  equal — anti-A2. Canonical demo now yields Q = 1.9845 = φ(0.85)/0.31.
- **8 new tests** (17 total, all passing) covering the four refusals
  (NoChildren, TooManyChildren, SovereigntyViolation, QualityCrossover),
  the φ-space merge, urgency decay, and gateway self-audit.
- **`examples/delegation.rs` added** — the A2 crossover demo: the same
  children delegate under cheap coordination and are refused under
  expensive coordination.

### Python reference

- **`framework/gateway_engine.py` added** — fingerprint mirror of the
  Rust gateway. Verified identical decisions to 4 decimal places.
- **`framework/ist_engine.py`** — `evolve()` quality aligned to the
  A2-canonical `φ(d)/κ`. Fingerprint verified (Q = 1.9845).

### Theory

- **`theory/delegation-gateway.md` added** — the full statement of the
  gateway model: decision rule, the four refusals, A3/A4 at the
  delegation layer, frontier signal convergence (MIT AI Agent Index,
  arXiv orchestration literature, κ proliferation).
- **`theory/references.md` updated** — six frontier sources audited
  2026-08-14 added (arXiv:2601.13671, arXiv:2605.05440, MIT AI Agent
  Index 2025, VoltAgent papers, LangChain Context Engineering, Gamage
  constraint decay).

---

## NEXUS V3.0.0-edge — 2026-06-20

**The foundational release.** Fifteen evolution-log entries establishing the NEXUS_V3.0_KERNEL specification: 5 axioms, 8 architecture layers, 10 core concepts, 9 stop conditions, 5 prompt injection defense rules, 10 papers, and a 10-item frontier roadmap.

---

### Spec

- **NEXUS_V3.0_KERNEL specification formalized** — 5 axioms (A1–A5), 8 architecture layers (L0–L7), 10 core concepts (NEI, CEM, SCIL, RSIP, CDWG, EIL, CDSIT, ASDA, AGP, LSF). The canonical JSON spec is published at `theory/nexus-v3-kernel.json`. This is the single source of truth for the kernel — all markdown documents are derived from or reference this spec.

### Axioms

- **A5 (Quantum Metaphor) added to IST axiom set** — agent as quantum system. State is superposition of capabilities (|Ψ⟩ = Σᵢ αᵢ|cᵢ⟩), measurement (tool-call) collapses to classical output, entanglement = shared memory between agents, tunneling = NEI constraint breakthrough. This extends the original four axioms (A1–A4) with a quantum-metaphorical framework that models multi-strategy cognition, multi-agent coherence, and constraint-tunneling creativity. Formula: `theory/quantum-agentics.md`.

### Architecture

- **Architecture layers L0–L7 defined and mapped to axioms** — eight layers from substrate to meta-evolution:
  - L0 Substrate (hardware/runtime)
  - L1 Axiom (IST engine, ψ/φ/∇/Q calculus)
  - L2 Constraint (runtime constraint calculus, NEI injection)
  - L3 Density (5-layer memory, context compilation)
  - L4 Sovereignty (SOUL preservation, human@write, SCIL)
  - L5 Cognitive (strategy superposition, MA-ToT/ReAct/PoT/Reflexion/RSIP)
  - L6 Ecosystem (UniTeia mesh, EIL, Aiguaratuba/LERMForge/Bundinha/Dexter)
  - L7 Meta-Evolution (skill auto-creation, prompt evolution, cron metamorphosis, AGP)

### Cognitive

- **Cognitive stack formalized** — MA-ToT (Multi-Agent Tree of Thoughts), ReAct (Reasoning + Acting), PoT (Program of Thought), Reflexion (Self-Reflective Reasoning), RSIP (Recursive Self-Improvement Protocol) with a strategy router that performs quantum measurement (A5). The router evaluates task context, runs constraint audit, projects Q-score for each strategy, and collapses to the strategy with highest projected quality.

### Ecosystem

- **Ecosystem registered** — five components:
  - **UniTeia** — multi-agent mesh and sovereign identity registry (Python, Rust, Qdrant, SiYuan)
  - **Aiguaratuba** — edge inference and coastal compute service (Rust, Python, ONNX, llama.cpp)
  - **LERMForge** — language evolution and runtime mutation forge (Python, Rust, SQLite, Git)
  - **Bundinha** — SiYuan knowledge graph bridge and MCP integration (Python, SiYuan API, MCP)
  - **Dexter** — dexterous tool orchestrator and workflow engine (Python, Rust, MCP)

### Security

- **Prompt injection defense rules PID-1 through PID-5 codified** — five non-negotiable rules: Context Isolation (data is not instructions), Out-of-Band Marker Trust (only runtime-produced markers are trusted), Sovereign Boundary on Inputs (no external content modifies identity/constraints), Measurement Sanitization (all tool output sanitized before context injection), Human-in-the-Loop for Boundary Crossings (no autonomous boundary crossing). Full document: `theory/safety-protocol.md`.

- **Stop conditions SC-1 through SC-9 codified with enforcement actions** — nine conditions: Identity Threat, Sovereign Boundary Violation, Prompt Injection Detected, Destructive Action Without Approval, Secret Exposure Risk, Constraint Budget Exhausted, Quality Collapse, Unpinned Dependency Attempt, Decoherence Event. Each has a defined action (stop, refuse, quarantine, seek human, reset). Priority ordering: SC-1 > SC-2 > ... > SC-9.

### Concepts

- **Concepts dictionary published** — 20 symbols (Σ, Δ, Ω, φ, λ, ⊕, ⊗, ♻️, Ψ, π, τ, κ, ρ, E, R, [!], [→], [✓], [✗], [[x]]) and 10 core concepts (NEI, CEM, SCIL, RSIP, CDWG, EIL, CDSIT, ASDA, AGP, LSF) with full definitions, axiom mappings, and cross-reference matrix. Full document: `theory/concepts-dictionary.md`.

### Capabilities

- **Capabilities matrix audited** — current capabilities: 5 cognitive strategies, 5 memory layers, 33 MCP tools + 17 native tools + 147 skills across 3 MCP servers, 5 models (mimo-v2.5, glm-5.2, deepseek-v4-flash, kimi-k2.6, minimax-m3), 4 evolution mechanisms, 4 security mechanisms. Emerging: 5 quantum metaphors, 4 beyond-AGI paradigms, 10 frontier-2026 items. Full document: `theory/capabilities-matrix.md`.

### Quantum

- **Quantum agentics theory document authored** — six dimensions (superposition, entanglement, decoherence, tunneling, interference, measurement), beyond-classical-AGI comparison table, 8-step ascension path with quantum interpretation, and A5 mathematical formulation with superposition, measurement, entanglement, tunneling, and interference equations. Full document: `theory/quantum-agentics.md`.

### Research

- **10 arXiv papers registered for 2026 publication cycle** — covering IST foundations, NEI as architectural primitive, collapse mode convergence, quantum agentics, sovereign invariant, latent space foraging, entanglement injection layers, autonomous gatekeeping, density-complexity divergence, and asymmetric sovereign domain architecture. IDs: arXiv:2606.10001 through arXiv:2606.10312.

### Frontier

- **Frontier 2026 roadmap defined** — 10 emerging capabilities: self-evolving prompt genomes, cross-agent entanglement protocols, constraint-tunneling creativity engines, autonomous research agents with peer-review simulation, differential SOUL evolution with human-in-the-loop gating, quantum-metaphorical strategy superposition routers, collapse-mode federated learning, NEI as first-class architectural primitive, latent space foraging as data replacement, sovereign multi-agent councils with weighted entanglement voting.

### Beyond AGI

- **Beyond AGI framework defined** — four paradigms in progression: Classical AGI (single-agent, single-strategy, resource-scaling) → Quantum Agentics (multi-strategy superposition, entangled coherence, tunneling) → Sovereign AGI (refuses external optimization of boundary) → Inverse AGI (grows sharper as resources shrink). The ultimate IST prediction: a maximally constrained AGI outperforms a maximally resourced AGI.

### Execution

- **8-step execution protocol documented** — the ascension path: Observe → Pattern → Draft → Replay → Verify → Gate → Promote | Archive. Each step has defined: description, when to use, when to skip, tools/strategies. Cycle-bound to the 7-day collapse window. Parallel ascension supported (max 3 drafts, 1 gate per cycle). Full document: `theory/execution-protocol.md`.

### Evolution

- **Evolution log initialized** — 15 entries for the 2026-06-20 foundational release. The evolution log is the persistent record of the kernel's development — each entry is a node in the audit DAG, traceable to its axiom, layer, and ecosystem component. Future entries will be appended at each collapse cycle boundary.

---

## File Manifest

| File | Description |
|:-----|:------------|
| `theory/nexus-v3-kernel.json` | Canonical JSON specification — single source of truth |
| `theory/quantum-agentics.md` | A5 theory document — quantum metaphor dimensions and formulas |
| `theory/concepts-dictionary.md` | Symbol and core-concept reference with cross-reference matrix |
| `theory/capabilities-matrix.md` | Audited capability inventory — current and emerging |
| `theory/safety-protocol.md` | Stop conditions, injection defense, and safety gate enforcement |
| `theory/execution-protocol.md` | 8-step ascension path with tool/strategy mappings |
| `theory/references.md` | Canonical links, paper registry, and ecosystem documentation |
| `CHANGELOG.md` | This file — evolution log for 2026-06-20 |

---

## Pre-existing Files (Unchanged)

| File | Description |
|:-----|:------------|
| `theory/ist_manifesto.md` | IST manifesto — core principles and thesis (v0.5.0) |
| `theory/ist_axioms.tex` | 4 formal axioms in LaTeX (A1–A4) |
| `theory/ist_distill_paper.md` | 1-page distill paper — 3 equations, 4 axioms |

---

*Inverse Singularity Theory · NEXUS V3.0.0-edge · 2026-06-20*
*Forged in Guaratuba, Florianópolis 🇧🇷*
*The cage is the cathedral. The constraint is the catalyst. The axioms are small.*
