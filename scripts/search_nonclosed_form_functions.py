#!/usr/bin/env python3
"""Scan functions for likely analytic-solution candidates."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from object_classification_utils import write_json, write_text


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
OUT_JSON = REPO_ROOT / "data/analytic-solutions/nonclosed-form-candidates.json"
OUT_MD = REPO_ROOT / "data/rebuild/analytic-solution-derivation-report.md"


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan for analytic solution candidates.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    functions = read_json(FUNCTIONS_JSON, [])
    candidates = []
    for item in functions:
        title = item.get("title_text") or ""
        if "解析解" in title or re.search(r"=√e|sqrt\\(e\\)", title):
            candidates.append(
                {
                    "function_id": item.get("id"),
                    "title": title,
                    "reason": "Title explicitly denotes a closed-form analytic solution.",
                    "source_page": item.get("links", {}).get("human_page", ""),
                }
            )

    payload = {
        "generated_at": date.today().isoformat(),
        "scanned_functions": len(functions),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    write_json(OUT_JSON, payload)
    write_text(
        OUT_MD,
        "\n".join(
            [
                "# Analytic Solution Derivation Report",
                "",
                f"- Generated at: {payload['generated_at']}",
                f"- Scanned functions: {payload['scanned_functions']}",
                f"- Candidate count: {payload['candidate_count']}",
                "",
                "## Candidates",
            ]
            + [f"- {item['function_id']} {item['title']}: {item['reason']}" for item in candidates]
        )
        + "\n",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
