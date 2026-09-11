---
name: google-analytics-seo-analysis
description: >-
  Analyze Google Analytics 4 data for SEO and programmatic SEO decisions. Use when the user
  mentions GA, GA4, Google Analytics, organic sessions, landing pages, engagement rate,
  engaged sessions, average engagement time, conversions, events, return users, traffic
  channels, attribution, or SEO conversion analysis.
metadata:
  version: "1.0.0"
---

# Google Analytics SEO Analysis

Use this skill to evaluate whether organic traffic and SEO landing pages create useful engagement and business outcomes. Prefer GA4 exports, BigQuery GA4 data, or API output. If no direct access exists, ask for the smallest useful export rather than a broad analytics dump.

## Required Data

For most SEO work, request or derive:

- Date range and comparison period.
- Landing page + query string, session default channel group, source/medium.
- Sessions, engaged sessions, engagement rate, average engagement time per session.
- Key events/conversions and revenue if applicable.
- New users, returning users, total users.
- Device category and country when relevant.
- Page path/content group/page type for pSEO segmentation.

For programmatic SEO, add:
- Launch batch or publish date.
- Template/page type.
- Index status when available from GSC.
- Page quality score if the site stores one.

## Core Workflow

1. Define the SEO question: growth, conversion, engagement quality, page pruning, pSEO rollout, or recovery.
2. Filter to organic search unless the task explicitly needs all channels.
3. Segment landing pages by page type or URL pattern.
4. Compare pSEO pages against relevant baselines: editorial, product, tools, manually created pages, or site average.
5. Identify winners, underperformers, and pages needing noindex, merge, refresh, or better internal links.
6. Tie recommendations to business value, not just engagement.

## Organic Landing Page Analysis

Report by landing page:

| Metric | Use |
|---|---|
| Organic sessions | Demand and traffic scale |
| Engaged sessions | Quality proxy |
| Engagement rate | Landing-page satisfaction proxy |
| Avg engagement time | Depth proxy |
| Key events/conversions | Business value |
| Return users | Repeat usefulness |
| Device/country split | UX or intent differences |

Interpretation:
- High sessions + low engagement: likely intent mismatch, slow page, weak above-the-fold answer, or thin content.
- Low sessions + high conversion: improve rankings and internal links.
- High impressions in GSC + low GA sessions: CTR issue or ranking volatility.
- Indexed pSEO pages + no engagement/conversions after a fair period: consider noindex, merge, or delete.

## pSEO Health Thresholds

Compare programmatic pages against similar non-programmatic pages.

| Signal | Green | Yellow | Red |
|---|---:|---:|---:|
| Engagement rate | within 30% | 30-50% worse | 50%+ worse |
| Avg engagement time | within 30% | 30-50% worse | 50%+ worse |
| Conversion rate | comparable or better | weak but nonzero | zero value after discovery period |
| Return users | present if expected | low | absent where repeat use is expected |

Actions:
- Green pages: keep indexed, add links, use as template examples.
- Yellow pages: improve content modules, internal links, SERP promise, and conversion path.
- Red pages: halt similar page generation; noindex, merge, redirect, or delete weak segments.

## SEO Conversion Analysis

For each top organic landing page or page segment:

1. Identify the main search intent.
2. Map expected conversion or key event.
3. Check whether the page provides a direct path to that action.
4. Compare conversion rate against pages with similar intent.
5. Recommend changes to CTA placement, trust evidence, comparison modules, examples, or product routing.

Avoid treating all organic traffic equally. Informational pages, comparison pages, local/entity pages, and product pages should have different conversion expectations.

## Recovery Analysis

When traffic drops:

1. Split by landing page type, device, country, and date.
2. Identify whether the drop is traffic-only, engagement-only, or conversion-only.
3. Cross-check with GSC: impressions down means ranking/indexation; CTR down means SERP/title/rich-result issue; clicks down with stable GA conversion rate means acquisition issue.
4. Find pages that still get traffic but lost engagement after template, UX, speed, or content changes.
5. Recommend page-group actions.

## Output Format

```markdown
# GA4 SEO Analysis: [site/property]
**Period**: [date range] | **Data source**: [export/API/BigQuery/manual]

## Organic Summary
| Metric | Current | Previous | Change |
|---|---:|---:|---:|

## Landing Page Segments
| Segment | Sessions | Engagement Rate | Avg Engagement | Key Events | Status |
|---|---:|---:|---:|---:|---|

## Winners
[pages or segments to expand, link to, or model]

## Underperformers
| Page/Segment | Evidence | Likely Cause | Action |
|---|---|---|---|

## Recommendations
1. [highest value action]
2. [next action]
3. [measurement change]
```

## Related Skills

- `programmatic-seo`: for pSEO rollout and pruning decisions.
- `google-search-console-analysis`: for impressions, rankings, indexation, and CTR.
- `seo-audit`: for technical issues that affect analytics outcomes.
- `internal-linking-optimizer`: for routing authority and users to high-value pages.
