---
name: implementation-plan
description: >-
  Write an implementation plan that leads with the decisions the user is most
  likely to change — data models, type interfaces, anything user-facing — and
  buries mechanical work at the bottom. Use when the user says "implementation
  plan", "实现计划", "写个实现方案", or is ready to implement after
  brainstorming and wants a reviewable plan first.
---

# Implementation Plan

A plan's job is to surface the things the user might actually need to alter,
before changing them becomes expensive. Order it by likelihood of change, not
by execution order.

## Workflow

1. **Gather the inputs.** Collect what this plan is based on: the brainstorm,
   spec, prototype, or interview decisions from earlier in the conversation,
   plus a read of the code that will be touched.
2. **Sort by likelihood of change, not chronology.** Lead with the decisions
   the user is most likely to tweak:
   - data model and schema changes
   - new type interfaces and API shapes
   - anything user-facing (UX flows, copy, layout)
   Bury the mechanical refactoring at the bottom — the user trusts the agent
   on that part.
3. **Make the top decisions reviewable.** For each high-change-risk decision:
   the chosen option, 1-2 alternatives considered, and what changing it later
   would cost. This is what lets the user veto cheaply.
4. **Mark the improvisation zones.** Flag the areas where unknowns are likely
   to surface mid-implementation, and state the fallback posture for each
   (e.g. "pick the conservative option and log it").
5. **End with an explicit go/no-go.** Ask the user to approve, adjust, or
   reject. On approval, suggest starting implementation in a fresh session
   with this plan (and any prototypes) passed in as artifacts.

## Rules

- The plan is for review, not a contract — it should tell the reader where
  it is likely to be wrong.
- Do not start implementing in the same breath as presenting the plan.
- If a plan section would just restate the obvious ("write the code, run the
  tests"), cut it; length is not thoroughness.
