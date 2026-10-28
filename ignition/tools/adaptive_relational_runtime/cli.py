# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""End-to-end demo of the ARR deterministic runtime skeleton (CLI entry).

Constructs a minimal valid Source + Observation inline, runs the closed loop,
and prints the runtime-envelope receipt (validated against
runtime-envelope.schema.json). Read-only over schemas/registries; no real
execution, network, or external write. Run with:

    python -m tools.adaptive_relational_runtime.cli
"""
from __future__ import annotations

import json
import sys

from . import canonical
from . import runtime


def _minimal_source_and_observation() -> tuple[dict, dict]:
    t = "2026-07-24T00:00:00Z"
    source = {
        "record_kind": "Source",
        "schema_version": "arr-r1.0",
        "scope": {"domain": "demo", "context_ref": None},
        "provenance": ["inline-demo"],
        "explicitness": "EXPLICIT",
        "claim_ceiling": "SECONDARY",
        "uncertainty": "none stated",
        "alternatives": [],
        "lifecycle": {"state": "OBSERVED", "entered_at_scope": None, "transition_ref": None},
        "time": {
            "publication_time": None,
            "publication_time_status": "ABSENT",
            "ingestion_time": t,
            "ingestion_time_status": "OK",
        },
        "extensions": {},
        "source_type": "text",
        "content_hash": canonical.sha256_hex("demo source content"),
        "locator": {"ref_type": "url", "ref_value": "https://example.com/demo"},
        "tier": "SECONDARY_DERIVED",
        "rights_boundary": {
            "classification": "public",
            "republication": "allowed",
            "paraphrase": None,
            "attribution_ref": None,
            "notes": None,
        },
    }
    source["record_id"] = canonical.record_id("src", source)

    observation = {
        "record_kind": "Observation",
        "schema_version": "arr-r1.0",
        "scope": {"domain": "demo", "context_ref": None},
        "provenance": ["inline-demo"],
        "explicitness": "EXPLICIT",
        "claim_ceiling": "SECONDARY",
        "uncertainty": "none stated",
        "alternatives": [],
        "lifecycle": {"state": "OBSERVED", "entered_at_scope": None, "transition_ref": None},
        "time": {
            "observation_time": t,
            "observation_time_status": "OK",
            "ingestion_time": t,
            "ingestion_time_status": "OK",
        },
        "extensions": {},
        "source_ref": source["record_id"],
        "observer": "demo-collector",
        "raw_excerpt": {"kind": "inline", "value": "demo excerpt"},
        "collection_metadata": {"method": "manual", "tool_ref": "demo", "parameters": {}},
    }
    observation["record_id"] = canonical.record_id("obs", observation)
    return source, observation


def main() -> int:
    # Inline canonical reorder-invariance self-check (not a committed test file).
    if not canonical.reorder_invariance_check():
        print("canonical reorder-invariance: FAIL")
        return 1
    print("canonical reorder-invariance: PASS")

    source, observation = _minimal_source_and_observation()
    engine = runtime.ARRRuntime()
    envelope = engine.run(source, observation)

    print("\n== runtime stages ==")
    for stage in engine.stages:
        print(f"  {stage['stage']}: ok={stage['ok']}")

    print("\n== runtime-envelope receipt (validated) ==")
    print(json.dumps(envelope, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
