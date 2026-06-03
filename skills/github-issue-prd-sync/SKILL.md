---
name: github-issue-prd-sync
description: Workflow for synchronizing project PRDs with GitHub issues to ensure consistency for autonomous agents (like Night Watch).
---

# GitHub Issue PRD Sync

When a PRD (Product Requirements Document) is created or updated in the local filesystem, it must be mirrored exactly in the corresponding GitHub issue. This prevents "context drift" where an agent reading the issue has outdated information compared to the PRD file.

## Trigger Conditions
- A new PRD is created in `docs/prds/`.
- An existing PRD is significantly updated.
- A GitHub issue is created/updated to track the implementation of a PRD.
- Before delegating implementation to an autonomous agent from a GitHub issue, especially if the issue body is empty, stale, or only references a `docs/prds/*.md` filename.

## Workflow Steps

1. **Generate/Update PRD**: 
   - Use the designated PRD creator skill (e.g., `prd-creator`) to generate the markdown file in the project's `docs/prds/` directory.
   - Verify the content is complete and approved.

2. **Extract Content**:
   - Read the final markdown file content.
   - If the file contains YAML frontmatter (e.g., title, status, priority), decide if it should be included. Usually, the core markdown body is what's required.

3. **Sync to GitHub Issue**:
   - Use the `gh issue edit` command.
   - **CRITICAL**: Do NOT summarize, condense, or paraphrase the PRD.
   - **The issue body must be IDENTICAL to the PRD file content.**
   - Use a temporary file to avoid shell escaping issues with large markdown blocks:
     ```bash
     cat docs/prds/your-prd.md > /tmp/issue_body.md
     gh issue edit <issue-number> --body-file /tmp/issue_body.md
     ```

4. **Verification**:
   - Run `gh issue view <number> --json body` to confirm the content was uploaded correctly.
   - For quick sanity, check body length or a known heading:
     ```bash
     gh issue view <issue-number> --json body --jq '{bodyLen:(.body|length), startsWithPrd:(.body|startswith("# PRD"))}'
     ```
   - Delete the temporary file.

5. **Before Delegating Work**:
   - If the issue body was empty/stale, sync it first, then launch Codex/Night Watch/subagents.
   - Commit the PRD file in the implementation branch too; syncing the issue body does not add the local file to git.
   - In the agent prompt, explicitly require docs/tests/self-review and `Closes #<issue>` in the PR body.

## Pitfalls & Tips
- **Shell Limits**: Attempting to pass a full PRD as a string argument to `gh issue edit` often fails due to shell character limits or escaping issues (e.g., quotes, backticks). Always use `--body-file`.
- **Context Drift**: If you update the local `.md` file, you MUST immediately update the GitHub issue.
- **Night Watch Compatibility**: Autonomous agents like Night Watch often prioritize the GitHub issue over the filesystem; identical content ensures they have the most accurate requirements.

## Verification
- [ ] PRD file exists in `docs/prds/`.
- [ ] GitHub issue body matches the PRD file exactly.
- [ ] Issue status/column updated to reflect "Ready" if applicable.