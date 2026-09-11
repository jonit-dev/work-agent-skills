#!/usr/bin/env python3
"""docprint - render Markdown/HTML to a styled PDF, optionally N-up, optionally print.

Self-bootstrapping: if `markdown` or `pypdf` are missing it builds a cached venv at
~/.cache/agent-print/venv and re-execs itself there.

  docprint.py REPORT.md                      # -> REPORT.pdf (A4 portrait)
  docprint.py REPORT.md --nup 2              # -> REPORT-2up.pdf (2 A5 pages / A4 landscape)
  docprint.py REPORT.md --nup 2 --print      # ... and send it to the default printer
  docprint.py REPORT.md --nup 2 -d Brother_HL_L2320D --copies 2
  docprint.py A.md B.md --nup 2 --print      # several documents in one go
  docprint.py --list-printers
"""
from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.parse

VENV = pathlib.Path.home() / ".cache" / "agent-print" / "venv"
REQS = ["markdown", "pypdf"]


def ensure_deps() -> None:
    """Import deps, or build a cached venv and re-exec inside it."""
    try:
        import markdown, pypdf  # noqa: F401
        return
    except ImportError:
        pass
    if sys.prefix == str(VENV):
        sys.exit("error: dependencies still missing inside the bootstrap venv")
    py = VENV / "bin" / "python"
    if not py.exists():
        print(f"bootstrapping dependencies in {VENV} ...", file=sys.stderr)
        VENV.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", *REQS], check=True)
    os.execv(str(py), [str(py), os.path.abspath(__file__), *sys.argv[1:]])


# --- page geometry (PostScript points) -------------------------------------
PAGE_PT = {"A4": (595.28, 841.89), "Letter": (612.0, 792.0)}

# Source page size per N-up factor, chosen so the composed sheet needs no
# downscaling: two A5 portraits tile an A4 landscape exactly; four A6 tile A4.
NUP_SOURCE = {1: "A4", 2: "A5", 4: "A6"}

# Explicit CSS page dimensions per (sheet, orientation, nup). Chosen so the panel
# is rendered at exactly the size it will occupy -> no downscaling, and no
# mismatch between what we compose and what we tell CUPS.
#   landscape 2-up: sheet rotated, split into 2 columns -> panel is sheet_h/2 x sheet_w
#   portrait  2-up: sheet upright,  split into 2 rows    -> panel is sheet_w x sheet_h/2
def panel_css_size(sheet: str, n: int, orientation: str) -> str:
    sw, sh = PAGE_PT[sheet]
    if n == 1:
        return f"{sw}pt {sh}pt"
    if orientation == "portrait":
        cols, rows = (1, 2) if n == 2 else (2, 2)
        W, H = sw, sh
    else:
        cols, rows = (2, 1) if n == 2 else (2, 2)
        W, H = sh, sw
    return f"{W / cols}pt {H / rows}pt"


# Type scale keyed by how much area the panel gets, not by ISO name.
def type_for(n: int) -> dict:
    return TYPE["A4"] if n == 1 else (TYPE["A5"] if n == 2 else TYPE["A6"])

# Portrait composition: two A5 LANDSCAPE panels stack to fill an A4 portrait
# (210x148 x2 = 210x296); four A6 portraits tile A4 portrait 2x2. Same 1:1
# no-downscale property as the landscape path, just rotated.
NUP_SOURCE_PORTRAIT = {1: "A4", 2: "A5L", 4: "A6"}

# Type scale per source page size, sized for how large it actually prints.
TYPE = {
    "A4": dict(base=10.5, h1=21, h2=15, h3=12, tbl=9.2, mono=8.8, pad=6, mar="16mm 17mm"),
    "A5": dict(base=8.6, h1=16, h2=11.5, h3=9.4, tbl=7.6, mono=7.4, pad=3.5, mar="11mm"),
    "A5L": dict(base=8.6, h1=16, h2=11.5, h3=9.4, tbl=7.6, mono=7.4, pad=3.5, mar="10mm 12mm"),
    "A6": dict(base=6.6, h1=12, h2=9, h3=7.4, tbl=6.0, mono=5.8, pad=2.5, mar="8mm"),
}

