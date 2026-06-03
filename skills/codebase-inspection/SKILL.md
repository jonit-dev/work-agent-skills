---
name: codebase-inspection
description: "Inspect codebases w/ pygount: LOC, languages, ratios."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LOC, Code Analysis, pygount, Codebase, Metrics, Repository]
    related_skills: [github-repo-management]
prerequisites:
  commands: [pygount]
---

# Codebase Inspection with pygount

Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios using `pygount`.

## When to Use

- User asks for LOC (lines of code) count
- User wants a language breakdown of a repo
- User asks about codebase size or composition
- User wants code-vs-comment ratios
- General "how big is this repo" questions
- User asks “what’s next”, “where are we”, “what’s missing”, or “is this ready” for a code project; do a project-status inspection, not just LOC

## Prerequisites

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

## 1. Basic Summary (Most Common)

Get a full language breakdown with file counts, code lines, and comment lines:

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**IMPORTANT:** Always use `--folders-to-skip` to exclude dependency/build directories, otherwise pygount will crawl them and take a very long time or hang.

## 1A. Project Status / “What’s Next?” Review

When the user asks what should be done next in a repository, inspect durable project signals before answering:

1. Locate the repo if the name is approximate: search likely project roots and session history for aliases.
2. Read project instructions (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`) before making judgments.
3. Read roadmap/status sources first: `ROADMAP*`, `docs/**roadmap**`, `docs/PRDs/README.md`, `docs/PRDs/done/**`, audit reports, release checklists, TODO docs.
4. Check live repo state: `git status --short`, recent commits, and latest changed docs/files.
5. Inspect `package.json`/Makefile/scripts to identify real verification commands.
6. Run the lightest meaningful gate when feasible (`yarn verify`, `yarn test:unit`, worker tests, etc.) and report exact pass/fail output. If dependencies are missing, install per lockfile and retry once rather than guessing.
7. Separate: immediate blocker, next validation gate, operational/deploy tasks, and polish/branding tasks.
8. Do not over-index on stale audit reports. Compare them against latest commits and current files before saying issues remain open.

Support reference: `references/project-status-review-example-saas.md` captures a concrete ExampleSaaS/portfolio-manager example and checklist.

## 1B. Product Value / Production-Value Review

When the user asks whether a product “adds value,” “solves a problem,” “has bloat,” or needs a 0–100 value/readiness score, do not answer only from engineering completeness. Produce a product-value assessment grounded in repo evidence:

1. Read product docs first: `docs/product-requirements.md`, outcome docs, roadmap, PRDs, UX/product audits, pricing/legal/help pages if present.
2. Inspect current app surfaces and recent commits so stale reports are not repeated as live truth.
3. Score with a clear **0–100 value score** and separate production verdict.
4. Evaluate dimensions such as problem importance, target-user clarity, time to value, core loop completeness, differentiation, trust/comprehension, feature discipline, and monetization readiness.
5. Identify the product wedge in one sentence, then list what is genuinely valuable vs what currently feels like bloat.
6. Define production readiness as an end-user loop, not just test pass/fail. For portfolio/finance products, a good loop is: data entry/import → trustworthy snapshot → drift/data-quality diagnosis → cited review → ordered action list.
7. Recommend the next build order around the smallest loop that creates user value. Prefer prune/harden/sample-data validation before adding modules.
8. Save the report under `docs/` when useful and mention the path plus concise TLDR.

Support reference: `references/product-value-review-example-saas.md` captures a concrete product-value scorecard and report structure.

## 2. Common Folder Exclusions

Adjust based on the project type:

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

## 3. Filter by Specific Language

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

## 4. Detailed File-by-File Output

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines (pipe through sort)
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

## 5. Output Formats

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .

# Pipe-friendly: Language, file count, code, docs, empty, string
pygount --format=summary . 2>/dev/null
```

## 6. Interpreting Results

The summary table columns:
- **Language** — detected programming language
- **Files** — number of files of that language
- **Code** — lines of actual code (executable/declarative)
- **Comment** — lines that are comments or documentation
- **%** — percentage of total

Special pseudo-languages:
- `__empty__` — empty files
- `__binary__` — binary files (images, compiled, etc.)
- `__generated__` — auto-generated files (detected heuristically)
- `__duplicate__` — files with identical content
- `__unknown__` — unrecognized file types

## Pitfalls

1. **Always exclude .git, node_modules, venv** — without `--folders-to-skip`, pygount will crawl everything and may take minutes or hang on large dependency trees.
2. **Markdown shows 0 code lines** — pygount classifies all Markdown content as comments, not code. This is expected behavior.
3. **JSON files show low code counts** — pygount may count JSON lines conservatively. For accurate JSON line counts, use `wc -l` directly.
4. **Large monorepos** — for very large repos, consider using `--suffix` to target specific languages rather than scanning everything.
