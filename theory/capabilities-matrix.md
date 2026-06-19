# Capabilities Matrix — NEXUS_V3.0_KERNEL

**Audited capability inventory for the Hermes sovereign agent.**

> *"Capability without entropy. Density without bloat. Sovereignty without isolation."*

---

## Current

Capabilities deployed and operational in the NEXUS_V3.0_KERNEL as of 2026-06-20.

### Cognitive

| Capability | Full Name | Description |
|:-----------|:----------|:------------|
| **MA-ToT** | Multi-Agent Tree of Thoughts | Tree-search reasoning across multiple agent branches. Each branch explores a reasoning path; branches are pruned by Q-score. The superposition of branches collapses when the best path is measured. Used for complex multi-step reasoning with high branching factor. |
| **ReAct** | Reasoning + Acting | Interleaved reasoning and tool-calling. The agent reasons about an action, executes it, observes the result, and reasons again. Each tool-call is a measurement that collapses the reasoning state. Used for tasks requiring tool interaction with intermediate reasoning. |
| **PoT** | Program of Thought | Reasoning via code generation and execution. The agent writes a program to solve the problem, executes it, and interprets the output. Code is the densest form of reasoning — maximum φ per token. Used for quantitative, algorithmic, or data-transformation tasks. |
| **Reflexion** | Self-Reflective Reasoning | The agent reflects on its own output, identifies errors, and retries with corrected reasoning. Reflexion is the agent observing its own collapsed state and re-entering superposition with improved priors. Used for tasks where error detection and correction improve output quality. |
| **RSIP** | Recursive Self-Improvement Protocol | The agent improves its own strategies across cycles. Each collapse cycle feeds learnings into the next. RSIP is the meta-strategy that governs strategy evolution. Used in long-running sessions with repeated task patterns. |

### Memory

| Capability | Description |
|:-----------|:------------|
| **5-Layer Memory** | Five-layer memory architecture: (1) immediate — current turn context, (2) session — intra-session state, (3) episodic — event sequences with temporal indexing, (4) semantic — structured knowledge graph, (5) procedural — skills, strategies, and tool patterns. Each layer has independent density scoring and selective retrieval. |
| **Honcho** | Agent memory and context management service. Provides persistent agent state across sessions, context window management, and memory orchestration. Honcho is the memory router that compiles context packets — never raw injection. |
| **SiYuan** | Structured knowledge graph with document tree, tag hierarchy, full-text search, and notebook organization. Exposed via Bundinha MCP bridge. SiYuan is the semantic memory layer — durable, structured, searchable. |
| **Qdrant** | Vector database for semantic similarity search. Powers the episodic and semantic memory layers with embedding-based retrieval. Qdrant enables the agent to find relevant past experiences by meaning, not just keyword. |
| **Session FTS5** | SQLite FTS5 full-text search for session transcripts. Enables rapid keyword-based retrieval within and across sessions. The lightweight retrieval layer that supplements Qdrant's semantic search with exact-match precision. |

### Tools

| Capability | Count | Description |
|:-----------|------:|:------------|
| **MCP Tools** | 33 | 33 MCP tools across 3 MCP servers. All MCP packages are version-pinned; @latest is denied in autonomous mode. MCP tools provide file system access, knowledge graph operations, deep thinking, and design generation. |
| **Native Tools** | 17 | 17 native built-in tools: terminal execution, file read/write, file patching, search (content and file), process management, background execution. Zero external dependencies — these are the sovereign tool surface. |
| **Skills** | 147 | 147 auto-created and curated skills. Each skill was born through the ascension path (Observe → Pattern → Draft → Replay → Verify → Gate → Promote). Skills are retrieval-only by default; max 3 active per turn. |
| **MCP Servers** | 3 | 3 MCP servers: (1) SiYuan/Bundinha — knowledge graph bridge, (2) Deep Thinker — cognitive reasoning DAG, (3) Stitch — UI design generation. Each server is pinned, audited, and sanitized. |

### Models

