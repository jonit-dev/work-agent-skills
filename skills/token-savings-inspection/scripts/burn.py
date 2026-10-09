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
import re
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


def turn(project, session, model, when, base_in, cache_read, cache_write, output, tools,
         reads=0, wakes=()):
    """One normalized assistant turn. Every source yields these and nothing else.

    reads: tool calls in this turn that read files or logs in the caller's own context.
    wakes: what arrived before this turn -- "human", "teammate", "task" or "peer" each.
    """
    return {
        "project": project, "session": session, "model": model, "when": when,
        "base_in": base_in, "cache_read": cache_read, "cache_write": cache_write,
        "output": output, "tools": tools, "reads": reads, "wakes": list(wakes),
    }


# A shell command that reads files or logs into the caller's context.
READ_COMMAND = re.compile(
    r"(?:^|&&|;|\|\||\n)\s*(?:sed -n|grep|rg|cat|head|tail|awk|jq|find|python3? -c?(?:\s|$))")
READ_TOOLS = {"Read", "Grep", "Glob"}


def is_read(name, command):
    return name in READ_TOOLS or bool(command and READ_COMMAND.search(command.strip()))


def classify_prompt(text):
    """What a user record means: a wakeup kind, a human prompt, or None (harness noise)."""
    if "<teammate-message" in text:
        return "teammate"
    if "<task-notification" in text:
        return "task"
    if "<cross-session-message" in text:
        return "peer"
    text = text.lstrip()
    if (not text or text.startswith("<") or text.startswith("This session is being continued")
            or text.startswith("Base directory for this skill")):
        return None
    return "human"


# --- Claude Code -----------------------------------------------------------

def claude_root():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(base, "projects")


def claude_files():
    return sorted(glob.glob(os.path.join(claude_root(), "*", "*.jsonl")))


def claude_user_wake(record):
    if record.get("isMeta"):
        return None
    content = (record.get("message") or {}).get("content")
    if isinstance(content, list):
        content = " ".join(b.get("text", "") for b in content
                           if isinstance(b, dict) and b.get("type") == "text")
    return classify_prompt(content) if isinstance(content, str) else None


def claude_title(path):
    """The session's latest custom or generated title, or None."""
    title = None
    with open(path, errors="replace") as fh:
        for line in fh:
            if '"customTitle"' in line or '"aiTitle"' in line:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                title = record.get("customTitle") or record.get("aiTitle") or title
    return title


def claude_turns(path):
    project = os.path.basename(os.path.dirname(path))
    session = os.path.basename(path)[:-6]
    wakes = []
    with open(path, errors="replace") as fh:
        for line in fh:
            is_user = '"user"' in line and '"tool_result"' not in line
            if '"assistant"' not in line and not is_user:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("type") == "user":
                kind = claude_user_wake(record)
                if kind:
                    wakes.append(kind)
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
            calls = [b for b in (message.get("content") or [])
                     if isinstance(b, dict) and b.get("type") == "tool_use"]
            tools = [b.get("name") for b in calls]
            reads = sum(is_read(b.get("name"), (b.get("input") or {}).get("command"))
                        for b in calls)
            yield turn(project, session, message.get("model"), when,
                       get("input_tokens"), get("cache_read_input_tokens"),
                       get("cache_creation_input_tokens"), get("output_tokens"), tools,
                       reads, wakes)
            wakes = []


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
    pending_reads = 0
    wakes = []
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
                pending_reads += is_read(None, str(payload.get("arguments") or ""))
                continue
            if payload.get("type") == "user_message":
                kind = classify_prompt(payload.get("message") or "")
                if kind:
                    wakes.append(kind)
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
            reads, pending_reads = pending_reads, 0
            yield turn(project, session, model, when,
                       max(get("input_tokens") - cached, 0), cached, 0,
                       get("output_tokens") + get("reasoning_output_tokens"), tools,
                       reads, wakes)
            wakes = []


SOURCES = {
    "claude": (claude_root, claude_files, claude_turns),
    "codex": (codex_root, codex_files, codex_turns),
}


def active_sources(requested):
    names = list(SOURCES) if requested == "all" else [requested]
    return [n for n in names if os.path.isdir(SOURCES[n][0]())]


# Thresholds for the per-session leak flags. Each one maps to a measured failure.
BENCH_WINDOW = 200_000        # the benchmark: same turns with context capped here
LATE_COMPACT_PEAK = 300_000   # context above this means auto-compact fires too late
CALLER_READS = 100            # reads the caller ran itself instead of delegating
WAKEUPS = 50                  # teammate/task/peer messages, each a full-context turn
TURNS_PER_PROMPT = 200        # an unbounded autonomous loop
LONG_LIVED_HOURS = 12         # one session carrying many unrelated tasks
MEMORY_INDEX_LINES = 200      # Claude Code loads only this many lines of MEMORY.md
COMPACT_WINDOW_MAX = 300_000


def session_flags(turns, peak, hours, reads, wakes):
    flags = []
    if peak > LATE_COMPACT_PEAK:
        flags.append("late compaction: peak %dk. Set autoCompactWindow to about 200000."
                     % (peak / 1000))
    if reads >= CALLER_READS:
        flags.append("caller reads: %d file/log reads in this session. Send them to a "
                     "cheap read-only agent." % reads)
    pings = wakes["teammate"] + wakes["task"] + wakes["peer"]
    if pings >= WAKEUPS:
        flags.append("wakeups: %d (teammate %d, task %d, peer %d). Ask for one report at "
                     "the end." % (pings, wakes["teammate"], wakes["task"], wakes["peer"]))
    if turns / max(wakes["human"], 1) >= TURNS_PER_PROMPT:
        flags.append("loop: %d turns for %d human prompts. Give the loop a stop condition "
                     "and a budget." % (turns, wakes["human"]))
    if hours >= LONG_LIVED_HOURS:
        flags.append("long-lived: %.0fh. Start one fresh session per task." % hours)
    return flags


