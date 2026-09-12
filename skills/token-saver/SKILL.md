---
name: token-saver
description: Cut coding-agent token cost by preventing wasted work rather than compressing text — a narrow-retrieval substitution policy, a verification ladder, a retry circuit breaker, and a delegation rule. Also installs and configures the setup it describes (global skills, token-efficient defaults for Claude Code and Codex) with full config backup and one-command rollback. Use when setting up a new machine or agent, when asked to reduce token or context cost, when a session is burning turns re-reading the same code, or when deciding whether to delegate to subagents.
---

# token-saver

Most coding-agent spend is not verbose text. It is work that should never have happened:
duplicated retrieval, whole-file reads, full test suites run after every edit, retry loops
on the same failure, and subagents that each start their own model and tool loop.

**Compressing output after the work has happened cannot recover that.** Two independent
benchmarks measured shell-output compressors making sessions *more* expensive, because the
compression either missed most billed context or churned the prompt cache. See
[references/evidence.md](references/evidence.md).

So this skill has one rule, three ladders, and one setup script.

## The rule

> **A retrieval step replaces the one below it. It is never added on top of it.**

The measured failure mode is an agent that gets a correct answer from one tool, then
confirms the same fact with `rg` and a whole-file read. The semantic-server arm that did
this used **+10.1% uncached input and +59.3% tool calls** against bare Codex — the server
worked fine; the trajectory around it did not. That result is why this skill no longer
installs a semantic MCP server: see [references/evidence.md](references/evidence.md).

Any retrieval tool only pays if it *removes* the reads it replaces.

## Retrieval ladder

Climb only as far as the question requires, then stop.

1. **Symbol or path already known?** Read the range, not the file — `rg -n '<symbol>'`
   for the definition line, then `sed -n 'A,Bp'` or `Read` with an offset and limit.
2. **Owner unknown** ("where does auth happen?") — `rg` and `glob` for discovery. Name the
   symbol first; a search you cannot name is exploration, not retrieval.
3. **Retrieve the smallest unit that answers the question** — a function body, not its
   file; `rg -l` to locate before `rg -n` to read; callers by name, not a repo-wide dump.
4. **After a step establishes a fact, do not re-establish it.** No confirming `rg` after
   a read that already answered, no second pass over the same file. This is the rule
   above, and it is the single highest-value line in this skill.
5. **Fall back to a whole-file read only for a named unresolved question.** Write the
   question down first; if you cannot name it, you do not need the read.
6. **Stop retrieving** once there is enough evidence to implement or verify safely.

Exceptions, both real: tiny edits in a file you already have open, and small files where
one read is cheaper than three searches — do not ladder for the sake of laddering.

## Verification ladder

    smallest falsifier → component test → full suite at milestone

Run the narrowest test that can disprove the current hypothesis. A 15-minute suite after
every edit buys one bit of information for thousands of tokens of log. Full verification
runs once, before claiming completion.

Cap what comes back: `| tail -50`, `--reporter=dot`, `-q`, `--fail-fast`. Truncating the
diagnostic clue costs a whole extra turn, so cap output, do not blindfold yourself.

## Retry circuit breaker

> **Two failures with the same underlying cause: stop editing.**

Do not attempt a third fix. Re-state the assumption that must be wrong, escalate reasoning
effort, or return to planning. The expensive pattern is edit → test → shallow diagnosis →
edit → same test → shallower diagnosis, and it is how a cheap model outspends an expensive
one.

## Delegation rule

Subagents cost more than a single agent doing the same work — each child runs its own model
and tool loop, and OpenAI's own docs say so plainly. Delegate only when one is true:

1. The child can use a **materially cheaper model** for the same job, or
2. moving a **large read/search workload into an isolated context** saves the parent more
   repeated tokens than the child costs.

"Parallelize it" is a latency strategy, not a cost strategy. A reader agent that returns
paths, symbols and unresolved questions pays for itself. Five frontier-model agents
exploring the same repository do not.

## Planning, proportionally

Planning has a price. A one-line null check does not need a research agent and a PRD.

| Task | Route |
| --- | --- |
| Known file, obvious change | Execute directly |
| Well-specified, multi-file | Acceptance criteria, then execute |
| Uncertain, cross-cutting, unfamiliar repo, hard bug | Localize first → compact PRD → **fresh** executor context |

The gain in the third row is not that a PRD uses fewer words than a chat. It is that the
executor never rediscovers the architecture and never drags twenty exploratory tool results
through every subsequent turn. Use `prd-creator` to write it; keep it to objective,
non-goals, established facts (exact paths and symbols), invariants, change, acceptance,
verify commands. Delete anything that narrates the research.

## Cache stability

Cached input can cost ~0.1× base input; a cache write costs ~1.25×. An "optimizer" that
rewrites your system prompt to make it shorter can therefore **raise** the bill.

So: do not churn stable prefixes. `CLAUDE.md`, `AGENTS.md`, tool definitions and MCP
schemas should change between sessions, not within them. A stable 1,000-token instruction
block that is always cached is cheaper than 300 tokens rewritten every turn. Optimize
economic tokens, not visible prompt length.

## Setup

`scripts/setup-agents.sh` performs the whole installation, idempotently, for Claude Code
and Codex together.

