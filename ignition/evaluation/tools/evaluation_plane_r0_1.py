#!/usr/bin/env python3
"""Typed evaluation evidence and explicit adjudication boundary for R0.1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "evaluation" / "schemas"
ARTIFACT_SCHEMA = SCHEMAS / "evaluation-evidence-r0.1.schema.json"
TRANSITION_SCHEMA = SCHEMAS / "evaluation-promotion-transition-r0.1.schema.json"
ARTIFACT_KINDS = {
    "EVALUATION_RESULT",
    "EVALUATOR_METHOD",
    "BLIND_CHECKPOINT",
    "CONTAMINATION_DISCLOSURE",
    "ADJUDICATION_RECEIPT",
    "HELD_OUT_SUCCESSOR_RESULT",
}


def _validate(instance: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - CI installs jsonschema
        raise ValueError("jsonschema is required for Evaluation Plane validation") from exc
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "$"
        raise ValueError(f"{schema_path.name} at {location}: {first.message}")


def validate_evidence_artifact(artifact: dict[str, Any]) -> None:
    _validate(artifact, ARTIFACT_SCHEMA)
    if artifact["artifact_kind"] not in ARTIFACT_KINDS:
        raise ValueError("unknown Evaluation Evidence artifact kind")


def adjudication_boundary(
    artifact: dict[str, Any],
    transition: dict[str, Any] | None = None,
    *,
    authorized_transitions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Describe a possible state transition; never write a canonical registry."""
    validate_evidence_artifact(artifact)
    if transition is None:
        return {
            "state": "EVALUATION_EVIDENCE",
            "promotion": "NO_AUTOMATIC_PROMOTION",
            "canonicalized": False,
            "side_effects": [],
        }

    _validate(transition, TRANSITION_SCHEMA)
    if authorized_transitions is None or authorized_transitions.get(transition["transition_id"]) != transition["authorization"]["authorization_ref"]:
        raise ValueError("explicit transition authorization reference is not verified")
    if transition["source_artifact_id"] != artifact["artifact_id"]:
        raise ValueError("promotion source artifact id does not match")
    if transition["source_sha256"] != artifact["source"]["sha256"]:
        raise ValueError("promotion source hash does not match")
    return {
        "state": "ADJUDICATION_CANDIDATE_ONLY",
        "promotion": "EXPLICIT_AUTHORIZED_TRANSITION",
        "canonicalized": False,
        "side_effects": [],
        "authorization_ref": transition["authorization"]["authorization_ref"],
    }


def validate_contract(contract_path: Path | None = None) -> None:
    path = contract_path or ROOT / "evaluation" / "evaluation-plane-contract-r0.1.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("object_type") != "EVALUATION_EVIDENCE":
        raise ValueError("evaluation plane object type drift")
    if contract.get("promotion_boundary", {}).get("automatic_promotion") is not False:
        raise ValueError("automatic evaluation promotion is forbidden")
    if contract.get("promotion_boundary", {}).get("to") != "ADJUDICATION_CANDIDATE_ONLY":
        raise ValueError("only an adjudication candidate is a permitted transition target")
    if contract.get("promotion_boundary", {}).get("authorization_reference_must_be_verified_by_existing_authority") is not True:
        raise ValueError("promotion requires verification by an existing authority source")
    if set(contract.get("artifact_kinds", [])) != ARTIFACT_KINDS:
        raise ValueError("evaluation artifact-kind vocabulary drift")


if __name__ == "__main__":
    validate_contract()
    print("EVALUATION_PLANE_CONTRACT_VALID; AUTOMATIC_PROMOTION=FALSE")
