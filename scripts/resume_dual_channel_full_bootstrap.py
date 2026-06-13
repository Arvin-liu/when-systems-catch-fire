#!/usr/bin/env python3
"""Resume a dual-channel full bootstrap run."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume dual-channel full bootstrap verification.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()
    return subprocess.call(
        [
            "python3",
            "scripts/run_dual_channel_full_bootstrap.py",
            "--run-id",
            args.run_id,
            "--resume",
            "--rounds",
            str(args.rounds),
        ],
        cwd=REPO_ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
