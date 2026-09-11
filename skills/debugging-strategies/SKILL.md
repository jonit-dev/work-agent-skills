---
name: debugging-strategies
description: Diagnose bugs, crashes or performance regressions using reproducible evidence.
---

# Debugging Strategies

Find the cause before prescribing a fix. A diagnosis request ends with evidence and a proposed
fix; implement when the user requested repair. Keep production investigation read-only unless
a specific mutation is authorized, and protect credentials and personal data in captures.

## Investigation loop

1. Record expected versus actual behavior, exact reproduction, environment/version and affected
   scope. Read the complete relevant error/stack trace; inspect recent changes and existing
   diagnostics. Reduce to a minimal reproduction when possible. For intermittent failures,
   retain the timing, state transitions and workload needed to reproduce them.
2. Trace the failing path through its callers, data contracts and external boundaries. Compare
   a working and failing case. Rank plausible causes from evidence and choose a probe that
   distinguishes them; do not scan unrelated systems or change several variables at once.
3. Run that probe, capture its outcome and update the hypothesis. Use breakpoints, focused
   logging, differential analysis or bisect as appropriate. Isolate bisect/experiments from
   others' changes. For performance, profile first and compare before/after under the same
   workload. For memory leaks, compare retained allocations/heap snapshots across a repeatable
   lifecycle; for races, vary ordering/load and test synchronization boundaries.
4. When repair is authorized, first reproduce the defect with the appropriate regression test
   or runtime proof, fix the cause, then rerun that proof and relevant regression/integration
   gates. Preserve required repository checks. Remove temporary instrumentation you added.
   If reproduction or validation is unavailable, report that limit explicitly.
5. After three failed fixes, stop changing code and name the doubtful assumption. Preserve the
   failing evidence and next discriminating probe. Do not repeat an unchanged command or prompt
   as a new investigation.

## Context and output

Keep a compact record of reproduction, hypotheses ruled out, evidence paths and next probe.
On resume, inspect that record and changed inputs before repeating discovery. Load this skill
once while its instructions remain available and unchanged; read only relevant references.

For long diagnostics/tests, keep full logs in a local artifact and inspect bounded relevant
excerpts. Preserve the command's real exit status; a successful tail/grep is not a passing test.
Use completion notifications or a blocking wait up to 60 seconds for a running command, with
bounded output. Inspect new output/state, not the entire accumulated log on every poll.
Do not overlap expensive probes sharing a GPU, test database or mutable fixture.

Report location, cause, supporting evidence, fix (or proposed fix), validation and remaining
uncertainty. Do not substitute shorter reporting for missing diagnosis or runtime proof.

## Optional recipes

Read the relevant language/tool section of
[references/debugging-handbook.md](references/debugging-handbook.md) when you need debugger
setup, profiling examples or detailed issue-specific checklists. The original teaching material
is retained there; ordinary investigations do not need every language's examples.
