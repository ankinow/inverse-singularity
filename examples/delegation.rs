//! `cargo run --example delegation` — IST Delegation Gateway demo.
//!
//! Shows the A2 crossover decision: when does fan-out to subagents
//! raise system quality, and when does coordination κ swamp the gain?
//!
//! Mirrors `python3 framework/gateway_engine.py` — the Rust and Python
//! outputs must agree to within the ε floor. This is the fingerprint
//! check for the delegation layer.

use ist::gateway::{ChildSpec, DelegationBudget, Gateway, GateReason};

fn main() {
    println!("IST Delegation Gateway — The A2 Crossover");
    println!("──────────────────────────────────────────────");
    println!("delegate iff  Q_delegated > (1 + gain) · Q_local");
    println!("──────────────────────────────────────────────");

    // ── Scenario 1: cheap coordination, high-value children ──
    let cheap = DelegationBudget {
        coordination_kappa: 0.1,
        merge_kappa: 0.1,
        ..DelegationBudget::default()
    };
    let g1 = Gateway::new(cheap);
    let children1 = [
        ChildSpec::new(0.9, 0.1), // dense child, cheap to run
        ChildSpec::new(0.8, 0.1), // second child — rising bar
    ];
    let d1 = g1.gate(0.2, 0.5, &children1);
    print_decision("Cheap coordination, 2 dense children", &d1);

    // ── Scenario 2: expensive coordination, mediocre children ──
    let expensive = DelegationBudget {
        coordination_kappa: 10.0,
        merge_kappa: 5.0,
        ..DelegationBudget::default()
    };
    let g2 = Gateway::new(expensive);
    let children2 = [
        ChildSpec::new(0.5, 0.1),
        ChildSpec::new(0.5, 0.1),
    ];
    let d2 = g2.gate(0.4, 1.0, &children2);
    print_decision("Expensive coordination, 2 mediocre children", &d2);

    // ── Scenario 3: entropy import — A4 refusal ──
    let g3 = Gateway::default_budget();
    let children3 = [ChildSpec::new(0.2, 3.0)]; // costs more than it gives
    let d3 = g3.gate(0.5, 1.0, &children3);
    print_decision("Entropy import (κ > d) — sovereign refusal", &d3);

    // ── Scenario 4: over-budget fan-out — A1 refusal ──
    let g4 = Gateway::default_budget();
    let children4: Vec<ChildSpec> = (0..8).map(|_| ChildSpec::new(0.9, 0.1)).collect();
    let d4 = g4.gate(0.5, 1.0, &children4);
    print_decision("8 children vs max_children=5 — A1 cap", &d4);

    println!("──────────────────────────────────────────────");
    let audit = g1.audit();
    println!("Gateway audit: sovereign_score={:.3} sovereign_mode={}",
             audit.sovereign_score, audit.sovereign_mode);
    println!("\"Delegation is a constraint, not a capability.\"");
}

fn print_decision(label: &str, d: &ist::gateway::GateDecision) {
    println!();
    println!("{label}");
    println!("  children={}  Q_local={:.4}  Q_deleg={:.4}  κ_sys={:.4}",
             d.children, d.q_local, d.q_delegated, d.kappa_system);
    let verdict = match d.reason {
        GateReason::Allowed => "✓ DELEGATE",
        GateReason::NoChildren => "✗ refuse (no children)",
        GateReason::TooManyChildren => "✗ refuse (A1 cap)",
        GateReason::SovereigntyViolation => "✗ refuse (A4 entropy)",
        GateReason::QualityCrossover => "✗ refuse (A2 crossover)",
    };
    println!("  → {verdict}");
}
