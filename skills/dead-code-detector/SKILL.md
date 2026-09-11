---
name: dead-code-detector
description: Detect and report unused code, unlinked systems, orphaned files, unreachable API endpoints, dead exports, and disconnected components. Use when auditing codebase health, before major releases, or when the codebase feels bloated.
---

# Dead Code Detector

Systematic detection of unused code, orphaned files, unlinked systems, and disconnected components. The goal is to ensure everything in the codebase is properly hooked up, referenced, and tight.

## When to Use

- Codebase health audits
- Pre-release cleanup
- After large refactors or feature removals
- When the codebase feels bloated or navigation is confusing
- When you suspect API endpoints, components, or utilities are no longer used

## Detection Categories

Run each category in order. For each finding, classify severity:

| Severity | Meaning |
|----------|---------|
| **CRITICAL** | Entire files/modules with zero imports or references anywhere |
| **HIGH** | Exported functions/types/constants never imported elsewhere |
| **MEDIUM** | Code paths that are technically reachable but never actually called |
| **LOW** | Commented-out code blocks, TODO-gated dead branches, unused variables |

---

### 1. Orphaned Files (no imports anywhere)

Files that exist but are never imported, required, or referenced by any other file.

**Strategy:**
```bash
# Run the scanner script for comprehensive detection
node ~/.Codex/skills/dead-code-detector/scanner.mjs --orphans
```

**Manual approach:**
- For each file in `src/`, check if any other file imports it
- Pay special attention to:
  - `src/components/` - React components not used in any page/layout
  - `src/pages/api/` - API routes not called by any client code
  - `server/services/` - Services not imported by any route handler
  - `shared/` - Shared utilities/types not used by server or client
  - `src/hooks/` - Custom hooks not used in any component

```bash
# Example: Find if a file is imported anywhere
rg "from.*['\"].*filename" --type ts --type tsx -l
rg "import.*filename" --type ts --type tsx -l
rg "require.*filename" --type ts --type tsx -l
```

### 2. Dead Exports (exported but never imported)

Functions, classes, types, constants, or variables that are exported but never imported by any other module.

**Strategy:**
```bash
node ~/.Codex/skills/dead-code-detector/scanner.mjs --exports
```

**Manual approach:**
- Extract all named exports from each file
- Search the entire codebase for imports of each export name
- Exclude: barrel files (index.ts re-exports), test files importing test subjects, entry points

### 3. Unreachable API Endpoints

API routes that exist but are never called from client code, webhook configs, or external services.

**Strategy:**
```bash
node ~/.Codex/skills/dead-code-detector/scanner.mjs --api
```

**Manual approach:**
- List all files in `src/pages/api/` (or `app/api/` for Next.js App Router)
- Derive the URL path from the file path
- Search client code for fetch/axios/api calls to that path
- Check webhook configurations and external service integrations
- Check route registrations in middleware or config files

**Important exceptions** (do NOT flag these as dead):
- Webhook endpoints (`/api/webhooks/*`) - called by external services
- Health check endpoints (`/api/health`)
- Cron/scheduled endpoints - called by infrastructure
- OAuth callback endpoints - called by auth providers

### 4. Unused React Components

Components defined but never rendered anywhere.

**Strategy:**
- Search for `<ComponentName` or `ComponentName(` across all TSX/JSX files
- Check for dynamic imports: `lazy(() => import(...))`
- Check Astro files for `client:*` island usage
- Check Storybook stories (component may only be used there)

### 5. Dead Database Tables/Columns

Tables or columns defined in migrations but never queried.

**Strategy:**
- Extract table/column names from migration files and schema definitions
- Search all server code for references to those names
- Check Supabase RPC functions and policies
- Check for ORM model definitions that reference them

### 6. Unused Environment Variables

Env vars defined in `.env*` files but never read by code.

**Strategy:**
```bash
node ~/.Codex/skills/dead-code-detector/scanner.mjs --env
```

**Manual approach:**
- Extract all keys from `.env`, `.env.*` files
- Search codebase for `process.env.KEY`, `clientEnv.KEY`, `serverEnv.KEY`, `import.meta.env.KEY`
- Check wrangler.toml, docker-compose, CI configs

