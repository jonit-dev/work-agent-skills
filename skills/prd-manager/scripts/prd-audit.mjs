#!/usr/bin/env node
/**
 * Drift and bloat report. Everything here is a fact about the files, never a judgement:
 * the audit says what is inconsistent, a human or an agent decides what to do about it.
 *
 * Usage: node prd-audit.mjs [--older <days>] [--evidence <dir>] [--all] [--json]
 *                           [--strict] [--root <dir>]
 */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { basename, join, relative, resolve } from "node:path";
import { findPrdRoot, loadPrds, parseArgs, savingsLine, truncate } from "./prd-lib.mjs";

const DONE_WORDS = /\b(?:DONE|COMPLETE|COMPLETED|SHIPPED|LANDED|CLOSED)\b/u;
const OPEN_WORDS = /\b(?:PARTIAL|NOT STARTED|PROPOSED|OPEN|SCOPING|IN PROGRESS|BLOCKED|DRAFT)\b/u;
/** The `proof:` marker R1 asks every countable box to carry. */
const PROOF = /\bproof:/iu;
/** Process theatre: things nobody can fail, so nobody can finish them either. */
const CEREMONY =
  /revert(?:ed|ing)?\s+(?:the\s+\w+\s+)?check|revert the change|re-?apply the (?:commit|change)|independent (?:review|reviewer|pass)|second (?:review|reviewer|eyes)|evidence (?:record|file|report|ledger|document)|negative control|artificial (?:negative|failure)|caller census/iu;
/** R5's size cap: at most 3 phases, about 8 boxes. */
const MAX_PHASES = 3;
const MAX_BOXES = 8;

const EVIDENCE_DIRS = ["docs/verification", "docs/evidence", "verification", "evidence"];

function findEvidenceDir(repoRoot, flag) {
  if (typeof flag === "string") return resolve(flag);
  for (const candidate of EVIDENCE_DIRS) {
    const full = join(repoRoot, candidate);
    if (existsSync(full) && statSync(full).isDirectory()) return full;
  }
  return undefined;
}

function listMarkdown(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".")) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) listMarkdown(full, out);
    else if (entry.name.endsWith(".md")) out.push(full);
  }
  return out;
}

/**
 * Every `*.md` filename mentioned anywhere in the repo except the evidence directory
 * itself — one `git grep` rather than one per candidate file.
 */
function referencedNames(repoRoot, evidenceDir) {
  const exclude = `:(exclude)${relative(repoRoot, evidenceDir)}`;
  try {
    const raw = execFileSync(
      "git",
      ["grep", "-hoIE", "[A-Za-z0-9._/-]+\\.md", "--", ".", exclude],
      { cwd: repoRoot, encoding: "utf8", maxBuffer: 128 * 1024 * 1024, stdio: ["ignore", "pipe", "ignore"] },
    );
    return new Set(raw.split("\n").map((line) => basename(line.trim())));
  } catch {
    return undefined;
  }
}

/**
 * Every countable box as one string: the box line plus its indented continuation, so a
 * `proof:` written on the next line still counts. `## Blocked on` and `## Decisions` are
 * not work, so their lines are never judged.
 */
function countableBoxes(markdown) {
  const out = [];
  let note = false;
  let last = -1;
  for (const line of markdown.split("\n")) {
    if (/^#{2,4}\s/u.test(line)) {
      note = NOT_A_BOX_HEADING.test(line);
      last = -1;
    } else if (note) continue;
    else if (BOX.test(line)) {
      out.push(line.trim());
      last = out.length - 1;
    } else if (last !== -1 && /^\s{2,}\S/u.test(line)) out[last] += ` ${line.trim()}`;
  }
  return out;
}

const BOX = /^\s*[-*]\s+\[[ xX]\]/u;
const NOT_A_BOX_HEADING = /^#{2,4}\s+(?:Blocked on|Blocked|Decisions)\b/iu;
const COMPOUND_ONE = /\[ \][^\n]*\band\b[^\n]*\band\b/u;

