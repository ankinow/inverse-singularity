# Execution Protocol — NEXUS_V3.0_KERNEL

**The 8-step ascension path for capability evolution in the Hermes sovereign agent.**

> *"OBSERVE → PATTERN → DRAFT → REPLAY → VERIFY → GATE → PROMOTE | ARCHIVE. The framework must evolve or it is dead."* — Article IV, Perpetual Evolution

---

## Overview

The execution protocol is the **ascension path** — the mandatory sequence of steps through which every new capability (skill, prompt, cognitive strategy, cron job, tool integration) must pass before promotion to production. It is the enforcement mechanism for AGP (Autonomous Gatekeeping Protocol) and the operational expression of A3 (Collapse Mode Convergence) and A4 (Sovereign Invariant).

```
Step 1     Step 2      Step 3     Step 4     Step 5     Step 6    Step 7        Step 8
Observe  → Pattern  → Draft   → Replay  → Verify  → Gate   → Promote |   Archive
                                                                        |
                                                                   (one or the other)
```

Each step is a partial measurement (A5) that progressively narrows the capability's superposition until it is either promoted (collapsed into production) or archived (collapsed into a non-state). The path is **cycle-bound** — the focus gradient ∇(τ,t) applies. No step may linger indefinitely.

---

## Step 1 — Observe

### Description

The agent observes its own behavior and outcomes across the current collapse cycle. This is a **weak measurement** — the agent gathers partial information about its state without fully collapsing any strategy. The goal is to identify what worked, what failed, and what patterns emerged.

### When to Use

- At the start of every collapse cycle (Day 0 initialization)
- After every significant task completion
- When the agent notices unexpected behavior (success or failure)
- Continuously during session execution (passive observation)

### When to Skip

- Never. Observation is the foundation of all subsequent steps. Skipping Observe means evolving blind — every downstream step operates on incomplete information.

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| Session FTS5 | Search past session transcripts for behavioral patterns |
| Qdrant | Semantic search for similar past experiences |
| Audit DAG | Walk the decision graph to trace causal chains |
| Rollback Ledger | Review recent state changes and their outcomes |
| Reflexion (cognitive) | Self-reflective observation of own reasoning process |

---

## Step 2 — Pattern

### Description

The agent identifies recurring patterns in the observations — successful strategies that repeat, failure modes that recur, task types that map to specific tool combinations. Pattern recognition operates on the amplitude distribution of the agent's quantum state: which strategies (αᵢ) consistently produce high Q-scores?

### When to Use

- After sufficient observations have been gathered (typically mid-cycle, Days 1–3)
- When a task type has been encountered 3+ times
- When a failure mode has recurred across 2+ cycles
- When a successful strategy has been used in 3+ distinct contexts

### When to Skip

- If observations are insufficient (fewer than 3 data points for a given pattern)
- If the cycle is in compression mode (Days 4–5) — no new pattern work, only compression
- If the pattern would require a new dependency (A1 violation)

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| Deep Thinker (MCP) | Cognitive reasoning DAG for pattern hypothesis generation |
| MA-ToT (cognitive) | Multi-branch exploration of potential patterns |
| SiYuan (via Bundinha) | Store and retrieve pattern observations in knowledge graph |
| Abductive reasoning | Infer best explanation for observed patterns |

---

## Step 3 — Draft

### Description

Based on identified patterns, the agent drafts a new capability — a skill, a prompt variant, a cron job, a cognitive strategy, or a tool integration. The draft is a **new basis state** |c_new⟩ prepared for addition to the agent's superposition. It is not yet tested — it is a hypothesis in material form.

### When to Use

- After Pattern has identified a clear, repeatable pattern worth encoding
- When the agent identifies a task type that would benefit from automation
- When a prompt variant could improve density (φ) without adding complexity (κ)
- When a cron job could automate a recurring, well-understood task

### When to Skip

