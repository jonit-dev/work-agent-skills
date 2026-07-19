#!/usr/bin/env python3
"""Compare baseline and candidate forecasts from a CSV file.

Input CSV columns:
  y_true, baseline_pred, candidate_pred

Optional:
  timestamp

Outputs JSON with error metrics, paired loss deltas, bootstrap confidence
intervals, and an approximate Diebold-Mariano test for squared and absolute
error loss. Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from typing import Callable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--min-rows", type=int, default=30)
    return parser.parse_args()


def read_rows(path: str) -> tuple[list[float], list[float], list[float]]:
    actual: list[float] = []
    baseline: list[float] = []
    candidate: list[float] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"y_true", "baseline_pred", "candidate_pred"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing required columns: {', '.join(sorted(missing))}")
        for index, row in enumerate(reader, start=2):
            try:
                actual.append(float(row["y_true"]))
                baseline.append(float(row["baseline_pred"]))
                candidate.append(float(row["candidate_pred"]))
            except ValueError as exc:
                raise SystemExit(f"Non-numeric value on CSV line {index}: {exc}") from exc
    return actual, baseline, candidate


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def rmse(actual: list[float], pred: list[float]) -> float:
    return math.sqrt(mean([(a - p) ** 2 for a, p in zip(actual, pred)]))


def mae(actual: list[float], pred: list[float]) -> float:
    return mean([abs(a - p) for a, p in zip(actual, pred)])


def mape(actual: list[float], pred: list[float]) -> float | None:
    terms = [abs((a - p) / a) for a, p in zip(actual, pred) if a != 0]
    return mean(terms) if terms else None


def quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return math.nan
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[int(position)]
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def bootstrap_ci(
    pairs: list[tuple[float, float, float]],
    metric: Callable[[list[float], list[float]], float],
    iterations: int,
    confidence: float,
    rng: random.Random,
) -> dict[str, float]:
    n = len(pairs)
    deltas: list[float] = []
    for _ in range(iterations):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        actual = [row[0] for row in sample]
        baseline = [row[1] for row in sample]
        candidate = [row[2] for row in sample]
        deltas.append(metric(actual, candidate) - metric(actual, baseline))
    deltas.sort()
    alpha = 1 - confidence
    return {
        "lower": quantile(deltas, alpha / 2),
        "upper": quantile(deltas, 1 - alpha / 2),
    }


def normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def dm_test(loss_delta: list[float]) -> dict[str, float | None]:
    """Approximate two-sided paired loss test.

    Positive mean_delta means candidate loss is lower than baseline loss because
    deltas are baseline_loss - candidate_loss.
    """

    n = len(loss_delta)
    avg = mean(loss_delta)
    if n < 2:
        return {"statistic": None, "p_value": None, "mean_delta": avg}
    stdev = statistics.stdev(loss_delta)
    if stdev == 0:
        statistic = None
        p_value = 0.0 if avg != 0 else 1.0
    else:
        statistic = avg / (stdev / math.sqrt(n))
        p_value = 2 * (1 - normal_cdf(abs(statistic)))
    return {"statistic": statistic, "p_value": p_value, "mean_delta": avg}


def percent_change(candidate_value: float, baseline_value: float) -> float | None:
    if baseline_value == 0:
        return None
    return (candidate_value - baseline_value) / baseline_value


def main() -> None:
    args = parse_args()
    actual, baseline, candidate = read_rows(args.csv_path)
    n = len(actual)
    if n < args.min_rows:
        raise SystemExit(f"Need at least {args.min_rows} rows, got {n}")

    pairs = list(zip(actual, baseline, candidate))
    baseline_rmse = rmse(actual, baseline)
    candidate_rmse = rmse(actual, candidate)
    baseline_mae = mae(actual, baseline)
    candidate_mae = mae(actual, candidate)
    rng = random.Random(args.seed)

    squared_loss_delta = [
        (a - b) ** 2 - (a - c) ** 2 for a, b, c in pairs
    ]
    absolute_loss_delta = [
        abs(a - b) - abs(a - c) for a, b, c in pairs
    ]

    output = {
        "rows": n,
        "seed": args.seed,
        "confidence": args.confidence,
        "metrics": {
            "baseline": {
                "rmse": baseline_rmse,
                "mae": baseline_mae,
                "mape": mape(actual, baseline),
            },
            "candidate": {
                "rmse": candidate_rmse,
                "mae": candidate_mae,
                "mape": mape(actual, candidate),
            },
            "relative_change": {
                "rmse": percent_change(candidate_rmse, baseline_rmse),
                "mae": percent_change(candidate_mae, baseline_mae),
            },
        },
        "bootstrap_delta_candidate_minus_baseline": {
            "rmse": bootstrap_ci(pairs, rmse, args.bootstrap, args.confidence, rng),
            "mae": bootstrap_ci(pairs, mae, args.bootstrap, args.confidence, rng),
        },
        "paired_loss_tests": {
            "squared_error_dm_approx": dm_test(squared_loss_delta),
            "absolute_error_dm_approx": dm_test(absolute_loss_delta),
        },
        "interpretation": {
            "lower_metric_is_better": True,
            "negative_bootstrap_delta_favors_candidate": True,
            "positive_dm_mean_delta_favors_candidate": True,
        },
    }
    print(json.dumps(output, allow_nan=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
