---
name: programmatic-seo
description: >-
  Build, audit, or recover programmatic SEO systems that generate landing pages at scale.
  Use when planning pSEO, templated pages, directory pages, long-tail landing pages,
  city/category/use-case pages, scalable SEO content, indexation gating, crawl-budget
  management, or quality controls for thousands of pages. Coordinates with GSC, GA4,
  internal linking, schema markup, SEO audit, and AI search optimization skills.
metadata:
  version: "1.0.0"
---

# Programmatic SEO

Use this skill to plan, launch, monitor, or recover scalable SEO page systems. The working principle is simple: Google does not punish page count by itself; it punishes value deficiency, doorway behavior, duplication, crawl waste, and poor user outcomes at scale.

Primary source model: Deepak Gupta, "The Programmatic SEO Paradox" (2025): https://guptadeepak.com/the-programmatic-seo-paradox-why-your-fear-of-creating-thousands-of-pages-is-both-valid-and-obsolete/

## Coordinate With

- `google-search-console-analysis`: verify demand, indexation, CTR, crawl stats, manual actions, sitemap health, and cannibalization.
- `google-analytics-seo-analysis`: verify engagement, conversions, return behavior, and landing-page group quality.
- `seo-audit`: diagnose technical SEO, crawlability, Core Web Vitals, canonicalization, and site health.
- `internal-linking-optimizer`: build hub/cluster links, prevent orphan page creation, and distribute authority.
- `schema-markup`: generate valid JSON-LD patterns at template scale.
- `ai-search-optimization`: make page templates citable, answer-first, and useful for AI search engines.

## First Checks

If `.claude/product-marketing-context.md` exists, read it before asking for business context.

Before recommending or building pSEO, identify:

1. Page pattern: entity pages, comparison pages, integration pages, location pages, category filters, use-case pages, glossary pages, or another template.
2. Data source: database, API, UGC, first-party research, scraped data, customer/support signals, or manual editorial work.
3. Search demand: GSC queries, keyword research, support tickets, sales calls, marketplace search logs, competitor gaps.
4. Business goal: conversions, trial signups, leads, affiliate clicks, marketplace liquidity, product discovery, or support deflection.
5. Current scale: planned pages, indexed pages, traffic, organic conversions, crawl stats, and known quality issues.

## Non-Negotiable Page Gates

Do not scale pages that fail these gates. Recommend `noindex`, pruning, consolidation, or manual enrichment instead.

### 1. Unique Answer Gate

Ask: would this page give a materially different answer than sibling pages?

Pass signals:
- The page solves a distinct query or entity need.
- Users would need this exact page, not just the parent category page.
- The page has query-specific explanations, data, examples, comparisons, FAQs, or workflows.

Fail signals:
- Modifier-swapped pages where only city, category, tool, or keyword changes.
- Template copy dominates the page.
- The page exists mainly to funnel users to one generic form or parent page.

Rule of thumb: if a sibling page can replace the variable and remain roughly the same, the pattern is not ready.

### 2. Data Substantiation Gate

Ask: does the page contain unique data that required real effort to collect, compute, verify, or maintain?

Minimum standard:
- At least 5 valuable unique data points per page.
- At least 40% of page value should come from unique data, examples, research, UGC, product data, or computed insight.
- Data must be current enough for the query class.

Useful data types:
- Pricing, availability, compatibility, ratings, reviews, benchmarks, locations, specs, screenshots, examples, workflows, API fields, field mappings, support issues, local facts, trend data, and first-party usage signals.

### 3. Engagement Sustainability Gate

Ask: would search users stay, interact, convert, or return?

Use GA4 and product analytics where possible:
- Engagement rate, engaged sessions, average engagement time, scroll depth, click events, outbound clicks, conversions, and return users.
- Compare pSEO pages against comparable hand-built pages or the site average.

Thresholds:
- Green: engagement metrics within 30% of comparable editorial/product pages.
- Yellow: 30-50% worse; pause scale and improve the template.
- Red: 50%+ worse; halt generation and prune/noindex weak pages.

## Safe Scaling Protocol

Use a staged rollout. Never recommend publishing every possible URL at once unless the site already has proven authority, complete unique data, and monitoring.

### 1. Foundation Audit

Use `seo-audit`, `google-search-console-analysis`, and `google-analytics-seo-analysis`.

Deliver:
- Current organic baseline: clicks, impressions, CTR, average position, organic sessions, conversions.
- Indexation baseline: submitted vs indexed URLs, discovered-not-indexed patterns, crawled-not-indexed patterns.
- Crawl budget health: crawl stats, crawl errors, sitemap segmentation.
- Template risk assessment: duplicate content, thin content, canonicals, noindex rules, robots.txt, Core Web Vitals.

### 2. Template Design

Build the template around utility, not keywords.

Required elements:
- Distinct H1/title/meta tied to the exact entity or query.
- Answer-first intro that states who the page is for and what it solves.
- Unique data modules with provenance or freshness signals.
- Comparison, filtering, calculator, workflow, map, gallery, review, FAQ, or decision-support module where relevant.
- Related pages, parent hub, breadcrumbs, and alternatives.
- Schema chosen from `schema-markup` and populated only with visible, accurate page content.
- Quality score fields stored with each generated page.

Template quality gates:
- 5+ unique data points.
- 400+ useful words or equivalent structured utility.
- Template boilerplate should be less than 40% of page value.
- No autogenerated page should be indexable without passing data, canonical, and link checks.

### 3. Pilot

Start with the highest-value page set, usually 50-150 pages.

Actions:
- Publish the pilot in a dedicated sitemap.
- Submit sitemap in GSC.
- Track the page group in GA4 using landing-page paths, content group, page type, or custom dimensions.
- Monitor daily for 2 weeks, then weekly.

