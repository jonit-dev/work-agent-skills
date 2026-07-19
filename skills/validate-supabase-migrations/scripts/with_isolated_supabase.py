#!/usr/bin/env python3
"""Run a command against a temporary alternate-port local Supabase stack."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path


PORT_RE = re.compile(r"^(\s*(?:port|[A-Za-z0-9_]+_port)\s*=\s*)(\d+)(\s*(?:#.*)?)$", re.MULTILINE)
PROJECT_RE = re.compile(r'^(\s*project_id\s*=\s*)"([^"]+)"(\s*(?:#.*)?)$', re.MULTILINE)


def isolated_config(raw: bytes, offset: int) -> bytes:
    text = raw.decode("utf-8")

    def shift(match: re.Match[str]) -> str:
        return f"{match.group(1)}{int(match.group(2)) + offset}{match.group(3)}"

    text, port_count = PORT_RE.subn(shift, text)
    if port_count == 0:
        raise ValueError("No Supabase ports found in config.toml")
    text, project_count = PROJECT_RE.subn(
        lambda m: f'{m.group(1)}"{m.group(2)}-migration-validation-{offset}"{m.group(3)}',
        text,
        count=1,
    )
    if project_count != 1:
        raise ValueError("Expected exactly one project_id in config.toml")
    return text.encode("utf-8")


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=check, text=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--port-offset", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    root = args.project_root.resolve()
    config = root / "supabase" / "config.toml"
    original = config.read_bytes()
    original_hash = hashlib.sha256(original).hexdigest()
    rewritten = isolated_config(original, args.port_offset)

    if args.dry_run:
        if rewritten == original:
            raise RuntimeError("Dry run did not change config")
        print(f"config={config} original_sha256={original_hash} rewritten_ports=true")
        return 0
    if not command:
        parser.error("a command is required after --")

    start_attempted = False
    exit_code = 1
    try:
        config.write_bytes(rewritten)
        start_attempted = True
        run(["supabase", "start", "--workdir", str(root)], root)
        exit_code = run(command, root, check=False).returncode
    finally:
        if start_attempted:
            run(["supabase", "stop", "--no-backup", "--workdir", str(root)], root, check=False)
        config.write_bytes(original)
        restored_hash = hashlib.sha256(config.read_bytes()).hexdigest()
        if restored_hash != original_hash:
            print("ERROR: config.toml restoration hash mismatch", file=sys.stderr)
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
