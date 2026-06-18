//! `cargo run --example collapse` — the canonical 7-day collapse demo.
//!
//! Mirrors `python3 framework/nei_engine.py` exactly, byte-for-symbol.
//! This is the *fingerprint check*: the Rust output must equal the
//! Python output. If it doesn't, one of the two is wrong.

use ist::{IST, Step};

fn main() {
    println!("IST Engine v5 — Constraint-Driven Intelligence Amplification");
    println!("   (Rust primary · zero external crates · MIT)");
    println!("─────────────────────────────────────────────────────────────");

    let mut agent = IST::new();
    let complexity: f64 = 0.31;
    let density:    f64 = 0.85;

    println!("In 7 days:");
    println!("  φ(d)         = {:>8.4}   conceptual density", density.ln_1p());
    println!("  κ            = {:>8.4}   complexity entropy", complexity);
    println!("  Q            = {:>8.4}   quality ratio",     density / (complexity + f64::EPSILON));
    println!("─────────────────────────────────────────────────────────────");

    let steps: Vec<Step> = agent.collapse(complexity, density, 7);
    for s in &steps {
        println!("  t={}  Q={:>6.3}  IST={:>9.5}  urgency={:.4}",
                 s.t, s.quality, s.nei_score, s.urgency);
    }

    let audit = agent.constraint_audit(2, 0, 1024);
    println!("─────────────────────────────────────────────────────────────");
    println!("Audit: tool={}  dep={}  mem={}  purpose={}  score={:.3}",
             audit.tool_compliance,
             audit.dep_compliance,
             audit.memory_compliance,
             audit.purpose_aligned,
             audit.score);

    let self_audit = agent.audit();
    println!("Self:  sovereign_score={:.3}  sovereign_mode={}",
             self_audit.sovereign_score, self_audit.sovereign_mode);
    println!("─────────────────────────────────────────────────────────────");
    println!("\"The cage is the cathedral.\"");
}
