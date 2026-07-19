---
name: validate-prd-release-evidence
description: Validate PRD phases, production-readiness work, and release claims against acceptance criteria using evidence appropriate to each risk boundary. Use for PRD checkpoints, remediation reviews, go/no-go audits, release-readiness verification, or claims that implementation is complete and ready to ship.
---

# Validate PRD Release Evidence

Treat completion as unproven. Inspect the current worktree and relevant external state; do not infer completion from plans, green unit tests, or prior summaries.

## Build the validation map

1. Read the PRD, linked findings, rollout plan, and repository instructions.
2. Convert every phase, acceptance criterion, named artifact, invariant, checkpoint, and deploy gate into a checklist.
3. Draw the dependency order: schema before callers, producer before worker, claim before side effects, terminal state with reconciliation, deploy before staging, staging before soak.
4. Identify the authoritative evidence required for each item and the environment that can provide it.
5. Inspect `git status`, the full relevant diff, new/untracked files, migration order, generated files, and configuration drift before trusting test output.

## Match proof to the boundary

Use the narrowest fast check first, then increase realism:

1. Static inspection and focused unit tests.
2. Focused integration tests against real services, especially a fresh real database for SQL, constraints, transactions, concurrency, and migrations.
3. Full typecheck, lint, test, build, and repository verification.
4. Manual browser verification for interaction, rendering, timezone, accessibility, and user journeys.
5. Staging cron, queue, webhook, billing, and real CMS/provider exercises.
6. Production migration preflight/apply evidence, monitoring, rollback readiness, and soak results.

Never treat mocks as proof of database locking, transaction rollback, browser behavior, external CMS semantics, staging wiring, or production migration safety. A green fresh-chain migration does not prove an upgrade migration is safe on existing production data.

## Review adversarially

- Trace concurrency interleavings, ownership tokens, stale workers, retries, crash windows, and partial commits.
- Verify idempotency at the durable boundary with enforced keys or constraints, not only application checks.
- Confirm error paths check returned data as well as transport errors.
- Require reconciliation for paid or externally visible work that can fail between state transitions.
- Verify audit identities persist and connect producer, item, worker, outcome, and refund/delivery records.
- Check that tests exercise the current code and valid setup; inspect suspiciously strong evidence rather than repeating it.

Use independent reviewer passes when the user requests them or the governing workflow requires them. Give reviewers raw artifacts and bounded questions. Feed concrete findings into remediation, rerun the smallest proving test, then repeat the independent review. Do not let remediation redefine the original acceptance criterion.

## Preserve gates honestly

Keep these explicitly `PENDING` until direct evidence exists:

- Manual browser and end-to-end user verification.
- Staging cron/worker overlap, webhook, billing, and real CMS/provider verification.
- Production-data migration preflight and production apply.
- Post-deploy monitoring and soak windows.

Do not convert an unavailable external gate into PASS. Mark it `BLOCKED` only when completion cannot proceed because required authority, credentials, environment, or external state is unavailable; otherwise leave it `PENDING` with the next evidence-producing action.

## Report the checkpoint

For each criterion report:

- `PASS`: authoritative evidence directly proves it.
- `PENDING`: implementation may exist, but required manual, staging, production, or soak evidence is absent.
- `BLOCKED`: a named dependency prevents obtaining required evidence.

Include the criterion, status, evidence with file/line or command/result, remaining risk, and next gate. Separate implementation correctness from release readiness. End with an overall verdict that cannot be stronger than its required gates.

Before concluding, rerun `git status` and report unintended files or config changes. Never modify, discard, commit, deploy, or publish unrelated work while validating unless the user explicitly authorizes it.
