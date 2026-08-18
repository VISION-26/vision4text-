#!/usr/bin/env python3
"""Project copy gate derived from petergyang/no-ai-slop.

It scans the authored explanatory surfaces that students, lecturers, and PDF
readers actually see. Technical identifiers and quoted research terminology are
left alone; the gate targets canned AI-writing patterns and banned filler.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGETS = sorted(
    [str(path.relative_to(ROOT)) for path in (ROOT / "frontend/src/pages").rglob("*.jsx")]
    + [str(path.relative_to(ROOT)) for path in (ROOT / "frontend/src/components").rglob("*.jsx")]
    + ["backend/app/services/report_service.py"]
)

BANNED_WORDS = [
    "delve", "foster", "leverage", "utilize", "facilitate", "empower",
    "streamline", "robust", "cutting-edge", "paradigm shift", "game changer",
    "this is huge", "this changes everything", "tapestry", "realm", "beacon",
    "multifaceted", "meticulous", "intricate", "paramount", "transformative",
    "elevate", "embark", "supercharge", "harness", "ever-evolving",
]

PATTERNS = {
    "throat-clearing": [
        r"\bhere(?:'|’)s the thing\b",
        r"\blet me be clear\b",
        r"\bi(?:'|’)ll be honest\b",
        r"\bthe uncomfortable truth is\b",
    ],
    "faux-insight": [
        r"\bwhat nobody tells you\b",
        r"\bthe part everyone misses\b",
        r"\bwhat most people get wrong\b",
    ],
    "importance-puffery": [
        r"\bstands as a testament\b",
        r"\bmarks a pivotal moment\b",
        r"\bplays a vital role\b",
        r"\bunderscores its significance\b",
    ],
    "weasel-attribution": [
        r"\bexperts agree\b",
        r"\bstudies show\b",
        r"\bindustry reports suggest\b",
        r"\bmany argue\b",
    ],
    "fake-profound-ending": [
        r"\bthe future isn(?:'|’)t coming\b",
        r"\bthe future is already here\b",
    ],
}

def audit() -> list[str]:
    findings: list[str] = []
    for rel in TARGETS:
        path = ROOT / rel
        if not path.is_file():
            findings.append(f"missing copy surface: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for word in BANNED_WORDS:
            if re.search(rf"(?<![a-z0-9_-]){re.escape(word)}(?![a-z0-9_-])", lower):
                findings.append(f"{rel}: banned filler '{word}'")
        for label, expressions in PATTERNS.items():
            for expression in expressions:
                if re.search(expression, lower):
                    findings.append(f"{rel}: {label}")
    return findings

if __name__ == "__main__":
    failures = audit()
    if failures:
        print("CONTENT QUALITY GATE: FAIL")
        for item in failures:
            print(" -", item)
        sys.exit(1)
    print("CONTENT QUALITY GATE: PASS")
    print(f"Audited copy surfaces: {len(TARGETS)}")
