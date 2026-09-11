---
name: pr-manager
description: Naming and shaping pull requests so a reviewer understands one in ten seconds — the title convention, a TL;DR-first body with a done/missing checklist, one PR per PRD (never one per phase), and the progress label. Use when opening a PR, renaming or rewriting a thin one, auditing open PRs for title and shape drift, or deciding whether work needs a second PR. Not the PR lifecycle — branching, CI and merging belong to github-pr-workflow.
---

# pr-manager

A pull request is read by someone who was not in the room. This skill is about the parts that
decide whether they understand it: the title, the first three lines of the body, and whether
the work arrived as one PR or five.

Mechanics — branching, committing, watching CI, merging — belong to
[`github-pr-workflow`](../github-pr-workflow/SKILL.md).
Progress numbers come from [`prd-manager`](../prd-manager/SKILL.md), which reads the PRD's own
checkboxes.

## The title

```
<type>(<scope>): <imperative summary>          # no PRD
<type>(<scope>): PRD-<id> <imperative summary> # PRD-backed work
```

- **The PRD id goes in the title**, not only the branch or the body. It is how a reviewer
  finds the plan, how `prd-manager` matches the PR to its PRD, and how a search six months
  later finds why this happened.
- `<type>` is the conventional-commit verb: `feat`, `fix`, `docs`, `refactor`, `perf`,
  `test`, `chore`, `build`, `ci`.
- **Imperative, present tense.** "add the budget gate", not "added" or "adding".
- **Say the outcome, not the activity.** `fix(render): PRD-214 stop the frame crossing twice`
  beats `fix(render): PRD-214 changes to renderWorld`.
- **No phase suffixes.** `PRD-214 phase 2` in a title means the PRD was split across PRs —
  see below.
- Roughly 72 characters. A title that needs a colon-separated explainer is two titles.

| Bad | Why | Better |
|---|---|---|
| `updates` | says nothing | `fix(physics): PRD-170 stop the hot path allocating` |
| `PRD-227 work in progress` | status, not outcome; use draft state for that | `perf(core): PRD-227 cross the frame once` |
| `feat: PRD-331 phase 3 of 5` | one PRD, five PRs | `feat(website): PRD-331 the site is a workspace app` |
| `fix: resolve the issue where the thing breaks on some devices` | vague and over-long | `fix(android): PRD-213 bound GPU memory on Mali` |

## The body

Whoever opens it should learn what this is for, what is done, and what is not — before
scrolling. Keep it short: a body nobody finishes is a body nobody read.

```markdown
**TL;DR** — one sentence: what this changes and why it matters.

75% by the PRD's own boxes: 2/2 phases (5/5 boxes), 2/4 acceptance criteria. PRD: `path`.

## Phases
### Phase 1 — name  — 3/3
- [x] …
## Acceptance criteria
- [x] …
- [ ] …
## Still open
- what is not done, in plain words
```

Generate it rather than typing it, so the PR and the PRD cannot drift apart:

```sh
P=~/.claude/skills/prd-manager/scripts
node $P/prd-body.mjs <prd file>                    # print it
node $P/prd-body.mjs <prd file> --pr <n> --yes     # write it to the PR
```

Rules that matter more than the template:

- **TL;DR first, always.** Not a heading, not a table of contents, not a wall of context.
- **Every claim of evidence names the command and its result.** "tests pass" is not evidence;
  `pnpm test` → 2463 passed is.
- **"Still open" is not optional.** A PR that lists only what works reads as finished when it
  is not, and the reviewer finds out during merge.
- **No screenshots of text.** Paste the text.
- One Mermaid diagram when a diagram beats a paragraph; none when it does not.

## One PR per PRD

**Exactly one pull request per PRD, opened as a draft before phase 1 starts.**

Phase-sized PRs are the failure this rule exists to prevent. They split one plan's evidence
across five branches, so no branch shows the whole picture, the review happens five times on
partial context, and the PRD's progress stops being visible anywhere. Merging them in order
becomes its own coordination problem, and the last one always carries a rebase nobody wanted.

- Open the draft early, with the PRD's checklist in the body.
- Push each phase to that same PR as it lands.
- Tick the box in the PR body in the same push that ticks it in the PRD. A PR box ticked
  ahead of the PRD is the same lie as a claimed gate.
- Take it out of draft when the last acceptance box is ticked, and archive the PRD to
  `done/` in that same PR.

A second PR is right when the work is genuinely a different PRD — scope grew, so a new PRD
cites the finished one. It is never right merely because the first PR got large.

`prd-pr.mjs` reports when more than one open PR names the same PRD.

## The progress label

One label at a time, red through yellow to green, chosen by verified boxes — never by lines
written or files touched.

| Label | Meaning | Colour |
|---|---|---|
| `prd:25%` | phase 1 landed and verified | `#d73a4a` red |
| `prd:50%` | half the phase boxes landed and verified | `#e36209` orange |
| `prd:75%` | phases in, acceptance boxes still open | `#fbca04` yellow |
| `prd:100% — ready` | every phase and acceptance box ticked; PR out of draft | `#0e8a16` green |

```sh
P=~/.claude/skills/prd-manager/scripts
node $P/prd-pr.mjs --create-labels --yes    # once per repository
node $P/prd-pr.mjs <prd file> --yes         # label this PRD's PR, after every push
node $P/prd-pr.mjs --all --yes              # every open PRD that has a PR
```

Re-apply on every push. A stale label is worse than no label: it is read as a claim.

## Audit the open PRs

```sh
node ~/.claude/skills/pr-manager/scripts/pr-audit.mjs          # title and shape drift
node ~/.claude/skills/pr-manager/scripts/pr-audit.mjs --json
```

It reports, for every open PR: titles missing a conventional-commit type, titles carrying a
phase suffix, PRDs with more than one open PR, bodies with no TL;DR or no "still open"
section, bodies that are effectively empty, and drafts nobody has pushed to in weeks.

## Checklist

- [ ] Title: `<type>(<scope>): PRD-<id> <imperative outcome>`, under ~72 characters
- [ ] Body opens with a one-sentence TL;DR
- [ ] Done and still-open are both listed, generated from the PRD
- [ ] Exactly one open PR for this PRD
- [ ] Progress label re-applied on this push
- [ ] Draft until the last acceptance box is ticked
