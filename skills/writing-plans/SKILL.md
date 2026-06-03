---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.2.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

For PRDs/plans that must be based on a current feature branch rather than `master`, explicitly record the branch and dirty-state basis before writing:

```bash
git branch --show-current
git status --short
git log --oneline --decorate -n 10
```

If the plan spans sibling repos, inspect each relevant repo the same way and include exact repo paths, branches, and pre-existing dirty files in the plan. Do not checkout, reset, or base work on `master` unless the user explicitly asks. When there are unrelated pre-existing changes, call them out as unrelated so the plan's file changes are easy to verify.

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Astro docs/wiki architecture note

When planning an Astro migration for a game docs site that needs tutorials, blog/news, and an internal wiki, prefer a hybrid content architecture:

- **MDX for tutorials, guides, and blog/news/devlog posts**: long-form authoring, SEO-friendly pages, frontmatter, and embedded components when needed.
- **Structured data + Astro/React components for game database/wiki primitives**: items, mobs, NPCs, quests, recipes, classes, and world areas should be searchable/filterable and generated from data rather than handwritten React pages.
- **Reusable MDX components**: plan components such as `ItemCard`, `MobCard`, `RecipeCard`, `ClassBadge`, and wiki link cards so MDX content can reference live game data without duplicating facts.
- **Avoid regular React for plain tutorials** unless the page is primarily interactive. React-only long-form docs create unnecessary boilerplate and are harder to edit.

For concrete planning checklists, see:

- `references/astro-docs-mdx-wiki-architecture.md` — hybrid MDX/data architecture.
- `references/astro-game-docs-mdx-wiki-swarm.md` — PRD-first source exploration, parallel content lanes, Pagefind search, official link/icon integration, and visual QA for game docs/wiki migrations.

## Mobile App / Capacitor Deployment PRDs

When writing a PRD for deploying an existing web app to mobile with Capacitor, explicitly plan both the deployment automation and the app-like UX work. If the user says to reuse the same codebase, make that a primary requirement: avoid React Native/Expo forks and keep business logic in the existing app unless the user explicitly asks for a native rewrite.

For SSR/server-runtime apps, first decide whether the mobile shell should bundle static assets or load the hosted production URL. Astro SSR/Cloudflare Pages style apps usually need a hosted Capacitor WebView (`server.url`) so API routes and server rendering continue to work. The target command (for example `yarn deploy:mobile`) should cover web deploy, Capacitor sync, platform-gated native builds, and artifact/report output. Include safe sync-only/skip flags so the workflow can be tested without a production deploy.

Do not stop at “install Capacitor.” Include app-feel requirements: splash/icons/status bar, safe-area CSS, app-mode detection, mobile bottom navigation/app shell, 44px touch targets, no horizontal overflow, modal/bottom-sheet behavior, keyboard-safe forms, calendar/table adaptations, external auth/payment handoffs, app resume/session behavior, deep links, and Android/iOS build prerequisites.

See `references/capacitor-mobile-app-prd-checklist.md` for the reusable checklist.

## Mobile App / Capacitor PRDs

When planning Capacitor/native mobile deployment for an existing web app, do not assume `server.url`/hosted WebView is required just because backend APIs exist, and do not assume a local bundled WebView works just because another React app did. Add an explicit first spike that tests the project architecture:

- If the app is client-only React/Vite, a bundled `webDir` app loaded from `capacitor://localhost` may be the right default.
- If the app uses SSR/server-rendered routes, relative `/api/...` calls, auth cookies tied to the web origin, or dynamic non-prerendered pages, plan a proof step before choosing hosted vs bundled.
- Document both viable paths: hosted shell for lowest-risk reuse of SSR/API runtime, and bundled app with explicit remote API base/auth/deep-link handling if the spike passes.
- If the user wants the native app to feel distinct from mobile web, plan a mobile-app-only entry route/shell (for example `/app` or `/mobile-app`) and explicitly leave the public mobile landing page unchanged. The native app should not default to marketing sections like hero/pricing/testimonials/FAQ unless requested.
- Acceptance criteria should include proving native launch opens the app-only route, while `/` remains the regular mobile web landing page.

## Capacitor / Mobile Deployment PRDs for Existing Web Apps

When planning a Capacitor/native mobile deployment for an existing web app, be reuse-first and architecture-explicit:

- Do not assume Capacitor requires a hosted URL. Client-only apps can bundle into the WebView; SSR/API-heavy apps may need a hosted runtime or a dedicated static app shell that talks to remote APIs.
- Add an early spike to prove local bundled mode vs hosted shell before locking the plan.
- If the user wants the app to feel native, plan a dedicated app-only route/shell (for example `/app`) instead of reusing or redesigning the public mobile web landing page.
- Preserve mobile web unless explicitly asked to change it.
- Explicitly state “no second codebase”: reuse existing services, hooks, stores, auth/session utilities, validation schemas, API routes, Stripe/Supabase logic, and responsive components wherever possible.
- Add dev-readiness items, not just product UX: shared API origin resolver, auth redirect/session strategy, middleware rules for the app route, local mobile dev loop, version/build numbers, release channels, native security config, hardware back/keyboard/external-link behavior, and CI/macOS/iOS build constraints.
- Keep store upload/signing separate from the default deploy command unless the user explicitly requests store release automation.

See `references/capacitor-mobile-deployment-prd-checklist.md` for the reusable checklist.

## SaaS Release-Readiness Roadmap Reviews

When the user asks what is missing to release, launch, or beta a SaaS/app project, treat it as a roadmap-vs-readiness review, not a generic feature brainstorming task.

First inspect the project’s roadmap/PRDs/current feature map/package scripts/env examples where available. Separate **built feature surface** from **release proof**:

- manual critical-path validation and P0/P1 blocker evidence;
- automated release gate / E2E / production-equivalent runtime validation;
- production third-party setup: database/auth, payments/webhooks, hosting/DNS, email/SMS, analytics/search;
- onboarding/go-live checklist so users cannot reach an unusable state;
- operations: security settings, alerts, runbooks, rollback paths;
- pilot/customer validation.

Do not answer only with “add integrations, SEO, domain, deploy.” For release planning, the missing work is often provider configuration, real runtime validation, and operational readiness. Keep the final answer concise and decision-oriented: bottom line, blockers, planning-doc checklist, and what can be deferred.

See `references/saas-release-readiness-roadmap-review.md` for the reusable scan pattern and checklist.

## Validation / QA Handoff Plans

When writing a validation plan for a freelancer, QA contractor, or fixed time-box, do not automatically produce a full exhaustive plan. First establish:

- The actual time budget, e.g. 20 total hours vs. two full-time weeks.
- What is already covered by existing E2E/manual validation or user-provided status summaries.
- Which areas are prevalidated and only need smoke checks.
- Which remaining gaps are release-risk P0/P1 items.

For small budgets, reframe from “validate all features” to “critical-path validation for launch blockers.” The plan should explicitly include:

1. **Already covered / do not deeply revalidate** — stop paid QA time from being wasted on completed broad coverage.
2. **Remaining release-risk gaps** — manage tokens, paid booking intersections, real email/SMS, RBAC, mobile smoke, provider/webhook proof, and any newly reported bugs.
3. **Time-boxed allocation** — blocks by hours, each tied to an outcome.
4. **Evidence requirements** — pass/fail/blocked, screenshots/video, provider IDs where relevant, and reproduction steps for P0/P1.
5. **Explicit out-of-scope list** — items not validated due to time budget.

See `references/freelancer-validation-plan-handoff.md` for a reusable pattern and example wording.

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**
