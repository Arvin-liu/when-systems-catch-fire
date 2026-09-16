#!/usr/bin/env python3
"""Fail-closed validator for the Task172 Step08 metadata pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.foundation.knowledge_corpus_admission import admission_for_path
from tools.research.validate_task172_gate_c import validate as validate_gate_c
from tools.research.validate_task172_gate_r import validate as validate_gate_r
from tools.research.validate_task172_gate_t import validate as validate_gate_t


EXPECTED_SOURCE_HEAD = "36a1ed4c0e5b91598b5a4fada4bec1539ccc106b"
DATA_REL = Path("data/external-research/unesco-general-knowledge-r1")
SOURCE_REL = DATA_REL / "source-candidates.jsonl"
REQUEST_REL = DATA_REL / "provider-request-receipt.json"
TARGET_REL = DATA_REL / "target-disciplines.json"
ADMISSION_REL = DATA_REL / "metadata-admission.jsonl"
CROSSWALK_REL = DATA_REL / "crosswalk-pilot.json"
DEDUPE_REL = DATA_REL / "dedupe-ledger.jsonl"
FREEZE_REL = DATA_REL / "source-freeze.json"
RECEIPT_REL = DATA_REL / "step08-build-receipt.json"
OPERATION_REL = Path("data/operations/iterations/172/step08-scholarly-pilot.json")
REPORT_REL = Path("reports/operations/ignition-172-20260914-step08-scholarly-pilot.md")
PROVIDERS = ["OpenAlex", "Crossref", "OpenAIRE", "PubMed E-utilities"]
BAN_KEYS = {"abstract", "abstracts", "description", "fulltext", "full_text", "full-text", "raw_response", "response_body"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_no_banned_keys(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert str(key).lower() not in BAN_KEYS, f"forbidden content key: {path}.{key}"
            assert_no_banned_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_banned_keys(child, f"{path}[{index}]")


def validate(repo_root: Path) -> None:
    validate_gate_t(repo_root)
    validate_gate_r(repo_root)
    validate_gate_c(repo_root)
    data = repo_root / DATA_REL
    paths = {name: repo_root / rel for name, rel in {"source": SOURCE_REL, "request": REQUEST_REL, "target": TARGET_REL, "admission": ADMISSION_REL, "crosswalk": CROSSWALK_REL, "dedupe": DEDUPE_REL, "freeze": FREEZE_REL, "receipt": RECEIPT_REL, "operation": OPERATION_REL, "report": REPORT_REL}.items()}
    for name, path in paths.items():
        assert path.is_file(), f"Step08 artifact missing: {name}"

    source_rows = read_jsonl(paths["source"])
    request = read_json(paths["request"])
    target = read_json(paths["target"])
    admission_rows = read_jsonl(paths["admission"])
    crosswalk = read_json(paths["crosswalk"])
    dedupe_rows = read_jsonl(paths["dedupe"])
    freeze = read_json(paths["freeze"])
    receipt = read_json(paths["receipt"])
    operation = read_json(paths["operation"])
    assert paths["report"].read_text(encoding="utf-8").strip()

    for value, label in ((source_rows, "source"), (request, "request"), (target, "target"), (admission_rows, "admission"), (crosswalk, "crosswalk"), (dedupe_rows, "dedupe"), (freeze, "freeze"), (receipt, "receipt"), (operation, "operation")):
        assert_no_banned_keys(value, label)

    assert target.get("schema") == "task172-step08-target-disciplines-v1"
    assert target.get("source_exact_head") == EXPECTED_SOURCE_HEAD
    assert target.get("taxonomy") == {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
    targets = target.get("targets", [])
    assert len(targets) == 24 and len({row.get("field_code") for row in targets}) == 24, "Step08 target field coverage drift"
    target_by_code = {row["discipline_code"]: row for row in targets}
    assert len(target_by_code) == 24
    target_by_field = {row["field_code"]: row for row in targets}
    assert set(target_by_field) == {row["field_code"] for row in targets}
    assert all(row.get("mapping_type") == "QUERY_SEED_ONLY_NO_DIRECT_PROVIDER_EQUIVALENCE" and row.get("confidence") is None for row in targets)

    assert request.get("schema") == "task172-step08-provider-request-receipt-v1"
    assert request.get("source_exact_head") == EXPECTED_SOURCE_HEAD
    assert request.get("target_count") == 24
    assert request.get("raw_response_persistence") is False
    assert request.get("abstract_or_fulltext_persistence") is False
    assert request.get("provider_failure_is_not_no_literature") is True
    requests = request.get("provider_requests", [])
    request_statuses = Counter((row.get("provider"), row.get("status")) for row in requests)
    for provider, minimum in (("OpenAlex", 24), ("Crossref", 24), ("OpenAIRE", 24), ("PubMed E-utilities", 2)):
        assert request_statuses[(provider, "HTTP_SUCCESS")] >= minimum, f"{provider} request coverage is not frozen-success"
    assert all(row.get("response_sha256") for row in requests if row.get("status") == "HTTP_SUCCESS"), "successful provider response hash missing"
    assert request.get("candidate_count") == len(source_rows)
    assert request.get("candidate_count_by_provider") == dict(sorted(Counter(row.get("provider") for row in source_rows).items()))

    source_ids = [row.get("candidate_id") for row in source_rows]
    assert len(source_ids) == len(set(source_ids)) and all(source_ids), "source candidate identity drift"
    assert len(source_rows) > 0, "Step08 has no metadata candidates"
    for row in source_rows:
        assert row.get("provider") in PROVIDERS
        code = str(row.get("unesco_discipline_code"))
        assert code in target_by_code and row.get("unesco_field_code") == target_by_code[code]["field_code"]
        assert row.get("metadata_only") is True
        assert row.get("stable_identifier", {}).get("value")
        assert row.get("selection_status") == "CANDIDATE_REQUIRES_MANUAL_REVIEW"
        assert row.get("source_response_sha256")

    assert len(admission_rows) == len(source_rows)
    record_ids = [row.get("record_id") for row in admission_rows]
    assert len(record_ids) == len(set(record_ids)) and all(record_ids)
    for row in admission_rows:
        route = row.get("unesco_route", {})
        assert row.get("corpus_identity") == ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"]
        assert row.get("admission_status") == "METADATA_ADMITTED_MANUAL_REVIEW_REQUIRED"
        assert route.get("discipline_code") in target_by_code
        assert route.get("mapping_type") == "QUERY_SEED_ONLY_NO_DIRECT_PROVIDER_EQUIVALENCE"
        assert route.get("confidence") is None
        assert row.get("content_boundary") == {"metadata_only": True, "non_metadata_content_count": 0, "content_persistence": "DISABLED"}
        assert row.get("evidence_boundary") == {"evidence_promotion": False, "proof_promotion": False, "replication_promotion": False}
        assert row.get("routing", {}).get("slot") == "UNASSIGNED_PENDING_MANUAL_REVIEW"

    assert crosswalk.get("schema") == "task172-step08-unesco-modern-index-crosswalk-pilot-v1"
    assert crosswalk.get("source_exact_head") == EXPECTED_SOURCE_HEAD
    assert crosswalk.get("taxonomy") == target["taxonomy"]
    assert crosswalk.get("pilot_scope", {}).get("target_fields") == 24
    assert crosswalk.get("pilot_scope", {}).get("target_disciplines") == 24
    assert crosswalk.get("pilot_scope", {}).get("records") == len(admission_rows)
    assert crosswalk.get("pilot_scope", {}).get("metadata_only") is True
    assert crosswalk.get("pilot_scope", {}).get("manual_review_required") is True
    assert crosswalk.get("no_direct_mapping_rule") is True
    assert crosswalk.get("decision") == "STEP08_PILOT_PASS_FOR_METADATA_PIPELINE; NO_DIRECT_PROVIDER_EQUIVALENCE; NO_SCIENTIFIC_EVIDENCE_PROMOTION"
    crosswalk_rows = crosswalk.get("rows", [])
    assert len(crosswalk_rows) == 24 and {row.get("field_code") for row in crosswalk_rows} == set(target_by_field)
    counts = Counter(row.get("provider") for row in source_rows)
    assert crosswalk.get("provider_candidate_counts") == dict(sorted(counts.items()))
    for row in crosswalk_rows:
        expected = target_by_field[row["field_code"]]
        assert row.get("unesco_discipline_code") == expected["discipline_code"]
        assert row.get("mapping_type") == "QUERY_SEED_ONLY_NO_DIRECT_PROVIDER_EQUIVALENCE"
        assert row.get("confidence") is None
        assert row.get("provider_taxonomy_ids") == []
        assert row.get("manual_review_required") is True
        assert row.get("candidate_record_ids"), f"no candidate surfaced for field {row['field_code']}"
        assert set(row.get("providers_attempted", [])) >= {"OpenAlex", "Crossref", "OpenAIRE"}
        if row["field_code"] == "32":
            assert "PubMed E-utilities" in row.get("providers_attempted", [])

    assert dedupe_rows, "dedupe ledger missing"
    dedupe_ids = [record_id for row in dedupe_rows for record_id in row.get("record_ids", [])]
    assert sorted(dedupe_ids) == sorted(record_ids), "dedupe ledger does not cover exactly the admitted records"
    assert len(dedupe_ids) == len(set(dedupe_ids))
    assert all(row.get("decision") for row in dedupe_rows)

    assert freeze.get("schema") == "task172-step08-source-freeze-v1"
    assert freeze.get("freeze_event") == "SCAN_AND_PROVIDER_INPUT_FREEZE"
    assert freeze.get("formal_pre_freeze", {}).get("head") == EXPECTED_SOURCE_HEAD
    assert freeze.get("formal_pre_freeze", {}).get("pull_request") == 218
    assert freeze.get("formal_pre_freeze", {}).get("state") == "OPEN + DRAFT + unmerged"
    assert freeze.get("taxonomy_authority", {}).get("primary_disciplines") == 245
    assert freeze.get("provider_input", {}).get("source_candidates_sha256") == sha256(paths["source"])
    assert freeze.get("provider_input", {}).get("request_receipt_sha256") == sha256(paths["request"])
    assert freeze.get("provider_input", {}).get("raw_response_persistence") is False
    assert freeze.get("provider_input", {}).get("abstract_or_fulltext_persistence") is False
    assert freeze.get("decision") == "STEP08_SOURCE_AND_DERIVED_CLOSURE_FROZEN; METADATA_ONLY; NO_PROVIDER_TAXONOMY_EQUIVALENCE; NO_EVIDENCE_PROMOTION"

    assert receipt.get("schema") == "task172-step08-build-receipt-v1"
    assert receipt.get("source_exact_head") == EXPECTED_SOURCE_HEAD
    assert receipt.get("taxonomy") == target["taxonomy"]
    assert receipt.get("counts", {}).get("target_fields") == 24
    assert receipt.get("counts", {}).get("target_disciplines") == 24
    assert receipt.get("counts", {}).get("source_candidates") == len(source_rows)
    assert receipt.get("counts", {}).get("metadata_admitted") == len(admission_rows)
    assert receipt.get("raw_response_persistence") is False and receipt.get("content_persistence") is False
    assert receipt.get("evidence_promotion") is False and receipt.get("no_direct_provider_equivalence") is True
    output_map = {"source_candidates": SOURCE_REL, "provider_request_receipt": REQUEST_REL, "target_disciplines": TARGET_REL, "metadata_admission": ADMISSION_REL, "crosswalk": CROSSWALK_REL, "dedupe": DEDUPE_REL, "source_freeze": FREEZE_REL, "operation": OPERATION_REL, "report": REPORT_REL}
    for key, rel in output_map.items():
        assert receipt.get("outputs", {}).get(key) == sha256(repo_root / rel), f"receipt hash drift: {key}"
    for key, rel in {"target_disciplines": TARGET_REL, "metadata_admission": ADMISSION_REL, "crosswalk": CROSSWALK_REL, "dedupe": DEDUPE_REL}.items():
        assert freeze.get("derived_outputs", {}).get(key) == sha256(repo_root / rel), f"freeze hash drift: {key}"

    assert operation.get("schema") == "task172-step08-scholarly-pilot-v1"
    assert operation.get("source_exact_head") == EXPECTED_SOURCE_HEAD
    assert operation.get("taxonomy") == target["taxonomy"]
    assert operation.get("pilot", {}).get("target_fields") == 24
    assert operation.get("pilot", {}).get("target_disciplines") == 24
    assert operation.get("pilot", {}).get("metadata_candidates") == len(source_rows)
    assert operation.get("pilot", {}).get("metadata_admitted") == len(admission_rows)
    assert operation.get("pilot", {}).get("evidence_promotion") is False
    assert operation.get("pilot", {}).get("content_persistence") is False
    assert operation.get("source_freeze_sha256") == sha256(paths["freeze"])
    assert operation.get("crosswalk_sha256") == sha256(paths["crosswalk"])
    assert operation.get("dedupe_sha256") == sha256(paths["dedupe"])
    assert operation.get("report_sha256") == sha256(paths["report"])
    assert operation.get("decision") == crosswalk["decision"]

    for raw in (str(SOURCE_REL), str(ADMISSION_REL), str(CROSSWALK_REL)):
        decision = admission_for_path(raw)
        assert decision.classification == "KNOWLEDGE_SOURCE_ELIGIBLE" and decision.auto_discovery, f"metadata source not admitted: {raw}"
    for raw in (str(OPERATION_REL), str(REPORT_REL)):
        decision = admission_for_path(raw)
        assert decision.classification == "GENERATED_PROJECTION_EXCLUDED" and not decision.auto_discovery, f"operation leaked into admission: {raw}"

    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    subprocess.check_call(["git", "cat-file", "-e", EXPECTED_SOURCE_HEAD + "^{commit}"], cwd=repo_root)
    assert current != "", "current Formal head unavailable"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        validate(args.repo_root.resolve())
    except AssertionError as exc:
        raise SystemExit(f"TASK172_STEP08_VALIDATION_FAILED: {exc}") from exc
    print("TASK172_STEP08_VALIDATION_OK fields=24 target_disciplines=24 metadata_only=true direct_provider_equivalence=false evidence_promotion=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
