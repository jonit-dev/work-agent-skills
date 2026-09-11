---
name: md-to-pdf
description: Convert Markdown files to PDF. Use when asked to convert .md files to .pdf, export a markdown document as PDF, or produce a PDF from a markdown briefing/report.
---

# MD to PDF Converter

Converts `.md` files to styled `.pdf` using `python-markdown` + `weasyprint` (both available in the environment). Output file replaces the `.md` extension with `.pdf` in-place.

## When to use the script

Use the bundled script for any conversion. Don't inline the weasyprint logic each time.

```bash
python3 ~/.Codex/skills/md-to-pdf/scripts/convert.py path/to/file.md
# or convert all .md in a directory:
python3 ~/.Codex/skills/md-to-pdf/scripts/convert.py path/to/dir/
```

After conversion, delete the `.md` source if the user only wants the PDF.

## What the script does

- Converts Markdown (with tables and fenced code blocks) to HTML
- **Automatically detects Mermaid diagrams** (`\`\`\`mermaid` blocks) and renders them as PNG images via `mmdc` (mermaid-cli)
- Applies clean print-friendly CSS (Arial 12px, bordered tables, code blocks)
- Writes `<same-name>.pdf` next to the source file
- Prints `src -> dst (N KB)` for each file converted

## Mermaid support

- Mermaid diagrams are rendered to PNG at 2x scale for crisp text
- Uses `npx @mermaid-js/mermaid-cli` (no global install needed)
- Supports all Mermaid diagram types: flowchart, pie, xychart-beta, gantt, sequence, etc.
- If mmdc is unavailable, diagrams fall back to code blocks (no crash)
- **Important**: SVG rendering won't work because weasyprint doesn't support `<foreignObject>` — this script uses PNG to avoid that issue

## Notes

- `weasyprint` and `markdown` are already installed; no pip needed
- Works on single files or whole directories
- Does **not** delete the source `.md` — do that separately if needed
