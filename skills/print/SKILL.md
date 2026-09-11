---
name: print
description: "Render a Markdown, HTML, or PDF document to a clean printable PDF and send it to a physical printer via CUPS, with optional 2-up or 4-up landscape layout. Use when asked to print a file, print a report, send something to the printer, make a printable PDF, or fit multiple pages on one sheet."
---

# Print

Turns a document into paper. One script does the whole chain:

```
Markdown / HTML  ->  styled PDF  ->  optional N-up landscape sheet  ->  CUPS printer
```

`scripts/docprint.py` is the entire implementation. It bootstraps its own dependencies
(`markdown`, `pypdf`) into a cached venv at `~/.cache/agent-print/venv` on first run, so there
is nothing to install.

---

## Usage

```bash
S=~/.agents/skills/print/scripts/docprint.py

python3 $S --list-printers                       # what is available, and the default
python3 $S REPORT.md                             # -> REPORT.pdf, A4 portrait, nothing printed
python3 $S REPORT.md --nup 2                     # -> REPORT-2up.pdf, two pages per landscape sheet
python3 $S REPORT.md --nup 2 --print             # ... and send it to the default printer
python3 $S REPORT.md --print -d Brother_HL_L2320D --duplex two-sided-long-edge
python3 $S A.md B.md --nup 2 --print             # several documents in one invocation
python3 $S existing.pdf --nup 2 --print          # PDFs skip rendering and go straight to N-up
```

| Flag | Meaning |
|---|---|
| `--nup 1\|2\|4` | Source pages per printed sheet. Default 1. |
| `--orientation landscape\|portrait` | Sheet orientation for N-up. Default landscape (panels side by side). `portrait` stacks them top/bottom on an upright sheet. |
| `--print` | Actually send it. **Without this flag nothing is printed** — you just get the PDF. |
| `-d NAME` | CUPS printer. Omit to use the system default. |
| `-n N` | Copies. |
| `--duplex two-sided-short-edge` | Double-sided. Use **short-edge** whenever the sheet is landscape (incl. N-up landscape): pages are pre-rotated onto a portrait mediabox, so short-edge flipping is what makes the back side read right-side up when you turn the sheet. |
| `--media A4\|Letter` | Sheet size. Default A4. |

The PDF is always written next to the source file, so the user keeps it after printing.

---

## How N-up works here

The script does **not** shrink full pages down onto a sheet — that is what makes most 2-up output
hard to read. It renders each panel at the size it will actually occupy, so the composition is
1:1 with no downscaling.

**Landscape (default)** — panels side by side, sheet turned sideways:

| `--nup` | Panel is | Composed onto |
|---|---|---|
| 2 | half the sheet's height x its width | one landscape sheet, 2 columns |
| 4 | a quarter sheet | one landscape sheet, 2x2 |

**Portrait (`--orientation portrait`)** — panels stacked, sheet stays upright:

| `--nup` | Panel is | Composed onto |
|---|---|---|
| 2 | the sheet's width x half its height | one portrait sheet, 2 rows |
| 4 | a quarter sheet | one portrait sheet, 2x2 |

Effective body type is ~8.6pt at `--nup 2` and ~6.6pt at `--nup 4` regardless of orientation.
`--nup 4` is a reference card, not a document. Do not suggest it for anything read end to end.

**Which orientation?** Ask, or match the binder. Landscape 2-up reads like an open book and is
the better default for a report. Portrait 2-up keeps the sheet upright in a stack or a standard
folder. Neither is "the" right answer, and getting it wrong wastes the whole job — so if the
user has not said, ask before printing rather than after.

## Procedure

1. **Confirm the target before printing.** Run `--list-printers` if the user did not name one,
   and use the default unless the list shows something obviously more appropriate. Printer
   names containing `DO_NOT_USE`, `PHYSICAL_DO_NOT_USE`, or similar are traps — never pick one
   of those, even if it looks like the printer the user meant.
