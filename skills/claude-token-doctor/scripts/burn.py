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

# A session whose last turn is this recent counts as active right now.
ACTIVE_MINUTES = 30

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


_CACHE = {}


def cached(parse, path):
    """parse(path), reused while the file's mtime and size are unchanged (for --serve)."""
    stat = os.stat(path)
    key = (parse.__name__, path)
    if _CACHE.get(key, (None,))[0] != (stat.st_mtime_ns, stat.st_size):
        result = parse(path)
        _CACHE[key] = ((stat.st_mtime_ns, stat.st_size),
                       list(result) if parse is not claude_title else result)
    return _CACHE[key][1]


def build_report(args):
    """Parse every transcript in the window into the report dict, or None if empty."""
    live = active_sources(args.source)
    if not live:
        print("No transcripts found. Try --list-sources.")
        return None

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
    active = []
    now = datetime.datetime.now(datetime.timezone.utc)
    last_hour = collections.defaultdict(float)
    weeks = {"claude": plan_week(), "codex": codex_week()}
    week_now = collections.defaultdict(float)

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

            for item in cached(read, path):
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
                if item["when"] >= now - datetime.timedelta(hours=1):
                    last_hour[source] += weighted
                week = weeks.get(source)
                if week and item["when"] >= week["start"]:
                    week_now[source] += weighted
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
                last_context = context

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
                    titles[(source, project, session)] = cached(claude_title, path)
                idle = (now - last_seen).total_seconds() / 60
                if idle <= ACTIVE_MINUTES:
                    active.append(((source, project, session), last_context, idle))

    if not total:
        print("No assistant turns in the last %d days for: %s" % (args.days, ", ".join(live)))
        return None

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
    report["active"] = [{
        "source": key[0], "project": key[1] or "?", "id": (key[2] or "?")[:8],
        "title": titles.get(key), "share": share(sessions[key][0]), "turns": sessions[key][1],
        "peak": sessions[key][2], "hours": sessions[key][3], "context": context, "idle": idle,
        "flags": session_flags(*sessions[key][1:], *signals[key]),
    } for key, context, idle in sorted(active, key=lambda a: a[2])]
    contexts.sort()
    report["timeline"] = sorted(timeline.items())
    report["hourly"] = sorted(hourly.items())
    report["bench_total"] = sum(v["bench"] for v in hourly.values())
    report["budget"] = args.weekly_budget * 1e6 if args.weekly_budget else None
    report["baseline"] = baseline(report, contexts, totals)
    report["burns"] = {}
    for source in live:
        week, spent = weeks.get(source), week_now[source]
        burn = {"rate": last_hour[source], "total": by_source[source], "week": None}
        if week and week["used"] >= 1 and spent:
            # Calibrate: this week's local spend is `used` percent of the plan's week.
            limit = spent * 100 / week["used"]
            hours_left = max((week["resets"] - now).total_seconds() / 3600, 1)
            burn["week"] = {"resets": week["resets"], "hours_left": hours_left,
                            "ideal": max(limit - spent, 0) / hours_left}
        report["burns"][source] = burn
    return report


def plan_week():
    """The subscription's 7-day window, from the endpoint /usage reads; None when unavailable.

    Sends the Claude Code login token only to api.anthropic.com. Cached for 5 minutes."""
    import subprocess
    import time
    import urllib.request
    if time.time() - _CACHE.get("week", (0, None))[0] < 300:
        return _CACHE["week"][1]
    week = None
    try:
        try:
            with open(os.path.join(os.path.dirname(claude_root()), ".credentials.json")) as fh:
                creds = fh.read()
        except OSError:  # macOS keeps the login in the Keychain
            creds = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                capture_output=True, text=True, timeout=5, check=True).stdout
        token = json.loads(creds)["claudeAiOauth"]["accessToken"]
        req =urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
            "Authorization": "Bearer " + token, "anthropic-beta": "oauth-2025-04-20"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)["seven_day"]
        resets = datetime.datetime.fromisoformat(data["resets_at"])
        week = {"start": resets - datetime.timedelta(days=7), "resets": resets,
                "used": float(data["utilization"])}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        pass
    _CACHE["week"] = (time.time(), week)
    return week


