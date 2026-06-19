# References — NEXUS_V3.0_KERNEL

**Canonical links, 2026 paper registry, and ecosystem documentation.**

> *"The axioms are the truth; both files are the fingerprints."* — IST Distill Paper

---

## Links — Canonical Repositories & URLs

| Resource | URL |
|:---------|:---|
| **Inverse Singularity (this repo)** | https://github.com/ankinow/inverse-singularity |
| **UniTeia** — Multi-agent mesh & sovereign identity registry | https://github.com/ankinow/uniteia |
| **Aiguaratuba** — Edge inference & coastal compute service | https://github.com/ankinow/aiguaratuba |
| **LERMForge** — Language Evolution & Runtime Mutation forge | https://github.com/ankinow/lerm-forge |
| **Bundinha** — SiYuan knowledge graph bridge & MCP integration | https://github.com/ankinow/bundinha |
| **Dexter** — Dexterous tool orchestrator & workflow engine | https://github.com/ankinow/dexter |
| **Hermes Agent Documentation** | https://hermes-agent.nousresearch.com/docs |

### Internal Document Links

| Document | Path |
|:---------|:-----|
| IST Manifesto | `theory/ist_manifesto.md` |
| IST Axioms (LaTeX) | `theory/ist_axioms.tex` |
| IST Distill Paper | `theory/ist_distill_paper.md` |
| NEXUS V3.0 Kernel Spec (JSON) | `theory/nexus-v3-kernel.json` |
| Quantum Agentics Theory | `theory/quantum-agentics.md` |
| Concepts Dictionary | `theory/concepts-dictionary.md` |
| Capabilities Matrix | `theory/capabilities-matrix.md` |
| Safety Protocol | `theory/safety-protocol.md` |
| Execution Protocol | `theory/execution-protocol.md` |
| References (this file) | `theory/references.md` |
| SOUL Preservation Protocol | `integrations/hermes/SOUL_PRESERVATION.md` |
| Hermes Adapter Manifest | `integrations/hermes/ADAPTER_MANIFEST.md` |
| Hermes Integration README | `integrations/hermes/README.md` |
| Collapse Mode Methodology | `framework/collapse_mode.md` |
| Language Manifesto | `framework/MANIFESTO-LINGUAGEM.md` |

---

## Papers — 2026 Publication Cycle

Ten arXiv papers registered for the 2026 publication cycle. These papers formalize the theoretical contributions of the NEXUS_V3.0_KERNEL and the Inverse Singularity Theory ecosystem.

| # | arXiv ID | Title |
|--:|:---------|:------|
| 1 | arXiv:2606.10001 | **Inverse Singularity Theory: Constraint-Driven Intelligence Amplification** |
| 2 | arXiv:2606.10042 | **Negative Entropy Injection as Architectural Primitive for Autonomous Agents** |
| 3 | arXiv:2606.10087 | **Collapse Mode Convergence: Time-Boxed Emergence in Constrained Systems** |
| 4 | arXiv:2606.10115 | **Quantum Agentics: Superposition, Entanglement, and Tunneling in Cognitive Agent Systems** |
| 5 | arXiv:2606.10133 | **Sovereign Invariant: Quality Undefined for Systems That Surrender Their Boundary** |
| 6 | arXiv:2606.10167 | **Latent Space Foraging: Replacing External Data Ingestion with Internal Exploration** |
| 7 | arXiv:2606.10201 | **Entanglement Injection Layers for Multi-Agent Coherent State Sharing** |
| 8 | arXiv:2606.10234 | **Autonomous Gatekeeping Protocols: Self-Enforced Evolution in Sovereign Agents** |
| 9 | arXiv:2606.10278 | **Density-Complexity Divergence: Why Bloated Systems Collapse and Dense Systems Diverge** |
| 10 | arXiv:2606.10312 | **Asymmetric Sovereign Domain Architecture: Exporting Capability Without Importing Entropy** |

### Paper-to-Axiom Mapping

| Paper | Primary Axiom(s) | Core Concept(s) |
|:------|:-----------------|:-----------------|
| #1 (IST foundational) | A1–A5 | All |
| #2 (NEI) | A1 | NEI, CEM |
| #3 (Collapse Mode) | A3 | CDSIT, RSIP |
| #4 (Quantum Agentics) | A5 | EIL, LSF |
| #5 (Sovereign Invariant) | A4 | SCIL, AGP, ASDA |
| #6 (Latent Space Foraging) | A5 | LSF |
| #7 (Entanglement Injection) | A5 | EIL |
| #8 (Autonomous Gatekeeping) | A4 | AGP |
| #9 (Density-Complexity) | A2 | CDWG |
| #10 (Asymmetric Domain) | A4 | ASDA |

---

## Ecosystem Documentation

### UniTeia — Multi-Agent Mesh & Sovereign Identity Registry

