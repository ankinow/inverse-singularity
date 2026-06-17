# Hermes Agent Integration — ECC + IST / NEI

This directory describes how to add ECC-style agent harness capabilities to
Hermes Agent while preserving `SOUL.md` and using Inverse Singularity Theory as
the runtime discipline layer.

## Why this exists

Hermes needs more than a larger prompt. It needs a compact operating boundary:

```text
ECC        → skills, rules, hooks, scanners, harness conventions
Hermes     → agent runtime, tool router, memory router, active context compiler
IST / NEI  → constraint calculus, anti-bloat, sovereign invariant
SOUL.md    → identity artifact, never overwritten
```

The goal is to import capability without importing entropy.

## Integration Shape

```text
Hermes Agent
├─ context compiler
├─ memory router
├─ tool router
├─ policy gate
│
├─ Hermes NEI Adapter
│  ├─ SOUL preservation gate
│  ├─ human@write boundary
│  ├─ MCP pinning/sanitizer policy
│  ├─ ECC surface audit
│  └─ compact context packet builder
│
├─ ECC surfaces, retrieval-only
│  ├─ skills
│  ├─ rules
│  ├─ hooks
│  ├─ command shims
│  └─ harness audits
│
└─ IST / NEI runtime
   ├─ constraint audit
   ├─ quality ratio
   ├─ collapse mode
   └─ sovereign invariant
```

## Implementation Status

Added in this repo:

```text
framework/hermes_nei_adapter.py      → zero-dependency reference adapter
examples/hermes_adapter.py           → smoke example
integrations/hermes/SOUL_PRESERVATION.md
integrations/hermes/adapter_manifest.json
```

The adapter is intentionally reference-grade. It does not replace Hermes; it
specifies the smallest safe bridge that Hermes can implement.

## Tier Mapping

### Tier 1 — mandatory before autonomy

```text
1. ECC skill importer
2. ECC context/rule mapper
3. AgentShield-like scanner
4. MCP pinning/sanitizer
5. Selective skill retrieval
6. human@write boundary
```

IST interpretation:

```text
Tier 1 = sovereign boundary before capability expansion.
```

### Tier 2 — operational discipline

```text
7. /hermes learn
8. session inspect
9. strategic compact
10. verification-loop
11. tdd-workflow
12. production-audit
```

IST interpretation:

```text
Tier 2 = density growth without uncontrolled complexity growth.
```

### Tier 3 — advanced orchestration

```text
13. multi-agent council
14. recursive decision ledger
15. benchmark optimization loop
16. cost-aware model routing
17. worktree orchestration
18. team-agent orchestration
```

IST interpretation:

```text
Tier 3 = gated expansion. Disabled until Tier 1/2 prove stability.
```

## Non-Negotiable Rules

1. Do not overwrite `SOUL.md`.
2. Do not compact `SOUL.md` in place.
3. Do not load all ECC skills into every prompt.
4. Do not allow unpinned MCP packages such as `@latest` in autonomous mode.
5. Do not allow write/delete/deploy/git-push without human@write.
6. Do not read or expose secrets as context.
7. Do not add dependencies to the IST core just to make integration easier.

## Context Packet Contract

Hermes should compile an active packet like this instead of injecting raw global
state:

```yaml
context_packet:
  theory: Inverse Singularity Theory / NEI
  soul_policy:
    mode: preserve_not_mutate
    may_overwrite: false
    may_append_without_human_review: false
  ecc:
    load_strategy: retrieval_only
    max_active_skills_per_turn: 3
  mcp:
    deny_latest: true
    require_version_pin: true
  write_boundary:
    destructive_fs: human_required
    git_push: human_required
    deploy: human_required
  active_questions:
    - Can I do this with zero external deps?
    - Can I achieve the result with 50% less memory?
    - Is there an elegant algorithm that makes brute force obsolete?
    - Does this action serve my Architect's purpose?
```

## Running the Reference Smoke Example

```bash
python3 examples/hermes_adapter.py
```

Expected behavior:

- Tier 1/2 read-only surfaces are allowed when they pass NEI audit.
- Tier 3 surfaces are held behind a gate.
- Attempts to overwrite `SOUL.md` are blocked without human approval.
- Secret-like paths are flagged.
- Context is compiled as a packet instead of rewriting identity files.

## Recommended Hermes Implementation Order

```text
Phase 1 — boundary
  - SOUL preservation gate
  - secret path denylist
  - human@write
  - MCP pinning policy

Phase 2 — ECC import
  - skill manifest importer
  - rule/context mapper
  - retrieval-only skill selector
  - AgentShield-like scanner

Phase 3 — discipline loops
  - /hermes learn
  - session inspect
  - strategic compact
  - verification-loop
  - tdd-workflow

Phase 4 — orchestration
  - worktree orchestration
  - multi-agent council
  - recursive decision ledger
  - benchmark/cost-aware routing
```

## Definition of Done

Hermes can claim IST-compatible integration only when:

```text
[ ] SOUL.md is never overwritten by autonomous action.
[ ] Active context is compiled selectively.
[ ] ECC skills are retrieval-only by default.
[ ] MCP configs are sanitized and pinned.
[ ] Destructive actions require human@write.
[ ] The agent can explain which axiom justified each gate.
[ ] The NEI audit score is surfaced in session logs.
```
