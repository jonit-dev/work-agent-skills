---
name: prd-manager
description: Answer PRD questions without reading PRDs — one table of every PRD's real progress, a drift and bloat audit, and one-command archiving. Use when asked where the work stands, which PRDs are in flight or stalled, whether a PRD is ready to close, why docs feel bloated, or to move a finished PRD into done/. Repo-agnostic and zero-install. Not for writing a PRD (prd-creator) or for the rules of keeping one honest (prd-lifecycle).
---

# prd-manager

Operational tooling for a directory full of PRDs. Three commands read every PRD and print
a screen, so an agent never loads hundreds of thousands of words to learn where things stand.

## How it fits with the other PRD skills

| Skill | Owns |
|---|---|
| [`prd-creator`](../prd-creator/SKILL.md) | writing the plan — phases, wiring ledger, tests, and the header fields below |
| `prd-lifecycle` (a project skill, where one exists) | the rules for keeping a PRD honest |
| **`prd-manager`** | the machinery: reporting, auditing and archiving those PRDs |

`prd-creator` is the companion skill in this repository. Install it alongside this one —
without it there is nothing emitting the fields below in the first place:

```bash
ln -s "$PWD/skills/prd-creator" ~/.claude/skills/prd-creator
ln -s "$PWD/skills/prd-manager" ~/.claude/skills/prd-manager
```

They interlock through the fields a PRD carries. `prd-creator` emits them, this skill reads
and rewrites them:

```markdown
# PRD-<id> — <title>

**Status:** NOT STARTED          <- rewritten to DONE on close; audited against the folder
**Complexity:** 5 (MEDIUM)
**Depends on:** PRD-012

#### Phase 1: … 
**Status:** NOT STARTED          <- each phase's own marker, rewritten on close
- [ ] step                       <- phase boxes: the only source of the percentage
## Acceptance criteria
- [ ] claim                      <- acceptance boxes: the last thing to go green
```

A PRD written by `prd-creator` is trackable here the moment it exists. A PRD missing the
header `**Status:**` still closes — `prd-close.mjs` inserts the field rather than refusing —
but until then the audit cannot tell whether it is drifting.

## Run it

Zero install, zero dependencies, plain Node. Works in any repository with a PRD directory —
discovery walks up from the working directory looking for `docs/PRDs`, `docs/prds`, `PRDs`
or `prds`, and `PRD_ROOT=<dir>` overrides. `PRD_PATTERN=<regex>` overrides the `PRD-*.md`
filename convention.

```sh
S=~/.claude/skills/prd-manager/scripts   # or wherever this skill is installed

node $S/prd-board.mjs                      # every open PRD: %, boxes, age, batch, status
node $S/prd-board.mjs --filter inflight    # open | inflight | stalled | noboxes | ready | blocked | done | all
node $S/prd-board.mjs --pr --limit 20      # + the open PR matched to each PRD (needs gh)
node $S/prd-board.mjs --json               # same data for a script

node $S/prd-audit.mjs                      # drift and bloat, most actionable first
node $S/prd-audit.mjs --all --older 45     # every item; staleness threshold in days
node $S/prd-audit.mjs --strict             # exit 1 on filing drift, for a gate

node $S/prd-close.mjs <prd file>           # dry run: verify 100%, show the move
node $S/prd-close.mjs <prd file> --yes     # rewrite the status line, git mv to done/
node $S/prd-close.mjs <prd file> --reopen --reason "<what regressed>" --yes
```

## What each one is for

**`prd-board.mjs`** replaces "read the PRDs to see where we are." Progress comes from the PRD's
own checkboxes — ticked phase boxes bucket to 25/50/75, and 100% needs every acceptance box too —
so it cannot be talked into a number the file does not support. `age` is days since the last commit
touching the file.

**`prd-audit.mjs`** reports facts, never judgements, and names the fix for each:

| Finding | Why it matters |
|---|---|
| finished but still open | the archive move never happened |
| status line disagrees with the folder | the file says DONE and sits open, or sits in `done/` saying PROPOSED |
| duplicate PRD ids | the same number in several files; nobody can cite one |
| no phase checkboxes | progress cannot be reported, so the PRD never gets worked |
| compound acceptance criteria | a box conjoining independent claims can never be ticked |
| filed long ago, still at 0% | the plans nobody started, which every agent still reads |
| blocked and untouched | blockers outlive their condition |
| blocked PRD with no reason folder | the shape is `BLOCKED/<short-reason>/<prd>.md`; a loose file names no blocker |
| orphan evidence files | evidence nothing references — pure bloat |

**`prd-close.mjs`** is the archive move as one command. It refuses to close a PRD whose boxes are
open — listing exactly which ones, with line numbers, so "what is left" needs no read — then
updates **every** status field the PRD carries and `git mv`s the file:

- header `**Status:**` → `DONE — <date>. Every phase and acceptance box verified.` (inserted
  under the title when the PRD has no such field)
- header `**Progress:**`, where one exists → `100% — all phases and acceptance criteria verified.`
- each phase's own `**Status:**` still reading `NOT STARTED` / `IN PROGRESS` / `PARTIAL` → `DONE`
- a `**Closed:**` line stamping the date, the short HEAD sha and the PR, when `gh` can find one

Closing under `--force` with boxes still open says exactly that instead of claiming a verification
that did not happen. Dry run until `--yes`; `--keep-batch` preserves the batch subdirectory;
`--no-status` moves the file and touches nothing. `--reopen` is the regression path, demands
`--reason`, and strips the `**Closed:**` stamp — reopening without a named regression deletes the
record that the work landed.

Status words are uppercase, matching the folder convention: `NOT STARTED`, `PROPOSED`, `PARTIAL`,
`IN PROGRESS`, `BLOCKED`, `DONE`, `REOPENED`.

## How to use it in a session

1. `prd-board.mjs` before touching PRD work, and quote its numbers rather than re-deriving them.
2. `prd-audit.mjs` when the docs feel bloated, or before a release. Fix the top categories first —
   they are ordered by actionability, not by count.
3. `prd-close.mjs` in the commit that finishes the work, never as a later tidy-up.
4. Never hand-count checkboxes or guess a percentage. If a number is wrong, the PRD's boxes are
   wrong; fix the boxes.

## Token cost

Every command prints what it saved: the words of the PRDs it covered against the size of its own
output. A board of the in-flight work is typically ~99% cheaper than reading those PRDs. That is
the whole point — reach for these before opening a PRD file, and open the file only once the board
has told you which one.