/** One read per open PRD, three verdicts off the same boxes. */
function boxFindings(p) {
  const out = { ceremony: 0, compound: 0, noProof: 0 };
  for (const box of countableBoxes(readFileSync(p.file, "utf8"))) {
    if (PROOF.test(box) === false) out.noProof += 1;
    if (COMPOUND_ONE.test(box)) out.compound += 1;
    if (CEREMONY.test(box)) out.ceremony += 1;
  }
  return out;
}

function main() {
  const { flags } = parseArgs(process.argv.slice(2));
  const root = flags.root === undefined ? findPrdRoot() : flags.root;
  const prds = loadPrds(root);
  const repoRoot = prds[0]?.repoRoot ?? root;
  const olderThan = flags.older === undefined ? 30 : Number(flags.older);
  const cap = flags.all === true ? Number.POSITIVE_INFINITY : 10;

  const findings = [];
  const add = (key, title, fix, items) => {
    if (items.length > 0) findings.push({ fix, items, key, title });
  };

  const open = prds.filter((p) => !p.done);

  add(
    "ready-not-filed",
    "Finished but still open — every phase and acceptance box ticked",
    "prd-close.mjs <file> --yes",
    prds.filter((p) => !p.done && p.percent === 100 && !p.blockedOnly).map((p) => p.rel),
  );

  add(
    "blocked-only-not-filed",
    "Only `## Blocked on` items are left, but the file still reads as live work",
    "prd-close.mjs <file> --blocked <reason> — names what unblocks it, then fix the links",
    prds
      .filter((p) => p.blockedOnly && !p.blocked)
      .map((p) => `${p.rel}  (${p.blockedOn} blocked item${p.blockedOn === 1 ? "" : "s"})`),
  );

  const boxes = new Map(open.map((p) => [p.rel, boxFindings(p)]));

  add(
    "ceremony-box",
    "Ceremony boxes — an observed ritual nobody can fail, so nobody can finish it",
    "delete the box; the ritual belongs in the PR body or the PR template",
    open
      .filter((p) => boxes.get(p.rel).ceremony > 0)
      .map((p) => `${p.rel}  (${boxes.get(p.rel).ceremony})`),
  );

  add(
    "over-size-cap",
    `Over the size cap — more than ${MAX_PHASES} phases or about ${MAX_BOXES} boxes`,
    "split it into separate PRDs, each citing this one",
    open
      .filter((p) => p.phases > MAX_PHASES || p.phaseBoxes + p.acceptanceTotal > MAX_BOXES)
      .map((p) => `${p.rel}  (${p.phases} phases, ${p.phaseBoxes + p.acceptanceTotal} boxes)`),
  );

  add(
    "no-proof",
    "Box without proof: — nobody can tell when it is allowed to be ticked",
    "name the proof on the box (`proof: <command | CI job | PR>`), or cite the evidence beside it",
    open
      .filter((p) => boxes.get(p.rel).noProof > 0)
      .map((p) => `${p.rel}  (${boxes.get(p.rel).noProof})`),
  );

  add(
    "misfiled-done",
    "Filed under done/ with boxes still open",
    "reopen it, or tick and evidence the remaining boxes",
    prds.filter((p) => p.done && p.openBoxes > 0).map((p) => `${p.rel}  (${p.openBoxes} open)`),
  );

  add(
    "status-says-done",
    "Status line claims done, file is not in done/",
    "verify the boxes, then prd-close.mjs",
    prds
      .filter((p) => !p.done && DONE_WORDS.test(p.status) && !OPEN_WORDS.test(p.status))
      .map((p) => `${p.rel}  — ${truncate(p.status, 60)}`),
  );

  add(
    "status-says-open",
    "Filed under done/ but the status line says otherwise",
    "the one clean un-filing: move it back and say so",
    prds
      .filter((p) => p.done && OPEN_WORDS.test(p.status) && !DONE_WORDS.test(p.status))
      .map((p) => `${p.rel}  — ${truncate(p.status, 60)}`),
  );

  add(
    "no-phase-boxes",
    "No phase checkboxes — progress cannot be reported, so nobody works it",
    "add the boxes from the phase prose before starting",
    prds.filter((p) => !p.done && p.phases === 0).map((p) => p.rel),
  );

  add(
    "compound-criteria",
    "Acceptance boxes conjoining independent claims — unreachable by construction",
    "split it into one box per claim, or move the unreachable clause to a `## Blocked on` line",
    open
      .filter((p) => boxes.get(p.rel).compound > 0)
      .map((p) => `${p.rel}  (${boxes.get(p.rel).compound})`),
  );

  const ids = new Map();
  for (const prd of prds) ids.set(prd.id, [...(ids.get(prd.id) ?? []), prd.rel]);
  add(
    "duplicate-ids",
    "Same PRD id in more than one file",
    "one id, one file — merge or renumber",
    [...ids.entries()].filter(([, files]) => files.length > 1).map(([id, files]) => `${id}: ${files.join(", ")}`),
  );

  add(
    "never-started",
    `Filed ${olderThan}+ days ago and still at 0% — the bloat every agent still reads`,
    "keep, or move to an ideas file; a plan nobody starts is not a plan",
    prds
      .filter((p) => !p.done && !p.blocked && p.percent === 0 && (p.bornDays ?? 0) >= olderThan)
      .sort((a, b) => (b.bornDays ?? 0) - (a.bornDays ?? 0))
      .map((p) => `${p.rel}  (filed ${p.bornDays}d ago, last touched ${p.ageDays}d)`),
  );

  add(
    "blocked-stale",
    `Blocked and untouched for ${olderThan}+ days — several blockers outlive their condition`,
    "retry the blocked reason once, record what happened, then re-file",
    prds
      .filter((p) => p.blocked && (p.ageDays ?? 0) >= olderThan)
      .sort((a, b) => (b.ageDays ?? 0) - (a.ageDays ?? 0))
      .map((p) => `${p.rel}  (${p.ageDays}d)`),
  );

  add(
    "blocked-without-reason",
    "Blocked PRD not filed under a reason folder — BLOCKED/<short-reason>/<prd>.md",
    "move it under a folder naming the missing evidence, credential or person",
    prds.filter((p) => p.blocked && p.blockedReason === "").map((p) => p.rel),
  );

  const evidenceDir = findEvidenceDir(repoRoot, flags.evidence);
  if (evidenceDir !== undefined && existsSync(evidenceDir)) {
    const referenced = referencedNames(repoRoot, evidenceDir);
    if (referenced !== undefined) {
      add(
        "orphan-evidence",
        `Evidence files under ${relative(repoRoot, evidenceDir)} that nothing outside them references`,
        "delete, or cite them from the PRD they prove",
        listMarkdown(evidenceDir)
          .filter((file) => !referenced.has(basename(file)))
          .map((file) => relative(repoRoot, file)),
      );
    }
  }

  const ORDER = [
    "ready-not-filed",
    "blocked-only-not-filed",
    "ceremony-box",
    "status-says-done",
    "status-says-open",
    "duplicate-ids",
    "over-size-cap",
    "no-phase-boxes",
    "compound-criteria",
    "misfiled-done",
    "never-started",
    "blocked-without-reason",
    "blocked-stale",
    "no-proof",
    "orphan-evidence",
  ];
  findings.sort((a, b) => ORDER.indexOf(a.key) - ORDER.indexOf(b.key));

  if (flags.json === true) {
    process.stdout.write(`${JSON.stringify(findings, null, 2)}\n`);
  } else if (findings.length === 0) {
    process.stdout.write("No PRD drift found.\n");
  } else {
    let out = "";
    for (const finding of findings) {
      out += `\n${finding.title}  [${finding.items.length}]\n  fix: ${finding.fix}\n`;
      for (const item of finding.items.slice(0, cap)) out += `  - ${item}\n`;
      if (finding.items.length > cap) out += `  … ${finding.items.length - cap} more (--all)\n`;
    }
    const total = findings.reduce((sum, finding) => sum + finding.items.length, 0);
    out += `\n${total} items across ${findings.length} categories.\n`;
    process.stdout.write(out);
    process.stdout.write(savingsLine(prds, out));
  }

  const actionable = new Set(["duplicate-ids", "misfiled-done", "ready-not-filed", "status-says-done", "status-says-open"]);
  if (flags.strict === true && findings.some((finding) => actionable.has(finding.key))) process.exit(1);
}

main();
