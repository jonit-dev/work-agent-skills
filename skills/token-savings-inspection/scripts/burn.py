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
    titles = {}

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
                reads += item["reads"]
                wakes.update(item["wakes"])

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
            "title": titles.get(key), "share": share(cost), "turns": count,
            "peak": peak, "hours": hours, "flags": session_flags(count, peak, hours,
                                                                 *signals[key]),
        } for key, (cost, count, peak, hours) in top],
        "tools": tools.most_common(6),
        "config": config_checks(live),
        "unpriced": (share(unpriced_cost), unpriced.most_common(5)) if unpriced else None,
    }
    print_text(report)
    if args.html:
        with open(args.html, "w") as fh:
            fh.write(render_html(report))
        print("\nHTML report: %s" % os.path.abspath(args.html))
    return 0


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

    if r["unpriced"]:
        print("\nUNPRICED MODELS (counted at 1.0x -- %.0f%% of reported spend)" % r["unpriced"][0])
        for name, value in r["unpriced"][1]:
            print("  %-28s %d turns" % (name, value))
        print("  Add a ratio to MODEL_RATE to price these correctly.")


HTML_STYLE = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e4e4df;
--bar:#3b6fd8;--hot:#d2483c;--ok:#2f8a4e;--chip:#fbeae8}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141413;--card:#1e1e1c;
--ink:#ecece8;--muted:#9c9c96;--line:#33332f;--bar:#6e9bf0;--hot:#f07a6e;--ok:#5cc07f;--chip:#3a2422}}
:root[data-theme=dark]{--bg:#141413;--card:#1e1e1c;--ink:#ecece8;--muted:#9c9c96;--line:#33332f;
--bar:#6e9bf0;--hot:#f07a6e;--ok:#5cc07f;--chip:#3a2422}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,sans-serif}main{max-width:1040px;margin:0 auto;padding:24px 16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 10px}
.muted{color:var(--muted)}.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
gap:10px;margin-top:16px}.tile,.card{background:var(--card);border:1px solid var(--line);
border-radius:10px;padding:12px 14px}.tile b{display:block;font-size:22px}
.row{display:grid;grid-template-columns:90px 1fr 150px;gap:10px;align-items:center;margin:6px 0}
.track{background:var(--line);border-radius:4px;height:14px;overflow:hidden}
.fill{background:var(--bar);height:100%}.fill.hot{background:var(--hot)}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px 6px;
border-top:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:500;border:0}
.scroll{overflow-x:auto}.flag{display:block;background:var(--chip);border-radius:6px;
padding:3px 8px;margin:3px 0;font-size:13px}.ok{color:var(--ok)}.bad{color:var(--hot)}
code{font-size:13px}
"""


def render_html(r):
    from html import escape as e
    bar = lambda pct, hot=False: ('<div class="track"><div class="fill%s" style="width:%.1f%%">'
                                  '</div></div>' % (" hot" if hot else "", min(pct, 100)))
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>Token Burn Report</title><style>%s</style></head><body><main>' % HTML_STYLE,
           '<h1>Token burn: last %d days</h1><div class="muted">Generated %s by '
           '<code>burn.py</code>. Units are base-input-equivalent tokens.</div>' % (
               r["days"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))]
    tiles = [("%.0fM" % (r["total"] / 1e6), "weighted tokens"),
             ("%d" % r["session_count"], "sessions"), ("%d" % r["turns"], "turns"),
             ("%.0f%%" % r["over_300k"], "spend on turns over 300k")]
    if r["preamble"]:
        tiles.append(("%dk" % (r["preamble"][0] / 1000), "preamble per session (p50)"))
    out.append('<div class="tiles">%s</div>' % "".join(
        '<div class="tile"><b>%s</b><span class="muted">%s</span></div>' % t for t in tiles))

    out.append('<h2>Spend by context size of the turn</h2><div class="card">')
    for label, low, pct, turns in r["buckets"]:
        out.append('<div class="row"><span>%s</span>%s<span class="muted">%.1f%% · %d turns'
                   '</span></div>' % (label, bar(pct, low >= 300), pct, turns))
    out.append('<p class="muted">Cost per turn scales with context. Red buckets are turns '
               'over 300k: compact earlier or start fresh sessions.</p></div>')

    out.append('<h2>Top sessions and leak checks</h2><div class="card scroll"><table>'
               '<tr><th>Share</th><th>Session</th><th>Turns</th><th>Peak</th><th>Age</th>'
               '<th>Leaks and fixes</th></tr>')
    for s in r["sessions"]:
        flags = "".join('<span class="flag">%s</span>' % e(f) for f in s["flags"]) or \
            '<span class="ok">none</span>'
        out.append('<tr><td>%.1f%%%s</td><td><b>%s</b><br><span class="muted">%s %s · '
                   '%s</span></td><td>%d</td><td>%dk</td><td>%.0fh</td><td>%s</td></tr>' % (
                       s["share"], bar(s["share"] * 3, s["share"] >= 10),
                       e(s["title"] or "(untitled)"), s["source"], s["id"],
                       e(s["project"][-40:]), s["turns"], s["peak"] / 1000, s["hours"], flags))
    out.append('</table></div>')

    out.append('<h2>Config checks</h2><div class="card">%s</div>' % "".join(
        '<div class="%s">%s</div>' % ("ok" if line.endswith("ok.") or line == "none" else "bad",
                                      e(line)) for line in r["config"]))

    out.append('<h2>Top projects</h2><div class="card">')
    for name, pct in r["projects"]:
        out.append('<div class="row"><span>%.1f%%</span>%s<span class="muted" '
                   'style="overflow:hidden;text-overflow:ellipsis">%s</span></div>' % (
                       pct, bar(pct), e(name[-40:])))
    out.append('</div><h2>Tool calls</h2><div class="card">%s</div>' % " · ".join(
        "%s <b>%d</b>" % (e(n or "?"), v) for n, v in r["tools"]))
    if r["unpriced"]:
        out.append('<h2>Unpriced models</h2><div class="card bad">Counted at 1.0x: %.0f%% of '
                   'spend. %s</div>' % (r["unpriced"][0], e(", ".join(
                       "%s (%d turns)" % m for m in r["unpriced"][1]))))
    out.append("</main></body></html>\n")
    return "\n".join(out)

if __name__ == "__main__":
    sys.exit(main())
