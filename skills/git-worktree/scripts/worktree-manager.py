#!/usr/bin/env python3
"""Create and discover project-local worktrees without changing the primary."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def git(path, *args, check=True):
    p = subprocess.run(["git", "-C", str(path), *args], text=True,
                       capture_output=True, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p


def records(path):
    result = []
    for block in git(path, "worktree", "list", "--porcelain", "-z").stdout.split("\0\0"):
        row = {}
        for field in block.split("\0"):
            if field:
                key, _, value = field.partition(" ")
                row[key] = value
        if "worktree" in row:
            result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("list", "ls", "cleanup", "clean"):
        sub.add_parser(name)
    for name in ("create", "path", "switch", "go"):
        p = sub.add_parser(name)
        p.add_argument("branch")
        p.add_argument("--slug")
        if name == "create":
            p.add_argument("base", help="Explicit ref or fetched SHA")
    args = parser.parse_args()
    rows = records(Path.cwd())
    if not rows or "bare" in rows[0]:
        raise RuntimeError("A non-bare primary checkout is required.")
    root = Path(rows[0]["worktree"]).resolve()
    if not root.is_dir():
        raise RuntimeError(f"Primary checkout is missing: {root}")
    if args.cmd in ("list", "ls", "cleanup", "clean"):
        print(json.dumps(rows, indent=2))
        if args.cmd in ("cleanup", "clean"):
            print("Report only. Follow the skill's required post-merge cleanup checks.", file=sys.stderr)
        return
    git(root, "check-ref-format", "--branch", args.branch)
    slug = args.slug or args.branch.replace("/", "-")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", slug) or ".." in slug:
        raise RuntimeError("Use a single task slug; traversal and nested paths are forbidden.")
    path = root / ".worktrees" / slug
    if path.resolve() != path or (root / ".worktrees").is_symlink():
        raise RuntimeError("Worktree placement may not follow a symlink.")
    matches = [r for r in rows if r.get("branch") == "refs/heads/" + args.branch]
    if matches:
        existing = Path(matches[0]["worktree"]).resolve()
        if args.cmd == "create":
            if existing != path:
                raise RuntimeError(f"Branch is already at {existing}; inspect/reuse it instead of making another copy.")
            if "locked" in matches[0] or "prunable" in matches[0] or not existing.is_dir():
                raise RuntimeError("Existing registration is locked or missing; inspect before reuse.")
            print("Existing checkout; verify ownership and state before editing.", file=sys.stderr)
        print(existing)
        return
    if args.cmd != "create":
        raise RuntimeError("Branch has no registered worktree.")
    if path.exists():
        raise RuntimeError(f"Unregistered path exists: {path}; inspect instead of overwriting.")
    base = git(root, "rev-parse", "--verify", "--end-of-options", args.base + "^{commit}").stdout.strip()
    if git(root, "show-ref", "--verify", "--quiet", "refs/heads/" + args.branch, check=False).returncode == 0:
        raise RuntimeError("Existing branch: inspect and attach deliberately, do not invent another task name.")
    probe = str(path / ".placement-check")
    if git(root, "check-ignore", "-q", "--", probe, check=False).returncode:
        raise RuntimeError(f"Add /.worktrees/ to {root}/.gitignore, then rerun. Ignore must exist BEFORE creation.")
    git(root, "worktree", "add", "-b", args.branch, str(path), base)
    print(path)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
