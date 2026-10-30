# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus scale-run hook (generic CLI).

Intended to be invoked against a corpus root supplied at runtime. It writes all
artifacts to ``--out-dir`` and emits typed references only — never private note
content. The public formal repository uses this only on synthetic fixtures; the
private evidence branch points it at the frozen WAIC corpus.

Example:
    python -m tools.adaptive_relational_runtime.corpus.cli \
        --corpus-root /path/to/WAIC-2026-知识库 \
        --out-dir /private/evidence/r3-run \
        --frozen-ref 50393395ce9e6a1592787d991e630e364c5b6a09 \
        --shard-count 16
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .driver import run_full


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="R3 corpus scale-run (generic, boundary-safe)")
    ap.add_argument("--corpus-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frozen-ref", required=True)
    ap.add_argument("--shard-count", type=int, default=16)
    ap.add_argument("--max-retries", type=int, default=2)
    args = ap.parse_args(argv)

    if not Path(args.corpus_root).exists():
        print(f"corpus-root not found: {args.corpus_root}", file=sys.stderr)
        return 2

    summary = run_full(
        corpus_root=args.corpus_root,
        out_dir=args.out_dir,
        frozen_corpus_ref=args.frozen_ref,
        shard_count=args.shard_count,
        max_retries=args.max_retries,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
