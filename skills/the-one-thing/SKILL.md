---
name: the-one-thing
description: >
  360-degree project analysis that identifies THE ONE THING per category — the single
  highest-leverage action in each dimension of a released product. Categories: Code & Architecture,
  Marketing & Growth, SEO & Content, Product & UX, Operations & Infrastructure. Produces a
  unified strategic report with a cross-cutting "First Domino" recommendation.
  Inspired by Gary Keller's "The One Thing." Use when the user asks "what should I focus on?",
  "what's the most important thing?", "where should I focus?", "analyze my project",
  "the one thing", "project health check", "360 review", or any variant.
  Accepts optional arguments: a specific category to focus on, or "all" (default) for full 360.
---

# The One Thing — 360 Report

> "What's the ONE thing I can do such that by doing it everything else will be easier or unnecessary?"
> — Gary Keller

## Philosophy

This skill applies Gary Keller's Focusing Question to **every dimension** of a released product.
A product isn't just code — it's code + marketing + SEO + product experience + operations.
The goal: find the **first domino** in each category, then identify the **cross-cutting first domino**
that creates the most cascading value across ALL categories.

A single domino can knock over another 50% larger than itself. The right fix cascades.

## The Six Lies of Products

1. **Not everything matters equally** — 20% of effort drives 80% of results. Find the 20%.
2. **Multitasking fixes don't work** — Fixing 1 thing deeply beats fixing 10 shallowly.
3. **Discipline isn't the answer** — The right system eliminates the need for discipline.
4. **Willpower is finite** — If a process requires constant vigilance, it's the wrong process.
5. **Perfect balance is a myth** — Sometimes you must let one area slip to fix the foundation.
6. **Big moves aren't scary** — A bold strategic shift is less risky than a hundred incremental workarounds.

## Categories

The analysis covers 5 categories. Each gets its own "One Thing."

| # | Category | Scope |
|---|----------|-------|
| 1 | **Code & Architecture** | Tech debt, architecture, testing, type safety, DX, dependencies |
| 2 | **Marketing & Growth** | Positioning, channels, conversion, social proof, content marketing |
| 3 | **SEO & Content** | Technical SEO, content strategy, keyword coverage, SERP visibility |
| 4 | **Product & UX** | User experience, feature gaps, onboarding, retention, pricing |
| 5 | **Operations & Infra** | Deployment, monitoring, security, cost, reliability, CI/CD |

## Analysis Process

### Phase 1: Rapid Reconnaissance (Breadth)

Gather signal across ALL categories using parallel tool calls. Speed matters.

#### 1.1 Code & Architecture Signals

**Project vitals:**
- Read package.json / equivalent for deps, scripts, engine constraints
- Read main config files (tsconfig, eslint, CI configs)
- Check `git log --oneline -50` for recent commit patterns and churn

**Structural scan:**
- Map the top-level directory structure
- Identify architectural pattern (monolith, monorepo, microservices, etc.)
- Read AGENTS.md, README, or ARCHITECTURE.md for stated conventions

**Pain signal detection:**

| Dimension | What to look for |
|-----------|-----------------|
| **Architecture** | Circular dependencies, god files (>500 lines), unclear boundaries, mixed concerns |
| **Tech Debt** | TODO/FIXME/HACK comments, @ts-ignore, eslint-disable, suppressed warnings |
| **Error Handling** | Empty catch blocks, swallowed errors, inconsistent error patterns |
| **Type Safety** | `any` types, missing validations at boundaries, implicit contracts |
| **Testing** | Missing test directories, low-signal tests, no integration tests, flaky test patterns |
| **DX** | Slow builds, missing scripts, no local dev setup, poor error messages |
| **Dependencies** | Outdated major versions, abandoned packages, duplicate functionality |

Use Grep with targeted patterns:
```
# Tech debt signals
TODO|FIXME|HACK|XXX|WORKAROUND
@ts-ignore|@ts-expect-error|eslint-disable|noqa|noinspection
# Error handling gaps
catch\s*\(\s*\w*\s*\)\s*\{\s*\}
# Type safety issues (TypeScript)
:\s*any[^a-zA-Z]|as\s+any
# Convention violations
process\.env\. (if project convention says not to use it)
```

Use `git log --format='%H' --diff-filter=M -- '*.ts' | head -20` to find most-modified files (churn = pain).

**Health checks:**
- Does `lint` pass? Does `typecheck` pass? Do `tests` pass?
- Check CI config and recent run status
- Look for verify/check scripts

#### 1.2 Marketing & Growth Signals

**Look for marketing artifacts:**
- Check `docs/marketing/`, `docs/business-model-canvas/`, `docs/research/`
- Read README or landing page component for positioning language
- Check for analytics integration (Amplitude, GA, Mixpanel, etc.)
- Look for referral system, social sharing, or viral mechanics in code

**Analyze from code:**
- Pricing page component — how clear is the value proposition per tier?
- Onboarding flow — what happens after signup? Is there a guided experience?
- CTA patterns — are there conversion points throughout the product?
- Social proof — testimonials, user counts, trust badges in UI components?
- Email templates — transactional only or also marketing/nurture sequences?