```bash
scripts/setup-agents.sh              # dry run — prints every change, writes nothing
scripts/setup-agents.sh --apply      # back up, apply, then verify
scripts/setup-agents.sh --verify     # check an existing install; exits 1 on any failure
scripts/setup-agents.sh --rollback   # restore the most recent backup
```

`--apply` ends by verifying its own work rather than trusting that each step
reported success: both config files must parse, every expected key must be present,
each skill link must resolve to a readable `SKILL.md` (a dangling symlink looks
installed to `ls` and is invisible to the agent), the always-on line must be present
in both files, and a restorable backup must exist. `--verify` runs the same checks
alone and exits non-zero on failure, so it can gate a provisioning script.

**It backs up before it touches anything.** Every `--apply` run first copies
`settings.json`, `config.toml`, `CLAUDE.md` and `AGENTS.md` into
`~/.agents/token-saver-backups/<timestamp>/` and writes a `restore.sh` beside them. Nothing
is edited until that backup exists. `--rollback` restores the newest one; any older
snapshot restores by running its own `restore.sh`.

What it does:

1. **Skills** — links `token-saver`, `prd-creator` and `prd-manager` into
   `~/.claude/skills/` and `~/.codex/skills/` from one shared checkout, so both agents read
   the same file and an update lands in both.
2. **The always-on line** — appends one line to `~/.claude/CLAUDE.md` and
   `~/.codex/AGENTS.md`, between markers so re-runs replace rather than duplicate it:

   > Token discipline, every session: slice uncertain or cross-file work into a compact
   > PRD with the `prd-creator` skill first and execute from that, rather than exploring
   > and implementing in one context (`prd-manager` reports where PRDs stand); retrieve
   > the smallest range that answers the question and **never re-establish a fact you
   > already have** — no confirming grep after a read that answered it; run the smallest
   > test that can falsify the current hypothesis; after two failures with the same cause,
   > stop editing and re-plan. Full policy: `~/.agents/skills/token-saver/SKILL.md`.

   It names `prd-creator` and carries its rules inline on purpose. A skill that is merely *installed*
   self-activated **zero times in ten sessions** in JetBrains' evaluation of Ponytail —
   measured savings only appeared when the rules were force-injected into the prompt. An
   instruction that depends on being discovered is an instruction that does not run.

3. **Config defaults** — the settings in the table below, and deliberately not the others.

## Config: what gets set, and what gets refused

Applied by default — none of these reduce reasoning quality:

| Agent | Setting | Value | Why |
| --- | --- | --- | --- |
| Claude | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | `3` | Default is 20. Caps simultaneous fan-out; does not cap total work. |
| Claude | `ENABLE_TOOL_SEARCH` | `true` | Defers MCP tool schemas instead of loading every definition up front. Pure win with several MCP servers. |
| Claude | `MAX_MCP_OUTPUT_TOKENS` | `12000` | Default 25K. Bounds a pathological MCP dump. |
| Codex | `model_verbosity` | `low` | Shortens visible prose only. Reasoning is a separate setting and is untouched. |
| Codex | `tool_output_token_limit` | `10000` | Bounds giant build and test logs. |
| Codex | `agents.max_concurrent_threads_per_session` | `3` | Same reasoning as the Claude cap. |
| Codex | `agents.default_subagent_reasoning_effort` | `medium` | Children mostly scan and summarize; the parent keeps its own effort. |

**Refused by default.** Each of these is in the source research; each one degrades output
or is unsafe to set blind. `--aggressive` applies the spawn-depth one anyway, after printing
the risk. The rest the script will not set at all.

| Setting | Research value | Why it is refused |
| --- | --- | --- |
| `CLAUDE_CODE_EFFORT_LEVEL` | `medium` | **This is the "nerf your own output" setting.** A global, permanent downgrade of reasoning on every task including the hard ones. The correct shape is cheap *children*, not a cheap brain. Your baseline is a personal call; lower it per-session with `/effort` when the work is routine. |
| Codex `model_reasoning_effort` | `medium` | Same objection, same answer. The script does not read, write, or recommend a value for it. |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | `1` | There are version-specific reports of this behaving one level off, where `1` blocks subagent spawning entirely. `--aggressive` sets it; verify once after any Claude Code upgrade that delegation still works. |
| Codex `skills.max_context_tokens` | `3000–5000` | Actively harmful on a large skill collection: it truncates the catalog, so skills stop being discoverable — including this one. The fix for a bloated catalog is pruning unused skills, not capping the budget that makes them findable. |
| Codex `agents.max_depth` | `1` | Not in the current official config reference. Do not encode a setting you cannot verify is enforced; put "do not delegate" in the worker's instructions instead. |
| Claude output style `Concise` | — | Reasonable on its own, but it stacks badly with Ponytail and i-have-adhd, which already shape output. Three concision layers compete and the result is terse work reports, not cheaper sessions. Pick one. |
| RTK, Headroom, other output compressors | — | Measured *more* expensive end to end in two independent benchmarks. If you want one, A/B it on your own repository and count cache reads, cache writes and dollars — never "tokens compressed". |

Full reasoning and sources: [references/evidence.md](references/evidence.md).

## Verify it worked

```bash
scripts/setup-agents.sh              # re-run dry: every step should report "ok"
```

Then, in a fresh session of either agent, confirm the always-on line is in context. If a
session reads a file and then greps for the same symbol, the rule is not reaching the model
— check that the line survived in `CLAUDE.md` / `AGENTS.md` rather than adding more
instructions elsewhere.
