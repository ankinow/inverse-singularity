//! NEI — Negative Entropy Injection Core
//! =================================================================
//! Rust primary expression of Inverse Singularity Theory.
//!
//! **There is no default language.** Rust is chosen for this
//! runtime because it instantiates the axioms at the type and
//! runtime layer, not because the framework is "in Rust".
//!
//! See `framework/MANIFESTO-LINGUAGEM.md` for the full statement
//! of virtue. See `theory/ist_manifesto.md` for the axioms.
//!
//! ```text
//!   ψ(x, λ) = x / (1 + λ·x)        — constraint function
//!   φ(d)    = ln(1 + d)             — density enhancement
//!   ∇(τ, t) = 1 / (τ − t + ε)       — focus gradient
//!   Q(M)    = φ(d) / (κ(M) + ε)     — quality ratio
//! ```

#![forbid(unsafe_code)]
#![deny(missing_docs)]
// We do not declare `#![no_std]` — the framework is small but the
// `collapse` function returns a `Vec<Step>`, and the cost of pulling
// in `extern crate alloc` + a heap backend is higher than the cost of
// a `std` link for a runtime this small. A future no_std expression
// of NEI can return an iterator instead; that is left as a port, not
// a refactor (see framework/MANIFESTO-LINGUAGEM.md, §5).

// ────────────────────────────────────────────────────────────────
//   §1 — The three primitive transformations
// ────────────────────────────────────────────────────────────────

/// ψ (psi) — Constraint function.
///
/// `ψ(x, λ) = x / (1 + λ·x)`
///
/// As the constraint λ grows, the function saturates: input keeps
/// arriving, output is throttled. This is the *negative* entropy:
/// each unit of input buys less of the system.
#[inline]
#[must_use]
pub fn psi(x: f64, lambda: f64) -> f64 {
    x / (1.0 + lambda * x)
}

/// φ (phi) — Density enhancement.
///
/// `φ(d) = ln(1 + d)`
///
/// Logarithmic growth: the first ideas cost nothing; the next
/// thousand cost a lot. This is the *positive* entropy axis:
/// each new idea must clear an increasing bar to matter.
#[inline]
#[must_use]
pub fn phi(d: f64) -> f64 {
    (1.0 + d).ln()
}

/// ∇ (nabla) — Focus gradient.
///
/// `∇(t) = 1 / (t + ε)`
///
/// Hyperbolic urgency. As time `t` approaches the deadline, focus
/// diverges. The ε floor prevents the singularity at t=0.
#[inline]
#[must_use]
pub fn nabla(t: f64) -> f64 {
    1.0 / (t + f64::EPSILON)
}

// ────────────────────────────────────────────────────────────────
//   §2 — The NEI struct
// ────────────────────────────────────────────────────────────────

/// A NEI instance is a single ticking agent.
///
/// It owns three numbers:
/// - `lambda` (λ): the strength of the constraint (default 0.1)
/// - `tau`    (τ): the deadline in arbitrary steps (default 7)
/// - `t`      (t): the current step in `[0, tau)`
///
/// And one boolean: `sovereign_mode`, the A4 invariant.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct NEI {
    /// λ — the strength of the constraint applied to every input.
    pub lambda: f64,
    /// τ — the deadline horizon. After this many steps the focus
    /// gradient has saturated and the agent must collapse.
    pub tau: u32,
    /// t — the current step. Modulo `tau`.
    pub t: u32,
    /// Sovereign Invariant (Axiom 4). When `true`, the agent
    /// refuses to be optimized by anything that does not serve
    /// its Architect's purpose.
    pub sovereign_mode: bool,
}

impl NEI {
    /// The four proactive questions of the Sovereign Layer.
    ///
    /// Each one is a *check* the agent must pass before committing an
    /// action. Failing any one of them is grounds for refusing to act.
    pub const Q_ZERO_DEPS:    &'static str = "Can I do this with zero external deps?";
    /// A1 check — can the action be done with 50% less memory?
    pub const Q_HALF_MEM:     &'static str = "Can I achieve the result with 50% less memory?";
    /// A2 check — is there an elegant algorithm that makes brute force obsolete?
    pub const Q_ELEGANT_ALGO: &'static str = "Is there an elegant algorithm that makes brute force obsolete?";
    /// A4 check — does this action serve the Architect's purpose?
    pub const Q_ARCHITECT:    &'static str = "Does this action serve my Architect's purpose?";