### 7. Orphaned CSS/Styles

CSS classes, Tailwind utilities defined in custom CSS but never used in templates.

**Strategy:**
- Extract custom class names from global CSS files
- Search all template/component files for those class names
- For Tailwind: check `safelist` in tailwind config for intentional preservation

### 8. Stale Dependencies

npm packages in `dependencies`/`devDependencies` that are never imported.

**Strategy:**
```bash
node ~/.Codex/skills/dead-code-detector/scanner.mjs --deps
```

**Manual approach:**
- For each package in package.json dependencies
- Search for `import ... from 'package'` or `require('package')`
- Check config files that reference packages (babel, postcss, eslint, etc.)
- Check CLI scripts in package.json scripts

### 9. Dead Routes/Pages

Page files that exist but are not linked from navigation, sitemaps, or any other page.

**Strategy:**
- List all page files in `src/pages/`
- Check navigation components, sitemaps, link elements for references
- Check redirects configuration
- Verify pages are accessible (not blocked by middleware)

### 10. Disconnected Event Handlers/Listeners

Event listeners, webhook handlers, or pub/sub subscribers that are registered but their triggering events are never emitted.

**Strategy:**
- Find all event listener registrations
- Find all event emission/dispatch points
- Cross-reference: every listener should have at least one emitter

---

## Running the Scanner

The scanner script provides automated detection for common patterns:

```bash
# Full scan (all categories)
node ~/.Codex/skills/dead-code-detector/scanner.mjs

# Specific categories
node ~/.Codex/skills/dead-code-detector/scanner.mjs --orphans    # Orphaned files
node ~/.Codex/skills/dead-code-detector/scanner.mjs --exports    # Dead exports
node ~/.Codex/skills/dead-code-detector/scanner.mjs --api        # Unreachable API endpoints
node ~/.Codex/skills/dead-code-detector/scanner.mjs --deps       # Stale dependencies
node ~/.Codex/skills/dead-code-detector/scanner.mjs --env        # Unused env vars

# Output as JSON for further processing
node ~/.Codex/skills/dead-code-detector/scanner.mjs --json

# Scan a specific directory
node ~/.Codex/skills/dead-code-detector/scanner.mjs --dir ./src/components
```

## Report Format

Present findings in this structure:

```markdown
# Dead Code Report

**Scanned:** <date>
**Project:** <project name>
**Total findings:** X (Y critical, Z high, W medium, V low)

## Critical: Orphaned Files
| File | Last Modified | Reason |
|------|--------------|--------|
| `src/components/OldWidget.tsx` | 2024-03-15 | Zero imports found |

## High: Dead Exports
| File | Export | Type |
|------|--------|------|
| `shared/utils/helpers.ts` | `formatLegacyDate` | function |

## High: Unreachable API Endpoints
| Endpoint | File | Reason |
|----------|------|--------|
| `POST /api/legacy/sync` | `src/pages/api/legacy/sync.ts` | No client calls found |

## Medium: Stale Dependencies
| Package | Version | Reason |
|---------|---------|--------|
| `lodash` | ^4.17.0 | No imports found |

## Recommended Actions
1. **Delete** orphaned files (after git blame review)
2. **Remove** dead exports (update barrel files)
3. **Archive or delete** unreachable endpoints
4. **Uninstall** stale dependencies
```

## Safety Checklist

Before recommending deletion, verify:

- [ ] File is not dynamically imported (`import()` with variable paths)
- [ ] File is not referenced in build configs (webpack, vite, astro, etc.)
- [ ] Export is not used via re-export chains (barrel files)
- [ ] API endpoint is not called by external services, cron jobs, or webhooks
- [ ] Dependency is not used by build tools, config files, or CLI scripts
- [ ] Code is not behind a feature flag that's currently disabled
- [ ] Check `git log` to understand why the code was added (may be intentionally preserved)

## Integration with Other Skills

- After finding dead code, use `/dry-refactoring` if remaining code has duplication
- After cleanup, use `/context-building` to verify the system still works as expected
- Run tests after any deletions to catch broken references