def compact_window(settings_path):
    """The auto-compact window in tokens, the source that set it, or (None, None)."""
    env = os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
    if env:
        text = env.strip().lower()
        scale = {"k": 1_000, "m": 1_000_000}.get(text[-1:], 1)
        try:
            value = float(text.rstrip("km")) * scale
        except ValueError:
            return None, "env (unparsed: %s)" % env
        return int(value if value >= 1000 else value * 1000), "env"
    try:
        with open(settings_path) as fh:
            value = json.load(fh).get("autoCompactWindow")
    except (OSError, ValueError):
        return None, None
    return (int(value), "settings") if isinstance(value, (int, float)) else (None, None)


def config_checks(live):
    lines = []
    if "claude" in live:
        base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
        window, source = compact_window(os.path.join(base, "settings.json"))
        if window is None:
            lines.append("autoCompactWindow is unset: compaction waits for the model window "
                         "(about 1M on 1M models). Set \"autoCompactWindow\": 200000.")
        elif window > COMPACT_WINDOW_MAX:
            lines.append("autoCompactWindow is %dk (from %s): too high. Use about 200k."
                         % (window / 1000, source))
        else:
            lines.append("autoCompactWindow is %dk (from %s): ok." % (window / 1000, source))
        for index in glob.glob(os.path.join(base, "projects", "*", "memory", "MEMORY.md")):
            with open(index, errors="replace") as fh:
                count = sum(1 for _ in fh)
            if count > MEMORY_INDEX_LINES:
                lines.append("%s has %d lines: lines after %d are not loaded, so those "
                             "memories are invisible. Shorten it." % (index.replace(base, "~/.claude"
                             if base == os.path.expanduser("~/.claude") else base),
                             count, MEMORY_INDEX_LINES))
    return lines or ["none"]