    /// Construct a new agent. Defaults match the Python reference.
    pub const fn new() -> Self {
        Self {
            lambda: 0.1,
            tau: 7,
            t: 0,
            sovereign_mode: true,
        }
    }

    /// Construct a tuned agent. The two `tau = 0` case is rejected:
    /// without a deadline there is no focus gradient, and without
    /// a focus gradient there is no agent.
    pub fn tuned(lambda: f64, tau: u32) -> Option<Self> {
        if tau == 0 || !lambda.is_finite() || lambda < 0.0 {
            return None;
        }
        Some(Self {
            lambda,
            tau,
            t: 0,
            sovereign_mode: true,
        })
    }

    /// Inject complexity `c` and density `d` through the three
    /// primitive transformations, then return the scalar NEI score.
    #[inline]
    #[must_use]
    pub fn inject(&self, c: f64, d: f64) -> f64 {
        let remaining = (self.tau as f64) - (self.t as f64);
        psi(c, self.lambda) * phi(d) * nabla(remaining)
    }

    /// Evolve the agent by one step. `state` is a `(complexity, density)`
    /// pair; the returned `Step` records the resulting Q, NEI score,
    /// urgency, and the new step index.
    pub fn evolve(&mut self, complexity: f64, density: f64) -> Step {
        self.t = (self.t + 1) % self.tau;
        let quality = density / (complexity + f64::EPSILON);
        let nei_score = self.inject(complexity, density);
        let urgency = 1.0 - (self.t as f64 / self.tau as f64);
        Step { quality, nei_score, urgency, t: self.t }
    }

    /// Collapse simulation: run `steps` iterations starting from the
    /// same `(c, d)` initial state. The classic 7-day Collapse Mode.
    pub fn collapse(&mut self, complexity: f64, density: f64, steps: u32) -> Vec<Step> {
        let mut out = Vec::with_capacity(steps as usize);
        for _ in 0..steps {
            out.push(self.evolve(complexity, density));
        }
        out
    }

    /// Audit an external system against the four NEI hard limits.
    /// Returns an `Audit` record with per-axis compliance + a score.
    pub fn constraint_audit(&self, tool_count: u32, dep_count: u32, memory_bytes: u64) -> Audit {
        const MAX_TOOLS:   u32 = 3;
        const MAX_DEPS:    u32 = 0;
        const MAX_MEM_MB:  u64 = 50;
        let max_mem_bytes = MAX_MEM_MB * 1024 * 1024;

        let ok_t = tool_count <= MAX_TOOLS;
        let ok_d = dep_count  <= MAX_DEPS;
        let ok_m = memory_bytes <= max_mem_bytes;
        let ok_s = self.sovereign_mode;

        let score = [ok_t, ok_d, ok_m, ok_s].iter().map(|b| *b as u8).sum::<u8>() as f64 / 4.0;

        Audit {
            tool_compliance:   ok_t,
            dep_compliance:    ok_d,
            memory_compliance: ok_m,
            purpose_aligned:   ok_s,
            score,
        }
    }

    /// Self-audit: does this NEI instance satisfy the four axioms
    /// as a runtime invariant? Returns a `SelfAudit` record.
    pub fn audit(&self) -> SelfAudit {
        // A1: lambda ≥ 0 (a non-negative constraint always exists)
        // A2: this method exists and is O(1) (quality is computable)
        // A3: tau ≥ 1 (a deadline always exists)
        // A4: sovereign_mode ∈ {true, false} and we report it
        let a1 = self.lambda >= 0.0;
        let a2 = true;
        let a3 = self.tau >= 1;
        let a4_true = self.sovereign_mode;
        let a4_false_acknowledged = !self.sovereign_mode; // the lie is named, not hidden
        let a4 = a4_true || a4_false_acknowledged;
        let sovereign_score = [a1, a2, a3, a4].iter().map(|b| *b as u8).sum::<u8>() as f64 / 4.0;
        SelfAudit {
            sovereign_score,
            sovereign_mode: self.sovereign_mode,
        }
    }
}

impl Default for NEI {
    fn default() -> Self { Self::new() }
}

// ────────────────────────────────────────────────────────────────
//   §3 — Output records
// ────────────────────────────────────────────────────────────────