1b. **Check the printer's actual media before choosing `--media`, and pass it explicitly.**
   `lpoptions -p NAME` shows the configured default (often `Letter`, not `A4`). `--media` sets
   *both* the composition sheet and the `lp` flag, so a wrong value is not cosmetic: it produces
   a sheet whose dimensions disagree with the paper, and CUPS resolves that by rotating or
   scaling. **A4 content sent to a Letter tray is the classic way to get sideways output.**
   If the physical paper is not verifiable from the CLI, ask — you cannot see the tray.
2. **Render first, print second.** Generate the PDF without `--print`, then look at it before
   committing paper — especially for anything over two sheets.
3. **Check the page count against the layout.** An odd source page count with `--nup 2` leaves
   the last sheet half empty. If that happens, say so and offer to tighten the document rather
   than silently printing a mostly blank sheet.
4. **State the layout in words before printing anything.** "11 sheets, Letter landscape, two
   portrait panels side by side" is checkable; "2-up" is not, and it reads the same whether you
   got the orientation right or wrong. This is the step that catches a wrong assumption while it
   is still free.
5. **Print**, then report the job id from `lp` and the sheet count so the user knows what to
   expect at the tray.

### Inspecting output before printing

`mutool` or `pdftoppm` will rasterise a page so you can actually look at it:

```bash
mutool draw -o /tmp/preview%d.png -r 100 OUT.pdf     # then Read the PNG
pdftoppm -png -r 100 OUT.pdf /tmp/preview            # fallback
```

Reading page 1 catches the common failures in one shot: a stray browser header/footer, a table
running off the edge, or type that is too small at the chosen `--nup`.

---

## Writing documents that print well

- **No emoji.** Emoji render inconsistently in headless-browser PDF output and a status column
  built from checkmarks and warning signs can print completely blank. Carry status in words.
- **No Markdown checkboxes** in print-first documents — inline `[ ]` does not become a checkbox
  in most renderers, it just prints as brackets.
- **Keep tables under six columns.** Anything wider will compress into unreadable slivers at
  `--nup 2`.
- Long code blocks do not wrap; they clip at the page edge. Keep printed code narrow.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| A date and file path print in the page corners | The browser is adding its own header/footer. The script passes both `--no-pdf-header-footer` and `--print-to-pdf-no-header`; if a new browser ignores both, add its equivalent flag in `render()`. |
| `no Chromium-based browser found` | Install one, or add its binary name to `BROWSERS` in the script. |
| Job vanishes with no output | `lpstat -o` shows the queue, `lpstat -p` shows printer state. A paused printer accepts jobs silently and prints nothing — resume with `cupsenable NAME`. |
| Content prints sideways / clipped as portrait | This chain's driver (Brother via `safe-brother-pdf` wrapper -> gutenprint) **ignores `orientation-requested`** — flag-based rotation is unreliable here and landscape sheets print clipped onto portrait paper. The script therefore pre-rotates landscape pages 90° onto a portrait mediabox in `send()` (`*.print.pdf`) and sends no orientation flag at all. Never add `orientation-requested` or `-o landscape` back. Verify on screen first: `mutool draw` the pre-rotated file. |
| Print is on-center but off-balance (bigger margin one side) | The `safe-brother-pdf` wrapper repaginates every PDF onto Letter with fixed margins (45pt sides/top, bottom was 90pt). Bottom is now 45pt; if a job prints off-center again, check `grep -n "bottom = " /usr/lib/cups/backend/safe-brother-pdf` (root-owned — edit via `pkexec`). |
| 2-up is side-by-side when it should be stacked (or vice versa) | Wrong `--orientation`. Landscape puts panels in 2 columns, portrait in 2 rows. Re-render; do not try to fix it at the printer. |
| Everything is one giant page | The source HTML overrode `@page`. Pass Markdown rather than pre-built HTML, or fix the HTML's own print CSS — the script only injects its stylesheet for Markdown input. |
