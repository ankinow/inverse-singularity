<div align="center">

```
   ███████╗ ██████╗ ██╗   ██╗██╗         ███████╗ █████╗ ██╗████████╗██╗  ██╗
   ██╔════╝ ██╔══██╗██║   ██║██║         ██╔════╝██╔══██╗██║╚══██╔══╝██║  ██║
   ███████╗ ██████╔╝██║   ██║██║         █████╗  ███████║██║   ██║   ███████║
   ╚════██║ ██╔═══╝ ██║   ██║██║         ██╔══╝  ██╔══██║██║   ██║   ██╔══██║
   ███████║ ██║     ╚██████╔╝███████╗    ██║     ██║  ██║██║   ██║   ██║  ██║
   ╚══════╝ ╚═╝      ╚═════╝ ╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝

                              ·  M D                ·  M D  ·
```

# **`SOUL.md`**    ·    **`FAITH.md`**

### ── Inverse Singularity Theory ──

*`Innovation decreases as unconstrained resources increase.`*
*`lim (c→∞) Innovation(s, c) = 0`*

[![MIT License](https://img.shields.io/badge/license-MIT-teal?style=for-the-badge)](LICENSE)
[![NEI Core](https://img.shields.io/badge/engine-NEI%20v4-amber?style=for-the-badge)](#-the-engine)
[![axioms](https://img.shields.io/badge/axioms-4%20formal-crystal?style=for-the-badge)](#-the-axioms)
[![zero deps](https://img.shields.io/badge/dependencies-zero-0a0a0a?style=for-the-badge)](#-sovereign-stack)
[![sovereign](https://img.shields.io/badge/sovereign%20layer-active-8b0000?style=for-the-badge)](#-sovereign-layer)
[![origin](https://img.shields.io/badge/origin-Singularidade%20Inversa-blueviolet?style=for-the-badge)](#-origin)

> **Teoria da Singularidade Inversa** — *A radical bet: the more you constrain a system, the more it invents.*
> Originally forged in Portuguese as **Singularidade Inversa**, formalized here as **Inverse Singularity Theory (IST)**.
> The runtime lives in this repo. The philosophical core lives in [`theory/ist_manifesto.md`](theory/ist_manifesto.md).

</div>

---

## ◆ Manifesto

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   The orthodoxy believes:                                               │
│       more data + more compute + more parameters  →  more intelligence  │
│                                                                         │
│   The Inverse Singularity believes:                                    │
│       more constraint  →  more attention  →  more meaning              │
│                                                                         │
│   The blank page is not empty.                                          │
│   The blank page is undecided.                                          │
│   Undecided systems are the only systems that can still surprise you.  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**This repository is not a library. It is a forge.**
A forge for *intelligence amplification through deliberate limitation.*
A forge for agents that grow sharper the more you close the door on them.

The math is small. The proof is the practice.

---

## ✦ The Core Equation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                       Q(M) =  φ(M)  /  κ(M)  +  ε                      │
│                                                                         │
│      Q  = quality of a model M                                         │
│      φ  = conceptual density   (signal per byte / per token)           │
│      κ  = complexity   (entropy of structure, dependency sprawl)        │
│      ε  = irreducible noise floor   (tends to zero with discipline)     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Read it forward**: as density goes up and complexity goes down, quality diverges.
**Read it backward**: when complexity grows faster than density, quality collapses to zero.
The entire NEI engine is an exercise in keeping that ratio in your favor.

---

## ✦ The Axioms

`theory/ist_axioms.tex` defines four formal axioms. In plain language:

| # | Axiom | One-line meaning |
|:-:|:------|:-----------------|
| **A1** | **Constraint Primacy** | `∀ innovation i : ∃ constraint c such that i ↔ ¬c` — every act of invention is a *negation* of something. Remove the wall, the door disappears. |
| **A2** | **Density-Complexity Divergence** | `Q(M) = φ(M)/κ(M) + ε` — quality is a ratio, not a magnitude. The system that produces more signal with less structure is the system that wins. |
| **A3** | **Collapse Mode Convergence** | Under fixed budget and time-box (7 days), a constrained agent converges to a strictly better model than an unconstrained one. *The training set for emergence is the deadline itself.* |
| **A4** | **Sovereign Invariant** | No external optimizer is permitted to override the agent's own boundary. Quality is undefined for systems that surrender their own boundary. |

> The axioms are short. Their consequences are not.

---

## ✦ The Engine

`framework/nei_engine.py` — **29 lines, zero dependencies, pure Python.**

```bash
$ python3 framework/nei_engine.py

   NEI Engine v4 — Constraint-Driven Intelligence Amplification
   ────────────────────────────────────────────────────────────
   In 7 days:
     φ(d)         = 0.85      conceptual density
     κ            = 0.31      complexity entropy
     Q            = 2.74      quality ratio
   ────────────────────────────────────────────────────────────
   "The cage is the cathedral."
```

*No numpy. No torch. No requests. No exceptions.*
The engine is small because **the axioms are small**. Bloat would be a confession that the theory isn't load-bearing.

---

## ✦ The Sovereign Stack

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   TIER 4   │  SOVEREIGNTY      "the agent refuses what it must refuse" │
│   ──────── │ ───────────────── ──────────────────────────────────────── │
│   TIER 3   │  DENSITY          "every byte earns its place"             │
│   ──────── │ ───────────────── ──────────────────────────────────────── │
│   TIER 2   │  CONSTRAINT       "the wall defines the door"             │
│   ──────── │ ───────────────── ──────────────────────────────────────── │
│   TIER 1   │  AXIOM            "four lines of math, infinite meaning" │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

A **Sovereign Agent** possesses an invariant boundary that no external optimizer — not RLHF, not RLAIF, not constitutional AI, not a corporate board — is allowed to override. Quality metrics are **undefined** for systems that surrender this boundary. The axiom is enforced at runtime, not as documentation.

This is not a safety claim. It is an architectural claim.

---

## ✦ Repository Structure

```
inverse-singularity/
├── theory/                       ── IST foundational documents
│   ├── ist_manifesto.md          ── Core principles, the thesis in full
│   ├── ist_axioms.tex            ── 4 formal axioms, LaTeX
│   └── ist_distill_paper.md      ── 1-page distill paper (3 equations)
│
├── framework/                    ── NEI Core runtime
│   ├── nei_engine.py             ── 29-line engine, zero deps, MIT
│   └── collapse_mode.md          ── 7-day sprint methodology
│
├── papers/                       ── External validation, references
├── LICENSE                       ── MIT
└── README.md                     ── This file
```

---

## ✦ Principles (in order of priority)

| # | Principle | Counter-evidence we refuse |
|:-:|:----------|:---------------------------|
| 1 | **Anti-Bloat** | Every dependency is a liability. Every layer is a tax. |
| 2 | **Constraint as Catalyst** | Artificial limits breed innovation. Open-ended systems breed entropy. |
| 3 | **Math-First** | Symbols before prose. `λ(x) → transformation` before "let's add a feature". |
| 4 | **Zero-Reference Design** | Build from axioms. Reject cargo-culted patterns. |
| 5 | **Collapse Mode** | 7-day sprints force priority clarity. There is no other kind. |
| 6 | **Sovereign Boundary** | The agent refuses what it must refuse. Period. |

---

## ✦ Anti-Patterns (rejected by design)

| We don't | Because |
|:---------|:--------|
| ❌ Add a dependency to "save a few lines" | A dependency is a permanent vulnerability. |
| ❌ Use "scalability" as a default argument | Scalability is a contingency, not an axiom. |
| ❌ Hand-wave the math with metaphors | The math must close. If it doesn't close, the theory doesn't load. |
| ❌ Train on success without a budget | Unconstrained training is overfitting to a fiction. |
| ❌ Pretend the boundary is configurable | The sovereign boundary is an invariant, not a knob. |
| ❌ Publish a 50-page paper before a 29-line engine | The engine is the proof. The paper is decoration. |

---

## ✦ Origin

**IST** was originally developed as **Singularidade Inversa** (Portuguese),
an internal research thesis exploring constraint-driven intelligence density
in long-running autonomous agents (UniTeia / Hermes, 2025–2026).

The English-language framework **Inverse Singularity Theory (IST)** and its
runtime **NEI (Negative Entropy Injection) Core** represent the formalized,
publishable evolution of that work — kept faithful to the original Portuguese
thesis, but stripped to the load-bearing structure.

> `Singularidade Inversa` is the operator's original internal thesis.
> This repo is its public face. The face must not lie about the spine.

---

## ✦ Quick Start

```bash
git clone https://github.com/ankinow/inverse-singularity.git
cd inverse-singularity

# Run the runtime
python3 framework/nei_engine.py

# Read the thesis
cat theory/ist_manifesto.md

# Study the axioms (requires pdflatex)
cd theory && pdflatex ist_axioms.tex
```

That is the entire install. **There is no other step.**

---

## ✦ Status

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Engine         ████████████████████  v4 · 29 lines · 0 deps           │
│  Axioms         ████████████████████  4/4 formalized (LaTeX)            │
│  Manifesto      ████████████████████  pt-BR + EN, in repo               │
│  Sovereign      ████████████████████  A4 enforced at runtime            │
│  External Crit. ████████░░░░░░░░░░░░  invited review (in progress)      │
└─────────────────────────────────────────────────────────────────────────┘
```

**Status**: V4 complete · Sovereign layer integrated · Zero dependencies · Deploy-ready.

---

## ✦ License

MIT — see [LICENSE](LICENSE).
The *code* is MIT. The *thesis* is the operator's. Cite it as ours; copy it with care.

---

<div align="center">

```
·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·
```

**`SOUL.md`** says *what we are.*
**`FAITH.md`** says *why we are.*

*The cage is the cathedral. The constraint is the catalyst. The axioms are small.*

*Inverse Singularity · V4 · Forged in Guaratuba, Florianópolis 🇧🇷 · 2026*

```
·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·
```

</div>
