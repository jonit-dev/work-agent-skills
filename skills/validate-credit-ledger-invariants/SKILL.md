---
name: validate-credit-ledger-invariants
description: Validate paid-credit charging, allocation, clawback, and refund workflows in Postgres/Supabase. Use when auditing credit conservation by pool, subscription eligibility, transactional creation and rollback, mixed-pool provenance, exactly-once terminal refunds, unique ledger keys, or concurrent charge/refund and subscription-status races.
---

# Validate Credit Ledger Invariants

## Define the accounting contract

Name every pool explicitly. For subscription (`S`) and purchased (`P`) credits, prove each operation with equations rather than total-balance intuition.

For a charge of `A = As + Ap`:

```text
S_after = S_before - As
P_after = P_before - Ap
usage_ledger.amount = -A
allocation.subscription_amount = As
allocation.purchased_amount = Ap
```

For its refund:

```text
S_final = S_after + As = S_before
P_final = P_after + Ap = P_before
refund_ledger.amount = A
refund references the original allocation/charge exactly once
```

Across a history, reconcile each pool independently:

```text
ending pool = opening pool + grants - charges + refunds - expirations - clawbacks
```

Never accept total-credit conservation when value moved between expiring subscription and durable purchased pools.

## Inspect the transaction boundary

Trace every credit-deducting entry point, including single creation, batch creation, planned promotion, retries, and administrative paths.

1. Lock the owner profile row with `FOR UPDATE` before reading eligibility, status, or balances.
2. Read subscription status and both balances in that locked statement.
3. Permit subscription credits only for the documented statuses, commonly `active` and `trialing`.
4. For canceled, past-due, unpaid, or NULL status, require purchased credits to cover the full charge and set `As = 0`.
5. Keep business-row creation/promotion, balance mutation, usage ledger insertion, and allocation insertion in one database transaction.
6. Return stable error codes and prove failure leaves every table unchanged.

Check lock order across functions to avoid deadlocks. A concurrent status update must serialize on the same profile row; test both possible winners.

## Preserve allocation provenance

Require one explicit allocation per charged business item and charge transaction. Assert:

- positive amount and nonnegative pool components;
- `subscription_amount + purchased_amount = amount`;
- charge transaction belongs to the same user and is negative usage;
- total allocations never exceed the batch charge;
- refund transaction is positive and linked once;
- deletion cannot erase accounting evidence while ledger history remains.

Do not infer a mixed split from current balances. For legacy data, parse only authoritative recorded splits; quarantine ambiguous rows for reconciliation.

## Prove rollback and exact refund

For each injected failure point—eligibility, business insert, balance update, ledger insert, allocation insert, or terminal state update—assert together:

- no unintended business row/status change;
- no allocation row;
- no usage/refund ledger row;
- both pool balances unchanged.

Terminal failure must lock the article/allocation, restore the original pool split, insert a deterministic unique refund key, mark the allocation refunded, and commit the terminal business state atomically. If refund proof is missing, roll back the terminal state instead of guessing.

## Run the status matrix

Test every deduction entry point with:

- active and trialing using subscription-first allocation;
- canceled and past-due with enough purchased credits, using purchased only;
- canceled, past-due, unpaid, and NULL with mixed total but insufficient purchased credits, producing the stable inactive/insufficient-purchased error;
- insufficient total for active/trialing;
- concurrent cancellation versus deduction.

Inspect allocation rows, not only returned balances.

## Run concurrency proofs

Use a real Postgres database, not mocks, for races.

- Launch 20 simultaneous charges for the same exact claim: require one winner, one business row, one usage transaction, one allocation, and one balance decrement.
- Launch 20 simultaneous terminal refunds: require one success, one refund ledger row, one allocation transition, one terminal state, and exact restoration of both pools.
- Race status cancellation with deduction: the serialized outcome must either charge under the earlier committed eligible state or reject under the inactive state; never consume subscription credits after observing inactivity.
- Repeat idempotency calls after commit and after a forced rollback.

Use unique constraints as the final boundary, but also lock and return affected rows. Treat zero affected rows as a lost claim, not success.

## Verify the whole state vector

After every case, query and compare in one report:

1. business row and status;
2. charge allocation rows and pool split;
3. usage/refund ledger rows, references, signs, and uniqueness;
4. subscription and purchased balances;
5. batch/item audit rows and charged/refunded counters.

Report automated local evidence separately from production evidence. A fresh migration reset and passing race test do not prove deployed migration history, legacy production splits, production volume, or rollout safety.
