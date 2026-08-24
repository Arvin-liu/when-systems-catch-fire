"""Validate the Amendment-01 local executor census without external access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_federation.local_executor_census import LocalExecutorCensusError, validate_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/operations/iterations/138/local-executor-census-r1.json"))
    args = parser.parse_args(argv)
    try:
        summary = validate_path(args.path)
    except LocalExecutorCensusError as exc:
        parser.error(str(exc))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
