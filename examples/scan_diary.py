#!/usr/bin/env python3
"""Companion scan: inspect the diary format across days to design the
A3-diary harness faithfully. Stdlib only (doutrina zero-deps).

Reads every 2026-<date>.md in the diary dir, classifies lines, and prints
a per-file histogram of the line-taxonomy so the harness's parser targets
real formats instead of assumptions.
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

DIARY = os.environ.get("HERMES_DIARY", "/mnt/hermes/diary")


def classify(line: str) -> str:
    s = line.lstrip()
    if s.startswith("!Sd/on"):
        return "SESS_START"
    if s.startswith("!Sd/off"):
        return "SESS_END"
    if re.match(r"^!S[dt]/", s):
        return "SD_OTHER"
    if s.startswith("!Lm:"):
        return "MODEL"
    if s.startswith("!Dc:"):
        return "DECISION_NOTE"
    if s.startswith("⊗Er:"):
        return "ERROR_MARK"
    if s.startswith("!Dm/") or s.startswith("!Dm:"):
        return "DECISION_META"
    if re.match(r"^>[A-Za-z_]+", s):       # >T:...
        return "TOOL_LINE"
    if s.startswith("# "):
        return "HEADER"
    if s.startswith("!") or s.startswith("#"):
        return "OTHER_CONTROL"
    return "CONTENT"


def main() -> None:
    files = sorted(f for f in os.listdir(DIARY) if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", f))
    if not files:
        files = sorted(f for f in os.listdir(DIARY) if f.endswith(".md") and "WEEKLY" not in f)
    for fname in files:
        path = os.path.join(DIARY, fname)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError as e:
            print(f"{fname}: ERR {e}")
            continue
        c = Counter(classify(ln) for ln in lines)
        n = len(lines)
        hist = " ".join(f"{k}={v}" for k, v in sorted(c.items()))
        print(f"{fname:16} lines={n:5}  {hist}")


if __name__ == "__main__":
    main()