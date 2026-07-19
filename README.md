# Work Agent Skills

Reusable, job-safe agent skills for product planning, PRD creation/execution, code review, debugging, testing, GitHub workflows, and QA.

This repository is intentionally public-safe:

- no personal notebooks
- no private project names or production hostnames
- no credentials or tokens
- no employer-specific evidence/logging material

## Contents

### PRD / planning

- `skills/prd-creator/` — create implementation-ready PRDs with complexity scoring, integration points, phases, and verification plans.
- `skills/prd-executor/` — execute PRDs by decomposing phases into dependency-aware tasks and parallel workstreams.
- `skills/writing-plans/` — write practical implementation plans for software changes.
- `skills/github-issue-prd-sync/` — keep GitHub issues and PRDs aligned.

### Engineering execution

- `skills/systematic-debugging/` — root-cause debugging workflow.
- `skills/test-driven-development/` — RED/GREEN/REFACTOR workflow.
- `skills/spike/` — time-boxed experiments before committing to a build.
- `skills/requesting-code-review/` — pre-commit review and quality gates.
- `skills/system-documenter/` — architecture cartography and living system documentation.
- `skills/dogfood/` — exploratory QA of web applications.
- `skills/local-self-verification/` — evidence-based local verification before handoff.
- `skills/forecasting-experiments/` — design and evaluate forecasting experiments.
- `skills/stripe-debugging/` — safely diagnose Stripe integration incidents without exposing secrets.

### Reliability / release validation

- `skills/validate-concurrent-workflows/` — verify claims, leases, fencing, and concurrency recovery.
- `skills/validate-credit-ledger-invariants/` — test credit-ledger integrity and race conditions.
- `skills/validate-durable-outbox-delivery/` — prove durable event delivery and idempotency behavior.
- `skills/validate-prd-release-evidence/` — assess PRD completion and release-readiness evidence.
- `skills/validate-supabase-migrations/` — safely validate fresh and upgrade migration chains.
- `skills/validate-timezone-scheduling/` — test timezone and DST-sensitive scheduling flows.

### Distribution / artifacts

- `skills/print-ready-docx/` — generate and verify print-ready DOCX artifacts.
- `skills/refresh-distribution-proof/` — rebuild distribution evidence with provenance and secret-safety checks.
- `skills/verify-android-webview-responsive-input/` — verify Android WebView layout and pointer input against the installed APK.

### GitHub / codebase workflow

- `skills/github-issues/`
- `skills/github-pr-workflow/`
- `skills/github-code-review/`
- `skills/codebase-inspection/`

## How to use

Copy the skill folder you need into your agent's skills directory, or reference the `SKILL.md` content directly in your agent/session.

Each skill is plain Markdown with YAML frontmatter.

## Public-safety note

These files were copied or adapted from local workflows and then scanned for personal/sensitive markers before publishing. Project-bound global skills and any skill that fails the scan stay out of this repository. If you add new skills, run `scripts/public_safety_scan.py` before pushing.
