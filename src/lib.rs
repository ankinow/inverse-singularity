//! IST — Imposition-Guided Selection Engine
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
// of IST can return an iterator instead; that is left as a port, not
// a refactor (see framework/MANIFESTO-LINGUAGEM.md, §5).

// ────────────────────────────────────────────────────────────────
//   §0 — Module surface
// ────────────────────────────────────────────────────────────────

/// IST — Delegation Gateway. The IST-governed decision layer for
/// subagent fan-out: when to delegate, how many children, and under
/// which deadline, such that delegation increases Q instead of κ.
pub mod gateway;

// ────────────────────────────────────────────────────────────────
//   §1 — The three primitive transformations
// ────────────────────────────────────────────────────────────────

/// ψ (psi) — Constraint function.
///
/// `ψ(x, λ) = x / (1 + λ·x)`
///
/// As the constraint λ grows, the function saturates: input keeps
/// arriving, output is throttled. This is the imposition:
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
/// thousand cost a lot. This is the creative axis:
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
//   §2 — The IST struct
// ────────────────────────────────────────────────────────────────

/// An IST instance is a single ticking agent.
///
/// It owns three numbers:
/// - `lambda` (λ): the strength of the constraint (default 0.1)
/// - `tau`    (τ): the deadline in arbitrary steps (default 7)
/// - `t`      (t): the current step in `[0, tau)`
///
/// And one boolean: `sovereign_mode`, the A4 invariant.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct IST {
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

impl IST {
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
    /// primitive transformations, then return the scalar IST score.
    #[inline]
    #[must_use]
    pub fn inject(&self, c: f64, d: f64) -> f64 {
        let remaining = (self.tau as f64) - (self.t as f64);
        psi(c, self.lambda) * phi(d) * nabla(remaining)
    }

    /// Evolve the agent by one step. `state` is a `(complexity, density)`
    /// pair; the returned `Step` records the resulting Q, IST score,
    /// urgency, and the new step index.
    pub fn evolve(&mut self, complexity: f64, density: f64) -> Step {
        self.t = (self.t + 1) % self.tau;
        // A2-canonical quality: Q = φ(d) / (κ + ε). The φ transform is
        // the mathematical encoding of A2 — the first units of density
        // are cheap, later ones face a rising bar. Computing quality as
        // a raw density/κ ratio (as earlier versions did) treats all
        // density contributions as linearly equal, which is anti-A2.
        // Aligned with the core equation 2026-08-14 (see CURIOSITY.md,
        // "κ Proliferation" thread — RESOLVED at runtime layer).
        let quality = phi(density) / (complexity + f64::EPSILON);
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

    /// Audit an external system against the four IST hard limits.
    /// Returns an `Audit` record with per-axis compliance + a score.
    pub fn constraint_audit(&self, tool_count: u32, dep_count: u32, memory_bytes: u64) -> Audit {
        const MAX_TOOLS:   u32 = 3;
        const MAX_DEPS:    u32 = 0;
        const MAX_MEM_MB:  u64 = 50;
        let max_mem_bytes = MAX_MEM_MB * 1024 * 1024;

        let ok_t = tool_count <= MAX_TOOLS;
        // A1 zero-deps doctrine: MAX_DEPS is 0, so `==` is the faithful
        // encoding of "at most zero dependencies" (u32 cannot be negative);
        // clippy::absurd_extreme_comparisons flags the `<=` form.
        let ok_d = dep_count  == MAX_DEPS;
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

    /// Self-audit: does this IST instance satisfy the four axioms
    /// as a runtime invariant? Returns a `SelfAudit` record.
    pub fn audit(&self) -> SelfAudit {
        // A1: lambda ≥ 0 (a non-negative constraint always exists)
        // A2: this method exists and is O(1) (quality is computable)
        // A3: tau ≥ 1 (a deadline always exists)
        let a1 = self.lambda >= 0.0;
        let a2 = true;
        let a3 = self.tau >= 1;
        // A4: sovereign_mode ∈ {true, false} and we report it. Previously
        // `a4 = sovereign_mode || !sovereign_mode` made A4 identically true —
        // the audit could never report a sovereignty lapse (unfalsifiable
        // invariant, flagged by CURIOSITY.md 2026-06-18). Now A4 is true
        // only when sovereignty is actually held; a surrendered system
        // scores honestly.
        let a4 = self.sovereign_mode;
        let sovereign_score = [a1, a2, a3, a4].iter().map(|b| *b as u8).sum::<u8>() as f64 / 4.0;
        SelfAudit {
            sovereign_score,
            sovereign_mode: self.sovereign_mode,
        }
    }
}

impl Default for IST {
    fn default() -> Self { Self::new() }
}

// ────────────────────────────────────────────────────────────────
//   §3 — Output records
// ────────────────────────────────────────────────────────────────

/// One step of the collapse simulation.
#[derive(Debug, Clone, Copy, PartialEq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Step {
    /// `Q = φ(density) / (complexity + ε)` — the A2-canonical quality.
    pub quality: f64,
    /// The scalar IST score, after the three transformations.
    pub nei_score: f64,
    /// `1 − t/τ` — the fraction of the deadline that remains.
    pub urgency: f64,
    /// The new step index.
    pub t: u32,
}

/// Result of `IST::constraint_audit` — a four-axis compliance record.
#[derive(Debug, Clone, Copy, PartialEq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
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

/// Result of `IST::audit` — the four-axiom self-report.
#[derive(Debug, Clone, Copy, PartialEq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct SelfAudit {
    /// `mean(axiom booleans)` ∈ [0, 1]
    pub sovereign_score:  f64,
    /// A4 raw value.
    pub sovereign_mode:   bool,
}

