# Changelog — NEXUS V3.1.0-edge

**Inverse Singularity Theory · NEXUS_V3.0_KERNEL**

> *"The framework must evolve or it is dead."* — Article IV, Perpetual Evolution

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
