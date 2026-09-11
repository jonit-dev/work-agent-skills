---
name: feature-mining-sandbox-validation
description: Prove a framework feature actually works by building a tight mini game against it in a clean sandbox, driving it with a playtest, and looking at the capture. Use when asked to validate mined or newly-landed features, to check that a PRD's feature really shipped, to build a sandbox game that exercises a capability, or to decide which PRDs are done enough to archive.
---

# Feature-mining sandbox validation

A feature is not proven by the tests that shipped with it. Those run inside the repository, where
the source is on disk and the author's assumptions are ambient. This skill proves a feature the way
a user meets it: from a separate project that installed the packages, in a game that needs the
feature to be playable, with a human-readable picture at the end.

**The loop is: install clean → build a mini game whose *rule* is the feature → assert with a
playtest → look at the capture → mutate to red → write down what broke.**

## When to use this

- "Does feature X actually work?" / "validate the mined features" / "prove PRD-N shipped"
- Deciding which PRDs are finished enough to move to `done/`
- Any time a capability has unit tests and no consumer

Do not use it for a feature that has no observable behavior — a refactor, an internal rename, a
build-system change. There is nothing to play.

## Step 1 — Find out what actually exists

**Never trust the PRD's Status line.** They go stale; a batch can read `PROPOSED, nothing has been
executed` on work that shipped weeks ago, and can equally name features that were never built.

Check the export surface, not the prose:

```sh
grep -oE '^export \{ [A-Za-z0-9_, ]+ \}' packages/core/src/index.ts | tr ',' '\n' | sort -u
```

Then, for each feature you were asked about, confirm it by symbol. A PRD batch about grass, oceans,
fluids and GI may have shipped none of them. Say so plainly and early — a demo cannot be written
against a capability that does not exist, and discovering that after building the scaffold wastes
the whole run.

Write the list down before building anything: **feature → PRD → does the symbol exist**.

## Step 2 — Install like a user, outside the repository

The sandbox must not inherit the monorepo. No workspace, no `AGENTS.md` chain, packages from
tarballs with `dist` only:

```sh
pnpm sandbox --genre <genre> --name <game-name> --template minimal
```

One game per folder. If a game reads `packages/*/src`, the run proves nothing about what a user's
agent can reach.

## Step 3 — Build a mini game, not a feature gallery

This is the part that gets done wrong. A scene with one of everything in it is a tech demo, and a
tech demo hides exactly the failures you are looking for, because nothing in it has to work for
anything else to work.

**Make the feature the game's rule.** The test of a good subject:

> If this feature silently returned a constant, would the game still be playable?

If yes, pick a different game. Some shapes that pass:

| Feature | A rule that needs it |
| --- | --- |
| Scene ray query / BVH | Stealth — the shadow you hide in *is* the trace, and the same query decides whether you are caught |
| Billboarding + sprite atlas | Anything with sprite enemies — they must face you and animate or the game is unreadable |
| Camera shake | Impact feedback on a hit you scored |
| Sky / atmosphere model | A timing or visibility rule read from the model's own output |
| Compute lifetime | A simulated field the player moves through or reads |

Keep it to one screen and one loop with a **win and a loss**. `outcome` should be a literal string
(`"playing"`, `"won"`, `"caught"`) so a scenario can compare against it rather than infer.

Expose one state value per feature, and make each one **monotonic or gated**:

- A looping index (`frameIndex`) is not assertable — two samples land on the same frame and read as
  "nothing happened". Count *advances* instead.
- A value that is true from frame one (a billboard's facing) is not assertable either. Gate the
  sample on something the scenario causes — the first kill, the first metre crossed — so it reads
  zero in the before-snapshot.

## Step 4 — Drive it with a playtest and let the harness argue

```sh
pnpm exec threenative-playtest --scenario playtests/<name>.playtest.json \
  --browser-recipe webgpu --headed \
  --server-command "pnpm dev --host 127.0.0.1 --port $PORT --strictPort"
```

Two things that will bite:

- **Do not export `PORT`.** The runner substitutes `$PORT` itself. A shell that expands it first
  starts the server on one port while the runner polls another, and every scenario fails with
  `TN_PLAYTEST_SERVER_FAILED` for a reason that has nothing to do with the game.
- **`TN_PLAYTEST_ASSERTION_TRIVIAL` is the harness doing its job.** It means the assertion was
  already satisfied before the scenario ran. Do not reach for the triviality opt-out; fix the
  measurement. Expect it to reject several of your first-draft assertions, and expect it to be
  right.

Also expect `atSteps` to accept only `equals`/`textIncludes` — a threshold at a labelled step needs
a state value that carries the threshold, not a richer assertion.

## Step 5 — Look at the capture. This is not optional.

Every green run so far in this repository's history has been capable of hiding a broken feature.
Screenshot the frame and **read it**:

- Is the feature visible at all? A GPU-traced contact patch fired straight up sits exactly under the
  caster's own footprint, where the caster hides it — the query runs and looks like it does not.
  Slant the ray and it becomes a shadow you can see.
- Is the scene washed out, or so dark the subject is invisible? Both happened here, both hid the
  thing being proven, and neither showed up in any assertion.
- Capture **mid-round**, not after the win. A screenshot of an empty arena proves nothing.

If a still cannot show the feature, capture two frames and compare them.

## Step 6 — Mutate to red, one control per claim

A green run alone is not evidence. For each feature, break exactly that feature, re-run, paste the
red, then revert:

```
remove the Billboard3D update  -> billboardFacingWorst 0.9999 -> 0.9506, exit 1
remove the field's ctx.add     -> computeSteps stayed 0, STAGNATED, exit 1
remove the tapped listener     -> outcome never left "playing", exit 1
```

Keep the original file so the revert is exact:

```sh
cp src/scenes/Play.ts /tmp/Play.ts.orig
# ...mutate, run, record...
cp /tmp/Play.ts.orig src/scenes/Play.ts
```

## Step 7 — Write down the sharp edges

The bugs this loop finds are usually not "the feature is broken". They are conditions the in-repo
example never reaches, whose error message names something other than the cause. File them where a
cold agent will hit them, with the failing output quoted, and say plainly whether you are committing
to a repair or just naming the boundary.

Each game's `README.md` gets a table: **mined feature → PRD → what the game asks of it → the state
value the proof reads.** That table is the deliverable a reader trusts; the commit message carries
the green counts and every red control with its exit code.

## Step 8 — Only then, archive the PRD

A landed implementation is not a finished PRD, and a passing web run does not close a device
criterion. Move a PRD to `docs/PRDs/done/` when its capability is on the public surface and reached
by a real consumer — and rewrite its Status line to name what is still `UNVERIFIED` rather than
deleting the caveat. `git mv` it in the commit that finishes it, then repoint the links and run
`pnpm check:docs`.

## The failure this whole loop exists to prevent

Unit tests pass, the PRD says shipped, and the first user's agent hits an opaque WGSL type error, or
a snapshot silently packed at the wrong coordinates with a correct-looking `triangleCount` and no
error raised anywhere. Both of those were live in this repository, both were invisible from inside
it, and both took one mini game and one screenshot to find.
