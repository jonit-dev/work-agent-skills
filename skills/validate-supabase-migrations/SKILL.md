---
name: validate-supabase-migrations
description: Validate Supabase/Postgres migration chains safely and reproducibly. Use when reviewing pending migrations, proving a fresh migration chain, testing upgrade/backfill behavior or legacy NULL data, checking PostgREST schema-cache RPC usability, or separating local automated evidence from production deployment evidence without assuming production database access.
---

# Validate Supabase Migrations

## Establish scope

1. Inspect `git status`, migration filenames, and diffs. Treat the repository and any explicitly supplied remote migration history as evidence; never imply production access.
2. Identify whether migrations are committed, untracked, backdated before an already-applied version, or edits to historically applied files. Flag forward-deployment risk separately from fresh-chain validity.
3. Record invariants to prove: objects, signatures, privileges, RLS, constraints, indexes, backfills, concurrency, and RPC behavior.

## Run an isolated fresh chain

Use `scripts/with_isolated_supabase.py` from the repository root. It temporarily offsets every Supabase port and changes `project_id`, starts a separate stack, runs a command, always stops the stack, and restores `supabase/config.toml` byte-for-byte.

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/validate-supabase-migrations/scripts/with_isolated_supabase.py" \
  --project-root "$PWD" --port-offset 100 -- \
  supabase db reset --workdir "$PWD"
```

Choose an unused offset. Do not reuse or stop the developer's normal stack. If Docker or the CLI is unavailable, report the missing evidence instead of substituting production.

## Verify beyond successful apply

Query the isolated database directly and through the API where relevant.

- Inspect `pg_proc`, `pg_get_functiondef`, `pg_indexes`, `pg_constraint`, `information_schema`, grants, and `pg_policies`.
- Call changed RPCs through Supabase/PostgREST, not only SQL, to catch overload and schema-cache issues.
- Assert positive and negative cases, affected-row counts, rollback, idempotency, ownership fencing, and concurrent winners.
- Seed conservative legacy fixtures before applying a forward migration when testing upgrades: duplicate rows, NULL foreign keys/timestamps/statuses, partial historical descriptions, and already-completed records. Never invent pool splits or ownership when history is ambiguous.
- Confirm backfills preserve audit/accounting rows and that new unique indexes can be built on realistic legacy data.

For upgrade-only behavior, apply the historical prefix, seed fixtures, then apply only the pending suffix. A fresh reset cannot prove an already-deployed upgrade.

## Preserve cleanup integrity

Before running, hash `supabase/config.toml`. Afterward, verify the hash and project `git status`. Treat cleanup failure as a failed validation. The wrapper restores config even when start, migration, assertions, or interruption fails.

## Report evidence precisely

Separate results into:

- **Automated local evidence:** fresh-chain output, SQL assertions, API/RPC calls, concurrency tests, and cleanup hashes.
- **Not proven locally:** production migration history, production row shape/volume, locks and runtime duration, deployed schema cache, secrets, and actual rollout success.
- **Deployment requirements:** forward-only migration order, backup/rollback plan, production preflight queries, lock-safe index rollout, and post-deploy checks.

Never convert “fresh local chain passed” into “safe in production” without upgrade-path and production-state evidence.
