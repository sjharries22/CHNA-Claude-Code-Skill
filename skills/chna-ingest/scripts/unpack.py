"""Resolve an input path to a list of .docx files.

Accepts a file (.docx or .zip) or a directory. Zip archives are extracted
into a sibling directory next to the archive so paths stay stable across
runs. Nested zips are walked one level deep.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


def _is_docx(path: Path) -> bool:
    return path.suffix.lower() == ".docx" and not path.name.startswith("~$")


def _extract_zip(archive: Path) -> Path:
    dest = archive.with_suffix("")
    dest.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)
    return dest


def collect(root: Path) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)

    if root.is_file():
        if _is_docx(root):
            return [root]
        if root.suffix.lower() == ".zip":
            return collect(_extract_zip(root))
        raise ValueError(f"Unsupported file type: {root}")

    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            if _is_docx(path):
                found.append(path)
            elif path.suffix.lower() == ".zip":
                found.extend(collect(_extract_zip(path)))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="File or directory to scan")
    args = parser.parse_args()

    try:
        docs = collect(args.path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps([str(p) for p in docs], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
