---
name: prd-manager
description: Answer PRD questions without reading PRDs — one table of every PRD's real progress, a drift and bloat audit, and one-command archiving. Use when asked where the work stands, which PRDs are in flight or stalled, whether a PRD is ready to close, why docs feel bloated, or to move a finished PRD into done/. Repo-agnostic and zero-install. Not for writing a PRD (prd-creator) or for the rules of keeping one honest (prd-lifecycle).
---

# prd-manager

Operational tooling for a directory full of PRDs: commands that print a screen, so an agent never loads hundreds of thousands of words to learn where things stand.

## How it fits with the other PRD skills

| Skill | Owns |
|---|---|
| [`prd-creator`](../prd-creator/SKILL.md) | writing the plan — phases, wiring ledger, tests, and the header fields below |
| [`pr-manager`](../pr-manager/SKILL.md) | PR titles, body shape, and auditing the open PRs |
| `prd-lifecycle` (a project skill, where one exists) | the rules for keeping a PRD honest |
| **`prd-manager`** | the machinery: reporting, auditing and archiving those PRDs |

`prd-creator` is the companion skill; install it next to this one
(`ln -s "$PWD/skills/prd-creator" ~/.claude/skills/prd-creator`) — without it there is nothing
emitting the fields below, which it writes and this skill rewrites:

```markdown
# PRD-<id> — <title>

**Status:** NOT STARTED          <- rewritten to DONE on close; audited against the folder
**Complexity:** 5 (MEDIUM)
**Depends on:** PRD-012

#### Phase 1: …
**Status:** NOT STARTED          <- each phase's own marker, rewritten on close
- [ ] step. proof: `npm test`   <- phase boxes: the only source of the percentage
## Acceptance criteria
- [ ] claim                      <- acceptance boxes: the last thing to go green
## Blocked on
- a missing device, credential or person — not a box, not progress
```

A PRD missing the header `**Status:**` still closes — `prd-close.mjs` inserts the field rather
than refusing — but until then the audit cannot tell whether it is drifting.

## The shape of a box

Six rules decide whether a PRD can be ticked at all. They are why the scripts count what they count, and `prd-audit.mjs` reports each one as a finding:

- **Every box names its proof inline** — a command, a CI job or a PR. A box nobody can verify is a
  box nobody is allowed to tick; the `no-proof` finding names every one.
- **No ceremony boxes.** An observed revert check, an independent reviewer's PASS, a written
  evidence record, an artificial negative control, a caller census: none is work, so none can ever be
  finished. They belong in the PR body or template; `ceremony-box` finds them by their wording.
- **Out of reach is not a box.** Hardware, credentials, other people and decisions that are not
  yours go under `## Blocked on`, one line each naming who or what unblocks it — not checkboxes,
  and never progress.
- **A decision deletes a moot box**, and the decision goes under `## Decisions` — what, who, when,
  why. Ticked work is never deleted and a finished PRD is never un-filed.
- **At most 3 phases and about 8 boxes.** Bigger work is several PRDs, each citing the one before.
- **A blocked-only PRD moves.** When the only thing left is `## Blocked on`, the file goes to
  `BLOCKED/<reason>/` (`prd-close.mjs --blocked <reason>`) so it stops reading as live work until
  the reason comes back. With any doable work left, it stays filed and lists its blocked items.

## Run it

Zero install, zero dependencies, plain Node. Works in any repository with a PRD directory —
discovery walks up from the working directory looking for `docs/PRDs`, `docs/prds`, `PRDs` or
`prds`; `PRD_ROOT=<dir>` overrides it and `PRD_PATTERN=<regex>` the `PRD-*.md` convention.

```sh
S=~/.claude/skills/prd-manager/scripts   # or wherever this skill is installed

node $S/prd-board.mjs                      # every open PRD: %, boxes, age, batch, status
node $S/prd-board.mjs --filter inflight    # open | inflight | stalled | noboxes | ready | blocked | blockedonly | done | all
node $S/prd-board.mjs --pr --limit 20      # + the open PR matched to each PRD (needs gh)
node $S/prd-board.mjs --json               # same data for a script

node $S/prd-audit.mjs                      # drift and bloat, most actionable first
node $S/prd-audit.mjs --all --older 45     # every item; staleness threshold in days
node $S/prd-audit.mjs --strict             # exit 1 on filing drift, for a gate

node $S/prd-close.mjs <prd file>           # dry run: verify 100%, show the move
node $S/prd-close.mjs <prd file> --yes     # rewrite the status line, git mv to done/
node $S/prd-close.mjs <prd file> --blocked release-credentials   # -> BLOCKED/<reason>/
node $S/prd-close.mjs <prd file> --reopen --reason "<what regressed>" --yes

node $S/prd-pr.mjs --create-labels --yes   # once per repository
node $S/prd-pr.mjs <prd file> --yes        # apply the progress label, after every push
node $S/prd-pr.mjs --all --yes             # every open PRD that has a PR
node $S/prd-body.mjs <prd file>            # the PR body, generated from the PRD
node $S/prd-body.mjs <prd file> --pr <n> --yes
```

## What each one is for

**`prd-board.mjs`** replaces "read the PRDs to see where we are." Progress comes from the PRD's
own checkboxes — ticked phase boxes bucket to 25/50/75, and 100% needs every acceptance box too —
so it cannot be talked into a number the file does not support. `age` is days since the last commit
touching the file. Boxes under `## Blocked on` and `## Decisions` are not work, so they never enter
the count; a PRD whose every remaining item is a `## Blocked on` line shows as **blocked-only**
(`--filter blockedonly`) rather than as work in flight.

