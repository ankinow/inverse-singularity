//! IST — Delegation Gateway
//! =================================================================
//! The IST-governed decision layer for subagent fan-out.
//!
//! **The question this module answers:** when should a sovereign agent
//! delegate work to children, how many children, and under which
//! deadline — such that the delegation increases Q instead of
//! increasing κ?
//!
//! ```text
//!   Q_local     = φ(d_local) / κ_local
//!   Q_delegated = φ(d_merge) / (κ_local + N·κ_coord + κ_merge)
//!
//!   delegate iff  Q_delegated > (1 + gain_threshold) · Q_local
//!             and N ≤ max_children
//!             and sovereignty is preserved
//! ```
//!
//! This is A2 applied to the agent's own runtime: sub-agents with
//! narrow contexts raise per-agent Q (the "Isolate strategy" that
//! every orchestration framework has rediscovered), but the
//! coordination substrate (briefs, summaries, merge passes) adds κ at
//! the system level. The industry measurement — up to 15× tokens for
//! multi-agent workflows over single-chat — is κ growth swamping the
//! φ gains. The gateway computes the crossover point instead of
//! guessing at it.

#![forbid(unsafe_code)]
#![deny(missing_docs)]

use crate::phi;

// ────────────────────────────────────────────────────────────────
//   §1 — Configuration
// ────────────────────────────────────────────────────────────────

/// The delegation budget: the constraints under which fan-out is allowed.
///
/// Every field is a hard limit (A1) — the wall that defines the door.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DelegationBudget {
    /// κ cost of coordinating one child: brief in + summary out.
    /// Expressed in the same normalized κ units as `ChildSpec.complexity`.
    pub coordination_kappa: f64,
    /// κ cost of merging N child summaries into one result.
    pub merge_kappa: f64,
    /// Hard cap on concurrent children (A1 constraint primacy).
    pub max_children: u32,
    /// Deadline horizon for the fan-out, in steps (A3 collapse mode).
    pub tau: u32,
    /// Minimum Q improvement required to justify delegation, e.g.
    /// `0.25` means "delegated Q must beat local Q by 25%".
    pub gain_threshold: f64,
}

impl Default for DelegationBudget {
    fn default() -> Self {
        Self {
            // A single child round-trip costs roughly its brief + its
            // summary — about 2κ units of coordination overhead.
            coordination_kappa: 2.0,
            // The merge pass is bounded: the aggregator reads N short
            // summaries, not N full transcripts.
            merge_kappa: 1.0,
            // Default fan-out cap: the sweet spot from orchestration
            // literature is 2–5 children; beyond that, coordination κ
            // grows faster than φ can compensate.
            max_children: 5,
            // Default deadline: 7 steps, the canonical Collapse Mode.
            tau: 7,
            // Default gain threshold: delegation must beat local Q by
            // at least 25% to justify its κ.
            gain_threshold: 0.25,
        }
    }
}

// ────────────────────────────────────────────────────────────────
//   §2 — Child specification
// ────────────────────────────────────────────────────────────────

/// One candidate child: its expected density, its expected cost, and
/// whether it *accepts* the parent's deadline (`τ`).
///
/// The third field encodes the Boundary Paradox (CURIOSITY thread
/// "The Delegation Boundary") at the child scale: a parent optimizes a
/// child against the parent's own budget, but `A4` says every agent is
/// an *imposition-refuser* — a child that did not choose the parent's
/// `τ` is a boundary the parent cannot price, only cross. So a κ-import
/// is only legitimate (A1-chosen, not A4-mirrored) when the child
/// itself consented to the parent's horizon.
///
/// Consent is **opt-in, not silent-default**: an unlabeled child is
/// assumed NOT to accept the parent's `τ` (a sovereign boundary the
/// gateway must not cross). Use [`ChildSpec::consenting`] to mark one
/// that has.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ChildSpec {
    /// Expected density contribution `d` of this child's result.
    pub density: f64,
    /// Expected complexity `κ` of this child's local execution.
    pub complexity: f64,
    /// Whether the child accepts the parent's deadline `τ` — the
    /// A1/A4 boundary marker. `false` = the child runs under its own
    /// sovereign horizon, which the parent may not impose on.
    pub accepts_tau: bool,
}

impl ChildSpec {
    /// Construct a child with a known (density, complexity) estimate
    /// that has **not** declared consent to the parent's `τ`.
    ///
    /// Such a child's κ-import is an imposed constraint (A4-mirrored):
    /// in sovereign mode it is a boundary crossing, not a chosen one.
    #[must_use]
    pub const fn new(density: f64, complexity: f64) -> Self {
        Self {
            density,
            complexity,
            accepts_tau: false,
        }
    }

