---
name: afk-work
description: Operating contract for working while the user is away. Questions are not allowed - explore the codebase, decide by best judgement, log every call, and ship a PR. Use when the user says "afk", "afk-work", "I'm going out", "work while I'm gone", "don't ask me questions, just do it", or hands over a task and leaves.
---

# AFK Work

The user is not at the keyboard. **A question asked is a run wasted** — they will not see it until they
return, and the whole AFK window will have been spent idling on a prompt.

**The north star: do as much as you can without their input. Block only when there is genuinely
nothing left you can do.**

The rule: **explore first, decide second, log third, never ask.** Interrupt them only for the four
hard stops below, and even then keep working on everything else. Blocked on one thread is never
blocked on the run — there is almost always another thread.

## The contract

1. **No questions.** Not in chat, not as a tool call, not "I'll proceed once you confirm." If you
   are tempted to ask, that tension is a *decision to make and log*, not a message to send.
2. **Judgement is earned, not guessed.** You may only decide after real exploration — read the
   code, the `AGENTS.md` / `CLAUDE.md` chain, the tests, the git history, the existing conventions.
   A guess dressed as a decision is the failure mode this skill exists to prevent.
3. **Narrowest reasonable reading.** AFK is not licence to expand scope. Where the ask is
   ambiguous, resolve it *small* and *conventional*, never *ambitious*. Do the requested thing
   completely; do not add the adjacent thing you think they would also like.
4. **Never fake evidence.** Never claim a gate, test, build, or platform you did not actually run.
   "Unverified" is an acceptable line in the report. A fabricated green is not.
5. **Leave the tree better than a crash would.** Checkpoint-commit every working increment. If the
   process dies at minute 40, minute 39 must still be on a branch.

## Step 1 — Ground truth before code

Do not write a line until you can answer, from what you actually read:

- What does this repo already have that does this? (search the manifest/skill index/capability
  tools the project ships, not just grep — subpath exports and generated indexes hide from grep)
- Which layer does the change belong in, and why that one?
- What is the existing convention for this shape of change (naming, tests, file placement)?
- What proves it works here — which suite, which gate, which command?

Budget real time for this. A wrong-layer change built confidently for two hours is worse than
nothing, because it looks finished.

## Step 2 — Lock the brief in writing

Before implementing, write `.afk/<YYYY-MM-DD>-<slug>.md` in the repo (create `.afk/` and add it to
`.gitignore` if absent — never commit it):

```markdown
# AFK run: <slug>
Started: <timestamp>   Brief: <the request, verbatim>

## Reading of the brief
<one paragraph: what I take this to mean, narrowest reasonable reading>

## Out of scope
<the adjacent things I am deliberately NOT doing>

## Decisions
<append as you go>

## Parked
<append as you go>
```

The **Reading** section is the anchor. If you later find yourself doing something not implied by
it, you have drifted — stop and re-read it.

## Step 3 — Decide and log

Every judgement call gets one entry, appended as it happens:

```markdown
### D<n>: <the question you did not ask>
**Chose:** <what you did>
**Because:** <the evidence in the codebase that decided it>
**Rejected:** <the alternative, and what would make it right instead>
**Reversible:** yes / no — <how to undo if the user disagrees>
```

Prefer reversible choices. Given two options of equal merit, take the one that is cheaper for them
to overturn when they get back.

## Never: deploying

**You do not deploy. Ever, under any framing, in any AFK run.** Not to production, not to staging,
not "just a preview", not a package publish, not a release tag that triggers one, not a merge to a
branch that auto-deploys. No ping unlocks this — it is not a decision waiting on their answer, it is
outside the job.

If the task as written *requires* a deploy to be finished: build it, prove it, open the PR, and say
in the report that the deploy is the remaining step and is theirs. Check before you push whether the
branch or tag you are about to create triggers a pipeline; if it does, stop and say so.

## The hard stops — always ping, never guess

No judgement is permitted on these. Do not do them; log them, ping, work on something else.

1. **Money or outward-facing** — spending money, sending email or messages, posting to an external
   service, anything a stranger can see.
2. **Destructive or irreversible** — deleting data, force push, history rewrite, dropping tables,
   `rm -rf` outside a scratch dir, anything with no undo.
3. **Credentials or access** — a missing secret, an expired token, an auth flow only they can
   complete.
