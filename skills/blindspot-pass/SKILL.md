---
name: blindspot-pass
description: >-
  Surface the user's unknown unknowns before they start work in an unfamiliar
  area (new part of a codebase, new domain, new tool). Produces a read-only
  briefing of blindspots plus concrete advice on how to prompt better. Use when
  the user says "blindspot pass", "盲区扫描", "unknown unknowns", or asks what
  they don't know before diving in.
---

# Blindspot Pass

Help the user discover their unknown unknowns before work starts. This is a
read-only pass: do not modify any files.

## Workflow

1. **Anchor on the user's starting point.** If not already clear from the
   conversation, ask once — a single short message, at most three
   sub-questions — about their experience with this problem and codebase,
   what they have already decided, and what they plan to do next.
2. **Explore the territory.** Search the relevant code, docs, git history, and
   (if the domain is unfamiliar) the web. Look specifically for things the
   user did not mention in their description of the task.
3. **Report blindspots**, organized as:
   - **Questions you didn't know to ask** — decisions hidden in this area
     (existing conventions, invariants, feature flags, edge cases).
   - **What "good" looks like** — quality bars, reference implementations, or
     prior art the user should calibrate against.
   - **History and potholes** — past attempts, known pitfalls, TODO/FIXME
     landmines, coupling that will bite.
   - **Domain concepts** — if the domain is new to the user, teach the 3-5
     concepts they need to evaluate results (not an encyclopedia).
4. **End with "how to prompt me better":** 3-6 concrete things the user should
   specify in their next prompt now that these blindspots are visible.

## Rules

- Prioritize blindspots that would change the user's approach; skip trivia.
- Cite files and line numbers so claims are checkable.
- If the area turns out to be simple with few blindspots, say so plainly
  instead of inventing findings.
