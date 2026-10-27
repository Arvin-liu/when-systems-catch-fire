#!/usr/bin/env python3
"""Fail-closed validator for the Task172 Gate R routing sidecar pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.foundation.knowledge_corpus_admission import admission_for_path
from tools.research.validate_task172_gate_t import validate as validate_gate_t


EXPECTED_PARENT_HEAD = "6d704d570827bf8d6ebb65fb65bcdd236056b4d3"
EXPECTED_COMMAND = {
    "repository": "Arvin-liu/1111",
    "ref": "b1fc45fb",
    "path": "agent-commands/IGNITION-20260913-176.md",
    "blob_sha": "98fd25bd1886cf8675992413d6c55d1e09b4502f",
}
GATE_T_REL = Path("data/research/task172-gate-t-unesco-1988")
GATE_R_REL = Path("data/research/task172-gate-r-routing")
OPERATION_REL = Path("data/operations/iterations/172/step04-routing-gate.json")
FUNCTION_REL = Path("data/foundation/function-assets/identity-cards.jsonl")
NONFUNCTION_REL = Path("data/foundation/nonfunction-claims/claim-registry.jsonl")
EXPECTED_COUNTS = {"CLASSIFIED": 182, "MULTIDISCIPLINARY": 26, "OUT_OF_UNESCO_SCOPE": 103, "UNRESOLVED": 439}
EXPECTED_CAPS = {"unesco_field_codes": 2, "unesco_discipline_codes": 3, "asset_role": 3, "collision_use": 4, "topic": 5}
NEGATIVE_USE = {"HISTORICAL_CONTEXT"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate(repo_root: Path) -> None:
    validate_gate_t(repo_root)
    gate_t = repo_root / GATE_T_REL
    gate_r = repo_root / GATE_R_REL
    schema = read_json(gate_r / "routing-schema.json")
    vocabulary = read_json(gate_r / "controlled-vocabulary.json")
    pilot = read_json(gate_r / "precision-pilot.json")
    audit = read_json(gate_r / "precision-audit.json")
    freeze = read_json(gate_r / "source-freeze.json")
    receipt = read_json(gate_r / "build-receipt.json")
    operation = read_json(repo_root / OPERATION_REL)

    assert schema.get("schema") == "task172-gate-r-routing-schema-v1", "wrong routing schema"
    assert vocabulary.get("schema") == "task172-gate-r-controlled-vocabulary-v1", "wrong controlled vocabulary"
    assert pilot.get("schema") == "task172-gate-r-precision-pilot-v1", "wrong precision pilot schema"
    assert audit.get("schema") == "task172-gate-r-precision-audit-v1", "wrong precision audit schema"
    assert freeze.get("schema") == "task172-gate-r-source-freeze-v1", "wrong source freeze schema"
    assert receipt.get("schema") == "task172-gate-r-build-receipt-v1", "wrong build receipt schema"
    assert operation.get("schema") == "task172-step04-routing-gate-v1", "wrong operation schema"

    assert freeze.get("freeze_event") == "SCAN_INPUT_FREEZE_REUSE", "Gate R did not reuse the scan freeze"
    assert freeze.get("direction_lock") == "IGNITION-20260913-176", "direction lock drift"
    assert freeze.get("command_source") == EXPECTED_COMMAND, "command provenance drift"
    formal = freeze.get("formal_pre_freeze", {})
    assert formal.get("head") == EXPECTED_PARENT_HEAD, "Gate R parent head drift"
    assert formal.get("pull_request") == 218, "wrong Draft PR binding"
    assert formal.get("state") == "OPEN + DRAFT + unmerged", "PR lifecycle ceiling drift"
    assert freeze.get("scan_inputs") == {"primary_pdf_persisted": False, "ocr_persisted": False, "full_corpus_retrieval": False, "mass_formal_routing": False}, "scan or retrieval boundary drift"
    gate_r_admission = admission_for_path("data/research/task172-gate-r-routing/precision-pilot.json")
    assert gate_r_admission.classification == "GENERATED_PROJECTION_EXCLUDED" and not gate_r_admission.auto_discovery, "Gate R sidecar crossed into Foundation admission"

    taxonomy = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
    assert freeze.get("taxonomy_authority", {}).get("fields") == taxonomy["fields"], "taxonomy field drift"
    assert freeze.get("taxonomy_authority", {}).get("primary_disciplines") == taxonomy["primary_disciplines"], "taxonomy discipline drift"
    assert freeze.get("taxonomy_authority", {}).get("primary_subdisciplines") == taxonomy["primary_subdisciplines"], "taxonomy subdiscipline drift"
    assert freeze["taxonomy_authority"]["gate_t_parse_sha256"] == sha256(gate_t / "primary-1988-parse.json"), "Gate T parse hash drift"
    assert freeze["taxonomy_authority"]["gate_t_ledger_sha256"] == sha256(gate_t / "discrepancy-ledger.json"), "Gate T ledger hash drift"
    assert freeze["authority_inputs"]["function_authority_sha256"] == sha256(repo_root / FUNCTION_REL), "function authority hash drift"
    assert freeze["authority_inputs"]["nonfunction_authority_sha256"] == sha256(repo_root / NONFUNCTION_REL), "nonfunction authority hash drift"

    assert schema.get("caps") == EXPECTED_CAPS, "routing caps drift"
    assert schema.get("classification_state") == ["CLASSIFIED", "MULTIDISCIPLINARY", "OUT_OF_UNESCO_SCOPE", "UNRESOLVED"], "classification states drift"
    assert vocabulary.get("asset_role") == ["METHOD_TRANSFER", "EVIDENCE_CHECK", "ANALOGY_SOURCE", "HISTORICAL_CONTEXT", "NARRATIVE_CASE"], "asset role vocabulary drift"
    assert vocabulary.get("negative_boundary") == "REJECT/QUARANTINE/WITHDRAWN records cannot acquire positive evidence-use tags", "negative boundary drift"

    rows = pilot.get("rows", [])
    assert len(rows) == 750, "pilot row count drift"
    assert pilot.get("source_exact_head") == EXPECTED_PARENT_HEAD, "pilot source head drift"
    assert pilot.get("taxonomy") == taxonomy, "pilot taxonomy drift"
    assert pilot.get("manual_review_required") == 750, "manual review ceiling drift"
    assert pilot.get("live_retrieval") is False and pilot.get("full_routing_promotion") is False, "pilot activation drift"
    ids = [row.get("canonical_id") for row in rows]
    assert len(set(ids)) == len(ids), "pilot canonical IDs are not unique"
    assert {row.get("asset_kind") for row in rows} == {"FUNCTION_ASSET", "NONFUNCTION_CLAIM"}, "asset-kind census drift"
    assert sum(row.get("asset_kind") == "FUNCTION_ASSET" for row in rows) == 250, "function sample drift"
    assert sum(row.get("asset_kind") == "NONFUNCTION_CLAIM" for row in rows) == 500, "nonfunction sample drift"
    authorities = {row["canonical_id"]: row for row in read_jsonl(repo_root / FUNCTION_REL)}
    authorities.update({row["canonical_id"]: row for row in read_jsonl(repo_root / NONFUNCTION_REL)})
    assert set(ids) <= set(authorities), "orphan canonical ID"
    for row in rows:
        assert row.get("source_record_sha") == authorities[row["canonical_id"]].get("record_sha256"), f"authority fingerprint mismatch: {row.get('canonical_id')}"
        assert row.get("review_state") == "PILOT_MANUAL_REVIEW_REQUIRED", "pilot row escaped manual review"
        assert row.get("tagger_version") == "task172-step04-precision-v2", "tagger version drift"
        assert set(row).issuperset({"canonical_id", "asset_kind", "domain", "asset_role", "collision_use", "topic", "evidence_projection", "source_record_sha", "tagger_version", "review_state"}), "pilot facet missing"
        domain = row["domain"]
        assert domain.get("classification_state") in schema["classification_state"], "unknown classification state"
        assert len(domain.get("unesco_field_codes", [])) <= EXPECTED_CAPS["unesco_field_codes"], "field cap exceeded"
        assert len(domain.get("unesco_discipline_codes", [])) <= EXPECTED_CAPS["unesco_discipline_codes"], "discipline cap exceeded"
        assert len(row.get("asset_role", [])) <= EXPECTED_CAPS["asset_role"], "role cap exceeded"
        assert len(row.get("collision_use", [])) <= EXPECTED_CAPS["collision_use"], "collision cap exceeded"
        assert len(row.get("topic", [])) <= EXPECTED_CAPS["topic"], "topic cap exceeded"
        if domain["classification_state"] == "OUT_OF_UNESCO_SCOPE":
            assert not domain.get("unesco_field_codes"), "out-of-scope record gained UNESCO field"
        disposition = str(row.get("evidence_projection", {}).get("final_disposition"))
        if any(word in disposition for word in ("REJECT", "QUARANTINE", "WITHDRAWN")):
            assert set(row.get("asset_role", [])) <= NEGATIVE_USE, "negative record gained positive role"

    assert audit.get("source_exact_head") == EXPECTED_PARENT_HEAD, "audit source head drift"
    assert audit.get("rows_checked") == 750 and audit.get("manual_review_required") == 750, "audit row count drift"
    assert audit.get("state_counts") == EXPECTED_COUNTS, "audit state counts drift"
    assert audit.get("hard_checks") == {"orphan_canonical": 0, "authority_fingerprint_mismatch": 0, "cap_violation": 0, "internal_governance_forced_unesco": 0, "out_of_scope_has_domain_code": 0, "negative_record_positive_use": 0}, "hard checks are not zero"
    assert audit.get("violations") == {"orphan": [], "fingerprint": [], "caps": [], "internal": [], "negative": []}, "audit violations are not empty"
    assert audit.get("deterministic") is True, "pilot is not marked deterministic"

    assert operation.get("source_exact_head") == EXPECTED_PARENT_HEAD, "operation source head drift"
    assert operation.get("command_source") == EXPECTED_COMMAND, "operation command drift"
    assert operation.get("taxonomy") == taxonomy, "operation taxonomy drift"
    assert operation.get("pilot", {}).get("hard_check_violations") == 0, "operation hard checks failed"
    assert operation.get("decision") == "GATE_R_PASS_FOR_SCHEMA_AND_PRECISION_PILOT; GATE_C_REQUIRED_BEFORE_MASS_INGESTION", "Gate R decision drift"
    assert operation.get("schema_sha256") == sha256(gate_r / "routing-schema.json"), "operation schema hash drift"
    assert operation.get("vocabulary_sha256") == sha256(gate_r / "controlled-vocabulary.json"), "operation vocabulary hash drift"
    assert operation.get("pilot_sha256") == sha256(gate_r / "precision-pilot.json"), "operation pilot hash drift"
    assert operation.get("audit_sha256") == sha256(gate_r / "precision-audit.json"), "operation audit hash drift"

    assert receipt.get("source_exact_head") == EXPECTED_PARENT_HEAD, "receipt source head drift"
    assert receipt.get("counts") == {"rows": 750, "function_assets": 250, "nonfunction_claims": 500}, "receipt counts drift"
    assert receipt.get("state_counts") == EXPECTED_COUNTS, "receipt state counts drift"
    assert receipt.get("hard_check_violations") == 0 and receipt.get("manual_review_rows") == 750, "receipt gate drift"
    assert receipt.get("live_retrieval") is False and receipt.get("formal_mass_routing") is False, "receipt activation drift"
    for key, path in {"routing_schema": gate_r / "routing-schema.json", "controlled_vocabulary": gate_r / "controlled-vocabulary.json", "precision_pilot": gate_r / "precision-pilot.json", "precision_audit": gate_r / "precision-audit.json", "source_freeze": gate_r / "source-freeze.json", "operation": repo_root / OPERATION_REL}.items():
        assert receipt.get("outputs", {}).get(key) == sha256(path), f"receipt output hash drift: {key}"
    forbidden = [path for path in gate_r.rglob("*") if path.is_file() and (path.suffix in {".pdf", ".txt", ".html"} or "ocr" in path.name.lower())]
    assert not forbidden, f"scan or OCR persisted in Gate R: {forbidden}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        validate(args.repo_root.resolve())
    except AssertionError as exc:
        raise SystemExit(f"TASK172_GATE_R_VALIDATION_FAILED: {exc}") from exc
    print("TASK172_GATE_R_VALIDATION_OK rows=750 function_assets=250 nonfunction_claims=500 hard_check_violations=0 manual_review=750")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
