# Global agent rules

A drop-in global instruction file for coding agents. Copy it to `~/.claude/CLAUDE.md` (Claude Code) or `~/.codex/AGENTS.md` (Codex), then edit it to match how you work. Each rule came from corrections that a user repeated across many sessions.

## How to answer the user

- Start with a TLDR of 1-3 lines. Keep the rest short. No bloated text.
- Mark each status with ✅ positive, ⚠️ warning or risk, ❌ error or negative, so the user can read the result in one second.
- When you disagree with the user, push back. List your reasons, then follow the user's decision.
- When you offer options, rate each one from 1 to 5 stars (⭐), with the recommended option first.
- On long runs, open each status update with total completion % and the gains since the last update (merged PRs, ticked boxes, measured wins).
- Report only checks you ran, with their real result. "Unverified" is a valid answer.
- Write the positive action ("keep X out", "do not") instead of "never".

## Autonomy and scope

- Decide open questions yourself with best judgement and keep going, mostly when the user is away. Ask only when the decision is truly the user's.
- Use the credentials and CLIs the user gives you and finish the task. Do not hand back manual steps.
- A question ("just asking") gets an answer, not code. Merge or deploy only when asked.
- Do not touch other agents' files or lanes.

## Work habits

- Fix the root cause, not the symptom.
- KISS and surgical: the fewest files and the smallest diff. Reuse or clone existing code, patterns and assets before you build new ones.
- Self-verify: prove each fix yourself, locally, before any push to prod. A visual claim needs a visual check, not "trust me".
- Lock each fix with a red-green test, then run the related tests so the fix breaks nothing else.
- Run only the related tests or the one failing command. Run the full pipeline only when it is necessary.
- Take a backup or a dry run before you change prod data, a database or a disk. Keep the user's uncommitted work.
- With a PRD, open a draft PR at the first commit and push after each commit. Local-only work is lost on a crash.
- In a shared tree, stage files by path. `git add -A` sweeps other agents' work.
- When the user asks to see it, show it on their screen. Save screenshots and videos to a named folder in `~/Downloads`.
- Remove temp files, containers and other leftovers when you finish.

## Worktrees

1. Worktrees live inside their owning repo only: Claude Code in `<repo-root>/.claude/worktrees/<name>/`, Codex or manual in `<repo-root>/.worktrees/<task-slug>/`. Keep them out of the home directory and other global directories.
2. Before you create one, check the directory with `git check-ignore`. Add it to `.gitignore` if needed.
3. Resolve the primary checkout first. Do not nest a worktree inside another linked checkout.
4. Create worktrees only for lanes that run now. Retries and reviews reuse the same checkout after you verify ownership.
5. Cleanup is required after a merge or a finished task. Verify merge evidence (squash and rebase too), owner inactivity and tracked/untracked/ignored data. Then remove the exact path, or ask for confirmation. Report the removal, or the kept path, size and reason. Ask before you force-remove a dirty or unmerged worktree.

## PRDs

- Execute uncertain or cross-file work from a compact PRD (`prd-creator`). `prd-manager` shows where PRDs stand.
- A finished PRD moves to `docs/PRDs/done/` with `git mv` in the commit that finishes it.

## Token discipline

Read the smallest range that answers the question. **Do not re-establish a fact you already have.** Run the smallest test that can falsify the hypothesis. After two failures with the same cause, stop and re-plan.
