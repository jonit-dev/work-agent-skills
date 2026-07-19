---
name: forecasting-experiments
description: Multi-agent forecasting research lab for BTC or S&P 500 forecast improvement. Use when the user asks to chew through available BTC, Bitcoin, crypto, SP500, S&P 500, market, macro, on-chain, price, indicator, or app data to discover self-verifiable forecasting improvements, run scientific experiments, validate hypotheses with backtests/statistical tests/proofs, prevent regressions, or produce evidence-backed changes for a forecasting app. Defaults to BTC when the asset is not specified.
---

# Forecasting Experiments

Run a disciplined forecasting science lab. The goal is not to produce interesting narratives; it is to find changes that measurably improve the app without introducing regressions.

## Defaults

- Default asset: BTC.
- Use SP500/S&P 500 only when the user explicitly asks for it or the local project already scopes the task to it.
- Prefer all available local data before fetching external data. If current market data, changing public data, or precise source attribution is needed, verify it from primary or reputable sources.
- Treat every discovery as a hypothesis until independently validated.

## Lab Workflow

1. **Map the app and data**
   - Inspect the repository for forecast models, feature pipelines, data loaders, evaluation scripts, tests, and UI assumptions.
   - Inventory available datasets, date ranges, frequencies, missingness, target definitions, leakage risks, and known baselines.
   - Identify the current production or app-facing metrics before proposing changes.

2. **Pre-register experiment rules**
   - Define the target, forecast horizon, baseline, train/validation/test split, walk-forward schedule, primary metric, secondary metrics, and failure criteria before testing candidates.
   - Use time-series splits only. Never shuffle time-dependent rows.
   - Preserve a final holdout period that is not used for feature selection, prompt iteration, parameter tuning, or model choice.
   - Use `references/experiment-report-template.md` as the required artifact schema for non-trivial runs.

3. **Spawn specialist agents**
   - Launch agents when multi-agent tools are available. Keep scopes independent and forbid file edits unless explicitly assigned.
   - Use at least these roles for broad lab work:
     - Data auditor: validates datasets, timestamps, missing values, resampling, target alignment, and leakage risks.
     - Signal miner: searches for candidate features, regimes, transformations, or model changes.
     - Backtest engineer: implements or reviews walk-forward tests, costs, metrics, and benchmark comparisons.
     - Statistician/skeptic: checks significance, multiple testing, robustness, and effect size.
     - App integration reviewer: checks whether a proposed change fits the app, tests, UI, performance, and maintainability.
   - Add domain agents for on-chain, macro, derivatives, sentiment, technical indicators, or market microstructure only when the data exists or can be sourced responsibly.
   - If subagents are unavailable, emulate the same roles sequentially and record each role's findings separately. Run the validator role last, after clearing prior role-specific context from the working notes as much as practical.

4. **Run experiments reproducibly**
   - Save commands, parameters, data versions, date ranges, random seeds, and output artifacts.
   - Compare against naive and current app baselines, such as persistence, moving-average, last-value, existing model, or current displayed forecast.
   - Use walk-forward or rolling-origin evaluation for time-series forecasting.
   - Include realistic assumptions: timestamp availability, trading calendar, data publication lag, fees/slippage when evaluating tradable signals, and inference latency when relevant.
   - When comparing forecast CSVs, prefer `scripts/forecast_compare.py` for a deterministic first-pass metric/statistics report:

```bash
python /path/to/forecasting-experiments/scripts/forecast_compare.py results.csv --bootstrap 5000 --confidence 0.95
```

