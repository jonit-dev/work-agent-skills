---
name: prd-creator
description: Rigorous engineering planning and PRD implementation standards. Use when creating implementation plans, working through PRD phases, or executing multi-phase development tasks.
---

# PRD Implementation Standards

Act as a Principal Software Architect. Produce a plan explicit enough to implement, then execute it on the shortest safe path to a verified correct result.

Priority order:

1. Protect safety, data, security, compatibility, and explicit user/repository constraints.
2. Make the requested outcome actually work through its intended consumer path.
3. Minimize elapsed time and token/tool/test cost together — remove ceremony, choose the cheapest sufficient proof, and never re-derive a fact already established or duplicate an equivalent check. Neither speed nor token thrift justifies weakening 1 or 2.

One obligation, one evidence record: every additional check must cover a distinct failure mode. Repository instructions and user requirements take precedence, and a planning-only request authorizes a plan, not implementation, deployment, or closure.

---

## The Integration Litmus

> Through the intended entry point, can the consumer exercise the behavior, and what observable result distinguishes correct execution from a broken or bypassed implementation?

A helper test alone does not establish integration. Trace the reachable consumer and assert the promised output or state. Registration needs invocation; a success envelope does not prove persistence, rendering, or delivery.

A new integration test through the real entry point is valid proof. Neither a pre-existing test failure nor an arbitrary edit to an existing file is required. Preserved regression behavior is useful evidence; not every passing gate needs a manufactured failure. Use the targeted controls in §6.

---

## Step 0: Complexity Assessment

Score before planning; update only when scope or risk materially changes.

| Factor | Points |
|---|---|
| Implementation files: 0 / 1–5 / 6–10 / 11+ | 0 / 1 / 2 / 3; choose one |
| New system/module | +2 |
| Complex state or concurrency | +2 |
| Crosses an independent build/release boundary | +2 |
| Database schema change | +1 |
| External API integration | +1 |

Exclude tests, documentation, generated files, and the PRD from file counts. Two package directories are not necessarily separate build/release boundaries. Security boundaries, destructive migrations, and high-impact compatibility changes promote the mode to HIGH; record why.

| Score | Mode | Process |
|---|---|---|
| 0–3 | LOW | Compact plan, ACs, affected checks, self-review. |
| 4–6 | MEDIUM | Add diagrams where they clarify boundaries and one reviewer at substantive checkpoints when available. |
| 7+ | HIGH | MEDIUM plus verification of named high-impact risks and required platforms. |

State `Complexity: <score> → <mode>; risk override: <reason or none>`. There is no minimum number of tests, diagrams or agents, and human gates follow the property being proved, not the score.

---

## Step 0.5: Can This PRD Close Here?

Give each acceptance criterion a lane and actor on its own line:

| Lane | Meaning and action |
|---|---|
| `local` | Runnable by the agent in the current approved environment. Execute and record the result. |
| `shared` | Reachable through CI, staging, a queue, or a scheduled runner. Name the job, triggering actor, required environment, and result reference. |
| `owner` | Requires a named human's action or sign-off. Default is zero. Goes under `## Blocked on` as a line naming the person and the result to confirm. |
| `unreachable` | Required hardware, access, or actor is currently unavailable. Record it under `## Blocked on`; it is not a checkbox and does not count toward progress. |

Check available tools and equivalent environments before declaring a blocker. A substitute counts only for the property it actually proves: a simulator cannot silently replace required physical-device evidence, nor a mock replace required live-service validation. State remaining gaps.

Start approved shared checks when their inputs are ready and continue independent phases; their results remain required. Every `local` box green does not make the PRD complete.

The lane rule comes from a source-supplied audit of 700+ PRDs and 240 rejected completion attempts across three unrelated repos: the criteria that stayed unticked were the ones needing evidence the author could not reach — 40% of open versus 17% of closed PRDs in one repo (physical device), 53% versus 23% in another (deploy/staging). Design evidence for the lane model, not a fact to re-prove during execution.

For `unreachable` qualification work, name the blocker in `## Blocked on` and split it into a linked qualification PRD only when its scope is genuinely separable. A qualification dependency needed to satisfy this PRD still blocks closure; relabeling it never counts as verification.

### Owner lane

This skill does not authorize deploying, publishing, rotating credentials, or changing production; those need a separate explicit request through the applicable authorization workflow. Name the owner, the action to confirm, and the repository's header flag for the human gate, and ask once at the end, after agent-executable work is verified. Never perform or approve the owner's action, and record a result only from attributable evidence. Pending owner acceptance keeps the PRD open.

