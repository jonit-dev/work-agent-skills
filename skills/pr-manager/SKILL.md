---
name: pr-manager
description: Shape a pull request so a person who was not in the session understands it in ten seconds — plain-language title, a body that opens with "What is this PR about?" and "Why does it matter?", done and still-open lists, one PR per PRD, the progress label, and how to write PR comments (push updates, review replies, CI notes). Use when opening a PR, rewriting a body that reads as jargon, writing or replying to a PR comment, auditing open PRs, or deciding whether work needs a second PR. Not the PR lifecycle (branching, CI, merging) — that is github-pr-workflow.
---

# pr-manager

The reader was not in your session. They do not know your function names. They decide in ten
seconds whether to keep reading. So the body opens with two questions, answered in plain words:

1. **What is this PR about?**
2. **Why does it matter?**

Code names, `file:line`, measurements and PRD checkboxes come after. Never before.

Lifecycle (branch, CI, merge): [`github-pr-workflow`](../github-pr-workflow/SKILL.md).
Progress numbers: [`prd-manager`](../prd-manager/SKILL.md).

## Body template

Drop a section only when it is empty.

```markdown
## What is this PR about?
1–3 sentences. What does the game or engine do differently after this PR?

## Why does it matter?
The problem, who feels it, what it costs. One number, with its unit and what it measures.

## What changed
3–6 bullets. One behavior each.

## How I checked it
Command → result. Anything not run: "Not run: <why>".

## Still open
What is not done. A checklist if there are several items.

## Where to look first        (only if the diff is over ~300 lines)
2–3 files, one line each on why.

<!-- prd-progress:start --> … collapsed <details> block, generated … <!-- prd-progress:end -->
```

### Ten-second test

Read only the first section to someone outside the project. If they cannot say what changed,
rewrite it. The opening **fails** if it has:

- a `file:line`, or a function or constant name the reader has not met
- more than one number, or a number with no unit
- a percentage that measures the PR's own paperwork ("25% by the PRD's boxes")
- a sentence over 25 words, or an idea you named yourself during the session

### Example (a terrain-renderer PR)

Before: the opening is a 90-word run of `TerrainTiles`, `LOD_TRANSITION_FRAMES = 3`,
`updateLodTransitionGeometry (world-tiles.ts:1292)`, `normalAt`, `setY`, then "25% by the PRD's
own boxes: 0/3 phases (2/6 boxes)". Nobody can tell what the PR is for.

