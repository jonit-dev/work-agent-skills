# WikiSkill Evolution — operating contract

This is a production-oriented adaptation of Tang et al. (2026), "WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution."

## Workspace

```text
repo/
  .wikiskill/
    raw/                    # immutable observable execution records
    raw-manifest.jsonl      # hashes for tamper detection
    wiki/
      index.md              # one-line catalog of patterns
      log.md                # chronological evolution notes
      skill-impact.md       # candidate diff + validation + decision
      patterns/             # one markdown page per durable pattern
    candidates/             # optional scratch area for proposed changes
  .agents/skills/           # recommended project-local executable skills
```

The three conceptual layers must remain separate even if a repository uses different physical paths.

## Layer contracts

### Raw layer

A raw record answers: what task was attempted, what observable actions occurred, what evidence came back, and what was the outcome?

Good evidence includes commands, tool calls, error messages, test/CI output, changed files, benchmark numbers, and the final externally visible result. Do not synthesize lessons here. Never rewrite a captured trace; add a new trace when new evidence appears.

### Wiki layer

The wiki is the compounding knowledge substrate. It should explain recurring success/failure patterns and preserve intervention history.

`index.md` is a compact catalog. Each entry should make relevance obvious by stating the problem, likely root cause, and current fix or mitigation.

Pattern pages should usually stay around 10–30 lines. Prefer updating an existing pattern to creating a near-duplicate.

`skill-impact.md` is objective history: what was proposed, what changed, what validation said, and whether it was accepted.

### Skills layer

Skills contain executable procedure only. A skill should not become a chronology of incidents. Each evolved skill should have a `PURPOSE.md` mapping it to motivating wiki patterns and an evolution history.

## Evolution cycle

### 0. Baseline

Before changing a skill, establish the current validation result. For software work this may be a regression suite, held-out replay set, CI status, benchmark, or scored task set.

### 1. Evidence generation

Run representative tasks with active skills. The task-solving run must not read the private wiki for answers. This preserves diagnostic value: failures expose what the active skill actually fails to teach.

### 2. Trace selection

Default sample budget per cycle: at most 8 traces, with up to 5 failures and up to 3 successes. Failures expose gaps; successes protect working behavior from regressions.

### 3. Wiki maintenance

For each sampled trace:

1. Inspect actual observable actions and outputs.
2. Compare passing and failing executions.
3. Identify action patterns, not just error strings.
4. Check whether an active skill was followed and whether it helped.
5. Update the smallest number of existing pattern pages possible.
6. Add new patterns only for generalizable observations.
7. Refresh `index.md` and append a cycle summary to `log.md`.

Use statuses: `provisional`, `confirmed`, `superseded`.

### 4. Skill proposal

Before proposing, inspect `skill-impact.md`. Then read relevant patterns and normally at least 4 traces.

Each proposal is atomic: create one skill or patch one existing skill. Prefer patching when the current skill is partly right. Link the change to evidence in `PURPOSE.md`.

Do not repeat a rejected proposal unchanged. A rejected idea may be reconsidered only when new evidence invalidates the earlier reason for rejection.

### 5. Gate and rollback

Evaluate the candidate independently from the evidence used to invent it.

Accept when the candidate objectively improves the target behavior and does not regress protected behavior. For a binary regression test, "previously failing target now passes while existing validation remains green" is sufficient evidence of improvement.

Reject when validation worsens, the target does not improve, or evidence is too noisy. Roll back only the skill change. Keep all wiki updates and record the rejection.

If no credible gate exists, keep the candidate unpromoted.

## Evidence strength

- **Weak:** one ambiguous anecdote → raw trace only.
- **Provisional:** repeated symptom or one deterministic reproduced bug → wiki pattern.
- **Confirmed:** multiple traces across tasks/contexts or strong controlled validation → eligible to drive skill evolution.
- **Model-specific:** useful only for a particular model/tool budget → label explicitly; avoid generalizing into universal procedure.

## Wiki hygiene

The original paper notes that automatic pruning remains an open problem. For long-running repositories, do not delete history casually. Merge duplicate patterns, mark obsolete pages `superseded`, and keep links to their replacements. Raw evidence remains immutable.

## Research-to-production differences

The research setup directly injected all active skills and used benchmark train/validation/test splits with strict score-improvement gating. A coding repository rarely has that exact setup, so this adaptation substitutes software-native validation while preserving the core causal structure: experience → compiled knowledge → candidate procedure → independent gate.
