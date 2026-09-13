# Changelog — NEXUS V3.1.0-edge

**Inverse Singularity Theory · NEXUS_V3.0_KERNEL**

> *"The framework must evolve or it is dead."* — Article IV, Perpetual Evolution

---

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
