---
name: babysit-prs
description: Scan <your-github-org> GitHub org repos for open PRs, review them in parallel using worktrees, fix issues (comments, CI failures, merge conflicts), push fixes, and label ready-to-merge. Use when asked to "babysit PRs", "review open PRs", "fix PR issues", or "clean up PRs".
user_invocable: true
argument_description: '[--repo=<owner/repo>] [--label=<filter-label>] [--dry-run] [--skip-ci] [--max=<N>]'
---

# Babysit PRs

Find and repair open PRs in `<your-github-org>` (or the requested repository), push verified fixes and label ready PRs. Announce `PR Babysitter: Scanning for open PRs...`. Never merge, force-push or delete branches; preserve the author's intent. User scope and authorization govern external mutations/comments.

## Arguments

| Argument | Behavior |
|---|---|
| `--repo=<owner/repo>` | Restrict the default organization scan to this repo. |
| `--label=<label>` | Process only PRs carrying this label. |
| `--dry-run` | Discover, triage, classify and report only; no fixes, commits, pushes, labels or comments. |
| `--skip-ci` | Skip CI failure analysis/repair; still require passing checks before labeling ready. |
| `--max=<N>` | Process at most N PRs; default 10. |

## Discover and triage

Use `gh` or the available GitHub connector. For CLI query examples, read [references/github-queries.md](references/github-queries.md) only when constructing discovery/triage calls.

Enumerate open PRs, excluding drafts and labels `ready-to-merge` and `do-not-babysit`. Apply requested filters, sort oldest updated first, then cap at `--max`. Report repositories scanned, PR counts and selected PRs with conflict/CI/review status. Do not infer readiness from truncated results.

Coordinate an agent team with tracked tasks per repository; repo teammates own their PRs, with isolated worktrees per PR. Launch independent work concurrently within available capacity, without duplicate repo/PR ownership. Use the available team/agent interface and session permissions. In each repository read `AGENTS.md`, `CLAUDE.md`, contribution instructions and verification scripts.

Before fixing, gather PR body, exact head/base and repository/fork identity, diff/files/commits, merge status, reviews, inline and issue comments, required checks and relevant failed-run logs. Classify `ALREADY_CLEAN`, `NEEDS_CONFLICT_RESOLUTION`, `NEEDS_CI_FIX` or `NEEDS_FIXES`; mixed issues require the full repair path. `ALREADY_CLEAN` requires passing CI, no conflicts and no unresolved feedback. In dry-run, stop at the report, including for already-clean PRs.

## Repair and verify

1. Assign each repair worker its PR/worktree/branch, project rules, review evidence, CI failures, conflicts and acceptance/verification commands. Never work in the main directory. Follow repository-local worktree placement and the installed manager; preserve other workers' changes.
2. Fetch the actual PR head/base, resolve base conflicts while preserving both intents, and address valid review comments. If feedback is wrong or unclear, retain it as unresolved with a reason. Unless `--skip-ci`, fix logged typecheck/lint/test/build failures.
3. Run repository-prescribed verification. If no prescribed command exists, inspect available scripts in this order: `yarn verify`, `npm run verify`, `yarn test` plus `yarn lint`, `npm test` plus `npm run lint`. Fix failures. Return files changed, comments addressed/unresolved, CI fixes, conflict resolution and actual verification evidence.
4. Stage only intended fixes, make one well-described fix commit per PR and push normally to the correct head remote/branch. Do not rewrite the author's commits. A rejected push needing force is a blocker; never force-push.
5. Re-fetch and verify the remote PR head matches the tested commit. Recheck current-head required CI, mergeability and outstanding feedback. Apply `ready-to-merge` only when all pass; skipped CI analysis, a successful push or local tests alone do not establish readiness. Create a missing label with color `0E8A16` and description `PR has been reviewed and is ready to merge`. Post the authorized concise summary with fixes, feedback, conflicts and verification; already-clean PRs can use the same readiness gate without repair.

Failed/incomplete verification means no ready label. Report partial fixes, remaining issues and reasons; post that status only within authorization. Keep full logs as artifacts and surface relevant failures, not entire passing logs.

## Failure handling and report

Unauthenticated `gh`: stop and ask the user to run `gh auth login`. Inaccessible repo: report and continue others. Failed worktree creation: report and skip that PR. Agent timeout: inspect/preserve partial work and report remaining issues. Do not silently label incomplete work ready.

Return scanned/discovered/processed counts and per-PR URL, status, fixes, verification, label and unresolved work; totals ready versus requiring attention. Keep dry-run results explicitly hypothetical.
