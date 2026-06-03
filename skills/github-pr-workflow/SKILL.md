---
name: github-pr-workflow
description: "GitHub PR lifecycle: branch, commit, open, CI, merge."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

### Dirty-repo selective commit discipline

When the repo already has unrelated modified/staged files, never rely on a broad `git commit` after `git add` unless the user explicitly asked to include everything. Before committing, inspect both unstaged and staged state:

```bash
git status --short
git diff --stat
git diff --cached --stat
```

If unrelated files are staged, either unstage them or commit only the intended paths:

```bash
git restore --staged <unrelated-files>
git commit --only path/to/file-a path/to/file-b -m "<message>"
```

If the user makes a conditional commit request such as "if all tests pass, commit", treat the condition literally:

1. Identify the repo's relevant full gate (`verify`, `test:unit`, affected E2E/API suites, or `verify:full` when that is the stated standard).
2. Run the gate before staging/committing, not just a targeted slice.
3. If the full requested gate fails, do **not** commit, even if the change-specific tests passed.
4. Report exactly which commands passed/failed and whether failures appear unrelated or environment-dependent; leave the working tree uncommitted unless the user relaxes the condition.

If a repo hook is broken or blocks after you already ran the relevant verification on the exact intended changes, use a hook bypass narrowly and record why in the final response. Prefer disabling hooks for that one command rather than changing repo config:

```bash
git -c core.hooksPath=/dev/null commit --only path/to/file-a path/to/file-b -m "<message>"
```

Do not use hook bypass to hide failing lint/tests; use it only after explicit local verification passed and the hook failure is unrelated to code correctness.

### Deploy-script change discipline

When changing or adding a deploy/release script, verify the deploy path without touching production unless the user explicitly asked to deploy. At minimum, check script syntax, package metadata parsing, the local gates the script will run (`build`, `typecheck`, tests/link checks), and any Docker image build if the deploy path builds containers. Inspect the script diff to confirm it targets the intended remote, branch/ref, and narrow service scope.

In the final report, distinguish clearly between `Verified without deploying` and an actual production deploy. Do not say a deploy command is production-proven if only dry verification ran. See `references/deploy-script-change-verification.md`.

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

Pitfall: some repos have expensive pre-push hooks that rerun formatting, lint, and full test suites even after you already verified locally. If a push hook starts rerunning a long suite or blocks on checks the user explicitly asked to skip for the next operation, first confirm the working tree stayed clean (`git status --short`) and that the intended verification already passed on the same HEAD. Then it is acceptable to push with `git push --no-verify origin <branch>` and immediately verify local and remote SHAs match:

```bash
git status --short --branch
git push --no-verify origin HEAD:<branch>
git rev-parse HEAD && git rev-parse origin/<branch>
```

Do not use `--no-verify` to hide unverified code. Use it only to bypass redundant hooks after an explicit prior green verification or when the user specifically instructed to skip that class of gate.

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

### Add a Self-Review Comment Safely

When adding a review/comment body that contains backticks, file paths like `src/pages/foo`, or shell-sensitive characters, do **not** pass it inline inside double quotes. The shell can execute backtick substitutions and corrupt the comment, even though `gh` may exit successfully. Write the body to a temp file and use `--body-file`:

```bash
cat > /tmp/pr-self-review.md <<'EOF'
Self-review pass.

Checked:
- `yarn tsc --noEmit`
- `src/pages/example.astro` uses the intended copy
EOF

gh pr review <PR_NUMBER> --comment --body-file /tmp/pr-self-review.md
# or: gh pr comment <PR_NUMBER> --body-file /tmp/pr-self-review.md
```

Pitfall: immediately after pushing a new commit, `gh pr checks --watch` can briefly report `no checks reported` before Actions attaches check runs. Do not treat that as final. Retry after a short delay or inspect `statusCheckRollup`:

```bash
gh pr view <PR_NUMBER> --json headRefOid,statusCheckRollup,mergeable,isDraft
```