**External signals (if URL available):**
- Check for social media links, blog, newsletter signup
- Look at meta descriptions for marketing messaging quality

#### 1.3 SEO & Content Signals

**Technical SEO scan:**
- Check sitemap configuration (count pages, verify structure)
- Look for robots.txt configuration
- Scan metadata generation (title, description, OG tags, structured data)
- Check for hreflang implementation (internationalization)
- Look for canonical URL handling
- Check for SEO test coverage

**Content strategy scan:**
- Count blog posts and pSEO pages (scale of content)
- Check content freshness (last updated dates)
- Look for keyword coverage in pSEO data files
- Check for internal linking strategy
- Scan for content gaps (categories with few pages)

**Performance signals:**
- Check for Core Web Vitals optimization (image optimization, lazy loading)
- Look for PageSpeed scripts or reports
- Check for CDN/edge caching configuration

#### 1.4 Product & UX Signals

**Feature completeness:**
- Read feature documentation (docs/features/, CURRENT-FEATURES.md)
- Check for PRDs in progress (docs/PRDs/ — what's planned vs done?)
- Look for roadmap (docs/management/ROADMAP.md)
- Identify the core user flow and check for friction points

**User experience:**
- Check for loading states, error states, empty states in UI components
- Look for accessibility patterns (ARIA, keyboard navigation)
- Check mobile responsiveness approach
- Analyze the pricing/checkout flow for conversion optimization
- Look for user feedback mechanisms (support forms, help pages)

**Retention signals:**
- Dashboard experience — is it valuable enough to return daily?
- Notification system — email, push, in-app?
- Usage tracking — does the product know how users behave?

#### 1.5 Operations & Infrastructure Signals

**Deployment:**
- Check deployment scripts and CI/CD configuration
- Look for staging/production environment separation
- Check for rollback capability
- Assess deployment frequency from git history

**Monitoring & Observability:**
- Check for error tracking (Baselime, Sentry, etc.)
- Look for logging patterns (structured logging, log levels)
- Check for health endpoints
- Look for alerting configuration

**Security:**
- Check for security headers implementation
- Look for rate limiting
- Check for input validation patterns
- Scan for hardcoded secrets or exposed env vars
- Check dependency vulnerabilities (if audit data available)

**Cost & Infrastructure:**
- Check hosting configuration (Cloudflare, Vercel, AWS, etc.)
- Look for resource constraints (CPU limits, memory, etc.)
- Check for caching strategy (Redis, CDN, browser cache)

### Phase 2: Deep Dive (Depth on Top Candidates)

From Phase 1, you'll have pain signals across all 5 categories. For each category's top candidate, apply the Focusing Question:

1. **Cascade potential**: If I fix this, how many other problems become easier or disappear?
2. **Blast radius**: How much of the product/codebase does this touch?
3. **Frequency**: How often does this cause pain (for developers, users, or the business)?
4. **Trend**: Is this getting worse over time? (Check git history, user growth trajectory)
5. **Reversibility**: Can this be fixed incrementally, or does it require a big bang?

**The domino test per category**: Imagine you fix this one thing perfectly. Re-examine the other candidates in that category. How many become easier, less painful, or irrelevant?

**The cross-cutting domino test**: Look across all 5 category winners. Which ONE, if fixed, would make the most OTHER category-winners easier? That's the overall First Domino.

### Phase 3: The 360 Report

Present findings in this exact structure:

---

# THE ONE THING — 360 Report

> Project: [name] | Date: [date] | Status: [Released/Beta/etc.]

## Executive Summary

[2-3 sentences: the single cross-cutting First Domino and why it matters most right now.
This is the answer to "if you could only do one thing this month, what should it be?"]

---

## 1. CODE & ARCHITECTURE

### The One Thing
**[One sentence: what it is]**

### Why This Is The First Domino
[2-3 sentences explaining the cascade effect. Reference specific files/patterns.]

### Evidence
[Bullet list of concrete signals. File paths, line counts, grep results, git churn data.]

### Domino Chain
```
FIX: [the one thing]
 └─► [problem that becomes easier #1]
 └─► [problem that becomes easier #2]
 └─► [problem that disappears entirely]
```

### Action
[Concrete, actionable first step. "Start by doing X in file Y."]

### Skip This
[1 thing the developer might be tempted to fix instead that would be lower leverage.]

---

## 2. MARKETING & GROWTH

### The One Thing
**[One sentence: what it is]**

### Why This Is The First Domino
[2-3 sentences. What growth unlock does this enable?]

### Evidence
[Concrete signals: missing social proof, unclear positioning, no email sequences,
weak CTAs, missing referral system, etc. Reference actual files/pages.]

### Domino Chain
```
FIX: [the one thing]
 └─► [growth problem that becomes easier #1]
 └─► [growth problem that becomes easier #2]
 └─► [growth problem that disappears entirely]
```

### Action
[Concrete first step. Not "do more marketing" but "add X to Y page."]

### Skip This
[1 marketing activity that feels productive but is lower leverage.]

---

## 3. SEO & CONTENT

### The One Thing
**[One sentence: what it is]**

### Why This Is The First Domino
[2-3 sentences. What SEO unlock does this enable?]

### Evidence
[Concrete signals: missing pages, weak metadata, content gaps, technical issues.
Reference sitemap counts, metadata patterns, pSEO coverage.]

### Domino Chain
```
FIX: [the one thing]
 └─► [SEO problem that becomes easier #1]
 └─► [SEO problem that becomes easier #2]
 └─► [SEO problem that disappears entirely]
```

### Action
[Concrete first step.]

### Skip This
[1 SEO activity that feels productive but is lower leverage.]

---

## 4. PRODUCT & UX

### The One Thing
**[One sentence: what it is]**

### Why This Is The First Domino
[2-3 sentences. What user experience or retention unlock does this enable?]

### Evidence
[Concrete signals: missing features, broken flows, UX friction points,
competitor gaps. Reference actual components/pages.]

### Domino Chain
```
FIX: [the one thing]
 └─► [product problem that becomes easier #1]
 └─► [product problem that becomes easier #2]
 └─► [product problem that disappears entirely]
```

### Action
[Concrete first step.]

### Skip This
[1 product improvement that feels important but is lower leverage.]

---

## 5. OPERATIONS & INFRASTRUCTURE

### The One Thing
**[One sentence: what it is]**

### Why This Is The First Domino
[2-3 sentences. What reliability or efficiency unlock does this enable?]

### Evidence
[Concrete signals: deployment issues, monitoring gaps, security vulnerabilities,
cost inefficiencies. Reference actual configs/scripts.]

### Domino Chain
```
FIX: [the one thing]
 └─► [ops problem that becomes easier #1]
 └─► [ops problem that becomes easier #2]
 └─► [ops problem that disappears entirely]
```

### Action
[Concrete first step.]

### Skip This
[1 ops improvement that feels urgent but is lower leverage.]

---

## THE FIRST DOMINO (Cross-Cutting)

### If You Can Only Do One Thing This Month:

**[One sentence: the single most impactful action across all categories]**

[3-5 sentences explaining why this particular action has the highest cross-category
cascade effect. Show how it makes at least 2 other category-winners easier.]

### Cross-Category Cascade
```
FIRST DOMINO: [the one thing]
 ├─► Code: [how it helps]
 ├─► Marketing: [how it helps]
 ├─► SEO: [how it helps]
 ├─► Product: [how it helps]
 └─► Ops: [how it helps]
```

### Priority Matrix

| Priority | Category | One Thing | Effort | Impact |
|----------|----------|-----------|--------|--------|
| 1 | [category] | [one thing] | [S/M/L] | [S/M/L] |
| 2 | [category] | [one thing] | [S/M/L] | [S/M/L] |
| 3 | [category] | [one thing] | [S/M/L] | [S/M/L] |
| 4 | [category] | [one thing] | [S/M/L] | [S/M/L] |
| 5 | [category] | [one thing] | [S/M/L] | [S/M/L] |

---

## Anti-Patterns to Avoid

### Per Category
- **The laundry list**: ONE thing per category. If you can't pick one, you haven't gone deep enough.
- **The obvious pick**: "Write more tests" / "Do more marketing" / "Create more content" are symptoms. What makes them hard? Fix that.
- **The surface fix**: If your one thing is a symptom, keep asking "why?" until you hit the root cause. Five Whys.
- **The scope creep**: Each one thing should be achievable in days to weeks, not months.
- **The popularity bias**: The most-discussed issue isn't necessarily the highest-leverage one.

### Cross-Cutting
- **Category tunnel vision**: Don't let the code category always win. A marketing unlock might be 10x more impactful than a refactor for a released product.
- **The builder's bias**: Engineers default to "make it better." Sometimes the product is good enough and the bottleneck is distribution, not quality.
- **Revenue blindness**: For released products, always ask "which category directly unblocks revenue growth?" That category deserves extra weight.

## Edge Cases

- **Healthy product**: If everything is solid, the one thing might be about scaling what's working (doubling down on the winning channel) rather than fixing what's broken.
- **Pre-revenue**: The one thing is almost always in Marketing/Growth or Product/UX, not Code.
- **Post-product-market-fit**: The one thing is often Operations (scaling) or Marketing (growth).
- **Struggling product**: The one thing is usually Product (are we solving the right problem?) or Marketing (are we reaching the right people?).

## Running the Analysis

Use the Task tool to spawn parallel research agents where beneficial:
- One agent for code/architecture deep dive
- One agent for SEO/content analysis
- Main thread handles marketing, product, and ops (requires more context from docs)

This maximizes speed while maintaining depth. Consolidate findings in Phase 3.

### Phase 4: Save Report to Disk

After presenting the report to the user, **always save the full report as a markdown file**:

1. **Location**: `docs/reports/the-one-thing-360-{YYYY-MM-DD}.md`
2. **Format**: The complete Phase 3 report as written — no truncation
3. **Naming**: Use the current date for the filename
4. **Notify user**: Confirm the file path after saving

This creates a historical record of strategic decisions and lets the team track how priorities evolve over time.
