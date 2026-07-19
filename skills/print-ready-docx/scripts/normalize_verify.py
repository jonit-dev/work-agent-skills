#!/usr/bin/env python3
"""Normalize a DOCX through LibreOffice, validate it, and render pages to PNG."""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


def run(cmd):
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(f"Command failed: {' '.join(map(str,cmd))}\n{result.stdout}\n{result.stderr}")
    return result


def zip_check(path):
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad: raise SystemExit(f"Corrupt DOCX member: {bad}")
        required={"[Content_Types].xml","word/document.xml"}
        missing=required-set(zf.namelist())
        if missing: raise SystemExit(f"Missing DOCX parts: {sorted(missing)}")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input",type=Path); ap.add_argument("--replace",action="store_true"); ap.add_argument("--render-dir",type=Path,required=True); a=ap.parse_args()
    source=a.input.resolve(); zip_check(source)
    soffice=shutil.which("soffice"); pdftoppm=shutil.which("pdftoppm")
    if not soffice or not pdftoppm: raise SystemExit("Require soffice and pdftoppm")
    try:
        from docx import Document
        Document(source)
    except ImportError:
        pass
    with tempfile.TemporaryDirectory(prefix="docx-normalize-") as td:
        td=Path(td); normalized=td/source.name
        run([soffice,"--headless","--convert-to","docx","--outdir",str(td),str(source)])
        if not normalized.exists(): raise SystemExit("LibreOffice did not create normalized DOCX")
        zip_check(normalized)
        target=source if a.replace else source.with_name(source.stem+"-normalized.docx")
        shutil.copy2(normalized,target)
    zip_check(target)
    a.render_dir.mkdir(parents=True,exist_ok=True)
    run([soffice,"--headless","--convert-to","pdf","--outdir",str(a.render_dir),str(target)])
    pdf=a.render_dir/(target.stem+".pdf")
    if not pdf.exists(): raise SystemExit("PDF render failed")
    run([pdftoppm,"-png",str(pdf),str(a.render_dir/"page")])
    pages=sorted(a.render_dir.glob("page-*.png"))
    if not pages: raise SystemExit("No rendered PNG pages")
    print(f"DOCX: {target}\nPDF: {pdf}\nPages: {len(pages)}\nInspect every page PNG before delivery.")


if __name__ == "__main__": main()
