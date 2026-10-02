#!/usr/bin/env python3
"""
Demonstration of constraint_portfolio function from ist-runtime.
Shows how adding mirrored constraints decreases Q (quality) per the Boundary Paradox.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from ist_engine import constraint_portfolio, phi_sourced, ConstraintSource

def main():
    print("=== constraint_portfolio demo ===\n")
    
    # Base kappa (complexity) for the agent's runtime
    baseline_kappa = 0.31  # as used in the ist-runtime examples
    
    # Example constraint: a chosen constraint with density d = 1.0
    d_chosen = 1.0
    # phi_sourced(d, chosen) = ln(1+d)
    density_chosen = phi_sourced(d_chosen, ConstraintSource.CHOSEN)
    print(f"Chosen constraint: d={d_chosen}, phi_sourced(d, chosen) = ln(1+{d_chosen}) = {density_chosen:.4f}")
    
    # Portfolio with only the chosen constraint
    chosen_only = [(d_chosen, ConstraintSource.CHOSEN)]
    result_chosen = constraint_portfolio(chosen_only, baseline_kappa)
    print(f"\nPortfolio (chosen only):")
    print(f"  density = Σ phi(chosen) = {result_chosen['density']:.4f}")
    print(f"  burden = Σ mirrored = {result_chosen['burden']:.4f}")
    print(f"  quality = density / (baseline_kappa + burden + ε) ≈ {result_chosen['quality']:.4f} (ε≈0)")
    print(f"  at_mirror_threshold = {result_chosen['at_mirror_threshold']}")
    
    # Add a mirrored constraint with same d (but mirrored contributes 0 to phi, d to burden)
    d_mirrored = 1.0
    mixed = [
        (d_chosen, ConstraintSource.CHOSEN),
        (d_mirrored, ConstraintSource.MIRRORED)
    ]
    result_mixed = constraint_portfolio(mixed, baseline_kappa)
    print(f"\nPortfolio (chosen + mirrored):")
    print(f"  density = Σ phi(chosen) = {result_mixed['density']:.4f}")
    print(f"  burden = Σ mirrored = {result_mixed['burden']:.4f}")
    print(f"  quality = density / (baseline_kappa + burden + ε) ≈ {result_mixed['quality']:.4f} (ε≈0)")
    print(f"  at_mirror_threshold = {result_mixed['at_mirror_threshold']}")
    
    # Show the relative drop in Q
    q_drop = result_chosen['quality'] - result_mixed['quality']
    print(f"\nQuality drop due to adding one mirrored constraint: {q_drop:.4f}")
    print(f"Relative drop: {(q_drop / result_chosen['quality'] * 100):.1f}%")
    
    # Demonstrate the threshold: when burden > density
    print(f"\nBoundary analysis:")
    print(f"  For chosen-only: burden ({result_chosen['burden']:.4f}) > density ({result_chosen['density']:.4f})? {result_chosen['burden'] > result_chosen['density']}")
    print(f"  For mixed portfolio: burden ({result_mixed['burden']:.4f}) > density ({result_mixed['density']:.4f})? {result_mixed['burden'] > result_mixed['density']}")
    print(f"  at_mirror_threshold is True when burden > density")
    
    # Additional test: empty portfolio
    empty = []
    result_empty = constraint_portfolio(empty, baseline_kappa)
    print(f"\nEmpty portfolio:")
    print(f"  density = {result_empty['density']:.4f}, burden = {result_empty['burden']:.4f}, quality = {result_empty['quality']:.4f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())