---
name: code-review-excellence
description: Review diffs for actionable defects; design review standards or mentor reviewers.
---

# Code Review Excellence

Review against the requested behavior and repository contracts. Prioritize correctness,
security, performance, maintainability and meaningful test coverage. Review-only requests
authorize inspection, not code edits, posted comments or PR mutations.

## Review workflow

1. Establish the base/head or working diff, requirements, applicable instructions and check
   status. Read changed code, relevant callers, contracts and tests; expand inspection when
   a dependency or observed failure warrants it. A large diff needs coherent review slices,
   not an automatic demand to rewrite or split an otherwise valid change.
2. Trace affected behavior end to end. Check boundary/empty/error cases, async races and
   lifecycle cleanup; authentication and authorization; validation, injection, secrets and
   sensitive errors; query/load costs, blocking work and resource leaks. Apply only relevant
   checks, but do not omit a risky integration merely because it is outside the diff.
3. Verify suspected defects against the actual implementation and call sites. Use a focused
   reproduction or non-mutating test where useful. Check that tests assert observable behavior,
   cover failures and remain independent/deterministic. Inspect architecture/API compatibility
   and documentation when the change affects their contracts.
4. Report each distinct finding once: severity, file/line, concrete trigger, user impact,
   evidence and a bounded fix. Separate blockers from suggestions; omit style preferences
   enforced by tooling, speculative defects and repeated findings. Say when no actionable
   defect was found and name material limits of the review. Never imply checks ran if they did not.

## Context and verification economy

Load this skill once per available context. Re-read if it changed or its instructions were
lost; do not read it again for every file or repair. Preserve a small record of reviewed
base/head, paths, open findings and checks when resuming.

Inspect existing test artifacts before rerunning the identical command. Reuse a result only
when the command, relevant source (including uncommitted files), dependencies, configuration
and environment still match; otherwise rerun. Repository-required independent checks and
final integration gates still apply. Read full failure evidence when needed, but return
the result and log path instead of copying passing logs or full diffs into the conversation.

Review repairs against the findings and affected integrations. New behavior or risk expands
the review; unchanged context does not require restarting the whole investigation.

## Review standards and mentoring

For team review standards, mentoring, language examples or a detailed security checklist,
read the relevant section of [references/review-handbook.md](references/review-handbook.md).
It preserves the original teaching material; it is not required reading for an ordinary diff.
Keep feedback specific, respectful and grounded in impact. Resolve disagreement using code,
tests and measured tradeoffs, not personal preference. Adapt the output to the requested
review format; do not fill empty template sections.