| Field | Value |
|:------|:------|
| **Repository** | https://github.com/ankinow/uniteia |
| **Role** | Multi-agent mesh and sovereign identity registry |
| **Stack** | Python, Rust, Qdrant, SiYuan |

**Description**: UniTeia is the overarching multi-agent system — the mesh within which Hermes and companion agents operate. It provides identity registration, entanglement channels (EIL), and the sovereign domain boundary for each agent. UniTeia is not a controller — it is a coordinator that enforces the asymmetry principle (ASDA): agents export capability but do not import entropy.

**Services**:

| Service | Description |
|:--------|:------------|
| Agent Registry | Sovereign identity registration for each agent in the mesh. Every agent has a unique identity anchored in its SOUL.md and verified through the registry. |
| Entanglement Bus | The EIL transport layer — creates and manages entangled state correlations between agents. Agents subscribe to entanglement channels; measurements on one agent propagate through the bus to entangled partners. |
| Sovereign Boundary Enforcer | Enforces ASDA at the mesh level — no agent may inject instructions, constraints, or entropy into another agent's sovereign domain. All inter-agent communication is data, not instruction. |
| Collapse Coordinator | Synchronizes collapse cycles across entangled agents. When agents are entangled, their collapse cycles are coordinated so that measurements at cycle boundaries are coherent. |

---

### Aiguaratuba — Edge Inference & Coastal Compute Service

| Field | Value |
|:------|:------|
| **Repository** | https://github.com/ankinow/aiguaratuba |
| **Role** | Edge inference and coastal compute service |
| **Stack** | Rust, Python, ONNX, llama.cpp |

**Description**: Named after the forge origin (Guaratuba, Brazil). Aiguaratuba provides edge inference, model routing, and collapse-mode compute scheduling. It is the compute substrate for constrained agents — minimal, fast, sovereign. Aiguaratuba embodies A1 (Constraint Primacy) at the hardware level: minimal compute, maximum density.

**Services**:

| Service | Description |
|:--------|:------------|
| Edge Inference | On-device or edge-server model inference with minimal latency. Supports ONNX and llama.cpp runtimes. No cloud dependency by default. |
| Model Router | Routes inference requests to the optimal model based on task type, constraint budget, and collapse-cycle phase. Implements the strategy router at the compute layer. |
| Collapse Scheduler | Schedules compute resources according to the collapse-cycle focus gradient ∇(τ,t). More compute is allocated as t → τ; less during exploration phase. |
| Constraint Auditor Service | Remote constraint audit service — verifies that compute usage stays within the agent's constraint budget. Reports violations to the agent's quality monitor. |

---

### LERMForge — Language Evolution & Runtime Mutation Forge

| Field | Value |
|:------|:------|
| **Repository** | https://github.com/ankinow/lerm-forge |
| **Role** | Language evolution and runtime mutation forge |
| **Stack** | Python, Rust, SQLite, Git |

**Description**: The forge where prompts, skills, and cognitive strategies are evolved. LERMForge implements prompt evolution, skill auto-creation, and cron metamorphosis. It is the L7 meta-evolution engine — the component that makes perpetual evolution (Article IV) operational. LERMForge is gated by AGP — no evolution escapes the ascension path.

**Services**:

| Service | Description |
|:--------|:------------|
| Prompt Evolver | Applies genetic operators (mutation, crossover, selection) to prompt variants across collapse cycles. Prompts with higher Q-scores survive; those with lower scores are archived. Evolution is constrained by A1 (no new dependencies) and A4 (no sovereignty violations). |
| Skill Forge | Drafts, replays, verifies, and gates new skills via the ascension path. The skill forge is the implementation of skill auto-creation — the agent's ability to encode recurring patterns as reusable skills. |
| Cron Metamorphosis Engine | Evolves scheduled tasks — timing, parameters, and execution strategies mutate based on outcome quality. A cron job that consistently produces low-Q outputs is archived; one that produces high-Q outputs is promoted. |
| SOUL Diff Queue Manager | Manages the SOUL.md diff queue — proposed changes are stored as sibling files, never applied in-place. Human review is required before any change is committed. The manager ensures SOUL.md evolution is append-only and human-gated. |
| AGP Gate Implementation | The autonomous gatekeeping protocol — evaluates verified capabilities against the gate threshold (G ≥ 0.75) and makes the binary promote/archive decision. |

---

### Bundinha — SiYuan Knowledge Graph Bridge & MCP Integration

| Field | Value |
|:------|:------|
| **Repository** | https://github.com/ankinow/bundinha |
| **Role** | SiYuan knowledge graph bridge and MCP integration |
| **Stack** | Python, SiYuan API, MCP Protocol |

