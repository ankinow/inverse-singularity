#!/usr/bin/env python3
"""Crate identity drift watchdog — Cargo.toml version vs CHANGELOG head (ist-runtime).

Guards the failure mode the v0.8.15 entry fixed *by hand* and then watched
silently recur: `Cargo.toml` (and `Cargo.lock`) sit one release identity while
`CHANGELOG.md` marches ahead, release after release. The v0.8.15 alignment
bumped the crate 0.7.0 → 0.8.14 to match the CHANGELOG lineage, but the fix was
a one-time manual edit with no instrument behind it — so the drift recurred
(crate stayed at 0.8.14 while CHANGELOG advanced v0.8.15 … v0.8.22, eight
releases behind by 2026-09-13).

This is the same disease class as A5's silent-knob drift, applied to the
crate's *own identity*: two version strings in the repo that must stay equal
(`Cargo.toml#version` and the `CHANGELOG.md` head `## vX.Y.Z`) but drift apart
because the release step bumps one and not the other, and nothing asserts the
pair. No compiler error: `version = "0.8.14"` is a well-formed Cargo field.
The drift is *semantically valid and structurally invisible* — the exact
enforcement gap the Structural/Behavioral Split thread names.

Instrument contract (same discipline as the A5 `--check` watchdog):

  main()        read-only diagnostic — always exit 0; reports whether the two
                identities agree or how far apart they are.
  --check       report-only watchdog — fail-closed (exit 1, `DRIFT` line) when
                the two identities disagree; silent (exit 0) when aligned. The
                exit code is a *reporting* mechanism for a cron, not a gate —
                this instrument never edits Cargo.toml/Cargo.lock/CHANGELOG.
  --selftest    deterministic, no-repo — proves the parse + compare against
                synthetic fixtures (aligned / drifted by N / malformed).

Zero deps. Stdlib only. Reads relative to the repo root (its own grandparent).

Verdicts:
  OK       : Cargo.toml#version == CHANGELOG head (both parse; semver-equal).
  DRIFT    : both parse but differ (names the gap: crate X vs changelog Y).
  UNVERIFIED: either side unparseable / file missing (never guessed).
exit 0 = self-check PASS (main / --check aligned), 1 = self-check FAIL / drift.
"""

from __future__ import annotations

import pathlib
import re
import sys

# Repo root = grandparent of this file (examples/crate_identity_check.py).
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CARGO_TOML = REPO_ROOT / "Cargo.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# semver subset this crate uses: v<major>.<minor>.<patch>[ -suffix]
_SEMVER_RE = re.compile(
    r"^(?:v?)(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$"
)


def parse_semver(raw: str):
    """Return a comparable (major, minor, patch, raw) tuple, or None if unparseable."""
    m = _SEMVER_RE.match(raw.strip().lstrip("v"))
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), raw.strip())


def cargo_version() -> str | None:
    """Extract the first `version = "…"` line of Cargo.toml's [package] table."""
    if not CARGO_TOML.exists():
        return None
    in_package = False
    for line in CARGO_TOML.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s.startswith("["):
            in_package = (s == "[package]")
            continue
        if in_package:
            m = re.match(r'^version\s*=\s*"([^"]+)"', s)
            if m:
                return m.group(1)
    return None


def changelog_head_version() -> str | None:
    """Extract the first `## vX.Y.Z` heading of CHANGELOG.md."""
    if not CHANGELOG.exists():
        return None
    for line in CHANGELOG.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^##\s+v(\d+\.\d+\.\d+)", line.strip())
        if m:
            return m.group(1)
    return None


def compare(cargo: str | None, changelog: str | None) -> tuple[str, str]:
    """Return (verdict, detail)."""
    cv = parse_semver(cargo) if cargo else None
    cl = parse_semver(changelog) if changelog else None
    if cv is None or cl is None:
        return "UNVERIFIED", (
            f"crate={cargo or '<missing>'}, changelog={changelog or '<missing>'}"
        )
    if cv[:3] == cl[:3]:
        return "OK", f"crate == changelog == v{cv[0]}.{cv[1]}.{cv[2]}"
    return "DRIFT", (
        f"crate v{cv[0]}.{cv[1]}.{cv[2]} vs changelog v{cl[0]}.{cl[1]}.{cl[2]}"
        f" (gap {cl[0]*1000000 + cl[1]*1000 + cl[2] - (cv[0]*1000000 + cv[1]*1000 + cv[2])} releases)"
    )