CSS_TMPL = """
@page {{ size: {pagesize}; margin: {mar}; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', 'DejaVu Sans', Arial, sans-serif; font-size: {base}pt;
       color: #15171c; line-height: 1.42; margin: 0; }}
h1 {{ font-size: {h1}pt; margin: 0 0 3px; letter-spacing: -0.015em; line-height: 1.15;
     border-bottom: 2pt solid #15171c; padding-bottom: 5px; }}
h2 {{ font-size: {h2}pt; margin: 15px 0 6px; padding-bottom: 3px;
     border-bottom: 0.75pt solid #b9bfc9; letter-spacing: -0.005em; }}
h3 {{ font-size: {h3}pt; margin: 11px 0 4px; line-height: 1.28; }}
h4, h5, h6 {{ font-size: {h3}pt; margin: 9px 0 3px; }}
p {{ margin: 4px 0; }}
ul, ol {{ margin: 3px 0 7px; padding-left: 14px; }}
li {{ margin: 1.5px 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: {tbl}pt; }}
th {{ background: #eceff4; font-weight: 600; text-align: left; padding: {pad}px 5px;
     border: 0.6pt solid #b9bfc9; }}
td {{ padding: {pad}px 5px; border: 0.5pt solid #d4d9e1; vertical-align: top; }}
tr:nth-child(even) td {{ background: #fafbfc; }}
tr {{ page-break-inside: avoid; }}
code {{ font-family: 'DejaVu Sans Mono', monospace; background: #eef0f4; padding: 0.5px 3px;
       border-radius: 2px; font-size: {mono}pt; }}
pre {{ background: #eef0f4; padding: 7px; border-radius: 3px; overflow-x: auto;
      font-size: {mono}pt; }}
pre code {{ background: none; padding: 0; }}
hr {{ border: none; border-top: 0.6pt solid #d4d9e1; margin: 12px 0; }}
img {{ max-width: 100%; }}
strong {{ font-weight: 650; }}
em {{ color: #565c68; }}
h1, h2, h3 {{ page-break-after: avoid; }}
blockquote {{ margin: 6px 0; padding: 1px 0 1px 9px; border-left: 2pt solid #b9bfc9;
             color: #474d58; }}
"""

BROWSERS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
            "brave", "brave-browser", "microsoft-edge"]


def find_browser() -> str:
    for name in BROWSERS:
        if shutil.which(name):
            return name
    sys.exit("error: no Chromium-based browser found (tried: " + ", ".join(BROWSERS) + ")")


def render(src: pathlib.Path, size: str, scale: dict | None = None) -> pathlib.Path:
    """Markdown/HTML -> PDF. `size` is a CSS @page size (name or explicit dims)."""
    import markdown

    pdf = src.with_suffix(".pdf")
    if src.suffix.lower() in {".html", ".htm"}:
        html_path, temp = src, False
    else:
        body = markdown.markdown(
            src.read_text(encoding="utf-8"),
            extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        )
        css = CSS_TMPL.format(pagesize=size, **(scale or TYPE["A4"]))
        html_path = src.with_suffix(".render.html")
        html_path.write_text(
            '<!DOCTYPE html><html><head><meta charset="utf-8">'
            f"<style>{css}</style></head><body>{body}</body></html>",
            encoding="utf-8",
        )
        temp = True

    url = "file://" + urllib.parse.quote(str(html_path.resolve()))
    proc = subprocess.run(
        [find_browser(), "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--print-to-pdf-no-header",
         f"--print-to-pdf={pdf}", url],
        capture_output=True, text=True,
    )
    if temp:
        html_path.unlink(missing_ok=True)
    if not pdf.exists():
        sys.exit(f"error: PDF was not produced.\n{proc.stderr[-1500:]}")
    return pdf


def nup(src: pathlib.Path, n: int, sheet: str = "A4",
        orientation: str = "landscape") -> pathlib.Path:
    """Tile N source pages onto one sheet. Returns the new PDF path.

    orientation="landscape": 2-up sits side by side on a landscape sheet.
    orientation="portrait":  2-up stacks top/bottom on a portrait sheet, which
    is what you want when the printer is loaded portrait and you do not want to
    turn the paper sideways to read it.
    """
    from pypdf import PdfReader, PdfWriter, Transformation

    sw, sh = PAGE_PT[sheet]
    if orientation == "portrait":
        W, H = sw, sh
        cols, rows = (1, 2) if n == 2 else (2, 2)
    else:
        W, H = sh, sw  # landscape
        cols, rows = (2, 1) if n == 2 else (2, 2)
    cw, ch = W / cols, H / rows

    reader = PdfReader(src)
    writer = PdfWriter()
    for i in range(0, len(reader.pages), n):
        out = writer.add_blank_page(width=W, height=H)
        for slot, page in enumerate(reader.pages[i:i + n]):
            pw, ph = float(page.mediabox.width), float(page.mediabox.height)
            s = min(cw / pw, ch / ph)
            col, row = slot % cols, slot // cols
            tx = col * cw + (cw - pw * s) / 2
            ty = H - (row + 1) * ch + (ch - ph * s) / 2
            out.merge_transformed_page(page, Transformation().scale(s).translate(tx, ty))
    dst = src.with_name(f"{src.stem}-{n}up.pdf")
    with open(dst, "wb") as fh:
        writer.write(fh)
    return dst


