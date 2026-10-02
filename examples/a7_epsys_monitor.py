#!/usr/bin/env python3
"""A7 ε_system monitor — report-only JSON of the sovereignty term and related metrics.

This script outputs a JSON report with:
  - epsilon: total epsilon (ε_code + ε_system)
  - epsilon_soberano: the chosen residue (ε_system)
  - epsilon_ratio: ε_system / (ε_code + ε_system) [proportion of chosen residue in total epsilon]
  - trend: the trend verdict of the sovereignty term (from a8_epsilon_system_trend.py --trend)

Modes:
  --help: show help
  --selftest: run self tests
  (default): output the JSON report.

The script is read-only and does not modify state.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a6_epsilon_probe as probe  # noqa: E402  (single source of truth)

DIARY = os.environ.get("HERMES_DIARY", probe.DIARY)
TREND_SCRIPT = str(Path(__file__).resolve().parent / "a8_epsilon_system_trend.py")
SCHEMA = "a7-epsys-monitor/v1"

USAGE = (
    "usage: a7_epsys_monitor.py [--help | --selftest | --trend]\n"
    "  (default) sample the live ε_system and output JSON report\n"
    "  --help   print usage and exit 0\n"
    "  --selftest prove the fire/abstain/append logic; exits non-zero on failure\n"
    "  --trend  output the trend analysis JSON from a8_epsilon_system_trend.py\n"
)

KNOWN_FLAGS = ("--help", "--selftest", "--trend", "-h")


def arg_guide(args, err=sys.stderr, out=sys.stdout):
    """Up-front arg hygiene — an unrecognized flag must NEVER fall through to the
    default (append/sample) path.
    """
    unknown = [a for a in args if a not in KNOWN_FLAGS]
    if unknown:
        err.write("unknown flag(s): %s\n%s" % (" ".join(unknown), USAGE))
        return 2
    if "--help" in args or "-h" in args:
        out.write(USAGE)
        return 0
    return None


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sample_once(diary=DIARY):
    """Measure the live ε_system once and return the counts and computed values."""
    tally = probe.parse_dir(diary)
    eps_code, eps_system = probe.compute(tally)
    return {
        "typed": tally["typed_mutation"] + tally["typed_observe"],
        "untyped_ambiguous": tally["untyped_ambiguous"],
        "mislabels": tally["mislabels"],
        "honesty": tally["honesty"],
        "eps_code": eps_code,
        "eps_system": eps_system,
    }


def get_trend_verdict():
    """Run a8_epsilon_system_trend.py --trend and return the verdict string."""
    result = subprocess.run(
        [sys.executable, TREND_SCRIPT, "--trend"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        # If the trend script fails, we return an error verdict
        return "TREND_SCRIPT_FAILED"
    try:
        trend_data = json.loads(result.stdout.strip())
        return trend_data.get("verdict", "UNKNOWN")
    except (json.JSONDecodeError, KeyError):
        return "TREND_OUTPUT_INVALID"


def get_trend_json():
    """Run a8_epsilon_system_trend.py --trend and return the full JSON."""
    result = subprocess.run(
        [sys.executable, TREND_SCRIPT, "--trend"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        # If the trend script fails, return an error object
        return {
            "error": "TREND_SCRIPT_FAILED",
            "stderr": result.stderr,
        }
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {
            "error": "TREND_OUTPUT_INVALID",
            "output": result.stdout,
        }


def main():
    rc = arg_guide(sys.argv[1:])
    if rc is not None:
        sys.exit(rc)

    if "--selftest" in sys.argv:
        ok = _selftest()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    if "--trend" in sys.argv:
        trend_json = get_trend_json()
        print(json.dumps(trend_json, indent=2))
        sys.exit(0)

    # Default: sample and output JSON report
    data = sample_once()
    eps_code = data["eps_code"]
    eps_system = data["eps_system"]
    epsilon_total = eps_code + eps_system
    epsilon_soberano = eps_system
    epsilon_ratio = eps_system / epsilon_total if epsilon_total > 0 else 0.0
    trend_verdict = get_trend_verdict()

    report = {
        "schema": SCHEMA,
        "epsilon": round(epsilon_total, 6),
        "epsilon_soberano": round(epsilon_soberano, 6),
        "epsilon_ratio": round(epsilon_ratio, 6),
        "trend": trend_verdict,
    }
    print(json.dumps(report, indent=2))


def _selftest():
    ok = True

    def check(name, cond, note=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  selftest[{name:20s}] {'PASS' if cond else 'FAIL'}  {note}")

    # 1. single-source imports resolve
    for attr in ("parse_dir", "compute", "verdict"):
        check(f"import-{attr}", hasattr(probe, attr), "a6 probe exposes the measure")

    # 2. sample_once returns expected keys
    data = sample_once()
    expected_keys = {"typed", "untyped_ambiguous", "mislabels", "honesty", "eps_code", "eps_system"}
    check("sample-keys", set(data.keys()) == expected_keys, "all expected keys present")
    check("sample-values-non-negative",
          all(data[k] >= 0 for k in ("typed", "untyped_ambiguous", "mislabels", "honesty")),
          "counts non-negative")
    check("sample-eps-float", isinstance(data["eps_code"], float) and isinstance(data["eps_system"], float), "eps values are float")

    # 3. get_trend_verdict returns a string
    verdict = get_trend_verdict()
    check("trend-returns-string", isinstance(verdict, str), "get_trend_verdict returns a string")

    # 4. JSON report has expected keys and types
    data = sample_once()
    eps_code = data["eps_code"]
    eps_system = data["eps_system"]
    epsilon_total = eps_code + eps_system
    epsilon_soberano = eps_system
    epsilon_ratio = eps_system / epsilon_total if epsilon_total > 0 else 0.0
    trend_verdict = get_trend_verdict()
    report = {
        "schema": SCHEMA,
        "epsilon": round(epsilon_total, 6),
        "epsilon_soberano": round(epsilon_soberano, 6),
        "epsilon_ratio": round(epsilon_ratio, 6),
        "trend": trend_verdict,
    }
    expected_report_keys = {"schema", "epsilon", "epsilon_soberano", "epsilon_ratio", "trend"}
    check("report-keys", set(report.keys()) == expected_report_keys, "all expected report keys present")
    check("report-epsilon-float", isinstance(report["epsilon"], float), "epsilon is float")
    check("report-epsilon-soberano-float", isinstance(report["epsilon_soberano"], float), "epsilon_soberano is float")
    check("report-epsilon-ratio-float", isinstance(report["epsilon_ratio"], float), "epsilon_ratio is float")
    check("report-trend-string", isinstance(report["trend"], str), "trend is string")

    return ok


if __name__ == "__main__":
    main()