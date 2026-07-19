---
name: print-ready-docx
description: Create professional, print-ready, reader-compatible DOCX files from Markdown reports or structured text. Use when Codex must generate Word documents for printing, convert .md reports to .docx, format financial/legal/market reports, preserve headings/tables/links, or repair a DOCX that crashes or closes in a reader. Enforces LibreOffice normalization plus render-and-inspect visual QA.
---

# Print-ready DOCX

Create conservative DOCX documents that open reliably and print cleanly.

## Required workflow

1. Read the source completely and identify title, subtitle, metadata, warnings, tables, lists, and sources.
2. Choose one preset:
   - `contract`: legal, tax, negotiation, due-diligence, or dense operational reports.
   - `business`: market research, executive briefs, valuations, and general professional reports.
3. Create the DOCX with `scripts/md_to_docx.py`.
4. Normalize and render it with `scripts/normalize_verify.py --replace --render-dir ...`.
5. Open every rendered page image at 100% and inspect it. Never infer visual quality from successful generation.
6. Fix numbering continuation, split callouts, clipped tables, orphan headings, excessive blank pages, or unreadable density; repeat steps 3–5.
7. Deliver only final DOCX files unless the user requests PDFs or QA images.

Do not skip LibreOffice normalization. Raw OOXML may render successfully in LibreOffice yet crash less tolerant DOCX readers.

## Environment

Use an isolated environment, never the system/global Python:

```bash
uv venv <tmp>/docx-venv
uv pip install --python <tmp>/docx-venv/bin/python python-docx
```

Require `soffice` and `pdftoppm`. If missing, report the missing dependency rather than claiming visual verification.

## Create

```bash
<tmp>/docx-venv/bin/python scripts/md_to_docx.py \
  input.md output.docx \
  --preset contract \
  --title "Compra de imóvel" \
  --subtitle "Tributação e revisão contratual" \
  --date "15 de julho de 2026" \
  --metadata "Status=Revisão necessária" \
  --warning "Validar com advogado e contador."
```

Defaults:

- A4 portrait; use `--letter` only when the destination requires US Letter.
- Calibri 11 pt body.
- Real Word headings and lists.
- Fixed-width tables with repeated header rows and expanding row heights.
- Clickable HTTP(S) links.
- First-page cover plus quiet running header/footer.

## Normalize and verify

```bash
<tmp>/docx-venv/bin/python scripts/normalize_verify.py output.docx \
  --replace \
  --render-dir <tmp>/render-output
```

The command must succeed at all gates:

- ZIP/OOXML integrity;
- optional `python-docx` reopen;
- LibreOffice round-trip normalization;
- DOCX→PDF conversion;
- PDF→PNG rendering.

Then inspect every `page-*.png`. Use a contact sheet only for overview; open suspicious pages individually.

## Compatibility repair

When a user reports “opens and closes”, crashes, blank output, or unsupported content:

1. Preserve the original.
2. Run `normalize_verify.py --replace` on a copy.
3. Reopen with `python-docx` and render again.
4. Prefer conservative OOXML: no text boxes, floating shapes, embedded fonts, macros, complex fields, or percentage-width tables.
5. Use simple ASCII filenames when the reader may mishandle Unicode.

## Content rules

- Preserve meaning and citations; do not silently rewrite legal/financial conclusions.
- Use tables only for repeated comparable fields. Convert prose-heavy grids into sections or bullets.
- Use a risk callout for material “do not sign/pay/execute” warnings.
- Keep headings with following content and prevent one-row callouts from splitting across pages.
- Restart numbered lists for each logical sequence.
- Do not claim a title page, TOC, page number, or link works until verified in the render.

Read [references/design-and-qa.md](references/design-and-qa.md) when selecting layout or diagnosing render problems.

## Final response

Link each final DOCX with an absolute workspace path. Mention visual QA only if all rendered pages were actually inspected.
