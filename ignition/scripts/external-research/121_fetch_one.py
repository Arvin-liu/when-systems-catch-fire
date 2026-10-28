#!/usr/bin/env python3
"""121_fetch_one.py — Fetch a single source by ID, with hard timeout."""

from __future__ import annotations

import hashlib
import json
import re
import signal
import socket
import ssl
import sys
import time
import urllib.request
from pathlib import Path

socket.setdefaulttimeout(22)
BASE = Path(__file__).resolve().parent.parent.parent
CACHE = BASE / ".cache" / "fulltext"
CACHE.mkdir(parents=True, exist_ok=True)

USER_AGENT = "ignition-fulltext-resolver/1.0 (mailto:research@ignition.local)"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def _sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _pdf_pages(path: Path) -> int | None:
    try:
        import pypdf
        return len(pypdf.PdfReader(str(path)).pages)
    except Exception:
        pass
    try:
        import subprocess
        proc = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=10)
        for line in proc.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
    except Exception:
        pass
    return None


def _html_headers(path: Path) -> list[str]:
    import re
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        headers = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", text, re.S | re.I)
        return [re.sub(r"<[^>]+>", " ", h).strip() for h in headers if re.sub(r"<[^>]+>", " ", h).strip() and len(h) < 200]
    except Exception:
        return []


def direct_url(src: dict) -> tuple[str, str, str] | None:
    url = src.get("url", "")
    doi = src.get("doi_or_identifier", "")

    arxiv_id = None
    if doi.lower().startswith("arxiv:") or re.match(r"^\d{4}\.\d{4,5}$", doi, re.I):
        arxiv_id = doi.replace("arXiv:", "").replace("arxiv:", "").strip()
    elif url and "arxiv.org" in url:
        m = re.search(r"arxiv\.org/(?:abs|html|pdf)/(\d+\.\d+)", url, re.I)
        if m:
            arxiv_id = m.group(1)
    if arxiv_id:
        return ("arxiv_pdf", f"https://arxiv.org/pdf/{arxiv_id}.pdf", ".pdf")

    if "openreview.net" in url and "forum?id=" in url:
        m = re.search(r"forum\?id=([A-Za-z0-9_-]+)", url)
        if m:
            return ("openreview_pdf", f"https://openreview.net/pdf?id={m.group(1)}", ".pdf")

    if "proceedings.mlr.press" in url and "/v" in url:
        m = re.search(r"proceedings\.mlr\.press/[^\s\"']+", url)
        if m:
            base = "https://" + m.group(0).rstrip("/")
            # If URL already points to a PDF, strip .pdf to get directory, then add /slug.pdf
            if base.endswith(".pdf"):
                base = base[:-4]
            if base.endswith(".html"):
                base = base[:-5]
            m2 = re.search(r"/v(\d+)/([^/]+)$", base)
            if m2:
                slug = m2.group(2)
                return ("pmlr", base + "/" + slug + ".pdf", ".pdf")
            return ("pmlr", base + ".pdf", ".pdf")

    if "proceedings.neurips.cc" in url or "papers.neurips.cc" in url:
        if url.endswith("-Paper.pdf") or url.endswith("-Paper-Conference.pdf"):
            return ("neurips_pdf", url, ".pdf")
        return ("neurips_url", url, ".html")

    if "aclanthology.org" in url:
        if url.endswith(".pdf"):
            return ("acl_pdf", url, ".pdf")
        return ("acl", url + ".pdf" if not url.endswith("/") else url.rstrip("/") + ".pdf", ".pdf")

    if url.lower().endswith(".pdf"):
        return ("direct_pdf", url, ".pdf")

    return ("source_url", url, ".html")


def main():
    sid = sys.argv[1]
    registry = BASE / "data" / "external-research" / "120-function-paradigm-atlas" / "120-function-source-registry.jsonl"
    sources = [json.loads(line) for line in registry.read_text().splitlines() if line.strip()]
    src = next(s for s in sources if s["source_id"] == sid)
    cand = direct_url(src)
    if not cand:
        print(json.dumps({"source_id": sid, "ok": False, "error": "no_direct_candidate"}, ensure_ascii=False))
        return
    provider, url, ext = cand
    out = CACHE / f"{sid}_{provider}{ext}"
    rec = {"source_id": sid, "title": src["title"], "source_family": src["source_family"], "provider": provider, "requested_url": url, "ext": ext, "ok": False}
    def _alarm_handler(signum, frame):
        raise TimeoutError("fetch_timeout")
    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(25)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            data = r.read()
        rec["ok"] = True
        rec["http_status"] = r.status
        rec["content_type"] = dict(r.headers).get("Content-Type", "")
        rec["effective_url"] = r.geturl()
        rec["size"] = len(data)
        out.write_bytes(data)
        rec["file_sha256"] = _sha256(data)
        rec["local_path"] = str(out.relative_to(BASE))
        rec["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if ext == ".pdf":
            if data[:5] != b"%PDF-":
                rec["ok"] = False
                rec["error"] = "bad_pdf_magic"
            else:
                rec["page_count"] = _pdf_pages(out)
                rec["headers"] = []
        else:
            rec["headers"] = _html_headers(out)
    except urllib.error.HTTPError as e:
        rec["error"] = str(e.reason)[:200]
        rec["http_status"] = e.code
    except Exception as e:
        rec["error"] = str(e)[:200]
    finally:
        signal.alarm(0)
    print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
