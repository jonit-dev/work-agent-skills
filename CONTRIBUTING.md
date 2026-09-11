# Contributing

This is a public repository. Everything merged here is world-readable forever,
including anything later deleted — git history keeps it. Treat every change as
permanent publication.

## The rules that matter

1. **No credentials.** No API keys, tokens, private keys, connection strings, or
   session cookies — not even expired ones, not even in an example block.
   Read secrets from the environment or a config file outside the repo.
2. **No personal identifiers.** No real names, emails, phone numbers, home
   directories (`/home/<you>/...`), or personal schedules. Write skills for
   "the user", not for a specific person.
3. **No private project or employer names.** Use a placeholder such as
   `<your-github-org>` and let the reader substitute their own.
4. **No binaries or personal media.** No screenshots of your desktop, no photos.
   Keep the repo text-first.

## How changes get in

`main` is protected. All changes arrive through a pull request, and a PR cannot
merge until both required checks pass:

| Check | What it does |
| --- | --- |
| `gitleaks` | Scans the diff **and the full history** for secret patterns. Config: `.gitleaks.toml`. |
| `public-safety-scan` | Scans for personal names, local paths, and private project terms. Script: `scripts/public_safety_scan.py`. |

Run both locally before you push:

```bash
python3 scripts/public_safety_scan.py

# gitleaks: https://github.com/gitleaks/gitleaks/releases
gitleaks dir . --config .gitleaks.toml --redact
```

## Handling a false positive

The scanners are deliberately blunt, because a scanner people learn to ignore is
worse than no scanner. If a finding is genuinely benign:

- **gitleaks** — add a narrow regex to `[allowlist]` in `.gitleaks.toml`.
- **public-safety-scan** — add a `(path, value)` pair to `BENIGN` in
  `scripts/public_safety_scan.py`.

Keep the exception as specific as possible and say in the PR why it is safe.
Never silence a finding by deleting the rule.

## If a secret does get committed

Rotate it first — assume it is compromised the moment it is pushed. Removing the
commit is cleanup, not remediation, and it does not un-publish anything.

## Adding a skill

One directory under `skills/`, containing a `SKILL.md` with YAML frontmatter:

```yaml
---
name: your-skill-name
description: What it does and when an agent should reach for it.
---
```

Write the description so an agent can tell from it alone whether the skill
applies. Put long reference material in a `references/` subdirectory rather than
inflating `SKILL.md`.
