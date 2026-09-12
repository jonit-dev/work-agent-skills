#!/usr/bin/env python3
"""Where the token budget actually went.

Reads local coding-agent session transcripts and reports spend by context size, by
project, by session, plus the always-resident preamble cost. No dependencies, no
network, read-only.

    python3 burn.py                  # last 7 days, every agent found
    python3 burn.py 30               # last 30 days
    python3 burn.py --source codex   # one agent only
    python3 burn.py --list-sources   # what is installed on this machine

Supported transcript formats: Claude Code (~/.claude/projects/*/*.jsonl) and Codex
(~/.codex/sessions/**/rollout-*.jsonl). Both are auto-detected; whichever is present
gets read. Adding a third agent means one entry in SOURCES.

The headline row is SPEND BY CONTEXT SIZE. Cost per turn scales with the context
carried into it, so a small number of very long turns can dominate a week. If most
of the spend sits above 300k, the fix is a smaller context window (so compaction
actually fires) or fresh sessions between unrelated tasks -- not compression.

Weighting: cache reads bill at roughly 0.1x base input, cache writes at 1.25x, and
output at ~5x, so raw token counts overstate cheap cached reads and understate
output. Everything here is reported in base-input-equivalent tokens, scaled by a
rough per-model price ratio. Models with no known ratio are counted at 1.0 and
reported separately -- an unpriced model is flagged, never silently billed as cheap.
"""

import argparse
import collections
import datetime
import glob
import json
import os
import sys

CACHE_READ_RATE = 0.1
CACHE_WRITE_RATE = 1.25
OUTPUT_RATE = 5.0

# Rough price ratios against the flagship of each family. Substring match on the
# model id, longest key first, so "gpt-5-mini" does not match "gpt-5".
MODEL_RATE = {
    "haiku": 0.2,
    "sonnet": 0.6,
    "opus": 1.0,
    "gpt-5-mini": 0.2,
    "gpt-5.5": 1.0,
    "gpt-5": 1.0,
}

SIZE_BUCKETS = [(0, 100), (100, 200), (200, 300), (300, 500), (500, 1000), (1000, None)]


def model_rate(model):
    """Price ratio for a model id, or None when the model is unknown."""
    for name in sorted(MODEL_RATE, key=len, reverse=True):
        if name in (model or ""):
            return MODEL_RATE[name]
    return None


def bucket_label(tokens):
    for low, high in SIZE_BUCKETS:
        if high is None or low <= tokens / 1000 < high:
            return "%dk+" % low if high is None else "%d-%dk" % (low, high)
    return "?"


def parse_time(value):
    try:
        return datetime.datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def turn(project, session, model, when, base_in, cache_read, cache_write, output, tools):
    """One normalized assistant turn. Every source yields these and nothing else."""
    return {
        "project": project, "session": session, "model": model, "when": when,
        "base_in": base_in, "cache_read": cache_read, "cache_write": cache_write,
        "output": output, "tools": tools,
    }


# --- Claude Code -----------------------------------------------------------

def claude_root():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(base, "projects")


def claude_files():
    return sorted(glob.glob(os.path.join(claude_root(), "*", "*.jsonl")))


def claude_turns(path):
    project = os.path.basename(os.path.dirname(path))
    session = os.path.basename(path)[:-6]
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
            when = parse_time(record.get("timestamp"))
            if when is None:
                continue
            message = record.get("message") or {}
            usage = message.get("usage") or {}
            if not usage:
                continue
            get = lambda key: usage.get(key) or 0
            tools = [b.get("name") for b in (message.get("content") or [])
                     if isinstance(b, dict) and b.get("type") == "tool_use"]
            yield turn(project, session, message.get("model"), when,
                       get("input_tokens"), get("cache_read_input_tokens"),
                       get("cache_creation_input_tokens"), get("output_tokens"), tools)


# --- Codex -----------------------------------------------------------------

def codex_root():
    base = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    return os.path.join(base, "sessions")


def codex_files():
    return sorted(glob.glob(os.path.join(codex_root(), "**", "rollout-*.jsonl"),
                            recursive=True))


def codex_turns(path):
    """Codex logs usage in event_msg/token_count and tool calls in separate records.

    input_tokens already includes the cached portion, unlike Claude Code, so base
    input is the difference. Reasoning tokens bill as output.
    """
    project = "?"
    session = os.path.basename(path)
    model = None
    pending_tools = []
    with open(path, errors="replace") as fh:
        for line in fh:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            payload = record.get("payload") or {}
            kind = record.get("type")

            if kind == "session_meta":
                cwd = payload.get("cwd") or ""
                project = os.path.basename(cwd.rstrip("/")) or project
                session = (payload.get("id") or session)[:8]
                continue
            if kind == "turn_context":
                model = payload.get("model") or model
                continue
            if payload.get("type") == "function_call":
                pending_tools.append(payload.get("name"))
                continue
            if payload.get("type") != "token_count":
                continue

            usage = ((payload.get("info") or {}).get("last_token_usage")) or {}
            if not usage:
                continue
            when = parse_time(record.get("timestamp"))
            if when is None:
                continue
            get = lambda key: usage.get(key) or 0
            cached = get("cached_input_tokens")
            tools, pending_tools = pending_tools, []
            yield turn(project, session, model, when,
                       max(get("input_tokens") - cached, 0), cached, 0,
                       get("output_tokens") + get("reasoning_output_tokens"), tools)


