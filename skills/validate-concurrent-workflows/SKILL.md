---
name: validate-concurrent-workflows
description: Validate database-backed concurrent producers, workers, claims, leases, billing, retries, and crash recovery. Use when reviewing or testing schedulers, queues, cron jobs, webhook consumers, payment or credit ledgers, idempotent APIs, stale-lock recovery, or any workflow whose correctness depends on overlapping executions, transaction boundaries, or exactly-once effects.
---

# Validate Concurrent Workflows

Prove invariants against the real database. Treat mock-only concurrency tests as branch tests, never as evidence that transactions, row locks, constraints, or isolation behave correctly.

## Establish the model

1. Name each durable state, owner token, lease timestamp, attempt counter, charge reference, and uniqueness key.
2. Write invariants before tests: one winner, bounded work, no duplicate effect, recoverable crash, fenced stale owner, and exact item-to-ledger identity.
3. Trace every state transition and external effect. Mark its transaction boundary and every crash window.
4. Read [race-test-patterns.md](references/race-test-patterns.md) when designing the test matrix or evaluating claim, lease, billing, and recovery semantics.

## Require authoritative evidence

- Run two or more producers/workers concurrently against a disposable real database using independent connections.
- Synchronize contenders at a barrier so they race on the same committed starting state. Do not merely launch promises whose database operations execute serially in one mock.
- Assert final database state, returned winners and losers, ledger rows, unique keys, and external calls. A successful response alone is weak evidence.
- Repeat races enough to expose timing sensitivity while keeping assertions deterministic.
- Verify the actual migration defining each RPC, constraint, trigger, or index. Do not infer production behavior from client code or an obsolete migration.

## Validate claims and fencing

- Make a claim a single conditional statement or transaction that returns the claimed row and an owner/run token.
- Assert exactly one contender wins and every loser performs zero downstream mutation, charge, refund, notification, or delivery.
- Require all owner mutations to include the current fencing token. Prove worker A cannot finish, renew, release, refund, or overwrite after worker B acquires an expired lease.
- Test fresh, stale, and unknown-age locks separately. Treat a null/missing lease timestamp as its own explicit policy, not automatically stale.
- Test heartbeat renewal immediately before and after expiry. Define boundary behavior precisely.

## Validate crashes and money

- Insert failpoints immediately before and after each transaction commit and before each external effect.
- Restart recovery from persisted state after every failpoint. Assert no item is lost, duplicated, permanently locked, or processed under the wrong identity.
- Tie charges and refunds to the exact item and original transaction reference. Enforce idempotency with a database unique constraint, not a prior read.
- Race duplicate charges, duplicate refunds, terminal failure, and recovery. Assert balances and pool splits remain exact and only the winning owner can create ledger effects.
- Prefer atomic producer transactions that claim the exact item, charge it, and create its durable work row together. If split, prove compensation and replay safety for every gap.

## Review tests skeptically

- Reject shared mock queues such as `[true, false]` as proof of atomicity; they encode the desired winner rather than testing the database.
- Assert exact item IDs. Counts can pass while the wrong row is charged, recovered, deleted, or refunded.
- Inspect error results from lock release and post-claim mutations. An awaited call whose error is ignored is not proven durable.
- Verify failed work remains in a state the recovery query actually selects.
- Check attempt counters across claim and failure handlers for double increments.
- Ensure audit correlation IDs survive in durable state across asynchronous boundaries; fire-and-forget logs are not a queue contract.

## Report

Lead with violated invariants, ordered by impact. For each finding include the race/crash sequence, current evidence, missing authoritative test, and the smallest invariant-preserving correction. Separate proven behavior from plausible code shape.
