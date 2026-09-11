# wikiskill-evolution

A practical meta-skill for coding agents, based on **WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution** (Tang et al., 2026, arXiv:2608.27454).

Its job is to stop useful engineering lessons from disappearing into chat history or being overfit directly into giant `SKILL.md` files.

## Mental model

```text
observable task runs
      ↓
.wikiskill/raw/          immutable evidence
      ↓
.wikiskill/wiki/         distilled patterns + intervention history
      ↓
active agent skills      concise executable procedure
      ↓
independent validation
   ↙        ↘
accept     rollback skill
              ↓
        wiki still persists
```

## Install

For a user-level, cross-runtime skill installation:

```bash
mkdir -p ~/.agents/skills
cp -R wikiskill-evolution ~/.agents/skills/
```

Or put the folder in the skill directory used by your agent runtime.

For a repository where you want project-local evolved skills, keep those active skills under a project skill directory such as `.agents/skills/`; the meta-skill itself may remain global.

## Bootstrap a repository

```bash
python ~/.agents/skills/wikiskill-evolution/scripts/wikiskill.py init --root .
```

This creates:

```text
.wikiskill/
  raw/
  raw-manifest.jsonl
  wiki/
    index.md
    log.md
    skill-impact.md
    patterns/
  candidates/
```

Optionally copy the contents of `AGENTS_SNIPPET.md` into your repository instructions so the agent knows when to invoke the meta-skill.

## Capture observable experience

Save relevant test or command output to a file, then:

```bash
python ~/.agents/skills/wikiskill-evolution/scripts/wikiskill.py capture \
  --root . \
  --task "Fix Android renderer lifecycle race" \
  --outcome fail \
  --summary "Renderer recreated before native surface teardown completed" \
  --evidence /tmp/test-output.txt \
  --tags android \
  --tags lifecycle \
  --skills native-rendering
```

Raw traces are hashed. `validate` reports later mutation:

```bash
python ~/.agents/skills/wikiskill-evolution/scripts/wikiskill.py validate --root .
```

## Record a skill gate

After proposing one skill change and evaluating it:

```bash
python ~/.agents/skills/wikiskill-evolution/scripts/wikiskill.py impact \
  --root . \
  --iteration 4 \
  --skill native-rendering \
  --decision rejected \
  --baseline "12/15 replay tasks" \
  --candidate "11/15 replay tasks" \
  --validation "held-out replay + unit tests" \
  --patterns .wikiskill/wiki/patterns/surface-teardown-order.md \
  --diff-file /tmp/skill.diff \
  --notes "Fixed lifecycle race but regressed resize handling"
```

The skill patch is rolled back, but that rejection remains in the wiki so the next proposer does not blindly repeat it.

## What is faithful to the paper

The package preserves the paper's main causal structure:

- raw experience, accumulated wiki knowledge, and executable skills are separate;
- experience is consolidated into persistent pattern pages;
- skill proposals consult historical intervention outcomes;
- changes are atomic and validated independently;
- rejected skill changes are rolled back while wiki knowledge persists;
- diagnostic task runs do not use the wiki as an answer source;
- failure and success traces are both sampled so fixes do not destroy working behavior.

## What is intentionally adapted

The research implementation stores full experimental trajectories and gates on benchmark validation scores. For normal software repositories this package stores **observable** execution evidence rather than private reasoning, and allows CI, tests, held-out replay tasks, or benchmarks to serve as the gate.

The paper also calls out wiki pruning as an unresolved limitation. This implementation recommends merging duplicate patterns and marking stale pages `superseded`, while retaining raw evidence and historical outcomes.

## Tests

```bash
python -m unittest discover -s tests -v
```

Behavioral pressure cases are in `tests/PRESSURE_CASES.md`. The current package has automated structural/runtime tests for initialization, immutable capture, tamper detection, impact logging, and skill packaging. A true behavioral RED/GREEN evaluation should be run with the target coding-agent runtime because this chat environment does not expose a second isolated agent instance for pressure testing.
