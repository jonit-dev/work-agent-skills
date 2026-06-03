#!/usr/bin/env python3
"""Conservative public-safety scan for accidental personal/private content.

This is not a substitute for human review. It flags likely secrets, local paths,
personal names, private project names, and employer/evidence terms that should
not appear in this public skill pack.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOW = {
    "GITHUB_TOKEN",  # generic environment variable name in GitHub skills
}
PATTERNS = {
    "github_pat_or_ghp": re.compile(r"\b(ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "openai_style_key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private_key": re.compile(r"-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "local_home_path": re.compile(r"/home/joao\b|/Users/joao\b", re.I),
    "personal_phone": re.compile(r"\b778\D{0,3}846\D{0,3}7427\b"),
    "private_terms": re.compile(r"\b(SADA|Insight|Definya|WealthLens|personal-life|Xero|Sarah|Thea|coldstartlabs)\b", re.I),
}

hits = []
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    if path.relative_to(ROOT).as_posix() == "scripts/public_safety_scan.py":
        continue
    text = path.read_text(errors="ignore")
    for name, pat in PATTERNS.items():
        for m in pat.finditer(text):
            value = m.group(0)
            if value in ALLOW:
                continue
            line = text.count("\n", 0, m.start()) + 1
            hits.append((str(path.relative_to(ROOT)), line, name, value[:80]))

if hits:
    for file, line, kind, value in hits:
        print(f"{file}:{line}: {kind}: {value}")
    sys.exit(1)
print("public safety scan: PASS")
