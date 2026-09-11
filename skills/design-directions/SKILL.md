---
name: design-directions
description: >-
  Generate several deliberately divergent single-file HTML prototypes with fake
  data so the user can react to designs before any real implementation.
  Use when the user wants design options, a mockup to react to, says
  "design directions", "出几个设计方向", "做个原型看看", or can only judge a
  design by seeing it.
---

# Design Directions

The user has "unknown knowns": criteria they can only articulate when they see
something. Give them things to react to, cheaply, before touching real code.

## Workflow

1. Confirm scope from context: what surface is being designed (page, panel,
   component, report) and what data it shows. Do not ask more than one
   clarifying question; guessing reasonably is part of the point.
2. Build **4 deliberately different directions** by default (fewer only if the
   user asked). Different means different layout philosophy, density,
   hierarchy, or interaction model — not one design with four color schemes.
3. Deliver as self-contained HTML: inline CSS/JS, realistic fake data
   hardcoded in, no build step, no network calls. Default to one file per
   direction (a single file with a direction switcher only if the user asks).
   Write files to a scratch directory (`./design-directions/`), never into the
   real app; do not commit them, and if this is a git repo add the directory
   to `.git/info/exclude`.
4. Name each direction with a short memorable label and one sentence on the
   idea behind it, so the user can say "the second one, but denser".
5. Tell the user how to view them (e.g. `open design-directions/*.html`) and
   ask them to react: what to keep, what to kill. Then iterate on the chosen
   direction, or combine elements on request.

## Rules

- Do not modify application code, add dependencies, or wire up backends at
  this stage.
- Use realistic fake data (plausible names, numbers, edge-case lengths) —
  lorem ipsum hides layout problems.
- Push at least one direction beyond the user's stated taste; the point is to
  discover what they didn't know they wanted.
