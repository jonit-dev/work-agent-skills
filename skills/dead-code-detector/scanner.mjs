#!/usr/bin/env node

/**
 * Dead Code Detector Scanner
 *
 * Pure Node.js — no external dependencies (no ripgrep, no grep).
 * Detects orphaned files, dead exports, unreachable API endpoints,
 * stale dependencies, and unused environment variables.
 *
 * Usage:
 *   node scanner.mjs                    # Full scan
 *   node scanner.mjs --orphans          # Orphaned files only
 *   node scanner.mjs --exports          # Dead exports only
 *   node scanner.mjs --api              # Unreachable API endpoints
 *   node scanner.mjs --deps             # Stale dependencies
 *   node scanner.mjs --env              # Unused env vars
 *   node scanner.mjs --json             # Output as JSON
 *   node scanner.mjs --dir ./src        # Scope orphan scan to a directory
 */

import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, relative, basename, extname, dirname, resolve } from "node:path";

// ─── Config ───────────────────────────────────────────────────────────────────

const CODE_EXTENSIONS = new Set([
  ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".astro", ".svelte", ".vue",
]);

const IGNORE_DIRS = new Set([
  "node_modules", ".git", "dist", "build", ".next", ".astro", ".vercel",
  ".wrangler", "coverage", ".turbo", "__pycache__", ".cache", ".claude",
]);

// Files that are entry points or config — never flag as orphaned
const ENTRY_POINT_PATTERNS = [
  /^src\/pages\//,
  /^src\/content\//,
  /^src\/layouts\//,
  /^src\/middleware/,
  /^app\/.*\/page\./,
  /^app\/.*\/layout\./,
  /^app\/.*\/route\./,
  /^(astro|next|vite|nuxt|svelte)\.config\./,
  /^tailwind\.config\./,
  /^postcss\.config\./,
  /^tsconfig/,
  /^wrangler\./,
  /^playwright\./,
  /^vitest\./,
  /^jest\./,
  /\.config\.(ts|js|mjs|cjs)$/,
  /\.d\.ts$/,
  /^\.env/,
  /^(README|LICENSE|CHANGELOG)/i,
  /^package\.json$/,
  /^(\.eslint|\.prettier|\.babel)/,
  /\/env\.(ts|js)$/,
  /^tests?\//,
  /\.test\./,
  /\.spec\./,
  /\.e2e\./,
  /^scripts\//,
  /^migrations?\//,
  /^supabase\//,
  /^emails?\//,
  /^locales?\//,
  /^public\//,
  /^docs\//,
];

// Packages that are used by tooling/config, not via import statements
const CONFIG_ONLY_PACKAGES = new Set([
  "typescript", "eslint", "prettier", "@types/node", "@types/react",
  "@types/react-dom", "autoprefixer", "postcss", "tailwindcss",
  "@tailwindcss/typography", "@tailwindcss/forms", "@tailwindcss/aspect-ratio",
  "@tailwindcss/vite", "husky", "lint-staged", "concurrently", "cross-env",
  "dotenv", "nodemon", "ts-node", "tsx", "wrangler",
  "@cloudflare/workers-types", "rimraf", "del-cli", "npm-run-all",
  "wait-on", "start-server-and-test",
]);

// API paths called by external systems, not client code
const EXTERNAL_API_PATTERNS = [
  /webhooks?/i, /health/i, /cron/i, /callback/i, /oauth/i,
  /\.well-known/i, /sitemap/i, /robots/i, /feed/i, /rss/i,
];

// ─── File System Helpers ──────────────────────────────────────────────────────

function getAllCodeFiles(dir, base = dir) {
  const results = [];
  if (!existsSync(dir)) return results;

  for (const entry of readdirSync(dir)) {
    if (IGNORE_DIRS.has(entry) || entry.startsWith(".")) continue;
    const full = join(dir, entry);
    let stat;
    try { stat = statSync(full); } catch { continue; }
    if (stat.isDirectory()) {
      results.push(...getAllCodeFiles(full, base));
    } else if (CODE_EXTENSIONS.has(extname(entry))) {
      results.push(relative(base, full));
    }
  }
  return results;
}