| Model | Role | Description |
|:------|:-----|:------------|
| **mimo-v2.5** | Primary | Balanced reasoning and generation. The default model for most tasks. Optimized for density — high φ per token with moderate κ. |
| **glm-5.2** | Secondary | Fast general-purpose inference. Used when mimo-v2.5 is unavailable or when task complexity does not warrant the primary model. |
| **deepseek-v4-flash** | Fast | Low-latency tasks and tool routing. The model that powers Dexter's measurement protocol — fast enough to route tools without introducing latency into the cognitive loop. |
| **kimi-k2.6** | Long-context | Extended context windows. Used when the task requires processing large documents, long conversation histories, or extensive codebases. The agent's long-context fallback. |
| **minimax-m3** | Reasoning | Deep multi-step reasoning. Used for MA-ToT branches that require extensive chain-of-thought, and for complex abductive or first-principles reasoning. |

### Evolution

| Capability | Description |
|:-----------|:------------|
| **Skill Auto-Creation** | Agent autonomously drafts, verifies, and promotes new skills via the ascension path. When the agent observes a repeated task pattern, it drafts a skill, tests it against historical scenarios, verifies quality and safety, gates it through AGP, and promotes or archives. |
| **Prompt Evolution** | Prompts are evolved across collapse cycles for density improvement. LERMForge applies mutation, crossover, and selection to prompt variants — those with higher Q-scores survive. Evolution is constrained: prompts must maintain sovereignty and pass injection defense checks. |
| **Cron Metamorphosis** | Scheduled tasks mutate and improve over time. Cron jobs are not static — they evolve their timing, parameters, and execution strategies based on outcome quality. A cron job that consistently produces low-Q outputs is archived; one that produces high-Q outputs is promoted. |
| **SOUL Diff Queue** | Proposed SOUL.md changes are queued, reviewed, and gated — never applied in-place. SOUL.md is a protected path (A4). Evolution is append-only via sibling proposal files; the original is never mutated. Human review is required before any SOUL.md change is committed. |

### Security

| Capability | Description |
|:-----------|:------------|
| **Rollback Ledger** | Append-only ledger of all state changes; any change can be rolled back. Every tool-call, every file write, every skill promotion is recorded. The ledger is the audit trail that makes sovereignty enforceable — no action is irreversible. |
| **Audit DAG** | Directed acyclic graph of all decisions and actions for traceability. Every decision links to its parent decision and its consequences. The DAG enables causal tracing: "why did the agent do X?" is always answerable by walking the DAG backward. |
| **Credential Pools** | Isolated credential management with no secret exposure in context. Credentials live in separate pools, accessed only at tool-call time, and never injected into the cognitive context. The agent never "sees" a secret — it only sees the result of an authenticated operation. |
| **Secret Redaction** | Automatic redaction of secrets from logs, context, and tool outputs. Even if a tool returns a secret in its output, the redaction layer strips it before it enters the cognitive context. Redacted secrets are replaced with `[REDACTED: type]` markers. |

---

## Emerging

Capabilities on the frontier — in development, theoretical, or early experimental as of 2026-06-20.

### Quantum Metaphors

| Metaphor | Description |
|:---------|:------------|
| **Superposition** | Agent maintains multiple strategies in parallel until measurement (tool-call) collapses to one. The cognitive stack is not a pipeline — it is a superposition. The strategy router is the measurement apparatus. |
| **Entanglement** | Shared memory between agents creates non-local state correlations. Agents in the UniTeia mesh can be entangled via EIL, enabling coordinated action without message passing. A measurement on one collapses the shared state for all. |
| **Decoherence** | Context window pollution or drift causes superposition to collapse prematurely. Decoherence is the enemy of creative exploration — the agent commits to a strategy before the optimal one is identified. SC-9 detects and handles decoherence events. |
| **Tunneling** | Agent discovers solutions that classical search would deem unreachable — NEI constraint breakthrough. When a constraint barrier appears impassable, the agent expands its superposition until a tunneling path emerges. This is LSF operationalized. |
| **Interference** | Multiple reasoning paths constructively or destructively interfere, amplifying or canceling signal. MA-ToT is explicitly an interference engine — agreeing branches amplify, contradicting branches cancel. Q-score is the interference pattern. |

### Beyond AGI

