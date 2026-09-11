#!/usr/bin/env python3
"""Integration checks use disposable repositories, never the user's projects."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

MANAGER = Path(__file__).with_name("worktree-manager.sh")
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="worktree-manager-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo with spaces"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Worktree Test")
        self.git("config", "core.excludesFile", "/dev/null")
        self.git("commit", "--allow-empty", "-m", "base")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args],
                              text=True, capture_output=True, check=True, env=ENV).stdout.strip()

    def manager(self, *args, cwd=None, ok=True):
        p = subprocess.run(["bash", str(MANAGER), *args], cwd=cwd or self.root,
                           capture_output=True, text=True, env=ENV)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0)
        return p

    def allow(self):
        (self.root / ".gitignore").write_text("/.worktrees/\n")

    def test_ignore_required_before_creation(self):
        self.manager("create", "feature", "main", ok=False)
        self.assertFalse((self.root / ".worktrees").exists())
        self.assertEqual(self.git("branch", "--list", "feature"), "")

    def test_nested_invocation_reuse_and_primary_preserved(self):
        self.allow()
        (self.root / "uncommitted").write_text("preserve")
        (self.root / ".env").write_text("test fixture only")
        first = Path(self.manager("create", "feat/one", "main").stdout.strip())
        second = Path(self.manager("create", "feat/two", "main", cwd=first).stdout.strip())
        self.assertEqual(second, self.root / ".worktrees" / "feat-two")
        self.assertEqual(self.manager("create", "feat/one", "main").stdout.strip(), str(first))
        self.assertEqual(len(json.loads(self.manager("list").stdout)), 3)
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual((self.root / "uncommitted").read_text(), "preserve")
        self.assertFalse((first / ".env").exists())
        self.manager("cleanup")
        self.assertTrue(first.is_dir())
        self.assertTrue(second.is_dir())

    def test_traversal_and_symlink_rejected(self):
        self.allow()
        self.manager("create", "feat/test", "main", "--slug", "../escape", ok=False)
        external = Path(self.tmp.name) / "external"
        external.mkdir()
        (self.root / ".worktrees").symlink_to(external)
        self.manager("create", "feat/test", "main", ok=False)
        self.assertEqual(list(external.iterdir()), [])

    def test_misplaced_branch_does_not_duplicate(self):
        self.allow()
        misplaced = self.root / "legacy"
        self.git("worktree", "add", "-b", "legacy", str(misplaced), "main")
        self.manager("create", "legacy", "main", ok=False)
        self.assertFalse((self.root / ".worktrees" / "legacy").exists())
        self.assertEqual(self.manager("path", "legacy").stdout.strip(), str(misplaced))

    def test_name_collision_and_bad_base(self):
        self.allow()
        self.manager("create", "feat/one", "main")
        self.manager("create", "feat-one", "main", ok=False)
        self.manager("create", "another", "missing-ref", ok=False)
        self.assertEqual(len(json.loads(self.manager("list").stdout)), 2)


if __name__ == "__main__":
    unittest.main()
