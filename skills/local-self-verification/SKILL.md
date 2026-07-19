---
name: local-self-verification
description: Create an evidence-backed self-verification plan for a local app, service, workflow, integration, UI, API, database, queue, websocket, or full system. Use when asked to plan verification, QA, acceptance validation, end-to-end proof, test evidence, Playwright/API/DB validation strategy, or a local self-verification report plan. If explicitly asked to execute verification too, use this plan as the checklist for implementation and reporting.
---

# Local Self-Verification

## Mission

Create a practical self-verification plan that lets an agent prove a local system works as intended. The plan must emulate a strong QA engineer: exercise real behavior, gather objective evidence, cover meaningful failure paths, and define cleanup.

Do not stop at "inspect the code" or "run tests." The plan should specify observable proof: programmatic requests, UI automation, database inspection, logs, network traces, websocket messages, background jobs, files, cache state, and other relevant side effects.

If the user explicitly asks to run verification, execute the plan and produce the final validation report. Otherwise, produce the plan only.

## Plan Inputs to Discover

Before writing the plan, identify or infer:

- Target feature, workflow, or system boundary.
- Expected behavior and acceptance criteria.
- Local startup commands.
- URLs, ports, routes, API endpoints, websocket endpoints, and worker processes.
- Required environment variables.
- Database type and connection method.
- Authentication method and test credentials.
- Test data requirements.
- External dependencies and local substitutes.
- Existing test framework and conventions.
- Safe cleanup strategy.

Infer safe defaults from README files, package scripts, docker compose files, env examples, tests, seed scripts, and repo conventions. Ask for clarification only when missing information prevents a safe or meaningful plan.

## Required Output

Create a Markdown self-verification plan. Use this structure unless the user requests a different format:

```markdown
# Self-Verification Plan: <target>

**Repository/Path:** `<path>`
**Environment:** <local/dev/docker/etc>
**Planned Test Run ID Format:** `qa_YYYYMMDD_HHMMSS_<suffix>`
**Final Report Path:** `validation-report.md` or `reports/validation-YYYYMMDD-HHMMSS.md`

## 1. Target Statement

What is being verified, what should be true when it works, the key user journeys, expected side effects, and forbidden side effects.

## 2. Acceptance Criteria

- <criterion>

## 3. System Discovery

- Startup commands:
- Routes/endpoints:
- Database/storage:
- Auth/test credentials:
- Workers/queues/websockets:
- External dependencies:
- Existing tests:
- Unknowns/assumptions:

## 4. Verification Matrix

| Area | Scenario | Method | Evidence to Capture | Expected Result | Priority |
|---|---|---|---|---|---|
| Smoke | App boots and route loads | command/curl/Playwright | process output, status code, screenshot | PASS condition | P0 |
| Happy path | Primary workflow succeeds | Playwright/API | network response, UI state, DB row | PASS condition | P0 |
| Negative path | Invalid input fails safely | API/UI | error payload, UI validation | PASS condition | P1 |
| Persistence | State survives reload/requery | DB/UI | SQL result, refreshed UI | PASS condition | P0 |
| Side effects | Jobs/files/events/logs are correct | logs/DB/files/ws | event/log/file evidence | PASS condition | P1 |
| Auth | Unauthorized access is blocked | API/UI | status code, redirect/error | PASS condition | P1 |
| Regression | Previously broken behavior stays fixed | existing/new test | test output | PASS condition | P1 |

## 5. Test Data Plan

- Generate `test_run_id`: `qa_YYYYMMDD_HHMMSS_<short-random-suffix>`.
- Prefix created users, records, files, and metadata with the test run ID.
- Record all created entities for cleanup.
- Avoid shared or production-like data.

## 6. Execution Steps

1. Start or confirm required services.
2. Run smoke checks.
3. Exercise API/service behavior.
4. Exercise UI behavior with Playwright if a UI exists.
5. Inspect database/storage state after important actions.
6. Inspect logs, queues, websockets, network traces, or background jobs when relevant.
7. Cross-check critical claims across multiple layers.
8. Handle failures with the red-green loop.
9. Clean up test data and temporary artifacts.
10. Write the validation report.

## 7. Evidence Requirements

- Commands run and key output.
- HTTP status codes, response schemas, and important payload fields.
- Playwright screenshots/traces, console errors, and failed network requests.
- Database queries and relevant result rows.
- Worker/job/log excerpts.
- Websocket frames or realtime event payloads.
- File, cache, object storage, or email side effects.

## 8. Bug Handling

For every bug:

1. Freeze and capture the failure.
2. Create the smallest reproducible check.
3. Run it red before fixing.
4. Fix only if in scope.
5. Rerun the same check green.
6. Keep a regression test when it fits the repo.
7. Document severity, status, red evidence, fix summary, green evidence, and remaining risk.

## 9. Cleanup Plan

- Delete only entities matching the current `test_run_id`.
- Remove temporary files, browser state, sessions, queue messages, uploads, and cache entries.
- Stop services started only for verification.
- Keep evidence artifacts only in the report/evidence directory.
- Verify cleanup where practical.

## 10. Final Report Template

The executed verification report should include:

- Scope.
- Expected behavior.
- Verification matrix with results.
- Commands and tools used.
- Evidence summary.
- Bugs found.
- Cleanup performed.
- Residual risks and gaps.
- Final conclusion: `PASS`, `FAIL`, or `PARTIAL`.
```

## Planning Rules

- Prioritize tests that catch production-relevant bugs first.
- Cover happy path and meaningful failure paths.
- Prefer real local services over mocks unless dependencies cannot run locally.
- Treat database inspection as supporting evidence, not a substitute for user-visible behavior.
- For UI systems, include Playwright coverage for core workflows, console errors, failed network requests, reload behavior, and important screenshots or traces.
- For async systems, require direct observation of websocket frames, queue state, worker logs, retries, or final side effects.
- For critical workflows, require a proof chain across layers, such as UI action, network response, DB state, worker log, and refreshed UI.
- Never plan broad destructive cleanup against shared data; cleanup must target the generated `test_run_id`.

## Pass/Fail Criteria

Plan the final report to mark:

- `PASS` only when all critical acceptance criteria are tested, evidence supports each critical claim, no critical or high-severity unresolved bugs remain, and cleanup succeeds.
- `FAIL` when a critical journey fails, serious data/auth/security/persistence issues are found, cleanup leaves unsafe state, or the system cannot be started or inspected enough to validate the target.
- `PARTIAL` when meaningful verification passes but important areas cannot be tested, evidence is incomplete, dependencies are unavailable, or non-critical bugs remain unresolved.
