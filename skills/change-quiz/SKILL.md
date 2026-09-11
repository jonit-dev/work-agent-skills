---
name: change-quiz
description: >-
  Generate a self-contained HTML report explaining a change set, ending with a
  quiz the user must pass before merging. Use when the user says "quiz me",
  "考考我", "change quiz", or wants to verify they truly understand what
  happened in a session or diff before approving it.
---

# Change Quiz

After a long session, the diff alone undersells what changed, because much of
the behavior depends on existing code paths. Build the user's understanding,
then verify it.

## Workflow

1. **Determine scope**: the current session's changes by default, or the
   diff/branch/PR the user points at. Read the touched code *and* the existing
   code paths it plugs into.
2. **Write one self-contained HTML file** (`change-report.html` in the
   project root; inline CSS/JS, no network). It must stay out of the change
   set it describes: do not commit it, and if this is a git repo add the
   filename to `.git/info/exclude`. Contents:
   - **Context & intent** — the problem, and the shape of the solution.
   - **What changed** — grouped by area, each linking file paths and
     explaining how the change interacts with pre-existing behavior.
   - **Behavior changes & risks** — what users/callers will observe
     differently; what could break and where to look if it does.
3. **End the file with a quiz**: 5-8 questions, answers hidden until clicked.
   Target the parts most likely to surprise:
   - behavior that depends on existing code paths, not just new code
   - edge cases and failure modes the change handles (or deliberately doesn't)
   - "what happens if X" tracing questions
   Avoid trivia answerable by skimming the diff (file names, line counts).
4. **Hold the bar**: tell the user the rule is merge only after a perfect
   score. Offer to grade their answers in chat; for any miss, explain the
   right answer and point to the exact code.

## Rules

- Write questions from the reviewer's perspective ("will this break X?"), not
  the author's.
- If the change is genuinely trivial, say a quiz is overkill and give a
  three-sentence summary instead.
