#!/usr/bin/env python3
"""Where the token budget actually went.

Reads Claude Code session transcripts and reports spend by context size, by
project, by session, plus the always-resident preamble cost. No dependencies,
no network, read-only.

    python3 burn.py            # last 7 days
    python3 burn.py 30         # last 30 days

The headline row is SPEND BY CONTEXT SIZE. Cost per turn scales with the context
carried into it, so a small number of very long turns can dominate a week. If most
of the spend sits above 300k, the fix is a smaller context window (so compaction
actually fires) or fresh sessions between unrelated tasks -- not compression.

Weighting: cache reads bill at roughly 0.1x base input, cache writes at 1.25x, and
output at ~5x, so raw token counts overstate cheap cached reads and understate
output. Everything here is reported in base-input-equivalent tokens.
"""

import collections
import datetime
import glob
import json
import os
import sys

CACHE_READ_RATE = 0.1
CACHE_WRITE_RATE = 1.25
OUTPUT_RATE = 5.0
# Rough price ratios against the largest model in a family.
FAMILY_RATE = {"haiku": 0.2, "sonnet": 0.6}

SIZE_BUCKETS = [(0, 100), (100, 200), (200, 300), (300, 500), (500, 1000), (1000, None)]


def transcript_dir():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(base, "projects")


def family_rate(model):
    for name, rate in FAMILY_RATE.items():
        if name in (model or ""):
            return rate
    return 1.0


def bucket_label(tokens):
    for low, high in SIZE_BUCKETS:
        if high is None or low <= tokens / 1000 < high:
            return "%dk+" % low if high is None else "%d-%dk" % (low, high)
    return "?"


def assistant_turns(path, cutoff):
    """Yield (usage, model) for each assistant turn after cutoff."""
    with open(path, errors="replace") as fh:
        for line in fh:
            if '"assistant"' not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("type") != "assistant":
                continue
            try:
                when = datetime.datetime.fromisoformat(
                    record.get("timestamp", "").replace("Z", "+00:00"))
            except ValueError:
                continue
            if when < cutoff:
                continue
            message = record.get("message") or {}
            usage = message.get("usage") or {}
            if usage:
                yield usage, message.get("model"), message.get("content") or [], when


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    by_size = collections.defaultdict(float)
    turns_by_size = collections.Counter()
    by_project = collections.defaultdict(float)
    tools = collections.Counter()
    sessions = {}
    total = 0.0
    preamble_reread = 0
    all_context = 0
    preambles = []

    for path in glob.glob(os.path.join(transcript_dir(), "*", "*.jsonl")):
        project = os.path.basename(os.path.dirname(path))
        session = os.path.basename(path)[:-6]
        cost = 0.0
        count = 0
        peak = 0
        first_context = 0
        first_seen = last_seen = None

        for usage, model, content, when in assistant_turns(path, cutoff):
            get = lambda key: usage.get(key) or 0
            context = (get("input_tokens") + get("cache_read_input_tokens")
                       + get("cache_creation_input_tokens"))
            if not context:
                continue

            weighted = family_rate(model) * (
                get("input_tokens")
                + CACHE_READ_RATE * get("cache_read_input_tokens")
                + CACHE_WRITE_RATE * get("cache_creation_input_tokens")
                + OUTPUT_RATE * get("output_tokens"))

            count += 1
            cost += weighted
            total += weighted
            all_context += context
            peak = max(peak, context)
            by_project[project] += weighted
            label = bucket_label(context)
            by_size[label] += weighted
            turns_by_size[label] += 1

            if count == 1:
                first_context = context
                first_seen = when
            last_seen = when

            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tools[block.get("name")] += 1

        if count:
            # The first turn is the always-resident prefix: instructions, memory,
            # skill catalog, tool schemas. Every later turn re-reads it.
            preamble_reread += first_context * count
            preambles.append(first_context)
            hours = ((last_seen - first_seen).total_seconds() / 3600
                     if first_seen and last_seen else 0.0)
            sessions[(project, session)] = (cost, count, peak, hours)

    if not total:
        print("No assistant turns in the last %d days under %s" % (days, transcript_dir()))
        return 1

    share = lambda value: 100 * value / total
    turn_total = sum(v[1] for v in sessions.values())

    print("=== %d-day burn: %.0fM weighted tokens, %d sessions, %d turns ===" % (
        days, total / 1e6, len(sessions), turn_total))

    print("\nSPEND BY CONTEXT SIZE OF THE TURN   <- the main lever")
    over_300k = 0.0
    for low, high in SIZE_BUCKETS:
        label = "%dk+" % low if high is None else "%d-%dk" % (low, high)
        if not by_size[label]:
            continue
        if low >= 300:
            over_300k += by_size[label]
        print("  %-12s %6.1f%%   %6d turns" % (label, share(by_size[label]),
                                               turns_by_size[label]))
    print("  --> %.0f%% of spend is on turns carrying more than 300k of context"
          % share(over_300k))

    if preambles:
        preambles.sort()
        pct = 100 * preamble_reread / all_context
        print("\nALWAYS-RESIDENT PREAMBLE (instructions, memory, skill catalog, tool schemas)")
        print("  p50=%dk  p90=%dk per session  ->  %.0f%% of every token read" % (
            preambles[len(preambles) // 2] / 1000,
            preambles[int(len(preambles) * 0.9)] / 1000, pct))
        print("  Prune it once, then leave it stable: reads bill at %.1fx but rewrites at %.2fx."
              % (CACHE_READ_RATE, CACHE_WRITE_RATE))

    print("\nTOP PROJECTS")
    for name, value in sorted(by_project.items(), key=lambda kv: -kv[1])[:8]:
        print("  %6.1f%%  %s" % (share(value), name[-58:]))

    print("\nTOP SESSIONS (the long ones are where the budget goes)")
    for (project, session), (cost, count, peak, hours) in sorted(
            sessions.items(), key=lambda item: -item[1][0])[:10]:
        print("  %5.1f%%  turns=%-5d peak=%4.0fk  %4.1fh  %s %s" % (
            share(cost), count, peak / 1000, hours, project[-42:], session[:8]))

    print("\nTOOL CALLS")
    for name, value in tools.most_common(6):
        print("  %-28s %d" % (name, value))

    return 0


if __name__ == "__main__":
    sys.exit(main())
