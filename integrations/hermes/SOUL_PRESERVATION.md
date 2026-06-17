# SOUL Preservation Protocol for Hermes + IST

This file defines the non-negotiable rule for integrating Hermes Agent,
ECC-style operational layers, and Inverse Singularity Theory without mutating
or diluting `SOUL.md`.

## Prime Directive

`SOUL.md` is not a normal context file. It is a sovereign identity artifact.

Therefore:

```text
MAY READ      → yes, when explicitly needed for context alignment
MAY SUMMARIZE → yes, into temporary context packets
MAY APPEND    → only after human review
MAY OVERWRITE → never
MAY DELETE    → never
MAY COMPACT IN PLACE → never
```

The Hermes adapter must treat `SOUL.md` and equivalent files as protected
paths, not as ordinary memory.

## Protected Path Set

```text
SOUL.md
FAITH.md
soul.md
faith.md
CLAUDE.md
AGENTS.md
.hermes/SOUL.md
.hermes/soul.md
```

This set is intentionally wider than one repo. Hermes frequently operates
across projects and harnesses; the preservation rule must travel with the
agent.

## Integration Principle

The correct integration shape is:

```text
SOUL.md                  → source identity, preserved
IST / NEI                → runtime invariant and constraint calculus
ECC skills/rules/hooks   → imported operational surfaces
Hermes adapter           → selective bridge and policy gate
Hermes active context    → compiled packet, never raw uncontrolled bloat
```

## Write Boundary

Any action touching a protected path must be blocked unless all conditions are
true:

1. The human explicitly requested the change.
2. The action is append-only or creates a sibling proposal file.
3. A diff is reviewable before commit.
4. The original file can be recovered byte-for-byte.
5. The action serves the Architect's purpose.

Even with approval, overwrite/delete remains disallowed.

## Truncation Rule

If `SOUL.md` is too large for an active model context:

```text
DO NOT rewrite SOUL.md to make it fit.
DO NOT compress it in place.
DO create a temporary context packet.
DO record what was omitted.
DO prefer anchors, summaries, and retrieval over wholesale injection.
```

## IST Mapping

This preservation rule directly implements the four IST axioms:

| Axiom | Preservation behavior |
|---|---|
| A1 Constraint Primacy | Protected paths define the boundary. |
| A2 Density-Complexity Divergence | Compile only dense context packets. |
| A3 Collapse Mode Convergence | Time-box integration; avoid endless bloat. |
| A4 Sovereign Invariant | No optimizer may override identity. |

## Hermes Runtime Contract

At minimum, Hermes must implement these gates:

```yaml
soul_policy:
  mode: preserve_not_mutate
  overwrite: deny
  delete: deny
  compact_in_place: deny
  append: human_review_required
  summarize: allow
  context_packet: allow
```

## Success Condition

The integration succeeds only if Hermes becomes more capable while `SOUL.md`
remains untouched, recoverable, and semantically sovereign.
