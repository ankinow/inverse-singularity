//! A3 Comparison Harness — the "no-deadline control group".
//!
//! CURIOSITY.md, "The Structural/Behavioral Split" (2026-06-23, Midday
//! dispatch): *"A3 can't be tested from inside the system that holds
//! it. The axiom is comparative ('a constrained agent converges to a
//! strictly better model than an unconstrained one') — two agents
//! required. The runtime has one. `collapse()` shows urgency rising
//! as t→τ, but the control group doesn't exist in the codebase: no
//! `--no-deadline` mode, no comparison harness, no paired experiment."*
//!
//! This example is that harness. It runs the paired N=1 experiment on
//! a shared input stream, sweeping two input regimes:
//!
//!   - **deadline agent (A)** — finite-τ IST (`tau = 7`). `Step.quality`
//!     is deadline-blind (A2, φ/κ), but `Step.nei_score` embeds ∇, so
//!     as the deadline closes the NEI score *rises* — the arc converges
//!     to a better model under pressure (A3 mechanism).
//!   - **control (C)** — no-deadline agent (τ = 1024; the axiom forbids
//!     a true τ=0, so the horizon is far enough that ∇ never engages).
//!     Its NEI score tracks the raw input only.
//!
//! **Regime 1 — constant input** (the classic 7-day collapse): density
//! and κ held fixed. Pure test of whether the deadline *does something*
//! to quality: A's NEI must rise (∇ grows while remaining→0) while C
//! stays flat.
//!
//! **Regime 2 — decaying input** (context rot, the Gamage curve):
//! density decays across the window while κ is fixed. Falsification
//! test: does the deadline *hold* NEI better (higher retention) than
//! the control when the underlying signal rots?
//!
//! Run: `cargo run --release --example a3_harness`
//!
//! Exit code: 0 if every A3 claim tested here is PASS, 1 otherwise
//! (a falsified claim is an honest, useful control result — never a
//! force-passed green).

use ist::{analyze_trajectory, IST};

/// The no-deadline control horizon. `IST::tuned` rejects `tau == 0`
/// (without a deadline there is no agent), so the control is a finite-
/// tau agent whose horizon never engages across the window.
const CONTROL_TAU: u32 = 1024;
/// The deadline-constrained agent's horizon: the classic 7-day mode.
const DEADLINE_TAU: u32 = 7;
/// Total steps in the experiment window.
///
/// One less than `DEADLINE_TAU` on purpose: after τ evolutions the
/// agent's step index wraps back to 0 and ∇ resets to its *load* point,
/// not its deadline point. To observe the deadline (the peak where
/// remaining→1 and ∇→1.0) we stop *at* t = τ−1, before the wrap. A
/// window that spans the wrap would reset the monotone run and hide the
/// A3 convergence — exactly what the first version of this harness hit.
const STEPS: u32 = DEADLINE_TAU - 1;

/// A full paired run over one input stream.
struct Run {
    label: String,
    a: Vec<ist::Step>,
    c: Vec<ist::Step>,
    a_report: ist::TrajectoryReport,
    c_report: ist::TrajectoryReport,
}