function readFileSafe(filePath) {
  try {
    return readFileSync(filePath, "utf-8");
  } catch {
    return null;
  }
}

function readJSON(filePath) {
  const raw = readFileSafe(filePath);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

/**
 * Loads all source file contents into memory for fast searching.
 * Returns Map<relativePath, fileContent>
 */
function loadAllSources(projectDir) {
  const files = getAllCodeFiles(projectDir, projectDir);
  const sources = new Map();
  for (const f of files) {
    const content = readFileSafe(join(projectDir, f));
    if (content !== null) sources.set(f, content);
  }
  // Also load config files at root
  const rootConfigs = readdirSync(projectDir).filter(
    (e) => /\.(json|toml|yaml|yml)$/.test(e) && !e.includes("lock"),
  );
  for (const c of rootConfigs) {
    const content = readFileSafe(join(projectDir, c));
    if (content !== null) sources.set(c, content);
  }
  return sources;
}

function isEntryPoint(relPath) {
  return ENTRY_POINT_PATTERNS.some((p) => p.test(relPath));
}

function fileToApiPath(filePath) {
  return filePath
    .replace(/^src\/pages/, "")
    .replace(/^app/, "")
    .replace(/\/route\.(ts|js)$/, "")
    .replace(/\/index\.(ts|js)$/, "")
    .replace(/\.(ts|tsx|js|jsx)$/, "")
    .replace(/\[\.{3}(\w+)\]/g, "*$1")
    .replace(/\[(\w+)\]/g, ":$1");
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// ─── Scanners ─────────────────────────────────────────────────────────────────

function scanOrphanedFiles(projectDir, sources, targetDir) {
  const allFiles = targetDir
    ? getAllCodeFiles(resolve(projectDir, targetDir), projectDir)
    : [...sources.keys()].filter((f) => CODE_EXTENSIONS.has(extname(f)));

  const orphans = [];

  for (const file of allFiles) {
    if (isEntryPoint(file)) continue;

    const fileBase = basename(file, extname(file));
    const dirName = basename(dirname(file));

    // Build search terms: the base name, and for index files the parent dir name
    const searchTerms = [fileBase];
    if (fileBase === "index") searchTerms.push(dirName);

    // Also build path fragments for alias imports like @server/foo/bar
    const pathNoExt = file.replace(extname(file), "");
    const pathFragments = pathNoExt.split("/");
    // Last 2 segments: e.g. "services/articleService"
    if (pathFragments.length >= 2) {
      searchTerms.push(pathFragments.slice(-2).join("/"));
    }

    let found = false;

    for (const [otherFile, content] of sources) {
      if (otherFile === file) continue;

      for (const term of searchTerms) {
        // Check import/require/from statements
        // Patterns: from 'xxx/term', import('xxx/term'), require('xxx/term')
        if (
          content.includes(`/${term}'`) ||
          content.includes(`/${term}"`) ||
          content.includes(`/${term}\``) ||
          content.includes(`'${term}'`) ||
          content.includes(`"${term}"`)
        ) {
          found = true;
          break;
        }
      }

      // For React components: check JSX usage <ComponentName
      if (!found && (file.endsWith(".tsx") || file.endsWith(".jsx"))) {
        const componentName = fileBase.charAt(0).toUpperCase() + fileBase.slice(1);
        if (content.includes(`<${componentName}`) || content.includes(`<${componentName} `)) {
          found = true;
        }
      }

      if (found) break;
    }

    if (!found) {
      orphans.push({
        file,
        severity: "CRITICAL",
        category: "orphaned-file",
        reason: "No imports or references found in any source file",
      });
    }
  }

  return orphans;
}

function scanDeadExports(projectDir, sources) {
  const findings = [];
  const exportRegex = /^export\s+(?:const|function|class|type|interface|enum|let|var|async\s+function)\s+(\w+)/gm;

  for (const [file, content] of sources) {
    // Skip test files, config files, type declarations
    if (/\.(test|spec|e2e)\./i.test(file)) continue;
    if (/\.config\./i.test(file)) continue;
    if (/\.d\.ts$/.test(file)) continue;
    if (/^tests?\//i.test(file)) continue;
    if (!CODE_EXTENSIONS.has(extname(file))) continue;

    let match;
    exportRegex.lastIndex = 0;
    while ((match = exportRegex.exec(content)) !== null) {
      const exportName = match[1];

      // Skip HTTP method exports (GET, POST, etc.) and Astro special exports
      if (/^(default|GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|ALL|prerender|partial)$/.test(exportName)) continue;

      // Skip very short generic names that would produce too many false positives
      if (exportName.length <= 1) continue;

      // Search all other files for usage of this export name
      let usedElsewhere = false;
      for (const [otherFile, otherContent] of sources) {
        if (otherFile === file) continue;
        if (/\.(test|spec|e2e)\./i.test(otherFile)) continue;

        // Check if the name appears in context that suggests import/usage
        // We use word boundary-like checks
        const idx = otherContent.indexOf(exportName);
        if (idx !== -1) {
          // Verify it's a word boundary (not part of a larger identifier)
          const charBefore = idx > 0 ? otherContent[idx - 1] : " ";
          const charAfter = otherContent[idx + exportName.length] || " ";
          if (!/\w/.test(charBefore) && !/\w/.test(charAfter)) {
            usedElsewhere = true;
            break;
          }
        }
      }

      if (!usedElsewhere) {
        findings.push({
          file,
          export: exportName,
          severity: "HIGH",
          category: "dead-export",
          reason: `Exported '${exportName}' is not imported by any non-test file`,
        });
      }
    }
  }

  return findings;
}

function scanUnreachableAPI(projectDir, sources) {
  const findings = [];

  // Find API route files
  const apiFiles = [...sources.keys()].filter(
    (f) => f.startsWith("src/pages/api/") || f.startsWith("app/api/") || f.startsWith("pages/api/"),
  );

  for (const file of apiFiles) {
    const apiPath = fileToApiPath(file);

    // Skip known external-facing endpoints
    if (EXTERNAL_API_PATTERNS.some((p) => p.test(apiPath))) continue;

    // Build path variants to search for
    const pathVariants = new Set([apiPath]);
    // Remove parameter placeholders for matching: /api/projects/:id -> /api/projects/
    pathVariants.add(apiPath.replace(/\/:[^/]+/g, "/"));
    // Last two segments: e.g. "projects/:id"
    const segments = apiPath.split("/").filter(Boolean);
    if (segments.length >= 2) {
      pathVariants.add(segments.slice(-2).join("/"));
      pathVariants.add(segments.slice(-1)[0]);
    }

    let found = false;

    for (const [otherFile, content] of sources) {
      // Skip the API route file itself and other API route files
      if (otherFile === file) continue;
      if (
        otherFile.startsWith("src/pages/api/") ||
        otherFile.startsWith("app/api/") ||
        otherFile.startsWith("pages/api/")
      ) continue;

      for (const variant of pathVariants) {
        if (!variant || variant.length < 4) continue;
        if (content.includes(variant)) {
          found = true;
          break;
        }
      }
      if (found) break;
    }

    if (!found) {
      findings.push({
        file,
        endpoint: apiPath,
        severity: "HIGH",
        category: "unreachable-api",
        reason: `No client code references '${apiPath}'`,
      });
    }
  }

  return findings;
}

function scanStaleDeps(projectDir, sources) {
  const findings = [];
  const pkg = readJSON(join(projectDir, "package.json"));
  if (!pkg) return findings;

  const allDeps = { ...pkg.dependencies, ...pkg.devDependencies };
  const scripts = pkg.scripts ? Object.values(pkg.scripts).join(" ") : "";

  // Combine all source content for searching (faster than iterating per-dep)
  const allContent = [...sources.values()].join("\n");

  for (const [dep, version] of Object.entries(allDeps)) {
    if (CONFIG_ONLY_PACKAGES.has(dep)) continue;

    // Check for import/require of this package
    // Patterns: from 'pkg', from 'pkg/', require('pkg'), require('pkg/')
    const inSources =
      allContent.includes(`'${dep}'`) ||
      allContent.includes(`"${dep}"`) ||
      allContent.includes(`'${dep}/`) ||
      allContent.includes(`"${dep}/`);

    if (inSources) continue;

    // Check scripts in package.json
    const depBin = dep.replace(/^@.*\//, ""); // @scope/pkg -> pkg
    if (scripts.includes(depBin)) continue;

    // Check @types packages — verify the base package is used
    if (dep.startsWith("@types/")) {
      const basePkg = dep.replace("@types/", "").replace("__", "/");
      if (allDeps[basePkg] || allDeps[`@${basePkg}`]) continue;

      // Also check if the package name appears as a scoped package
      const asScoped = `@${basePkg.replace("__", "/")}`;
      if (allDeps[asScoped]) continue;

      // Check if base package name is imported anywhere
      if (allContent.includes(`'${basePkg}'`) || allContent.includes(`"${basePkg}"`)) continue;
    }

    // Check if referenced in any config file
    let inConfig = false;
    for (const [f, content] of sources) {
      if (/\.config\.(ts|js|mjs|cjs)$/.test(f) || f === "package.json") {
        if (content.includes(dep)) {
          inConfig = true;
          break;
        }
      }
    }
    if (inConfig) continue;

    findings.push({
      package: dep,
      version,
      severity: "MEDIUM",
      category: "stale-dependency",
      reason: `No imports of '${dep}' found in source code`,
    });
  }

  return findings;
}

function scanUnusedEnv(projectDir, sources) {
  const findings = [];

  // Collect all env files
  const envFiles = [];
  try {
    for (const e of readdirSync(projectDir)) {
      if (e.startsWith(".env") && !e.includes(".example") && !e.includes(".local")) {
        envFiles.push(e);
      }
    }
  } catch {
    return findings;
  }

  const allKeys = new Map(); // key -> source file

  for (const envFile of envFiles) {
    const content = readFileSafe(join(projectDir, envFile));
    if (!content) continue;

    for (const line of content.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const match = trimmed.match(/^([A-Z_][A-Z0-9_]*)\s*=/);
      if (match) allKeys.set(match[1], envFile);
    }
  }

  // Combine all source content for searching
  const allContent = [...sources.values()].join("\n");

  for (const [key, source] of allKeys) {
    // Check common access patterns
    const found =
      allContent.includes(`process.env.${key}`) ||
      allContent.includes(`process.env["${key}"]`) ||
      allContent.includes(`process.env['${key}']`) ||
      allContent.includes(`import.meta.env.${key}`) ||
      allContent.includes(`clientEnv.${key}`) ||
      allContent.includes(`serverEnv.${key}`) ||
      allContent.includes(`env.${key}`) ||
      // Also check for the key in config/toml/yaml references
      allContent.includes(`"${key}"`) ||
      allContent.includes(`'${key}'`);

    if (!found) {
      findings.push({
        key,
        source,
        severity: "MEDIUM",
        category: "unused-env",
        reason: `'${key}' defined in ${source} but not referenced in code`,
      });
    }
  }

  return findings;
}

// ─── Output ───────────────────────────────────────────────────────────────────

function printFindings(findings, asJSON) {
  if (asJSON) {
    console.log(JSON.stringify(findings, null, 2));
    return;
  }

  if (findings.length === 0) {
    console.log("\n  No dead code found. Codebase is clean!\n");
    return;
  }

  const grouped = {};
  for (const f of findings) {
    if (!grouped[f.category]) grouped[f.category] = [];
    grouped[f.category].push(f);
  }

  const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const categoryLabels = {
    "orphaned-file": "Orphaned Files (zero imports)",
    "dead-export": "Dead Exports (never imported)",
    "unreachable-api": "Unreachable API Endpoints",
    "stale-dependency": "Stale Dependencies",
    "unused-env": "Unused Environment Variables",
  };

  const sortedCategories = Object.keys(grouped).sort(
    (a, b) =>
      (severityOrder[grouped[a][0]?.severity] ?? 99) -
      (severityOrder[grouped[b][0]?.severity] ?? 99),
  );

  console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("  DEAD CODE REPORT");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  const counts = {};
  for (const f of findings) counts[f.severity] = (counts[f.severity] || 0) + 1;
  console.log(
    `  Total: ${findings.length} findings —`,
    Object.entries(counts).map(([s, c]) => `${c} ${s}`).join(", "),
  );
  console.log();

  for (const cat of sortedCategories) {
    const items = grouped[cat];
    console.log(`  ── ${categoryLabels[cat] || cat} (${items.length}) ──\n`);

    for (const item of items) {
      const icon =
        item.severity === "CRITICAL" ? "[!!]" :
        item.severity === "HIGH" ? "[! ]" : "[-  ]";
      const main = item.file || item.endpoint || item.package || item.key || "unknown";
      const detail = item.export ? ` -> ${item.export}` : item.version ? ` (${item.version})` : "";
      console.log(`    ${icon} ${main}${detail}`);
      console.log(`        ${item.reason}`);
    }
    console.log();
  }

  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  const flags = new Set(args.filter((a) => a.startsWith("--")));
  const asJSON = flags.has("--json");
  const targetDir = flags.has("--dir") ? args[args.indexOf("--dir") + 1] : null;

  const projectDir = process.cwd();

  const runAll =
    !flags.has("--orphans") &&
    !flags.has("--exports") &&
    !flags.has("--api") &&
    !flags.has("--deps") &&
    !flags.has("--env");

  if (!asJSON) console.log("\n  Loading source files...");
  const sources = loadAllSources(projectDir);
  if (!asJSON) console.log(`  Loaded ${sources.size} files\n`);

  let findings = [];

  if (runAll || flags.has("--orphans")) {
    if (!asJSON) process.stdout.write("  [1/5] Scanning orphaned files...");
    const results = scanOrphanedFiles(projectDir, sources, targetDir);
    findings.push(...results);
    if (!asJSON) console.log(` found ${results.length}`);
  }

  if (runAll || flags.has("--exports")) {
    if (!asJSON) process.stdout.write("  [2/5] Scanning dead exports...");
    const results = scanDeadExports(projectDir, sources);
    findings.push(...results);
    if (!asJSON) console.log(` found ${results.length}`);
  }

  if (runAll || flags.has("--api")) {
    if (!asJSON) process.stdout.write("  [3/5] Scanning unreachable APIs...");
    const results = scanUnreachableAPI(projectDir, sources);
    findings.push(...results);
    if (!asJSON) console.log(` found ${results.length}`);
  }

  if (runAll || flags.has("--deps")) {
    if (!asJSON) process.stdout.write("  [4/5] Scanning stale dependencies...");
    const results = scanStaleDeps(projectDir, sources);
    findings.push(...results);
    if (!asJSON) console.log(` found ${results.length}`);
  }

  if (runAll || flags.has("--env")) {
    if (!asJSON) process.stdout.write("  [5/5] Scanning unused env variables...");
    const results = scanUnusedEnv(projectDir, sources);
    findings.push(...results);
    if (!asJSON) console.log(` found ${results.length}`);
  }

  printFindings(findings, asJSON);

  const hasSerious = findings.some((f) => f.severity === "CRITICAL" || f.severity === "HIGH");
  process.exit(hasSerious ? 1 : 0);
}

main();
