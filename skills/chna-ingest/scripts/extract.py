"""Extract structured content from a .docx file into citation-ready JSON.

Each emitted chunk carries enough metadata to be cited later:
- source_file: basename of the .docx
- chunk_id: stable within a file (e.g. "p:42", "t:3:1:0")
- kind: paragraph | heading | table_cell
- heading_path: list of ancestor headings, root-first
- style: Word style name (raw, useful for downstream heuristics)
- text: the chunk's text content

Chunks with empty text are dropped. Downstream agents are responsible
for classifying chunks as quotes, statistics, methodology, etc.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator

HEADING_RE = re.compile(r"^Heading\s+(\d+)$", re.IGNORECASE)


def _load_docx():
    try:
        from docx import Document
        return Document
    except ImportError:
        print(
            "error: python-docx is required. Install with: pip install -r requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _heading_level(style_name: str | None) -> int | None:
    if not style_name:
        return None
    match = HEADING_RE.match(style_name)
    return int(match.group(1)) if match else None


def _iter_chunks(doc, source_file: str) -> Iterator[dict]:
    heading_stack: list[tuple[int, str]] = []

    for idx, para in enumerate(doc.paragraphs):
        text = (para.text or "").strip()
        if not text:
            continue
        style = para.style.name if para.style else None
        level = _heading_level(style)

        if level is not None:
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            yield {
                "source_file": source_file,
                "chunk_id": f"p:{idx}",
                "kind": "heading",
                "heading_path": [h for _, h in heading_stack],
                "style": style,
                "text": text,
            }
            heading_stack.append((level, text))
        else:
            yield {
                "source_file": source_file,
                "chunk_id": f"p:{idx}",
                "kind": "paragraph",
                "heading_path": [h for _, h in heading_stack],
                "style": style,
                "text": text,
            }

    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                text = (cell.text or "").strip()
                if not text:
                    continue
                yield {
                    "source_file": source_file,
                    "chunk_id": f"t:{t_idx}:{r_idx}:{c_idx}",
                    "kind": "table_cell",
                    "heading_path": [h for _, h in heading_stack],
                    "style": None,
                    "text": text,
                }


def extract(path: Path) -> dict:
    Document = _load_docx()
    doc = Document(str(path))
    chunks = list(_iter_chunks(doc, path.name))
    return {
        "source_file": path.name,
        "source_path": str(path),
        "chunks": chunks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help=".docx file to extract")
    parser.add_argument(
        "-o", "--output", type=Path, help="Write JSON here instead of stdout"
    )
    args = parser.parse_args()

    if not args.docx.exists():
        print(f"error: {args.docx} does not exist", file=sys.stderr)
        return 1

    payload = extract(args.docx)
    blob = json.dumps(payload, indent=2, ensure_ascii=False)

    if args.output:
        args.output.write_text(blob, encoding="utf-8")
    else:
        print(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