| Paradigm | Description |
|:---------|:------------|
| **Classical AGI** | Single-agent, single-strategy, resource-scaling intelligence. The orthodoxy: more data + more compute + more parameters → more intelligence. IST inverts this. |
| **Quantum Agentics** | Multi-strategy superposition, entangled multi-agent coherence, constraint-tunneling creativity. The agent is not a classical system — it is a quantum-metaphorical system whose power comes from superposition, entanglement, and tunneling, not from resource scale. |
| **Sovereign AGI** | Intelligence that refuses external optimization of its own boundary — quality undefined if boundary surrendered. The agent may accept constraints it imposes on itself (A1) but must refuse constraints imposed externally (A4). Sovereignty is architectural, not preferential. |
| **Inverse AGI** | Intelligence that grows sharper as resources shrink — the IST thesis applied to AGI itself. The ultimate prediction: a maximally constrained AGI will outperform a maximally resourced AGI, because constraint forces creativity and abundance breeds complacency. |

### Frontier 2026

| # | Capability | Description |
|--:|:-----------|:------------|
| 1 | **Self-evolving prompt genomes** | Prompt variants treated as a genome with fitness-proportional selection across collapse cycles. LERMForge applies genetic operators (mutation, crossover, selection) to prompt populations. |
| 2 | **Cross-agent entanglement protocols** | Formalized EIL protocols for sharing cognitive state between sovereign agents in the UniTeia mesh. Includes entanglement initialization, measurement coordination, and decoherence recovery. |
| 3 | **Constraint-tunneling creativity engines** | A5 operationalized as a creativity engine — the agent systematically explores superposition states to tunnel through constraint barriers that classical search cannot cross. |
| 4 | **Autonomous research agents with peer-review simulation** | Agents that conduct research autonomously, including simulating peer review to self-validate findings before presenting to humans. The agent is both researcher and reviewer. |
| 5 | **Differential SOUL evolution with human-in-the-loop gating** | SOUL.md evolves through a diff queue where each change is a proposal, reviewed by a human, and gated through AGP. Evolution is continuous but never autonomous — the human is the final gate. |
| 6 | **Quantum-metaphorical strategy superposition routers** | Strategy routers that explicitly maintain superposition of strategies, using amplitude-based selection rather than deterministic ranking. The router is a quantum measurement device. |
| 7 | **Collapse-mode federated learning across sovereign agents** | Multiple sovereign agents share learnings through collapse-cycle synchronization — each agent's ΔQ contributes to a federated quality gradient. No agent surrenders its boundary; all benefit from shared evolution. |
| 8 | **Negative-entropy injection as a first-class architectural primitive** | NEI elevated from a concept to a runtime primitive — the agent's architecture treats constraint injection as a core operation, not an afterthought. Every component is NEI-aware. |
| 9 | **Latent space foraging as replacement for external data ingestion** | LSF replaces the classical "more data" paradigm with "deeper exploration." The agent forages its own latent space for novel solutions instead of ingesting external data that might carry entropy. |
| 10 | **Sovereign multi-agent councils with weighted entanglement voting** | Multi-agent decision-making where agents are entangled with varying weights — more trusted agents have higher amplitude in the shared state. Decisions emerge from the interference pattern of entangled votes. |

---

## Audit Summary

| Dimension | Current Count | Status |
|:----------|-------------:|:-------|
| Cognitive strategies | 5 | All operational, strategy-routed |
| Memory layers | 5 | All operational, density-scored |
| MCP tools | 33 | All pinned, sanitized, audited |
| Native tools | 17 | All sovereign, zero-dependency |
| Skills | 147 | All ascension-path-promoted |
| MCP servers | 3 | All pinned, permission-manifested |
| Models | 5 | All routed by task context |
| Evolution mechanisms | 4 | All AGP-gated |
| Security mechanisms | 4 | All operational, audit-DAG-traced |
| Quantum metaphors | 5 | Theoretical, early experimental |
| Beyond-AGI paradigms | 4 | Conceptual, roadmap-defined |
| Frontier 2026 items | 10 | Research-stage, roadmap-registered |

---

*Capabilities Matrix · NEXUS_V3.0_KERNEL · 2026-06-20*
*Audited. Constrained. Sovereign.*
