#!/usr/bin/env python3
"""Small filesystem harness for the wikiskill-evolution meta-skill.

This tool manages evidence and audit history. Knowledge synthesis and skill
proposal remain agent tasks because they require semantic judgment.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

WS = ".wikiskill"


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:limit].rstrip("-") or "trace")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def workspace(root: Path) -> Path:
    return root.resolve() / WS


def ensure_initialized(root: Path) -> Path:
    ws = workspace(root)
    required = [
        ws / "raw",
        ws / "wiki" / "patterns",
        ws / "wiki" / "index.md",
        ws / "wiki" / "log.md",
        ws / "wiki" / "skill-impact.md",
        ws / "raw-manifest.jsonl",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit(
            "WikiSkill workspace is not initialized. Run `wikiskill.py init --root <repo>`.\n"
            + "Missing:\n- "
            + "\n- ".join(missing)
        )
    return ws


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root)
    ws = workspace(root)
    (ws / "raw").mkdir(parents=True, exist_ok=True)
    (ws / "wiki" / "patterns").mkdir(parents=True, exist_ok=True)
    (ws / "candidates").mkdir(parents=True, exist_ok=True)

    write_if_missing(ws / "raw-manifest.jsonl", "")
    write_if_missing(
        ws / "wiki" / "index.md",
        "# Pattern index\n\nNo durable patterns recorded yet.\n",
    )
    write_if_missing(
        ws / "wiki" / "log.md",
        "# Evolution log\n\nChronological summaries of WikiSkill maintenance cycles.\n",
    )
    write_if_missing(
        ws / "wiki" / "skill-impact.md",
        "# Skill impact history\n\nAccepted and rejected skill proposals are recorded here.\n",
    )
    print(f"Initialized {ws}")
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    root = Path(args.root)
    ws = ensure_initialized(root)

    trace_id = args.id or f"{utc_stamp()}-{slugify(args.task)}"
    if not re.fullmatch(r"[A-Za-z0-9._-]+", trace_id):
        raise SystemExit("--id may contain only letters, numbers, dot, underscore, and hyphen")

    path = ws / "raw" / f"{trace_id}.md"
    if path.exists():
        raise SystemExit(f"Refusing to overwrite immutable raw trace: {path}")

    evidence_chunks: list[str] = []
    for item in args.evidence or []:
        source = Path(item)
        if not source.exists() or not source.is_file():
            raise SystemExit(f"Evidence file does not exist: {source}")
        text = source.read_text(encoding="utf-8", errors="replace")
        evidence_chunks.append(f"### {source}\n\n```text\n{text}\n```\n")

    tags = ", ".join(args.tags or []) or "none"
    skills = ", ".join(args.skills or []) or "none"
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    body = [
        f"# Trace {trace_id}",
        "",
        f"Captured: {now}",
        f"Outcome: {args.outcome}",
        f"Tags: {tags}",
        f"Active skills: {skills}",
        "",
        "## Task",
        args.task.strip(),
        "",
        "## Observable outcome",
        args.summary.strip(),
        "",
        "## Evidence",
    ]
    if evidence_chunks:
        body.append("\n".join(evidence_chunks).rstrip())
    else:
        body.append("No external evidence file attached. Add a new trace rather than editing this record if more evidence appears later.")
    body.append("")
    path.write_text("\n".join(body), encoding="utf-8")

    rel = path.relative_to(ws).as_posix()
    entry = {
        "id": trace_id,
        "path": rel,
        "sha256": sha256(path),
        "captured": now,
        "outcome": args.outcome,
    }
    with (ws / "raw-manifest.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    print(path)
    return 0


def cmd_impact(args: argparse.Namespace) -> int:
    root = Path(args.root)
    ws = ensure_initialized(root)
    diff = ""
    if args.diff_file:
        p = Path(args.diff_file)
        if not p.exists() or not p.is_file():
            raise SystemExit(f"Diff file does not exist: {p}")
        diff = p.read_text(encoding="utf-8", errors="replace").rstrip()

    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    patterns = ", ".join(args.patterns or []) or "none"
    notes = args.notes.strip() if args.notes else "none"
    validation = args.validation.strip() if args.validation else "not specified"

    entry = [
        "",
        f"## {args.iteration} — {args.skill}",
        "",
        f"Recorded: {timestamp}",
        f"Decision: {args.decision}",
        f"Baseline: {args.baseline}",
        f"Candidate: {args.candidate}",
        f"Patterns: {patterns}",
        "",
        "### Validation",
        validation,
        "",
        "### Change",
    ]
    if diff:
        entry += ["```diff", diff, "```"]
    else:
        entry.append("No diff attached.")
    entry += ["", "### Notes", notes, ""]

    with (ws / "wiki" / "skill-impact.md").open("a", encoding="utf-8") as f:
        f.write("\n".join(entry))
    print(f"Recorded {args.decision} impact for {args.skill}")
    return 0


def read_manifest(ws: Path) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    manifest = ws / "raw-manifest.jsonl"
    for lineno, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"manifest line {lineno}: invalid JSON ({e})")
            continue
        records.append(record)
    return records, errors


def validate_workspace(root: Path) -> list[str]:
    ws = ensure_initialized(root)
    errors: list[str] = []
    records, manifest_errors = read_manifest(ws)
    errors.extend(manifest_errors)

    tracked: set[str] = set()
    for rec in records:
        rel = rec.get("path")
        expected = rec.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            errors.append(f"manifest record missing path/sha256: {rec!r}")
            continue
        tracked.add(rel)
        p = ws / rel
        if not p.exists():
            errors.append(f"tracked raw trace missing: {rel}")
            continue
        actual = sha256(p)
        if actual != expected:
            errors.append(f"immutable raw trace modified: {rel}")

    for p in sorted((ws / "raw").glob("*.md")):
        rel = p.relative_to(ws).as_posix()
        if rel not in tracked:
            errors.append(f"untracked raw trace: {rel}; capture traces through wikiskill.py")

    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_workspace(Path(args.root))
    if errors:
        print("WikiSkill validation FAILED", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print("WikiSkill validation OK")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.root)
    ws = ensure_initialized(root)
    traces = list((ws / "raw").glob("*.md"))
    patterns = list((ws / "wiki" / "patterns").glob("*.md"))
    impact_text = (ws / "wiki" / "skill-impact.md").read_text(encoding="utf-8")
    accepted = len(re.findall(r"^Decision:\s*accepted\s*$", impact_text, flags=re.M | re.I))
    rejected = len(re.findall(r"^Decision:\s*rejected\s*$", impact_text, flags=re.M | re.I))
    print(json.dumps({
        "workspace": str(ws),
        "raw_traces": len(traces),
        "patterns": len(patterns),
        "accepted_skill_changes": accepted,
        "rejected_skill_changes": rejected,
    }, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filesystem harness for wikiskill-evolution")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="initialize .wikiskill workspace")
    p.add_argument("--root", default=".")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("capture", help="capture an immutable observable execution trace")
    p.add_argument("--root", default=".")
    p.add_argument("--task", required=True)
    p.add_argument("--outcome", choices=["pass", "fail", "partial"], required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--evidence", action="append", help="text/log file to embed; repeatable")
    p.add_argument("--tags", action="append")
    p.add_argument("--skills", action="append")
    p.add_argument("--id")
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("impact", help="append an accepted/rejected skill proposal result")
    p.add_argument("--root", default=".")
    p.add_argument("--iteration", required=True)
    p.add_argument("--skill", required=True)
    p.add_argument("--decision", choices=["accepted", "rejected"], required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--validation")
    p.add_argument("--patterns", action="append")
    p.add_argument("--diff-file")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_impact)

    p = sub.add_parser("validate", help="validate workspace structure and raw immutability")
    p.add_argument("--root", default=".")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("status", help="show workspace counts")
    p.add_argument("--root", default=".")
    p.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
