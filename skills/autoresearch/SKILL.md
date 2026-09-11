---
name: autoresearch
description: Run autonomous, evidence-driven optimization loops over a bounded editable surface with a fixed evaluation harness, comparable budgets, baseline-first experiments, commit-level provenance, keep/discard decisions, and a durable result ledger. Use when asked to “autoresearch,” optimize a measurable metric overnight, repeatedly improve code or model performance, run autonomous experiments, tune a training setup, or adapt Karpathy's autoresearch pattern to another repository.
---

# Autoresearch

Turn a repository into a controlled experiment loop. Optimize evidence, not activity.

## Establish the contract

Before changing files, write down:

- **Objective:** one primary scalar metric and direction (`min` or `max`).
- **Evaluator:** the exact deterministic command and output field that decides the result.
- **Budget:** equal per-trial wall-clock/compute/data budget plus a total run limit or deadline.
- **Mutable surface:** the smallest file set the loop may edit.
- **Immutable surface:** evaluator, held-out data, budget enforcement, result parser, and safety constraints.
- **Secondary gates:** correctness, memory, latency, complexity, cost, or other non-negotiable bounds.

Reject a setup whose evaluator can be modified by the experimenter, whose trials use unequal budgets, or whose objective cannot be parsed reliably. Do not begin an unbounded `LOOP FOREVER`; require a user-specified limit or choose a conservative explicit cap and report it.

For the original `karpathy/autoresearch` repository, read `program.md`, `README.md`, `prepare.py`, and `train.py`. Preserve `prepare.py` and its evaluation logic; only `train.py` is mutable unless the user explicitly changes the contract.

## Isolate the run

1. Inspect repository instructions and current Git state.
2. Never overwrite unrelated dirty work. Use a fresh branch or isolated worktree.
3. Name the branch `autoresearch/<tag>`; refuse a collision rather than reusing an old run.
4. Record the starting commit, environment, dependency lock hash, hardware, seed, evaluator command, limits, and metric contract.
5. Keep the ledger outside commits by default so experiment commits remain code-only.

Use resets only inside the isolated experiment branch/worktree. Never reset a shared branch, a dirty checkout, or commits predating the run. Prefer `git revert` or restoring the known-good candidate when provenance would otherwise be ambiguous.

## Initialize the ledger

Create `results.tsv` with tab-separated fields:

```text
experiment	commit	primary_metric	secondary_metrics	status	duration_s	description
```

Statuses: `baseline`, `keep`, `discard`, `crash`, `timeout`, `invalid`.

Store raw logs under a run-specific ignored directory. Redirect verbose commands to files; extract only summaries into context. Never claim a result without preserving the raw command output and exit status.

## Run the loop

1. **Baseline first.** Run the untouched candidate under the exact contract. Stop if the baseline is not reproducible or the evaluator fails.
2. **Choose one hypothesis.** Prefer one conceptual change per trial so causality stays legible. Predict the expected mechanism and likely trade-off before editing.
3. **Commit the candidate.** Make a narrow experiment commit before evaluation.
4. **Evaluate identically.** Use the same command, seed policy, data, budget, hardware class, and parser. Enforce a timeout.
5. **Parse and validate.** Reject missing/non-finite metrics, harness changes, budget violations, correctness failures, or suspiciously incomparable output.
6. **Log every trial.** Include failures and discarded ideas; negative evidence prevents repetition.
7. **Decide:**
   - Keep only if the primary metric beats the incumbent by more than expected noise and all hard gates pass.
   - Discard if it loses, is inconclusive, violates a gate, or buys a trivial gain with disproportionate complexity.
   - Prefer simplification when performance is statistically tied.
8. **Return to the incumbent.** Restore the last accepted state after a discard, then begin the next independent hypothesis.
9. **Periodically reproduce.** Re-run the incumbent and baseline after several trials to detect drift, thermal effects, cache effects, data mutation, or benchmark gaming.

For noisy metrics, use repeated trials or confidence intervals. Do not rank candidates on single-run noise. Reserve a final untouched holdout or fresh seed set for confirmation when the loop searches many ideas.

## Research strategy

- Start with high-information, low-complexity changes.
- Alternate exploitation of successful families with exploration of orthogonal ideas.
- Track failed families and avoid cosmetic permutations of known losers.
- Combine changes only after their individual effects are understood.
- Treat crashes as evidence: fix trivial implementation defects once; abandon structurally broken ideas.
- Penalize benchmark overfitting, evaluator leakage, hidden resource increases, and dependence on unavailable packages.
- Do not install dependencies, fetch new data, or widen permissions unless the experiment contract permits it.

## Stop and report

Stop when the run limit/deadline is reached, the user interrupts, the environment becomes unstable, the evaluator loses integrity, or progress saturates under the predefined rule.

Leave:

- the branch at the best accepted commit;
- a clean working tree except intentionally untracked/ignored logs and ledger;
- a ranked ledger with baseline, kept, discarded, crashed, and invalid trials;
- exact reproduction commands;
- a concise report: best metric vs baseline, absolute/relative change, secondary trade-offs, experiment count, failed families, confidence/noise caveat, and recommended next hypothesis.

Never push, publish, deploy, spend money, or touch production without explicit approval.

## Source adaptation

This workflow ports the experimental semantics of Karpathy's MIT-licensed `autoresearch` without copying its model implementation. Read `references/karpathy-autoresearch.md` for upstream-specific mechanics, provenance, and deliberate safety adaptations.
