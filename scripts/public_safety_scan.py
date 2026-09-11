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
    # Unambiguous private identifiers: match regardless of case.
    "private_terms": re.compile(r"\b(SADA|Definya|WealthLens|personal-life|Xero|coldstartlabs)\b", re.I),
    # Words that are also ordinary English or common placeholder names. Matched
    # case-sensitively so "key insight" does not masquerade as the company
    # "Insight", and reviewed against BENIGN below so mockup personas do not
    # drown out real findings.
    "ambiguous_terms": re.compile(r"\b(Insight|Sarah|Thea)\b"),
}

# Known-benign occurrences: fictional personas in UI mockups and documentation
# headings. Each entry is (path suffix, matched value). Keep this list short and
# justify every addition in the PR that introduces it.
BENIGN = {
    ("skills/last30days/README.md", "Sarah"),          # mockup greeting copy
    ("skills/taste-skill/SKILL.md", "Sarah"),          # named as a banned generic persona
    ("skills/humanizer/SKILL.md", "Insight"),          # "Key Insight" callout heading
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
            rel = path.relative_to(ROOT).as_posix()
            if (rel, value) in BENIGN:
                continue
            line = text.count("\n", 0, m.start()) + 1
            hits.append((str(path.relative_to(ROOT)), line, name, value[:80]))

if hits:
    for file, line, kind, value in hits:
        print(f"{file}:{line}: {kind}: {value}")
    sys.exit(1)
print("public safety scan: PASS")
