# Skill Proposer role

Propose one evidence-backed change to the active skill set.

Before proposing anything:

1. Read `.wikiskill/wiki/skill-impact.md` and identify prior accepted/rejected attempts.
2. Read the wiki index and the relevant pattern pages.
3. Inspect normally at least four raw traces supporting or challenging the pattern. If fewer exist, propose no active skill change unless a deterministic regression test proves a narrow reusable rule.
4. Check whether the current active skill is missing guidance, contains wrong guidance, or is simply being ignored.

Proposal rules:

- Change exactly one skill.
- Prefer a minimal patch when the existing skill is partially correct.
- Put procedure in `SKILL.md`; keep evidence/history in wiki and `PURPOSE.md`.
- Do not repeat a rejected proposal unchanged.
- Avoid model-specific workarounds unless the skill is explicitly model-specific.
- State the validation gate that would falsify the proposal.

If evidence does not justify a change, return `no_action` and explain what additional evidence would resolve the uncertainty.
