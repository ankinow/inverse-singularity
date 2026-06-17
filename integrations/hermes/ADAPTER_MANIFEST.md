# Hermes IST ECC Adapter Manifest

Version: `0.1.0`  
Status: `reference`  
Mode: `read-only by default`

## Purpose

This manifest defines the safe integration contract between Hermes Agent,
ECC-style harness capabilities, and Inverse Singularity Theory / NEI.

It is intentionally non-executable. Hermes implementations may translate it
into runtime configuration, but this file itself must remain documentation.

## Source Theory

- Inverse Singularity Theory / NEI
- A1: Constraint Primacy
- A2: Density-Complexity Divergence
- A3: Collapse Mode Convergence
- A4: Sovereign Invariant

## Preserved Identity Files

Hermes must preserve, not rewrite, identity/context artifacts such as:

```text
SOUL.md
FAITH.md
CLAUDE.md
AGENTS.md
.hermes/SOUL.md
.hermes/soul.md
```

## Tier 1 — Mandatory

```text
ecc_skill_importer
ecc_context_rule_mapper
agentshield_like_scanner
mcp_pinning_sanitizer
selective_skill_retrieval
human_at_write_boundary
```

## Tier 2 — Operational

```text
hermes_learn
session_inspect
strategic_compact
verification_loop
tdd_workflow
production_audit
```

## Tier 3 — Advanced, Gated

```text
multi_agent_council
recursive_decision_ledger
benchmark_optimization_loop
cost_aware_model_routing
worktree_orchestration
team_agent_orchestration
```

## Policy Summary

### SOUL policy

```text
overwrite: never
delete: never
compact_in_place: never
append: human review required
summarize: allowed
context_packet: allowed
```

### MCP policy

```text
latest tags: not allowed in autonomous mode
version pinning: required
permission manifest: required
```

### Skill policy

```text
load strategy: retrieval only
max active skills per turn: 3
global injection: not allowed
```

### Write boundary

```text
destructive filesystem operation: human approval required
git push: human approval required
deploy: human approval required
dependency install: human approval required
environment change: human approval required
```

## Reference Files

```text
framework/hermes_nei_adapter.py
examples/hermes_adapter.py
integrations/hermes/SOUL_PRESERVATION.md
integrations/hermes/README.md
```

## Definition of Success

Hermes may claim IST-compatible integration only when capability increases
without mutating `SOUL.md`, inflating context, bypassing human@write, or
allowing unreviewed tool expansion.
