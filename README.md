# Agent Skills

Reusable skills for AI coding agents — Claude Code, Codex, and anything else that
reads a `SKILL.md`. 68 skills covering planning, execution, review, research,
and release validation.

This repository is public-safe by construction: no credentials, no personal
identifiers, no private project names. Two CI gates enforce it on every pull
request — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Install

Skills are plain directories. Symlink the ones you want into your agent's skills
directory:

```bash
git clone https://github.com/jonit-dev/agent-skills.git
cd agent-skills

# Claude Code
ln -s "$PWD/skills/improve" ~/.claude/skills/improve

# Codex
ln -s "$PWD/skills/improve" ~/.codex/skills/improve
```

To share one set between both agents, keep the checkout in a neutral location
and symlink from each agent's directory into it.

## Contents

### Planning and specification

| Skill | What it does |
| --- | --- |
| `prd-creator` | Create implementation-ready PRDs with complexity scoring, phases, and verification plans |
| `prd-executor` | Execute a PRD by decomposing phases into dependency-aware parallel workstreams |
| `writing-plans` | Write practical implementation plans for software changes |
| `implementation-plan` | Turn a request into a sequenced, reviewable plan |
| `implementation-notes` | Keep a running record of decisions made during a build |
| `interview-me` | Interview the user one question at a time to resolve ambiguity before implementation |
| `blindspot-pass` | Surface unknown unknowns before starting work in an unfamiliar area |
| `the-one-thing` | Reduce a sprawling request to the single highest-leverage action |
| `github-issue-prd-sync` | Keep GitHub issues and PRDs aligned |

### Execution and refactoring

| Skill | What it does |
| --- | --- |
| `improve` | Survey a codebase as a senior advisor and produce prioritized handoff plans |
| `afk-work` | Operating contract for autonomous work when the user is away |
| `gauntlet-loop` | Build/critique/integrate loop that drives an artifact to a quality bar |
| `react-refactoring` | Restructure React code without changing behavior |
| `dead-code-detector` | Find unused code, orphaned files, and unreachable endpoints |
| `codebase-inspection` | Map an unfamiliar codebase before changing it |
| `system-documenter` | Architecture cartography and living system documentation |
| `spike` | Time-boxed experiments before committing to a build |
| `skill-creator` / `skill-optimizer` | Author and tighten skills themselves |
| `wikiskill-evolution` | Turn recurring lessons into durable project knowledge |

### Review, testing, and debugging

| Skill | What it does |
| --- | --- |
| `code-review-excellence` | Review diffs for actionable defects; set review standards |
| `requesting-code-review` | Pre-commit review and quality gates |
| `github-code-review` | Review on GitHub, with inline comments |
| `swarm-validated-review` | Multi-agent review with independent verification of findings |
| `debugging-strategies` | Diagnose bugs and regressions from reproducible evidence |
| `systematic-debugging` | Root-cause debugging workflow |
| `test-driven-development` | RED/GREEN/REFACTOR workflow |
| `e2e-testing-patterns` | Reliable end-to-end suites with Playwright and Cypress |
| `dogfood` | Exploratory QA of web applications |
| `local-self-verification` | Evidence-based local verification before handoff |
| `change-quiz` | Generate a quiz that proves you understand a change before merging |

### Git and release workflow

| Skill | What it does |
| --- | --- |
| `git-worktree` | Manage project-local worktrees, and clean them up after merge |
| `git-advanced-workflows` | Rebase, bisect, and recovery workflows |
| `github-pr-workflow` | Open, review, and land pull requests |
| `github-issues` | Triage and manage issues |
| `babysit-prs` | Scan an org for open PRs, fix issues, and label ready-to-merge |
| `discord-announcement` | Generate player-facing release notes from unreleased changes |
| `refresh-distribution-proof` | Re-verify distribution claims before a release |

### Release validation

| Skill | What it does |
| --- | --- |
| `validate-concurrent-workflows` | Verify claims, leases, fencing, and concurrency recovery |
| `validate-credit-ledger-invariants` | Test credit-ledger integrity and race conditions |
| `validate-durable-outbox-delivery` | Prove durable event delivery and idempotency |
| `validate-prd-release-evidence` | Assess PRD completion and release readiness |
| `validate-supabase-migrations` | Validate fresh and upgrade migration chains |
| `validate-timezone-scheduling` | Test timezone and DST-sensitive scheduling |
| `verify-android-webview-responsive-input` | Verify responsive input in Android WebViews |
| `stripe-debugging` | Diagnose Stripe integration incidents without exposing secrets |

### Research and analysis

| Skill | What it does |
| --- | --- |
| `last30days` | Research a topic across Reddit, X, and the web, then write ready-to-use prompts |
| `autoresearch` | Autonomous multi-source research runs |
| `reference-hunt` | Track down authoritative sources for a claim |
| `forecasting-experiments` | Design and evaluate forecasting experiments |
| `biotech-fundamental-analysis` | Score biotech companies on fundamentals separately from valuation |
| `feature-mining-sandbox-validation` | Prove a framework feature works by building a mini game against it |

### Web, SEO, and performance

| Skill | What it does |
| --- | --- |
| `audit-website` | Audit a site across SEO, performance, security, and content rules |
| `pagespeed` | Diagnose and fix page speed problems |
| `programmatic-seo` | Build programmatic SEO page systems |
| `google-analytics-seo-analysis` | Analyze GA data for SEO decisions |
| `google-search-console-analysis` | Turn Search Console data into action |

### Product, writing, and output

| Skill | What it does |
| --- | --- |
| `lean-product-playbook` | Product discovery and validation sequence |
| `design-directions` | Generate divergent HTML prototypes to react to before implementation |
| `taste-skill` | Raise the quality bar on generated design and copy |
| `humanizer` | Strip AI tells out of written output |
| `pitch-explainer` | Explain a product or change to a non-technical audience |
| `attention-ping` | Notify the user by ntfy when an agent is genuinely blocked |
| `md-to-pdf` / `print` / `print-ready-docx` | Render Markdown to PDF, DOCX, or a physical printer |
| `xlsx-workbooks` | Read, build, format, and validate Excel workbooks |
| `pokemon-tcg-api` | Query Pokémon TCG card, set, and price data |

## Contributing

Pull requests only — `main` is protected and both secret-scanning checks must
pass. Read [CONTRIBUTING.md](CONTRIBUTING.md) first; it covers what must never be
committed and how to handle a false positive.

## License

See [LICENSE](LICENSE).
