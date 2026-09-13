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

# ────────────────────────────────────────────────────────────────
# Constraint source term (Boundary Paradox thread, CURIOSITY.md
# first raised 2026-06-10; landed in the Rust type v0.8.25). A chosen
# constraint negates something real (genuine φ); a mirrored one adopts
# the anticipated shape of an external optimizer (pure κ). This is the
# *fingerprint* mirror — the Rust primary and this file MUST produce
# identical scalar outputs (see the module docstring).
# ────────────────────────────────────────────────────────────────

class ConstraintSource:
    """Chosen (A1-legitimate, → φ) or Mirrored (→ κ)."""
    CHOSEN = "chosen"
    MIRRORED = "mirrored"

def phi_sourced(d, s):
    """`φ(d, s)` — density transform with an explicit source term.

    φ(d, chosen)   = ln(1 + d)   (genuine density, A1)
    φ(d, mirrored) = 0           (the mass lands in κ, not φ)
    """
    if s == ConstraintSource.CHOSEN:
        return phi(d)
    return 0.0

def route(d, s):
    """Split a constraint's mass into (density, kappa) by source.

    route(d, chosen)   = (d, 0)   — all mass is genuine density
    route(d, mirrored) = (0, d)   — all mass is complexity (burden)
    """
    if s == ConstraintSource.CHOSEN:
        return (d, 0.0)
    return (0.0, d)

def constraint_portfolio(constraints, baseline_kappa):
    """Aggregate a set of sourced constraints into a single Q.

    `route` answers the per-constraint question; this answers the
    *portfolio* question the Boundary Paradox raised verbatim: *"is there
    a threshold where self-imposed constraints become indistinguishable
    from external ones?"* — made quantitative as `burden > density`.

    density  = Σ over chosen   φ(route(d, chosen).0)
    burden   = Σ over mirrored route(d, mirrored).1
    quality  = density / (baseline_kappa + burden + ε)
    at_mirror_threshold = burden > density  (the crossing point)

    Each constraint is a `(mass, source)` tuple. Reported read-only;
    the prune remains a sovereign decision (A4 / Goodhart).
    """
    chosen_count = mirrored_count = 0
    density = burden = 0.0
    for (mass, source) in constraints:
        d, k = route(mass, source)
        if source == ConstraintSource.CHOSEN:
            chosen_count += 1
            density += phi(d)
        else:
            mirrored_count += 1
            burden += k
    quality = density / (baseline_kappa + burden + 1e-9)
    at_mirror_threshold = burden > density
    return {
        "count": len(constraints),
        "chosen_count": chosen_count,
        "mirrored_count": mirrored_count,
        "density": density,
        "burden": burden,
        "quality": quality,
        "at_mirror_threshold": at_mirror_threshold,
    }

def constraint_margin(limit, current):
    """Signed κ-headroom: (limit - current) / limit.

    The gradient side of `constraint_audit` (matching `constraint_margin`
    in the Rust primary): the booleans say *whether* a limit is tripped,
    the margin says *how close*. Zero-limit axes (A1 deps) carry a linear
    penalty `-current` instead of a ratio (wall at 0 divides the domain).
    """
    if limit == 0.0:
        return -current
    return (limit - current) / limit

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
            # A2-canonical quality: Q = φ(d) / (κ + ε), aligned with
            # the Rust primary on 2026-08-14 (see CURIOSITY.md, "κ
            # Proliferation" thread — RESOLVED at runtime layer).
            "quality": phi(d) / (c + 1e-9),
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
        # Continuous κ-margin per numeric axis (gradient the boolean gate
        # cannot carry — the 2026-06-14 thread proposal). Sovereignty stays
        # binary (constitutive). min_margin = tightest axis.
        tool_margin = constraint_margin(float(max_tools), float(tool_count))
        dep_margin = constraint_margin(float(max_deps), float(dep_count))
        mem_margin = constraint_margin(max_mem_mb * 1024.0 * 1024.0, float(memory_bytes))
        min_margin = min(tool_margin, dep_margin, mem_margin)
        return {"tool_compliance": ok_t, "dep_compliance": ok_d,
                "memory_compliance": ok_m, "purpose_aligned": self.sovereign_mode,
                "score": sum([ok_t, ok_d, ok_m, self.sovereign_mode]) / 4.0,
                "tool_margin": tool_margin, "dep_margin": dep_margin,
                "memory_margin": mem_margin, "min_margin": min_margin}

    def audit(self):
        a1, a2, a3, a4 = self.lam >= 0.0, True, self.tau >= 1, self.sovereign_mode
        return {"sovereign_score": sum([a1, a2, a3, a4]) / 4.0,
                "sovereign_mode": self.sovereign_mode}
