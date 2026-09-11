---
name: xlsx-workbooks
description: Read, inspect, create, edit, format, render, and validate Microsoft Excel .xlsx workbooks. Use for spreadsheet or workbook requests involving tabular reports, dashboards, formulas, filters, frozen panes, conditional/status coloring, charts, multi-sheet output, CSV-to-XLSX conversion, or verification of an existing XLSX file.
---

# XLSX Workbooks

Produce a real `.xlsx` file, not a renamed CSV. Preserve the user's source data
and make status, assumptions, formulas, and scope visible inside the workbook.

## Workflow

1. Inspect the input and available spreadsheet tools.
2. Choose one durable data owner: source CSV/JSON/database query or existing
   workbook. Do not hand-maintain the same rows in two formats.
3. Create or edit the workbook with a task-specific script. Prefer LibreOffice
   UNO when available because it supports styled XLSX without adding a project
   dependency. Use ExcelJS, SheetJS, or XlsxWriter when already installed.
4. Add usable presentation: title, status/dashboard rows, readable widths,
   wrapped text, filters, frozen headers, number formats, and an explicit
   legend for non-obvious colors or icons.
5. Validate structure and values, render a preview, inspect it visually, then
   report the exact output path and any verification limits.

## Read or validate

Run the bundled tool:

```bash
python3 scripts/workbook_tool.py inspect input.xlsx
python3 scripts/workbook_tool.py validate input.xlsx
python3 scripts/workbook_tool.py render input.xlsx --output-dir /tmp/xlsx-preview
```

`inspect` returns JSON with sheet names, used ranges, formulas, and bounded cell
previews. `validate` checks OOXML ZIP integrity and that LibreOffice can open
every sheet. `render` creates a PDF; convert the relevant page to PNG and
visually inspect it when layout matters.

For exact values beyond the bounded preview, rerun `inspect` with
`--max-rows` and `--max-columns`, or write a focused UNO read script.

## Create or edit

Read [libreoffice-uno.md](references/libreoffice-uno.md) before writing a UNO
creator. It contains the atomic-save pattern, formatting properties, filters,
freeze panes, and validation checklist.

Apply these defaults unless the user specifies another style:

- Put summary/progress cells above the filterable table.
- Sort priority or relevance by an explicit rank, not alphabetically.
- Use semantic status icons plus color; never rely on color alone.
- Use green for complete, yellow for partial, red for missing/failing, blue for
  informational/differentiating, and gray for excluded/not applicable.
- Keep raw data or source CSV as the durable owner when the workbook is a
  formatted report; add a reproducible generator beside it when appropriate.
- Preserve formulas as formulas. Do not replace them with displayed values.
- Save to a temporary `.xlsx`, validate it, then atomically replace the target.

## Quality gate

Before delivery, verify all of the following:

1. The workbook opens as `Microsoft Excel 2007+` and contains the expected
   sheets.
2. Status totals, percentages, formulas, sort order, and exclusions recompute
   from the same row set.
3. Headers are frozen and filters cover the entire table.
4. Long content is wrapped and no essential dashboard value is hidden.
5. A rendered preview confirms colors, icons, title, and first data rows.

If LibreOffice reports an existing-target error, write to a unique temporary
path and use atomic replacement only after a successful save.