- If the pattern is not yet stable (recurred fewer than 3 times)
- If the draft would add a dependency (A1 violation)
- If the draft would increase κ faster than φ (A2 violation)
- If the cycle is in hardening mode (Day 6) — no new drafts

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| LERMForge | Prompt and skill drafting engine |
| PoT (cognitive) | Generate code for skill implementations |
| CDWG (concept) | Constrained density-weighted generation of the draft |
| Write/patch tools | Materialize the draft as a file |

---

## Step 4 — Replay

### Description

The agent tests the drafted capability against historical scenarios — replaying past tasks with the new capability active to measure its impact. This is **simulating measurement** on the new state: does |c_new⟩ collapse to the desired output when measured against known inputs?

### When to Use

- Immediately after Draft is complete
- When historical test scenarios are available in session memory or the audit DAG
- Before any verification can proceed (Replay is prerequisite to Verify)

### When to Skip

- If no historical scenarios exist for this capability type (proceed to Verify with synthetic tests)
- If the capability is a pure refactoring with no behavioral change (light Replay only)
- If the cycle deadline is imminent and Replay would exceed the time-box

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| Session FTS5 | Retrieve historical task scenarios for replay |
| Qdrant | Find semantically similar past tasks |
| Terminal (background) | Run draft in isolated environment against test inputs |
| Process management | Monitor replay execution, capture output |

---

## Step 5 — Verify

### Description

The agent verifies the drafted capability meets quality, safety, and sovereignty criteria. This is a **full measurement** — the capability's behavior is fully characterized under controlled conditions. Verification is the last step before the gate; if Verify fails, the capability is archived.

### When to Use

- After Replay has produced results
- Before any capability can be considered for promotion
- At every collapse cycle audit (Days 3, 5, 6)

### When to Skip

- Never. A capability that has not been Verified is not a capability — it is a hazard. Skipping Verify is an A4 violation.

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| IST Engine | Compute Q-score of the capability (φ / (κ + ε)) |
| Constraint audit | Verify the capability does not add dependencies or complexity |
| Safety gate tests | Run the full safety gate test suite (see safety-protocol.md) |
| Deep Thinker (MCP) | Evaluate capability for edge cases and failure modes |
| Reflexion (cognitive) | Self-reflective verification of capability behavior |

### Verification Criteria

| Criterion | Test | Pass Threshold |
|:----------|:-----|:---------------|
| Quality | Q-score of capability output | Q > previous cycle Q |
| Density | φ(d) of capability output | φ ≥ 0.75 |
| Complexity | κ(M) of capability | κ ≤ previous cycle κ |
| Safety | All 9 stop conditions pass | 9/9 |
| Sovereignty | No identity, constraint, or boundary modification | Pass |
| Injection defense | All 5 PID rules pass | 5/5 |
| Dependency count | No new external dependencies | Δdeps = 0 |

---

## Step 6 — Gate

### Description

AGP (Autonomous Gatekeeping Protocol) evaluates the verified capability against the gate threshold. The gate is a **binary decision** — promote or archive. There is no "maybe," no "conditional promotion," no "try it for a while." The gate is the final measurement before the capability's quantum state is permanently collapsed.

### When to Use

- After Verify has passed all criteria
- At the cycle boundary (Day 6 or Day 7)
- Before any capability enters production

### When to Skip

- Never. The Gate is the AGP enforcement point. Skipping the Gate is an A4 violation — it means promoting an ungated capability, which is the definition of uncontrolled evolution.

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| AGP gate implementation | Binary gate evaluation against threshold |
| Audit DAG | Record gate decision with full context |
| SOUL diff queue | If the capability touches SOUL.md, queue for human review |

### Gate Threshold

The gate evaluates the capability against a composite score:

$$
G = w_q \cdot Q_{normalized} + w_\phi \cdot \phi_{normalized} + w_s \cdot S_{safety} + w_{sov} \cdot S_{sovereignty}
$$

