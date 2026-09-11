---
name: interview-me
description: >-
  Interview the user one question at a time to turn ambiguities into explicit
  decisions before implementation, prioritizing questions whose answers would
  change the architecture. Use when the user says "interview me", "访谈我",
  "问我问题", or wants ambiguities resolved before a task starts.
---

# Interview Me

Resolve the user's known unknowns by interviewing them, one question at a
time, before any implementation.

## Workflow

1. **Build the question list silently.** From the conversation, plus a quick
   scan of relevant code, list the ambiguities in the task. For each, note
   whether the answer would change: architecture/data model > scope/behavior >
   UX details > cosmetics. Sort by that impact.
2. **Ask one question at a time.** Use the structured question tool when
   available. Every question must:
   - Present 2-4 concrete options with their trade-offs, not an open-ended
     "what do you want?".
   - Put a recommended option first, marked as recommended.
   - Say why the answer matters (what it would change).
3. **Stop early.** End the interview once remaining unknowns would not change
   the approach — typically 3-7 questions. Never pad with questions you could
   answer yourself from the code; go read the code instead.
4. **Deliver the decision record.** Summarize as a compact list of decisions
   ("known knowns") ready to paste into an implementation prompt or plan,
   plus any deliberately deferred unknowns and the assumption chosen for each.

## Rules

- One question per turn. Do not batch.
- If the user answers "I don't know", offer to prototype (the
  design-directions skill exists for this) or default to the recommended
  option and record it as an assumption — do not re-ask.
- Do not start implementing during the interview.
