#!/usr/bin/env python3
"""Fail-closed validator for the policy-only Task172 Gate C lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.foundation.knowledge_corpus_admission import admission_for_path
from tools.research.validate_task172_gate_r import EXPECTED_PARENT_HEAD as EXPECTED_GATE_R_HEAD
from tools.research.validate_task172_gate_r import validate as validate_gate_r
from tools.research.validate_task172_gate_t import validate as validate_gate_t


EXPECTED_SOURCE_HEAD = "998b5654248b41a8982d0674bf0368b400b65eec"
COMMAND_SOURCE = {
    "repository": "Arvin-liu/1111",
    "ref": "b1fc45fb",
    "path": "agent-commands/IGNITION-20260913-176.md",
    "blob_sha": "98fd25bd1886cf8675992413d6c55d1e09b4502f",
}
TAXONOMY = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
GATE_C_REL = Path("data/research/task172-gate-c-scholarly-admission")
OPERATION_REL = Path("data/operations/iterations/172/step05-scholarly-gate.json")
REPORT_REL = Path("reports/operations/ignition-172-20260913-step05-gate-c-scholarly.md")
POLICY_FILES = {
    "admission_policy": "admission-policy.json",
    "provider_roles": "provider-roles.json",
    "rights_policy": "rights-policy.json",
    "correction_retraction_policy": "correction-retraction-policy.json",
    "dedupe_policy": "dedupe-policy.json",
    "cross_domain_pilot": "cross-domain-pilot.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise AssertionError(f"cannot read {path}: {exc}") from exc


def validate(repo_root: Path) -> None:
    validate_gate_t(repo_root)
    validate_gate_r(repo_root)
    gate_c = repo_root / GATE_C_REL
    assert gate_c.is_dir(), "Gate C sidecar is missing"
    files = {key: gate_c / filename for key, filename in POLICY_FILES.items()}
    files["source_freeze"] = gate_c / "source-freeze.json"
    files["receipt"] = gate_c / "build-receipt.json"
    for key, path in files.items():
        assert path.is_file(), f"Gate C file missing: {key}"
    policy = {key: read_json(path) for key, path in files.items() if key not in {"source_freeze", "receipt"}}
    freeze = read_json(files["source_freeze"])
    receipt = read_json(files["receipt"])
    operation = read_json(repo_root / OPERATION_REL)
    report_path = repo_root / REPORT_REL
    assert report_path.is_file(), "Gate C report is missing"

    assert policy["admission_policy"].get("schema") == "task172-gate-c-scholarly-admission-policy-v1", "admission policy schema drift"
    assert policy["provider_roles"].get("schema") == "task172-gate-c-provider-roles-v1", "provider role schema drift"
    assert policy["rights_policy"].get("schema") == "task172-gate-c-rights-policy-v1", "rights policy schema drift"
    assert policy["correction_retraction_policy"].get("schema") == "task172-gate-c-correction-retraction-policy-v1", "correction policy schema drift"
    assert policy["dedupe_policy"].get("schema") == "task172-gate-c-conservative-dedupe-policy-v1", "dedupe policy schema drift"
    assert policy["cross_domain_pilot"].get("schema") == "task172-gate-c-cross-domain-policy-pilot-v1", "pilot schema drift"
    assert freeze.get("schema") == "task172-gate-c-source-freeze-v1", "source freeze schema drift"
    assert receipt.get("schema") == "task172-gate-c-build-receipt-v1", "receipt schema drift"
    assert operation.get("schema") == "task172-step05-scholarly-gate-v1", "operation schema drift"

    assert freeze.get("freeze_event") == "SCAN_INPUT_FREEZE_REUSE", "scan freeze drift"
    assert freeze.get("direction_lock") == "IGNITION-20260913-176", "direction lock drift"
    assert freeze.get("command_source") == COMMAND_SOURCE, "command provenance drift"
    formal = freeze.get("formal_pre_freeze", {})
    assert formal.get("head") == EXPECTED_SOURCE_HEAD, "Gate C source head drift"
    assert formal.get("pull_request") == 218, "wrong Draft PR binding"
    assert formal.get("state") == "OPEN + DRAFT + unmerged", "PR lifecycle ceiling drift"
    assert freeze.get("taxonomy_authority", {}).get("fields") == TAXONOMY["fields"], "taxonomy field drift"
    assert freeze.get("taxonomy_authority", {}).get("primary_disciplines") == TAXONOMY["primary_disciplines"], "taxonomy discipline drift"
    assert freeze.get("taxonomy_authority", {}).get("primary_subdisciplines") == TAXONOMY["primary_subdisciplines"], "taxonomy subdiscipline drift"
    scan_flags = {
        "primary_pdf_persisted": False,
        "ocr_persisted": False,
        "live_scholarly_retrieval": False,
        "abstract_fulltext_persisted": False,
        "corpus_admission": False,
        "mass_formal_ingestion": False,
    }
    assert freeze.get("scan_inputs") == scan_flags, "scan or admission boundary drift"

    admission = policy["admission_policy"]
    assert admission.get("corpus_identities") == ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"], "corpus identities drift"
    assert admission.get("mode") == "METADATA_ONLY", "admission mode drift"
    ceiling = admission.get("admission_ceiling", {})
    assert ceiling.get("stable_identifier_required") is True, "stable identifier ceiling drift"
    assert ceiling.get("accepted_identifiers") == ["DOI", "PROVIDER_STABLE_ID"], "identifier vocabulary drift"
    assert ceiling.get("metadata_rows_admitted_in_gate_c") == 0, "Gate C admitted rows"
    assert ceiling.get("live_retrieval_in_gate_c") is False, "Gate C live retrieval enabled"
    assert ceiling.get("abstract_persistence_by_default") is False and ceiling.get("fulltext_persistence_by_default") is False, "content persistence drift"
    assert ceiling.get("mass_formal_ingestion_authorized_in_gate_c") is False, "mass ingestion authorization drift"
    assert admission.get("promotion_boundary", {}).get("metadata_is_not_evidence") is True, "metadata/evidence boundary drift"

    roles = policy["provider_roles"].get("roles", [])
    assert {row.get("provider_id") for row in roles} == {"OpenAlex", "Crossref", "OpenAIRE", "PubMed E-utilities"}, "provider set drift"
    assert all(row.get("no_evidence_promotion") is True for row in roles), "provider evidence boundary drift"
    assert "provider failure" in policy["provider_roles"].get("failure_semantics", ""), "provider failure semantics missing"

    rights = policy["rights_policy"]
    assert rights.get("mode") == "METADATA_ONLY", "rights mode drift"
    content_rules = rights.get("content_rules", {})
    assert content_rules.get("explicit_license_and_scope_required_for_content") is True, "license scope drift"
    assert content_rules.get("oa_status_is_not_a_license") is True, "OA/license boundary drift"
    assert content_rules.get("unknown_rights_block_abstract_and_fulltext") is True, "unknown rights drift"

    correction = policy["correction_retraction_policy"]
    assert correction.get("statuses") == ["NOT_OBSERVED", "CORRECTED", "RETRACTED", "EXPRESSION_OF_CONCERN", "UPDATED", "UNKNOWN"], "correction states drift"
    assert correction.get("default_status") == "UNKNOWN", "correction default drift"
    assert "positive evidence" in correction.get("authority", ""), "correction evidence boundary missing"
    assert correction.get("admission_behavior", {}).get("original_record") == "retained for audit and linked lineage", "original-record retention drift"

    dedupe = policy["dedupe_policy"]
    assert dedupe.get("precedence") == ["NORMALIZED_DOI", "PROVIDER_STABLE_ID_WITH_PROVIDER_NAMESPACE", "EXACT_NORMALIZED_TITLE_FIRST_AUTHOR_YEAR"], "dedupe precedence drift"
    assert dedupe.get("collision_rules", {}).get("unresolved_collision") == "retain records separately and mark the collision unresolved", "unresolved collision drift"

    pilot = policy["cross_domain_pilot"]
    assert pilot.get("mode") == "POLICY_SIMULATION_ONLY", "pilot mode drift"
    assert {row.get("domain_id") for row in pilot.get("domains", [])} == {"natural_science", "engineering_medicine", "social_science", "humanities_law_arts_philosophy"}, "pilot domain set drift"
    assert pilot.get("target_range_per_domain") == [5, 12], "pilot target range drift"
    assert pilot.get("selection_slots") == ["overview", "foundational", "recent", "method", "critical"], "pilot slot drift"
    assert len(pilot.get("synthetic_cases", [])) == 8, "synthetic case count drift"
    assert pilot.get("live_retrieval") is False, "pilot live retrieval enabled"
    assert pilot.get("metadata_rows_admitted") == 0, "pilot admitted metadata rows"
    assert pilot.get("abstract_fulltext_persisted") is False, "pilot persisted content"
    assert pilot.get("corpus_admission") is False, "pilot corpus admission enabled"
    assert pilot.get("status") == "POLICY_PILOT_PASS_NO_CORPUS_ADMISSION", "pilot decision drift"

    assert operation.get("source_exact_head") == EXPECTED_SOURCE_HEAD, "operation source head drift"
    assert operation.get("command_source") == COMMAND_SOURCE, "operation command drift"
    assert operation.get("taxonomy") == TAXONOMY, "operation taxonomy drift"
    assert operation.get("gate_r", {}).get("source_exact_head") == EXPECTED_GATE_R_HEAD, "Gate R precondition drift"
    assert operation.get("gate_r", {}).get("precision_pilot_rows") == 750, "Gate R pilot precondition drift"
    assert operation.get("pilot", {}).get("domains") == 4 and operation.get("pilot", {}).get("synthetic_cases") == 8, "operation pilot count drift"
    assert operation.get("pilot", {}).get("live_retrieval") is False and operation.get("pilot", {}).get("metadata_rows_admitted") == 0, "operation admission drift"
    assert operation.get("admission") == {"corpus_identities": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"], "mode": "METADATA_ONLY", "mass_formal_ingestion_authorized": False}, "operation admission policy drift"
    assert operation.get("decision") == "GATE_C_PASS_FOR_SCHOLARLY_ADMISSION_POLICY_AND_PROVIDER_ROLES; METADATA_ONLY; NO_CORPUS_ADMISSION; 24_FIELD_FORMAL_INGESTION_MAY_BEGIN_AFTER_EXACT_HEAD_CI", "Gate C decision drift"
    assert operation.get("report_sha256") == sha256(report_path), "operation report hash drift"
    for key, path in files.items():
        if key not in {"source_freeze", "receipt"}:
            assert operation.get("policy_hashes", {}).get(key) == sha256(path), f"operation policy hash drift: {key}"
    assert operation.get("source_freeze_sha256") == sha256(files["source_freeze"]), "operation freeze hash drift"

    assert receipt.get("source_exact_head") == EXPECTED_SOURCE_HEAD, "receipt source head drift"
    assert receipt.get("scan_inputs") == scan_flags, "receipt scan boundary drift"
    assert receipt.get("live_retrieval") is False and receipt.get("corpus_admission") is False, "receipt admission drift"
    assert receipt.get("abstract_fulltext_persisted") is False and receipt.get("mass_formal_ingestion") is False, "receipt content/mass drift"
    assert receipt.get("counts") == {"domains": 4, "target_per_domain": 5, "synthetic_cases": 8, "metadata_rows_admitted": 0}, "receipt counts drift"
    for key, path in {**files, "operation": repo_root / OPERATION_REL, "report": report_path}.items():
        if key == "receipt":
            continue
        assert receipt.get("outputs", {}).get(key) == sha256(path), f"receipt output hash drift: {key}"

    # Generated sidecar and its operation/report must remain outside automatic
    # Knowledge admission, and no scan/content artifact may be hidden inside it.
    for raw in [str(GATE_C_REL / "admission-policy.json"), str(OPERATION_REL), str(REPORT_REL)]:
        decision = admission_for_path(raw)
        assert decision.classification == "GENERATED_PROJECTION_EXCLUDED" and not decision.auto_discovery, f"Gate C crossed admission boundary: {raw}"
    forbidden = [path for path in gate_c.rglob("*") if path.is_file() and (path.suffix.lower() in {".pdf", ".txt", ".html"} or "ocr" in path.name.lower() or "abstract" in path.name.lower() or "fulltext" in path.name.lower())]
    assert not forbidden, f"scan or scholarly content persisted in Gate C: {forbidden}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        validate(args.repo_root.resolve())
    except AssertionError as exc:
        raise SystemExit(f"TASK172_GATE_C_VALIDATION_FAILED: {exc}") from exc
    print("TASK172_GATE_C_VALIDATION_OK domains=4 synthetic_cases=8 metadata_rows_admitted=0 corpus_admission=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
