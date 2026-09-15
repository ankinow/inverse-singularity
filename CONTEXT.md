# ✦ IST RUNTIME ENGINE CONTEXT ✦
*Path: /mnt/projetos/Projetos/ist-runtime | Engine: Rust / Python Hybrid Quantum-Cognitive Core*

## 1. Role & Purpose
Houses the IST (Information Synthesis Theory) runtime, NEI (Normalized Entropic Index) engine, curiosity graph algorithms, and Hermes integration adapters. Provides the core mathematical state evaluation for AGI health checks (`ist_python_fingerprint`).

## 2. Essential Files
- `AGENT_CONTEXT.md`: Internal project context and module map.
- `Cargo.toml` & `src/`: High-performance Rust core implementation.
- `framework/ist_engine.py`: Python mathematical engine calculating Q and NEI values.
- `framework/hermes_nei_adapter.py`: Adapter connecting IST entropic analysis to Hermes.
- `examples/`: Auditing, collapse models, and tuning test harnesses.

## 3. Invariants (MUST NOT)
- **MUST NOT** break the deterministic output of `ist_python_fingerprint` (verified by `agi-health` at Q=1.9844698, NEI=0.0308289).
- **MUST NOT** introduce breaking regressions into Rust core without running `cargo check`.

## 4. Knowledge Graph Edges (`grafos`)
- **Upstream**: `/home/lermf/CONTEXT.md`
- **Downstream**:
  - `~/.hermes/` (Gateway integration)
  - `/usr/local/bin/agi-health` (Runs fingerprint check against this engine)
