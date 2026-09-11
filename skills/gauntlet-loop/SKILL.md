---
name: gauntlet-loop
description: Run a benchmark-driven Gauntlet Loop for complex code, UI, product, research, or writing work. Use when the user wants sustained autonomous improvement against a concrete inspectable quality bar, with separate builder and fresh critic subagents, repeated evidence-based comparison, and no arbitrary fixed round count. Do not use for small well-scoped fixes, routine edits, or tasks whose output cannot be inspected or tested.
---

# Gauntlet Loop

Run a lead-agent workflow that repeatedly builds, inspects, criticizes, and improves a real artifact against a concrete quality bar.

The core rule is strict separation of duties: **the builder never grades its own work**. A fresh critic must inspect the actual artifact and the actual benchmark or measurement.

## Operating principles

1. Give the lead agent the outcome and constraints, not a prescribed implementation.
2. Use a concrete bar that can be inspected, measured, or compared.
3. Decompose the work into the smallest meaningful pieces that can be improved and judged independently.
4. Use separate builder and critic subagents. Keep critics fresh and read-only.
5. Make critics inspect real evidence: running code, rendered pixels, screenshots, tests, metrics, traces, deployed previews, or finished prose. Never let them grade a builder-authored summary.
6. When a candidate loses, identify the single largest meaningful gap and loop that gap back to a builder.
7. Do not stop after an arbitrary number of rounds. Stop only under the termination rules below.
8. Keep the user able to observe and stop the run without needing to interrupt for routine status updates.

## Start by deciding whether this skill applies

Use this workflow when all of the following are true:

- The task is substantial enough to benefit from multiple improvement rounds.
- There is or can be an inspectable artifact.
- A credible reference, benchmark, test, metric, rubric, or comparison can be established.
- Additional rounds have a reasonable chance of improving the result.

For a small fix or a task with an obvious one-pass solution, perform the task normally instead of creating Gauntlet machinery.

## Phase 1: Establish the charter

Before editing, create `.gauntlet/charter.md` and record:

- **Goal:** the user-visible outcome.
- **Constraints:** requirements, exclusions, compatibility, safety, scope, and repository rules.
- **Quality bar:** the concrete reference or measurement that the artifact must meet.
- **Evidence method:** exact commands, tools, screenshots, metrics, test cases, or review procedure used to judge it.
- **Baseline:** the current artifact's result against the same evidence method.
- **Budget:** any user-provided time, token, cost, round, or scope limit. Do not invent a fixed round count when none was given.
- **Termination conditions:** copied from this skill plus any task-specific conditions.

If the user supplied references, inspect them and choose the strongest bar that is both relevant and actually testable.

If no bar was supplied, delegate a short read-only benchmark search to one or more subagents. Choose a bar that is difficult to game and explain its usefulness in one sentence. Do not use vague standards such as “production-ready,” “beautiful,” or “excellent” without observable criteria.

Examples of valid bars:

- Backend: a test suite, correctness oracle, latency target, failure-recovery scenario, security review, or reference implementation.
- Frontend or game: side-by-side screenshots or video, interaction recordings, frame-time targets, accessibility checks, and a real reference product.
- Research: held-out predictions, point-in-time backtests, factual verification, reproducible calculations, or a reference analysis.
- Writing: reference passages plus a concrete rubric for clarity, factual density, structure, and audience fit.

## Phase 2: Capture a baseline

Run or render the current artifact before making improvements.

Save the important evidence under `.gauntlet/evidence/baseline/` when practical. For visual work, capture screenshots or recordings. For code, retain commands and concise outputs. For writing or research, retain the exact draft and validation results.

Spawn a fresh critic to judge the baseline. The critic must receive:

- the goal;
- the quality bar and reference;
- the constraints;
- the artifact or exact instructions to inspect it;
- the required critic response format from `references/critic-protocol.md`.

Do not send the critic the builder's rationale, chain of decisions, or persuasive summary.

## Phase 3: Decompose and prioritize

As lead agent, divide the goal into the smallest components that can be improved and judged independently. Record them in `.gauntlet/progress.md` using `references/progress-template.md` as a guide.

For each component, define:

- its local outcome;
- its relationship to the global quality bar;
- its evidence or acceptance check;
- dependencies and likely file ownership;
- the current largest gap.

Prioritize by expected impact on the global bar, not by ease or novelty.

Parallelize read-heavy exploration and independent components. Be conservative with parallel write-heavy work: avoid giving multiple builders overlapping file ownership unless they work in isolated worktrees and an integration step is planned.

## Phase 4: Run builder–critic loops

For each active component:

1. Spawn a builder subagent. Prefer the optional `gauntlet_builder` custom agent when installed; otherwise use a write-enabled worker with the same role instructions.
2. Give the builder only the component goal, relevant constraints, current artifact, current critic finding, allowed scope, and acceptance check.
3. The builder changes the real artifact and runs the required local checks.
4. Capture the resulting evidence under `.gauntlet/evidence/<component>/<round>/` when practical.
5. Spawn a **fresh** critic subagent. Prefer the optional `gauntlet_critic` custom agent when installed; otherwise explicitly require read-only behavior and fresh context.
6. The critic inspects the artifact and benchmark directly, using blind A/B comparison when practical. It returns the exact verdict structure in `references/critic-protocol.md`.
7. If the verdict is `FAIL`, route only the largest meaningful gap and its next acceptance check to the next builder round.
8. If the verdict is `PASS`, mark the component provisionally passed and move to the next highest-impact gap.
9. If the verdict is `BLOCKED`, verify the blocker independently before escalating it to the lead agent.

