---
name: google-search-console-analysis
description: >-
  Fetch or analyze Google Search Console data for SEO decisions. Use when the user mentions
  GSC, Google Search Console, Search Console performance, queries, impressions, CTR,
  average position, indexation, sitemap status, crawl stats, manual actions, low-hanging
  fruit keywords, cannibalization, or pSEO monitoring.
metadata:
  version: "1.0.0"
---

# Google Search Console Analysis

Use this skill to turn GSC data into SEO actions. Prefer real GSC exports or API output. If credentials are available locally, use the existing Claude-side script rather than recreating a fetcher.

## Data Access

Existing script:

```bash
node ~/.claude/skills/gsc-analysis/scripts/gsc-fetch.cjs --site=DOMAIN --days=28 --output=/tmp/gsc-DOMAIN.json
```

Notes:
- Logs go to stderr; JSON data goes to stdout or the `--output` path.
- The script checks `$GCP_KEY_FILE`, `~/projects/convertbanktoexcel.com/cloud/keys/coldstart-labs-service-account-key.json`, then `./cloud/keys/coldstart-labs-service-account-key.json`.
- The service account must have access to the GSC property, usually `sc-domain:DOMAIN`.
- GSC has a normal 2-3 day data lag.
- If the script cannot run, ask for a GSC export or use user-provided screenshots/data.

## Core Workflow

1. Determine property and date range.
2. Fetch query/page, daily trend, device, country, and sitemap data where available.
3. Segment by page type when possible: blog, product, pSEO, category, tool, homepage, docs.
4. Compare against the user's goal: growth, recovery, CTR, indexation, cannibalization, or pSEO safety.
5. Return prioritized actions, not just metrics.

## Analyses

### Performance Summary

Report:
- Clicks, impressions, CTR, average position.
- Daily trend and week-over-week or period-over-period change.
- Top queries and pages by clicks.
- Top queries and pages by impressions.
- Device and country splits.

### Low-Hanging Fruit

Prioritize queries with high impressions and positions 8-25.

Difficulty bands:
- Easy: position 8-12; title/meta/H1/internal-link improvements.
- Medium: position 13-18; content expansion and stronger links.
- Hard: position 19-25; search-intent rewrite or new page required.

Opportunity score:

| Factor | Weight |
|---|---:|
| Impressions | 30 |
| Position gap | 25 |
| Effort required | 25 |
| Commercial intent | 20 |

### CTR Optimization

Flag pages ranking well but underperforming CTR:

| Avg Position | Weak CTR |
|---:|---:|
| 1 | <20% |
| 2 | <10% |
| 3 | <7% |
| 4-5 | <4% |

Recommend title, meta description, rich-result/schema, brand, and intent alignment fixes.

### Cannibalization

Flag queries where multiple URLs receive meaningful impressions or clicks.

For each issue, decide:
- Consolidate pages.
- Canonicalize.
- Retarget one page.
- Add internal links to establish the intended primary URL.
- Keep multiple pages only when intents are genuinely different.

### Indexation and pSEO Safety

For programmatic SEO, segment by page type or path prefix.

Track:
- Submitted pages.
- Indexed pages.
- Indexation ratio.
- Discovered currently not indexed.
- Crawled currently not indexed.
- Duplicate/canonical issues.
- Crawl errors.
- Manual actions.
- Sitemap errors and warnings.

Thresholds:
- Green: indexation ratio 60%+, stable crawl errors, no manual actions.
- Yellow: indexation ratio 40-60%, growing excluded pages, weak sitemap health.
- Red: indexation ratio <40%, manual action, crawl errors above 10% of target URLs, duplicate issues affecting 20%+ of pages.

## Output Format

```markdown
# GSC Analysis: [domain]
**Period**: [date range] | **Data source**: [API/export/manual]

## Performance Summary
| Metric | Value | Notes |
|---|---:|---|

## Top Queries
| Query | Clicks | Impressions | CTR | Position | Primary Page |
|---|---:|---:|---:|---:|---|

## Top Pages
| Page | Clicks | Impressions | CTR | Position | Notes |
|---|---:|---:|---:|---:|---|

## Opportunities
| Priority | Query/Page | Evidence | Action |
|---:|---|---|---|

## Risks
[indexation, cannibalization, CTR, crawl, manual action risks]

## Recommended Next Steps
1. [highest impact action]
2. [next action]
3. [monitoring or validation step]
```

## Related Skills

- `programmatic-seo`: for scalable page planning and safety gates.
- `seo-content-3-kings-technique`: for position 5-15 title/H1/intro refreshes.
- `seo-audit`: for technical and on-page audits.
- `internal-linking-optimizer`: for authority flow and orphan fixes.