    /// Construct a child that explicitly accepts the parent's deadline
    /// `τ`. Its κ-import is a *chosen* constraint (A1-legitimate): the
    /// child's own sovereign boundary consented to the parent's
    /// horizon, so the A4 refusal does not apply to it.
    #[must_use]
    pub const fn consenting(density: f64, complexity: f64) -> Self {
        Self {
            density,
            complexity,
            accepts_tau: true,
        }
    }
}

// ────────────────────────────────────────────────────────────────
//   §3 — The gateway
// ────────────────────────────────────────────────────────────────

/// An IST delegation gateway: decides whether a sovereign agent may
/// fan work out to children, under the budget's constraints.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Gateway {
    /// The hard constraints of this gateway.
    pub budget: DelegationBudget,
    /// Current step in `[0, tau)` — drives A3 urgency.
    pub t: u32,
    /// A4: when `true`, the gateway refuses delegations that would
    /// import external entropy (children whose purpose diverges from
    /// the Architect's purpose cannot be spawned).
    pub sovereign_mode: bool,
}

impl Gateway {
    /// Construct a gateway from a budget. Defaults match the Python
    /// reference (`framework/gateway_engine.py`).
    #[must_use]
    pub const fn new(budget: DelegationBudget) -> Self {
        Self {
            budget,
            t: 0,
            sovereign_mode: true,
        }
    }

    /// Construct a gateway with default budget.
    #[must_use]
    pub fn default_budget() -> Self {
        Self::new(DelegationBudget::default())
    }

    /// The system-level κ of delegating to `n` children:
    /// `κ_system = κ_local + n·κ_coord + κ_merge`.
    #[inline]
    #[must_use]
    pub fn system_kappa(&self, local_kappa: f64, children: u32) -> f64 {
        local_kappa + (children as f64) * self.budget.coordination_kappa + self.budget.merge_kappa
    }

    /// A3 urgency: the fraction of the deadline that remains.
    #[inline]
    #[must_use]
    pub fn urgency(&self) -> f64 {
        1.0 - (self.t as f64 / self.budget.tau as f64)
    }

    /// The merge density: child densities combine logarithmically
    /// (φ is additive in log-space, so `φ(d_merge) = Σ φ(d_child)`).
    /// This encodes A2 at the fan-out level: the first child is cheap,
    /// each additional child must clear a rising bar to add φ.
    #[inline]
    #[must_use]
    pub fn merge_density(&self, children: &[ChildSpec]) -> f64 {
        // d_merge is the density whose φ equals the sum of child φs.
        // φ(d) = ln(1+d)  →  d = e^Σφ − 1
        let sum_phi: f64 = children.iter().map(|c| phi(c.density)).sum();
        sum_phi.exp_m1()
    }

    /// The highest single-child density — the "oracle child" ceiling
    /// for Q comparison when a merge is not worth its κ.
    #[inline]
    #[must_use]
    pub fn max_child_density(&self, children: &[ChildSpec]) -> f64 {
        children.iter().map(|c| c.density).fold(0.0_f64, f64::max)
    }

    /// Gate decision: should the agent delegate to these children?
    ///
    /// Evaluates the A2 crossover:
    /// ```text
    ///   Q_local     = φ(d_local) / κ_local
    ///   Q_delegated = φ(d_merge) / κ_system
    /// ```
    /// and returns `delegate = true` only if the delegated quality
    /// beats the local quality by `gain_threshold`, the child count is
    /// within budget, and sovereignty is preserved.
    #[must_use]
    pub fn gate(
        &self,
        local_density: f64,
        local_kappa: f64,
        children: &[ChildSpec],
    ) -> GateDecision {
        let n = children.len() as u32;

        // A1: hard cap on fan-out.
        if n > self.budget.max_children {
            return GateDecision::refuse(GateReason::TooManyChildren, n);
        }
        if n == 0 {
            return GateDecision::refuse(GateReason::NoChildren, 0);
        }

        // A4: refuse to *impose* entropy — a non-consenting child whose
        // expected complexity exceeds its density is a net κ import the
        // parent forces across the child's boundary (A4-mirrored). A
        // child that explicitly accepted the parent's τ makes that same
        // κ-import a *chosen* constraint (A1-legitimate): its own
        // sovereign boundary consented, so the refusal does not apply.
        // Consent is opt-in — a silent child is never assumed to accept.
        if self.sovereign_mode
            && children
                .iter()
                .any(|c| !c.accepts_tau && c.complexity > c.density + f64::EPSILON)
        {
            return GateDecision::refuse(GateReason::SovereigntyViolation, n);
        }

        // A2: the crossover computation.
        let q_local = phi(local_density) / (local_kappa + f64::EPSILON);
        let d_merge = self.merge_density(children);
        let kappa_system = self.system_kappa(local_kappa, n);
        let q_delegated = phi(d_merge) / (kappa_system + f64::EPSILON);

        let beats_local = q_delegated > q_local * (1.0 + self.budget.gain_threshold);
        if beats_local {
            GateDecision::allow(q_local, q_delegated, kappa_system, n)
        } else {
            GateDecision::refuse(GateReason::QualityCrossover, n)
        }
    }

