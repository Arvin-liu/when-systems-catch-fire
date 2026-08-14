#!/usr/bin/env python3
"""Materialize or verify stage-snapshot actor_ref enums from the actor registry."""

from __future__ import annotations

import argparse
import json

from stage_snapshot_contract import materialize_actor_schema_refs, validate_actor_contract_sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = materialize_actor_schema_refs(check=args.check)
    if args.check:
        result.update(validate_actor_contract_sources())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