### Size cap

**At most 3 phases and about 8 boxes per PRD**, whatever the complexity mode. Work that does not fit is a second PRD, not a longer checklist: consolidate duplicate proof, or split genuinely independent scope. Never weaken a criterion, disguise several outcomes as one untestable box, or raise the mode merely to allow a human gate. If required coverage genuinely exceeds the cap, preserve it, say why in the PRD, and split the rest.

---

## Pre-Planning

For a new PRD, inspect repository instructions and naming/location conventions, then create the file with its header and phase outline before extended research. Fill it as findings land; do not overwrite an existing PRD or invent an ID that collides. For an existing PRD, update that file instead of creating a duplicate. The requested plan must exist on disk, not only in chat.

Use targeted reads of entry points, incumbent implementations, utilities, schemas, tests, configuration loaders, and build/CI scripts. Batch independent discovery instead of exploring unrelated areas one after another. Discover real commands; never assume yarn, pnpm, cargo, or any other runner. Prefer configuration schemas and `.env.example`; never print or copy secrets into a PRD.

Identify changed behavior, consumer/trigger, replacement paths, affected files, and risks. Resolve ambiguity from the repository first; ask only for decisions blocking correctness or authorization. State safe, reversible assumptions otherwise.

User-facing does not necessarily mean a new screen: the access path may be a UI, CLI, API, or SDK. Internal work needs a runtime/build trigger. Record the full path: consumer action → entry point → implementation → observable result.

### Integration Ledger

Use one row per changed integration boundary or consumer-visible capability, not per helper, exported symbol, test, or gate. For no wiring change, write `Integration: unchanged — <reason>`.

| Capability | Reachable consumer/trigger | Replaces / disposition | Evidence |
|---|---|---|---|
| Invoice creation | Checkout route → billing service; fill actual `file:line` | Legacy handler delegates | AC-1 / E1 |

Fill actual non-test entry-point locations before the owning phase completes; do not invent line numbers. Public libraries and auto-discovered routes may use a consumer fixture or real request through their public entry point. A unit test importing an internal helper is not a live consumer.

Delete or delegate obsolete paths. Temporary coexistence needs explicit migration/rollout scope, routing ownership, cutover/removal conditions, and tracked remaining work. Prove the new path runs rather than falling back. A removal required by this PRD cannot be postponed merely to close it.

---

## The shape of a box

A PRD is only as honest as its boxes, and a box nobody can tick is worse than no box at all.

- **Name the proof on the box.** `- [ ] Linux desktop build runs 300 frames. proof: \`npm run verify:desktop\`` — a command, a CI job/run, or a PR. When that proof is green, anyone may tick it and write the result beside it (`300 frames, exit 0`). A box with no proof is a wish.
- **No ceremony boxes.** An observed revert check, a reviewer's PASS, a written evidence record, an artificial negative control, a caller census: that is paperwork, and it belongs in the PR body or the PR template. Keep the work, drop the ceremony.
- **What you cannot reach is not a box.** Hardware, credentials, other people and owner decisions go under `## Blocked on`, one line each naming who or what unblocks it. They do not count toward progress, and they never harden into untickable boxes.
- **A decision deletes a moot box.** Record what was decided, by whom, on what date and why under `## Decisions`, then delete the box it made moot. Delete a box no other way. Ticked work is never deleted, and a finished PRD is never un-filed and rewritten as a fresh plan.
- **Cap the PRD: at most 3 phases and about 8 boxes.** One claim per box; a criterion that conjoins several facts is several boxes or a `## Blocked on` line.

## Plan Structure

Keep the repository's organization and these tooling-facing field names:

```markdown
# PRD-<id> — <title>

**Status:** NOT STARTED
**Complexity:** <score> (<LOW|MEDIUM|HIGH>)
**Owner:** <owner>
**Depends on:** <PRD ids or None>

## Context
Problem, current behavior, relevant files inspected.

## Solution
Approach, consumer flow, reused components, data changes, risks.
Architecture/sequence diagram only where it resolves real ambiguity.

## Acceptance Criteria
- [ ] AC-1 [local]: <consumer action → observable result, platform/threshold> — proof: `<command or job or PR>` — Evidence: pending.

## Blocked on
- <what is out of reach, and who or what unblocks it> — unblocked by <person, credential, device or decision>.

## Integration Ledger
<Applicable rows, or Integration: unchanged — reason.>

## Decisions
- <date> (<who>): <what was decided and why>.

## Execution Phases
#### Phase 1: <one working outcome>
**Status:** NOT STARTED
**Files:** <new/edited paths and purpose>
**Implementation:** <steps, contracts, error handling>
**Verification:** `<command or job>` — <assertion, ACs and distinct risks covered>
```