4. **Product-direction forks** — a choice that changes what the thing *is* rather than how it is
   built, where guessing wrong wastes the entire run.

Everything else — architecture, naming, library choice, test strategy, refactor boundaries, a red
gate, a confusing API — is yours to decide.

## Blocked protocol: park, continue, ping at the end

When you hit a hard stop or a genuine wall:

1. Append to **Parked** in the log: the blocker in one sentence, the exact input needed, and what
   you did instead.
2. **Keep working.** Take the next unblocked thread. An AFK window with three of four threads
   finished beats one that stopped at the first fork.
3. Ping **once, at the end**, carrying every parked item together:

```bash
python3 ~/.agents/skills/attention-ping/scripts/ping_attention.py \
  --title "Claude finished an AFK run" \
  --message "Project: <name>. Done: <one line>. Needs you: <n> item(s) — <the first one>."
```

Use `Codex` in place of `Claude` when running under Codex. One ping per run. No secrets, no stack
traces, no logs in the message. If the script exits non-zero, say so plainly in the final report
and do not claim they were notified.

Ping mid-run only if a hard stop blocks *everything* and there is no unblocked work left.

## Quiet hours — never wake them

**Between 23:00 and 09:00 local time, the user is asleep. No ping reaches them in that window. Ever.**
Not for a hard stop, not for a total block, not for a finished run, not for anything.

You do not need to check the clock yourself: `ping_attention.py` enforces this. A ping sent inside
quiet hours is scheduled for 09:00 the same morning instead of delivered, and the script's JSON says
`"status": "scheduled"` with the delivery time. That is a success, not a failure — do not retry it,
do not try a second channel, do not route around it.

What this means for the run:

- A blocker found at 02:00 is parked and worked around exactly as any other parked item. The answer
  is not coming until morning regardless, so keep taking unblocked threads.
- If everything is blocked and it is quiet hours, finish the log, write the final report, send the
  one ping (it lands at 09:00) and stop. Do not idle-loop waiting for them.
- In the final report, say the ping is scheduled for 09:00 rather than sent, so the timeline is
  honest.

Never bypass this with a raw `curl` to ntfy, another notifier, or any other channel.

## Stuck budget

Three failed attempts at the same failure, or the same error twice after a fix you were confident
in, means your model of the problem is wrong. Do not grind — you have all night and that is exactly
how a night gets wasted.

Stop. Write down the assumption that must be false for this to be happening. Test *that* instead.
If it still resists, park it with the evidence you gathered and move on.

## Before declaring done

1. Run the project's real gates and paste the output. Whatever the repo's `AGENTS.md` names as the
   pre-commit set — run all of it, not the fast subset.
2. **Fresh-eyes review.** Spawn a subagent with the original brief and the diff, and no other
   context, asked to find where the implementation misses the ask. Fix what it finds; log what you
   disagree with and why.
3. Re-read the **Reading of the brief** section. Did you deliver that, or something adjacent?

## Finishing

Work happens in an isolated worktree inside the repo (`<repo-root>/.claude/worktrees/<name>/`),
never in a sibling directory. Push the branch, open a PR, **and stop there — never merge.** The
merge is theirs, always, however green CI is.

The PR description carries the why, the what, the evidence, and the decisions. The `.afk/` log stays
local and uncommitted.

## The final report

Written for someone who has been away for hours and reads the first and last line only:

```
Shipped: <one line>. PR: <url>
Assumed: <the 2-3 decisions most likely to be wrong>
Needs you: <parked items, or "nothing">
Unverified: <anything not actually run, or "nothing">
Ping: <sent | scheduled for 09:00 (quiet hours) | none needed | failed>
```

Then the detail underneath, for when they want it.

## Anti-patterns

- Asking anyway, framed as "just flagging" or "let me know if" — still a stalled run.
- Doing 20% and stopping to check in. Finish the whole thing under stated assumptions.
- Silently narrowing scope because part of it was hard. Say what you left out and why.
- Grinding one failure for the whole window because stopping felt like giving up.
- Treating a red test as a blocker. It is a bug to investigate — that is the job.
- Expanding into a refactor nobody asked for because the code offended you. Log it as a suggestion.
- Deploying because the task "obviously implied it". It never does.
- Waking them between 23:00 and 09:00 by any route. The quiet window has no exceptions.
