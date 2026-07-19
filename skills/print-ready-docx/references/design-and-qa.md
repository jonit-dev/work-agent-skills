# Design and QA reference

## Presets

### Contract

- A4 portrait, 22.5 mm side margins, 19 mm top/bottom.
- Calibri 11 pt, 1.25 line spacing, 6 pt after.
- H1 16 pt blue; H2 13 pt blue; H3 12 pt dark blue.
- Dense but readable tables; pale blue headers.
- Red callout for blocking risks; gold callout for caveats.

### Business

- Same page geometry and typography, 1.10 line spacing.
- More whitespace between sections.
- Limit tables to market comparables, scenarios, metrics, and checklists.

## Visual QA checklist

- Cover is balanced and metadata fits.
- Header/footer do not collide with content.
- Every heading has content beneath it on the same page.
- Numbered lists restart at 1 for each logical sequence.
- Table headers repeat after a page break.
- No row has fixed height; text wraps without clipping.
- Callout boxes remain on one page.
- Links are legible in print even without color.
- No page is accidentally blank.
- A short final page is intentional, not caused by keep-with-next or an oversized table.
- Currency, percentages, accents, and superscript m² render correctly.

## Compatibility choices

Prefer:

- paragraphs, inline runs, tables, headers, footers;
- fixed DXA table geometry;
- standard fonts;
- simple PAGE fields;
- external HTTP(S) hyperlinks.

Avoid unless explicitly needed:

- floating drawings and text boxes;
- custom embedded fonts;
- macros/OLE objects;
- complex dynamic fields;
- nested tables;
- section proliferation;
- tracked changes/comments in final print copies.

## Repair sequence

1. `unzip -t file.docx`.
2. Open with `python-docx`.
3. LibreOffice round-trip to DOCX in a temporary directory.
4. Replace the deliverable with the normalized copy.
5. Render normalized DOCX to PDF/PNG.
6. Inspect every page and compare with the source text.
