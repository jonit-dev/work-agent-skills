---
name: skill-optimizer
description: Use when slimming an agent skill library.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, optimization, progressive-disclosure, context]
    related_skills: []
---

# Skill Optimizer

Optimize a skill library for accurate routing and low context cost without erasing operational knowledge.

Inspired by Eric Provencher's article, [Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/status/2095991462416490862), and hardened through use on a large real-world skill catalog.

## Core contract

1. Inventory the real library with `scripts/audit_skills.py`.
2. Fix routing metadata before rewriting bodies.
3. Treat overlap as a judgment call; never delete or merge skills automatically.
4. Move detail into support files only when a large root mixes independent workflows or rarely needed reference material.
5. Validate frontmatter, rerun the audit, and smoke-test discovery in a fresh session.

## What good looks like

- **Description:** a short trigger plus differentiator. Keep it under the runtime's index limit; 60 characters is a conservative default. Say *when to load*, not the full itinerary. Avoid “always,” “any time,” exhaustive synonym lists, and broad “pick me” language.
- **Root `SKILL.md`:** trigger, invariants, boundaries, execution order, verification, and pointers.
- **Support files:** provider details, long examples, transcripts, project-specific evidence, command catalogs, and independent sub-workflows.
- **Boundaries:** counter-triggers when neighboring skills could plausibly match the same request.

A short description is not automatically better. Preserve names, safety boundaries, irreversible-action approval gates, exact verification criteria, and unique triggers.

## Workflow

### 1. Audit

From this repository:

```bash
python skills/skill-optimizer/scripts/audit_skills.py /path/to/skills
```

Use `--json` for machine-readable output and `--include-hidden` only when archived skills matter. Override `--description-warn` or `--root-warn` for runtimes with different limits.

### 2. Triage in this order

1. Descriptions over the routing limit or containing aggressive routing language.
2. Semantically overlapping names or descriptions.
3. Large root files with no support files.
4. Multi-workflow roots that force irrelevant detail into context.
5. Stale instructions that newer models no longer need.

Do not optimize vendor or plugin-managed skills blindly. Determine ownership first; upstream-managed files may be overwritten by updates.

### 3. Edit narrowly

- Patch descriptions in batches while preserving the original trigger.
- For progressive disclosure, create a named support file and replace the moved section with a one-line pointer.
- Do not mass-rewrite bodies. Recipes protecting production, money, privacy, Git history, or external communication remain explicit.
- Do not weaken completion criteria merely because a newer model is more capable.

### 4. Verify

```bash
python skills/skill-optimizer/scripts/audit_skills.py /path/to/skills --json
```

Confirm:

- every `SKILL.md` parses;
- descriptions remain distinctive;
- warning counts and catalog characters decreased;
- support-file pointers resolve;
- no skill was deleted or silently broadened;
- a fresh agent session selects edited skills for positive triggers and rejects near-miss triggers.

## Stop conditions

Stop and ask before deleting, merging, archiving, or renaming skills because those actions can break references and scheduled workflows. After three failed routing smoke tests, name the disputed trigger boundary instead of repeatedly rewriting prompts.

## Reporting

Report before/after catalog characters, warning counts, files changed, unresolved overlaps, and the exact smoke-test result. Do not claim improved routing from character reduction alone.
