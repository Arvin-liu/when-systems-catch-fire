#!/usr/bin/env python3
"""fulltext_fetcher.py — Download full-text files from legitimate OA locations.

Uses curl subprocess for reliable transfer and streaming. Records SHA256, file
size, content type, and PDF page count. No credentials are stored.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import urllib.request

CACHE_DIR = Path(os.environ.get("FULLTEXT_CACHE_DIR", ".cache/fulltext")).expanduser()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = os.environ.get(
    "FULLTEXT_USER_AGENT",
    "ignition-fulltext-resolver/1.0 (mailto:research@ignition.local)",
)


def _run_curl(url: str, out_path: Path, timeout: int = 60) -> dict[str, Any]:
    """Download url to out_path with curl; return status dict."""
    cmd = [
        "curl", "-L", "--fail", "--retry", "2", "--max-time", str(timeout),
        "-A", USER_AGENT, "-o", str(out_path), "-w",
        "HTTP=%{http_code}\nSIZE=%{size_download}\nCT=%{content_type}\nURL=%{url_effective}\n",
        url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "curl_timeout", "http_status": None}
    except FileNotFoundError:
        return {"ok": False, "error": "curl_not_found", "http_status": None}

    stderr = proc.stderr.strip()
    if proc.returncode != 0:
        return {"ok": False, "error": stderr or f"curl_exit_{proc.returncode}", "http_status": None}

    info = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k.lower()] = v
    return {
        "ok": True,
        "http_status": int(info.get("http", 0)),
        "size": int(info.get("size", 0)),
        "content_type": info.get("ct", ""),
        "effective_url": info.get("url", url),
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _pdf_page_count(path: Path) -> int | None:
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return len(reader.pages)
    except Exception:
        pass
    try:
        proc = subprocess.run(
            ["pdfinfo", str(path)], capture_output=True, text=True, timeout=10
        )
        for line in proc.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
    except Exception:
        pass
    return None


def _html_has_sections(path: Path) -> list[str]:
    """Return list of h2/h3 text found in HTML."""
    import re
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        headers = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", text, re.S | re.I)
        cleaned = []
        for h in headers:
            h = re.sub(r"<[^>]+>", " ", h).strip()
            if h and len(h) < 200:
                cleaned.append(h)
        return cleaned
    except Exception:
        return []


def fetch(url: str, source_id: str, provider: str, expected_ext: str | None = None) -> dict[str, Any]:
    """Download a single URL and return a fetch record."""
    ext = expected_ext or (".pdf" if ".pdf" in url.lower() else ".html")
    fname = f"{source_id}_{provider}{ext}"
    out_path = CACHE_DIR / fname

    info = _run_curl(url, out_path)
    info["source_id"] = source_id
    info["provider"] = provider
    info["requested_url"] = url
    info["local_path"] = str(out_path.relative_to(Path.cwd()) if out_path.is_absolute() else out_path)
    info["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if not info["ok"] or info.get("size", 0) == 0:
        info["file_sha256"] = None
        return info

    info["file_sha256"] = _sha256(out_path)

    # Validate PDF magic
    if ext == ".pdf":
        with open(out_path, "rb") as f:
            magic = f.read(5)
        if magic != b"%PDF-":
            info["ok"] = False
            info["error"] = f"bad_pdf_magic: {magic!r}"
            return info
        info["page_count"] = _pdf_page_count(out_path)
        info["sections"] = []
    else:
        info["page_count"] = None
        info["sections"] = _html_has_sections(out_path)

    return info


def fetch_best_candidate(resolution_attempts: list[dict], source_id: str) -> dict[str, Any]:
    """Given resolution attempts, pick the first successful one and download it."""
    for att in resolution_attempts:
        if att.get("status") == "SUCCESS" and att.get("url"):
            ext = ".pdf" if "pdf" in (att.get("content_type") or "").lower() or ".pdf" in att["url"].lower() else ".html"
            return fetch(att["url"], source_id, att.get("provider", "unknown"), ext)
    return {"ok": False, "error": "no_successful_candidate", "source_id": source_id}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 fulltext_fetcher.py <url> <source_id> [provider]")
        sys.exit(1)
    url, source_id = sys.argv[1], sys.argv[2]
    provider = sys.argv[3] if len(sys.argv) > 3 else "manual"
    ext = ".pdf" if ".pdf" in url.lower() else ".html"
    print(json.dumps(fetch(url, source_id, provider, ext), ensure_ascii=False, indent=2))
