#!/usr/bin/env python3
"""Plugin identity drift watchdog — the ist-gate plugin's version across its FIVE surfaces.

The crate-identity disease (v0.8.23) applied one level up: ist-gate is a
Hermes-facing plugin whose *identity* is asserted in five places, and nothing
asserted they agreed. Found by a frontier scan on 2026-09-14, all five live
surfaces disagreed:

  1. plugin.yaml   version: "0.4.0"   (the manifest Hermes reads)
  2. SKILL.md      version: "0.4.1"   (the docs)
  3. identity.py   (did not exist — no code single source)
  4. gate_tools.py ist_gate_status()["version"] = "0.3.0"  (the tool surface —
     any agent querying its own constraint posture saw a pre-0.4.0 stamp)
  5. hooks.py      pulse "[ist-gate v0.3]" injected into EVERY LLM call
     (stale by two releases), while the written narrative (ist-runtime
     CHANGELOG v0.8.36) called the same build "ist-gate v0.5".

Same class as A5's silent-knob drift and the crate's Cargo.toml-vs-CHANGELOG
drift: each string is well-formed, the plugin loads fine, and the mismatch is
structurally invisible — the exact enforcement gap the Structural/Behavioral
Split thread names. The fix shape: a code SINGLE SOURCE (`identity.py`
VERSION) that the two runtime surfaces *derive* from, plus this instrument to
assert every surface — declared and rendered — against it.

Instrument contract (same discipline as crate_identity_check.py / A5 --check):

  main()        read-only diagnostic — always exit 0; prints every surface.
  --check       report-only watchdog — fail-closed (exit 1) when any two
                surfaces disagree (DRIFT) or a surface is missing/unparseable
                (UNVERIFIED — never assert alignment we cannot see). The exit
                code is a *reporting* mechanism for a cron, not a gate: this
                instrument never edits plugin.yaml / SKILL.md / any module.
  --selftest    deterministic, hermetic — fixture plugin dirs in tmp: aligned
                OK; each declared surface drifted → DRIFT; stale RENDERED
                literal (tool/pulse) → DRIFT; missing surface → UNVERIFIED.

Zero deps, stdlib only. Plugin dir defaults to the canonical
/mnt/hermes/plugins/ist-gate, override with $IST_GATE_PLUGIN_DIR.

Verdicts:
  OK         : all five surfaces parse and agree (semver-equal).
  DRIFT      : >=2 parsed surfaces disagree (names every surface + value).
  UNVERIFIED : a surface is missing/unparseable (fail-closed, never guessed).
exit 0 = main / --check aligned; 1 = --check DRIFT or UNVERIFIED / selftest FAIL.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_PLUGIN_DIR = "/mnt/hermes/plugins/ist-gate"

# semver subset the plugin uses: v<major>.<minor>.<patch>[ -suffix]
_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def parse_semver(raw: str | None):
    """Return a comparable (major, minor, patch) tuple, or None if unparseable."""
    if not raw:
        return None
    m = _SEMVER_RE.match(raw.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def plugin_yaml_version(d: Path) -> str | None:
    """Extract `version: "…"` from the plugin manifest."""
    f = d / "plugin.yaml"
    if not f.exists():
        return None
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'^version\s*:\s*"?([^"\s]+)"?\s*$', line.strip())
        if m:
            return m.group(1)
    return None


def skill_md_version(d: Path) -> str | None:
    """Extract `version:` from the SKILL.md YAML frontmatter (first block only)."""
    f = d / "SKILL.md"
    if not f.exists():
        return None
    in_fm = False
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s == "---":
            if in_fm:
                break  # end of frontmatter, no version found
            in_fm = True
            continue
        if in_fm:
            m = re.match(r'^version\s*:\s*"?([^"\s]+)"?\s*$', s)
            if m:
                return m.group(1)
    return None


def identity_py_version(d: Path) -> str | None:
    """Extract `VERSION = "…"` from identity.py (the code single source)."""
    f = d / "identity.py"
    if not f.exists():
        return None
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'^VERSION\s*=\s*["\']([^"\']+)["\']', line.strip())
        if m:
            return m.group(1)
    return None


_RENDER_CODE = (
    "import sys, json;"
    "sys.path.insert(0, sys.argv[1]);"
    "import gate_tools, hooks;"
    "st = gate_tools.ist_gate_status() or {};"
    "pl = hooks._on_pre_llm_call() or {};"
    "print(json.dumps({'status': st.get('version'), 'pulse': pl.get('context')}))"
)


def rendered_surfaces(d: Path) -> tuple[dict, str | None]:
    """Render the two runtime surfaces by importing the plugin in a subprocess.

    Returns ({'status': str|None, 'pulse': str|None}, error|None). Rendering —
    not trusting the literals — is the family discipline: the tool output and
    the per-call pulse are what agents/hooks actually SEE.
    """
    try:
        p = subprocess.run(
            [sys.executable, "-c", _RENDER_CODE, str(d)],
            capture_output=True, text=True, timeout=60,
        )
        if p.returncode != 0:
            err = (p.stderr or "").strip().splitlines()
            return {}, f"render import failed rc={p.returncode}: {err[-1] if err else '?'}"
        line = p.stdout.strip().splitlines()[-1]
        data = json.loads(line)
        return {"status": data.get("status"), "pulse": data.get("pulse")}, None
    except Exception as e:  # fail-closed boundary — never raise into the caller
        return {}, f"render failed: {type(e).__name__}: {e}"


def _pulse_version(pulse: str | None) -> str | None:
    """Pull the vX.Y.Z out of the per-call pulse line, e.g. '[ist-gate v0.5.0] …'."""
    if not pulse:
        return None
    m = re.search(r"\bv(\d+\.\d+\.\d+)\b", pulse)
    return m.group(1) if m else None


def collect(d: Path) -> tuple[dict, dict, list[str]]:
    """Gather all five surfaces. Returns (declared, rendered, problems)."""
    declared = {
        "plugin.yaml": plugin_yaml_version(d),
        "SKILL.md": skill_md_version(d),
        "identity.py": identity_py_version(d),
    }
    problems: list[str] = []
    if not d.is_dir():
        problems.append(f"plugin dir missing: {d}")
        return declared, {}, problems

    rendered_raw, err = rendered_surfaces(d)
    rendered = {
        "status(tool)": rendered_raw.get("status"),
        "pulse(hooks)": _pulse_version(rendered_raw.get("pulse")),
    }
    if err:
        problems.append(err)
    return declared, rendered, problems


def compare(d: Path) -> tuple[str, str, dict]:
    """Return (verdict, detail, surfaces)."""
    declared, rendered, problems = collect(d)
    surfaces = {**declared, **rendered}

    values: dict[str, tuple[int, int, int]] = {}
    unparsed: list[str] = []
    for name, raw in surfaces.items():
        sv = parse_semver(raw)
        if sv is None:
            unparsed.append(f"{name}={raw or '<missing>'}")
        else:
            values[name] = sv

    if len(set(values.values())) > 1:
        listing = ", ".join(
            f"{n}=v{v[0]}.{v[1]}.{v[2]}" for n, v in values.items()
        )
        detail = f"surfaces disagree — {listing}"
        if unparsed:
            detail += f"; also unreadable: {', '.join(unparsed)}"
        return "DRIFT", detail, surfaces

    if unparsed or problems:
        why = "; ".join(unparsed + problems) if (unparsed or problems) else ""
        return "UNVERIFIED", f"cannot confirm alignment — {why}", surfaces

    return "OK", (
        f"all 5 surfaces agree at v{next(iter(values.values()))[0]}."
        f"{next(iter(values.values()))[1]}.{next(iter(values.values()))[2]}"
    ), surfaces


def report(d: Path) -> str:
    verdict, detail, surfaces = compare(d)
    lines = [
        "=== plugin identity drift — ist-gate (5 surfaces) ===",
        f"dir          : {d}",
    ]
    for name in ("plugin.yaml", "SKILL.md", "identity.py",
                 "status(tool)", "pulse(hooks)"):
        val = surfaces.get(name)
        lines.append(f"{name:<13}: {val if val else '<missing>'}")
    lines.append(f"verdict      : {verdict}")
    lines.append(f"detail       : {detail}")
    return "\n".join(lines)


# --- selftest: hermetic fixture plugins, incl. render-tier stale literals ----
_FIX_GOOD = {
    "plugin.yaml": 'name: demo\nversion: "1.2.3"\ndescription: "fixture"\n',
    "SKILL.md": '---\nname: demo\ndescription: "fixture"\nversion: "1.2.3"\n---\n\n# demo\n',
    "identity.py": 'VERSION = "1.2.3"\n',
    "gate_tools.py": (
        "import identity\n"
        "def ist_gate_status(args=None):\n"
        "    return {'version': identity.VERSION}\n"
    ),
    "hooks.py": (
        "import identity\n"
        "def _on_pre_llm_call(**kw):\n"
        "    return {'context': f'[demo v{identity.VERSION}] ok'}\n"
    ),
}

_STALE_TOOL = (
    "def ist_gate_status(args=None):\n"
    "    return {'version': '9.9.9'}\n"
)
_STALE_PULSE = (
    "def _on_pre_llm_call(**kw):\n"
    "    return {'context': '[demo v9.9.9] ok'}\n"
)


def _fixture(td: str, name: str, **mutations: str | None) -> Path:
    d = Path(td) / name
    d.mkdir(parents=True, exist_ok=True)
    files: dict[str, str | None] = dict(_FIX_GOOD)
    files.update(mutations)
    for fn, content in files.items():
        if content is None:  # mutation deletes the surface
            continue
        (d / fn).write_text(content, encoding="utf-8")
    for fn in mutations:
        if mutations[fn] is None and (d / fn).exists():
            (d / fn).unlink()
    return d


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
    with tempfile.TemporaryDirectory() as td:
        # t1: aligned fixture → OK
        v, d, _ = compare(_fixture(td, "aligned"))
        sc.check(v == "OK", f"aligned must be OK, got {v} ({d})")

        # t2: manifest drifted → DRIFT naming plugin.yaml
        v, d, _ = compare(_fixture(
            td, "yaml-drift",
            **{"plugin.yaml": 'name: demo\nversion: "1.2.4"\ndescription: "x"\n'}))
        sc.check(v == "DRIFT", f"manifest drift must be DRIFT, got {v}")
        sc.check("plugin.yaml=v1.2.4" in d, f"detail names plugin.yaml, got {d}")

        # t3: docs drifted → DRIFT naming SKILL.md
        v, d, _ = compare(_fixture(
            td, "skill-drift",
            **{"SKILL.md": '---\nname: demo\nversion: "1.2.2"\n---\n# x\n'}))
        sc.check(v == "DRIFT", f"docs drift must be DRIFT, got {v}")
        sc.check("SKILL.md=v1.2.2" in d, f"detail names SKILL.md, got {d}")

        # t4: code single source drifted → DRIFT naming identity.py
        v, d, _ = compare(_fixture(
            td, "identity-drift", **{"identity.py": 'VERSION = "1.2.1"\n'}))
        sc.check(v == "DRIFT", f"identity drift must be DRIFT, got {v}")
        sc.check("identity.py=v1.2.1" in d, f"detail names identity.py, got {d}")

        # t5: RENDER-tier — declared all agree, tool surface renders stale literal
        v, d, _ = compare(_fixture(
            td, "stale-tool", **{"gate_tools.py": _STALE_TOOL}))
        sc.check(v == "DRIFT", f"stale rendered tool must be DRIFT, got {v}")
        sc.check("status(tool)=v9.9.9" in d, f"detail names status(tool), got {d}")

        # t6: RENDER-tier — pulse renders stale literal
        v, d, _ = compare(_fixture(
            td, "stale-pulse", **{"hooks.py": _STALE_PULSE}))
        sc.check(v == "DRIFT", f"stale rendered pulse must be DRIFT, got {v}")
        sc.check("pulse(hooks)=v9.9.9" in d, f"detail names pulse(hooks), got {d}")

        # t7: surface missing but others aligned → UNVERIFIED (never guessed)
        v, d, _ = compare(_fixture(td, "missing-skill", **{"SKILL.md": None}))
        sc.check(v == "UNVERIFIED", f"missing SKILL.md must be UNVERIFIED, got {v}")

        # t8: plugin dir missing → UNVERIFIED
        v, d, _ = compare(Path(td) / "no-such-dir")
        sc.check(v == "UNVERIFIED", f"missing dir must be UNVERIFIED, got {v}")

        # t9: garbage version string → UNVERIFIED
        v, d, _ = compare(_fixture(
            td, "garbage", **{"identity.py": 'VERSION = "banana"\n'}))
        sc.check(v == "UNVERIFIED", f"garbage identity must be UNVERIFIED, got {v}")

    print("  selftest[aligned     ] declared+rendered agree → OK")
    print("  selftest[drift-tiers ] yaml/skill/identity/tool/pulse each drift → DRIFT")
    print("  selftest[unverified  ] missing surface/dir, garbage → UNVERIFIED")
    print(f"SELFTEST: {'PASS' if sc.ok else 'FAIL'}")
    for m in sc._fails:
        print(f"  [check fail] {m}")
    return 0 if sc.ok else 1


def check(d: Path) -> int:
    """--check watchdog: one OK line + exit 0; DRIFT/UNVERIFIED + exit 1."""
    verdict, detail, _ = compare(d)
    if verdict == "OK":
        print(f"OK: plugin identity aligned — {detail}")
        return 0
    print(f"{verdict}: {detail} (fail-closed)")
    return 1


def main() -> int:
    """Read-only diagnostic: print the full report, always exit 0."""
    d = Path(os.environ.get("IST_GATE_PLUGIN_DIR", DEFAULT_PLUGIN_DIR))
    print(report(d))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--check" in sys.argv:
        sys.exit(check(Path(os.environ.get("IST_GATE_PLUGIN_DIR", DEFAULT_PLUGIN_DIR))))
    sys.exit(main())
