//! `cargo run --example audit` — constraint_audit demo.
//!
//! Runs the four-axis compliance check across several tool/dep/mem
//! combinations, showing which configurations pass the IST hard limits.

use ist::IST;

fn main() {
    let agent = IST::new();

    println!("IST Constraint Audit — Hard Limit Compliance Matrix");
    println!("─────────────────────────────────────────────────────");
    println!("Limits: tools ≤ 3 | deps = 0 | memory ≤ 50 MiB");
    println!();

    let cases: &[(&str, u32, u32, u64)] = &[
        ("Minimal CLI tool        ", 1, 0, 1024),
        ("Heavy tooling            ", 7, 0, 1024),
        ("One dependency           ", 2, 1, 1024),
        ("Memory hog (200 MiB)     ", 2, 0, 200 * 1024 * 1024),
        ("Perfect compliance       ", 2, 0, 1024),
        ("Worst case (all fail)    ", 7, 5, 200 * 1024 * 1024),
        ("Edge: exactly 3 tools    ", 3, 0, 1024),
        ("Edge: 50 MiB exactly     ", 2, 0, 50 * 1024 * 1024),
    ];

    println!("{:<25} {:>6} {:>6} {:>12} {:>8}", "Scenario", "tools", "deps", "mem (bytes)", "score");
    println!("{:-<63}", "");

    for (label, tools, deps, mem) in cases {
        let a = agent.constraint_audit(*tools, *deps, *mem);
        println!(
            "{:<25} {:>6} {:>6} {:>12} {:>8.3}",
            label, tools, deps, mem, a.score
        );
    }

    println!();
    println!("Detailed breakdown for worst case:");
    let worst = agent.constraint_audit(7, 5, 200 * 1024 * 1024);
    println!("  tool_compliance:    {}", worst.tool_compliance);
    println!("  dep_compliance:     {}", worst.dep_compliance);
    println!("  memory_compliance:  {}", worst.memory_compliance);
    println!("  purpose_aligned:    {}", worst.purpose_aligned);
    println!("  score:              {:.3}", worst.score);

    println!();
    println!("\"The cage defines what passes.\"");
}