**`prd-audit.mjs`** reports facts, never judgements, and names the fix for each:

| Finding | Why it matters |
|---|---|
| finished but still open | the archive move never happened |
| only blocked work left, not in `BLOCKED/<reason>/` | a live-looking file nobody in reach can advance |
| ceremony box | an observed ritual nobody can fail, so nobody can finish it either |
| box without `proof:` | nobody can tell when it is allowed to be ticked |
| over the size cap | more than 3 phases or about 8 boxes; split it |
| status line disagrees with the folder | the file says DONE and sits open, or sits in `done/` saying PROPOSED |
| duplicate PRD ids | the same number in several files; nobody can cite one |
| no phase checkboxes | progress cannot be reported, so the PRD never gets worked |
| compound acceptance criteria | a box conjoining independent claims can never be ticked |
| filed long ago, still at 0% | the plans nobody started, which every agent still reads |
| blocked and untouched | blockers outlive their condition |
| blocked PRD with no reason folder | the shape is `BLOCKED/<short-reason>/<prd>.md`; a loose file names no blocker |
| orphan evidence files | evidence nothing references — pure bloat |

**`prd-pr.mjs`** applies the progress label to the PRD's pull request and reports when more than
one open PR names the same PRD. **`prd-body.mjs`** generates that PR's body from the PRD — TL;DR,
the phase checklists as they actually stand, and what is still open.

**`prd-close.mjs`** is the archive move as one command. It refuses to close a PRD whose boxes are
open — listing exactly which ones, with line numbers, so "what is left" needs no read — then
updates **every** status field the PRD carries (the header `**Status:**`, a `**Progress:**` line
where one exists, each phase's own `**Status:**`, and a `**Closed:**` line stamping the date, the
short HEAD sha and the PR when `gh` can find one) and `git mv`s the file.

Closing under `--force` with boxes still open says exactly that instead of claiming a verification
that did not happen. Dry run until `--yes`; `--keep-batch` preserves the batch subdirectory;
`--no-status` moves the file and touches nothing. `--reopen` is the regression path, demands
`--reason`, and strips the `**Closed:**` stamp — reopening without a named regression deletes the
record that the work landed. `--blocked <reason>` is the other archive move, for a PRD whose every
reachable box is ticked and whose only open items sit under `## Blocked on`: it stamps the status
and `git mv`s the file to `BLOCKED/<reason>/`, where it stops reading as live work until whoever
or whatever the reason names comes back. It refuses when a box is still open (that is doable work,
so the file stays put) or when there is no `## Blocked on` list to wait on; `<reason>` is a short
slug (`requires-physical-device`, `release-credentials`, `owner-decision`). Fix the links the move
broke in the same commit. Status words are uppercase, matching the folder convention: `NOT STARTED`,
`PROPOSED`, `PARTIAL`, `IN PROGRESS`, `BLOCKED`, `DONE`, `REOPENED`.

## One PR per PRD

**Exactly one pull request per PRD, opened as a draft before phase 1 starts. Never one PR per
phase.** Phase-sized PRs split one plan's evidence across branches nobody re-reads, the review
happens on partial context, and the PRD's progress stops being visible anywhere. Open it with
`prd-body.mjs`'s checklist, push every phase to that same PR, tick the box in the PR body in the
same push that ticks it in the PRD, re-apply the label on every push, and `prd-close.mjs` the PRD
into `done/` in the PR that takes it out of draft. A second PR is right only when the work is
genuinely a different PRD: scope grew, so the new one cites the finished one. `prd-pr.mjs` reports
when more than one open PR names the same PRD.

## The progress label

One label at a time, chosen by verified boxes — never by lines written or files touched.

| Label | Meaning | Colour |
|---|---|---|
| `prd:25%` | phase 1 landed and verified | `#d73a4a` red |
| `prd:50%` | half the phase boxes landed and verified | `#e36209` orange |
| `prd:75%` | phases in, acceptance boxes still open | `#fbca04` yellow |
| `prd:100% — ready` | every phase and acceptance box ticked; PR out of draft | `#0e8a16` green |

`prd-pr.mjs` computes the bucket from the PRD and swaps the label on its PR, so a stale label
cannot survive a push. Re-apply on every push: a stale label is worse than none, because it is read
as a claim. Title conventions, the body shape and auditing the open PRs belong to `pr-manager`.

## How to use it in a session

1. `prd-board.mjs` before touching PRD work, and quote its numbers rather than re-deriving them.
2. `prd-audit.mjs` when the docs feel bloated, or before a release — it is ordered by
   actionability, not by count, so fix the top categories first.
3. `prd-pr.mjs` and `prd-body.mjs` after every push, so the label and the PR body match the PRD's
   boxes rather than the last time someone remembered; `prd-close.mjs` in the commit that finishes
   the work, never as a later tidy-up.
4. Never hand-count checkboxes or guess a percentage. If a number is wrong, the PRD's boxes are
   wrong; fix the boxes.

Every command prints what it saved: the words of the PRDs it covered against the size of its own
output — a board of the in-flight work is typically ~99% cheaper than reading those PRDs. Reach
for these before opening a PRD file, and open the file only once the board has told you which one.