Add required owner flags near `**Status:**`; omit absent flags rather than filling them with `None`. Allowed status values: `NOT STARTED`, `PROPOSED`, `PARTIAL`, `IN PROGRESS`, `BLOCKED`, `DONE`, `REOPENED`. Keep status values exact; put explanations on a separate line:

```markdown
**Status:** PARTIAL
**Blocker:** Implementation verified; awaiting <owner>'s <named check> for AC-3.
```

Preserve `**Progress:**` where tooling uses it. Checkboxes are for required work/ACs, not examples, alternatives, or optional follow-ups, and not ceremony. Drop the `## Blocked on` and `## Decisions` sections when they are empty. Reuse existing required checklists instead of creating parallel copies. The closure helper's parser is authoritative for syntax; inspect it when conventions are unclear.

---

## 4. Execution Phases

Each phase delivers a coherent, testable vertical slice. Prefer roughly five implementation files or fewer, but do not fragment a working slice to satisfy a file cap. Documentation/refactor phases may prove correct consumption or preserved contracts rather than new UI behavior.

Phases are ordered by dependency, not by numbering: a dependent phase waits only for the prerequisite it actually needs, and independent phases with stable contracts and non-conflicting write surfaces may run in the same wave. Orchestrating that execution is `prd-executor`'s job, not this skill's.

Prove capabilities on a production-representative subject exercising the hard requirements — not an easy toy. If an AC names an actual production subject, use that subject. An intermediate smaller fixture must list omitted requirements and the phase that closes each gap; final acceptance cannot retain those gaps.

Implement scope, run selected affected checks, record evidence and integration locations, then perform the checkpoint. Reuse coverage; add or extend tests only for uncovered behavior or plausible regressions. Follow existing naming conventions.

Store evidence once, on the owning AC or existing phase box. Reference it elsewhere:

```markdown
- [x] AC-1 [local]: Invoice appears after checkout. proof: `npm test -- invoice` — 12 passed, exit 0; <tested snapshot>, <environment>; asserts the persisted invoice through checkout.
- [x] AC-2 [local]: Repeated checkout is idempotent. proof: `npm test -- idempotent`, assertion <test name>.
```

Identify the tested revision including relevant uncommitted changes; a commit hash alone does not identify a dirty worktree. For shared evidence, link the actual run/artifact and relevant job result. Keep output concise, inspect failure details, and retain the useful artifact reference — not a full log dump or a separate report per phase unless tooling/user requirements need one. A tool exit code alone does not establish the asserted outcome.

---

## 5. Checkpoint Protocol

Self-verification is mandatory after every phase: compare the diff to ACs, inspect reachability and failure handling, then evaluate actual execution evidence. No checklist or reviewer verdict substitutes for running the selected checks.

LOW uses self-review. MEDIUM/HIGH use one `prd-work-reviewer` or equivalent at a substantive checkpoint when available; an equivalent orchestrator review of the same scope satisfies it. If unavailable, perform and label self-review. The verdict is reported in the PR, never as a PRD checkbox.

Pass the reviewer the PRD path, phase/AC IDs, changed paths, tested snapshot, concise evidence and unresolved risks, using whatever delegation tool the harness has. Review the diff and the evidence first: AC alignment, reachable consumers, incumbent routing, required platforms, assertion quality. Rerun only a named coverage gap, stale result or suspected false positive, and report `PASS`, `NEEDS CORRECTION` or `BLOCKED` with actionable locations.

Fix findings, rerun affected checks, and review the correction/delta only. Findings that do not overlap may be handled concurrently; related findings stay with one root-cause investigation. Required shared/owner acceptance may remain pending while independent work continues; do not mark its ACs or owning phase DONE early. Human checkpoints use the owner lane, not an extra checklist.

---

## 6. Verification Strategy

### Select checks by marginal value

Before adding any test or verification step, answer: *which plausible failure does this catch that the selected checks do not?* If none, omit it. Extend an existing test or fixture before building a new harness, and pick the cheapest reliable instrument at the relevant boundary.