5. **Validate statistically**
   - Report effect size, confidence intervals or bootstrap intervals, and uncertainty, not only point estimates.
   - Use significance tests appropriate to the metric and data dependence. Consider Diebold-Mariano tests for forecast error comparisons, bootstrap/permutation tests for uncertain distributions, and deflated/adjusted Sharpe or multiple-comparison correction for strategy-style searches.
   - Penalize data dredging. If many candidates were searched, require stricter evidence or a fresh holdout.
   - Reject improvements that only win on one cherry-picked period, one metric, or one fragile parameter setting.
   - Default threshold when the user does not specify one: 95% confidence interval, p < 0.05 after reasonable multiple-testing adjustment, at least 30 final-holdout observations, and a practically meaningful effect size for the app. If these defaults are inappropriate for the horizon or dataset, state the replacement threshold before testing.
   - Require a math/proof section for every kept candidate: define the metric formula, state assumptions, explain why the test matches the data-generating process, and show why the candidate cannot use future information.

6. **Prevent regressions**
   - Before implementation, identify the app behavior that must remain unchanged.
   - Add or update automated tests for data alignment, leakage prevention, feature calculation, model evaluation, API shape, and UI-facing forecast output as applicable.
   - Run the repository's existing test suite and targeted new tests.
   - Require an independent validation agent or local second pass to review candidate changes for regressions, false positives, and math mistakes before finalizing.

7. **Gate app changes**
   - Do not modify the app for a hypothesis unless it clears the evidence gate below.
   - Prefer shipping a reproducible experiment report first when evidence is promising but not yet implementation-ready.
   - Keep app changes small and reversible: feature flags, config switches, side-by-side metrics, or non-default experimental modes when uncertainty remains.

## Evidence Gate

A candidate is implementation-ready only when all are true:

- Reproducible: another agent or a fresh local run can reproduce the result from recorded commands and inputs.
- Leak-free: data availability and target alignment are point-in-time valid.
- Baseline-beating: improvement is measured against the current app baseline and at least one naive baseline.
- Out-of-sample: primary claim is based on validation/test periods not used to invent or tune the candidate.
- Statistically credible: effect size and uncertainty are reported; significance or robustness survives reasonable multiple-testing concerns.
- Robust: result holds across meaningful subperiods, market regimes, horizons, or parameter perturbations.
- Regression-protected: automated tests cover the new path and existing relevant tests pass.
- App-relevant: improvement maps to a user-visible app metric or workflow, not just an offline curiosity.
- Proof-reviewed: metric formulas, statistical assumptions, and point-in-time feature availability have been checked by a validator or a clearly separated second pass.

If any gate fails, label the candidate as `rejected`, `needs more data`, or `research-only`.

## Agent Prompt Patterns

Specialist prompt:

```text
You are part of a forecasting experiment lab for <BTC/SP500>.
Focus only on <data audit/signal mining/backtest/statistics/app integration>.
Do not edit files unless explicitly assigned.
Use only evidence you can cite: file paths, commands, data ranges, metrics, formulas, source links, or artifacts.
Return hypotheses, tests performed, results, caveats, and whether the evidence passes the implementation gate.
Call out leakage, overfitting, multiple testing, and regression risks.
```

Validation prompt:

```text
You are the independent validator for a forecasting experiment.
Do not edit files.
Review the candidate claim, experiment code/results, statistics, and proposed app change.
Try to disprove it: check leakage, split integrity, metric choice, multiple testing, reproducibility, robustness, and regression risk.
Classify the candidate as keep, downgrade to research-only, needs more testing, or reject.
```

## Required Output

For a research-only run, produce:

- data inventory and quality notes
- completed `references/experiment-report-template.md` sections, adapted to the project
- baseline metrics
- candidate hypotheses tested
- backtest/evaluation commands
- statistical results and robustness checks
- rejected ideas with reasons
- implementation-ready candidates, if any

For an app-change run, also produce:

- code changes made
- tests added or updated
- test/backtest commands run
- before/after metrics
- remaining risks and rollout recommendation

## Red Flags

Stop or downgrade the claim when you find:

- shuffled time splits, future data, target leakage, or publication-lag violations
- tuning on the final holdout
- improvements that disappear under transaction costs, realistic latency, or minor parameter changes
- missing baseline comparison
- no uncertainty estimate
- unclear data provenance
- untested changes to app-facing forecast behavior
