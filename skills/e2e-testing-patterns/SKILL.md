---
name: e2e-testing-patterns
description: Master end-to-end testing with Playwright and Cypress to build reliable test suites that catch bugs, improve confidence, and enable fast deployment. Use when implementing E2E tests, debugging flaky tests, or establishing testing standards.
---

# E2E Testing Patterns

Use the repository's Playwright or Cypress suite to prove critical user journeys, complex interactions, authentication and real API integration. Cover relevant browsers, responsive layouts and accessibility. Keep ordinary unit logic and API-contract coverage in faster lower-level tests; E2E assertions should measure observable user outcomes.

## Reliable tests

1. Inspect existing configuration, scripts, fixtures and conventions. Reuse page objects/custom commands for repeated interactions. Use stable role/label or test-ID selectors, not styling classes, DOM position or internals.
2. Make tests independent and deterministic. Create unique fixture data, clean it up even on failure, and isolate accounts/state across parallel workers. Avoid shared mutable fixtures and order dependencies.
3. Wait for observable readiness with auto-retrying assertions or an explicit URL/response/event, not fixed sleeps. Register response waits before triggering the request. A generic network-idle condition alone is not proof that the UI is ready.
4. Drive the actual user action and assert the resulting UI/state, including important failures. Mock external services and controlled error cases when appropriate, but distinguish mocked UI coverage from proof that the real application integration works. Do not mock away the behavior you claim to verify.
5. Run targeted cases while iterating and required full-suite/CI checks before completion. Ensure tests are collected. Keep traces, screenshots, video and reports for failures; retries help capture evidence but do not fix flakes. Report actual commands, results and any unverified paths.

## Tool-specific examples — load only what you need

- Playwright setup, page objects, fixture lifecycle, waits and interception: [references/playwright-examples.md](references/playwright-examples.md).
- Cypress configuration, typed custom commands, intercept aliases and delayed responses: [references/cypress-examples.md](references/cypress-examples.md).
- Visual regression, CI sharding and accessibility examples: [references/advanced-examples.md](references/advanced-examples.md).

These are illustrative snippets, not a ready-to-run suite. Adapt to installed versions and real fixtures. Choose project-appropriate timeouts/retry limits, prohibit focused-only tests in CI, and use HTML/JUnit artifacts where needed. Parallelize/shard only independent tests within environment capacity. For visual baselines stabilize data/rendering and inspect differences before accepting updates; automated accessibility scans complement interaction checks.

## Diagnose failures

Reproduce with the same browser, revision, data and environment; inspect the first failure's trace and resulting page/network state. For Playwright, use the existing runner with `--headed` or `--debug`, trace viewer, screenshots and `test.step`; use `page.pause()` only for an interactive investigation. Remove temporary pauses afterward. Fix the race, selector, cleanup or state issue rather than inflating sleeps/retries. Keep full diagnostic artifacts outside chat and return relevant evidence.
