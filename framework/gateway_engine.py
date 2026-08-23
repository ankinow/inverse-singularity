"""IST Delegation Gateway — Python reference (mirror of src/gateway.rs)

PRIMARY RUNTIME: Rust (`src/gateway.rs`, exported as `ist::gateway`).
THIS FILE: the Python reference, kept for didactic reasons and as a
fingerprint for the Rust port — both implementations MUST produce
identical decisions for identical inputs.

The gateway answers the delegation question in IST terms:

    Q_local     = φ(d_local) / κ_local
    Q_delegated = φ(d_merge) / (κ_local + N·κ_coord + κ_merge)

    delegate iff  Q_delegated > (1 + gain_threshold) · Q_local
              and N ≤ max_children
              and sovereignty is preserved

A2 applied to the agent's own runtime: sub-agents with narrow contexts
raise per-agent Q (the "Isolate strategy"), but coordination (briefs,
summaries, merges) adds κ at the system level. The gateway computes the
crossover point instead of guessing at it.
"""
import math

phi = lambda d: math.log(1 + d)          # φ: density enhancement


class GateReason:
    ALLOWED = "allowed"
    NO_CHILDREN = "no_children"
    TOO_MANY_CHILDREN = "too_many_children"
    SOVEREIGNTY_VIOLATION = "sovereignty_violation"
    QUALITY_CROSSOVER = "quality_crossover"


class DelegationBudget:
    def __init__(self, coordination_kappa=2.0, merge_kappa=1.0,
                 max_children=5, tau=7, gain_threshold=0.25):
        self.coordination_kappa = coordination_kappa
        self.merge_kappa = merge_kappa
        self.max_children = max_children
        self.tau = tau
        self.gain_threshold = gain_threshold


class ChildSpec:
    def __init__(self, density, complexity, accepts_tau=False):
        # `accepts_tau` mirrors the Boundary Paradox (Rust ChildSpec):
        # does the child accept the parent's deadline? Consent is
        # opt-in. A non-consenting child whose κ-import exceeds its
        # density is an imposed constraint (A4-mirrored) and is refused
        # by the gateway in sovereign mode; a consenting one makes the
        # same import a chosen constraint (A1-legitimate).
        self.density = density
        self.complexity = complexity
        self.accepts_tau = accepts_tau

    @classmethod
    def consenting(cls, density, complexity):
        return cls(density, complexity, accepts_tau=True)


class GateDecision:
    def __init__(self, delegate, reason, q_local, q_delegated,
                 kappa_system, children):
        self.delegate = delegate
        self.reason = reason
        self.q_local = q_local
        self.q_delegated = q_delegated
        self.kappa_system = kappa_system
        self.children = children


class Gateway:
    def __init__(self, budget=None, t=0, sovereign_mode=True):
        self.budget = budget or DelegationBudget()
        self.t = t
        self.sovereign_mode = sovereign_mode

    def system_kappa(self, local_kappa, children):
        return (local_kappa
                + children * self.budget.coordination_kappa
                + self.budget.merge_kappa)

    def urgency(self):
        return 1 - (self.t / self.budget.tau)

    def merge_density(self, children):
        sum_phi = sum(phi(c.density) for c in children)
        return math.expm1(sum_phi)  # e^Σφ − 1

    def max_child_density(self, children):
        return max((c.density for c in children), default=0.0)

    def gate(self, local_density, local_kappa, children):
        n = len(children)

        if n > self.budget.max_children:
            return GateDecision(False, GateReason.TOO_MANY_CHILDREN, 0, 0, 0, n)
        if n == 0:
            return GateDecision(False, GateReason.NO_CHILDREN, 0, 0, 0, 0)

        # A4: refuse to *impose* entropy. A non-consenting child whose
        # complexity exceeds its density is a κ-import the parent forces
        # across the child's boundary (A4-mirrored). A child that
        # accepted the parent's τ makes the same import a chosen
        # constraint (A1-legitimate). Consent is opt-in.
        if (self.sovereign_mode
                and any(not c.accepts_tau and c.complexity > c.density + 1e-9
                        for c in children)):
            return GateDecision(False, GateReason.SOVEREIGNTY_VIOLATION, 0, 0, 0, n)

        q_local = phi(local_density) / (local_kappa + 1e-9)
        d_merge = self.merge_density(children)
        kappa_system = self.system_kappa(local_kappa, n)
        q_delegated = phi(d_merge) / (kappa_system + 1e-9)

        if q_delegated > q_local * (1 + self.budget.gain_threshold):
            return GateDecision(True, GateReason.ALLOWED,
                                q_local, q_delegated, kappa_system, n)
        return GateDecision(False, GateReason.QUALITY_CROSSOVER,
                            q_local, q_delegated, kappa_system, n)

    def evolve(self):
        self.t = (self.t + 1) % self.budget.tau

    def audit(self):
        a1 = self.budget.max_children >= 1 and self.budget.gain_threshold >= 0.0
        a2 = self.budget.coordination_kappa >= 0.0 and self.budget.merge_kappa >= 0.0
        a3 = self.budget.tau >= 1
        a4 = self.sovereign_mode
        return {"sovereign_score": sum([a1, a2, a3, a4]) / 4.0,
                "sovereign_mode": self.sovereign_mode}
