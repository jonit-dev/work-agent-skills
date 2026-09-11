#!/usr/bin/env python3
"""Inspect, validate, or render XLSX workbooks with LibreOffice."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import tempfile
import time
import zipfile

try:
    import uno
except ImportError as error:
    raise SystemExit(
        "Python UNO is unavailable. Install LibreOffice's python3-uno package."
    ) from error


REQUIRED_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "xl/workbook.xml",
    "xl/styles.xml",
}


def start_office(port: int, profile: pathlib.Path) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [
            "libreoffice",
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation={uno.systemPathToFileUrl(str(profile))}",
            f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def connect(port: int):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local
    )
    last_error: Exception | None = None
    for _ in range(40):
        try:
            context = resolver.resolve(
                f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext"
            )
            return context.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", context
            )
        except Exception as error:
            last_error = error
            time.sleep(0.25)
    raise RuntimeError(f"could not connect to LibreOffice: {last_error}")


def workbook_snapshot(path: pathlib.Path, max_rows: int, max_columns: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="xlsx-workbooks-") as temp:
        profile = pathlib.Path(temp) / "profile"
        port = 25000 + (os.getpid() % 1000)
        office = start_office(port, profile)
        document = None
        try:
            desktop = connect(port)
            hidden = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
            hidden.Name = "Hidden"
            hidden.Value = True
            read_only = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
            read_only.Name = "ReadOnly"
            read_only.Value = True
            document = desktop.loadComponentFromURL(
                uno.systemPathToFileUrl(str(path.resolve())),
                "_blank",
                0,
                (hidden, read_only),
            )
            if document is None:
                raise RuntimeError("LibreOffice returned no document")
            sheets = []
            for sheet_name in document.Sheets.ElementNames:
                sheet = document.Sheets.getByName(sheet_name)
                cursor = sheet.createCursor()
                cursor.gotoEndOfUsedArea(True)
                address = cursor.RangeAddress
                preview = []
                formulas = []
                row_limit = min(address.EndRow + 1, max_rows)
                column_limit = min(address.EndColumn + 1, max_columns)
                for row_index in range(row_limit):
                    row = []
                    for column_index in range(column_limit):
                        cell = sheet.getCellByPosition(column_index, row_index)
                        row.append(cell.String)
                        if cell.Formula and cell.Formula != cell.String:
                            formulas.append(
                                {
                                    "cell": cell.AbsoluteName,
                                    "formula": cell.Formula,
                                    "display": cell.String,
                                }
                            )
                    preview.append(row)
                sheets.append(
                    {
                        "name": sheet_name,
                        "used_range": {
                            "start_row": address.StartRow + 1,
                            "start_column": address.StartColumn + 1,
                            "end_row": address.EndRow + 1,
                            "end_column": address.EndColumn + 1,
                        },
                        "preview": preview,
                        "formulas": formulas,
                        "preview_truncated": (
                            address.EndRow + 1 > max_rows
                            or address.EndColumn + 1 > max_columns
                        ),
                    }
                )
            return {"path": str(path.resolve()), "sheets": sheets}
        finally:
            if document is not None:
                document.close(True)
            office.terminate()
            try:
                office.wait(timeout=5)
            except subprocess.TimeoutExpired:
                office.kill()


def validate_zip(path: pathlib.Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        missing = sorted(REQUIRED_PARTS.difference(archive.namelist()))
        corrupt = archive.testzip()
    return {
        "zip_ok": corrupt is None and not missing,
        "missing_parts": missing,
        "corrupt_part": corrupt,
    }


def render(path: pathlib.Path, output_dir: pathlib.Path) -> pathlib.Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    output = output_dir / f"{path.stem}.pdf"
    if not output.exists():
        raise RuntimeError(f"LibreOffice did not create {output}: {result.stdout}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "validate"):
        command = subparsers.add_parser(name)
        command.add_argument("workbook", type=pathlib.Path)
        command.add_argument("--max-rows", type=int, default=25)
        command.add_argument("--max-columns", type=int, default=15)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("workbook", type=pathlib.Path)
    render_parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()

    workbook = args.workbook.resolve()
    if not workbook.is_file():
        raise SystemExit(f"workbook not found: {workbook}")
    if args.command == "render":
        print(render(workbook, args.output_dir.resolve()))
        return

    snapshot = workbook_snapshot(workbook, args.max_rows, args.max_columns)
    if args.command == "inspect":
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return

    result = validate_zip(workbook)
    result["opened_by_libreoffice"] = bool(snapshot["sheets"])
    result["sheet_count"] = len(snapshot["sheets"])
    result["sheet_names"] = [sheet["name"] for sheet in snapshot["sheets"]]
    result["valid"] = result["zip_ok"] and result["opened_by_libreoffice"]
    print(json.dumps(result, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
