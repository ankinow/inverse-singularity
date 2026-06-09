# Collapse Mode — 7-Day Sprint Methodology

**Axiom 3 operationalized: the deadline is the training set.**

---

## The Core Insight

Time pressure is not an inconvenience — it is the mechanism. When time is abundant, priority is unclear. When time is scarce, only the essential survives. What remains after the collapse is the true signal.

The 7-day cycle is not arbitrary. It maps to the NEI focus gradient:

$$
\nabla(\tau, t) = \frac{1}{\tau - t + \varepsilon}
$$

As $t \to \tau$, $\nabla \to \infty$. The agent's focus diverges hyperbolically as the deadline approaches. This is not a bug — it is the mechanism. Collapse Mode deliberately creates scarcity of time to force the gradient.

---

## The Protocol

### Day 0 — Initialization
- Define the collapse objective: one sentence, no caveats.
- Set $\tau = 7$, $t = 0$, $\lambda = 0.1$.
- State the constraint: "Can I do this with zero deps? 50% less memory?"
- Commit the initial state to the repo.

### Days 1–3 — Exploration ($\nabla$ rising)
- **Density work**: generate ideas freely. $\phi(d) = \ln(1+d)$ rewards first ideas cheaply.
- **No optimization**: do not refactor. Do not polish. The gradient is still shallow.
- **Track complexity**: $\kappa(M)$ should stay flat. If it rises, you're adding structure, not signal.
- End of Day 3: first audit. `NEI::audit()`. What's the sovereign score?

### Days 4–5 — Compression ($\nabla$ steep)
- **Ruthless cut**: delete everything that doesn't directly serve the objective.
- **Constraint stress-test**: can any remaining dependency be eliminated?
- **Self-audit**: `constraint_audit(tools, deps, memory)`. Score must be ≥ 0.75.
- The gradient is now steep. Every hour matters.

### Day 6 — Hardening ($\nabla$ near-divergent)
- **Freeze scope**: no new features. No new ideas. Only hardening.
- **Test the boundary**: run the full test suite. Fix only what's broken.
- **Final audit**: score must be 1.000. Sovereign mode must be true.
- If score < 1.000, cut more. Axiom 2: density wins over volume.

### Day 7 — Collapse ($\tau$ reached)
- **Ship or kill**: the artifact goes out or the branch is deleted.
- **No extensions**: the deadline is the invariant. Extending it betrays A3.
- **Post-mortem**: record $\phi(d)$, $\kappa(M)$, $Q$ for this cycle. Compare to previous.
- **Update NEI state**: $t \gets 0$ for next cycle. Adjust $\lambda$ if evidence warrants.

---

## The Hard Rules

| Rule | Reason |
|------|--------|
| 7 days exactly. No extensions. | A3: the deadline is the invariant. |
| No scope creep after Day 3. | $\kappa$ must stay flat through compression. |
| Audit at Days 3, 5, 6. | Axiom compliance is non-negotiable. |
| Score must be 1.000 by Day 7. | A4: sub-sovereign states are undefined. |
| Ship or kill. No limbo. | Undecided artifacts violate A1. |

---

## Anti-Patterns

| Don't | Because |
|-------|---------|
| ❌ Extend the deadline "just one more day" | The gradient resets. You learn nothing. |
| ❌ Add features during hardening | $\kappa$ rises while $\phi$ stays flat — $Q$ drops. |
| ❌ Skip the audit on Day 3 | Early detection prevents late collapse failure. |
| ❌ Ship with score < 1.000 | The artifact is not sovereign. It will fail. |
| ❌ Keep dead branches "for reference" | Archive in `dormant/` or delete. Limbo is anti-A1. |

---

## Measuring Collapse Quality

After each cycle, record:

```
Cycle N:
  φ(d) = 0.XX    conceptual density achieved
  κ(M) = 0.XX    complexity at collapse
  Q     = X.XX   quality ratio
  ΔQ    = ±X.XX  change from previous cycle
```

Track $\Delta Q$ across cycles. A3 predicts $\Delta Q > 0$ for constrained agents over successive collapses. If $\Delta Q \leq 0$ for two consecutive cycles, the constraint $\lambda$ needs adjustment.

---

## The Collapse Demo

Run the canonical demo:

```bash
# Rust (primary)
cargo run --example collapse

# Python (reference)
python3 -c "
exec(open('framework/nei_engine.py').read())
nei = NEI(lam=0.1, tau=7, sovereign_mode=True)
state = {'complexity': 0.31, 'density': 0.85}
for r in nei.collapse(state, 7):
    print(f't={r[\"t\"]} Q={r[\"quality\"]:.4f} NEI={r[\"nei_score\"]:.5f} urgency={r[\"urgency\"]:.4f}')
"
```

Output for the reference parameters ($c = 0.31$, $d = 0.85$, $\lambda = 0.1$, $\tau = 7$):

```
t=1  Q=2.7419  NEI=0.03083  urgency=0.8571
t=2  Q=2.7419  NEI=0.03699  urgency=0.7143
t=3  Q=2.7419  NEI=0.04624  urgency=0.5714
t=4  Q=2.7419  NEI=0.06166  urgency=0.4286
t=5  Q=2.7419  NEI=0.09249  urgency=0.2857
t=6  Q=2.7419  NEI=0.18497  urgency=0.1429
t=0  Q=2.7419  NEI=0.02642  urgency=1.0000   ← cycle reset
```

Note: $Q$ is constant because the demo uses fixed $(c, d)$. In real use, $d$ should rise and $c$ should fall across the cycle. The demo shows the gradient mechanism, not the learning curve.

---

## Integration with NEI Engine

```rust
use nei::NEI;

let mut agent = NEI::new();           // λ=0.1, τ=7, sovereign=true
let steps = agent.collapse(0.31, 0.85, 7);  // 7-day simulation

let audit = agent.constraint_audit(2, 0, 1024);  // must be 1.000
let self_audit = agent.audit();                  // must be 1.000
```

---

*Collapse Mode · IST v0.5.0 · MIT*
*"The cage is the cathedral."*