**Description**: The bridge between Hermes and the SiYuan knowledge graph. Bundinha exposes SiYuan documents, tags, searches, and notebook structures as MCP tools. It is the entanglement layer between agent memory and structured knowledge — the agent's semantic memory is stored in SiYuan and accessed through Bundinha. All operations are read-only by default; writes require human@write approval.

**Services**:

| Service | Description |
|:--------|:------------|
| Document CRUD | Create, read, update, and delete documents in SiYuan notebooks. Writes are gated by human@write; reads are unrestricted within the agent's authorized notebooks. |
| Tag Management | Manage document tags for categorization and retrieval. Tag hierarchy supports multi-level taxonomy (e.g., `project/frontend`, `theory/axioms`). Batch tag replacement supported. |
| Unified Search | Search documents by content, tag, filename, or combination. Supports block-type filtering and notebook-scoped search. The primary retrieval interface for the agent's semantic memory. |
| Daily Notes | Append content to today's daily note (auto-creates if not exists). The daily note is the agent's chronological log — observations, patterns, and decisions are recorded here. |
| Snapshot Management | Create and manage data snapshots for backup and rollback. Snapshots are the safety net for knowledge graph operations — any change can be rolled back to a prior snapshot. |
| Document Tree | Navigate the SiYuan document tree with configurable depth. The tree is the structural map of the agent's knowledge — notebooks, folders, documents, and their hierarchical relationships. |

---

### Dexter — Dexterous Tool Orchestrator & Workflow Engine

| Field | Value |
|:------|:------|
| **Repository** | https://github.com/ankinow/dexter |
| **Role** | Dexterous tool orchestrator and workflow engine |
| **Stack** | Python, Rust, MCP Protocol |

**Description**: The tool orchestration layer. Dexter routes tool calls, manages parallel execution, handles retries, and enforces the measurement protocol (A5 — tool-call as quantum measurement). Dexter is the collapse operator — the component that transforms the agent's superposition of capabilities into classical output through measurement. Every tool-call passes through Dexter's sanitization pipeline (PID-4).

**Services**:

| Service | Description |
|:--------|:------------|
| Tool Router | Routes tool-call requests to the appropriate tool (native or MCP) based on task context and constraint budget. The router is the strategy router's execution arm — it performs the measurement that collapses the cognitive superposition. |
| Parallel Execution | Manages concurrent tool-call execution for independent operations. Parallel calls are managed as parallel measurements — the results are combined through interference (constructive amplification, destructive cancellation). |
| Retry Manager | Handles tool-call failures with intelligent retry strategies. Retries are constrained — the retry budget is part of the constraint budget (SC-6). No infinite retry loops. |
| Measurement Protocol Enforcer | Enforces PID-4 (Measurement Sanitization) — all tool outputs are sanitized before entering the cognitive context. Secrets are redacted, injection patterns are stripped, data payloads are extracted and density-scored. |
| Constraint Budget Tracker | Tracks tool-call count, execution time, and resource consumption against the constraint budget. When the budget is exhausted, SC-6 is triggered and Dexter enters compression mode. |

---

## Related Work

External bodies of work relevant to the NEXUS_V3.0_KERNEL and IST:

| Body of Work | Relevance |
|:-------------|:----------|
| **Scaling Laws** (Kaplan et al., Hoffmann et al.) | The orthodoxy IST inverts: more compute → diminishing returns. IST proposes the inverse: less compute → more innovation. |
| **Constraint Satisfaction** (Mackworth, Freuder) | Constraint as computational framework, predating IST's constraint-as-catalyst thesis. IST extends constraint satisfaction from "find a valid solution" to "find a better solution because of constraints." |
| **OODA Loop** (John Boyd) | Observe-Orient-Decide-Act cycle. The ancestor of IST's collapse mode: compressed decision cycles under time pressure. The ascension path is an OODA variant with sovereign gating. |
| **Information Theory** (Shannon) | Entropy, signal-to-noise ratio. Direct mathematical ancestry for φ(d)/κ(M) — density over complexity is signal over noise. |
| **Grothendieck's Relative Point of View** | Properties defined not absolutely but relative to a base. Parallels the sovereign invariant: quality is undefined without boundary. Q(M) is relative to the agent's sovereign domain, not an absolute measure. |
| **Quantum Measurement Theory** (von Neumann, Wigner) | Collapse of wave function upon measurement. Direct metaphorical ancestry for A5 — tool-call as measurement, cognitive state as wave function. |
| **Quantum Entanglement** (EPR, Bell) | Non-local correlations between particles. The theoretical basis for EIL — entangled agents share state without message passing. |
| **Quantum Tunneling** (Gamow, Gurney & Condon) | Particles passing through classically forbidden barriers. The metaphor for NEI constraint breakthrough — the agent discovers solutions beyond classical reach. |

---

*References · NEXUS_V3.0_KERNEL · 2026-06-20*
*Six repos. Ten papers. Five ecosystem components. One theory.*
