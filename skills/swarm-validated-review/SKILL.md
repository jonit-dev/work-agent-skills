---
name: swarm-validated-review
description: Use when a user asks for a parallel agent swarm, delegated investigation, multi-agent review, independent verification, false-positive reduction, or a manager/double-check pass for any task. Applies to audits, code reviews, research, planning, bug hunts, production readiness checks, architecture reviews, and other task-agnostic investigations where multiple specialist passes should be reconciled into a curated result.
---

# Swarm Validated Review

Run focused specialist agents in parallel, then route their findings through a skeptical manager review before presenting or acting on the result. The goal is higher coverage with lower false positives.

## When To Use

Use this skill when the user explicitly asks for:

- a swarm, team, multiple agents, or parallel investigation
- independent specialists plus a manager/reviewer pass
- double-checking findings to reduce false positives
- a broad audit that benefits from parallel slices
- evidence-backed findings across security, correctness, readiness, UX, operations, research, or strategy

Do not spawn subagents unless the user explicitly asks for delegated/parallel agent work or the current system allows it and the request clearly calls for it.

## Core Workflow

1. **Define the objective and slices**
   - Restate the concrete output expected: report, fix list, implementation, recommendation, or decision.
   - Split work into independent slices with minimal overlap.
   - Keep the critical path local. Delegate sidecar investigation that can run in parallel.

2. **Launch specialist agents**
   - Give each agent a bounded scope, clear evidence requirements, and explicit instruction not to edit files unless assigned.
   - Ask for severity, impact, proof, and false-positive checks.
   - Avoid duplicating the same question across agents unless deliberate redundancy is needed.

3. **Work locally while agents run**
   - Inspect high-risk or central paths yourself.
   - Run relevant validation commands.
   - Capture exact file paths, line references, commands, outputs, links, or artifacts.

4. **Normalize specialist outputs**
   - Merge duplicates.
   - Separate confirmed findings from gaps, assumptions, and product decisions.
   - Preserve evidence and caveats.
   - Flag items that need direct verification before inclusion.

5. **Run a manager review**
   - Send the combined candidate findings to a separate reviewer/manager agent.
   - Instruct it to classify each item as `keep`, `downgrade`, `merge duplicate`, `reject`, or `needs caveat`.
   - Require it to verify later code/docs/migrations/config that may already remediate the issue.

6. **Curate the final output**
   - Include only findings that survived local or manager validation.
   - Make caveats explicit.
   - Order by risk and actionability.
   - Include a concise fix order or next-step plan.

## Agent Prompt Pattern

Use this shape for each specialist:

```text
You are part of a parallel investigation of <target>.
Focus only on <slice>.
Do not edit files unless explicitly assigned.
Return real issues only with evidence: file paths/line numbers, command output, source links, or concrete artifacts.
For each issue include severity, impact, and why it is not a false positive.
Avoid speculative findings. Note any missing production-critical or task-critical pieces separately.
```

Use this shape for the manager:

```text
You are the manager/reviewer for a multi-agent investigation of <target>.
Do not edit files.
Your job is to reduce false positives.
Review the candidate findings below against the source material.
Classify each as: keep, downgrade, merge duplicate, reject, or needs caveat.
For kept findings, provide corrected severity and concise evidence.
Be skeptical and verify whether later code, docs, config, or migrations already remediate the issue.
Return a curated list and a rejected/merged section with reasons.
```

## Specialist Slicing Examples

For code or product audits:

- core flow and logic correctness
- security and authorization
- production readiness and operations
- data integrity and migrations
- tests and CI
- frontend UX/accessibility

For research or strategy:

- primary-source evidence
- competitive landscape
- risks and objections
- implementation feasibility
- cost and operational constraints

For implementation planning:

- architecture/design
- API/data model
- migration/backward compatibility
- test strategy
- deployment/rollout risks

## Evidence Rules

- Prefer primary evidence over opinion.
- Require exact references when possible: file path and line, command output, source link, test name, migration name, log excerpt, or screenshot.
- Distinguish bugs from product gaps.
- Distinguish direct exploitability from defense-in-depth concerns.
- Do not keep a finding merely because multiple agents mentioned it; keep it because evidence supports it.
- If a finding depends on environment configuration, state the condition clearly.

## Severity Calibration

- **Critical:** auth bypass, data exposure, data corruption, money/credit loss, production-wide outage, public unauthenticated dangerous action.
- **High:** privilege escalation, cross-tenant/cross-user access, reliable business-critical flow failure, serious operational gap.
- **Medium:** correctness bug, incomplete production workflow, reliability weakness, non-atomic operation with recoverable impact.
- **Low:** product readiness gap, missing polish, documentation mismatch, future risk.

Adjust severity downward when exploitability depends on an unverified external condition, and state that condition.

## Final Output Pattern

Use a concise structure:

- verification performed
- executive summary
- critical/high/medium/low findings
- for each finding: severity, evidence, impact, false-positive caveat, fix
- recommended fix order
- rejected/merged/caveated findings

If the user asked for a file, create it and report the path.

## Guardrails

- Do not let subagents make overlapping edits unless each owns a disjoint write scope.
- Do not wait idly if agents are running; continue local non-overlapping work.
- Do not outsource the final judgment. The main agent owns the curated result.
- Do not include raw unverified specialist claims in the final answer.
- Do not hide uncertainty; label caveats directly.