MEDIA_DIMS = {"A4": (595.28, 841.89), "Letter": (612.0, 792.0)}


def prerotated_copy(pdf: pathlib.Path, media: str) -> pathlib.Path:
    """Rotate landscape pages 90deg onto a portrait mediabox.

    This printer chain (safe-brother-pdf wrapper -> gutenprint) ignores
    orientation-requested, so flag-based rotation is unreliable and landscape
    sheets print clipped in portrait. A portrait page with pre-rotated
    content leaves the driver nothing to decide.
    """
    pypdf = __import__("pypdf")
    pw, ph = MEDIA_DIMS[media]
    reader = pypdf.PdfReader(str(pdf))
    writer = pypdf.PdfWriter()
    rotated = False
    for page in reader.pages:
        if float(page.mediabox.width) > float(page.mediabox.height):
            blank = pypdf.PageObject.create_blank_page(width=pw, height=ph)
            blank.merge_transformed_page(
                page, pypdf.Transformation().rotate(90).translate(pw, 0))
            writer.add_page(blank)
            rotated = True
        else:
            writer.add_page(page)
    if not rotated:
        return pdf
    out = pdf.with_suffix(".print.pdf")
    with out.open("wb") as f:
        writer.write(f)
    return out


def send(pdf: pathlib.Path, printer: str | None, copies: int, media: str,
         duplex: str | None, title: str) -> None:
    if media not in MEDIA_DIMS:
        sys.exit(f"error: unsupported --media {media} (need A4 or Letter)")
    sheet = prerotated_copy(pdf, media)
    cmd = ["lp", "-t", title, "-o", f"media={media}", "-n", str(copies)]
    if printer:
        cmd += ["-d", printer]
    if duplex:
        cmd += ["-o", f"sides={duplex}"]
    cmd.append(str(sheet))
    r = subprocess.run(cmd, capture_output=True, text=True)
    print((r.stdout or r.stderr).strip())
    if r.returncode:
        sys.exit(r.returncode)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render Markdown/HTML to PDF, N-up, and print.")
    ap.add_argument("files", nargs="*", help=".md, .html or .pdf inputs")
    ap.add_argument("--orientation", choices=["landscape", "portrait"],
                    default="landscape",
                    help="sheet orientation for --nup 2/4 (default landscape). "
                         "portrait stacks panels top/bottom on an upright sheet.")
    ap.add_argument("--nup", type=int, default=1, choices=[1, 2, 4],
                    help="source pages per printed sheet (default 1)")
    ap.add_argument("--print", dest="do_print", action="store_true", help="send to a printer")
    ap.add_argument("-d", "--printer", help="CUPS printer name (default: system default)")
    ap.add_argument("-n", "--copies", type=int, default=1)
    ap.add_argument("--media", default="A4")
    ap.add_argument("--duplex", choices=["one-sided", "two-sided-long-edge",
                                         "two-sided-short-edge"])
    ap.add_argument("--list-printers", action="store_true")
    args = ap.parse_args()

    if args.list_printers:
        subprocess.run(["lpstat", "-p", "-d"])
        return
    if not args.files:
        ap.error("no input files")

    for f in args.files:
        src = pathlib.Path(f).expanduser().resolve()
        if not src.exists():
            sys.exit(f"error: {src} not found")

        if src.suffix.lower() == ".pdf":
            pdf = src
        else:
            pdf = render(src,
                         panel_css_size(args.media, args.nup, args.orientation),
                         type_for(args.nup))

        out = (nup(pdf, args.nup, sheet=args.media, orientation=args.orientation)
               if args.nup > 1 else pdf)
        pages = len(__import__("pypdf").PdfReader(out).pages)
        print(f"{src.name} -> {out} ({pages} sheet{'s' if pages != 1 else ''})")

        if args.do_print:
            send(out, args.printer, args.copies, args.media, args.duplex, src.stem)


if __name__ == "__main__":
    ensure_deps()
    main()