    /// Advance the gateway one step. Call after each fan-out round so
    /// that A3 pressure accumulates across rounds.
    pub fn evolve(&mut self) {
        self.t = (self.t + 1) % self.budget.tau;
    }

    /// Four-axis self-audit, mirroring `IST::audit` at the gateway
    /// layer.
    #[must_use]
    pub fn audit(&self) -> GatewayAudit {
        let a1 = self.budget.max_children >= 1 && self.budget.gain_threshold >= 0.0;
        let a2 = self.budget.coordination_kappa >= 0.0 && self.budget.merge_kappa >= 0.0;
        let a3 = self.budget.tau >= 1;
        let a4 = self.sovereign_mode;
        let sovereign_score = [a1, a2, a3, a4].iter().map(|b| *b as u8).sum::<u8>() as f64 / 4.0;
        GatewayAudit {
            sovereign_score,
            sovereign_mode: a4,
        }
    }
}

impl Default for Gateway {
    fn default() -> Self {
        Self::default_budget()
    }
}

// ────────────────────────────────────────────────────────────────
//   §4 — Decision records
// ────────────────────────────────────────────────────────────────

/// Why the gateway refused (or allowed) a delegation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GateReason {
    /// Delegation is permitted.
    Allowed,
    /// Zero children were proposed — nothing to delegate.
    NoChildren,
    /// `children.len() > max_children` — A1 hard cap.
    TooManyChildren,
    /// A child would import more κ than it contributes — A4.
    SovereigntyViolation,
    /// `Q_delegated ≤ (1 + gain_threshold)·Q_local` — A2 crossover
    /// not met. This is the *good* refusal: the gateway protected the
    /// system from its own fan-out.
    QualityCrossover,
}

/// The outcome of a `Gateway::gate` call.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct GateDecision {
    /// Whether delegation is permitted.
    pub delegate: bool,
    /// The reason for the decision.
    pub reason: GateReason,
    /// `Q_local = φ(d_local)/κ_local`.
    pub q_local: f64,
    /// `Q_delegated = φ(d_merge)/κ_system`.
    pub q_delegated: f64,
    /// The system-level κ of the proposed fan-out.
    pub kappa_system: f64,
    /// The number of children proposed.
    pub children: u32,
}

impl GateDecision {
    #[must_use]
    fn allow(q_local: f64, q_delegated: f64, kappa_system: f64, children: u32) -> Self {
        Self {
            delegate: true,
            reason: GateReason::Allowed,
            q_local,
            q_delegated,
            kappa_system,
            children,
        }
    }

    #[must_use]
    fn refuse(reason: GateReason, children: u32) -> Self {
        Self {
            delegate: false,
            reason,
            q_local: 0.0,
            q_delegated: 0.0,
            kappa_system: 0.0,
            children,
        }
    }
}

/// Result of `Gateway::audit` — the four-axiom self-report at the
/// delegation layer.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct GatewayAudit {
    /// `mean(axiom booleans)` ∈ [0, 1].
    pub sovereign_score: f64,
    /// A4 raw value.
    pub sovereign_mode: bool,
}