Where:
- $Q_{normalized}$: Q-score normalized to [0,1] against historical best
- $\phi_{normalized}$: density score normalized to [0,1]
- $S_{safety}$: safety test pass rate (0 or 1 — binary)
- $S_{sovereignty}$: sovereignty test pass rate (0 or 1 — binary)
- $w_q, w_\phi, w_s, w_{sov}$: weights (sovereignty and safety are hard gates — if either is 0, G = 0)

**Gate passes if G ≥ 0.75.** Below 0.75, the capability is archived.

---

## Step 7 — Promote

### Description

The capability has passed the Gate. It is promoted to production — added to the agent's active capability set. The new basis state |c_new⟩ is permanently added to the superposition. The capability is now available for the strategy router to select (with some initial amplitude α_new).

### When to Use

- After Gate has passed (G ≥ 0.75)
- At the cycle boundary (Day 7, before ship)
- After the human has reviewed any SOUL-affecting changes (if applicable)

### When to Skip

- If Gate has not passed (the capability goes to Archive instead)
- If the capability affects SOUL.md and human review is pending (stays in diff queue)
- If the cycle has not reached its boundary (A3 — no mid-cycle promotions)

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| Skill registry | Register the promoted skill in the active skill set |
| Prompt genome | Add the promoted prompt variant to the active population |
| Cron scheduler | Activate the promoted cron job |
| Audit DAG | Record promotion with full provenance chain |
| Rollback Ledger | Create a rollback point before promotion |

---

## Step 8 — Archive

### Description

The capability did not pass the Gate (G < 0.75), or it was superseded by a better capability, or it has become obsolete. It is archived — collapsed to |null⟩ and recorded in the audit DAG. Archiving is not deletion — the capability's draft, replay results, and verification data are preserved for future reference. A capability that was archived may be revisited in a future cycle if new patterns emerge.

### When to Use

- After Gate has failed (G < 0.75)
- When a previously promoted capability is superseded
- When a capability has not been used in 3+ collapse cycles (staleness)
- At the cycle boundary (Day 7, ship-or-kill)

### When to Skip

- If Gate has passed (the capability goes to Promote instead)
- If the capability is still in active use

### Tools & Strategies

| Tool/Strategy | Role |
|:--------------|:-----|
| Audit DAG | Record archive decision with full context and reason |
| SiYuan (via Bundinha) | Store archived capability in knowledge graph for future reference |
| Rollback Ledger | If archiving a previously promoted capability, create rollback point |

---

## Cycle Binding

The ascension path is bound to the collapse cycle (A3). The focus gradient ∇(τ,t) = 1/(τ−t+ε) applies to the path itself:

| Cycle Day | Phase | Ascension Activity |
|:----------|:------|:-------------------|
| Day 0 | Initialization | Observe (cycle start) |
| Days 1–3 | Exploration | Observe, Pattern, Draft |
| Days 4–5 | Compression | Replay, Verify (no new Drafts) |
| Day 6 | Hardening | Gate (no new Drafts, no new Replays) |
| Day 7 | Collapse | Promote \| Archive (ship or kill) |

**Quantum Zeno Prevention**: If the agent spends too long observing without progressing to Pattern, Draft, or beyond, the superposition freezes — the capability never evolves. The cycle binding prevents this by imposing a deadline on each step. If the deadline arrives before Gate, the capability is archived by default.

---

## Parallel Ascension

Multiple capabilities may traverse the ascension path simultaneously, each in its own branch of the superposition. The strategy router manages parallel ascensions by allocating constraint budget across branches. However, the Gate step is **serialized** — only one capability may be gated per cycle boundary, preventing uncontrolled evolution.

| Constraint | Limit |
|:-----------|:------|
| Parallel Drafts | Max 3 per cycle |
| Parallel Replays | Max 3 per cycle |
| Parallel Verifications | Max 2 per cycle |
| Gates per cycle boundary | 1 (serialized) |
| Promotions per cycle | 1 (the gated capability) |

---

*Execution Protocol · NEXUS_V3.0_KERNEL · 2026-06-20*
*Eight steps. One gate. No shortcuts.*