After (facts from the PR's own evidence lines):

```markdown
## What is this PR about?
Terrain tiles fade from one detail level to the next over 3 frames. Until now the CPU rewrote
every vertex of the tile on each of those frames. This PR moves the fade to the GPU, using
Three.js morph targets, so the CPU does no per-vertex work during a fade.

## Why does it matter?
Each fade frame cost the CPU about 1.2–2.4 ms per 65×65 tile (mean of 100 frames). Several
tiles fade at once while the player walks, and that cost lands in the frame budget.

## What changed
- A fade frame now reads 0 heights and 0 normals from the terrain data (was 4,225 + 25,350).
- The old CPU blend stays as the reference the new path is tested against.
- Tile memory accounting and cleanup cover the morph data.

## How I checked it
- `pnpm exec vitest run packages/core/__tests__/world-terrain-tiles.spec.ts …` → 124 passed.
- The GPU result matches the CPU blend within 1 mm in unit tests.
- Not run: any GPU or visual comparison. Not run: the desktop host.

## Still open
- [ ] Terrain walk on a real GPU. The playtest used SwiftShader (software), so it proves nothing.
- [ ] Same walk on the desktop host.
- [ ] Choose the detail level by on-screen error (phase 3).
```

The code names stay available. Put them in "Where to look first" or a line comment on the diff.

## Writing rules (body, comments, commits)

1. **Answer first.** Sentence one is the point, not the context.
2. **Short, active sentences.** Max 25 words. One idea each. "The CPU rewrites the vertices", not
   "vertex rewriting is performed".
3. **Define or drop internal names.** First use: name plus a few words. If the reader cannot use
   the name, remove it.
4. **A number needs a unit and a meaning.** "1.2 ms per fade frame per tile", not "25,000".
5. **Never claim a gate you did not run.** "Not run" is a valid line. A fake green is not.
6. **Cut AI filler.** No "This PR aims to", "comprehensive", "robust", "leverage", "ensure",
   "various improvements", "I hope this helps", hedge stacks ("could potentially"), closing
   recaps. Do not add opinion or experience the work does not show. Catalog:
   <https://github.com/conorbronsdon/avoid-ai-writing>.
7. **Light formatting.** At most one bold phrase per section, few dashes, no emoji headers.
8. **Nothing machine-local**: no `/home/<user>/…`, `/tmp/…` log paths, session URLs, tokens. Strip `Co-Authored-By` and generated-by trailers unless the repo asks.
9. **Mermaid only**, never ASCII. Paste text; do not screenshot it.

**Gather before you write.** Never write from memory of the session. Read the change:

```sh
git log --oneline origin/<base>..HEAD
git diff --stat origin/<base>..HEAD
```

Collect the PRD or issue ids, the gate output you ran, and any capture or before/after image.
List every PRD or issue the PR touches, with what happens to it: closes, advances, unblocks.

**Screenshots** (anything with pixels): commit the image where the PR can reach it, or attach it
with the API and use the returned URL. Use a table and caption what to look at.

```markdown
| Before | After |
|---|---|
| ![before](<url>) | ![after](<url>) |
```

**Mermaid** renders natively on GitHub. Use one when order or structure is the point: a new
sequence between processes, a state machine, a pipeline with a moved stage, ownership that moved
between layers. Skip it for a one-function fix. Label nodes with real names, keep it under about
12 nodes, and put it next to the prose it explains.

Write the body to a scratch file and use `--body-file`; `--body` strings break fences.

```sh
gh pr create --draft --base <base> --title "<title>" --body-file <scratch>/pr-body.md
gh pr view <n>        # read it back
```

**The generated PRD block.** `prd-body.mjs` prints only the collapsed progress block. It never
writes the opening. With `--pr <n> --yes` it replaces just the text between its markers, so your
prose survives every regeneration.

```sh
node ~/.claude/skills/prd-manager/scripts/prd-body.mjs <prd file> --pr <n> --yes
```

Long per-box evidence (log paths, full command lines) stays in the PRD. The PR links to it.

## Title

```
<type>(<scope>): <imperative outcome>            # no PRD
<type>(<scope>): PRD-<id> <imperative outcome>   # PRD-backed
```

- `<type>`: `feat fix docs refactor perf test chore build ci`.
- PRD id **in the title**, so a reviewer can find the plan.
- Imperative, present tense. Name the **outcome**, in words a teammate outside the area knows.
- No phase suffix. About 72 characters. It becomes the squash subject: it must make sense in a year.
- Keep it true. When scope changes, rename the PR. A title that says "measure" on a PR that
  ships a feature is a lie.

| Bad | Better |
|---|---|
| `updates` | `fix(physics): PRD-170 stop the hot path allocating` |
| `PRD-214: measure terrain LOD blend CPU work` (PR now ships the GPU fade) | `perf(core): PRD-214 fade terrain detail levels on the GPU` |
| `feat: PRD-331 phase 3 of 5` | `feat(website): PRD-331 make the site a workspace app` |
| `refactor(core): updateLodTransitionGeometry uses setY` | `perf(core): PRD-214 stop rewriting terrain vertices on the CPU` |

## Comments

A comment is read alone, in a notification. Every comment: **answer first**, **one topic**,
**reply in the thread**, **cite evidence** (commit SHA, command and result, CI run link), never
repeat the body (edit the body instead), never edit another person's comment.

| Moment | Shape |
|---|---|
| Push with new work | `Pushed <sha>: <what changed since the last push>. Next: <one thing>.` Skip if a reviewer needs nothing new. |
| Reply to a review comment | `Fixed in <sha>: <how, one line>.` · `Not changing: <reason>.` · `Question: <q>`. |
| CI failure | `<job> failed: <cause>. Fix: <what>. Run: <link>.` If the failure is not yours, say why. |
| Evidence or screenshots | Caption what to look at, then the table. |
| Blocked | `Blocked on <specific thing> from <who>. Resuming when <condition>.` |
| Ready | `Ready: all boxes ticked. Run: <gates>. Not run: <gates>.` |
| Decision needed | `Keep X (recommended) or switch to Y? X: … Y: …` Recommendation first. |

```sh
gh pr comment <n> --body-file <scratch>/comment.md
gh api repos/{owner}/{repo}/pulls/<n>/comments/<comment_id>/replies -f body="Fixed in abc1234: …"
```

Resolve a thread only after the fix is pushed and you said so in the thread. A judgment-call
thread: let the reviewer resolve it.

## One PR per PRD

Exactly one PR per PRD, opened as a draft at the first commit. Never one per phase: it splits
the evidence, repeats review on partial context, and the last PR carries a rebase nobody wanted.

- Push each phase to the same PR. Tick the PR box in the same push that ticks the PRD box.
- Leave draft when the last acceptance box is ticked. Move the PRD to `done/` in that PR.
- A second PR is right only for a different PRD. A big first PR is not a reason.

## Progress label

One label, chosen by verified boxes, never by lines written. A repository's own scheme wins
(for example a `prd:progress` script in the repo). Default scheme: `prd:25%` red, `prd:50%` orange,
`prd:75%` yellow, `prd:100% — ready` green. Re-apply on every push; a stale label reads as a claim.

```sh
node ~/.claude/skills/prd-manager/scripts/prd-pr.mjs <prd file> --yes
```

## Audit

```sh
node ~/.claude/skills/pr-manager/scripts/pr-audit.mjs
```

Reports titles with no type or with a phase suffix, PRDs with several open PRs, bodies with no
"what is this about" opening, openings full of code references, no "still open", near-empty
bodies, stale drafts.

## Checklist

- [ ] Title: type, scope, PRD id, imperative outcome, true to what the PR now ships
- [ ] Opens with "What is this PR about?" then "Why does it matter?" and passes the ten-second test
- [ ] Each evidence line has a command and result. Un-run gates say "Not run"
- [ ] "Still open" present. PRD block collapsed at the bottom
- [ ] One open PR for this PRD. Label re-applied. Draft until the last box
- [ ] Read back with `gh pr view`
