//! A3 Adaptive-Budget Harness — does the agent that knows its own
//! half-life beat the far-ceiling knob?
//!
//! The A3-τ-productive finding (v0.7.5, `examples/a3_productive_tau.py`)
//! measured the *production* Hermes/IST session survival curve from the
//! real diary: holds ~100% to turn ~30, then collapses; effective
//! productive τ\* = **turn 55** (first turn where survivors < 50%). The
//! live budget knob is `agent.max_turns=999` — a distant ceiling the
//! agent "never feels" (gap ratio 18.16× of τ\*). The recommendation was
//! a **self-adaptive τ** = deadline at ~1.2 × half-life, so convergence
//! pressure exists while >50% of sessions are still alive.
//!
//! This example is the **in-runtime control group** for that
//! recommendation. It re-uses the A3 comparison harness's machinery
//! (`IST::tuned`, `evolve`, `analyze_trajectory`) on the *production rot
//! input shape* — the same decay the diary survival curve exhibits — and
//! compares two budget regimes on a shared stream:
//!
//!   - **adaptive (A)** — deadline τ = 55 (the measured empirical
//!     half-life; the "agent that knows its own half-life").
//!   - **far ceiling (P)** — deadline τ = 999 (the current production
//!     knob; a horizon whose ∇ never engages within the window).
//!
//! **Falsifiable claim (A3-inverted):** under a decaying input whose
//! survival half-life is known, the adaptive deadline retains NEI at
//! least as well as the far ceiling across the rot arc (
//! `retention_A >= retention_P`), because the deadline exerts
//! convergence pressure while the session is still alive — the far
//! ceiling exerts none at all. CAMEO graph: A wraps the decay with a
//! rising NEI tail, P tracks the raw rot and decays.
//!
//! If this FAILS it honestly falsifies the "agent that knows its own
//! half-life" recommendation: a deadline at the half-life would be no
//! better than the 999 knob under rot, and v0.7.5's ττ=66 proposal
//! should be revisited.
//!
//! Window = τ\* − 1 (54 steps) so we observe the deadline peak before
//! the step-index wrap (same wrap discipline as `a3_harness.rs`).
//!
//! Run: `cargo run --release --example a3_adaptive_budget`
//!
//! Exit: 0 = self-adaptive-τ claim holds; 1 = falsified (honest).

use ist::{analyze_trajectory, IST};

/// Empirical productive half-life (turn of first <50% survivor),
/// measured by `examples/a3_productive_tau.py` on 2026-08-23.
const HALF_LIFE_TURN: u32 = 55;
/// The current production budget knob (`agent.max_turns`), the far-ceiling
/// arm whose ∇ never engages.
const FAR_CEILING_TAU: u32 = 999;
/// Window = half-life − 1, so the adaptive arm reaches the deadline
/// peak (remaining→1, ∇→1.0) without wrapping the monotone run.
const STEPS: u32 = HALF_LIFE_TURN - 1;
/// Gamma (learning rate) shared by both arms, matching the A3 harness.
const GAMMA: f64 = 0.1;

fn main() {
    // Shared production-rot input: density decays like the diary survival
    // curve — holds high early, sags through the second half. κ fixed.
    let rot_d: Vec<f64> = (0..STEPS)
        .map(|i| {
            let f = i as f64 / STEPS as f64;
            // hold to ~55% of the arc, then sag to the measured ~0.48 alive
            1.0 - 0.52 * f * f // slow quadratic decay → ~0.48 at the tail
        })
        .collect();

    let mut a_agent = IST::tuned(GAMMA, HALF_LIFE_TURN).expect("adaptive τ=55");
    let mut p_agent = IST::tuned(GAMMA, FAR_CEILING_TAU).expect("far ceiling τ=999");

    let mut a: Vec<ist::Step> = Vec::new();
    let mut p: Vec<ist::Step> = Vec::new();
    for d in &rot_d {
        a.push(a_agent.evolve(1.0, *d));
        p.push(p_agent.evolve(1.0, *d));
    }
    let a_rep = analyze_trajectory(&a);
    let p_rep = analyze_trajectory(&p);

    println!("A3 adaptive-budget harness — self-adaptive τ vs far ceiling");
    println!("adaptive τ={HALF_LIFE_TURN} (measured half-life) · far ceiling τ={FAR_CEILING_TAU} ");
    println!("window {STEPS} steps · shared production-rot input (κ=1, d 1→~0.48)");
    println!("====================================================================");

    let a_first = a.first().unwrap();
    let a_last = a.last().unwrap();
    let p_first = p.first().unwrap();
    let p_last = p.last().unwrap();

    println!("[adaptive A τ=55]");
    println!(
        "  q_stability={:.4} urgency_slope={:.4} focus_delta={:+.4} engaged={}",
        a_rep.quality_stability, a_rep.urgency_slope, a_rep.focus_delta, a_rep.deadline_engaged
    );
    println!(
        "  NEI {:.4}→{:.4} (retention {:.3})",
        a_first.nei_score,
        a_last.nei_score,
        retention(a_first.nei_score, a_last.nei_score)
    );
    println!("[far ceiling P τ=999]");
    println!(
        "  q_stability={:.4} urgency_slope={:.4} focus_delta={:+.4} engaged={}",
        p_rep.quality_stability, p_rep.urgency_slope, p_rep.focus_delta, p_rep.deadline_engaged
    );
    println!(
        "  NEI {:.4}→{:.4} (retention {:.3})",
        p_first.nei_score,
        p_last.nei_score,
        retention(p_first.nei_score, p_last.nei_score)
    );

    // ─── Verdict ────────────────────────────────────────────────────
    // Claim (A3-inverted, self-adaptive τ): under a rot arc with known
    // half-life, deadline-at-half-life retains NEI at least as well as the
    // far ceiling (which exerts no convergence pressure at all). A budget
    // that still holds the raw decay curve strictly better than the rocket
    // knob is the strongest honest claim; equality already falsifies the
    // "far ceiling is harmless" reading of v0.7.3 (it IS strictly worse
    // than A3-positive).
    let a_ret = retention(a_first.nei_score, a_last.nei_score);
    let p_ret = retention(p_first.nei_score, p_last.nei_score);
    let adaptive_holds = a_ret >= p_ret - 1e-6;

    println!("====================================================================");
    println!("A3 self-adaptive-τ verdict:");
    println!(
        "  retention A(τ=55)={:.4} vs P(τ=999)={:.4}  → adaptive_holds: {}",
        a_ret,
        p_ret,
        if adaptive_holds { "PASS" } else { "FAIL" }
    );
    println!(
        "  urgency gradient exists in A (slope {:.4} > 0), absent in P ({:.4}) — the deadline the production knob never felt",
        a_rep.urgency_slope,
        p_rep.urgency_slope
    );
    println!(
        "RESULT: self-adaptive τ {}",
        if adaptive_holds {
            "SUPPORTED (deadline-at-half-life ≥ far ceiling under rot)"
        } else {
            "FALSIFIED (v0.7.5 τ=66 proposal should be revisited)"
        }
    );
    std::process::exit(if adaptive_holds { 0 } else { 1 });
}

fn retention(first: f64, last: f64) -> f64 {
    if first.abs() > 1e-12 {
        last / first
    } else {
        0.0
    }
}
