use std::marker::PhantomData;

/// Compile-time constraint priming marker.
/// Zero runtime cost: const generic encodes constraint density d,
/// PhantomData prevents any allocation / dyn dispatch.
/// Preserves IST κ invariant (Q = φ(d)/κ + ε).
pub struct ConstraintPriming<const D: usize> {
    _marker: PhantomData<()>,
}

impl<const D: usize> ConstraintPriming<D> {
    /// Create a new priming marker (zero cost).
    pub const fn new() -> Self {
        Self { _marker: PhantomData }
    }
    /// Density function φ(d) = ln(1 + d) as per IST Axiom A2.
    /// Provided as non-const to avoid const-ln limitation (Rust 1.80).
    pub fn phi() -> f64 {
        ((D as f64) + 1.0).ln()
    }
}

#[cfg(test)]
mod tests {
    use super::ConstraintPriming;
    #[test]
    fn phi_zero() {
        assert!((ConstraintPriming::<0>::phi() - 0.0).abs() < 1e-12);
    }
    #[test]
    fn phi_monotonic() {
        assert!(ConstraintPriming::<1>::phi() > ConstraintPriming::<0>::phi());
    }
}
