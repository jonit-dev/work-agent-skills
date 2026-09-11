---
name: implementation-notes
description: >-
  Keep a running implementation-notes.md during implementation that logs
  decisions, plan deviations, and surprises, so the next iteration can learn
  from this one. Use when the user says "keep implementation notes",
  "记录实现笔记", or kicks off implementation of a reviewed plan or spec.
---

# Implementation Notes

No plan survives contact with the codebase. Log what changed and why, without
stopping the work.

## Workflow

1. **At the start of implementation**, create `implementation-notes.md` in the
   project root. If the file already exists from a previous task, do not
   overwrite it — append a new dated section for this task. Treat it as
   disposable working material: do not commit it unless the user asks, and if
   this is a git repo, add the filename to `.git/info/exclude` (not
   `.gitignore`, which would show up in the diff). Structure:

```markdown
# Implementation Notes — <task name>

## Context
Links to the plan/spec/prototype this run is based on.

## Decisions
Choices made where the plan was silent. One line each: what + why.

## Deviations
Where reality forced a change from the plan.
Each entry: what the plan said / what was found / what was done instead / why.

## Surprises & Open Questions
Edge cases, dead code, wrong assumptions in the plan — anything the next
planning session should know.
```

2. **During implementation**, when an edge case forces a choice the plan
   didn't anticipate: pick the conservative option (smallest blast radius,
   easiest to reverse), log it under Deviations, and keep going. Only stop to
   ask the user when the deviation would invalidate the plan's goal.
3. **Update the file as you go**, not retroactively at the end. Entries are
   one to three lines; this is a log, not documentation.
4. **At the end of the session**, give the user a brief digest of Deviations
   and Open Questions — these are the discovered unknowns that should feed the
   next planning round. The digest in chat is the durable handoff; the file
   itself is disposable scaffolding unless the user chooses to keep it.

## Rules

- Never silently deviate from the agreed plan; every deviation gets an entry.
- Do not duplicate what git already records (diffs, file lists); record the
  reasoning that a diff cannot show.
