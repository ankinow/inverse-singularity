/*! Compile-time constraint priming (zero deps, no dyn). */
/// Marker shim for compile-time constraint priming.
pub mod shim;

/// Re-export priming marker.
pub use shim::ConstraintPriming;
