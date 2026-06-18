//! `cargo run --example tuned` — `IST::tuned()` constructor demo.
//!
//! Shows which (λ, τ) pairs produce a valid agent and how the
//! resulting IST score surface behaves across different constraints.

use ist::IST;

fn main() {
    println!("IST Tuned Constructor — (λ, τ) Grid");
    println!("──────────────────────────────────────");
    println!("τ must be ≥ 1. λ must be finite and ≥ 0.");
    println!();

    let lambdas: &[f64] = &[0.0, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0];
    let taus: &[u32] = &[0, 1, 3, 7, 14, 28];

    println!("  λ↓ / τ→   {:>5} {:>5} {:>5} {:>5} {:>5} {:>5}",
             taus[0], taus[1], taus[2], taus[3], taus[4], taus[5]);
    println!("  {:-<40}", "");

    for &lambda in lambdas {
        print!("  {:>8.3} ", lambda);
        for &tau in taus {
            match IST::tuned(lambda, tau) {
                Some(agent) => {
                    // Inject a canonical (c=0.5, d=0.85) pair to sample
                    // the score surface.
                    let s = agent.inject(0.5, 0.85);
                    print!("{:>5.2} ", s);
                }
                None => {
                    print!("  --  ");
                }
            }
        }
        println!();
    }

    println!();
    println!("--- Detailed analysis ---");
    println!();

    // Rejection cases
    for (lambda, tau, why) in &[
        (-0.1, 7, "negative λ"),
        (0.1, 0, "zero τ"),
        (f64::NAN, 7, "NaN λ"),
        (f64::INFINITY, 7, "infinite λ"),
    ] {
        let result = IST::tuned(*lambda, *tau);
        println!(
            "  tuned(λ={}, τ={}) -> {}  // {}",
            lambda, tau,
            if result.is_some() { "Some" } else { "None" },
            why
        );
    }

    println!();
    println!("--- Score surface along τ axis (λ=0.1) ---");
    for tau in 1..=10 {
        let agent = IST::tuned(0.1, tau).unwrap();
        let s = agent.inject(0.5, 0.85);
        println!("  τ={:>2}  IST={:.5}  urgency(t=0)={:.4}", tau, s, 1.0 / (tau as f64 + f64::EPSILON));
    }

    println!();
    println!("--- Score surface along λ axis (τ=7) ---");
    for lambda in [0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0] {
        let agent = IST::tuned(lambda, 7).unwrap();
        let c = 0.5;
        let psi_val = c / (1.0 + lambda * c);
        let s = agent.inject(c, 0.85);
        println!("  λ={:>5.2}  ψ(c)={:.5}  IST={:.5}", lambda, psi_val, s);
    }

    println!();
    println!("\"Tune the constraint, not the output.\"");
}
