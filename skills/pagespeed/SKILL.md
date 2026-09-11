---
name: pagespeed
description: Run Google PageSpeed Insights / Lighthouse audit on any URL and generate a detailed markdown report. Use when the user wants to analyze site performance, Core Web Vitals, SEO, accessibility, or best practices scores.
allowed-tools: Bash, Read, Write, Glob, Grep, WebFetch
user-invocable: true
argument-prompt: "What URL would you like to audit? (e.g., https://example.com)"
---

# PageSpeed Insights / Lighthouse Audit Skill

Run a comprehensive Lighthouse audit on any URL and produce a structured markdown report.

## Prerequisites

- Google Chrome or Chromium installed
- `npx lighthouse` available (ships with npm)

## Instructions

When this skill is invoked:

### 1. Parse Arguments

The user provides a URL as the argument. If no URL is provided, ask for one.

Optionally the user may specify:
- `--mobile-only` or `--desktop-only` to run only one strategy
- `--output=<path>` to save the report to a specific path (default: `docs/pagespeed-report-YYYY-MM-DD.md` in the current project)

### 2. Detect Chrome

Find Chrome binary. Try in order:
1. `CHROME_PATH` env var
2. `which google-chrome`
3. `which chromium-browser`
4. `which chromium`

Set `CHROME_PATH` to the found binary for Lighthouse.

### 3. Run Lighthouse Audits

Run **both mobile and desktop** audits (unless user specified one):

```bash
# Mobile (default Lighthouse settings)
CHROME_PATH=<chrome> npx lighthouse <URL> \
  --output=json \
  --output-path=<scratchpad>/lh-mobile.json \
  --chrome-flags="--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage --disable-software-rasterizer" \
  --only-categories=performance,seo,accessibility,best-practices \
  2>&1 | tail -5

# Desktop (no throttling)
CHROME_PATH=<chrome> npx lighthouse <URL> \
  --output=json \
  --output-path=<scratchpad>/lh-desktop.json \
  --chrome-flags="--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage --disable-software-rasterizer" \
  --form-factor=desktop \
  --screenEmulation.disabled \
  --throttling.cpuSlowdownMultiplier=1 \
  --only-categories=performance,seo,accessibility,best-practices \
  2>&1 | tail -5
```

