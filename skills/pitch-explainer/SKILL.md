---
name: pitch-explainer
description: >-
  Package the spec, prototype, and implementation notes of a finished piece of
  work into one self-contained document that gets reviewers to buy-in fast.
  Use when the user says "pitch doc", "explainer", "提案文档", "打包给评审",
  or needs approvals from people who weren't in the loop.
---

# Pitch & Explainer

Shipping needs buy-in. Reviewers start with the same unknowns the author
started with; experts want to see that the failure points they'd probe were
accounted for. Build the document that closes both gaps.

## Workflow

1. **Collect the artifacts.** Spec, prototype, implementation notes, the diff,
   demo media (GIF/screenshots) — whatever this session or the user can
   provide. Ask once if a key artifact is missing, then work with what exists.
2. **Lead with the demo.** The first thing a reviewer sees should be the
   thing working — a demo GIF, screenshot, or live link. Architecture comes
   after belief.
3. **Write one self-contained document** (single HTML file preferred, inline
   CSS/no network; markdown if the venue demands it), structured as:
   - **The demo** — show it working, first.
   - **The problem** — why this exists, in the reviewer's terms.
   - **What was built** — the shape of the solution, key decisions and why.
   - **Anticipated questions** — the failure points and edge cases an expert
     reviewer would probe, each answered honestly. Pull from the
     implementation notes' Deviations and Surprises if they exist.
   - **Limitations & open questions** — what this deliberately does not do.
4. **Make it droppable.** One file the user can drop into Slack or an issue:
   no build step, no external dependencies, readable on a phone.

## Rules

- Write for the reviewer's unknowns, not the author's pride — the goal is
  that their first question is already answered in the doc.
- Do not oversell: limitations stated up front build more trust than
  completeness claimed and disproven.
- Keep it short enough to read in five minutes; link out for depth.
