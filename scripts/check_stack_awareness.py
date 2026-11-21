#!/usr/bin/env python3
"""Health check for the four-seat stack-awareness pack. Local, read-only."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED = [
    "docs/STACK_MANIFEST.md",
    "docs/FOUR_PROGRAM_AWARENESS.md",
    ".cursor/rules/stack-awareness.mdc",
    "docs/stack-paste/grok-custom-instructions.md",
    "docs/stack-paste/grokbot-starter-prompt.md",
    "docs/stack-paste/cursor-opener.md",
    "docs/stack-paste/x-seat-note.md",
]
SEATS = ["Cursor", "Grok Bot", "Grok", "X"]
GATES = ["NO-GO", "PremiumPlus", "permanent"]
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{10,}|Bearer\s+[A-Za-z0-9._-]{10,}|BEGIN [A-Z ]*PRIVATE KEY)")

failures = []
for rel in REQUIRED:
    path = ROOT / rel
    if not path.is_file():
        failures.append(f"missing: {rel}")

manifest = ROOT / "docs/STACK_MANIFEST.md"
if manifest.is_file():
    text = manifest.read_text(encoding="utf-8")
    for seat in SEATS:
        if seat not in text:
            failures.append(f"manifest missing seat: {seat}")
    for gate in GATES:
        if gate not in text:
            failures.append(f"manifest missing marker: {gate}")
    for path in [ROOT / r for r in REQUIRED if (ROOT / r).is_file()]:
        if SECRET_RE.search(path.read_text(encoding="utf-8")):
            failures.append(f"secret-shaped string in: {path.relative_to(ROOT)}")

if failures:
    print("STACK AWARENESS: FAIL")
    for failure in failures:
        print(f" - {failure}")
    sys.exit(1)
print("STACK AWARENESS: OK — manifest, Cursor rule, and 4 paste packs present; all seats + gates named; no secret-shaped strings.")