Use the scratchpad directory for temporary JSON files. Run mobile and desktop sequentially (Chrome can't share ports).

### 4. Parse Results

Use this Python script to extract data from the JSON reports:

```python
import json

def parse_lighthouse(path, label):
    with open(path) as f:
        data = json.load(f)

    result = {"label": label}

    # Category scores
    cats = data.get("categories", {})
    result["scores"] = {}
    for key, cat in cats.items():
        result["scores"][cat["title"]] = int((cat.get("score") or 0) * 100)

    # Lab metrics
    audits = data.get("audits", {})
    lab_keys = [
        "first-contentful-paint", "largest-contentful-paint",
        "total-blocking-time", "cumulative-layout-shift",
        "speed-index", "interactive", "server-response-time"
    ]
    result["lab"] = {}
    for m in lab_keys:
        if m in audits:
            a = audits[m]
            result["lab"][a["title"]] = {
                "value": a.get("displayValue", "N/A"),
                "score": a.get("score"),
                "numericValue": a.get("numericValue")
            }

    # Opportunities (failed audits with savings)
    result["opportunities"] = []
    for k, v in audits.items():
        details = v.get("details", {})
        if details.get("type") == "opportunity" and v.get("score") is not None and v.get("score") < 1:
            result["opportunities"].append({
                "title": v["title"],
                "displayValue": v.get("displayValue", ""),
                "savings_ms": details.get("overallSavingsMs", 0),
                "savings_bytes": details.get("overallSavingsBytes", 0),
                "score": v.get("score"),
                "description": v.get("description", "")
            })
    result["opportunities"].sort(key=lambda x: -x["savings_ms"])

    # Diagnostics (failed non-opportunity audits)
    result["diagnostics"] = []
    for k, v in audits.items():
        if v.get("score") is not None and v.get("score") < 1:
            details = v.get("details", {})
            if details.get("type") != "opportunity":
                group = v.get("group", "")
                if group in ("diagnostics", ""):
                    result["diagnostics"].append({
                        "title": v["title"],
                        "displayValue": v.get("displayValue", ""),
                        "score": v.get("score"),
                    })

    # Category-specific failures
    for cat_key in ["seo", "accessibility", "best-practices"]:
        cat_data = cats.get(cat_key, {})
        refs = [ref["id"] for ref in cat_data.get("auditRefs", []) if ref.get("weight", 0) > 0]
        issues = []
        for ref_id in refs:
            if ref_id in audits:
                a = audits[ref_id]
                if a.get("score") is not None and a.get("score") < 1:
                    issues.append({
                        "title": a["title"],
                        "displayValue": a.get("displayValue", ""),
                    })
        result[f"{cat_key}_issues"] = issues

    # Unused JS breakdown
    ujs = audits.get("unused-javascript", {})
    if ujs.get("details", {}).get("items"):
        result["unused_js"] = []
        for item in ujs["details"]["items"][:8]:
            result["unused_js"].append({
                "url": item.get("url", ""),
                "wastedBytes": item.get("wastedBytes", 0),
                "totalBytes": item.get("totalBytes", 0),
            })

    # JS execution time
    bt = audits.get("bootup-time", {})
    if bt.get("details", {}).get("items"):
        result["js_execution"] = []
        for item in bt["details"]["items"][:6]:
            result["js_execution"].append({
                "url": item.get("url", ""),
                "total": item.get("total", 0),
            })

    # Main thread breakdown
    mt = audits.get("mainthread-work-breakdown", {})
    if mt.get("details", {}).get("items"):
        result["main_thread"] = []
        for item in mt["details"]["items"][:8]:
            result["main_thread"].append({
                "group": item.get("groupLabel", item.get("group", "")),
                "duration": item.get("duration", 0),
            })

    # Passed/failed counts
    passed = sum(1 for v in audits.values() if v.get("score") == 1)
    failed = sum(1 for v in audits.values() if v.get("score") is not None and v.get("score") < 1)
    result["passed_audits"] = passed
    result["failed_audits"] = failed

    return result
```

### 5. Generate Markdown Report

Create a report with this structure:

```markdown
# PageSpeed Insights Report - <URL>

**Date:** <current date>
**Tool:** Lighthouse <version> (local run via Chrome <version>)
**URL tested:** <URL>

---

## Overall Scores

| Category         | Mobile | Desktop |
| ---------------- | ------ | ------- |
| Performance      | XX     | XX      |
| Accessibility    | XX     | XX      |
| Best Practices   | XX     | XX      |
| SEO              | XX     | XX      |

---

## Lab Data

| Metric                         | Mobile  | Desktop |
| ------------------------------ | ------- | ------- |
| First Contentful Paint (FCP)   | X.Xs    | X.Xs    |
| Largest Contentful Paint (LCP) | X.Xs    | X.Xs    |
| Total Blocking Time (TBT)      | Xms     | Xms     |
| Cumulative Layout Shift (CLS)  | X.XXX   | X.XXX   |
| Speed Index                    | X.Xs    | X.Xs    |
| Time to Interactive (TTI)      | X.Xs    | X.Xs    |
| Server Response Time (TTFB)    | Xms     | Xms     |

**Bold** any values that need improvement (score < 0.9).

---

## Performance Opportunities

For each opportunity, include:
- Title and estimated savings (ms and/or bytes)
- Brief description of the issue
- Specific recommendations
- If unused JS: include top offending scripts table

---

## Main Thread Work (Mobile)

Table of main thread categories and durations.

## Best Practices Issues

List each failed audit with source and recommendation.

## SEO Issues

List each failed audit with details and fix.

## Accessibility Issues

List each failed audit (or note "No issues found").

---

## Priority Action Items

### High Priority
Numbered list of most impactful fixes with brief explanation.

### Medium Priority
...

### Low Priority
...

---

## Summary

2-3 sentence overview of the site's performance posture and key takeaways.
```

### 6. Save and Report

- Save the markdown report to the output path
- Display a summary table of scores to the user
- List the top 3 action items
- Tell the user where the report was saved

## Error Handling

- If Chrome is not found: tell the user to install Chrome/Chromium
- If Lighthouse fails: show the error output and suggest `npx lighthouse --help`
- If the URL is unreachable: report the connection error
- If quota issues with PageSpeed API: this skill uses local Lighthouse, not the API, so this shouldn't happen

## Notes

- This skill runs Lighthouse locally, not via the Google PageSpeed API, so there are no quota limits
- Results may vary slightly between runs due to network conditions
- Mobile uses simulated throttling (Lighthouse default: slow 4G + 4x CPU slowdown)
- Desktop runs without throttling
- The JSON files in scratchpad are temporary and can be deleted after the report is generated
