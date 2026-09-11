# Purpose

## Origin

This meta-skill adapts the WikiSkill research architecture into a practical coding-agent workflow.

## Research patterns retained

- Separate immutable raw experience, persistent structured knowledge, and executable skills.
- Keep the wiki across rejected skill proposals.
- Use an impact history so rejected interventions are not blindly repeated.
- Propose atomic skill changes and gate them against validation evidence.
- Keep executable skills concise while the wiki accumulates richer history.
- Generate diagnostic experience without giving the task-solving agent direct wiki access.

## Production adaptations

- Raw evidence stores observable actions and outputs rather than private reasoning traces.
- Validation can be software tests, CI, replay tasks, benchmarks, or task-specific scoring.
- A deterministic regression test can justify a narrow change before four independent traces exist.
- Wiki entries may be marked superseded to control long-term knowledge sprawl.

## Source

Tang et al., "WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution," arXiv:2608.27454, 2026.