def main():
    parser = argparse.ArgumentParser(description="Where the token budget actually went.")
    parser.add_argument("days", nargs="?", type=int, default=7)
    parser.add_argument("--source", default="all", choices=["all"] + list(SOURCES))
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--html", metavar="PATH", help="also write an HTML report to PATH")
    parser.add_argument("--weekly-budget", type=float, metavar="M",
                        help="weekly budget in millions of weighted tokens; draws a burndown line")
    parser.add_argument("--doctor", action="store_true",
                        help="print only the verdict, the leaks and their fixes; exit 1 on leaks")
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
    signals = {}
    timeline = collections.defaultdict(lambda: [0.0, 0.0])
    hourly = collections.defaultdict(lambda: {"bench": 0.0, "ctx": [], "reads": 0, "calls": 0})
    contexts = []
    totals = collections.Counter()
    titles = {}
    paths = {}

    for source in live:
        _, files, read = SOURCES[source]
        for path in files():
            if os.path.getmtime(path) < cutoff.timestamp():
                continue  # untouched since before the window: no turns inside it
            cost = 0.0
            reads = 0
            wakes = collections.Counter()
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
                hour = item["when"].replace(minute=0, second=0, microsecond=0)
                timeline[hour][context >= 300_000] += weighted
                # Benchmark: the same turn if auto-compact had kept context at BENCH_WINDOW.
                trimmed = max(item["cache_read"] - max(context - BENCH_WINDOW, 0), 0)
                slot = hourly[hour]
                slot["bench"] += weighted - (rate if rate is not None else 1.0) * (
                    CACHE_READ_RATE * (item["cache_read"] - trimmed))
                slot["ctx"].append(context)
                slot["reads"] += item["reads"]
                slot["calls"] += len(item["tools"])
                contexts.append(context)
                totals["tool_calls"] += len(item["tools"])
                totals["reads"] += item["reads"]
                reads += item["reads"]
                wakes.update(item["wakes"])
                totals.update(item["wakes"])

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
                signals[(source, project, session)] = (reads, wakes)
                paths[(source, project, session)] = path
                if source == "claude":
                    titles[(source, project, session)] = claude_title(path)

    if not total:
        print("No assistant turns in the last %d days for: %s" % (args.days, ", ".join(live)))
        return 1

    share = lambda value: 100 * value / total
    top = sorted(sessions.items(), key=lambda item: -item[1][0])[:10]
    buckets = []
    for low, high in SIZE_BUCKETS:
        label = "%dk+" % low if high is None else "%d-%dk" % (low, high)
        if by_size[label]:
            buckets.append((label, low, share(by_size[label]), turns_by_size[label]))
    preambles.sort()
    report = {
        "days": args.days, "total": total, "turns": sum(v[1] for v in sessions.values()),
        "session_count": len(sessions),
        "sources": [(n, share(v)) for n, v in sorted(by_source.items())],
        "buckets": buckets,
        "over_300k": sum(b[2] for b in buckets if b[1] >= 300),
        "preamble": (preambles[len(preambles) // 2], preambles[int(len(preambles) * 0.9)],
                     100 * preamble_reread / all_context) if preambles else None,
        "projects": [(n, share(v)) for n, v in
                     sorted(by_project.items(), key=lambda kv: -kv[1])[:8]],
        "sessions": [{
            "source": key[0], "project": key[1] or "?", "id": (key[2] or "?")[:8],
            "title": titles.get(key), "path": paths.get(key), "share": share(cost), "turns": count,
            "peak": peak, "hours": hours, "flags": session_flags(count, peak, hours,
                                                                 *signals[key]),
        } for key, (cost, count, peak, hours) in top],
        "tools": tools.most_common(6),
        "config": config_checks(live),
        "unpriced": (share(unpriced_cost), unpriced.most_common(5)) if unpriced else None,
    }
    contexts.sort()
    report["timeline"] = sorted(timeline.items())
    report["hourly"] = sorted(hourly.items())
    report["bench_total"] = sum(v["bench"] for v in hourly.values())
    report["budget"] = args.weekly_budget * 1e6 if args.weekly_budget else None
    report["baseline"] = baseline(report, contexts, totals)
    if args.html:
        os.makedirs(os.path.dirname(os.path.abspath(args.html)), exist_ok=True)
        with open(args.html, "w") as fh:
            fh.write(render_html(report))
    if args.doctor:
        return print_doctor(report, args.html)
    print_text(report)
    if args.html:
        print("\nHTML report: %s" % os.path.abspath(args.html))
    return 0


def print_doctor(r, html_path):
    """The doctor verdict: each leak with its share and fix, then the baseline gaps."""
    issues = top_issues(r)
    print("TOKEN DOCTOR: last %d days, %.0fM weighted tokens, %d sessions" % (
        r["days"], r["total"] / 1e6, r["session_count"]))
    if not issues:
        print("Verdict: healthy. No common token leaks found.")
    else:
        print("Verdict: %d leak%s found, largest first.\n" % (len(issues),
                                                           "" if len(issues) == 1 else "s"))
    for n, issue in enumerate(issues, 1):
        where = ("%.0f%% of spend, %d sessions" % (issue["share"], len(issue["hits"]))
                 if issue["share"] is not None else "config")
        print("%d. %s (%s)" % (n, issue["title"], where))
        print("   Fix: %s" % issue["fix"])
        worst = sorted(issue["hits"], key=lambda h: -h[0]["share"])[:2]
        for s, flag in worst:
            print("   e.g. %s: %s" % ((s["title"] or s["id"])[:40], flag.split(".")[0]))
    print("\nBenchmark: the same turns at a %dk compaction window would cost about %.0fM "
          "(%.0f%% less). Estimate: trims cached context only." % (
              BENCH_WINDOW / 1000, r["bench_total"] / 1e6,
              100 * (1 - r["bench_total"] / r["total"])))
    gaps = [row for row in r["baseline"] if not row[3]]
    if gaps:
        print("\nBaseline gaps (now -> recommended):")
        for name, now, target, _ in gaps:
            print("  %-28s %-18s %s" % (name, now, target))
    if html_path:
        print("\nReport: %s" % os.path.abspath(html_path))
        print("Open it and press \"Copy for Claude\" on a leak to hand over the fix with evidence.")
    return 1 if issues else 0


def baseline(r, contexts, totals):
    """Current value against a recommended target for each lever. (name, now, target, ok)."""
    window, _ = compact_window(os.path.join(
        os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"), "settings.json"))
    median = contexts[len(contexts) // 2] if contexts else 0
    pings = totals["teammate"] + totals["task"] + totals["peer"]
    sessions = max(r["session_count"], 1)
    rows = [
        ("Spend on turns over 300k", "%.0f%%" % r["over_300k"], "under 10%",
         r["over_300k"] < 10),
        ("Median context per turn", "%dk" % (median / 1000), "under 150k", median < 150_000),
        ("autoCompactWindow", "%dk" % (window / 1000) if window else "unset (model max)",
         "about 200k", bool(window) and window <= COMPACT_WINDOW_MAX),
        ("Turns per human prompt", "%.0f" % (r["turns"] / max(totals["human"], 1)),
         "under 50", r["turns"] / max(totals["human"], 1) < 50),
        ("Caller reads per tool call", "%.0f%%" % (100 * totals["reads"]
                                                   / max(totals["tool_calls"], 1)),
         "under 20%", totals["reads"] / max(totals["tool_calls"], 1) < 0.2),
        ("Wakeups per session", "%.0f" % (pings / sessions), "under 20", pings / sessions < 20),
        ("Longest top session", "%.0fh" % max((s["hours"] for s in r["sessions"]), default=0),
         "under %dh" % LONG_LIVED_HOURS,
         all(s["hours"] < LONG_LIVED_HOURS for s in r["sessions"])),
    ]
    if r["preamble"]:
        rows.append(("Preamble per session (p50)", "%dk" % (r["preamble"][0] / 1000),
                     "under 40k", r["preamble"][0] < 40_000))
    return rows


def print_text(r):
    print("=== %d-day burn: %.0fM weighted tokens, %d sessions, %d turns ===" % (
        r["days"], r["total"] / 1e6, r["session_count"], r["turns"]))
    if len(r["sources"]) > 1:
        print("  " + "   ".join("%s %.0f%%" % s for s in r["sources"]))

    print("\nSPEND BY CONTEXT SIZE OF THE TURN   <- the main lever")
    for label, _, pct, turns in r["buckets"]:
        print("  %-12s %6.1f%%   %6d turns" % (label, pct, turns))
    print("  --> %.0f%% of spend is on turns carrying more than 300k of context"
          % r["over_300k"])

    if r["preamble"]:
        print("\nALWAYS-RESIDENT PREAMBLE (instructions, memory, skill catalog, tool schemas)")
        print("  p50=%dk  p90=%dk per session  ->  %.0f%% of every token read" % (
            r["preamble"][0] / 1000, r["preamble"][1] / 1000, r["preamble"][2]))
        print("  Prune it once, then leave it stable: reads bill at %.1fx but rewrites at %.2fx."
              % (CACHE_READ_RATE, CACHE_WRITE_RATE))

    print("\nTOP PROJECTS")
    for name, pct in r["projects"]:
        print("  %6.1f%%  %s" % (pct, name[-58:]))

    print("\nTOP SESSIONS (the long ones are where the budget goes)")
    for s in r["sessions"]:
        print("  %5.1f%%  turns=%-5d peak=%4.0fk  %4.1fh  %-6s %s %s  %s" % (
            s["share"], s["turns"], s["peak"] / 1000, s["hours"], s["source"],
            s["project"][-36:], s["id"], (s["title"] or "")[:50]))

    print("\nTOOL CALLS")
    for name, value in r["tools"]:
        print("  %-28s %d" % (name, value))

    print("\nLEAK CHECKS (top sessions; each flag names its fix)")
    flagged = [s for s in r["sessions"] if s["flags"]]
    for s in flagged:
        print("  %5.1f%%  %s %s  %s" % (s["share"], s["source"], s["id"], s["title"] or ""))
        for flag in s["flags"]:
            print("          - " + flag)
    if not flagged:
        print("  none")

    print("\nCONFIG CHECKS")
    for line in r["config"]:
        print("  - " + line)

    print("\nBASELINE (now -> recommended)")
    for name, now, target, ok in r["baseline"]:
        print("  %-4s %-28s %-18s %s" % ("ok" if ok else "FIX", name, now, target))

    if r["unpriced"]:
        print("\nUNPRICED MODELS (counted at 1.0x -- %.0f%% of reported spend)" % r["unpriced"][0])
        for name, value in r["unpriced"][1]:
            print("  %-28s %d turns" % (name, value))
        print("  Add a ratio to MODEL_RATE to price these correctly.")


# Per leak flag prefix: short fix, title, why it costs tokens, and the prompt for an agent.
ISSUES = {
    "late compaction": (
        "Set autoCompactWindow to about 200000, then /compact or restart old sessions.",
        "Sessions compact too late",
        "Every tool call re-reads the whole context. A turn at 500k costs about 5 times a "
        "turn at 100k, and auto-compact on a 1M model waits until about 1M.",
        "Set \"autoCompactWindow\": 200000 in ~/.claude/settings.json and check that "
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW is unset or not higher. Then ask me to /compact or "
        "restart each listed session that is still open."),
    "caller reads": (
        "Send multi-range reads, greps and log parsing to a cheap read-only subagent.",
        "The caller reads files and logs itself",
        "Each read in the main session is paid at its full context size. A cheap read-only "
        "subagent pays it at a small context and returns a short answer.",
        "Read the listed transcripts (JSONL, tool_use blocks named Bash/Read/Grep) and find the "
        "most repeated read commands. Then add a rule to my global agent instructions: after "
        "the brief, any read that is more than one bounded range goes to a cheap read-only "
        "subagent. Propose a helper script for any read pattern that repeats more than 20 times."),
    "wakeups": (
        "Ask subagents and teammates for one report at the end; wait with one blocking command.",
        "Too many wakeups",
        "Each teammate message, task notification or cross-session message starts a turn "
        "that re-reads the full context.",
        "Read the listed transcripts and find which subagents, teammates or background jobs "
        "sent the messages. Change their briefs so they report once at the end, and replace "
        "polling or progress pings with one blocking background command per wait."),
    "loop": (
        "Give each /goal or autonomous loop a stop condition and a turn or time budget.",
        "Autonomous loops run without a budget",
        "Hundreds of turns per human prompt means a /goal or autonomous loop kept going with "
        "no stop condition.",
        "Read the listed transcripts and name what kept each loop running. Then add a stop "
        "condition and a turn or time budget to the loop instructions I use (goal prompts, "
        "skills or CLAUDE.md)."),
    "long-lived": (
        "Commit, end the session, and start one fresh session per task.",
        "Sessions stay open too long",
        "A session open for many hours carries summaries of many unrelated tasks, so every "
        "turn pays for old work.",
        "List which of these sessions are still open. For each, commit its work, end it, and "
        "write a one-paragraph handoff so a fresh session can continue from the PRD or task."),
}


def top_issues(r):
    """Group session flags and failed config checks into issues, largest spend share first."""
    groups = {}
    for s in r["sessions"]:
        for flag in s["flags"]:
            groups.setdefault(flag.split(":")[0], []).append((s, flag))
    issues = []
    for kind, hits in groups.items():
        fix, title, why, action = ISSUES[kind]
        issues.append({"title": title, "why": why, "action": action, "fix": fix,
                       "share": sum(s["share"] for s, _ in hits), "hits": hits})
    issues.sort(key=lambda i: -i["share"])
    fixed = [line for line in r["config"] if "autoCompactWindow" in line and line.endswith("ok.")]
    for issue in issues:
        if issue["title"] == ISSUES["late compaction"][1] and fixed:
            issue["fix"] = "Setting already ok. Restart or /compact the old sessions."
            issue["action"] = ("The setting is already fixed (%s). Restart or /compact the "
                               "listed sessions that are still open; new sessions are covered."
                               % fixed[0])
    for line in r["config"]:
        if not (line.endswith("ok.") or line == "none"):
            title = ("autoCompactWindow" if "autoCompactWindow" in line
                     else "memory index too long" if "MEMORY.md" in line else line[:40])
            fix = ("Shorten MEMORY.md under %d lines; move detail into topic files."
                   % MEMORY_INDEX_LINES if "MEMORY.md" in line else line)
            issues.append({"title": "Config: " + title, "why": line, "fix": fix,
                           "action": "Fix this config problem: " + line, "share": None,
                           "hits": []})
    return issues


def issue_prompt(issue, r):
    lines = ["Token leak to fix: %s." % issue["title"]]
    if issue["share"] is not None:
        lines.append("It affects %d of my top sessions, %.0f%% of Claude Code spend in the last "
                     "%d days (burn.py, base-input-equivalent tokens)."
                     % (len(issue["hits"]), issue["share"], r["days"]))
    lines += ["", "Why it costs tokens: " + issue["why"]]
    if issue["hits"]:
        lines += ["", "Evidence:"]
        for s, flag in issue["hits"]:
            lines.append("- %s (session %s, %.1f%% of spend, %d turns, peak %dk, %.0fh): %s" % (
                s["title"] or "untitled", s["id"], s["share"], s["turns"], s["peak"] / 1000,
                s["hours"], flag))
            if s["path"]:
                lines.append("  transcript: %s" % s["path"])
    lines += ["", "What to do: " + issue["action"],
              "", "Report what you changed and how to check that it worked."]
    return "\n".join(lines)


COPY_SCRIPT = """
function copyText(id, btn){const t=document.getElementById(id).value;
const done=()=>{const o=btn.textContent;btn.textContent='Copied';setTimeout(()=>btn.textContent=o,1500)};
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(done,()=>fallback(t,done))}
else{fallback(t,done)}}
function fallback(t,done){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);
a.select();try{document.execCommand('copy');done()}catch(e){}a.remove()}
"""


HTML_STYLE = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e4e4df;
--bar:#3b6fd8;--hot:#d2483c;--ok:#2f8a4e;--chip:#fbeae8}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141413;--card:#1e1e1c;
--ink:#ecece8;--muted:#9c9c96;--line:#33332f;--bar:#5b8ae6;--hot:#e0665a;--ok:#5cc07f;--chip:#3a2422}}
:root[data-theme=dark]{--bg:#141413;--card:#1e1e1c;--ink:#ecece8;--muted:#9c9c96;--line:#33332f;
--bar:#5b8ae6;--hot:#e0665a;--ok:#5cc07f;--chip:#3a2422}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.45 system-ui,sans-serif}main{max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:18px;margin:0}h2{font-size:13px;text-transform:uppercase;letter-spacing:.04em;
color:var(--muted);margin:18px 0 6px;font-weight:600}.muted{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.top{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.verdict{font-size:15px;margin-top:2px}.verdict b.bad{color:var(--hot)}.verdict b.ok{color:var(--ok)}
.stats{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px}.stats div b{font-size:17px;margin-right:4px}
.issue{display:grid;grid-template-columns:24px minmax(0,1fr) 120px auto;gap:10px;align-items:start;
padding:8px 0;border-top:1px solid var(--line)}.issue:first-child{border-top:0}
.issue .n{font-weight:700;color:var(--hot)}.issue .t{font-weight:600}.issue .fix{color:var(--muted)}
.share{font-size:12px;color:var(--muted)}.track{background:var(--line);border-radius:3px;height:6px;
overflow:hidden;margin-top:3px}.fill{background:var(--bar);height:100%}.fill.hot{background:var(--hot)}
button{font:inherit;font-size:12px;border:1px solid var(--line);background:transparent;color:var(--ink);
border-radius:6px;padding:4px 9px;cursor:pointer;white-space:nowrap}button.primary{background:var(--bar);
border-color:var(--bar);color:#fff}details>summary{cursor:pointer;color:var(--muted);font-size:12px}
pre{white-space:pre-wrap;word-break:break-word;font-size:12px;background:var(--bg);border:1px solid
var(--line);border-radius:6px;padding:8px;margin:6px 0 0}textarea.src{position:absolute;left:-9999px;
width:1px;height:1px}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:5px 6px;
border-top:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:500;border:0;
font-size:12px}.scroll{overflow-x:auto}.ok{color:var(--ok)}.bad{color:var(--hot)}
.flag{display:inline-block;background:var(--chip);border-radius:4px;padding:1px 6px;margin:1px 2px 1px 0;
font-size:12px}.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.row{display:grid;grid-template-columns:80px 1fr 110px;gap:8px;align-items:center;margin:4px 0;font-size:13px}
.row .track{height:10px;margin:0}.more{margin-top:18px}.more>summary{font-size:13px;color:var(--ink);font-weight:600}
.chart{width:100%;min-width:560px;height:auto;display:block}.chart rect.c{fill:var(--bar)}
.chart rect.h{fill:var(--hot)}.chart line{stroke:var(--line);stroke-width:1}
.chart line.base{stroke:var(--muted)}.chart text{fill:var(--muted);font-size:11px;text-anchor:end}
.chart text.x{text-anchor:start}.legend{display:flex;gap:14px;font-size:12px;color:var(--muted)}
.legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px}
.legend i.c{background:var(--bar)}.legend i.h{background:var(--hot)}
.chart path{fill:none;stroke-width:2}.chart path.actual{stroke:var(--hot)}
.chart path.bench{stroke:var(--bar);stroke-dasharray:6 4}.chart path.budget{stroke:var(--muted);
stroke-dasharray:2 4}.chart rect.hit{fill:transparent}.chart text.end{text-anchor:end;fill:var(--ink)}
.legend i.b{background:var(--muted)}.kpis{display:grid;grid-template-columns:repeat(auto-fit,
minmax(260px,1fr));gap:10px;margin-top:10px}.kpi b{font-size:16px}.spark{width:100%;height:70px;
display:block;margin:4px 0}.spark polyline{fill:none;stroke:var(--muted);stroke-width:1.5}
.spark circle.c{fill:var(--bar)}.spark circle.h{fill:var(--hot)}.spark line.target{stroke:var(--ok);
stroke-dasharray:4 3;stroke-width:1.5}
@media (max-width:640px){.issue{grid-template-columns:20px minmax(0,1fr)}.issue .share,.issue .act{grid-column:2}}
"""


def render_timeline(timeline):
    """Hourly stacked bars: spend under 300k (blue) and over 300k (red), as inline SVG."""
    if not timeline:
        return ""
    from html import escape as e
    width, height, left, bottom = 960, 150, 40, 20
    peak = max(a + b for _, (a, b) in timeline) or 1
    start, end = timeline[0][0], timeline[-1][0]
    hours = int((end - start).total_seconds() // 3600) + 1
    step = (width - left) / hours
    bar = max(step - 2, 1)
    scale = (height - bottom - 6) / peak
    marks = []
    for when, (cool, hot) in timeline:
        x = left + int((when - start).total_seconds() // 3600) * step
        tip = "%s  under 300k: %.1fM  over 300k: %.1fM" % (
            when.astimezone().strftime("%a %H:00"), cool / 1e6, hot / 1e6)
        y = height - bottom
        for value, css in ((cool, "c"), (hot, "h")):
            if value:
                h = max(value * scale - (2 if css == "h" and cool else 0), 1)
                y -= value * scale
                marks.append('<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                             'rx="2"><title>%s</title></rect>' % (css, x, y, bar, h, e(tip)))
    grid = []
    for frac in (0.5, 1.0):
        y = height - bottom - peak * frac * scale
        grid.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text x="%d" y="%.1f">%.0fM'
                    '</text>' % (left, width, y, y, left - 6, y + 4, peak * frac / 1e6))
    labels = []
    for n in range(0, hours, max(hours // 8, 1)):
        when = start + datetime.timedelta(hours=n)
        labels.append('<text class="x" x="%.1f" y="%d">%s</text>' % (
            left + n * step, height - 5, when.astimezone().strftime("%a %H:00")))
    return ('<div class="card scroll"><div class="top"><div class="legend">'
            '<span><i class="c"></i>turns under 300k context</span>'
            '<span><i class="h"></i>turns over 300k context</span></div>'
            '<span class="muted" style="font-size:12px">weighted tokens per hour · hover a bar'
            '</span></div><svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Hourly '
            'weighted token spend, split by context size">%s%s%s<line class="base" x1="%d" '
            'x2="%d" y1="%d" y2="%d"/></svg></div>' % (
                width, height, "".join(grid), "".join(marks), "".join(labels), left, width,
                height - bottom, height - bottom))


def _scale_fn(lo, hi, a, b):
    return lambda v: a + (b - a) * ((v - lo) / ((hi - lo) or 1))


def render_burndown(r):
    """Cumulative spend against the benchmark and an optional weekly budget, as inline SVG."""
    from html import escape as e
    rows = r["hourly"]
    if len(rows) < 2:
        return ""
    actual = dict(r["timeline"])
    start, end = rows[0][0], rows[-1][0] + datetime.timedelta(hours=1)
    width, height, left, bottom = 960, 190, 48, 20
    run_a = run_b = 0.0
    pts_a, pts_b, cols = [], [], []
    for when, slot in rows:
        run_a += sum(actual.get(when, (0, 0)))
        run_b += slot["bench"]
        pts_a.append((when + datetime.timedelta(hours=1), run_a))
        pts_b.append((when + datetime.timedelta(hours=1), run_b))
    budget_end = None
    top = run_a
    if r["budget"]:
        per_hour = r["budget"] / (7 * 24)
        top = max(top, per_hour * (end - start).total_seconds() / 3600)
        rate_now = run_a / max((end - start).total_seconds() / 3600, 1)
        budget_end = start + datetime.timedelta(hours=r["budget"] / max(rate_now, 1))
    x = _scale_fn(start.timestamp(), end.timestamp(), left, width)
    y = _scale_fn(0, top * 1.05, height - bottom, 6)
    path = lambda pts: "M%.1f,%.1f " % (x(start.timestamp()), y(0)) + " ".join(
        "L%.1f,%.1f" % (x(t.timestamp()), y(v)) for t, v in pts)
    parts = ['<line class="base" x1="%d" x2="%d" y1="%d" y2="%d"/>' % (
        left, width, height - bottom, height - bottom)]
    for frac in (0.5, 1.0):
        v = top * frac
        parts.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text x="%d" y="%.1f">%.0fM'
                     '</text>' % (left, width, y(v), y(v), left - 6, y(v) + 4, v / 1e6))
    if r["budget"]:
        hours = (end - start).total_seconds() / 3600
        parts.append('<path class="budget" d="M%.1f,%.1f L%.1f,%.1f"/>' % (
            x(start.timestamp()), y(0), x(end.timestamp()), y(r["budget"] / 168 * hours)))
    parts.append('<path class="bench" d="%s"/>' % path(pts_b))
    parts.append('<path class="actual" d="%s"/>' % path(pts_a))
    for (t, va), (_, vb) in zip(pts_a, pts_b):
        parts.append('<rect class="hit" x="%.1f" y="0" width="%.1f" height="%d"><title>%s  '
                     'actual %.0fM · benchmark %.0fM</title></rect>' % (
                         x(t.timestamp()) - 6, 12, height - bottom,
                         e(t.astimezone().strftime("%a %H:00")), va / 1e6, vb / 1e6))
    parts.append('<text class="end" x="%.1f" y="%.1f">%.0fM</text>' % (
        width - 2, y(run_a) - 4, run_a / 1e6))
    parts.append('<text class="end" x="%.1f" y="%.1f">%.0fM</text>' % (
        width - 2, y(run_b) - 4, run_b / 1e6))
    note = "Benchmark saves %.0f%% (estimate: same turns, cached context trimmed to %dk)." % (
        100 * (1 - run_b / run_a), BENCH_WINDOW / 1000)
    if budget_end:
        note += " At the current rate the weekly budget runs out %s." % (
            budget_end.astimezone().strftime("%a %d %b %H:00"))
    legend = ('<span><i class="h"></i>actual cumulative spend</span><span><i class="c"></i>'
              'benchmark: %dk compaction window</span>%s' % (
                  BENCH_WINDOW / 1000, '<span><i class="b"></i>weekly budget pace</span>'
                  if r["budget"] else ""))
    return ('<div class="card scroll"><div class="top"><div class="legend">%s</div></div>'
            '<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Cumulative token '
            'spend against benchmark">%s</svg><div class="muted" style="font-size:12px">%s'
            '</div></div>' % (legend, width, height, "".join(parts), e(note)))


def render_kpis(r):
    """Small multiples: each KPI per 3-hour block against its target line."""
    from html import escape as e
    blocks = collections.OrderedDict()
    for when, slot in r["hourly"]:
        key = when.replace(hour=when.hour - when.hour % 3)
        b = blocks.setdefault(key, {"ctx": [], "reads": 0, "calls": 0})
        b["ctx"] += slot["ctx"]
        b["reads"] += slot["reads"]
        b["calls"] += slot["calls"]
    if len(blocks) < 2:
        return ""
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
    kpis = [
        ("Median context per turn", 150_000, lambda v: "%dk" % (v / 1000),
         [med(b["ctx"]) for b in blocks.values()]),
        ("Turns over 300k context", 0.10, lambda v: "%.0f%%" % (100 * v),
         [sum(c >= 300_000 for c in b["ctx"]) / max(len(b["ctx"]), 1) for b in blocks.values()]),
        ("Caller reads per tool call", 0.20, lambda v: "%.0f%%" % (100 * v),
         [b["reads"] / max(b["calls"], 1) for b in blocks.values()]),
    ]
    cards = []
    w, h, pad = 300, 70, 4
    for name, target, fmt, vals in kpis:
        top = max(max(vals), target) * 1.1 or 1
        x = _scale_fn(0, len(vals) - 1, pad, w - pad)
        y = _scale_fn(0, top, h - pad, pad)
        line = " ".join("%.1f,%.1f" % (x(i), y(v)) for i, v in enumerate(vals))
        dots = "".join('<circle class="%s" cx="%.1f" cy="%.1f" r="2.5"><title>%s</title></circle>'
                       % ("h" if v > target else "c", x(i), y(v), fmt(v))
                       for i, v in enumerate(vals))
        last = vals[-1]
        cards.append('<div class="card kpi"><div class="top"><span>%s</span><b class="%s">%s'
                     '</b></div><svg class="spark" viewBox="0 0 %d %d" role="img" aria-label="%s'
                     ' per 3 hours"><line class="target" x1="0" x2="%d" y1="%.1f" y2="%.1f"/>'
                     '<polyline points="%s"/>%s</svg><div class="muted" style="font-size:12px">'
                     'target %s · latest block %s · per 3 hours</div></div>' % (
                         e(name), "bad" if last > target else "ok", fmt(last), w, h, e(name), w,
                         y(target), y(target), line, dots, fmt(target), fmt(last)))
    return '<div class="kpis">%s</div>' % "".join(cards)


def render_html(r):
    from html import escape as e
    bar = lambda pct, hot=False: ('<div class="track"><div class="fill%s" style="width:%.1f%%">'
                                  '</div></div>' % (" hot" if hot else "", min(pct, 100)))
    issues = top_issues(r)
    prompts = [issue_prompt(i, r) for i in issues]
    gaps = [row for row in r["baseline"] if not row[3]]
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>Token Doctor</title><style>%s</style><script>%s</script></head>'
           '<body><main>' % (HTML_STYLE, COPY_SCRIPT)]

    # 1. Verdict and the one action that matters most.
    verdict = ('<b class="bad">%d leak%s found</b> · %.0f%% of spend is on turns over 300k '
               'context' % (len(issues), "" if len(issues) == 1 else "s", r["over_300k"])
               if issues else '<b class="ok">Healthy</b> · no common token leaks found')
    copy_all = ""
    if issues:
        everything = "\n\n---\n\n".join(
            ["Here are the top token leaks from my token doctor report, largest first. Fix "
             "them in this order and report after each one."] + prompts)
        copy_all = ('<textarea class="src" id="p-all" readonly>%s</textarea><button '
                    'class="primary" onclick="copyText(\'p-all\',this)">Copy all fixes for '
                    'Claude</button>' % e(everything))
    out.append('<div class="top"><div><h1>Token Doctor</h1><div class="verdict">%s</div></div>'
               '%s</div>' % (verdict, copy_all))
    stats = [("%.0fM" % (r["total"] / 1e6), "weighted tokens"),
             ("%d" % r["session_count"], "sessions"), ("%d" % r["turns"], "turns"),
             ("%d/%d" % (len(gaps), len(r["baseline"])), "baseline levers off target")]
    out.append('<div class="stats muted">%s<span>last %d days · %s</span></div>' % (
        "".join('<div><b style="color:var(--ink)">%s</b>%s</div>' % s for s in stats),
        r["days"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))

    # 2. KPI monitor: burndown against the benchmark, then each KPI against its target.
    out.append('<h2>Burndown vs benchmark</h2>' + render_burndown(r) + render_kpis(r))

    # 3. The leaks, ranked, one row each.
    if issues:
        out.append('<h2>Leaks to fix, largest first</h2><div class="card">')
        for n, (issue, prompt) in enumerate(zip(issues, prompts), 1):
            share = ('%.0f%% of spend · %d sessions%s' % (
                issue["share"], len(issue["hits"]), bar(issue["share"], True))
                if issue["share"] is not None else "config")
            out.append('<div class="issue"><span class="n">%d</span><div><div class="t">%s</div>'
                       '<div class="fix">%s</div><details><summary>evidence and prompt'
                       '</summary><pre>%s</pre></details></div><div class="share">%s</div>'
                       '<div class="act"><textarea class="src" id="p-%d" readonly>%s</textarea>'
                       '<button onclick="copyText(\'p-%d\',this)">Copy for Claude</button></div>'
                       '</div>' % (n, e(issue["title"]), e(issue["fix"]), e(prompt), share, n,
                                   e(prompt), n))
        out.append('</div>')

    # 4. Baseline: off-target levers first.
    rows = sorted(r["baseline"], key=lambda row: row[3])
    out.append('<h2>Baseline: now vs recommended</h2><div class="card scroll"><table><tr>'
               '<th>Lever</th><th>Now</th><th>Recommended</th><th></th></tr>%s</table></div>'
               % "".join('<tr><td>%s</td><td><b>%s</b></td><td class="muted">%s</td>'
                         '<td class="%s">%s</td></tr>' % (
                             e(n), e(v), e(t), "ok" if ok else "bad", "ok" if ok else "fix")
                         for n, v, t, ok in rows))

    out.append('<h2>Spend per hour</h2>' + render_timeline(r["timeline"]))

    # 5. Everything else, collapsed.
    out.append('<details class="more"><summary>Sessions, context sizes, projects, config'
               '</summary>')
    out.append('<h2>Top sessions</h2><div class="card scroll"><table><tr><th>Share</th>'
               '<th>Session</th><th>Turns</th><th>Peak</th><th>Age</th><th>Leaks</th></tr>')
    for s in r["sessions"]:
        flags = "".join('<span class="flag">%s</span>' % e(f.split(".")[0])
                        for f in s["flags"]) or '<span class="ok">none</span>'
        out.append('<tr><td>%.1f%%</td><td><b>%s</b><br><span class="muted">%s %s</span></td>'
                   '<td>%d</td><td>%dk</td><td>%.0fh</td><td>%s</td></tr>' % (
                       s["share"], e(s["title"] or "(untitled)"), s["source"], s["id"],
                       s["turns"], s["peak"] / 1000, s["hours"], flags))
    out.append('</table></div><div class="grid2"><div><h2>Spend by context size</h2>'
               '<div class="card">')
    for label, low, pct, turns in r["buckets"]:
        out.append('<div class="row"><span>%s</span>%s<span class="muted">%.1f%% · %d</span>'
                   '</div>' % (label, bar(pct, low >= 300), pct, turns))
    out.append('</div></div><div><h2>Top projects</h2><div class="card">')
    for name, pct in r["projects"]:
        out.append('<div class="row"><span>%.1f%%</span>%s<span class="muted" style="overflow:'
                   'hidden;text-overflow:ellipsis;white-space:nowrap">%s</span></div>' % (
                       pct, bar(pct), e(name[-40:])))
    out.append('</div></div></div>')
    out.append('<h2>Config checks</h2><div class="card">%s</div>' % "".join(
        '<div class="%s">%s</div>' % ("ok" if line.endswith("ok.") or line == "none" else "bad",
                                      e(line)) for line in r["config"]))
    out.append('<h2>Tool calls</h2><div class="card">%s</div>' % " · ".join(
        "%s <b>%d</b>" % (e(n or "?"), v) for n, v in r["tools"]))
    if r["unpriced"]:
        out.append('<h2>Unpriced models</h2><div class="card bad">Counted at 1.0x: %.0f%% of '
                   'spend. %s</div>' % (r["unpriced"][0], e(", ".join(
                       "%s (%d turns)" % m for m in r["unpriced"][1]))))
    out.append('<p class="muted" style="font-size:12px">Units are base-input-equivalent '
               'tokens. Generated by token-savings-inspection burn.py.</p></details>')
    out.append("</main></body></html>\n")
    return "\n".join(out)

if __name__ == "__main__":
    sys.exit(main())
