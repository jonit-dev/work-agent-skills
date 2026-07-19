---
name: validate-durable-outbox-delivery
description: Validate durable transactional outbox and multi-destination delivery implementations for enqueue atomicity, leases, retries, crash recovery, concurrency, manual retry, and defensible idempotency claims. Use for code reviews, PRD checkpoints, incident remediation, or release audits involving notifications, webhooks, email, CMS publishing, queues, or other externally delivered side effects.
---

# Validate Durable Outbox Delivery

Treat delivery guarantees as unproven. Trace persisted state and transaction boundaries before reading happy-path service code.

## Model the state machine

Identify:

- Source transaction and deterministic event key.
- Parent outbox state, availability time, lease owner, and lease expiry.
- Per-destination rows and their pending, processing, delivered, failed, and retry fields.
- Retry-cycle identity and terminal/manual-retry states.
- External request idempotency keys or provider receipts.

Draw transitions for enqueue, claim, send, record success, partial failure, worker crash, lease expiry, automatic retry, manual retry, and completion. Require every transition to have an owner predicate and a durable recovery path.

## Validate enqueue and drain

Require deterministic enqueue in the same database transaction as the source state change. Prove duplicate enqueue attempts converge on one logical event without overwriting delivered destination state.

Require the drain to be bounded and independently scheduled. It must select available outbox work even when the original source row is no longer due, visible, or in its former status. Reject designs whose only drain path re-queries the source eligibility condition.

For each claimed parent:

1. Claim with one atomic conditional mutation and a unique lease token.
2. Create or load per-destination rows deterministically.
3. Send only unfinished destinations for the current retry cycle.
4. Never resend a delivered destination during sibling retry.
5. Mark the parent complete only when destination outcomes satisfy the documented policy.

## Attack concurrency and crashes

Exercise real database concurrency where possible:

- Multiple drainers race for one parent; exactly one current lease owner proceeds.
- The old owner cannot heartbeat, finalize, or release after lease takeover.
- A crash after parent claim but before destination claim becomes recoverable after expiry.
- A crash after external success but before local success recording follows the documented duplicate-risk strategy.
- Expired `processing` parents and destination rows return to retryable state without resetting delivered siblings.
- Retry cycle N cannot mutate, satisfy, or suppress cycle N+1.

Use transaction isolation, constraints, conditional updates, and returned rows as evidence. Unit mocks cannot prove these interleavings.

## Validate manual retry

Prove authorization and ownership at the database/API boundary. Permit retry only for documented terminal/retryable states and never for already-complete work. Reset only fields needed for a new retry cycle, increment or replace the cycle identity, preserve prior delivery history, and keep already-delivered destinations ineligible for resend.

Test concurrent manual retries and manual-versus-automatic drain races. Require one accepted retry cycle and deterministic responses for losers.

## Calibrate delivery claims

Distinguish these guarantees explicitly:

- **Application-level idempotency:** deterministic keys, unique constraints, leases, and destination state prevent duplicate application sends in tested paths.
- **Provider-level idempotency:** the external provider accepts and enforces the supplied key.
- **Exactly-once external effect:** generally impossible to prove when a process can crash after the provider acts but before local acknowledgement, unless the provider offers a queryable, durable idempotency contract.

Do not call an HTTP/email/CMS side effect mathematically exactly-once merely because one database row or one mocked fetch exists. Report the residual ambiguity window and mitigation.

## Demand appropriate evidence

Use focused unit tests first, then real database tests for enqueue rollback, uniqueness, leases, expiry, cycle isolation, and concurrent drainers. Use provider sandbox or staging tests for external idempotency behavior. Preserve production migration, real-provider, and soak gates as pending until direct evidence exists.

Report each invariant as `PASS`, `PENDING`, or `BLOCKED`, with file/line or command/result evidence, the strongest guarantee actually proven, residual duplicate/loss risk, and the next evidence-producing action. Inspect `git status` and unintended configuration drift before the final verdict.