def report() -> str:
    cargo = cargo_version()
    changelog = changelog_head_version()
    verdict, detail = compare(cargo, changelog)
    lines = [
        "=== crate identity drift — Cargo.toml vs CHANGELOG ===",
        f"cargo_toml   : {cargo or '<missing>'}", 
        f"changelog    : v{changelog or '<missing>'} (head)",
        f"verdict      : {verdict}",
        f"detail       : {detail}",
    ]
    return "\n".join(lines)


class SelfCheck:
    def __init__(self) -> None:
        self._fails: list[str] = []

    def check(self, cond: bool, msg: str) -> None:
        if not cond:
            self._fails.append(msg)

    @property
    def ok(self) -> bool:
        return not self._fails


def selftest() -> int:
    sc = SelfCheck()

    # aligned
    v, d = compare("0.8.22", "0.8.22")
    sc.check(v == "OK", f"aligned must be OK, got {v} ({d})")
    # drifted (crate behind)
    v, d = compare("0.8.14", "0.8.22")
    sc.check(v == "DRIFT", f"crate-behind must be DRIFT, got {v} ({d})")
    sc.check("gap 8" in d, f"gap must be 8 in detail, got {d}")
    # drifted (changelog behind — the symmetric direction)
    v, d = compare("0.8.22", "0.8.14")
    sc.check(v == "DRIFT", f"changelog-behind must be DRIFT, got {v}")
    # leading v tolerated
    v, d = compare("v0.8.22", "0.8.22")
    sc.check(v == "OK", f"leading-v must be OK, got {v}")
    # unparseable → UNVERIFIED
    v, d = compare("0.8", "0.8.22")
    sc.check(v == "UNVERIFIED", f"short-version must be UNVERIFIED, got {v}")
    v, d = compare(None, "0.8.22")
    sc.check(v == "UNVERIFIED", f"missing cargo must be UNVERIFIED, got {v}")
    v, d = compare("0.8.22", None)
    sc.check(v == "UNVERIFIED", f"missing changelog must be UNVERIFIED, got {v}")
    v, d = compare("banana", "0.8.22")
    sc.check(v == "UNVERIFIED", f"garbage must be UNVERIFIED, got {v}")

    print("  selftest[aligned   ] 0.8.22==0.8.22 → OK, v-prefix tolerated")
    print("  selftest[drift     ] 0.8.14 vs 0.8.22 → DRIFT (gap 8), symmetric")
    print("  selftest[unverifd  ] short/missing/garbage → UNVERIFIED")
    print(f"SELFTEST: {'PASS' if sc.ok else 'FAIL'}")
    for m in sc._fails:
        print(f"  [check fail] {m}")
    return 0 if sc.ok else 1


def check() -> int:
    """--check watchdog: silent OK, fail-loud DRIFT (exit 1)."""
    cargo = cargo_version()
    changelog = changelog_head_version()
    verdict, detail = compare(cargo, changelog)
    print(report())
    if verdict == "DRIFT":
        print(f"DRIFT: {detail} (fail-closed)")
        return 1
    if verdict == "UNVERIFIED":
        # a missing/unparseable side is a signal we cannot confirm alignment —
        # fail-closed rather than silently pass (never assert OK we can't see)
        print(f"DRIFT: UNVERIFIED — {detail} (fail-closed, cannot confirm alignment)")
        return 1
    print("DRIFT: none (crate identity aligned with CHANGELOG head)")
    return 0


def main() -> int:
    """Read-only diagnostic: print the report, always exit 0."""
    print(report())
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--check" in sys.argv:
        sys.exit(check())
    sys.exit(main())