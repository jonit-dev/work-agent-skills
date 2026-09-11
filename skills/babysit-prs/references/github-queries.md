# GitHub discovery and triage queries

Read only when forming CLI calls. Replace placeholders and inspect supported fields with local `gh` help. Paginate beyond these page limits when needed. Never print credentials.

```bash
gh repo list <your-github-org> --json nameWithOwner,pushedAt --limit 100 --source
gh pr list --repo <owner/repo> --state open --json number,title,isDraft,headRefName,url,mergeable,reviewDecision,labels,updatedAt,headRepository,headRepositoryOwner --limit 50
gh pr view <number> --repo <owner/repo> --json title,body,headRefOid,headRefName,baseRefName,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,commits,files
gh api --paginate repos/<owner/repo>/pulls/<number>/reviews
gh api --paginate repos/<owner/repo>/pulls/<number>/comments
gh api --paginate repos/<owner/repo>/issues/<number>/comments
gh pr checks <number> --repo <owner/repo>
gh run list --repo <owner/repo> --branch <headRefName> --limit 10 --json databaseId,headSha,conclusion,status
gh run view <run-id> --repo <owner/repo> --log-failed
```

Match a workflow run's `headSha` to the PR head; the most recent branch run may belong to another revision. Use exact file/line/diff context for actionable review feedback. Preserve complete relevant failure logs locally.

For authorized multiline PR comments, prepare a text file and use `gh pr comment <number> --repo <owner/repo> --body-file <path>` so shell expansion cannot alter content. Apply the readiness and dry-run rules in `SKILL.md` before mutations.