Success criteria:
- No manual actions.
- No crawl-error spike.
- 70%+ indexation for pilot pages after normal discovery time.
- Engagement within 30% of comparable pages.
- Early impressions or clicks appearing in GSC.

### 4. Controlled Scale

Scale only while metrics stay green.

Recommended cadence:
- First expansion: 300-500 total pages.
- Next expansion: 1,500-2,000 total pages.
- Ongoing growth: 20-30% more indexable URLs per month.
- Avoid growing indexable pSEO URLs by more than 50% month over month without strong prior evidence.

Pause scaling when any yellow flag appears. Do not resume until the root cause is fixed.

### 5. Continuous Quality Scoring

Score every generated page from 0-100:

| Factor | Weight |
|---|---:|
| Unique content/data | 20 |
| Number and usefulness of unique data points | 15 |
| Engagement vs comparable pages | 25 |
| Organic trend and indexation health | 20 |
| Conversion or valuable interaction | 20 |

Actions:
- 80-100: keep indexed; use as a model page.
- 60-79: keep indexed; maintain and refresh.
- 40-59: improve, consolidate, or temporarily noindex.
- 0-39: noindex, delete, redirect, or merge.

## GSC Monitoring

Use `google-search-console-analysis` for:

- Search demand validation: high-impression queries without dedicated pages.
- Indexation ratio by page type: indexed pages divided by canonical pages submitted for that page type.
- Sitemap performance: errors, submitted counts, discovered/crawled but not indexed.
- CTR opportunities: pages ranking 1-5 with weak CTR.
- Cannibalization: multiple pSEO URLs competing for the same query.
- Manual actions and security issues.
- Crawl stats and crawl errors.

Health thresholds:

| Signal | Green | Yellow | Red |
|---|---:|---:|---:|
| Indexation ratio | 60%+ | 40-60% | <40% |
| Crawl efficiency | 50%+ useful crawls | 30-50% | <30% |
| Duplicate/title/canonical issues | isolated | growing | affects 20%+ |
| Crawl errors | stable/low | rising | >10% of pSEO URLs |
| Manual actions | none | n/a | any notice |

## GA4 Monitoring

Use `google-analytics-seo-analysis` for:

- Organic landing-page engagement by page type.
- Conversions and assisted conversions from pSEO pages.
- Engagement rate, engaged sessions, average engagement time, scroll/click events, and return users.
- Comparisons against editorial, product, or manually created pages.
- Cohort behavior for newly published page batches.
- Weak-page detection for pruning or noindex decisions.

Health thresholds:

| Signal | Green | Yellow | Red |
|---|---:|---:|---:|
| Engagement vs comparable pages | within 30% | 30-50% worse | 50%+ worse |
| Conversions | stable or improving | weak but present | no value after discovery period |
| Return users | present for repeat-use topics | low | absent where expected |
| Pogo-risk proxy | healthy engaged sessions | high exits | very short engagement |

## Indexation Strategy

Use three tiers:

1. Always index: highest-value pages with complete unique data, search demand, and strong engagement.
2. Conditional index: useful but lower-priority pages; monitor and noindex if quality drops.
3. Strategic noindex: incomplete, low-demand, internal, or future-value pages.

Do not include noindexed, canonicalized-away, parameter, faceted, or low-quality pages in priority sitemaps.

## Internal Linking Requirements

Use `internal-linking-optimizer` for link graph planning.

Minimum for indexable pSEO pages:
- Breadcrumbs to parent hubs.
- 5-8 closely related contextual links.
- Links to parent category/hub pages.
- Links to alternatives, comparisons, or adjacent entities.
- Each important page should receive 5-10 relevant internal links over time.

Avoid isolated pages. If the site cannot link to a page naturally, question whether it should exist.

## Recovery Workflow

Use this when a site with pSEO pages loses traffic, loses indexation, or receives a manual action.

1. Freeze new page generation.
2. Segment pages by template, launch batch, indexation status, organic sessions, conversions, and quality score.
3. Identify bottom pages: zero traffic, low engagement, duplicate data, no conversions, or deindexed for months.
4. Keep and enrich winners; merge, redirect, delete, or noindex weak pages.
5. Fix template-level defects before publishing new URLs.
6. Submit updated sitemaps and request recrawls for high-value pages.
7. Resume with a smaller batch only after GSC and GA4 show stabilization.

For manual actions, document fixes and submit reconsideration only after the offending patterns are removed.

## Output Formats

### pSEO Plan

```markdown
# Programmatic SEO Plan: [site/topic]

## Page Pattern
[template type and target query classes]

## Demand Evidence
[GSC/keyword/customer/competitor evidence]

## Page Gates
| Gate | Requirement | Status | Risk |
|---|---|---|---|

## Data Model
[unique data fields, source, freshness]

## Template Modules
[content, utility, schema, links, conversion modules]

## Rollout
[pilot size, sitemap, noindex/index rules, expansion cadence]

## Monitoring
[GSC metrics, GA4 metrics, stop/pause thresholds]

## Required Work
[engineering/content/data tasks in priority order]
```

### pSEO Audit

```markdown
# Programmatic SEO Audit: [site]

## Executive Diagnosis
[healthy / cautious / stop-scaling / recovery]

## Metrics
| Area | Current | Threshold | Status |
|---|---:|---:|---|

## Template Risks
[duplication, thin content, crawl waste, poor engagement]

## Page Actions
| Segment | Count | Action | Reason |
|---|---:|---|---|

## Fix Plan
1. [highest-impact fix]
2. [next fix]
3. [monitoring change]
```
