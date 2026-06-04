# MANIFESTO da LINGUAGEM — *A Note on the Choice of Rust*

> *This document is the philosophical companion to `framework/nei_engine.py`
> and `src/lib.rs`. It exists to make one thing unambiguous:*
>
> **There is no default language. There never will be.**
>
> Rust is the *current expression* of NEI. It was chosen, not assumed.
> The choice is a virtue, not a rule. The next expression may be
> something else — and the axioms will be the only thing that does not
> move.

---

## 1. The Question

A reader of this repository will, naturally, ask:

> *Why is the engine in Rust? Did the author have a preference? Is
> this a "Rust project"? Should I file an issue to port it to my
> favorite language?*

The shortest honest answer is:

> The engine is in Rust because **Rust, at the level of types and
> runtime, instantiates the four NEI axioms more directly than any
> other widely available language at the time of writing.**
>
> This is not a vote for Rust. It is a description of a fit.

## 2. The Four Axioms, Read in Rust

| Axiom | What it asks of a language | How Rust answers |
|:------|:---------------------------|:-----------------|
| **A1 — Constraint Primacy** | Can the language express "thou shalt not" at compile time? | `#[forbid(unsafe_code)]`, `#[deny(missing_docs)]`, `no_std`, the `?` operator, the borrow checker, the absence of `null`, the `Result<T, E>` type. |
| **A2 — Density-Complexity Divergence** | Does the language reward short, dense, type-checked code? | Algebraic data types, pattern matching, `const fn`, zero-cost abstractions, no runtime reflection, no implicit conversions. |
| **A3 — Collapse Mode Convergence** | Is there a fast, dead-simple path from source to artifact? | `cargo build` produces a single static binary. No interpreter. No virtual machine. No bytecode. No package manager step at install time. One file in, one binary out. |
| **A4 — Sovereign Invariant** | Can a subsystem refuse to be optimized against its own boundary? | `#![forbid(...)]`, the `panic = "abort"` profile, the absence of `unsafe`, the `?` operator's refusal to silently swallow errors. The compiler is the auditor. |

None of these are "Rust is best." They are "Rust, here, is *the most direct expression* of these specific constraints."

## 3. The Negative Space — Why Not Other Languages

The other languages we considered, and the reason they were not chosen for the *primary* runtime:

- **Python** — Beautiful, dense, interactive. The reference engine remains in Python for didactic reasons. But: GIL, runtime type errors, no compile-time enforcement of the four axioms, no `no_std`, the entire standard library is a dependency the axioms do not need.
- **C** — Closer to the axioms in some ways (no_std, no GC, no runtime), but: A4 is impossible to enforce at the type level; A2 is undermined by the language's lack of algebraic types; the cost of *not* choosing Rust is, surprisingly, *more* code.
- **Go** — Excellent A3, decent A1. But A2 is poor (no algebraic types, no zero-cost abstractions, GC runtime); A4 is unenforceable.
- **Zig** — A very strong candidate. Rejected for now only because Rust's `cargo` ecosystem is more mature at the time of writing. This is a *contingent* reason, not a structural one. The next expression of NEI may be in Zig.
- **Haskell, OCaml, Idris, Lean, Coq** — Algebraic types, dependent types, theorem provers. Closer to the math than any other family. But A3 fails badly in practice: build times, toolchain complexity, and onboarding cost. The axioms ask for *both* a tight math expression *and* a tight operational expression; the proof-assistant family gives the first and weakens the second.
- **JavaScript, TypeScript, Ruby, PHP, Java, Kotlin, Swift** — Not in the running. The axiom-cost of an interpreter or VM in the loop is too high to justify any other virtue they might offer.

The list is not a verdict on the languages. It is a record of *why this choice was made, here, now*. Each reader will weigh these factors differently. The author invites disagreement.

## 4. What This Manifesto Is Not

It is not:

- A claim that Rust is "the best language" in any universal sense.
- A claim that NEI cannot be expressed in another language.
- A claim that the Python reference is "less correct" or "less important."
- A ban on ports to other languages — see below.

## 5. The Portability Clause

The engine is small by design. Porting it to another language is:

- **Explicitly invited.** If you can express the four axioms more directly in another language, the framework is better for it.
- **Required to keep the math identical.** Any port must produce the same scalar outputs (ψ, φ, ∇, Q) to within floating-point determinism. The Python reference and the Rust primary are *fingerprints* of each other: their outputs must agree.
- **Required to keep the four-axiom self-audit (`NEI::audit`) intact.** The Sovereign Invariant is the only invariant of the framework. A port that loses it is not a port; it is a fork.

## 6. The Sovereign Statement

> **There is no default language. There is only the question, in front of
> each implementation: which language, here, now, expresses the four
> axioms most directly — and is willing to *refuse to add a dependency*
> in order to keep the answer true?**

The answer today is Rust.
The answer tomorrow may be different.
The axioms do not move.

---

*`framework/MANIFESTO-LINGUAGEM.md` · v1 · 2026-06-04 · MIT*
*Companion to `src/lib.rs` (Rust primary) and `framework/nei_engine.py` (Python reference).*
