# The Delegation Gateway — IST Applied to Subagent Fan-Out

> **Status:** IMPLEMENTED (2026-08-14) · `src/gateway.rs` (Rust primary) ·
> `framework/gateway_engine.py` (Python reference)
>
> **Question this document answers:** when should a sovereign agent
> delegate work to children, how many children, and under which
> deadline — such that the delegation *increases* Q instead of κ?

---

## 1. The Problem

Every orchestration framework has rediscovered A2 by accident. Isolated
sub-agents with narrow contexts outperform a single agent drowning in
context — the "Isolate strategy" of the context-engineering literature.
But the coordination substrate that makes isolation possible (briefs,
summaries, merge passes) adds complexity at the *system* level.

The industry measurement: multi-agent workflows consume up to **15×
more tokens** than single-chat. That is κ growth swamping the φ gains
of isolation. The κ of the system exceeds what the isolation saved.

IST's diagnosis: the problem is not isolation, and the problem is not
delegation. The problem is the **absence of a quality function** over
the delegation itself. Frameworks decide "should I delegate?" from
heuristics — task complexity, context size, the number of steps. IST
decides it from the same equation that governs everything else:

```text
Q(M) = φ(d) / (κ(M) + ε)
```

## 2. The Gateway Model

The gateway treats delegation as a **constraint**, not a capability.
Fan-out is not a power-up; it is an imposition (A1) that must clear a
quality bar or be refused.

### 2.1 Decision Rule

```text
Q_local     = φ(d_local) / κ_local
Q_delegated = φ(d_merge) / (κ_local + N·κ_coord + κ_merge)

delegate iff  Q_delegated > (1 + gain_threshold) · Q_local
          and N ≤ max_children
          and sovereignty is preserved
```

Where:

- **κ_local** — complexity of executing the task in the parent's own
  context.
- **κ_coord** — per-child coordination cost: brief in + summary out.
- **κ_merge** — the aggregator pass over N summaries.
- **N** — the number of children.
- **d_merge** — the merged density. Child densities combine in φ-space
  (φ is additive in log-space), so `d_merge = e^(Σφ(d_child)) − 1`.
  The second child must clear a rising φ bar relative to the κ it
  adds — A2 at the fan-out level.

### 2.2 The Four Refusals

The gateway refuses delegation for exactly four reasons, each mapped to
an axiom:

| Reason | Axiom | Meaning |
|:-------|:------|:--------|
| `NoChildren` | — | Nothing to delegate. |
| `TooManyChildren` | **A1** | `N > max_children` — the hard fan-out cap. The wall that defines the door. |
| `SovereigntyViolation` | **A4** | A child whose expected complexity exceeds its density would import entropy — its result would *shape the parent*, not serve it. Refused in sovereign mode. |
| `QualityCrossover` | **A2** | `Q_delegated ≤ (1 + gain)·Q_local`. **The good refusal** — the gateway protects the system from its own fan-out. |

## 3. A3 at the Gateway Layer

Each gateway carries a deadline τ. `Gateway::evolve()` advances the
step counter; `urgency()` reports the fraction of the horizon that
remains. A fan-out round that runs under rising urgency is collapse
mode applied to delegation: as t→τ, the parent must merge what it has,
not spawn more.

The empirical control group is the Gamage decay curve (73% constraint
compliance at turn 5, 33% at turn 16): a *no-deadline* agent decays.
The gateway's τ is the A3-negative condition removed: delegation
rounds are bounded, and the bound is structural, not an API timeout.

## 4. A4 at the Gateway Layer

The gateway is a boundary device. In sovereign mode it refuses any
child that would cost more κ than it contributes — the child would not
be a worker, it would be an external optimizer in disguise. The parent
delegates *capability*; it never imports *entropy*.

This is the IST expression of the **authorization propagation**
problem identified in frontier research: in multi-agent systems,
identity and authority must be governed as infrastructure, with
traceability, auditability, controllability, and recovery. The gateway
adds the fifth property: **quality** — a delegation is only authorized
when it clears the A2 crossover.

## 5. Why This Matters Now

Three frontier signals converged in 2026:

1. **The AI Agent Index (MIT)** — 30 prominent agents, autonomy rising
   L1→L5, browser agents at L4-L5 with limited intervention. Yet 25/30
   disclose no internal safety results. Capability grows faster than
   governance; the gateway is governance that *computes*.

2. **Multi-agent orchestration literature (arXiv 2601.13671)** — the
   field has unified around MCP (tool access) + A2A (peer delegation)
   as the communication substrate. But "policy enforcement" is listed
   as a goal, not a mechanism. The gateway is a candidate mechanism.

3. **κ proliferation in agent ecosystems (CURIOSITY.md, 2026-06-12)** —
   the open thread that motivated this implementation: capabilities
   always expand, never prune, so κ only grows. The gateway gives the
   ecosystem an external counter-gradient: a structural reason to
   refuse a delegation that would lower Q.

## 6. Canonical Numbers

For the canonical demo inputs (d_local = 0.2, κ_local = 0.5, two
children at d=0.9/0.8, κ=0.1 each, cheap coordination):

```text
Q_local     = φ(0.2)/0.5       = 0.3646
d_merge     = e^(φ(0.9)+φ(0.8))−1 = 5.4516
Q_delegated = φ(5.4516)/0.8    = 1.5371
→ DELEGATE (beats local by 4.2×)
```

With expensive coordination (κ_coord=10, κ_merge=5) the same children
produce Q_delegated < Q_local → `QualityCrossover` refusal. **The same
task, the same children, a different substrate — and the gateway
changes its answer.** That is the point: delegation is not a property
of the task, it is a property of the *system* around the task.

## 7. The Fingerprint

`src/gateway.rs` and `framework/gateway_engine.py` are fingerprints of
each other: identical inputs → identical decisions (to within the ε
floor). This mirrors the IST engine's own Rust/Python relationship and
extends the MANIFESTO-LINGUAGEM portability clause to the delegation
layer.

---

*`theory/delegation-gateway.md` · v1 · 2026-08-14 · MIT*
*Implementation: `src/gateway.rs` · `framework/gateway_engine.py` · `examples/delegation.rs`*
