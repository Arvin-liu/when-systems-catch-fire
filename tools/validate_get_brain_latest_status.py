#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "GET-BRAIN-LATEST.md"
JSON = ROOT / "data/get-brain/latest-status.json"

SECRET_PATTERNS = [
    re.compile(r"gh[po]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*\S+"),
    re.compile(r"(?i)token\s*[:=]\s*\S+"),
    re.compile(r"(?i)authorization\s*[:=]\s*\S+"),
]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    if not MD.exists():
        fail("missing GET-BRAIN-LATEST.md")
    if not JSON.exists():
        fail("missing data/get-brain/latest-status.json")

    md = MD.read_text(encoding="utf-8")
    data = json.loads(JSON.read_text(encoding="utf-8"))

    title = data.get("title")
    if not title or not title.startswith("点火项目最新现状｜"):
        fail("bad json title")
    if title not in md:
        fail("markdown title mismatch")
    if data.get("review_status") != "PENDING_GPT_REVIEW":
        fail("review_status must remain PENDING_GPT_REVIEW")
    if "PENDING_GPT_REVIEW" not in md:
        fail("markdown review status mismatch")
    if "MERGED_AUTHORITY" not in md or "OPEN_PR" not in md:
        fail("status categories missing in markdown")
    if "MERGED_AUTHORITY" not in data.get("status", {}):
        fail("status categories missing in json")

    text = md + "\n" + JSON.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(f"secret pattern matched: {pattern.pattern}")

    latest_entries = [p for p in ROOT.rglob("*") if p.name == "GET-BRAIN-LATEST.md"]
    if len(latest_entries) != 1:
        fail(f"expected exactly one GET-BRAIN-LATEST.md, found {len(latest_entries)}")

    print("OK")


if __name__ == "__main__":
    main()