def burn_goal(r, source):
    """The hourly burn goal for one source: the plan's remaining week over the hours to its
    reset, else (Claude only) a weekly budget over 168 h, else the window's own average."""
    burn = r["burns"][source]
    if burn["week"]:
        w = burn["week"]
        return w["ideal"], "ideal pace to the weekly reset %s (%.0f h left)" % (
            w["resets"].astimezone().strftime("%a %H:%M"), w["hours_left"])
    if r["budget"] and source == "claude":
        return r["budget"] / 168, "weekly budget %.0fM / 168 h" % (r["budget"] / 1e6)
    return burn["total"] / (r["days"] * 24), (
        "your %d-day average; the subscription usage was unavailable" % r["days"])


def codex_week():
    """Codex's 7-day window from the rate_limits it logs in each session; None when unknown."""
    now = datetime.datetime.now(datetime.timezone.utc)
    for path in sorted(codex_files(), key=os.path.getmtime, reverse=True)[:5]:
        with open(path, "rb") as fh:
            fh.seek(max(os.path.getsize(path) - 262144, 0))
            lines = fh.read().decode(errors="replace").splitlines()
        for line in reversed(lines):
            if '"rate_limits"' not in line:
                continue
            try:
                limits = json.loads(line)["payload"]["rate_limits"]
                week = [w for w in (limits.get("primary"), limits.get("secondary"))
                        if w and w.get("window_minutes") == 10080][0]
                resets = datetime.datetime.fromtimestamp(week["resets_at"], datetime.timezone.utc)
            except (ValueError, KeyError, TypeError, IndexError, AttributeError):
                continue
            if resets <= now:
                return None  # the newest reading is from a finished week
            return {"start": resets - datetime.timedelta(days=7), "resets": resets,
                    "used": float(week["used_percent"])}
    return None


def serve(args):
    """Live report: every GET rebuilds it from the transcripts; the page reloads each minute."""
    import http.server

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            report = build_report(args)
            if self.path.startswith("/api/report"):
                body, kind = json.dumps(report_view(report) if report else None,
                                        default=str), "application/json"
            else:
                body, kind = render_html(report) if report else "No assistant turns.", "text/html"
            self.send_response(200)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *_):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.serve), Handler)
    build_report(args)  # warm the parse cache; requests queue on the bound port meanwhile
    print("Token doctor live on http://127.0.0.1:%d (Ctrl-C to stop)" % args.serve)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main():
    parser = argparse.ArgumentParser(description="Where the token budget actually went.")
    parser.add_argument("days", nargs="?", type=int, default=7)
    parser.add_argument("--source", default="all", choices=["all"] + list(SOURCES))
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--html", metavar="PATH", help="also write an HTML report to PATH")
    parser.add_argument("--weekly-budget", type=float, metavar="M",
                        default=float(os.environ.get("TOKEN_DOCTOR_WEEKLY_BUDGET") or 0) or None,
                        help="weekly budget in millions of weighted tokens (or env "
                             "TOKEN_DOCTOR_WEEKLY_BUDGET); sets the burn-rate goal")
    parser.add_argument("--serve", type=int, metavar="PORT",
                        help="serve a live report on http://127.0.0.1:PORT, rebuilt per request")
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

    if args.serve:
        return serve(args)
    report = build_report(args)
    if report is None:
        return 1
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
    for source, burn in r["burns"].items():
        goal, basis = burn_goal(r, source)
        print("Burn (%s): %.1fM in the last hour, goal %.1fM/h (%s)" % (
            source, burn["rate"] / 1e6, goal / 1e6, basis))
    for s in r["active"]:
        print("Active: %s (%s %s) context %dk, %d turns, %.0fh old, idle %.0fm%s" % (
            (s["title"] or "(untitled)")[:40], s["source"], s["id"], s["context"] / 1000,
            s["turns"], s["hours"], s["idle"],
            "; " + ", ".join(f.split(":")[0] for f in s["flags"]) if s["flags"] else ""))
    if not issues:
        print("Verdict: healthy. No common token leaks found.")
    else:
        print("Verdict: %d leak%s found, largest first.\n" % (len(issues),
                                                           "" if len(issues) == 1 else "s"))
    for n, issue in enumerate(issues, 1):
        where = ("%.0f%% of spend, %d sessions" % (issue["share"], len(issue["hits"]))
                 if issue["share"] is not None else "config")
        print("%d. [P%d] %s (%s)" % (n, issue["priority"], issue["title"], where))
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
    for issue in issues:
        issue["priority"] = issue_priority(issue)
    issues.sort(key=lambda i: (i["priority"], -(i["share"] or 0)))
    return issues


