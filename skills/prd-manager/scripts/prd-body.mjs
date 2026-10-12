#!/usr/bin/env node
/**
 * The pull request body for a PRD, generated from the PRD.
 *
 * Prints only the collapsible PRD-progress block. The human-written opening ("What is this PR
 * about?", "Why does it matter?") is never generated; --pr replaces just this block between its
 * markers, so that prose survives every regeneration.
 *
 * Usage: node prd-body.mjs <prd file> [--pr <number> [--yes]]
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { basename, dirname, relative, resolve } from "node:path";
import { findPrdRoot, parseArgs, progressOf, repoRootOf } from "./prd-lib.mjs";

const START = "<!-- prd-progress:start -->";
const END = "<!-- prd-progress:end -->";
const HEADING = /^(#{2,4})\s+(.*)$/u;
const PHASE_HEADING = /^#{3,4}\s+(?:Phase\b|\d+\.\s)/iu;
const ACCEPTANCE_HEADING = /^#{2,4}\s+Acceptance criteria\b/iu;
const BOX = /^\s*[-*]\s+\[([ xX])\]\s*(.*)$/u;

/** Sections with their boxes, so the body can group "done" and "left" under real headings. */
function sections(markdown) {
  const out = [];
  let current = { boxes: [], kind: "other", title: "" };
  out.push(current);
  for (const line of markdown.split("\n")) {
    const heading = HEADING.exec(line);
    if (heading !== null) {
      current = {
        boxes: [],
        kind: PHASE_HEADING.test(line) ? "phase" : ACCEPTANCE_HEADING.test(line) ? "acceptance" : "other",
        title: heading[2].replace(/[*`]/gu, "").trim(),
      };
      out.push(current);
      continue;
    }
    const box = BOX.exec(line);
    if (box !== null) current.boxes.push({ text: box[2].trim(), ticked: box[1] !== " " });
  }
  return out;
}

function bullet(box) {
  return `- [${box.ticked ? "x" : " "}] ${box.text}`;
}

function build(markdown, { id, file }) {
  const progress = progressOf(markdown);
  const all = sections(markdown);
  const phases = all.filter((section) => section.kind === "phase" && section.boxes.length > 0);
  const acceptance = all.filter((section) => section.kind === "acceptance" && section.boxes.length > 0);

  const lines = [];
  lines.push(START);
  lines.push(
    `<details><summary>PRD progress: ${progress.percent}% — ${progress.phasesComplete}/${progress.phases} phases ` +
      `(${progress.phaseBoxesTicked}/${progress.phaseBoxes} boxes), ` +
      `${progress.acceptanceTicked}/${progress.acceptanceTotal} acceptance (generated)</summary>`,
  );
  lines.push("");
  lines.push(`PRD: \`${file}\``);
  lines.push("");
  for (const phase of phases) {
    const done = phase.boxes.filter((box) => box.ticked).length;
    lines.push(`**${phase.title}** — ${done}/${phase.boxes.length}`);
    lines.push("");
    for (const box of phase.boxes) lines.push(bullet(box));
    lines.push("");
  }
  if (acceptance.length > 0) {
    lines.push("**Acceptance criteria**");
    lines.push("");
    for (const section of acceptance) for (const box of section.boxes) lines.push(bullet(box));
    lines.push("");
  }
  lines.push("</details>");
  lines.push(END);
  return lines.join("\n");
}

function main() {
  const { flags, positional } = parseArgs(process.argv.slice(2));
  const file = positional[0];
  if (file === undefined) {
    process.stderr.write("usage: prd-body.mjs <prd file> [--pr <number> [--yes]]\n");
    process.exit(1);
  }
  const full = resolve(file);
  const markdown = readFileSync(full, "utf8");
  const root = flags.root === undefined ? findPrdRoot(dirname(full)) : resolve(flags.root);
  const repoRoot = repoRootOf(root);
  const id = /^(PRD-[A-Za-z0-9.]*\d[A-Za-z0-9.]*)/u.exec(basename(full))?.[1] ?? basename(full);
  const body = build(markdown, { file: relative(repoRoot, full), id });

  if (flags.pr === undefined) {
    process.stdout.write(`${body}\n`);
    return;
  }
  if (flags.yes !== true) {
    process.stdout.write(`${body}\n\n--- dry run — add --yes to write this to PR #${flags.pr}.\n`);
    return;
  }
  const current = execFileSync("gh", ["pr", "view", String(flags.pr), "--json", "body", "-q", ".body"], { cwd: repoRoot, encoding: "utf8" }).trimEnd();
  const from = current.indexOf(START);
  const to = current.indexOf(END);
  // Keep the human-written opening; replace only the generated block (or append it once).
  const next = from !== -1 && to > from ? `${current.slice(0, from)}${body}${current.slice(to + END.length)}` : `${current}\n\n${body}`;
  execFileSync("gh", ["pr", "edit", String(flags.pr), "--body", next], { cwd: repoRoot, stdio: "inherit" });
  process.stdout.write(`\nPR #${flags.pr} body updated from ${relative(repoRoot, full)}.\n`);
}

main();
