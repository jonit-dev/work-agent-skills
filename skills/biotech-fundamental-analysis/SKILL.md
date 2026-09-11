---
name: biotech-fundamental-analysis
description: >
  Disciplined biotech fundamental analysis framework that separates business quality
  (Fundamental Score 0-10) from valuation attractiveness (Value Score). Produces structured
  investment reports with scoring, competitive landscape, red flag analysis, and portfolio
  positioning. Use when the user asks to "analyze a biotech company", "score a biotech stock",
  "evaluate a biotech pipeline", "biotech fundamental analysis", "biotech due diligence",
  "biotech investment thesis", "score this biotech", "biotech valuation", "biotech competitive
  analysis", "quarterly biotech re-score", or any biotech investment evaluation task.
---

# Biotech Fundamental Analysis Framework

> Disciplined, repeatable, evidence-driven system for evaluating biotech companies.

## Two Independent Scores

| Score | Measures | Scale |
|-------|----------|-------|
| **Fundamental Score** | Business quality | 0-10 (6 categories) |
| **Value Score** | Valuation attractiveness | Qualitative (NPV-based) |

These combine into a 2x2 portfolio positioning matrix.

## Analysis Workflow

### Step 1: Gather Company Information

Collect via web search, SEC filings, press releases, ClinicalTrials.gov:
- Ticker, market cap, cash position, quarterly burn rate
- Pipeline assets by stage (preclinical through approved)
- Key upcoming catalysts and data readout timelines
- Management team backgrounds and track records
- Competitive landscape and standard of care

### Step 2: Fundamental Score (0-10)

Apply the 6-category rubric. See [references/scoring-criteria.md](references/scoring-criteria.md) for full criteria.

| Category | Max |
|----------|-----|
| Science & Platform Strength | 2 |
| Pipeline Depth & Breadth | 2 |
| Clinical Data Quality | 2 |
| Management Quality & Execution | 2 |
| Market Opportunity / Economic TAM | 1 |
| Cash Runway & Balance Sheet | 1 |

**Hard filters**: Flag companies scoring 0 in Science or Clinical Data as structurally weak regardless of total score.

### Step 3: Competitive Landscape & Red Flags

Evaluate competitive positioning and run the red flag checklist. See [references/red-flags.md](references/red-flags.md) for the structured framework covering scientific, clinical, commercial, financial, and management red flags.

### Step 4: Value Score

Evaluate mispricing on five dimensions:
1. **Economic TAM** — actual monetizable opportunity (not headline TAM)
2. **NPV per Share** — probability-adjusted, summed across pipeline, vs market price
3. **Time to Cash Flows** — shorter = better, penalize long uncertain paths
4. **Probability-Adjusted Valuation** — phase success rates, mechanism/competitive/regulatory risk
5. **Margin of Safety** — buffer between NPV and market price (non-negotiable for high Value Score)

### Step 5: Generate Report

Use the template in [references/report-template.md](references/report-template.md). Save to `reports/biotech-analysis-{TICKER}-{YYYY-MM-DD}.md`.

### Step 6: Portfolio Positioning

Map to the 2x2 matrix:

```
                    High Fundamental Score
                           |
          MONITOR          |        PRIORITY BUY
       (quality, pricey)   |     (quality + cheap)
  ─────────────────────────┼──────────────────────
          REMOVE           |       VALUE TRAP
       (weak + pricey)     |     (cheap but weak)
                           |
                    Low Fundamental Score
  Left = Expensive              Right = Undervalued
```

## Quarterly Re-Scoring

1. Update Fundamental Scores with new data
2. Update Value Scores for price/NPV changes
3. Re-rank universe, adjust portfolio weights
4. Refresh watchlists, document every score change with rationale

## Principles

- Every score tied to explicit, cited evidence
- Never let cheapness excuse weak fundamentals
- Red flags override scores
- Economic TAM = actual monetizable opportunity
- Probability-adjust everything
- Margin of safety is non-negotiable
