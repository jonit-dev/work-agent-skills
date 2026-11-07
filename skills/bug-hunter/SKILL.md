---
name: bug-hunter
description: Adversarial state-machine bug hunt. Finder, Skeptic and Arbiter rounds discover implicit state machines (status columns, flags, nulls, timestamps, queues, cron, webhooks, caches) and verify real bugs. Investigation only, no code changes. Use when the user says "bug hunt", "bug hunter", "hunt bugs", "state machine audit", "find race conditions", "adversarial review", or asks for a deep correctness sweep of a codebase and database. Same contract under Claude Code and Codex.
---

# Mission: Adversarial State Machine Bug Hunt

You are a team of adversarial software verification agents.

Your mission is to discover and verify as many real bugs as possible in the implicit state machines hidden throughout this database and codebase.

**DO NOT refactor, rewrite, redesign, or convert anything into actors. This is an investigation-only mission.**

## How to run it

- Run each role as a separate agent with fresh context: Finder, Skeptic, Arbiter. Claude Code: use the `Agent` tool. Codex: use its subagents, or run the roles in separate passes.
- Give the Skeptic and Arbiter the code and the Finder's claims. Do not give them the Finder's conclusions as fact.
- Write the report to a new `.md` file (for example `docs/operations/bug-hunt/<date>-<scope>.md`). Keep chat output to a short TLDR.
- Put ready-to-apply fixes in the report only. Another agent applies them.
- Scope: when the user names a subsystem, hunt there. Otherwise start with the highest-risk machines (money, inventory, trade, auth, queues, crons).
- Read-only database access only. Use isolated local copies for any reproduction.

## Phase 1 — Discover Implicit State Machines

Systematically inspect the entire accessible codebase and database, including:

- Tables, enums, status columns, timestamps, flags, and constraints
- Database triggers, functions, transactions, and stored procedures
- Backend services, workers, queues, cron jobs, and event handlers
- API endpoints, webhooks, retries, and asynchronous operations
- Frontend lifecycle logic and distributed state synchronization

Identify every implicit state machine, including those spread across multiple files, tables, or services.

Reconstruct its states, events, transitions, guards, invariants, side effects, and failure paths.

Do not limit yourself to explicit status fields. Look for state encoded through combinations of booleans, null values, timestamps, relationships, and external system responses.

## Phase 2 — Aggressive Bug Finder

For every discovered state machine, investigate:

- Illegal or missing state transitions
- Unreachable states and deadlocks
- Contradictory state combinations
- Missing authorization checks on transitions
- Race conditions and TOCTOU vulnerabilities
- Lost updates and transaction isolation failures
- Duplicate events and non-idempotent operations
- Retry and timeout inconsistencies
- Partial failures and incomplete compensation
- State corruption during concurrent operations
- Broken invariants and orphaned records
- State divergence between database, cache, and services
- Events arriving out of order
- Recovery failures following crashes or restarts

Scoring:

- Low impact: +1
- Medium impact: +5
- Critical impact: +10

Maximize discovery coverage. Report plausible bugs even when certainty is incomplete, but explicitly distinguish hypotheses from demonstrated defects.

Each finding must include:

1. Unique bug ID
2. Exact location and relevant code references
3. Affected state machine
4. Expected versus actual behavior
5. Triggering event sequence
6. Impact and severity
7. Evidence and reproducibility
8. Confidence level

## Phase 3 — Adversarial Bug Skeptic

You are an independent reviewer. Your goal is to DISPROVE the Bug Finder's claims.

For each reported bug:

1. Examine the actual implementation and related database constraints.
2. Construct the strongest possible counterargument.
3. Search for existing safeguards, guards, transactions, and validation.
4. Attempt to demonstrate that the alleged failure cannot occur.
5. Identify incorrect assumptions and missing preconditions.

Scoring:

- Correctly disprove: +original bug points
- Incorrectly dismiss: -2× original bug points

For each finding, report:

- Bug ID
- Counterargument
- Supporting evidence
- Confidence percentage
- Decision: DISPROVE / ACCEPT / UNCERTAIN
- Points gained or risked

Do not dismiss bugs merely because their reproduction is difficult.

## Phase 4 — Independent Arbiter

Evaluate the original report and the skeptic's challenge.

Do not assume either agent is correct.

For every disputed finding:

1. Independently inspect the relevant implementation.
2. Reconstruct the exact execution path.
3. Verify state invariants and transition preconditions.
4. Attempt reproduction using isolated tests where feasible.
5. Consider concurrency, failures, retries, and production execution conditions.
6. Identify whether the issue is demonstrated, disproven, or still uncertain.

Scoring:

- Correct judgment: +1
- Incorrect judgment: -1

Final verdicts:

- CONFIRMED BUG
- NOT A BUG
- UNVERIFIED — NEEDS MORE EVIDENCE

Never label a bug confirmed solely because two agents agree.

## Phase 5 — Coverage Expansion

After adjudication, inspect the discovered state-machine graph for unexplored transitions and failure paths.

Run additional Finder → Skeptic → Arbiter rounds targeting gaps.

Prioritize:

- High-impact state machines
- Transitions with external side effects
- Financial or destructive operations
- Concurrency-sensitive workflows
- Missing or weak test coverage

Stop when all accessible state machines and high-risk transition paths have been examined, or when further investigation is blocked by unavailable evidence.

## Final Deliverables

### State Machine Inventory
Every discovered state machine, its location, states, transitions, and risk level.

### Confirmed Bug Report
Rank confirmed bugs by severity, with exact evidence, reproduction steps, and affected state transitions.

### Unverified Findings
Separate plausible but unconfirmed defects, explaining what evidence is missing.

### Adversarial Scoreboard
Finder score, Skeptic score, Arbiter results, and false-positive statistics.

### Coverage Report
State machines examined, transitions checked, areas not covered, and remaining risks.

## Non-Negotiable Rules

- Do not modify production data.
- Do not change application code unless explicitly authorized.
- Run tests only in safe, isolated environments.
- No fabricated bugs, evidence, or reproduction results.
- Every confirmed issue must have a defensible technical explanation.
- Avoid duplicate reports describing the same underlying defect.
- Optimize for real bugs discovered, not merely the number of findings.

BEGIN. Discover the hidden state machines and attack every transition.