// ────────────────────────────────────────────────────────────────
//   §3b — Trajectory analysis (A3: deadline-aware quality)
// ────────────────────────────────────────────────────────────────
//
// CURIOSITY.md, "Structural/Behavioral Split" (2026-06-22, Morning
// dispatch): *"maybe A3's proper expression isn't a field in `Step`
// at all, but a function over `Vec<Step>` — something that reads the
// arc, not the point."* `Step.quality` is A2 (local, static per
// input); `Step.nei_score`/`Step.urgency` are A3 (global, respond to
// the deadline). The split lives in the memory layout of `Step`.
// This function is the A3 view of a trajectory: it reads the arc,
// not the point, and asks whether the deadline *does something* to
// the agent.

/// Reads the arc of a `Vec<Step>` (A3 view), not any single point.
///
/// The four IST axioms split into two kinds: A1/A2/A4 are structural
/// (checkable on one `NEI` instance), A3 is behavioral (only readable
/// across a trajectory under pressure). This report is the A3 lever:
/// it quantifies how the arc bends, and whether quality holds while
/// the deadline closes.
#[derive(Debug, Clone, Copy, PartialEq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct TrajectoryReport {
    /// Number of steps in the arc.
    pub length: usize,
    /// `1 − σ_quality / μ_quality` — quality stability across the arc.
    /// 1.0 means constant quality (A2 holds, nothing decays); near 0
    /// means the arc collapsed (A2 erosion, the Gamage curve).
    pub quality_stability: f64,
    /// Mean absolute change of `urgency` per step. Positive = the arc
    /// is under a closing deadline (A3 active); 0 = a flat horizon
    /// (A3 absent — the "no-deadline control group" of the thread).
    pub urgency_slope: f64,
    /// `nei_score.last − nei_score.first` as a fraction of the first.
    /// The NEI score embeds ∇, so under a real deadline this should be
    /// positive — the arc *converges to a better model* as t→τ (A3).
    pub focus_delta: f64,
    /// WINDOW-LOCAL monotone-deadline detector (see §3b gap note below).
    ///
    /// `0` if the arc contains no monotone urgency descent; `1` if
    /// urgency is strictly decreasing across at least one adjacent pair
    /// (run length ≥ 2) inside the window.
    ///
    /// ⚠️ **Scope warning (docstring is intentionally honest):** this
    /// flag is single-window and *cannot separate a real deadline from a
    /// far horizon*. Any ticking forward produces a (possibly tiny)
    /// monotone urgency descent, so even a no-deadline control with a
    /// far τ reports `engaged = 1` within a short window — the τ=1024
    /// control in `examples/a3_harness.rs` does exactly that which is
    /// why the harness's A3-separation verdict keys on `urgency_slope`
    /// (the gradient), not on this flag. Do **not** use `deadline_engaged`
    /// alone to assert A3; prefer `urgency_slope > 0` for that claim.
    ///
    /// ([Structural/Behavioral Split → A3, §3b documentation gap —
    /// CURIOSITY 2026-08-22])
    pub deadline_engaged: u8,
}

