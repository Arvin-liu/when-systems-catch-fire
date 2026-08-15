#!/usr/bin/env python3
"""Validate the declarative Pack Registry/Bus R1 boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_runtime.pack_registry import PackBus, PackLoader, PackRegistry, PackRegistryError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packs-root", type=Path, default=ROOT / "packs")
    args = parser.parse_args()
    try:
        registry = PackRegistry.discover(args.packs_root)
        validation = registry.validate()
        if validation["status"] != "PASS":
            print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
            return 1
        loader = PackLoader(registry)
        loaded = loader.load_all()
        bus = PackBus(registry, loader)
        result = {
            **validation,
            "loaded_pack_ids": [item.manifest.pack_id for item in loaded],
            "loaded_health": [item.health for item in loaded],
            "routes": bus.trace(),
            "load_side_effects": "DECLARATIVE_ONLY",
            "authority_boundary": "NO_PERMISSION_OR_TRUTH_AUTHORITY_UPGRADE",
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (PackRegistryError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error_type": type(exc).__name__, "summary": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
