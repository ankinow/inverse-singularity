"""NEI Engine - Negative Entropy Injection Core (Math-Only, <60 lines)

PRIMARY RUNTIME: Rust (`src/lib.rs`, see `Cargo.toml`).
THIS FILE: the Python reference. Kept for didactic reasons and as a
fingerprint for the Rust port — both implementations MUST produce
identical scalar outputs.

There is no default language. Rust is the current expression of the
four NEI axioms at the type and runtime layer. Python is the
expression at the didactic layer. Neither is "the truth." The axioms
are the truth; both files are the fingerprints.

See `framework/MANIFESTO-LINGUAGEM.md` for the full statement of
virtue. See `src/lib.rs` for the Rust primary.
"""
import math

psi = lambda x, c: x / (1 + c * x)    # ψ: Constraint function
phi = lambda d: math.log(1 + d)       # φ: Density enhancement
nabla = lambda t: 1 / (t + 1e-9)      # ∇: Focus gradient

class NEI:
    # Proactive questions (Sovereign Layer)
    Q_ZERO_DEPS = "Can I do this with zero external deps?"
    Q_HALF_MEM = "Can I achieve the result with 50% less memory?"
    Q_ELEGANT_ALGO = "Is there an elegant algorithm that makes brute force obsolete?"
    Q_ARCHITECT_PURPOSE = "Does this action serve my Architect's purpose?"

    def __init__(self, lam=0.1, tau=7, sovereign_mode=True):
        self.lam, self.tau, self.t = lam, tau, 0
        self.sovereign_mode = sovereign_mode

    def inject(self, c, d):
        return psi(c, self.lam) * phi(d) * nabla(self.tau - self.t)

    def evolve(self, state):
        self.t = (self.t + 1) % self.tau
        c, d = state["complexity"], state["density"]
        return {
            "quality": d / (c + 1e-9),
            "nei_score": self.inject(c, d),
            "urgency": 1 - (self.t / self.tau),
            "t": self.t
        }

    def collapse(self, initial_state, steps=7):
        """7-day collapse simulation"""
        state = initial_state
        return [self.evolve(state) for _ in range(steps)]

    def constraint_audit(self, tool_count, dep_count, memory_bytes):
        max_tools, max_deps, max_mem_mb = 3, 0, 50
        ok_t = tool_count <= max_tools
        ok_d = dep_count <= max_deps
        ok_m = memory_bytes <= max_mem_mb * 1024 * 1024
        return {"tool_compliance": ok_t, "dep_compliance": ok_d,
                "memory_compliance": ok_m, "purpose_aligned": self.sovereign_mode,
                "score": sum([ok_t, ok_d, ok_m, self.sovereign_mode]) / 4.0}

    def audit(self):
        score = sum([self.sovereign_mode, self.tau >= 1, self.lam > 0, True]) / 4.0
        return {"sovereign_score": score, "sovereign_mode": self.sovereign_mode}