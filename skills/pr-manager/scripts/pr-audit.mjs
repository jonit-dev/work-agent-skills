#!/usr/bin/env node
/**
 * Title and shape drift across the open pull requests.
 *
 * Everything here is a fact about the PR as a reviewer meets it — its title and the first
 * screen of its body. Nothing here judges the code.
 *
 * Usage: node pr-audit.mjs [--limit <n>] [--stale <days>] [--json] [--repo <owner/name>]
 */
import { execFileSync } from "node:child_process";

const CONVENTIONAL = /^(?:feat|fix|docs|refactor|perf|test|chore|build|ci|style|revert)(?:\([^)]+\))?!?:\s+\S/u;
const PRD_ID = /\bPRD-[A-Za-z0-9.]*\d[A-Za-z0-9.-]*/giu;
const PHASE_SUFFIX = /\bphase\s*\d|\bpart\s*\d|\b\d\s*\/\s*\d\s*$|\bstep\s*\d/iu;
const TLDR = /\b(?:TL;?DR|TLDR|Summary|What this (?:adds|changes|does))\b/iu;
const STILL_OPEN = /\b(?:still open|not done|remaining|outstanding|todo|what'?s missing|left to do)\b/iu;
const TITLE_LIMIT = 72;

function parseArgs(argv) {
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    const next = argv[i + 1];
    if (next !== undefined && !next.startsWith("--")) {
      flags[argv[i].slice(2)] = next;
      i += 1;
    } else flags[argv[i].slice(2)] = true;
  }
  return flags;
}

function openPrs(limit, repo) {
  const args = [
    "pr",
    "list",
    "--state",
    "open",
    "--limit",
    String(limit),
    "--json",
    "number,title,body,isDraft,updatedAt,headRefName,labels,url",
  ];
  if (typeof repo === "string") args.push("--repo", repo);
  try {
    return JSON.parse(execFileSync("gh", args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }));
  } catch (error) {
    process.stderr.write(
      `gh could not list pull requests: ${String(error.stderr ?? error.message).trim()}\n` +
        "Run inside a repository with a GitHub remote, or pass --repo owner/name.\n",
    );
    process.exit(1);
  }
}

function idsIn(text) {
  return [...new Set((text.match(PRD_ID) ?? []).map((id) => id.toUpperCase().replace(/[-.]+$/u, "")))];
}

function main() {
  const flags = parseArgs(process.argv.slice(2));
  const staleDays = flags.stale === undefined ? 14 : Number(flags.stale);
  const prs = openPrs(flags.limit === undefined ? 200 : Number(flags.limit), flags.repo);
  const now = Date.now();

  const findings = [];
  const add = (title, fix, items) => {
    if (items.length > 0) findings.push({ fix, items, title });
  };
  const label = (pr) => `#${pr.number} ${pr.title}`;

  add(
    "Title has no conventional-commit type",
    "<type>(<scope>): <imperative summary> — feat, fix, docs, refactor, perf, test, chore, build, ci",
    prs.filter((pr) => !CONVENTIONAL.test(pr.title)).map(label),
  );

  add(
    "Title carries a phase or part number",
    "one PR per PRD — fold the phases into the PRD's single PR",
    prs.filter((pr) => PHASE_SUFFIX.test(pr.title)).map(label),
  );

  add(
    `Title longer than ${TITLE_LIMIT} characters`,
    "say the outcome, not the activity; an explainer after a colon is a second title",
    prs.filter((pr) => pr.title.length > TITLE_LIMIT).map((pr) => `${label(pr)}  (${pr.title.length})`),
  );

  add(
    "PRD named in the branch or body but not the title",
    "put the PRD id in the title — it is how a reviewer finds the plan",
    prs
      .filter((pr) => {
        const inTitle = idsIn(pr.title).length > 0;
        const elsewhere = idsIn(`${pr.headRefName} ${pr.body ?? ""}`).length > 0;
        return !inTitle && elsewhere;
      })
      .map(label),
  );

  const byPrd = new Map();
  for (const pr of prs) {
    for (const id of idsIn(`${pr.title} ${pr.headRefName}`)) {
      byPrd.set(id, [...(byPrd.get(id) ?? []), pr.number]);
    }
  }
  add(
    "More than one open PR names the same PRD",
    "phase-sized PRs split the evidence — close the extras into the first",
    [...byPrd.entries()]
      .filter(([, numbers]) => numbers.length > 1)
      .map(([id, numbers]) => `${id}: ${numbers.map((n) => `#${n}`).join(", ")}`),
  );

  add(
    "Body has no TL;DR or summary up top",
    "open with one sentence: what this changes and why it matters",
    prs.filter((pr) => (pr.body ?? "").trim() !== "" && !TLDR.test((pr.body ?? "").slice(0, 600))).map(label),
  );

  add(
    "Body is empty or near-empty",
    "a reviewer cannot review what the PR does not say",
    prs.filter((pr) => (pr.body ?? "").trim().length < 80).map(label),
  );

  add(
    "Body never says what is still open",
    "list what is not done — otherwise the PR reads finished when it is not",
    prs
      .filter((pr) => (pr.body ?? "").trim().length >= 80 && !STILL_OPEN.test(pr.body ?? "") && !/- \[ \]/u.test(pr.body ?? ""))
      .map(label),
  );

  add(
    "No PRD progress label",
    "node ~/.claude/skills/prd-manager/scripts/prd-pr.mjs <prd file> --yes",
    prs
      .filter((pr) => idsIn(`${pr.title} ${pr.headRefName}`).length > 0)
      .filter((pr) => !(pr.labels ?? []).some((entry) => entry.name.startsWith("prd:")))
      .map(label),
  );

  add(
    `Draft untouched for ${staleDays}+ days`,
    "push, or close it — a stale draft is a claim nobody is maintaining",
    prs
      .filter((pr) => pr.isDraft && (now - Date.parse(pr.updatedAt)) / 86400000 >= staleDays)
      .map((pr) => `${label(pr)}  (${Math.floor((now - Date.parse(pr.updatedAt)) / 86400000)}d)`),
  );

  if (flags.json === true) {
    process.stdout.write(`${JSON.stringify(findings, null, 2)}\n`);
    return;
  }
  if (findings.length === 0) {
    process.stdout.write(`${prs.length} open PRs, no title or shape drift.\n`);
    return;
  }
  for (const finding of findings) {
    process.stdout.write(`\n${finding.title}  [${finding.items.length}]\n  fix: ${finding.fix}\n`);
    for (const item of finding.items.slice(0, 15)) process.stdout.write(`  - ${item}\n`);
    if (finding.items.length > 15) process.stdout.write(`  … ${finding.items.length - 15} more\n`);
  }
  const total = findings.reduce((sum, finding) => sum + finding.items.length, 0);
  process.stdout.write(`\n${total} items across ${findings.length} categories, over ${prs.length} open PRs.\n`);
}

main();
