---
name: wikiskill-evolution
description: Use when repeated agent executions, recurring coding mistakes, successful workflows, or prior rejected skill changes should become durable project knowledge or reusable agent skills across sessions.
---

# WikiSkill Evolution

## Overview

Convert repeated agent experience into durable knowledge, then distill only validated procedures into executable skills. Keep **raw evidence**, **wiki knowledge**, and **active skills** separate.

## Core invariants

- Raw traces are immutable. Store observable evidence, never hidden chain-of-thought.
- The task-solving agent uses active skills, not `.wikiskill/wiki`, as a runtime crutch.
- Wiki knowledge persists even when a candidate skill is rejected.
- Change one skill at a time. Prefer a small patch over a rewrite.
- A skill contains procedure; the wiki contains incidents, evidence, alternatives, and history.

## Workflow

1. **Initialize**: run `python <this-skill>/scripts/wikiskill.py init --root <repo>`.
2. **Generate evidence**: execute representative tasks with the current active skills. Do not expose the private wiki to the task-solving run.
3. **Capture**: record pass/fail outcomes plus commands, tool outputs, test results, errors, and relevant diffs with `wikiskill.py capture`.
4. **Consolidate**: sample at most 8 useful traces, biased toward failures (up to 5 failures + 3 successes). Compare successes with failures. Create or patch concise pattern pages using `templates/pattern.md`; update `wiki/index.md` and `wiki/log.md`.
5. **Propose**: read `wiki/skill-impact.md` first, then relevant patterns and normally at least 4 traces. Avoid previously rejected approaches unless new evidence changes the premise. Create or patch exactly one skill and maintain its `PURPOSE.md` provenance.
6. **Gate**: evaluate the candidate on held-out tasks, regression tests, CI, benchmarks, or another objective metric. Accept only when it improves the target behavior without regressions; otherwise rollback the skill.
7. **Record impact**: append the candidate diff, metric, and accepted/rejected decision. Never rollback the wiki.

If fewer than 4 traces exist, normally keep the lesson in the wiki only. A narrow skill patch is allowed when a deterministic regression test reproduces the issue and proves the reusable rule; mark the wiki pattern provisional.

If no credible validation gate exists, do not promote the candidate to an active skill.

## Wiki quality

Patterns must explain the recurring behavior, root cause, evidence, actionable fix, and boundaries. Merge duplicates. Mark stale knowledge superseded instead of erasing history.

Keep active skills concise and model-agnostic where possible; record model-specific workarounds as such.

For the full operating contract, use `references/architecture.md`. For maintainer/proposer roles, use the prompt files in `prompts/`.