SOURCES = {
    "claude": (claude_root, claude_files, claude_turns),
    "codex": (codex_root, codex_files, codex_turns),
}


def active_sources(requested):
    names = list(SOURCES) if requested == "all" else [requested]
    return [n for n in names if os.path.isdir(SOURCES[n][0]())]


def main():
    parser = argparse.ArgumentParser(description="Where the token budget actually went.")
    parser.add_argument("days", nargs="?", type=int, default=7)
    parser.add_argument("--source", default="all", choices=["all"] + list(SOURCES))
    parser.add_argument("--list-sources", action="store_true")
    args = parser.parse_args()

    if args.list_sources:
        for name, (root, files, _) in SOURCES.items():
            path = root()
            found = len(files()) if os.path.isdir(path) else 0
            print("  %-8s %-46s %s" % (
                name, path, "%d transcripts" % found if found else "not installed"))
        return 0

    live = active_sources(args.source)
    if not live:
        print("No transcripts found. Try --list-sources.")
        return 1

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=args.days)

    by_size = collections.defaultdict(float)
    turns_by_size = collections.Counter()
    by_project = collections.defaultdict(float)
    by_source = collections.defaultdict(float)
    tools = collections.Counter()
    unpriced = collections.Counter()
    sessions = {}
    total = 0.0
    unpriced_cost = 0.0
    preamble_reread = 0
    all_context = 0
    preambles = []

    for source in live:
        _, files, read = SOURCES[source]
        for path in files():
            cost = 0.0
            count = 0
            peak = 0
            first_context = 0
            first_seen = last_seen = None
            project = session = None

            for item in read(path):
                if item["when"] < cutoff:
                    continue
                context = item["base_in"] + item["cache_read"] + item["cache_write"]
                if not context:
                    continue

                rate = model_rate(item["model"])
                raw = (item["base_in"]
                       + CACHE_READ_RATE * item["cache_read"]
                       + CACHE_WRITE_RATE * item["cache_write"]
                       + OUTPUT_RATE * item["output"])
                weighted = (rate if rate is not None else 1.0) * raw
                if rate is None:
                    unpriced[item["model"] or "unknown"] += 1
                    unpriced_cost += weighted

                project, session = item["project"], item["session"]
                count += 1
                cost += weighted
                total += weighted
                all_context += context
                peak = max(peak, context)
                by_project[project] += weighted
                by_source[source] += weighted
                label = bucket_label(context)
                by_size[label] += weighted
                turns_by_size[label] += 1
                tools.update(name for name in item["tools"] if name)

                if count == 1:
                    first_context = context
                    first_seen = item["when"]
                last_seen = item["when"]

            if count:
                # The first turn is the always-resident prefix: instructions, memory,
                # skill catalog, tool schemas. Every later turn re-reads it.
                preamble_reread += first_context * count
                preambles.append(first_context)
                hours = ((last_seen - first_seen).total_seconds() / 3600
                         if first_seen and last_seen else 0.0)
                sessions[(source, project, session)] = (cost, count, peak, hours)

    if not total:
        print("No assistant turns in the last %d days for: %s" % (args.days, ", ".join(live)))
        return 1

    share = lambda value: 100 * value / total
    turn_total = sum(v[1] for v in sessions.values())

    print("=== %d-day burn: %.0fM weighted tokens, %d sessions, %d turns ===" % (
        args.days, total / 1e6, len(sessions), turn_total))
    if len(by_source) > 1:
        print("  " + "   ".join("%s %.0f%%" % (name, share(value))
                                for name, value in sorted(by_source.items())))

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
    for (source, project, session), (cost, count, peak, hours) in sorted(
            sessions.items(), key=lambda item: -item[1][0])[:10]:
        print("  %5.1f%%  turns=%-5d peak=%4.0fk  %4.1fh  %-6s %s %s" % (
            share(cost), count, peak / 1000, hours, source, (project or "?")[-36:],
            (session or "?")[:8]))

    print("\nTOOL CALLS")
    for name, value in tools.most_common(6):
        print("  %-28s %d" % (name, value))

    if unpriced:
        print("\nUNPRICED MODELS (counted at 1.0x -- %.0f%% of reported spend)"
              % share(unpriced_cost))
        for name, value in unpriced.most_common(5):
            print("  %-28s %d turns" % (name, value))
        print("  Add a ratio to MODEL_RATE to price these correctly.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
