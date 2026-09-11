# Karpathy autoresearch reference

## Provenance

- Repository: https://github.com/karpathy/autoresearch
- Inspected commit: `228791fb499afffb54b46200aca536f79142f117`
- License stated upstream: MIT
- Primary sources inspected: `README.md`, `program.md`, `prepare.py`, `train.py`, `pyproject.toml`

## Semantics absorbed

1. Separate the **human-authored research program** from the **agent-edited candidate** and the **fixed evaluator**.
2. Restrict edits to one small surface (`train.py` upstream) while keeping data preparation and evaluation immutable (`prepare.py`).
3. Establish an untouched baseline first.
4. Give every trial the same wall-clock budget; upstream uses 300 seconds of training time.
5. Optimize one scalar metric; upstream minimizes validation bits per byte (`val_bpb`).
6. Commit each candidate before evaluation, record results in a TSV ledger, keep improvements, and restore the incumbent after losses.
7. Redirect large run output to a log and parse only result fields.
8. Treat simplicity as a secondary objective and memory as a resource constraint.
9. Continue autonomously without asking after every experiment.

## Original-repository contract

- Requirements: Python 3.10+, `uv`, one NVIDIA GPU; the upstream baseline was tested on an H100.
- Setup: `uv sync`, then `uv run prepare.py` to download data and train a tokenizer.
- Trial command: `uv run train.py > run.log 2>&1`.
- Expected result fields include `val_bpb`, `training_seconds`, `peak_vram_mb`, token count, step count, parameter count, and depth.
- Upstream marks a run as failed if it takes over about ten minutes, crashes, or does not emit the metric.
- Upstream's `results.tsv` uses commit, metric, memory, status, and description.

## Security and integrity review

The inspected repository is small. Network behavior is explicit:

- `prepare.py` downloads Parquet data from Karpathy's Hugging Face dataset endpoint.
- `train.py` asks the `kernels` package for a FlashAttention implementation from a named repository.
- The README suggests a shell-piped `uv` installer, but this skill does not execute it automatically.

No executable hooks, credential access, secret collection, deployment action, or messaging integration appeared in the inspected top-level source. The main operational risks are substantial GPU use, large downloads/cache growth, package execution, destructive Git resets on a shared checkout, benchmark gaming, and an upstream instruction to loop forever.

## Deliberate adaptations

- Replace “loop forever” with an explicit total experiment/time/cost cap.
- Require a fresh branch or worktree and forbid destructive resets outside that isolated run.
- Add raw-log preservation, exit-status checks, metric validity checks, and environment provenance.
- Require repeated measurements or confidence treatment when noise can change rankings.
- Add periodic baseline/incumbent reproduction and a final untouched confirmation set when many hypotheses are searched.
- Forbid new dependencies, new data, wider permissions, push/deploy/publication, and spending unless the user explicitly approves them.

These adaptations preserve the core autonomous hill-climbing loop while making it safe and reusable beyond the original single-GPU LLM benchmark.