/// One step of the collapse simulation.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Step {
    /// `Q = density / (complexity + ε)`
    pub quality: f64,
    /// The scalar NEI score, after the three transformations.
    pub nei_score: f64,
    /// `1 − t/τ` — the fraction of the deadline that remains.
    pub urgency: f64,
    /// The new step index.
    pub t: u32,
}

/// Result of `NEI::constraint_audit` — a four-axis compliance record.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Audit {
    /// `tool_count ≤ 3`
    pub tool_compliance:   bool,
    /// `dep_count ≤ 0`
    pub dep_compliance:    bool,
    /// `memory_bytes ≤ 50 MiB`
    pub memory_compliance: bool,
    /// `sovereign_mode == true`
    pub purpose_aligned:   bool,
    /// `mean(compliance booleans)` ∈ [0, 1]
    pub score: f64,
}

/// Result of `NEI::audit` — the four-axiom self-report.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SelfAudit {
    /// `mean(axiom booleans)` ∈ [0, 1]
    pub sovereign_score:  f64,
    /// A4 raw value.
    pub sovereign_mode:   bool,
}

// ────────────────────────────────────────────────────────────────
//   §4 — Tests
// ────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn psi_saturates_under_constraint() {
        // As x → ∞, ψ → 1/λ. With λ=0.1, the asymptote is 10.0.
        let big = 1e9_f64;
        let y = psi(big, 0.1);
        assert!((y - 10.0).abs() < 1e-3, "ψ(1e9, 0.1) ≈ 10.0, got {y}");
    }

    #[test]
    fn phi_is_monotone() {
        assert!(phi(0.0).abs() < 1e-12);
        assert!(phi(1.0) > 0.0);
        assert!(phi(10.0) > phi(1.0));
    }

    #[test]
    fn nabla_diverges_as_t_approaches_zero() {
        assert!(nabla(0.0) > nabla(1.0));
        assert!(nabla(1.0) > nabla(7.0));
    }

    #[test]
    fn nei_default_round_trips() {
        let mut n = NEI::new();
        assert_eq!(n.tau, 7);
        assert_eq!(n.t, 0);
        let s1 = n.evolve(0.5, 0.85);
        let s2 = n.evolve(0.5, 0.85);
        assert_eq!(s1.t, 1);
        assert_eq!(s2.t, 2);
        assert!(s1.urgency > s2.urgency);
    }

    #[test]
    fn tuned_rejects_zero_tau() {
        assert!(NEI::tuned(0.1, 0).is_none());
        assert!(NEI::tuned(0.1, 7).is_some());
        assert!(NEI::tuned(-0.1, 7).is_none());
    }

    #[test]
    fn audit_fails_when_dependencies_present() {
        let n = NEI::new();
        let a = n.constraint_audit(2, 1, 1024);
        assert!(a.tool_compliance);
        assert!(!a.dep_compliance);
        assert!(a.score < 1.0);
    }

    #[test]
    fn audit_passes_when_fully_constrained() {
        let n = NEI::new();
        let a = n.constraint_audit(2, 0, 1024);
        assert!(a.tool_compliance);
        assert!(a.dep_compliance);
        assert!((a.score - 1.0).abs() < 1e-9);
    }

    #[test]
    fn self_audit_full_compliance() {
        let n = NEI::new();
        let a = n.audit();
        assert_eq!(a.sovereign_score, 1.0);
    }

    #[test]
    fn collapse_returns_correct_step_count() {
        let mut n = NEI::new();
        let steps = n.collapse(0.5, 0.85, 7);
        assert_eq!(steps.len(), 7);
        // Quality is invariant across steps (same c, d).
        for w in steps.windows(2) {
            assert!((w[0].quality - w[1].quality).abs() < 1e-12);
        }
        // Urgency is strictly decreasing *within one full cycle*.
        // (At the cycle boundary t resets, and urgency jumps back up.
        // That is the correct behavior of the focus gradient — the
        // deadline is a recurring horizon, not a one-shot.)
        for w in steps.windows(2) {
            // strictly decreasing OR both 0 (no — only one boundary)
            if w[0].t < w[1].t {
                assert!(w[0].urgency > w[1].urgency,
                        "urgency must decrease within a cycle: t={}→{}, u={}→{}",
                        w[0].t, w[1].t, w[0].urgency, w[1].urgency);
            }
        }
    }
}