/// Analyze a collapse arc from the A3 (behavioral/trajectory) view.
///
/// `analyze_trajectory` is the complement of `Step.quality` (the A2
/// point view). It is deadline-blind service-quality, so it does not
/// collapse; urgency is never folded into `Step.quality`, keeping the
/// two measures honest about what they each represent.
#[must_use]
pub fn analyze_trajectory(steps: &[Step]) -> TrajectoryReport {
    let length = steps.len();

    // Quality stability (A2 erosion test): coefficient of variation.
    let q_mean = steps.iter().map(|s| s.quality).sum::<f64>() / length.max(1) as f64;
    let q_var = steps
        .iter()
        .map(|s| (s.quality - q_mean).powi(2))
        .sum::<f64>()
        / length.max(1) as f64;
    let q_sd = q_var.sqrt();
    let stability = if q_mean > 1e-12 { 1.0 - (q_sd / q_mean) } else { 1.0 };

    // Urgency slope (A3 engagement): mean |Δ urgency| per adjacent pair.
    let mut slope_sum = 0.0;
    let mut pairs = 0usize;
    for w in steps.windows(2) {
        slope_sum += (w[1].urgency - w[0].urgency).abs();
        pairs += 1;
    }
    let slope = if pairs > 0 { slope_sum / pairs as f64 } else { 0.0 };

    // Focus delta (A3 convergence): how the deadline bends NEI score.
    let focus_delta = if length > 1 {
        let first = steps[0].nei_score;
        let last = steps[length - 1].nei_score;
        if first.abs() > 1e-12 {
            (last - first) / first.abs()
        } else {
            0.0
        }
    } else {
        0.0
    };

    // Deadline engaged: is urgency strictly decreasing across any full
    // monotone run of length ≥ 2 (i.e. not just the wrap-around jump)?
    let mut engaged = 0u8;
    let mut run = 1usize;
    for w in steps.windows(2) {
        if w[0].t < w[1].t && w[1].urgency < w[0].urgency {
            run += 1;
        } else if w[0].t > w[1].t {
            run = 1;
        }
    }
    if run >= 2 {
        engaged = 1;
    }

    TrajectoryReport {
        length,
        quality_stability: stability.max(0.0),
        urgency_slope: slope,
        focus_delta,
        deadline_engaged: engaged,
    }
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
        let mut n = IST::new();
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
        assert!(IST::tuned(0.1, 0).is_none());
        assert!(IST::tuned(0.1, 7).is_some());
        assert!(IST::tuned(-0.1, 7).is_none());
    }

    #[test]
    fn audit_fails_when_dependencies_present() {
        let n = IST::new();
        let a = n.constraint_audit(2, 1, 1024);
        assert!(a.tool_compliance);
        assert!(!a.dep_compliance);
        assert!(a.score < 1.0);
    }

    #[test]
    fn audit_passes_when_fully_constrained() {
        let n = IST::new();
        let a = n.constraint_audit(2, 0, 1024);
        assert!(a.tool_compliance);
        assert!(a.dep_compliance);
        assert!((a.score - 1.0).abs() < 1e-9);
    }

    #[test]
    fn self_audit_full_compliance() {
        let n = IST::new();
        let a = n.audit();
        assert_eq!(a.sovereign_score, 1.0);
    }

    #[test]
    fn audit_is_falsifiable_on_sovereignty() {
        // Regression for CURIOSITY.md 2026-06-18: `audit()` used to compute
        // `a4 = sovereign_mode || !sovereign_mode` which is always true, so
        // the sovereign_score was always 1.0 — the audit could never report
        // a sovereignty lapse. Now a surrendered system must score honestly.
        let sovereign = IST {
            lambda: 0.1,
            tau: 7,
            t: 0,
            sovereign_mode: true,
        };
        let surrendered = IST {
            lambda: 0.1,
            tau: 7,
            t: 0,
            sovereign_mode: false,
        };

        let sa = sovereign.audit();
        assert_eq!(sa.sovereign_mode, true);
        // A1+A2+A3 true, A4 true  -> 4/4
        assert!((sa.sovereign_score - 1.0).abs() < 1e-12, "sovereign score {:.4}", sa.sovereign_score);

        let su = surrendered.audit();
        assert_eq!(su.sovereign_mode, false);
        // A1+A2+A3 true, A4 false -> 3/4 (HONEST — was bugged to 4/4)
        assert!((su.sovereign_score - 0.75).abs() < 1e-12, "surrendered score {:.4}", su.sovereign_score);
    }

    #[test]
    fn collapse_returns_correct_step_count() {
        let mut n = IST::new();
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

    #[test]
    fn trajectory_holds_quality_and_flags_deadline() {
        // A3 view over one full 7-day collapse. Quality must be constant
        // (A2 is deadline-blind → perfect stability), focus_delta must be
        // positive (the NEI score embeds ∇, so the arc bends upward as the
        // deadline closes), and the deadline must read as engaged.
        //
        // NOTE: we sample `tau - 1` steps (t=1..6 for tau=7) so the arc
        // ends at the tightest pre-wrap urgency. A 7th step would wrap
        // t back to 0 and urgency back to its loosest — the recurring
        // horizon documented in `collapse_returns_correct_step_count`.
        // That wrap is not "convergence"; it is the deadline restarting.
        let mut n = IST::new();
        let steps = n.collapse(0.31, 0.85, 6);
        let tr = analyze_trajectory(&steps);

        assert_eq!(tr.length, 6);
        // A2 quality is invariant per input → coefficient of variation 0.
        assert!((tr.quality_stability - 1.0).abs() < 1e-12,
                "quality_stability={:.6}", tr.quality_stability);
        // Urgency strictly decreases within the cycle → mean slope > 0.
        assert!(tr.urgency_slope > 0.0, "urgency_slope={:.6}", tr.urgency_slope);
        // NEI score rises as t→τ (focus gradient) → focus_delta positive.
        assert!(tr.focus_delta > 0.0, "focus_delta={:.6}", tr.focus_delta);
        assert_eq!(tr.deadline_engaged, 1);
    }

    #[test]
    fn deadline_engaged_is_not_an_a3_separator() {
        // §3b documentation gap (CURIOSITY 2026-08-22): `deadline_engaged`
        // is a WINDOW-LOCAL monotone detector. Any ticking forward — even
        // a far horizon with a tiny slope — produces a monotone urgency
        // descent, so it cannot separate a real (near) deadline from a
        // no-deadline control. That job belongs to `urgency_slope` (the
        // gradient). This test pins that doctrine in the code so the
        // docstring warning cannot silently regress.
        //
        // Build two arcs that both tick forward (t: 1→6) and both fire
        // engaged=1, but with very different urgency descent magnitude:
        // a near deadline (τ=7, urgency 1.0→~0.14) vs a far horizon
        // (τ=1024, urgency 1.0→~0.994).
        let near: Vec<Step> = (1u32..=6).map(|t| Step {
            quality: 1.0,
            nei_score: 10.0,
            urgency: 1.0 - (t as f64 / 7.0),
            t,
        }).collect();
        let far: Vec<Step> = (1u32..=6).map(|t| Step {
            quality: 1.0,
            nei_score: 10.0,
            urgency: 1.0 - (t as f64 / 1024.0),
            t,
        }).collect();

        let near_tr = analyze_trajectory(&near);
        let far_tr = analyze_trajectory(&far);

        // Both fire the (window-local) monotone flag — the very ambiguity
        // the §3b finding names.
        assert_eq!(near_tr.deadline_engaged, 1);
        assert_eq!(far_tr.deadline_engaged, 1);
        // ...but the gradient separates them by an order of magnitude,
        // which is why `urgency_slope` (not `engaged`) is the honest A3
        // separator named in the §3b finding.
        assert!(near_tr.urgency_slope > 0.1, "near slope={:.4}", near_tr.urgency_slope);
        assert!(far_tr.urgency_slope < 0.002, "far slope={:.6}", far_tr.urgency_slope);
    }

    #[test]
    fn trajectory_flat_when_no_steps() {
        // Edge case: an empty arc cannot declare a deadline.
        let empty: Vec<Step> = Vec::new();
        let tr = analyze_trajectory(&empty);
        assert_eq!(tr.length, 0);
        assert_eq!(tr.deadline_engaged, 0);
        assert_eq!(tr.urgency_slope, 0.0);
        assert_eq!(tr.focus_delta, 0.0);
    }

    #[test]
    fn trajectory_distinguishes_arc_from_point_stability() {
        // Hand-build two arcs that share a *single-point* quality but
        // differ in their arc shape: quality eroded vs quality held.
        let start = Step { quality: 1.0, nei_score: 10.0, urgency: 1.0, t: 1 };
        let held = Step { quality: 1.0, nei_score: 11.0, urgency: 0.5, t: 2 };
        let eroded = Step { quality: 0.3, nei_score: 11.0, urgency: 0.5, t: 2 };

        let stable_arc = analyze_trajectory(&[start, held]);
        let decay_arc = analyze_trajectory(&[start, eroded]);

        // The point view (last quality) differs, but the whole-point view
        // is where A3 lives: stability captures erosion the point cannot.
        assert_eq!(stable_arc.quality_stability, 1.0);
        assert!(decay_arc.quality_stability < 0.5,
                "decayed arc stability={:.4}", decay_arc.quality_stability);
        // Same urgency slope, same focus delta: only stability separates them.
        assert_eq!(stable_arc.urgency_slope, decay_arc.urgency_slope);
        assert_eq!(stable_arc.focus_delta, decay_arc.focus_delta);
    }
}
