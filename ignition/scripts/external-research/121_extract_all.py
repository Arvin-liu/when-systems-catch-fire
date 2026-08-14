#!/usr/bin/env python3
"""121_extract_all.py — Extract text snippets from all fetched full-text files."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

BASE = Path("/tmp/wscf-121")
CACHE = BASE / ".cache" / "fulltext"
OUT = BASE / "data" / "external-research" / "121-fulltext-resolver"


def pdf_text(path: Path) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        parts = []
        for i, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            parts.append(f"\n--- Page {i+1} ---\n{t}")
        return "\n".join(parts)
    except Exception:
        pass
    try:
        proc = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            return proc.stdout
    except Exception:
        pass
    return ""


def html_text(path: Path) -> str:
    import re
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def extract_headers(text: str) -> list[str]:
    headers = []
    for line in text.splitlines():
        line = line.strip()
        if line and (line.isupper() or re.match(r"^\d+(\.\d+)*\s+", line) or line in ["Abstract", "Introduction", "Related Work", "Conclusion", "Experiments", "Methods"]):
            if 5 < len(line) < 120:
                headers.append(line)
    return headers[:20]


def main():
    records = [json.loads(line) for line in open(OUT / "121-fetch-records.jsonl") if line.strip()]
    extracts = []
    for rec in records:
        if not rec.get("ok"):
            continue
        path = BASE / rec.get("local_path", "")
        if not path.exists():
            continue
        ext = path.suffix.lower()
        if ext == ".pdf":
            text = pdf_text(path)
        elif ext in (".html", ".htm"):
            text = html_text(path)
        else:
            continue
        words = text.split()
        extracts.append({
            "source_id": rec["source_id"],
            "title": rec["title"],
            "source_family": rec["source_family"],
            "format": ext[1:],
            "word_count": len(words),
            "first_2000_words": " ".join(words[:2000]),
            "pages_1_3": " ".join(text.split("--- Page 1 ---")[-1].split("--- Page 4 ---")[0].split()[:1000]) if ext == ".pdf" else "",
            "headers": extract_headers(text)[:20],
        })
    (OUT / "121-extracts.jsonl").write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in extracts), encoding="utf-8")
    print(f"Extracted {len(extracts)} sources")


if __name__ == "__main__":
    main()