Pitfall: local verification plus `mergeable=MERGEABLE`/`mergeStateStatus=CLEAN` is not enough if fresh CI has not finished on the final `headRefOid`. GitHub can report a clean merge state while required checks are still pending and later fail. Before merging after any pushed review fix:

```bash
gh pr view <PR_NUMBER> --json headRefOid,mergeable,mergeStateStatus,isDraft,statusCheckRollup,url
gh pr checks <PR_NUMBER> --watch
```

If any meaningful check fails, do **not** merge even if local tests passed. Inspect the failed logs (`gh run view <RUN_ID> --log-failed`), patch or classify the failure, push a new commit if needed, and repeat the fresh-CI gate. If annotations prove the job never started because of GitHub billing/spending limits, switch to the billing-blocked workflow in `references/github-billing-failure-pattern.md`: run the exact local equivalents from `.github/workflows/*.yml`, disclose the infra blocker, and only merge if the user asked to merge and branch protection permits it.

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

Pitfall: if `gh run view --log-failed` says `log not found`, and `gh run view <RUN_ID> --json jobs` shows failed jobs with empty `steps`, the job may not have started at all. Check the check-run annotations before assuming a code failure:

```bash
JOB_ID=<job_database_id_from_gh_run_view>
gh api repos/$OWNER/$REPO/check-runs/$JOB_ID/annotations --jq '.' > /tmp/annotations.json
cat /tmp/annotations.json
```

A GitHub billing/spending-limit failure appears as an annotation like: `The job was not started because recent account payments have failed or your spending limit needs to be increased`. Report this as CI infrastructure blocked, not a code/test failure.

**Batch classification across an org:** When inspecting multiple repos in a sweep, the same billing failure often hits every repo under the same GitHub org. After spotting the first billing annotation, check subsequent repos quickly with the same `gh api repos/<owner>/<repo>/check-runs/<job_id>/annotations` pattern. Do not spawn Codex or commit fixes for billing failures — the only remedy is resolving the account billing/spending limit on GitHub.

Pitfall: AI review/action checks can fail for missing repository secrets rather than PR code. Example log: `Action failed: Input required and not supplied: open_router_key` from an OpenRouter PR review action. Classify this as CI/repo secret infrastructure, not an app failure; do not spawn Codex to change product code or workflow secrets unless the user explicitly asks. When making the PR merge-ready, prompt Codex to fix only real code/test failures and leave secret/workflow remediation out of scope. Merge-readiness still requires checking GitHub branch protection: if the failed AI review check is required, report it as an external blocker; if not required and meaningful tests are green, it can be non-blocking.

**Security-safe pattern for `gh api` → `python3`:** Hermes may block piping `gh api` output directly into `python3` with a security warning. Instead, redirect to a temp file first, then parse:

