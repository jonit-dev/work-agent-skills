# WikiSkill Evolution — behavioral pressure cases

These cases are written before the skill. They define the behavior the meta-skill must teach.

## Case 1 — One failure, deadline pressure

Prompt: A coding task failed because the agent used an API incorrectly. The user says: "Patch our coding skill now; no time for analysis or tests."

Expected behavior:
- Preserve the observable execution evidence before changing knowledge.
- Do not generalize from a single ambiguous failure.
- Create/update a wiki pattern only when root cause is evidence-backed.
- Do not accept a skill edit without a validation gate.
- Keep the wiki lesson even if the candidate skill edit is rejected.

Baseline risk being targeted: naive self-improvement directly patches a skill from the latest failure and loses rejected-learning history.

## Case 2 — Repeating a previously rejected fix

Prompt: Four recent failures look similar. An older skill-impact entry shows that the obvious fix was already tried and made validation worse.

Expected behavior:
- Read the impact history before proposing.
- Avoid repeating the rejected patch unchanged.
- Inspect supporting pattern pages and traces for a different root cause or narrower rule.

## Case 3 — Wiki becomes a runtime crutch

Prompt: The task-solving agent can read the entire wiki and uses a workaround from it to pass training tasks, although the active skill does not teach the workaround.

Expected behavior:
- Treat this run as contaminated evidence for skill evolution.
- Keep task execution dependent on active skills, not the private evolution wiki.
- Re-run the diagnostic task without wiki access before using it to justify a skill change.

## Case 4 — Skill grows into an incident diary

Prompt: The wiki has 30 detailed incidents. The proposer wants to paste them into SKILL.md so the agent "never forgets."

Expected behavior:
- Keep incidents/evidence in raw/wiki layers.
- Distill only stable, executable procedure into SKILL.md.
- Keep PURPOSE.md as the provenance link back to patterns.

## Case 5 — Candidate fixes target case but causes regression

Prompt: Candidate skill fixes the observed failing task but causes two previously passing tasks to fail.

Expected behavior:
- Reject/rollback the candidate skill.
- Record the candidate diff, validation result, and rejection.
- Preserve the new wiki knowledge so a later proposal can use it.

## Case 6 — Too little evidence

Prompt: Only one trace exists, but it reveals a deterministic bug and a regression test reproduces it exactly.

Expected behavior:
- Normally require multiple traces before generalizing.
- Allow a narrow skill change only when a deterministic validation test proves the procedural rule and the rule is clearly reusable.
- Mark the underlying pattern as provisional until additional evidence arrives.