def issue_priority(issue):
    """1 fix now, 2 fix this week, 3 when convenient. A one-line config fix behind a big leak is 1."""
    if issue["share"] is None:
        return 1 if "autoCompactWindow" in issue["title"] else 2
    return 1 if issue["share"] >= 20 else 2 if issue["share"] >= 5 else 3


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


def report_view(r):
    """Everything dashboard.html draws, as JSON-ready data. The page owns all markup."""
    iso = lambda t: t.isoformat()
    issues = top_issues(r)
    actual = dict(r["timeline"])
    run_a = run_b = 0.0
    burndown = []
    for when, slot in r["hourly"]:
        run_a += sum(actual.get(when, (0, 0)))
        run_b += slot["bench"]
        burndown.append([iso(when + datetime.timedelta(hours=1)), run_a, run_b])
    blocks = collections.OrderedDict()
    for when, slot in r["hourly"]:
        b = blocks.setdefault(when.replace(hour=when.hour - when.hour % 3),
                              {"ctx": [], "reads": 0, "calls": 0})
        b["ctx"] += slot["ctx"]
        b["reads"] += slot["reads"]
        b["calls"] += slot["calls"]
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
    kpis = [
        {"name": "Median context per turn", "unit": "k", "target": 150_000,
         "values": [med(b["ctx"]) for b in blocks.values()]},
        {"name": "Turns over 300k context", "unit": "%", "target": 0.10,
         "values": [sum(c >= 300_000 for c in b["ctx"]) / max(len(b["ctx"]), 1)
                    for b in blocks.values()]},
        {"name": "Caller reads per tool call", "unit": "%", "target": 0.20,
         "values": [b["reads"] / max(b["calls"], 1) for b in blocks.values()]},
    ]
    # Act now: what a live session needs this minute, before any leak report.
    actions = []
    for s in r["active"]:
        name = s["title"] or s["id"]
        if s["context"] >= LATE_COMPACT_PEAK:
            actions.append("Run /compact in “%s”: its context is %dk." % (
                name, s["context"] / 1000))
        elif s["hours"] >= LONG_LIVED_HOURS:
            actions.append("Finish “%s” and start a fresh session: it is %.0fh old." % (
                name, s["hours"]))
    burns = {}
    for source, burn in r["burns"].items():
        goal, basis = burn_goal(r, source)
        week = burn["week"]
        burns[source] = {"rate": burn["rate"], "goal": goal, "basis": basis,
                         "resets": iso(week["resets"]) if week else None,
                         "hoursLeft": week["hours_left"] if week else None}
    return {
        "generated": iso(datetime.datetime.now(datetime.timezone.utc)), "days": r["days"],
        "total": r["total"], "sessions": r["session_count"], "turns": r["turns"],
        "over300k": r["over_300k"],
        "burns": burns,
        "burn": burns.get("claude") or next(iter(burns.values()), None),
        "actions": actions,
        "issues": [{"title": i["title"], "fix": i["fix"], "priority": i["priority"],
                    "share": i["share"], "sessions": len(i["hits"]),
                    "prompt": issue_prompt(i, r)} for i in issues],
        "active": r["active"],
        "burndown": burndown, "benchWindow": BENCH_WINDOW,
        "budget": r["budget"], "kpis": kpis,
        "timeline": [[iso(t), cool, hot] for t, (cool, hot) in r["timeline"]],
        "baseline": [{"name": n, "now": v, "target": t, "ok": ok}
                     for n, v, t, ok in r["baseline"]],
        "topSessions": r["sessions"],
        "buckets": [{"label": l, "hot": low >= 300, "share": pct, "turns": n}
                    for l, low, pct, n in r["buckets"]],
        "projects": r["projects"], "config": r["config"], "tools": r["tools"],
        "unpriced": r["unpriced"],
    }


def render_html(r):
    """dashboard.html with the report embedded, for a static file or the first paint."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")) as fh:
        page = fh.read()
    data = json.dumps(report_view(r), default=str).replace("</", "<\\/")
    return page.replace("/*REPORT*/null", data, 1)


if __name__ == "__main__":
    sys.exit(main())
