# Gauntlet Loop skill

A reusable skill for benchmark-driven, multi-agent improvement loops with strict
builder/critic separation. Runs under Codex and Claude Code.

## Install for Claude Code

```bash
mkdir -p ~/.claude/skills ~/.claude/agents
cp -R /path/to/gauntlet-loop ~/.claude/skills/gauntlet-loop
# agent profiles: gauntlet-builder.md, gauntlet-critic.md, gauntlet-integrator.md
```

If `~/.agents/skills/` is already the shared skill store, install there instead and symlink:
`ln -sfn ../../.agents/skills/gauntlet-loop ~/.claude/skills/gauntlet-loop`.

Invoke with `/gauntlet-loop`, followed by the goal, references, and constraints.

## Install for Codex

### Repository-scoped

From the repository root:

```bash
mkdir -p .agents/skills .codex/agents
cp -R /path/to/gauntlet-loop .agents/skills/gauntlet-loop
cp .agents/skills/gauntlet-loop/optional-codex/agents/*.toml .codex/agents/
```

The custom agents are optional. The skill can spawn ordinary Codex subagents with equivalent role instructions.

### User-scoped

```bash
mkdir -p ~/.agents/skills ~/.codex/agents
cp -R /path/to/gauntlet-loop ~/.agents/skills/gauntlet-loop
cp ~/.agents/skills/gauntlet-loop/optional-codex/agents/*.toml ~/.codex/agents/
```

Codex normally detects skill changes automatically. Restart Codex if the skill does not appear.

## Invoke

In Codex CLI or the IDE extension, mention the skill with `$`:

```text
$gauntlet-loop
Goal: Make this Bitcoin forecasting research pipeline materially better out of sample.
Quality bar: Beat naive current-price on untouched outer folds without leakage, while preserving calibration.
Constraints: Small explicit search budget; no production promotion unless the evidence gate passes.
```

Or for a visual task:

```text
$gauntlet-loop
Goal: Make this Three.js game scene compare favorably with the supplied reference captures.
References: ./references/*.png
Constraints: Keep the current engine and asset license requirements.
```

A useful request includes a goal, references or measurable bar, constraints, and any budget. When no bar is supplied, the skill instructs Codex to find and justify an inspectable one.

## What it creates during a run

The workflow keeps its working evidence under `.gauntlet/` in the target repository:

- `charter.md`
- `progress.md`
- `evidence/`
- optionally `progress.html` for long visual runs

## Design notes

This is an adaptation of Matt Shumer's “Gauntlet Loop” method for Codex. It uses Codex skills, current subagent support, read-only critics, and optional custom agent profiles. It intentionally avoids a fixed number of rounds, while adding practical stop conditions for a verified pass, an explicit budget, a hard blocker, safety, or an evidence-backed plateau.

Source workflow: https://somethingbig.ai/gauntlet-loop
Codex skills documentation: https://developers.openai.com/codex/build-skills
Codex subagents documentation: https://developers.openai.com/codex/agent-configuration/subagents