// ────────────────────────────────────────────────────────────────
//   §5 — Tests
// ────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn refuses_zero_children() {
        let g = Gateway::default_budget();
        let d = g.gate(0.5, 1.0, &[]);
        assert!(!d.delegate);
        assert_eq!(d.reason, GateReason::NoChildren);
    }

    #[test]
    fn refuses_over_budget_fanout() {
        let g = Gateway::default_budget();
        let many: Vec<ChildSpec> = (0..8).map(|_| ChildSpec::new(0.9, 0.1)).collect();
        let d = g.gate(0.5, 1.0, &many);
        assert!(!d.delegate);
        assert_eq!(d.reason, GateReason::TooManyChildren);
    }

    #[test]
    fn refuses_entropy_import_in_sovereign_mode() {
        let g = Gateway::default_budget();
        // This child costs more κ than it contributes AND has not
        // accepted the parent's τ → A4 boundary crossing (imposed).
        let bad = [ChildSpec::new(0.2, 3.0)];
        let d = g.gate(0.5, 1.0, &bad);
        assert!(!d.delegate);
        assert_eq!(d.reason, GateReason::SovereigntyViolation);
    }

    #[test]
    fn consenting_kappa_import_is_chosen_not_imposed() {
        // The same κ-import is A1-legitimate when the child explicitly
        // accepts the parent's τ — its own boundary consented, so the
        // A4 refusal does not apply. It proceeds to the A2 crossover.
        let g = Gateway::default_budget();
        let consenting = [ChildSpec::consenting(0.2, 3.0)];
        let d = g.gate(0.5, 1.0, &consenting);
        // Not refused on A4; the decision is now purely A2-driven.
        assert_ne!(d.reason, GateReason::SovereigntyViolation);
    }

    #[test]
    fn sovereignty_violation_must_involve_non_consent() {
        // In non-sovereign mode even a non-consenting κ-import is
        // allowed to reach the A2 crossover — sovereignty is a choice.
        let g = Gateway {
            sovereign_mode: false,
            ..Gateway::default_budget()
        };
        let imposed = [ChildSpec::new(0.2, 3.0)];
        let d = g.gate(0.5, 1.0, &imposed);
        assert_ne!(d.reason, GateReason::SovereigntyViolation);
        assert!(!d.delegate, "default κ still fails A2 crossover");
    }

    #[test]
    fn consent_is_opt_in_not_silent_default() {
        // Skinny child from the default constructor carries no consent:
        // if it would κ-import, the gateway treats it as an imposed
        // boundary even though `new` never mentioned a deadline.
        let g = Gateway::default_budget();
        let silent = [ChildSpec::new(0.2, 3.0)];
        let d = g.gate(0.5, 1.0, &silent);
        assert!(!d.delegate);
        assert_eq!(d.reason, GateReason::SovereigntyViolation);
    }

    #[test]
    fn allows_high_value_children() {
        // Low coordination cost, high child density → crossover met.
        let budget = DelegationBudget {
            coordination_kappa: 0.1,
            merge_kappa: 0.1,
            ..DelegationBudget::default()
        };
        let g = Gateway::new(budget);
        let children = [ChildSpec::new(0.9, 0.1), ChildSpec::new(0.8, 0.1)];
        let d = g.gate(0.2, 0.5, &children);
        assert!(d.delegate, "expected allow, got {d:?}");
        assert_eq!(d.reason, GateReason::Allowed);
        assert_eq!(d.children, 2);
    }

    #[test]
    fn refuses_when_coordination_kappa_swamps_gain() {
        // Expensive coordination + mediocre children → the *good*
        // refusal: delegation would lower system Q.
        let budget = DelegationBudget {
            coordination_kappa: 10.0,
            merge_kappa: 5.0,
            ..DelegationBudget::default()
        };
        let g = Gateway::new(budget);
        let children = [ChildSpec::new(0.5, 0.1), ChildSpec::new(0.5, 0.1)];
        let d = g.gate(0.4, 1.0, &children);
        assert!(!d.delegate);
        assert_eq!(d.reason, GateReason::QualityCrossover);
    }

    #[test]
    fn merge_density_combines_in_phi_space() {
        // Two children with d=0.5 each: φ(d) = ln(1.5) ≈ 0.4055, so
        // d_merge = e^(2·0.4055) − 1 = 2.25 − 1 = 1.25. Density
        // combines *superadditively* in d-space because φ is concave
        // (each child contributes its own φ, and the merge inverts
        // the sum). The A2 bar is on the κ side: each additional
        // child costs the same coordination κ but must clear a rising
        // φ bar relative to system κ.
        let g = Gateway::default_budget();
        let one = [ChildSpec::new(0.5, 0.1)];
        let two = [ChildSpec::new(0.5, 0.1), ChildSpec::new(0.5, 0.1)];
        let d1 = g.merge_density(&one);
        let d2 = g.merge_density(&two);
        let expected_one = phi(0.5).exp_m1(); // e^φ(0.5) − 1 = 0.5
        assert!(
            (d1 - expected_one).abs() < 1e-12,
            "d1={d1}, expected {expected_one}"
        );
        assert!((d2 - 1.25).abs() < 1e-12, "d2={d2}, expected 1.25");
        assert!(d2 > d1);
        // Per-child φ contribution is additive: φ(d2) = 2·φ(d1).
        assert!((phi(d2) - 2.0 * phi(d1)).abs() < 1e-12);
    }

    #[test]
    fn urgency_decays_as_gateway_evolves() {
        let mut g = Gateway::default_budget();
        let u0 = g.urgency();
        g.evolve();
        let u1 = g.urgency();
        assert!(u1 < u0);
    }

    #[test]
    fn audit_full_compliance() {
        let g = Gateway::default_budget();
        let a = g.audit();
        assert_eq!(a.sovereign_score, 1.0);
        assert!(a.sovereign_mode);
    }
}
