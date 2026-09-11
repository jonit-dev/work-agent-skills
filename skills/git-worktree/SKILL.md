---
name: git-worktree
description: Manage project-local Git worktrees for Codex and Claude Code, reuse task checkouts, audit SSD usage, and clean up after PR merge or task completion.
---

# Global worktree management

Shared source: ~/.agents/skills/git-worktree, linked into ~/.codex/skills and ~/.claude/skills. These instructions apply to every project. Resolve scripts/worktree-manager.sh relative to this skill.

## Create or reuse

1. Run `bash <manager> list` first. Resolve the primary owning checkout from Git's worktree registrations. Inside a linked checkout, --show-toplevel is NOT the primary.
2. Codex/manual worktrees belong ONLY in <primary>/.worktrees/<task-slug>. Claude native worktrees belong ONLY in <primary>/.claude/worktrees/<name>, created with Claude's native worktree tooling from the primary. Verify the intended path with git check-ignore BEFORE creation; add /.worktrees/ or /.claude/worktrees/ to the primary .gitignore when absent. Never use sibling directories, global holding directories, nested worktree roots, or substitute clones.
3. Reuse the existing task's checkout after confirming ownership. Dirty means preserve and investigate, not create -v2, -final, timestamps or another location. Continue retries and reviews in the same lane; read-only reviews usually need no new checkout. Never take over another active agent's checkout.
4. Fetch the intended upstream when freshness is required, verify its SHA, then run `bash <manager> create <branch> <base-ref-or-SHA> [--slug <task-slug>]`. The helper never switches/pulls in the primary, copies secrets, installs dependencies or resets existing branches. `path <branch>` prints the registered path; switch/go are aliases and cannot change a parent shell's cwd.

## SSD budget

Inspect free space and existing checkout sizes before a batch. Allocate only currently executing tasks; queue later tasks. Start with one lane and measure dependency/build footprint if no estimate exists. Do not preinstall dependencies or duplicate build trees for queued tasks. Do not share mutable node_modules/build directories between concurrent workers by symlink.

Record task, owner/session, absolute path, branch, base SHA and cleanup status in the task ledger. Keep one location per task.

## Required cleanup after merge or completion

Cleanup is part of delivery, not an optional suggestion. After PR merge, completed review/experiment, or user-authorized abandonment, inspect and retire the checkout in the same workflow. User authorization for routine cleanup persists; do not ask again when it already covers the action. If it does not, present exact paths and request confirmation before deletion.

Before removal:
1. Confirm the PR is merged and its final head is the checkout's HEAD, or establish equivalent integration evidence. Fetch the target branch when appropriate. For squash/rebase merges, verify the actual merged PR/head and patch evidence; ancestry alone may fail even when merged.
2. Confirm the owner released the checkout and agents/build/watch processes stopped. Do not infer inactivity from age, clean status or a missing lock.
3. Inspect tracked, untracked AND ignored files. Preserve needed .env, artifacts, local data and evidence. Identify exact disposable cache directories before removing them under existing cleanup authorization.
4. Run ordinary `git worktree remove /exact/registered/path` from outside it. Never remove the primary, locked worktrees, or parents containing another worktree. Never default to --force, branch -D, blanket cleanup, or recursive worktree deletion. Keep branches when deletion safety is unclear; a retained branch is cheap.
5. Verify the registration and directory are gone. Report removed paths and measured space change, or the retained path, size, concrete blocker and next cleanup action. Never silently leave a merged lane behind. For abandoned unmerged work, preserve its commits/data and get explicit authorization.

The manager's cleanup/clean command is deliberately report-only; it does not establish deletion eligibility. It lists all registrations, including misplaced checkouts and linked .git files. Use `git status --porcelain --untracked-files=all --ignored` per candidate. A clean default status does not mean ignored data is disposable.

## Audit existing sprawl

Use scripts/audit-worktrees.py /home for a read-only JSON inventory of owner repositories, registered paths, placement violations and allocated sizes. Dependency/build/cache interiors are skipped; scan errors are reported. Nested paths are not double-counted. Filesystem reflinks/shared extents mean du totals are NOT guaranteed reclaimable SSD space. Ordinary clones are not classified as worktrees.

Misplaced checkouts need an explicitly authorized relocation or cleanup operation after ownership inspection. Use Git move/repair mechanisms, not filesystem moves of live checkouts. Audit and skill maintenance do not authorize sweeping /home or deleting existing work.