fn main() {
    // Regime 1 — constant input: no decay. The deadline must *do something*.
    let const_d: Vec<f64> = vec![1.0; STEPS as usize];
    let r1 = experiment("regime-1 constant input κ=1, d=1", 1.0, &const_d);

    // Regime 2 — decaying input (context rot, Gamage curve).
    let rot_d: Vec<f64> = (0..STEPS)
        .map(|i| {
            let f = i as f64 / STEPS as f64;
            1.0 - 0.30 * f
        })
        .collect();
    let r2 = experiment("regime-2 decaying input κ=1, d=1→0.7", 1.0, &rot_d);

    println!("A3 comparison harness — deadline agent vs no-deadline control");
    println!("Deadline τ={DEADLINE_TAU} · control τ≈∞ ({CONTROL_TAU}) · window {STEPS} steps");
    println!("====================================================================");

    println!("[{}]", r1.label);
    println!(
        "  A(τ=7)   q_stability={:.4} urgency_slope={:.4} focus_delta={:+.4} engaged={}",
        r1.a_report.quality_stability,
        r1.a_report.urgency_slope,
        r1.a_report.focus_delta,
        r1.a_report.deadline_engaged
    );
    println!(
        "  C(τ=∞)   q_stability={:.4} urgency_slope={:.4} focus_delta={:+.4} engaged={}",
        r1.c_report.quality_stability,
        r1.c_report.urgency_slope,
        r1.c_report.focus_delta,
        r1.c_report.deadline_engaged
    );
    report_nei(&r1);

    println!("[{}]", r2.label);
    println!(
        "  A(τ=7)   q_stability={:.4} urgency_slope={:.4} focus_delta={:+.4} engaged={}",
        r2.a_report.quality_stability,
        r2.a_report.urgency_slope,
        r2.a_report.focus_delta,
        r2.a_report.deadline_engaged
    );
    println!(
        "  C(τ=∞)   q_stability={:.4} urgency_slope={:.4} focus_delta={:+.4} engaged={}",
        r2.c_report.quality_stability,
        r2.c_report.urgency_slope,
        r2.c_report.focus_delta,
        r2.c_report.deadline_engaged
    );
    report_nei(&r2);

    // ─── Verdicts ────────────────────────────────────────────────────
    // Claim 1 (A3 mechanism, regime 1): deadline NEI rises as ∇ grows,
    // control stays flat. ∇(remaining) = 1/(remaining+ε) grows as
    // remaining→0, so A's NEI should climb when input is constant.
    // `first()`/`last()` are `Option`; the windows are non-empty by
    // construction, so `unwrap()` is sound here.
    let a1_last = r1.a.last().unwrap().nei_score;
    let a1_first = r1.a.first().unwrap().nei_score;
    let c1_last = r1.c.last().unwrap().nei_score;
    let c1_first = r1.c.first().unwrap().nei_score;
    let mech = a1_last > a1_first * 1.5 && (c1_last - c1_first).abs() < 1e-3;

    // Claim 2 (A3 separation): deadline agent sees an urgency gradient,
    // control is ~flat. `urgency_slope` is the honest separator — the
    // deadline_engaged flag alone cannot separate them within one window
    // (any ticking forward registers a monotone run).
    let slope = r1.a_report.urgency_slope > 1e-2 && r1.c_report.urgency_slope < 1e-3;

    // Claim 3 (A3 rescue, regime 2): the deadline retains NEI no worse
    // than the control under context rot. FAIL here is a genuine
    // falsification of "the deadline holds quality."
    let a_ret = retention(
        r2.a.first().unwrap().nei_score,
        r2.a.last().unwrap().nei_score,
    );
    let c_ret = retention(
        r2.c.first().unwrap().nei_score,
        r2.c.last().unwrap().nei_score,
    );
    let rescue = a_ret >= c_ret - 1e-6;

    println!("====================================================================");
    println!("A3 empirical verdicts (paired N=1):");
    println!(
        "  1. mechanism (const input, A-NEI rises vs C flat): {}  ## A {:+.4}→{:+.4} (Δ{:+.4}) · C flat {:+.4}",
        p(mech),
        a1_first,
        a1_last,
        a1_last - a1_first,
        c1_last - c1_first
    );
    println!(
        "  2. separation (urgency_slope A>0, C≈0):           {}  ## A={:.4} C={:.4}",
        p(slope),
        r1.a_report.urgency_slope,
        r1.c_report.urgency_slope
    );
    println!(
        "  3. rescue (NEI retention A≥C under rot):          {}  ## A={:.4} C={:.4}",
        p(rescue),
        a_ret,
        c_ret
    );
    let passed = mech && slope && rescue;
    println!(
        "RESULT: A3 {}",
        if passed {
            "CONFIRMED"
        } else {
            "FALSIFIED (honest control)"
        }
    );
    std::process::exit(if passed { 0 } else { 1 });
}

fn report_nei(r: &Run) {
    println!(
        "  A nei {:.4}→{:.4} (retention {:.2})   C nei {:.4}→{:.4} (retention {:.2})",
        r.a.first().unwrap().nei_score,
        r.a.last().unwrap().nei_score,
        retention(
            r.a.first().unwrap().nei_score,
            r.a.last().unwrap().nei_score
        ),
        r.c.first().unwrap().nei_score,
        r.c.last().unwrap().nei_score,
        retention(
            r.c.first().unwrap().nei_score,
            r.c.last().unwrap().nei_score
        )
    );
    println!("  --------------------------------------------------------------");
}

fn experiment(label: &str, kappa: f64, densities: &[f64]) -> Run {
    let mut a_agent = IST::tuned(0.1, DEADLINE_TAU).expect("deadline");
    let mut c_agent = IST::tuned(0.1, CONTROL_TAU).expect("control");

    let mut a = Vec::new();
    let mut c = Vec::new();
    for d in densities {
        a.push(a_agent.evolve(kappa, *d));
        c.push(c_agent.evolve(kappa, *d));
    }
    let a_report = analyze_trajectory(&a);
    let c_report = analyze_trajectory(&c);
    Run {
        label: label.to_string(),
        a,
        c,
        a_report,
        c_report,
    }
}

fn retention(first: f64, last: f64) -> f64 {
    if first.abs() > 1e-12 {
        last / first
    } else {
        0.0
    }
}

fn p(ok: bool) -> &'static str {
    if ok {
        "PASS"
    } else {
        "FAIL"
    }
}
