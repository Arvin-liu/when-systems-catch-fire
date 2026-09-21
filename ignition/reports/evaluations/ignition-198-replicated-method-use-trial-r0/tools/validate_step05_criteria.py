#!/usr/bin/env python3
"""Validate the sealed, predeclared Task198 replicate decision logic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ROOT / "criteria" / "replicated-method-use-criteria.json"
DIGEST = ROOT / "criteria" / "replicated-method-use-criteria.sha256"
REPO = ROOT.parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
    assert criteria["sealed"] is True
    assert criteria["visibility"] == "EVALUATOR_ONLY"
    assert criteria["successor_visible"] is False
    assert criteria["builder_execution"] == "NOT_RUN"
    assert criteria["successor_execution"] == "NOT_RUN"
    assert criteria["evaluator_execution"] == "NOT_RUN"
    assert criteria["method_trace_schema"]["reuse_status"] == "METHOD_USE_TRACE_R0_REUSED_NO_SECOND_SCHEMA"
    assert criteria["replicate_unit"]["unit"] == "conversation"
    assert criteria["replicate_unit"]["cases_per_conversation"] == 3
    assert criteria["replicate_unit"]["case_order_is_predeclared"] is True
    assert criteria["replicate_unit"]["order_is_outcome_adaptive"] is False
    codes = {item["code"] for item in criteria["replication_disposition_rules"].values()}
    assert codes == {
        "REPLICATED_METHOD_USE_SIGNAL_SUPPORTED",
        "REPLICATED_METHOD_USE_SIGNAL_PARTIAL",
        "REPLICATED_METHOD_USE_SIGNAL_NOT_SUPPORTED",
    }
    assert criteria["fixed_interpretation_ceiling"] == "REPLICATED_CONDITION_ASSOCIATION_ONLY_NOT_CAUSAL_EFFECT"
    assert set(criteria["not_computed"]) >= {"probability", "effect_size", "causal_effect"}
    assert criteria["canonical_claim_ids"] == []
    assert criteria["canonical_promotion"] == "NONE"
    assert sha256(DIGEST) != sha256(CRITERIA)
    recorded = DIGEST.read_text(encoding="utf-8").split()[0]
    assert recorded == sha256(CRITERIA)

    for packet_name in ("facts-a", "facts-b", "method-a", "method-b", "broken-a", "broken-b"):
        packet = json.loads((ROOT / "packets" / packet_name / "packet-manifest.json").read_text(encoding="utf-8"))
        assert not any("criteria" in item["path"].lower() for item in packet["read_allowlist"])
        assert not any("evaluator" in item["path"].lower() for item in packet["read_allowlist"])

    print("TASK198_STEP05_PREDECLARED_REPLICATION_LOGIC_SEALED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