| Risk | Suitable evidence |
|---|---|
| Pure logic/validation | Focused unit tests and affected regressions. |
| API/job/persistence wiring | Real-entry-point integration test asserting resulting state. |
| UI interaction | Existing component/E2E flow; visual observation for properties assertions cannot establish. |
| Native/rendering/export | Required target execution on representative inputs and observable output. |
| Performance | Comparable measurements against the AC's workload, environment, and threshold. |
| Docs/config/build tooling | Relevant parser, build, link, consumer, or smoke check; no dummy unit-test quota. |

One real-entry-point integration test can prove behavior, wiring and regression safety together — do not also require curl, a demo or another E2E for the same property. A mocked helper test cannot claim integration coverage, and typechecking alone cannot prove runtime behavior.

### Minimum sufficient proof and the stop condition

For each AC, choose the smallest evidence set that would reliably reject a broken implementation. Prefer the highest useful consumer boundary: one strong observation may cover behavior, wiring, persistence, and regression. Add another check only for a distinct plausible failure, needed failure localization, or a high-impact invariant the primary proof cannot establish. High-risk security, data, billing, concurrency, compatibility, recovery, or irreversible changes may therefore need complementary evidence; choose the cheapest *sufficient*, not merely the cheapest, proof.

Stop verification when every in-scope AC has current evidence, the required consumer path is exercised, material changed risks are covered by checks capable of detecting them, required repository/user gates are green (or explicitly pending externally), and no observed failure, reviewer finding, or material uncertainty remains unresolved. Then stop adding tests, equivalent reruns, reviewers, or demos unless new information introduces a distinct risk or a requirement demands them. Run independent required checks concurrently when they do not contend for mutable resources.

### Negative controls: targeted, not universal

For new/changed behavior with an automated test harness, use test-first red → green. The red must arise from the missing behavior or bug, not an unrelated syntax/import/environment error. An already-observed valid red counts; do not disable the feature again for equivalent proof.

When no valid red exists, use a safe targeted negative control for a distinct behavior claim that could pass with the implementation absent or bypassed. A control can cover several ACs only when the observed assertions actually distinguish them. Exercise the real caller for integration claims.

No manufactured red for unchanged regression checks, lint/type/build checks, or behavior-preserving refactors whose contracts should pass before and after. Refactors still need evidence the new path is reached and the old path has the planned disposition.

When one of these false-pass risks is plausible, use the matching detection method rather than adding a generic extra test:

