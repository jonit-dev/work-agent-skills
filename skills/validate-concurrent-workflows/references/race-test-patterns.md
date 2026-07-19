# Race Test Patterns

Use this matrix selectively. Each test must use independent database connections and assert durable final state.

## Two-producer race

Seed one eligible item. Hold both producers at a barrier, release them together, and assert:

- one durable work item exists for the exact source item;
- one charge exists with the exact item reference;
- one producer reports the win;
- the loser creates no work, ledger, audit, or source-state mutation;
- a unique constraint rejects any alternate path that bypasses the normal claim.

## Worker A/B lease fencing

1. Worker A claims generation `token-a`.
2. Advance database time beyond lease expiry without allowing A to finish.
3. Worker B claims `token-b`.
4. Attempt A heartbeat, completion, release, failure, charge, and refund.
5. Assert every A mutation affects zero rows and produces no external effect.
6. Let B finish and assert its token owns the final transition.

Repeat with a fresh lease and with a null/unknown lease timestamp. State the intended policy for each case.

## Crash-boundary matrix

Place failpoints around:

| Boundary | Required replay assertion |
| --- | --- |
| Before source claim commit | Item remains eligible; no charge/work exists |
| After claim, before charge/work commit | Atomic rollback or explicit recoverable claim exists |
| After durable work commit, before response | Replay returns existing identity without another charge |
| After claim, before external call | Lease expiry permits a fenced new owner |
| After external success, before DB acknowledgement | Delivery idempotency prevents a second external effect |
| After terminal state, before refund response | Refund unique key makes replay balance-neutral |

Prefer transaction-local failpoints for database boundaries and a fake idempotent adapter for external calls. Do not replace the database with mocks.

## Atomic claim assertions

For N simultaneous contenders, collect returned rows and owner tokens. Assert:

- exactly one non-empty result per item;
- no item appears twice across winners;
- claimed count never exceeds configured batch size;
- losing updates have affected-row count zero;
- later mutations require both item identity and owner token;
- query plans use the intended constraint/index when scale matters.

## Idempotent ledger assertions

Assert the database has unique keys for both original charge and reversal. Race at least 20 identical requests and verify one ledger row, exact balance delta, preserved subscription/purchased pool split, and stable replay result. Then race refund against retry/completion and prove only the valid terminal owner can reverse the original charge.

## Evidence hierarchy

From strongest to weakest:

1. Real database race with independent sessions and final-state assertions.
2. Integration test of the exact RPC/constraint under production-equivalent isolation.
3. Single-session database behavior test.
4. Unit test verifying client arguments and lost-claim branches.
5. Static inspection or mock that preselects a winner.

Use weaker evidence to localize failures, never to claim concurrency correctness.
