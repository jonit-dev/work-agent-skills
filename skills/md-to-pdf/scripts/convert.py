#!/usr/bin/env python3
"""Convert one or more Markdown files to PDF using python-markdown + weasyprint.
Automatically detects and renders Mermaid diagrams to PNG via mmdc (npx @mermaid-js/mermaid-cli).

Usage: python3 convert.py file.md [file2.md ...]
       python3 convert.py dir/          # converts all *.md in dir
Output: <same path>.pdf (replaces .md extension)
"""
import sys
import re
import pathlib
import subprocess
import tempfile
import base64
import shutil
import markdown
from weasyprint import HTML

CSS = """
@page { size: Letter; margin: 0.5in 0.6in; }
body { font-family: Arial, sans-serif; font-size: 12px; margin: 0; color: #222; line-height: 1.5; }
h1   { font-size: 22px; border-bottom: 2px solid #333; padding-bottom: 6px; margin-top: 28px; }
h2   { font-size: 17px; margin-top: 26px; border-bottom: 1px solid #aaa; padding-bottom: 4px; }
h3   { font-size: 14px; margin-top: 18px; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 11px; }
th, td { border: 1px solid #ccc; padding: 5px 8px; text-align: left; }
th   { background: #f0f0f0; font-weight: bold; }
code { background: #f5f5f5; padding: 1px 4px; font-size: 11px; font-family: monospace; }
pre  { background: #f5f5f5; padding: 10px; font-size: 11px; overflow-x: auto; border-radius: 4px; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #aaa; margin: 8px 0; padding-left: 12px; color: #555; }
hr   { border: none; border-top: 1px solid #ddd; margin: 16px 0; }
.mermaid-diagram { text-align: center; margin: 8px 0; }
.mermaid-diagram img { max-width: 60%; height: auto; }
strong { color: #111; }
"""

MERMAID_BLOCK_RE = re.compile(r'```mermaid\s*\n(.*?)```', re.DOTALL)


def _has_mmdc() -> bool:
    """Check if mermaid-cli is available via npx."""
    try:
        r = subprocess.run(
            ["npx", "--yes", "@mermaid-js/mermaid-cli", "--version"],
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


def _render_mermaid_png(code: str, tmpdir: pathlib.Path, idx: int) -> str | None:
    """Render mermaid code to PNG via mmdc. Returns base64 img tag or None on failure."""
    src = tmpdir / f"d{idx}.mmd"
    dst = tmpdir / f"d{idx}.png"
    src.write_text(code.strip(), encoding="utf-8")

    try:
        r = subprocess.run(
            ["npx", "--yes", "@mermaid-js/mermaid-cli",
             "-i", str(src), "-o", str(dst),
             "-b", "white", "-s", "1", "--quiet"],
            capture_output=True, text=True, timeout=60,
        )
        if dst.exists():
            b64 = base64.b64encode(dst.read_bytes()).decode("ascii")
            return f'<div class="mermaid-diagram"><img src="data:image/png;base64,{b64}"/></div>'
        print(f"    mmdc error (diagram {idx}): {r.stderr[:200]}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"    mmdc timeout (diagram {idx})", file=sys.stderr)
    return None


def _md_to_html(md_text: str, render_mermaid: bool) -> str:
    """Convert markdown to HTML body, optionally rendering mermaid blocks to PNG."""
    if not render_mermaid or not MERMAID_BLOCK_RE.search(md_text):
        return markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    parts: list[tuple[str, str]] = []
    last_end = 0
    idx = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = pathlib.Path(tmpdir)
        for m in MERMAID_BLOCK_RE.finditer(md_text):
            parts.append(("md", md_text[last_end:m.start()]))
            print(f"    Rendering mermaid diagram {idx + 1}...")
            img = _render_mermaid_png(m.group(1), tmppath, idx)
            if img:
                parts.append(("raw", img))
            else:
                # Fallback: show code block
                parts.append(("md", f"```\n{m.group(1).strip()}\n```"))
            idx += 1
            last_end = m.end()
        parts.append(("md", md_text[last_end:]))

    html_parts = []
    for kind, content in parts:
        if kind == "md":
            html_parts.append(markdown.markdown(content, extensions=["tables", "fenced_code"]))
        else:
            html_parts.append(content)
    return "".join(html_parts)


def convert(src: pathlib.Path, render_mermaid: bool = True) -> pathlib.Path:
    dst = src.with_suffix(".pdf")
    md_text = src.read_text(encoding="utf-8")

    has_mermaid = bool(MERMAID_BLOCK_RE.search(md_text))
    if has_mermaid and render_mermaid:
        print(f"  {src.name}: found mermaid diagrams, rendering as PNG...")
    body = _md_to_html(md_text, render_mermaid and has_mermaid)

    html = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    HTML(string=html, base_url=str(src.parent)).write_pdf(str(dst))
    return dst


def main():
    targets: list[pathlib.Path] = []
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        if p.is_dir():
            targets.extend(sorted(p.glob("*.md")))
        elif p.suffix == ".md" and p.exists():
            targets.append(p)
        else:
            print(f"Skipping: {arg}", file=sys.stderr)

    if not targets:
        print("Usage: convert.py file.md [file2.md ...] or convert.py dir/")
        sys.exit(1)

    # Check mmdc availability once
    has_mermaid_in_any = any(
        MERMAID_BLOCK_RE.search(t.read_text(encoding="utf-8")) for t in targets
    )
    can_render = False
    if has_mermaid_in_any:
        print("  Checking mermaid-cli availability...")
        can_render = _has_mmdc()
        if not can_render:
            print("  WARNING: mmdc not available, mermaid blocks will render as code")

    for src in targets:
        dst = convert(src, render_mermaid=can_render)
        print(f"  {src} -> {dst} ({dst.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
