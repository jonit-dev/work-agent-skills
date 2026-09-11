# LibreOffice UNO XLSX recipes

## Use this path when

Use Python UNO when LibreOffice is installed and the workspace has no existing
XLSX library. Prefer a project dependency already in use when it preserves
formulas and formatting more reliably.

## Safe creation pattern

1. Launch a headless LibreOffice process with a unique port and temporary user
   profile.
2. Create `private:factory/scalc`.
3. Populate and format the workbook.
4. Save with filter `Calc MS Excel 2007 XML` to a unique temporary `.xlsx`.
5. Close the document.
6. Validate the temporary file with `workbook_tool.py validate`.
7. Atomically replace the requested target.

Never call `storeAsURL` directly on an existing target. LibreOffice can return
`0x440a AlreadyExists` even when an overwrite property is supplied.

## Core operations

```python
document = desktop.loadComponentFromURL("private:factory/scalc", "_blank", 0, ())
sheet = document.Sheets.getByIndex(0)
sheet.Name = "Report"

sheet.getCellRangeByName("A1:H1").merge(True)
sheet.getCellByPosition(0, 0).String = "Report title"
sheet.getCellRangeByName("A1:H1").CellBackColor = 0x17365D
sheet.getCellRangeByName("A1:H1").CharColor = 0xFFFFFF
sheet.getCellRangeByName("A1:H1").CharWeight = 150.0

sheet.Columns.getByIndex(0).Width = 3000
sheet.Rows.getByIndex(0).Height = 900
sheet.getCellRangeByName("A3:H20").IsTextWrapped = True

document.CurrentController.freezeAtPosition(2, 4)
table = sheet.getCellRangeByName("A4:H20")
document.DatabaseRanges.addNewByName("ReportFilter", table.RangeAddress)
document.DatabaseRanges.getByName("ReportFilter").AutoFilter = True
```

Create a `PropertyValue` for saving:

```python
from com.sun.star.beans import PropertyValue

def prop(name, value):
    item = PropertyValue()
    item.Name = name
    item.Value = value
    return item

document.storeAsURL(
    uno.systemPathToFileUrl(str(temporary_output.resolve())),
    (prop("FilterName", "Calc MS Excel 2007 XML"),),
)
```

## Formatting rules

- Use `CellBackColor`, `CharColor`, `CharWeight`, `CharHeight`, and
  `IsTextWrapped`.
- Set column widths explicitly; UNO uses hundredths of a millimeter.
- Use number formats for percentages, currency, dates, and decimals.
- Add icons or text labels alongside color-coded states.
- Make the first filter row visually distinct and freeze it.
- Sort semantic rankings through a rank map such as
  `Critical=0, High=1, Medium=2, Low=3, Very low=4`.

## Editing existing files

Open hidden, modify the smallest range, and save to a new file first. Preserve:

- formulas and named ranges;
- existing number formats;
- merged ranges and freeze panes;
- filters and sheet names;
- hidden sheets, rows, and columns.

Do not round-trip through CSV when these workbook features matter.

## Validation

Run:

```bash
python3 scripts/workbook_tool.py validate output.xlsx
python3 scripts/workbook_tool.py render output.xlsx --output-dir /tmp/xlsx-preview
```

Use `pdfinfo` to check the PDF and `pdftoppm` to create PNG previews. Visually
inspect the dashboard and at least one data page. A successful XLSX ZIP check
does not prove readable layout or correct formulas.
