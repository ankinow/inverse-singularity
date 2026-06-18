"""IST Engine - Imposition-Guided Selection (Math-Only, <70 lines)

PRIMARY RUNTIME: Rust (`src/lib.rs`, see `Cargo.toml`).
THIS FILE: the Python reference. Kept for didactic reasons and as a
fingerprint for the Rust port — both implementations MUST produce
identical scalar outputs.

There is no default language. Rust is the current expression of the
four IST axioms at the type and runtime layer. Python is the
expression at the didactic layer. Neither is "the truth." The axioms
are the truth; both files are the fingerprints.

See `framework/MANIFESTO-LINGUAGEM.md` for the full statement of
virtue. See `src/lib.rs` for the Rust primary.

NB: ∇ epsilon — Python uses 1e-9 (didactic clarity); Rust uses
f64::EPSILON (~2.22e-16). Both are valid floors that prevent the
t=0 singularity. Outputs diverge at ~7th decimal place.
"""
import math

psi = lambda x, c: x / (1 + c * x)           # ψ: Constraint function
phi = lambda d: math.log(1 + d)              # φ: Density enhancement
nabla = lambda t: 1 / (t + 1e-9)             # ∇: Focus gradient (ε differs from Rust)

class IST:
    Q_ZERO_DEPS = "Can I do this with zero external deps?"
    Q_HALF_MEM = "Can I achieve the result with 50% less memory?"
    Q_ELEGANT_ALGO = "Is there an elegant algorithm that makes brute force obsolete?"
    Q_ARCHITECT_PURPOSE = "Does this action serve my Architect's purpose?"

    def __init__(self, lam=0.1, tau=7, sovereign_mode=True):
        self.lam, self.tau, self.t = lam, tau, 0
        self.sovereign_mode = sovereign_mode

    @classmethod
    def tuned(cls, lam, tau):
        if tau == 0 or not math.isfinite(lam) or lam < 0.0:
            return None
        return cls(lam=lam, tau=tau)

    def inject(self, c, d):
        return psi(c, self.lam) * phi(d) * nabla(self.tau - self.t)

    def evolve(self, c, d):
        self.t = (self.t + 1) % self.tau
        return {
            "quality": d / (c + 1e-9),
            "nei_score": self.inject(c, d),
            "urgency": 1 - (self.t / self.tau),
            "t": self.t
        }

    def collapse(self, c, d, steps):
        return [self.evolve(c, d) for _ in range(steps)]

    def constraint_audit(self, tool_count, dep_count, memory_bytes):
        max_tools, max_deps, max_mem_mb = 3, 0, 50
        ok_t = tool_count <= max_tools
        ok_d = dep_count <= max_deps
        ok_m = memory_bytes <= max_mem_mb * 1024 * 1024
        return {"tool_compliance": ok_t, "dep_compliance": ok_d,
                "memory_compliance": ok_m, "purpose_aligned": self.sovereign_mode,
                "score": sum([ok_t, ok_d, ok_m, self.sovereign_mode]) / 4.0}

    def audit(self):
        a1, a2, a3, a4 = self.lam >= 0.0, True, self.tau >= 1, self.sovereign_mode
        return {"sovereign_score": sum([a1, a2, a3, a4]) / 4.0,
                "sovereign_mode": self.sovereign_mode}
