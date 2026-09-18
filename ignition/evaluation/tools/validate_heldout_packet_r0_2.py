#!/usr/bin/env python3
"""Validate the R0.2 held-out packet and exact separated surface manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

IGNITION_ROOT = Path(__file__).resolve().parents[2]
PACKET_BUILDER = IGNITION_ROOT / "evaluation" / "heldout" / "r0.2"
sys.path.insert(0, str(PACKET_BUILDER))

import build_packet_manifest  # noqa: E402


def main() -> int:
    manifest = build_packet_manifest.MANIFEST
    build_packet_manifest.validate_packet(json.loads(manifest.read_text(encoding="utf-8")))
    print("HELDOUT_R0_2_PACKET_VALID; COGNITIVE_AND_OPERATIONAL_SURFACES_SEPARATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
