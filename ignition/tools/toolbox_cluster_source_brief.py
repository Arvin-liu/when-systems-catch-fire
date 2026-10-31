#!/usr/bin/env python3
"""Print source-pinned article-cluster briefs without creating repository files."""

from __future__ import annotations

import argparse
import json
import sys

from extract_cluster_source_brief import render_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cluster_ids", nargs="+", help="one or more IDs from the checked repository snapshot")
    args = parser.parse_args(argv)
    try:
        receipt = render_receipt(args.cluster_ids)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("SOURCE_BRIEF_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