```bash
gh api repos/$OWNER/$REPO/check-runs/$JOB_ID/annotations --jq '.' > /tmp/annotations.json
cat /tmp/annotations.json
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git diff --staged --check
git diff --staged --stat
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

If the PR already has a review-fix commit and the next change is part of the same review/CI remediation, it is acceptable to keep history tidy by amending that commit and force-pushing with lease:

```bash
git add <fixed_files>
git diff --staged --stat
git commit --amend --no-edit
git push --force-with-lease origin HEAD:<pr-branch>
```

Pitfalls:
- Stage only intended files. Local tools can modify editor/framework state files such as `.astro/settings.json`; leave unrelated dirty files unstaged unless the user asked to include them.
- After any amend/force-push, treat CI as fresh and re-check `headRefOid` plus all required checks before merging.

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

### Common CI failure patterns

| Failure | Typical fix |
|---------|-------------|
| `yarn install --frozen-lockfile` fails with "lockfile needs to be updated" | Run `yarn install` locally (not `--frozen-lockfile`) to regenerate `yarn.lock`, commit and push. |
| `npm ci` fails with lockfile mismatch | Run `npm install` locally, commit updated `package-lock.json`. |
| Prettier / ESLint formatting errors | Run the formatter locally (`yarn lint --fix` or `npx prettier --write ...`), commit and push. |
| Missing env var in CI | Check `.github/workflows/*.yml` for required secrets; if the secret is missing, classify as repo infrastructure, not code failure. |
| TypeScript compilation error | Read the `tsc` output, fix the type issue, run `yarn tsc --noEmit` locally, commit and push. |
## 6. Merge-Readiness Audit

### Handoff / prior-work identity check

When the user asks to "double check" work described in a previous message or context handoff, first prove you are inspecting the same artifact before checking PR state or running verification:

```bash
pwd
git status --short --branch
git log --oneline -5
gh pr view <PR_NUMBER> --json number,state,headRefName,baseRefName,headRefOid,mergeCommit,url
```

Compare the worktree path, branch name, PR number, and commit hashes against the user's referenced summary. If they do not match, locate the referenced worktree/branch/PR before proceeding. Do not substitute a nearby stale worktree or different merged PR and report that as the answer.

When the requested validation is functional, such as "use E2E tests to validate links," PR metadata is not enough. Run the repo's actual build/test/link-check commands on the referenced `HEAD`, then include those command results in the final report.

When the user asks which PRs are "safe to merge", "ready to merge", or to "check PRs", do not rely on labels alone. Verify the merge gate explicitly:

1. List open PRs with metadata and checks:

```bash
gh pr list --state open \
  --json number,title,isDraft,mergeable,labels,statusCheckRollup,updatedAt,url \
  --limit 30
```

Safe-to-merge criteria:
- `isDraft == false`
- `mergeable == MERGEABLE`
- `mergeStateStatus == CLEAN` (not just old green checks)
- `headRefOid` matches the locally verified/pushed commit you intend to merge
- all required/meaningful checks are `COMPLETED` with `SUCCESS` or acceptable `SKIPPED` on the current `headRefOid`; pending checks must be watched to completion
- no failed checks such as test/verify/smoke jobs
- labels like `ready-to-merge`, `nw:ready-review`, or `e2e-validated` are supportive signals only, not proof

Stale-green pitfall: a PR can have all checks green on its head but still be unsafe because `master` moved and GitHub reports `mergeable=CONFLICTING` or `mergeStateStatus=DIRTY/UNSTABLE`. In that case, do not merge. Update the PR branch against current base, resolve conflicts preserving both sides, rerun local verification, push, then wait for fresh CI and re-check `headRefOid`, `mergeable`, and `mergeStateStatus` before merging.

When the user says "review, iterate, and merge" on an existing PR, treat it as a full merge-readiness loop, not just code review. First inspect `gh pr view <PR> --json state,isDraft,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,statusCheckRollup,url`. If GitHub reports `CONFLICTING`, `DIRTY`, or `UNSTABLE`, the immediate task is to update the PR branch against the current base and resolve conflicts before any merge attempt. Do not summarize "what's next" while mergeability is blocked unless the user asked for planning instead of action.

2. For multiple candidates, simulate cumulative merges in a temporary worktree before recommending an order:

```bash
set -e
cd /path/to/repo
git fetch origin <base-branch> --prune
tmp=$(mktemp -d /tmp/pr-merge-check.XXXXXX)
git worktree add "$tmp" origin/<base-branch>
cd "$tmp"

for pr in <PR_NUMBERS_IN_PROPOSED_ORDER>; do
  echo "=== Trying PR #$pr ==="
  git fetch origin pull/$pr/head:pr-$pr
  git merge --no-commit --no-ff pr-$pr
  git commit -m "temp merge pr $pr"
done

# Run the repo's standard verification if available.
# If dependencies are missing in the temp worktree, install them there first.
# Examples: yarn install --frozen-lockfile && yarn verify; npm ci && npm test; pytest.

cd /path/to/repo
git worktree remove --force "$tmp"
```

3. Report separately:
- **Safe to merge now**: non-draft, mergeable, green checks, cumulative merge simulation and verification pass
- **Not safe yet**: draft, conflicts, failed checks, partial/resumable labels, or verification failure
- **Suggested merge order**: smallest/least overlapping first, or the verified cumulative order

Pitfalls:
- A `ready-to-merge` label can be stale or automated. Treat it as a hint, not a gate.
- `gh` JSON piped directly to `python3` may trigger security approval in Hermes. Prefer writing to a temp file first, then parsing the file.
- Temporary worktrees do not share `node_modules`; local verification may fail with `tsc: not found` until dependencies are installed in that worktree.
- **Orchestration-script merge conflicts are high-risk.** If `git merge` or `git rebase` produces conflicts in files that control AI provider behavior (e.g., `scripts/night-watch-cron.sh`, CI workflow YAML, prompt templates), **abort immediately** rather than auto-resolving. A bad resolution can silently change the behavior of future autonomous runs. Use `git merge --abort` or `git rebase --abort`, report the conflict, and leave manual resolution for the user.

### Updating a stale/conflicting PR to mergeable, then merging when green

When the user explicitly asks to "leave it mergeable" and "merge once green", use a fix-then-gate loop:

```bash
PR=123
BASE=master

# Confirm current repo and PR state.
git fetch origin "$BASE" --prune
gh pr view "$PR" --json headRefName,headRefOid,mergeable,mergeStateStatus,isDraft,statusCheckRollup

# Check out the PR branch and integrate current base.
BRANCH=$(gh pr view "$PR" --json headRefName --jq .headRefName)
gh pr checkout "$PR"
git merge "origin/$BASE"  # or rebase, if that repo prefers linear PR branches

# Resolve conflicts by preserving both the base branch's new behavior and the PR's feature changes.
# Then run the repo's standard verification.
yarn verify
yarn test

git add <resolved-files>
git commit -m "fix: update PR #$PR against $BASE"
git push

# Wait for fresh CI on the new head.
gh pr checks "$PR" --watch

gh pr view "$PR" --json headRefOid,mergeable,mergeStateStatus,isDraft
# Require mergeable=MERGEABLE and mergeStateStatus=CLEAN before merging.
gh pr merge "$PR" --squash --delete-branch --subject "<squash title>"

# Verify the result.
gh pr view "$PR" --json state,mergedAt,mergeCommit,headRefName
git fetch origin "$BASE" --quiet
git checkout "$BASE"
git pull --ff-only origin "$BASE"
git status --short --branch
```

If using Codex to do the update, prompt it to commit and push but **not merge**; the parent agent should independently verify PR state, fresh CI, and mergeability before `gh pr merge`.

For a phased/stacked set of PRs, fix and merge strictly one at a time. First enumerate the entire pending queue so you do not miss an earlier PR in the sequence. After each merge, update the next PR branch against the newly advanced base, rerun local targeted verification, wait for fresh CI on the new `headRefOid`, and only then merge. See `references/dependent-pr-fix-merge.md` for the reusable sequence and pitfalls, and `references/stacked-product-pr-case-study.md` for a concrete copy/docs/i18n-heavy product PR example.

#### Conflict-resolution guardrails for autonomous runs
- Before attempting to rebase/merge a stale PR, check how far behind it is: `git log <branch>..origin/master --oneline`.
- If `git merge` or `git rebase` produces conflicts in **orchestration / prompt-generation scripts** (e.g., `scripts/night-watch-cron.sh`, CI workflow YAML, or any file that controls what the AI provider sees), **abort immediately** rather than auto-resolving. These files are high-risk to fix blindly because a bad resolution can change the behavior of future autonomous runs.
- Abort helpers:
  ```bash
  git merge --abort   # if merge was in progress
  git rebase --abort  # if rebase was in progress
  ```
- Report the conflict in the final output and leave manual resolution for the user. Never push a conflicted branch back to the remote.
- If conflicts are in **product code or tests** and the fix is unambiguous (e.g., both sides added independent functions), resolve by preserving both changes, run `yarn verify` / `yarn test`, then commit and push.

### Merging another feature branch into an open PR branch

Use this when the user asks to merge a current/local feature branch, UI revamp, refactor branch, or shared dependency branch into an existing PR branch and fix conflicts.

```bash
# 1. Identify the source branch and target PR branch.
git status --short --branch
git fetch origin --prune
gh pr list --state open --json number,title,headRefName,baseRefName,mergeable,url --limit 50

SOURCE_BRANCH=$(git branch --show-current)   # or set explicitly, e.g. feat/ui-revamp
PR=123
TARGET_BRANCH=$(gh pr view "$PR" --json headRefName --jq .headRefName)

# 2. Use a separate worktree so the user's current branch/worktree stays intact.
WORKTREE="/tmp/$(basename "$PWD")-pr-$PR-merge"
rm -rf "$WORKTREE"
git worktree add "$WORKTREE" "$TARGET_BRANCH"
cd "$WORKTREE"

# 3. Merge the source branch into the PR branch and resolve conflicts.
git merge --no-ff "$SOURCE_BRANCH"
# Resolve conflicts by preserving BOTH: the PR feature behavior and the incoming branch's refactor/UI conventions.
grep -R "<<<<<<<\|=======\|>>>>>>>" -n . --exclude-dir=node_modules --exclude-dir=.git || true
git diff --check
git add <resolved-files>

# 4. Verify with the repo's normal commands. If the worktree has no dependencies, install first.
test -d node_modules || yarn install --frozen-lockfile
yarn tsc   # replace/add project-specific tests as appropriate

# 5. Commit, push, and verify the PR is clean on the new head.
git commit -m "Merge branch '$SOURCE_BRANCH' into $TARGET_BRANCH"
git push origin "$TARGET_BRANCH"
gh pr view "$PR" --json headRefName,headRefOid,mergeable,mergeStateStatus,statusCheckRollup,url
```

Pitfalls:
- First check the actual current/source branch name. The user's phrase like "current UI revamp branch" may be approximate.
- `git worktree add <path> <target-branch>` may print the main worktree's branch in a later command if that command runs from the wrong directory; always run `git status --short --branch` inside the worktree before merging.
- Temporary worktrees do not share `node_modules`; install dependencies before `yarn tsc`/tests if needed.
- For lockfile conflicts, preserve both independent dependency entries when both branches added packages.
- After pushing, require the PR's `headRefOid` to match local `HEAD` and `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN` before reporting it as mergeable.

### Directly merging a local feature branch into `master`

Use this when the user explicitly asks to "merge everything to master" for a local branch/worktree rather than opening a PR. Also use it when a PR was already opened but the user corrects the workflow with "no need to open PRs, just merge to master" or equivalent. In that case, stop treating the PR as the gate: verify the feature branch locally, merge/push directly to the requested base, then confirm the remote base SHA. GitHub may later mark the PR as merged automatically, but that is an outcome, not the workflow gate.

If a PR has already been merged but the base branch still fails local release/test gates, switch from PR iteration to a **post-merge master rescue**: sync the real base branch, reproduce the failing base gates, fix forward in an isolated temporary worktree, run the full affected gate set on the final base HEAD, push only the verified rescue commit to `master`, then confirm local/remote SHAs and clean up. See `references/post-merge-master-rescue.md`.

Keep the merge isolated so the user's current worktree and any other checked-out `master` worktree are not disturbed.

```bash
# From the feature worktree
pwd
git status --short --branch
git log --oneline -8
git fetch origin --prune

# Verify the feature branch first, before merge.
yarn typecheck && yarn build && yarn test:links

# Create a temporary merge worktree from the current remote master.
MERGE_WT=/tmp/<repo>-merge-master
rm -rf "$MERGE_WT"
git worktree remove "$MERGE_WT" --force 2>/dev/null || true
git branch -D merge/<feature>-to-master 2>/dev/null || true
git worktree add -b merge/<feature>-to-master "$MERGE_WT" origin/master
cd "$MERGE_WT"

# Merge the feature branch by local branch name or full path ref.
git merge --no-ff <feature-branch> -m "Merge <feature-branch> into master"
```

If conflicts happen in docs/navigation/content files, resolve by preserving both sides' routes and entry points, not by blindly choosing ours/theirs. Example: if `master` added `/tutorials/`, `/wiki/`, `/blog/`, `/search/` while the feature added `/guides/early-game/`, keep all of them in the nav and make `/guides/` a hub linking to both progression guides and tutorials.

After resolving conflicts:

```bash
grep -R "<<<<<<<\|=======\|>>>>>>>" -n src --exclude-dir=node_modules --exclude-dir=.git
# should print nothing
git diff --check
git add <resolved-files>
yarn install --frozen-lockfile
yarn typecheck && yarn build && yarn test:links
```

For UI/docs routes, also run a preview/browser smoke check on the conflict-resolved tree before pushing: open the hub route and one detail route, check console errors, and verify key dynamic/embed counts if relevant.

Commit and push only after verification:

```bash
git commit --no-edit
git push origin HEAD:master
git fetch origin master --prune
git rev-parse HEAD && git rev-parse origin/master
```

Clean up the temporary worktree/branch after confirming the remote SHA matches. Report any feature work that was started but not committed separately so the user knows it was not part of the merge.

## 7. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

Pitfall: `gh pr merge --squash --delete-branch` can successfully merge the PR but still exit non-zero if it cannot delete a **local** branch, commonly because that branch is checked out by a worktree. It can also fail after merging when run from a temporary worktree if Git tries to check out a base branch that is already checked out in another worktree, e.g. `fatal: 'master' is already used by worktree at ...`. If this happens, verify before retrying:

```bash
gh pr view <PR_NUMBER> --json state,mergedAt,mergeCommit,mergedBy,url,headRefName
# If state == MERGED, do not retry the merge. Clean up local worktrees/branches instead:
git worktree remove --force /tmp/<worktree>
git fetch origin --prune
# If the local PR branch remains after worktree cleanup, delete it explicitly:
git branch -D <headRefName> 2>/dev/null || true
# If the remote branch still exists, delete it explicitly from a real repo workdir:
git -C /path/to/repo push origin --delete <headRefName>
```

After a non-zero merge exit, always verify both local and remote branch cleanup. `--delete-branch` may fail before deleting the remote branch when a checked-out worktree blocks local deletion. Also expect repository hooks to run on `git push origin --delete`; if a pre-push hook runs verification during branch deletion, let it complete unless it is clearly redundant and slow, then use the push-hook bypass rules above.

When running from a temp worktree whose branch is the PR head, prefer executing the merge from outside that worktree to avoid local branch deletion failures:

```bash
cd /tmp
gh pr merge <PR_NUMBER> --repo OWNER/REPO --squash --delete-branch --subject "<title>"
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |

## References

- `references/ci-troubleshooting.md` — general CI failure diagnosis
- `references/github-billing-failure-pattern.md` — how to spot and classify GitHub Actions billing/spending-limit failures that block CI from starting, including local workflow-equivalent verification when CI cannot run
- `references/dependent-pr-fix-merge.md` — phased/stacked PR fix-and-merge sequence using isolated worktrees, fresh-base updates, Codex delegation, CI gating, and cleanup
- `references/stacked-product-pr-case-study.md` — concrete sequential merge case study for copy/docs/i18n-heavy product PR stacks, including conflict-resolution heuristics
- `references/deploy-script-change-verification.md` — dry verification checklist for deploy/release script changes, including local gates, Docker smoke builds, service-scope review, and final-report wording when production was not touched
- `references/post-merge-master-rescue.md` — fix-forward workflow for already-merged PRs that leave `master`/`main` failing local gates, including isolated rescue worktrees, exact gate reruns, push-to-base verification, and cleanup
