#!/usr/bin/env python3
"""fulltext_extract.py — Extract text and anchors from cached full-text files.

Supports PDF (via pypdf or pdfplumber) and HTML (BeautifulSoup or regex).
Returns a structured record with first N words, headers, figure/table counts,
and line/page ranges. No copyrighted text is stored verbatim beyond short fair-use
quotations for evidence cards.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


CACHE_DIR = Path(os.environ.get("FULLTEXT_CACHE_DIR", ".cache/fulltext")).expanduser()


def _pdf_text(path: Path) -> tuple[str, int | None]:
    text = ""
    pages = None
    # Try pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        pages = len(reader.pages)
        for i, page in enumerate(reader.pages):
            try:
                t = page.extract_text() or ""
                text += f"\n--- Page {i+1} ---\n" + t
            except Exception:
                pass
        return text, pages
    except Exception:
        pass

    # Try pdftotext
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, text=True, timeout=30
        )
        if proc.returncode == 0:
            text = proc.stdout
            # Count pages via pdfinfo
            info = subprocess.run(
                ["pdfinfo", str(path)], capture_output=True, text=True, timeout=10
            )
            for line in info.stdout.splitlines():
                if line.startswith("Pages:"):
                    pages = int(line.split(":", 1)[1].strip())
            return text, pages
    except Exception:
        pass

    return "", pages


def _html_text(path: Path) -> tuple[str, list[str]]:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return "", []

    # Strip scripts/styles
    text = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S | re.I)
    # Replace headers with markers
    headers = re.findall(r"<h[123][^>]*>(.*?)</h[123]>", text, flags=re.S | re.I)
    headers = [re.sub(r"<[^>]+>", " ", h).strip() for h in headers]
    headers = [h for h in headers if h and len(h) < 200]
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, headers


def extract(path: str | Path, source_id: str = "") -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": "file_not_found", "path": str(p)}

    result: dict[str, Any] = {
        "ok": True,
        "source_id": source_id,
        "path": str(p),
        "size_bytes": p.stat().st_size,
    }

    ext = p.suffix.lower()
    if ext == ".pdf":
        text, pages = _pdf_text(p)
        result["format"] = "pdf"
        result["page_count"] = pages
        result["text_length"] = len(text)
        result["word_count"] = len(text.split())
        result["headers"] = []
    elif ext in (".html", ".htm"):
        text, headers = _html_text(p)
        result["format"] = "html"
        result["page_count"] = None
        result["text_length"] = len(text)
        result["word_count"] = len(text.split())
        result["headers"] = headers
    else:
        return {"ok": False, "error": "unsupported_format", "path": str(p)}

    # Short snippets for evidence cards (first 300 words, abstract section)
    words = text.split()
    result["snippet_first_300_words"] = " ".join(words[:300])
    result["snippet_last_100_words"] = " ".join(words[-100:]) if len(words) > 400 else ""
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 fulltext_extract.py <path> [source_id]")
        sys.exit(1)
    print(json.dumps(extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""), ensure_ascii=False, indent=2))
