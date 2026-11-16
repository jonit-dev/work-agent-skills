#!/usr/bin/env node
/**
 * Contract check between the two PRD skills: the template in prd-creator must stay closable by
 * this parser. A template with no phase box reports 0% forever, and prd-close refuses it.
 *
 * Usage: node test-prd-template.mjs [path/to/prd-creator/SKILL.md]
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { progressOf } from "./prd-lib.mjs";

const skill = process.argv[2] ?? fileURLToPath(new URL("../../prd-creator/SKILL.md", import.meta.url));
const template = /```markdown\n(# PRD-[\s\S]*?)\n```/u.exec(readFileSync(skill, "utf8"))?.[1];
assert.ok(template, `no PRD template block in ${skill}`);

// Tick every box, as a finished PRD would be: it must then report ready to close.
const progress = progressOf(template.replace(/^(\s*[-*]\s+)\[ \]/gmu, "$1[x]"));
assert.ok(progress.phases > 0, "the template has no phase box, so prd-manager reports 0% and prd-close refuses it");
assert.equal(progress.ready, true, "the template with every box ticked must be ready to close");
console.log(
  `ok: ${progress.phases} phase(s), ${progress.phaseBoxes} phase box(es), ` +
    `${progress.acceptanceTotal} acceptance box(es), closable once ticked`,
);
