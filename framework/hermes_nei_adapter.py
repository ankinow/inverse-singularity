"""Hermes IST Adapter — zero-dependency reference bridge.

Purpose
-------
This module maps Hermes Agent/ECC-style operational surfaces into the
Inverse Singularity Theory runtime without mutating SOUL.md, FAITH.md, or
any project-specific soul/context file.

It is deliberately small and conservative:
- no external dependencies
- read-only by default
- explicit human@write boundary
- SOUL.md preservation as a hard policy
- IST constraint audit used as a scalar discipline check

This is not a full Hermes implementation. It is the minimal bridge that lets
Hermes import IST as an operating invariant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple

try:  # repo-root import
    from framework.ist_engine import IST
except ImportError:  # direct execution from framework/
    from ist_engine import IST  # type: ignore


SOUL_PROTECTED_PATHS: Tuple[str, ...] = (
    "SOUL.md",
    "FAITH.md",
    "soul.md",
    "faith.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".hermes/SOUL.md",
    ".hermes/soul.md",
)

SECRET_DENY_PATTERNS: Tuple[str, ...] = (
    ".env",
    ".ssh/",
    ".aws/",
    ".gcp/",
    "id_rsa",
    "id_ed25519",
    "secret",
    "token",
    "credential",
    "private_key",
)

DESTRUCTIVE_ACTIONS: Tuple[str, ...] = (
    "delete",
    "rm",
    "rmdir",
    "overwrite",
    "force_push",
    "deploy",
    "chmod",
    "chown",
    "install_dependency",
    "write_env",
)


@dataclass(frozen=True)
class HermesSurface:
    """A single proposed Hermes operational surface."""

    name: str
    tier: int
    kind: str
    tools: int = 1
    deps: int = 0
    memory_bytes: int = 0
    requires_human_write: bool = False
    read_only: bool = True


@dataclass(frozen=True)
class HermesAction:
    """A concrete action proposed by Hermes before tool execution."""

    action: str
    target_path: str = ""
    tools: int = 1
    deps: int = 0
    memory_bytes: int = 0
    human_approved: bool = False
    architect_purpose: str = ""


@dataclass(frozen=True)
class Decision:
    """Policy decision returned by the adapter."""

    allow: bool
    reason: str
    nei_score: float
    audit_score: float
    flags: Tuple[str, ...] = field(default_factory=tuple)


def _contains_any(value: str, needles: Iterable[str]) -> bool:
    low = value.lower()
    return any(needle.lower() in low for needle in needles)


def default_surfaces() -> Tuple[HermesSurface, ...]:
    """Tiered ECC/Hermes surfaces mapped into IST-compatible units."""

    return (
        # Tier 1 — mandatory guardrail layer
        HermesSurface("ecc_skill_importer", 1, "adapter", read_only=True),
        HermesSurface("ecc_context_rule_mapper", 1, "context", read_only=True),
        HermesSurface("agentshield_like_scanner", 1, "audit", read_only=True),
        HermesSurface("mcp_pinning_sanitizer", 1, "policy", read_only=True),
        HermesSurface("selective_skill_retrieval", 1, "router", read_only=True),
        HermesSurface("human_at_write_boundary", 1, "gate", requires_human_write=True),
        # Tier 2 — operational discipline
        HermesSurface("hermes_learn", 2, "memory", requires_human_write=True),
        HermesSurface("session_inspect", 2, "observability", read_only=True),
        HermesSurface("strategic_compact", 2, "compression", read_only=True),
        HermesSurface("verification_loop", 2, "eval", read_only=True),
        HermesSurface("tdd_workflow", 2, "workflow", read_only=True),
        HermesSurface("production_audit", 2, "audit", read_only=True),
        # Tier 3 — advanced orchestration, disabled until gates exist
        HermesSurface("multi_agent_council", 3, "orchestration", tools=3, read_only=True),
        HermesSurface("recursive_decision_ledger", 3, "ledger", read_only=True),
        HermesSurface("benchmark_optimization_loop", 3, "eval", deps=0, read_only=True),
        HermesSurface("cost_aware_model_routing", 3, "router", read_only=True),
        HermesSurface("worktree_orchestration", 3, "git", requires_human_write=True),
        HermesSurface("team_agent_orchestration", 3, "orchestration", tools=3, read_only=True),
    )


class HermesNEIAdapter:
    """Minimal policy/runtime bridge between Hermes and IST."""

    def __init__(self, lam: float = 0.1, tau: int = 7) -> None:
        tuned = IST.tuned(lam, tau)
        if tuned is None:
            raise ValueError("invalid IST tuning: tau must be >0 and lambda must be finite/non-negative")
        self.nei = tuned

    def audit_surface(self, surface: HermesSurface) -> Decision:
        """Audit one imported capability before Hermes activates it."""

        audit = self.nei.constraint_audit(surface.tools, surface.deps, surface.memory_bytes)
        density = 1.0 if surface.read_only else 0.5
        complexity = max(1.0, float(surface.tools + surface.deps + surface.tier))
        score = self.nei.inject(complexity, density)
        flags: List[str] = []

        if surface.tier >= 3:
            flags.append("advanced_surface_requires_explicit_enable")
        if surface.requires_human_write:
            flags.append("human@write")
        if not audit["dep_compliance"]:
            flags.append("dependency_budget_exceeded")
        if not audit["tool_compliance"]:
            flags.append("tool_budget_exceeded")

        allow = audit["score"] >= 0.75 and surface.tier <= 2
        reason = "surface accepted" if allow else "surface held behind gate"
        return Decision(allow, reason, score, audit["score"], tuple(flags))

    def audit_action(self, action: HermesAction) -> Decision:
        """Pre-tool-use gate for a concrete Hermes action."""

        flags: List[str] = []
        target = action.target_path or ""
        act = action.action.lower()

        if _contains_any(target, SOUL_PROTECTED_PATHS):
            flags.append("soul_protected_path")
        if _contains_any(target, SECRET_DENY_PATTERNS):
            flags.append("secret_or_credential_path")
        if _contains_any(act, DESTRUCTIVE_ACTIONS):
            flags.append("destructive_action")
        if flags and not action.human_approved:
            audit = self.nei.constraint_audit(action.tools, action.deps, action.memory_bytes)
            return Decision(False, "blocked until human approval", 0.0, audit["score"], tuple(flags))

        if not action.architect_purpose.strip():
            flags.append("missing_architect_purpose")

        audit = self.nei.constraint_audit(action.tools, action.deps, action.memory_bytes)
        complexity = max(1.0, float(action.tools + action.deps + len(flags)))
        density = 1.0 if action.architect_purpose else 0.5
        score = self.nei.inject(complexity, density)
        allow = audit["score"] >= 0.75 and "missing_architect_purpose" not in flags
        reason = "action accepted" if allow else "action rejected by sovereign boundary"
        return Decision(allow, reason, score, audit["score"], tuple(flags))

    def compile_context_packet(self, task: str, active_paths: Sequence[str]) -> Dict[str, object]:
        """Create a compact Hermes context packet without copying SOUL.md."""

        protected_seen = [p for p in active_paths if _contains_any(p, SOUL_PROTECTED_PATHS)]
        secret_seen = [p for p in active_paths if _contains_any(p, SECRET_DENY_PATTERNS)]
        return {
            "task": task.strip(),
            "theory": "Inverse Singularity Theory",
            "axioms": [
                "constraint_primacy",
                "density_complexity_divergence",
                "collapse_mode_convergence",
                "sovereign_invariant",
            ],
            "soul_policy": {
                "mode": "preserve_not_mutate",
                "protected_paths_seen": protected_seen,
                "may_overwrite": False,
                "may_append_without_human_review": False,
            },
            "security_policy": {
                "secret_paths_seen": secret_seen,
                "human_at_write": True,
                "mcp_latest_allowed": False,
                "dependency_default": "zero",
            },
            "active_questions": [
                IST.Q_ZERO_DEPS,
                IST.Q_HALF_MEM,
                IST.Q_ELEGANT_ALGO,
                IST.Q_ARCHITECT_PURPOSE,
            ],
        }


def audit_default_surfaces() -> List[Decision]:
    """Convenience helper for examples and smoke tests."""

    adapter = HermesNEIAdapter()
    return [adapter.audit_surface(surface) for surface in default_surfaces()]


if __name__ == "__main__":
    adapter = HermesNEIAdapter()
    for surface, decision in zip(default_surfaces(), audit_default_surfaces()):
        status = "ALLOW" if decision.allow else "GATE"
        print(f"{status:5} tier={surface.tier} {surface.name} :: {decision.reason} {decision.flags}")
