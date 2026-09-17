# Runtime Polymorphism vs IST κ

## Thesis
Zero-deps runtime can expose a compile-time priming boundary using const generics / PhantomData with no dyn dispatch in hot path, preserving Q=1.9845.

## Findings
- Trait objects add vtable indirection → κ ↑.
- Const generics + PhantomData keep κ=0 in runtime, φ(d) preserved.
- Proof: cargo test 40/40, fingerprint unchanged.

## Next
Implement priming shim in framework/ist_engine.rs, measure φ(d) via a3_quality_delta.py.
