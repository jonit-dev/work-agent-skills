from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
CLI = SKILL_ROOT / "scripts" / "wikiskill.py"


def run(*args: str, cwd: Path | None = None, check: bool = True):
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {proc.args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


class WikiSkillCliTests(unittest.TestCase):
    def test_init_creates_three_layer_workspace_scaffold(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run("init", "--root", str(root))
            self.assertTrue((root / ".wikiskill" / "raw").is_dir())
            self.assertTrue((root / ".wikiskill" / "wiki" / "patterns").is_dir())
            self.assertTrue((root / ".wikiskill" / "wiki" / "index.md").is_file())
            self.assertTrue((root / ".wikiskill" / "wiki" / "skill-impact.md").is_file())

    def test_capture_is_manifested_and_validate_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run("init", "--root", str(root))
            out = run(
                "capture", "--root", str(root),
                "--id", "trace-1",
                "--task", "repair parser",
                "--outcome", "fail",
                "--summary", "parser rejected valid input",
            )
            trace = Path(out.stdout.strip())
            self.assertTrue(trace.exists())
            manifest = (root / ".wikiskill" / "raw-manifest.jsonl").read_text().strip()
            rec = json.loads(manifest)
            self.assertEqual(rec["path"], "raw/trace-1.md")
            self.assertEqual(run("validate", "--root", str(root)).returncode, 0)

    def test_validate_detects_raw_trace_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run("init", "--root", str(root))
            run(
                "capture", "--root", str(root),
                "--id", "trace-1",
                "--task", "repair parser",
                "--outcome", "fail",
                "--summary", "parser rejected valid input",
            )
            trace = root / ".wikiskill" / "raw" / "trace-1.md"
            trace.write_text(trace.read_text() + "\nretroactive edit\n")
            proc = run("validate", "--root", str(root), check=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("immutable raw trace modified", proc.stderr)

    def test_capture_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run("init", "--root", str(root))
            common = [
                "capture", "--root", str(root), "--id", "trace-1",
                "--task", "task", "--outcome", "pass", "--summary", "done",
            ]
            run(*common)
            proc = run(*common, check=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Refusing to overwrite", proc.stderr)

    def test_impact_records_rejection_for_future_proposers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run("init", "--root", str(root))
            run(
                "impact", "--root", str(root), "--iteration", "3",
                "--skill", "debugging-api", "--decision", "rejected",
                "--baseline", "8/10", "--candidate", "6/10",
                "--validation", "held-out replay",
                "--notes", "regressed two passing cases",
            )
            text = (root / ".wikiskill" / "wiki" / "skill-impact.md").read_text()
            self.assertIn("Decision: rejected", text)
            self.assertIn("regressed two passing cases", text)
            status = json.loads(run("status", "--root", str(root)).stdout)
            self.assertEqual(status["rejected_skill_changes"], 1)


class SkillPackageTests(unittest.TestCase):
    def test_skill_frontmatter_and_size(self):
        text = (SKILL_ROOT / "SKILL.md").read_text()
        self.assertTrue(text.startswith("---\nname: wikiskill-evolution\n"))
        self.assertIn("description: Use when", text)
        self.assertLessEqual(len(text.split()), 500)

    def test_required_supporting_files_exist(self):
        expected = [
            "PURPOSE.md",
            "README.md",
            "references/architecture.md",
            "templates/pattern.md",
            "templates/skill-purpose.md",
            "templates/impact-entry.md",
            "prompts/wiki-maintainer.md",
            "prompts/skill-proposer.md",
            "AGENTS_SNIPPET.md",
        ]
        for rel in expected:
            self.assertTrue((SKILL_ROOT / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()