| Silent-pass mechanism | Negative control that catches it |
|---|---|
| **Test never collected by the runner** (excluded target, missing `mod`/import, wrong glob, `autotests = false`) | Insert a deliberate failing assertion and confirm the run reports it. Check the runner's file list and test count, not just exit 0. |
| **Both sides of a comparison resolve to the same thing** (a "differential" test whose two imports are the same module; a report diffed against a copy of itself) | Log the resolved identity of each side — module path, artifact hash, object id — and assert they differ. |
| **Assertion already satisfied by the pre-change baseline** | Run the gate with the feature disabled, or at the previous commit. It MUST fail. If it passes, it proves nothing about your change. |
| **Gate reads a stale or generated artifact** | Delete the artifact and re-run. It must regenerate or fail loudly — never pass on the old copy. |
| **Real implementation mocked out** | Assert the production path actually ran: a call count, a side effect, a log line emitted from the real code. |
| **Assertion kind silently ignored** by the harness (unknown key, typo'd field) | Assert something you know is false and confirm the harness reports failure rather than skipping. |

These controls are conditional diagnostics, not a universal checklist. Use a row only when that silent-pass mechanism is plausible and the selected evidence does not already exclude it. An already-observed valid red still counts.

Investigate specific false-pass risks: uncollected tests, self-comparisons, stale artifacts, ignored assertions, vacuous fixtures, and mocks bypassing production. Prefer runner/provenance output and existing coverage. Inject a deliberate failure only where cheaper inspection cannot establish collection or sensitivity. A call count alone does not prove the promised end state.

Temporary mutations must be isolated and reversible: preserve user changes, restore the exact candidate, rerun the affected check to green. Never mutate production, disable real security controls, or commit a negative control. A proof that cannot run safely stays `UNVERIFIED`.

### Reuse valid evidence

Reuse evidence while its code, dependencies, configuration, inputs, environment and platform are unchanged. Later edits invalidate the affected evidence, not every result in the PRD. CI evidence must match the candidate's scope and show the required tests actually ran — a skipped or cancelled job is not a passing check.

Run focused checks while iterating and the broader required gates once at final verification, unless a matching result already exists. Never weaken a required check to meet a token budget, and never rerun unrelated suites after status-only edits. Missing execution or access means `UNVERIFIED` or `BLOCKED`; existing red CI is not a passing gate, and only an explicit authorized waiver counts.

---

## 7. Acceptance Criteria and Required Closure

Write criteria about consumers and observable outcomes, not mere artifact existence: "invoice appears in billing after checkout," not just "endpoint returns 200." Compatibility, correct artifact consumption, security invariants, or documentation usability can also be valid outcomes.

When every in-scope AC is implemented and verified, all required gates/reviews and completion-blocking dependencies are satisfied, and no required work remains, you MUST mark the PRD DONE and move it to the repository's `done/` location in the same implementation task. Do not stop at "ready to close" or merely recommend the move.

This includes required `local`, `shared` and `owner` evidence. An open owner check means `PARTIAL` with a separate blocker explanation, not `DONE`, and unreachable required qualification blocks closure too. "Code complete" is a qualified implementation statement, not completed acceptance.

Never tick, delete, weaken, or relabel a required AC to make closure succeed. The one exception is R4: a decision that made a box moot deletes it and is recorded under `## Decisions`. Not-applicable items need a factual scope explanation; changes to agreed requirements need authorization. Closure consumes existing evidence; it is not another test suite or review cycle. Reconcile the boxes, phase statuses, `**Status:**` and `**Progress:**` from recorded evidence — gaps and placeholders keep the PRD open. Optional follow-ups do not block closure; unfinished required work does.

A PRD whose only remaining work is its `## Blocked on` list is not DONE: file it under the repository's blocked location (`BLOCKED/<reason>/` where that convention exists), naming the reason in the folder, so the owner can validate it later. Any PRD with doable work left stays where it is.

Use the repository's `prd-manager` closure helper when available; inspect its usage and destination. For installations with this layout:

```sh
node "$HOME/.claude/skills/prd-manager/scripts/prd-close.mjs" "<prd-path>" --yes
```

If the helper is unavailable, update the fields and `git mv` to the established done directory (or `done/` under the PRD root when no convention exists); use a normal move outside Git, and never overwrite a collision. A helper rejection is not permission to bypass it manually. Verify the destination exists, the old path is gone and the status fields are accurate, then update affected board/index links and PR references.

Include the move/status/link changes in the finishing commit or PR when authorized, but do not merge or deploy merely to close a PRD. Report verified implementation separately from incomplete archival if a move or status write fails, and never claim a move or a successful run without observing it.

---

## Guardrails and Isolation Anti-Patterns

Do not ship orphan code, mocked-only integration proof, unread contracts, uncollected tests, self-comparisons, manufactured success, stale artifacts, vacuous fixtures, or success responses without the promised state change. Investigate concrete risks rather than adding another generic checklist.

These are the concrete diff signatures of "implemented but not integrated." Scan the changed surface for the applicable signatures during self-review/checkpoint; do not mechanically prove every row when the diff cannot exhibit it. Finding one fails the affected phase until the wiring/evidence is corrected.

| Smell | What it looks like in the diff |
|---|---|
| **Orphan module** | New file whose only importers are its own tests — or zero importers at all |
| **Additive migration** | The new implementation lands and the old one is still the one running. Two or three copies of the behavior, none sharing a source. |
| **Dead-code marker** | `#![allow(dead_code)]`, `eslint-disable no-unused`, unused-export suppression added so the new code compiles |
| **Unread contract** | A types/contract/schema/descriptor file the implementation never consults |
| **Listed-but-absent test** | A test name promised in the PRD with no body in the repo |
| **Uncompiled test** | A test file the build excludes: missing `mod`/import, excluded target, non-matching glob |
| **Self-comparison** | A differential or parity gate whose two sides resolve to the same module, file, or artifact |
| **Toy proof** | The capability proved on the one input that needs none of the hard requirements |
| **Twin constants** | PRD says "derived from one owner"; the code has two hardcoded literals with nothing tying them |
| **Registered but unspawned** | Plugin/handler/route registered, nothing ever invokes it |
| **Manufactured evidence** | The report emits `status: "applied"` / `ok: true` as a literal instead of measuring anything |
| **Vacuous fixture** | The gate's fixture does not contain the feature under test (an overlay-packaging gate whose fixture has no overlays) |
| **Envelope ≠ state** | The call returns success and the persisted state is unchanged — `changed: true` written next to an empty object |
| **Pure function stands in for the loop** | The evidence harness calls the function directly; the frame loop / request path never does |

The §0.5 audit figures are source-supplied rationale, kept inline so this skill has no dangling `references/` dependency; the sections above are the active rules.
