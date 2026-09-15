#!/usr/bin/env python3
"""Fail-closed validator for the incremental Task172 Step09 corpus.

Step09 admits only scholarly metadata references.  The global ledger stores a
physical record once; field/discipline links provide the UNESCO routing
relations.  A partial wave is valid while ``pending_fields`` is explicit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from tools.research.validate_task172_gate_c import validate as validate_gate_c
from tools.research.validate_task172_gate_r import validate as validate_gate_r
from tools.research.validate_task172_gate_t import validate as validate_gate_t


FIELDS = (
    "11", "12", "21", "22", "23", "24", "25", "31", "32", "33",
    "51", "52", "53", "54", "55", "56", "57", "58", "59", "61",
    "62", "63", "71", "72",
)
TAXONOMY = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
DATA_REL = Path("data/external-research/unesco-general-knowledge-r1/step09-corpus")
LEDGER_REL = DATA_REL / "physical-records.jsonl"
LINKS_REL = DATA_REL / "discipline-links.jsonl"
MANIFEST_REL = DATA_REL / "corpus-manifest.json"
POLICY_REL = DATA_REL / "corpus-policy.json"
OPERATION_TEMPLATE = "data/operations/iterations/172/step09-field-{field}.json"
REPORT_TEMPLATE = "reports/operations/ignition-172-20260915-step09-field-{field}.md"
BANNED_KEYS = {"abstract", "abstracts", "description", "fulltext", "full_text", "full-text", "raw_response", "response_body"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical_id(identity: str) -> str:
    return "scholarly-metadata-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def assert_no_banned_keys(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert str(key).lower() not in BANNED_KEYS, f"forbidden content key: {path}.{key}"
            assert_no_banned_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_banned_keys(child, f"{path}[{index}]")


def validate(repo_root: Path) -> None:
    validate_gate_t(repo_root)
    validate_gate_r(repo_root)
    validate_gate_c(repo_root)
    data = repo_root / DATA_REL
    required = [repo_root / rel for rel in (LEDGER_REL, LINKS_REL, MANIFEST_REL, POLICY_REL)]
    assert all(path.is_file() for path in required), "Step09 corpus root artifact missing"
    manifest = load_json(repo_root / MANIFEST_REL)
    policy = load_json(repo_root / POLICY_REL)
    physical = load_jsonl(repo_root / LEDGER_REL)
    links = load_jsonl(repo_root / LINKS_REL)
    for value, label in ((manifest, "manifest"), (policy, "policy"), (physical, "physical"), (links, "links")):
        assert_no_banned_keys(value, label)

    assert manifest.get("schema") == "task172-step09-corpus-manifest-v1"
    assert manifest.get("formal_write") is True
    assert manifest.get("taxonomy") == TAXONOMY
    assert manifest.get("committed_fields"), "Step09 must expose at least one committed field"
    committed = manifest["committed_fields"]
    pending = manifest.get("pending_fields")
    assert isinstance(committed, list) and len(committed) == len(set(committed))
    assert set(committed) <= set(FIELDS), "unknown UNESCO field committed"
    assert committed == sorted(committed, key=FIELDS.index), "field wave order drift"
    assert pending == [field for field in FIELDS if field not in committed]
    assert manifest.get("same_physical_record_once") is True
    assert manifest.get("metadata_only") is True and manifest.get("evidence_promotion") is False
    assert manifest.get("physical_record_count") == len(physical)
    assert manifest.get("discipline_link_count") == len(links)
    assert manifest.get("last_field_code") == committed[-1]
    assert manifest.get("last_field_parent_head") and HEX40.match(manifest["last_field_parent_head"])

    assert policy.get("schema") == "task172-step09-corpus-policy-v1"
    assert policy.get("same_physical_record_once") is True
    assert policy.get("cross_field_links_are_not_taxonomy_equivalence") is True
    assert policy.get("provider_failure_is_not_no_literature") is True
    assert policy.get("unknown_rights_remain_metadata_only") is True
    assert policy.get("correction_retraction_requires_manual_review") is True
    assert policy.get("abstract_or_fulltext_persisted") is False
    assert policy.get("raw_provider_response_persisted") is False
    assert policy.get("evidence_promotion") is False

    physical_ids = [row.get("physical_record_id") for row in physical]
    identities = [row.get("identity_key") for row in physical]
    assert all(physical_ids) and len(physical_ids) == len(set(physical_ids))
    assert all(identities) and len(identities) == len(set(identities))
    physical_by_id = {row["physical_record_id"]: row for row in physical}
    for row in physical:
        identity = str(row["identity_key"]).lower()
        assert row["physical_record_id"] == physical_id(identity)
        assert row.get("metadata_only") is True
        assert row.get("manual_review_required") is True
        assert row.get("evidence_promotion") is False
        assert row.get("proof_promotion") is False
        assert row.get("replication_promotion") is False
        assert row.get("formal_field_introduced") in committed
        assert row.get("formal_parent_head") and HEX40.match(row["formal_parent_head"])
        assert row.get("source_exact_head")
        assert row.get("source_response_sha256")
        assert row.get("correction_retraction_status") in {"NOT_OBSERVED", "UPDATED", "RETRACTED", "CORRECTED", "UNKNOWN"}
        assert row.get("provider_observations")
        assert all(observation.get("source_response_sha256") for observation in row["provider_observations"])

    link_keys = [(row.get("field_code"), row.get("discipline_code"), row.get("physical_record_id")) for row in links]
    assert all(all(value for value in key) for key in link_keys)
    assert len(link_keys) == len(set(link_keys)), "duplicate field/discipline/physical link"
    links_by_field: dict[str, list[dict]] = {field: [] for field in committed}
    for row in links:
        field = str(row["field_code"])
        assert field in committed
        assert row.get("physical_record_id") in physical_by_id
        assert row.get("identity_key") == physical_by_id[row["physical_record_id"]]["identity_key"]
        assert row.get("metadata_only") is True
        assert row.get("manual_review_required") is True
        assert row.get("evidence_promotion") is False
        assert row.get("formal_parent_head") and HEX40.match(row["formal_parent_head"])
        links_by_field[field].append(row)

    field_dirs = {path.name for path in (data / "fields").glob("*") if path.is_dir()} if (data / "fields").is_dir() else set()
    assert field_dirs == set(committed), f"field directory set drift: {field_dirs} != {set(committed)}"
    for field in committed:
        field_dir = data / "fields" / field
        admission_path = field_dir / "field-admission.json"
        freeze_path = field_dir / "source-freeze.json"
        receipt_path = field_dir / "build-receipt.json"
        operation_path = repo_root / OPERATION_TEMPLATE.format(field=field)
        report_path = repo_root / REPORT_TEMPLATE.format(field=field)
        assert all(path.is_file() for path in (admission_path, freeze_path, receipt_path, operation_path, report_path)), f"field artifact missing: {field}"
        admission = load_json(admission_path)
        freeze = load_json(freeze_path)
        receipt = load_json(receipt_path)
        operation = load_json(operation_path)
        for value, label in ((admission, f"admission[{field}]"), (freeze, f"freeze[{field}]"), (receipt, f"receipt[{field}]"), (operation, f"operation[{field}]")):
            assert_no_banned_keys(value, label)
        assert report_path.read_text(encoding="utf-8").strip()

        field_links = links_by_field[field]
        assert admission.get("schema") == "task172-step09-field-admission-v1"
        assert admission.get("formal_write") is True
        assert admission.get("field_code") == field
        assert admission.get("taxonomy") == TAXONOMY
        assert admission.get("formal_parent_head") == field_links[0]["formal_parent_head"]
        assert admission.get("discovery_parent_head")
        assert admission.get("metadata_only") is True
        assert admission.get("manual_review_required") is True
        assert admission.get("evidence_promotion") is False
        assert admission.get("content_boundary") == {"metadata_only": True, "abstract_or_fulltext_persisted": False, "raw_provider_response_persisted": False}
        assert admission.get("evidence_boundary") == {"evidence_promotion": False, "proof_promotion": False, "replication_promotion": False}
        coverage = admission.get("coverage", [])
        assert coverage and all(row.get("selected_count") == 8 and row.get("status") == "READY_FOR_MANUAL_REVIEW" for row in coverage)
        assert admission.get("selected_link_count") == len(field_links)
        assert admission.get("global_physical_record_count_after_field") <= len(physical)
        assert admission.get("global_physical_record_count_after_field") >= admission.get("new_physical_record_count", 0)
        assert admission.get("policy_ref") == str(POLICY_REL)

        assert freeze.get("schema") == "task172-step09-field-source-freeze-v1"
        assert freeze.get("freeze_event") == "SCAN_AND_PROVIDER_INPUT_FREEZE"
        assert freeze.get("field_code") == field
        assert freeze.get("formal_parent_head") == admission["formal_parent_head"]
        assert freeze.get("discovery_parent_head") == admission["discovery_parent_head"]
        assert HEX64.match(freeze.get("packet_sha256", ""))
        assert freeze.get("raw_response_persistence") is False
        assert freeze.get("abstract_or_fulltext_persistence") is False
        assert freeze.get("selection_is_metadata_heuristic") is True

        assert receipt.get("schema") == "task172-step09-field-build-receipt-v1"
        assert receipt.get("field_code") == field
        assert receipt.get("formal_parent_head") == admission["formal_parent_head"]
        assert receipt.get("taxonomy") == TAXONOMY
        assert receipt.get("metadata_only") is True and receipt.get("manual_review_required") is True
        assert receipt.get("abstract_or_fulltext_persisted") is False and receipt.get("evidence_promotion") is False
        assert receipt.get("source_freeze_sha256") == sha256(freeze_path)
        assert receipt.get("outputs", {}).get("field_admission") == sha256(admission_path)
        assert receipt.get("outputs", {}).get("source_freeze") == sha256(freeze_path)
        assert receipt.get("outputs", {}).get("operation") == sha256(operation_path)
        assert receipt.get("outputs", {}).get("report") == sha256(report_path)

        assert operation.get("schema") == "task172-step09-field-operation-v1"
        assert operation.get("field_code") == field
        assert operation.get("formal_parent_head") == admission["formal_parent_head"]
        assert operation.get("taxonomy") == TAXONOMY
        assert operation.get("admission_status") == "METADATA_ADMITTED_MANUAL_REVIEW_REQUIRED"
        assert operation.get("coverage_status") == "READY_FOR_MANUAL_REVIEW"
        assert operation.get("source_freeze_sha256") == sha256(freeze_path)
        assert operation.get("content_boundary") == admission["content_boundary"]
        assert operation.get("evidence_boundary") == admission["evidence_boundary"]

    latest = committed[-1]
    latest_receipt = load_json(data / "fields" / latest / "build-receipt.json")
    assert latest_receipt.get("outputs", {}).get("physical_records") == sha256(repo_root / LEDGER_REL)
    assert latest_receipt.get("outputs", {}).get("discipline_links") == sha256(repo_root / LINKS_REL)
    assert latest_receipt.get("outputs", {}).get("manifest") == sha256(repo_root / MANIFEST_REL)
    assert latest_receipt.get("outputs", {}).get("policy") in {None, sha256(repo_root / POLICY_REL)}
    print(
        f"TASK172_STEP09_VALIDATION_OK fields={len(committed)} disciplines="
        f"{sum(len(load_json(data / 'fields' / field / 'field-admission.json').get('coverage', [])) for field in committed)} "
        f"physical_records={len(physical)} links={len(links)} metadata_only=true evidence_promotion=false"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        validate(args.repo_root.resolve())
    except AssertionError as exc:
        raise SystemExit(f"TASK172_STEP09_VALIDATION_FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
