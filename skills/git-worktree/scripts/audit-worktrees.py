#!/usr/bin/env python3
"""Read-only worktree inventory; no status changes or cleanup."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

spec = importlib.util.spec_from_file_location("manager", Path(__file__).with_name("worktree-manager.py"))
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


def main():
    scan = Path(sys.argv[1] if len(sys.argv) > 1 else "/home").resolve()
    if not scan.is_dir():
        raise SystemExit(f"Not a directory: {scan}")
    roots, errors = set(), []
    skip = {"node_modules", "target", ".venv", "venv", ".cache", "__pycache__"}
    for directory, dirs, files in os.walk(scan, followlinks=False, onerror=lambda e: errors.append(str(e))):
        dirs[:] = [d for d in dirs if d not in skip]
        if ".git" in dirs or ".git" in files:
            if ".git" in dirs:
                dirs.remove(".git")
            try:
                rows = manager.records(directory)
                if rows and "bare" not in rows[0]:
                    roots.add(rows[0]["worktree"])
            except RuntimeError as e:
                errors.append(f"{directory}: {e}")
    found = {}
    for root in sorted(roots):
        try:
            rows = manager.records(root)
        except RuntimeError as e:
            errors.append(f"{root}: {e}")
            continue
        for row in rows[1:]:
            path = Path(row["worktree"]).resolve()
            owner = Path(root).resolve()
            local = any(path.is_relative_to(owner / suffix) for suffix in (".worktrees", ".claude/worktrees"))
            found[str(path)] = {**row, "primary": root, "placement": "local" if local else "MISPLACED"}
    for path, row in found.items():
        p = subprocess.run(["du", "-sx", "--block-size=1", "--", path], capture_output=True, text=True)
        try:
            row["bytes"] = int(p.stdout.split()[0])
        except (ValueError, IndexError):
            row["bytes"] = 0
        row["size_error"] = p.stderr.strip() if p.returncode else None
    rows = sorted(found.values(), key=lambda r: r["bytes"], reverse=True)
    total = sum(r["bytes"] for r in rows if not any(
        r["worktree"] != q["worktree"] and Path(r["worktree"]).is_relative_to(Path(q["worktree"])) for q in rows))
    print(json.dumps({"scan_root": str(scan), "repositories": len(roots), "worktrees": len(rows),
                      "misplaced": sum(r["placement"] == "MISPLACED" for r in rows),
                      "allocated_bytes_no_nested_double_count": total,
                      "note": "Allocated sizes are not guaranteed reclaimable bytes; shared extents may be counted repeatedly. Build/cache/dependency interiors skipped. No cleanup eligibility inferred.",
                      "errors": errors, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