Do not let a builder declare a component passed. Tests run by a builder are evidence, not the final judgment.

Do not weaken tests, change the benchmark, crop away defects, cherry-pick favorable samples, alter scoring after seeing outcomes, or redefine the bar merely to obtain a pass. Any legitimate bar change must be documented in the charter with the reason and must trigger a new baseline.

## Phase 5: Integrate after major waves

After several components change, or whenever changes begin to conflict, spawn a fresh whole-artifact integrator. Prefer `gauntlet_integrator` when installed.

The integrator should:

- inspect the complete artifact rather than redesigning it;
- remove inconsistencies introduced by separate builders;
- resolve integration conflicts;
- preserve the strongest local improvements;
- run system-level checks;
- avoid broad rewrites without evidence that they improve the global bar.

After integration, run a new whole-artifact critic. A set of locally passing components does not imply that the complete result passes.

## Phase 6: Maintain observable progress

Keep `.gauntlet/progress.md` current after every critic verdict. It should show:

- current goal and bar;
- baseline result;
- component status;
- rounds attempted;
- latest evidence;
- largest remaining gaps;
- blockers;
- why the loop is continuing or stopping.

For long visual or product runs, also create a simple `.gauntlet/progress.html` that presents the evolving evidence—screenshots, videos, metrics, and verdicts—in a form the user can open without interrupting the run. Choose the simplest implementation suitable for the repository.

Keep routine tool logs out of the main thread. Return concise subagent summaries and preserve detailed evidence in `.gauntlet/`.

## Termination rules

Do not stop merely because the result is “pretty good,” because a round count was reached, or because the builder says it is done.

Stop when the first applicable condition is met:

1. **Bar passed:** a fresh whole-artifact critic returns `PASS`, supported by the required evidence.
2. **User stop or budget reached:** the user stops the run or an explicit time, token, cost, or scope budget is exhausted.
3. **Hard blocker:** a verified external dependency, missing permission, unavailable tool, or safety constraint prevents further progress.
4. **Evidence-backed plateau:** two consecutive whole-artifact rounds produce no meaningful improvement on the declared bar, and the lead agent can explain why another round is unlikely to be worth its cost. Do not claim a plateau from intuition alone.
5. **Unsafe or invalid direction:** continuing would require destructive, deceptive, unauthorized, or policy-violating action.

When stopping before a pass, report the highest-value next action rather than disguising the result as complete.

## Final validation and report

Before completion, spawn one fresh whole-artifact critic that did not participate as a builder. Re-run the global evidence method from the charter.

Return a concise final report containing:

- goal and quality bar;
- stop reason;
- baseline versus final evidence;
- components improved and number of critic rounds per component;
- validation commands or inspection method;
- files or artifacts changed;
- remaining gaps and risks;
- location of `.gauntlet/progress.md` and any visual progress page.

Never claim the artifact beat the reference unless the declared evidence supports that conclusion.

## Claude Code orchestration

- Spawn subagents with the `Agent` tool. Use `subagent_type: "gauntlet-builder"`,
  `"gauntlet-critic"`, and `"gauntlet-integrator"` when those agent definitions are installed
  (`~/.claude/agents/` for personal use, `.claude/agents/` per repository). Without them, use
  `general-purpose` for builders and integrators and `Explore` for critics, and paste the role
  boundaries from `references/critic-protocol.md` into the prompt.
- **A fresh critic means a fresh `Agent` call.** Do not continue a builder's agent with
  `SendMessage` and ask it to grade itself — that destroys the separation the method depends on.
- Critics must be read-only. The `gauntlet-critic` definition omits `Edit`, `Write` and
  `NotebookEdit`; if you fall back to another agent type, say "do not modify any file" in the
  prompt and give it read-only tools.
- Run parallel builders on independent components in a single message with multiple `Agent`
  calls. When two builders could touch the same files, pass `isolation: "worktree"` so each gets
  its own git worktree, and plan an integration step.
- Subagents run in the background by default and notify you on completion. Pass
  `run_in_background: false` for a critic whose verdict you need before deciding the next round.
- The subagent's final report is not shown to the user — relay the verdict and the largest gap
  yourself, and keep the detailed evidence in `.gauntlet/`.
- If the host offers a workflow runner and the user has explicitly opted into multi-agent
  orchestration, a find → verify pipeline is a reasonable way to run one wave. The
  builder/critic separation still applies inside it.

## Codex-specific orchestration

- Explicitly ask Codex to spawn subagents; skill instructions can trigger delegation, but do not rely on implicit delegation for the critical builder/critic separation.
- Use `/agent` in Codex CLI to inspect agent threads when needed.
- Critics should use read-only sandboxing. Builders and integrators may use workspace-write within the user's selected permission mode.
- Prefer high reasoning for the lead and critic on ambiguous or high-value tasks. Use faster agents for bounded exploration or repetitive evidence collection.
- Subagents inherit the parent session's approvals and sandbox constraints. Plan the workflow so required approvals can surface interactively.
- Do not create parallel builders with overlapping writes unless using isolated worktrees and an explicit integration plan.

## Optional custom agents

This skill includes optional Codex custom-agent profiles under `optional-codex/agents/`:

- `gauntlet_builder.toml`
- `gauntlet_critic.toml`
- `gauntlet_integrator.toml`

Install them under `.codex/agents/` for a repository or `~/.codex/agents/` for personal use.

The Claude Code equivalents are `gauntlet-builder.md`, `gauntlet-critic.md` and
`gauntlet-integrator.md` under `.claude/agents/` or `~/.claude/agents/`.

The workflow must still work without either set, by spawning ordinary subagents with the same role boundaries.
