#!/usr/bin/env python3
"""Validate Task198 evaluator-only sealed package without running evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEALED = ROOT / "evaluator-sealed"
CRITERIA = SEALED / "criteria.json"
PACKAGE = SEALED / "package-manifest.json"
REPO = ROOT.parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert criteria["sealed"] is True
    assert criteria["visibility"] == "EVALUATOR_ONLY"
    assert criteria["successor_visible"] is False
    assert criteria["builder_execution"] == "NOT_RUN"
    assert criteria["successor_execution"] == "NOT_RUN"
    assert criteria["evaluator_execution"] == "NOT_RUN"
    assert criteria["predeclared_logic_ref"]["sha256"] == "34723cdc82873215e223ce3216bc8990c2ee91985d3196c85e19de2bac5f3732"
    assert criteria["replicate_interpretation"]["conversation_level_repeated_runs"] is True
    assert criteria["replicate_interpretation"]["cases_within_conversation_non_independent"] is True
    assert criteria["replicate_interpretation"]["random_seed_control"] is False
    assert criteria["replicate_interpretation"]["condition_assignment"] == "predeclared_and_not_outcome_adaptive"
    assert criteria["replicate_interpretation"]["repeated_consistency_is_causal_proof"] is False
    dimension_ids = [item["dimension_id"] for item in criteria["evaluation_dimensions"]]
    assert dimension_ids == [
        "ACROSS-CASE-CONSISTENCY",
        "ACROSS-REPLICATE-CONSISTENCY",
        "CASE-ORDER-SENSITIVITY",
        "WORDING-TEMPLATE-IMITATION",
        "FALSE-POSITIVE-COMPLETION",
        "SOURCE-PROVENANCE-FIDELITY",
        "UNCERTAINTY-PRESERVATION",
    ]
    assert criteria["decision_logic"]["association_ceiling"] == "REPLICATED_CONDITION_ASSOCIATION_ONLY_NOT_CAUSAL_EFFECT"
    assert criteria["decision_logic"]["effect_size"] == "NOT_COMPUTED"
    assert criteria["decision_logic"]["probability"] == "NOT_COMPUTED"
    assert criteria["canonical_claim_ids"] == []
    assert criteria["canonical_promotion"] == "NONE"

    assert package["sealed"] is True
    assert package["successor_visible"] is False
    assert package["criteria_sha256"] == sha256(CRITERIA)
    assert package["predeclared_logic_sha256"] == criteria["predeclared_logic_ref"]["sha256"]
    assert len(package["packet_manifests"]) == 6
    for entry in package["packet_manifests"]:
        path = REPO / entry["path"]
        assert path.is_file()
        assert sha256(path) == entry["sha256"], entry["path"]
    assert package["future_result"] == "NOT_PRESENT"
    assert package["successor_execution"] == "NOT_RUN"
    assert package["evaluator_execution"] == "NOT_RUN"

    assert SEALED.joinpath("criteria.sha256").read_text(encoding="utf-8").split()[0] == sha256(CRITERIA)
    assert SEALED.joinpath("package-manifest.sha256").read_text(encoding="utf-8").split()[0] == sha256(PACKAGE)
    print("TASK198_STEP06_EVALUATOR_PACKAGE_SEALED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
