#!/usr/bin/env python3
"""Smoke example for the Hermes IST adapter."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from framework.hermes_nei_adapter import HermesAction, HermesNEIAdapter, audit_default_surfaces


def main() -> None:
    adapter = HermesNEIAdapter()

    print("== Surface audit ==")
    for decision in audit_default_surfaces():
        status = "ALLOW" if decision.allow else "GATE"
        print(f"{status:5} audit={decision.audit_score:.2f} nei={decision.nei_score:.6f} {decision.flags}")

    print("\n== SOUL preservation gate ==")
    proposed = HermesAction(
        action="overwrite",
        target_path="SOUL.md",
        human_approved=False,
        architect_purpose="Preserve the sovereign context while adding Hermes integration.",
    )
    print(adapter.audit_action(proposed))

    print("\n== Compact context packet ==")
    packet = adapter.compile_context_packet(
        task="Import ECC Tier 1/2 capabilities into Hermes through IST constraints.",
        active_paths=["SOUL.md", "framework/hermes_nei_adapter.py", ".env"],
    )
    for key, value in packet.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
