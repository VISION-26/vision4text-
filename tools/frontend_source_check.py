#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend/src"
FAILURES: list[str] = []

IMPORT_RE = re.compile(r'''(?:from\s+|import\s*)["'](\.[^"']+)["']''')

def resolve_import(source: Path, ref: str) -> bool:
    base = source.parent / ref
    candidates = [
        base,
        base.with_suffix(".js"),
        base.with_suffix(".jsx"),
        base.with_suffix(".css"),
        base / "index.js",
        base / "index.jsx",
    ]
    return any(item.is_file() for item in candidates)

def delimiter_error(text: str) -> str | None:
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    opens = set(pairs.values())
    i = 0
    quote = None
    line_comment = False
    block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            i += 1
            continue
        if ch in opens:
            stack.append((ch, i))
        elif ch in pairs:
            if not stack or stack[-1][0] != pairs[ch]:
                return f"unexpected {ch} at offset {i}"
            stack.pop()
        i += 1
    if stack:
        return f"unclosed {stack[-1][0]} at offset {stack[-1][1]}"
    return None

files = sorted([*SRC.rglob("*.js"), *SRC.rglob("*.jsx")])
delimiter_targets = {
    "frontend/src/pages/Overview/Overview.jsx",
    "frontend/src/pages/Login/Login.jsx",
    "frontend/src/pages/Research/Research.jsx",
    "frontend/src/pages/MedicalResearch/MedicalResearch.jsx",
    "frontend/src/pages/About/About.jsx",
    "frontend/src/pages/Detection/Detection.jsx",
    "frontend/src/pages/Reports/Reports.jsx",
    "frontend/src/context/DetectionContext.jsx",
    "frontend/src/components/common/Input.jsx",
    "frontend/src/components/layout/Sidebar.jsx",
    "frontend/src/components/layout/ProtectedLayout.jsx",
    "frontend/src/routes/index.jsx",
}
for path in files:
    text = path.read_text(encoding="utf-8")
    rel = str(path.relative_to(ROOT)).replace("\\\\", "/")
    if rel in delimiter_targets:
        issue = delimiter_error(text)
        if issue:
            FAILURES.append(f"{path.relative_to(ROOT)}: {issue}")
    for ref in IMPORT_RE.findall(text):
        if not resolve_import(path, ref):
            FAILURES.append(f"{path.relative_to(ROOT)}: unresolved import {ref}")

if FAILURES:
    print("FRONTEND SOURCE CHECK: FAIL")
    for item in FAILURES:
        print(" -", item)
    sys.exit(1)

print("FRONTEND SOURCE CHECK: PASS")
print(f"JS/JSX files checked: {len(files)}")
