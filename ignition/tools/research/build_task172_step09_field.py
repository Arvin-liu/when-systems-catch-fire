#!/usr/bin/env python3
"""Materialize one Task172 Step09 UNESCO field from a frozen scratch packet.

The packet is a bounded, metadata-only preparation input.  This generator is
used at a field checkpoint to create one append-only global physical-record
ledger plus field/discipline links.  It intentionally never fetches providers,
persists content, promotes evidence, or infers provider taxonomy equivalence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


FIELDS = (
    "11", "12", "21", "22", "23", "24", "25", "31", "32", "33",
    "51", "52", "53", "54", "55", "56", "57", "58", "59", "61",
    "62", "63", "71", "72",
)
DISCOVERY_HEAD = "294a2b095a30354797686db4d10430304f3309ae"
TAXONOMY = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
DATA_REL = Path("data/external-research/unesco-general-knowledge-r1/step09-corpus")
LEDGER_REL = DATA_REL / "physical-records.jsonl"
LINKS_REL = DATA_REL / "discipline-links.jsonl"
MANIFEST_REL = DATA_REL / "corpus-manifest.json"
POLICY_REL = DATA_REL / "corpus-policy.json"
OPERATION_TEMPLATE = "data/operations/iterations/172/step09-field-{field}.json"
REPORT_TEMPLATE = "reports/operations/ignition-172-20260915-step09-field-{field}.md"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict], *, append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    if append:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text)
    else:
        path.write_text(text, encoding="utf-8")


def physical_id(identity: str) -> str:
    return "scholarly-metadata-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def relative(repo_root: Path, path: Path) -> str:
    return str(path.relative_to(repo_root)).replace("\\", "/")


def policy() -> dict:
    return {
        "schema": "task172-step09-corpus-policy-v1",
        "corpus_identity": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"],
        "admission_scope": "metadata-only scholarly references; manual review required",
        "same_physical_record_once": True,
        "cross_field_links_are_not_taxonomy_equivalence": True,
        "no_provider_taxonomy_equivalence": True,
        "provider_failure_is_not_no_literature": True,
        "unknown_rights_remain_metadata_only": True,
        "correction_retraction_requires_manual_review": True,
        "abstract_or_fulltext_persisted": False,
        "raw_provider_response_persisted": False,
        "evidence_promotion": False,
        "proof_promotion": False,
        "replication_promotion": False,
        "provider_roles": {
            "Crossref": "registration and DOI metadata; no content equivalence",
            "OpenAlex": "discovery metadata and stable work identifiers; no content equivalence",
            "OpenAIRE": "discovery/rights signals; no content equivalence",
            "PubMed E-utilities": "biomedical discovery metadata where queried; no content equivalence",
        },
        "selection_policy": "deterministic metadata heuristic only; field/discipline coverage is not scientific relevance validation",
    }


def normalize_record(record: dict, parent_head: str, field: str) -> dict:
    identity = str(record.get("identity_key") or "").strip().lower()
    if not identity:
        raise SystemExit("record missing identity_key")
    if record.get("source_exact_head") != DISCOVERY_HEAD:
        raise SystemExit(f"record discovery head drift: {identity}")
    result = dict(record)
    result.update({
        "physical_record_id": physical_id(identity),
        "identity_key": identity,
        "formal_parent_head": parent_head,
        "formal_field_introduced": field,
        "metadata_only": True,
        "manual_review_required": True,
        "evidence_promotion": False,
        "proof_promotion": False,
        "replication_promotion": False,
        "taxonomy_assertion": "routing_reference_only; UNESCO assignment is a field/discipline link, not provider taxonomy equivalence",
    })
    return result


def normalize_link(ref: dict, parent_head: str, field: str) -> dict:
    identity = str(ref.get("identity_key") or "").strip().lower()
    result = dict(ref)
    result.update({
        "identity_key": identity,
        "physical_record_id": physical_id(identity),
        "formal_parent_head": parent_head,
        "formal_field_code": field,
        "metadata_only": True,
        "manual_review_required": True,
        "evidence_promotion": False,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--field", required=True, choices=FIELDS)
    parser.add_argument("--parent-head", required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    packet_path = args.packet.resolve()
    field = args.field
    parent_head = args.parent_head
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if packet.get("formal_write") is not False:
        raise SystemExit("only formal_write=false scratch packets may be admitted")
    if packet.get("field_code") != field or packet.get("source_exact_head") != DISCOVERY_HEAD:
        raise SystemExit("packet field or discovery parent mismatch")
    if packet.get("taxonomy") != TAXONOMY:
        raise SystemExit("packet taxonomy drift")
    targets = packet.get("targets", [])
    records = [normalize_record(row, parent_head, field) for row in packet.get("canonical_metadata_records", [])]
    links = [normalize_link(row, parent_head, field) for row in packet.get("selected_refs", [])]
    by_identity = {row["identity_key"]: row for row in records}
    if len(by_identity) != len(records):
        raise SystemExit("packet contains duplicate physical identities")
    if len(links) != len({(row["discipline_code"], row["identity_key"]) for row in links}):
        raise SystemExit("packet contains duplicate discipline links")
    if any(row["identity_key"] not in by_identity for row in links):
        raise SystemExit("link has no packet record")
    if any(row.get("metadata_only") is not True or row.get("evidence_promotion") is not False for row in records + links):
        raise SystemExit("packet boundary is not metadata-only")

    data = repo_root / DATA_REL
    existing_records = read_jsonl(repo_root / LEDGER_REL)
    existing_links = read_jsonl(repo_root / LINKS_REL)
    existing_ids = {row.get("physical_record_id") for row in existing_records}
    existing_fields = {str(row.get("field_code")) for row in existing_links}
    if field in existing_fields:
        raise SystemExit(f"field already materialized: {field}")
    new_records = [row for row in records if row["physical_record_id"] not in existing_ids]
    if len({row["physical_record_id"] for row in new_records}) != len(new_records):
        raise SystemExit("new physical records are not unique")
    if any(row["physical_record_id"] in existing_ids for row in records if row not in new_records):
        # Existing physical identities are allowed only when a later field links
        # to them; the branch must never duplicate the physical row.
        pass
    write_jsonl(repo_root / LEDGER_REL, new_records, append=True)
    write_jsonl(repo_root / LINKS_REL, links, append=True)

    field_dir = data / "fields" / field
    field_dir.mkdir(parents=True, exist_ok=True)
    input_freeze = [
        {"artifact": "step09 scratch field packet", "name": Path(row["path"]).name, "sha256": row["sha256"]}
        for row in packet.get("input_freeze", [])
    ]
    admission = {
        "schema": "task172-step09-field-admission-v1",
        "corpus_identity": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"],
        "formal_write": True,
        "field_code": field,
        "field_label": packet["field_label"],
        "formal_parent_head": parent_head,
        "discovery_parent_head": DISCOVERY_HEAD,
        "taxonomy": TAXONOMY,
        "metadata_only": True,
        "manual_review_required": True,
        "evidence_promotion": False,
        "content_boundary": {"metadata_only": True, "abstract_or_fulltext_persisted": False, "raw_provider_response_persisted": False},
        "evidence_boundary": {"evidence_promotion": False, "proof_promotion": False, "replication_promotion": False},
        "coverage": packet["coverage"],
        "selected_link_count": len(links),
        "new_physical_record_count": len(new_records),
        "physical_record_ids": sorted(row["physical_record_id"] for row in records),
        "global_physical_record_count_after_field": len(existing_records) + len(new_records),
        "policy_ref": str(POLICY_REL),
    }
    write_json(field_dir / "field-admission.json", admission)

    freeze = {
        "schema": "task172-step09-field-source-freeze-v1",
        "freeze_event": "SCAN_AND_PROVIDER_INPUT_FREEZE",
        "field_code": field,
        "formal_parent_head": parent_head,
        "discovery_parent_head": DISCOVERY_HEAD,
        "packet_sha256": sha256(packet_path),
        "packet_name": packet_path.name,
        "provider_input": input_freeze,
        "raw_response_persistence": False,
        "abstract_or_fulltext_persistence": False,
        "selection_is_metadata_heuristic": True,
        "decision": "STEP09_FIELD_SOURCE_AND_DERIVED_INPUT_FROZEN; METADATA_ONLY; MANUAL_REVIEW_REQUIRED; NO_EVIDENCE_PROMOTION",
    }
    write_json(field_dir / "source-freeze.json", freeze)

    operation_rel = Path(OPERATION_TEMPLATE.format(field=field))
    report_rel = Path(REPORT_TEMPLATE.format(field=field))
    receipt = {
        "schema": "task172-step09-field-build-receipt-v1",
        "field_code": field,
        "field_label": packet["field_label"],
        "formal_parent_head": parent_head,
        "discovery_parent_head": DISCOVERY_HEAD,
        "taxonomy": TAXONOMY,
        "counts": {
            "field_disciplines": len(targets),
            "selected_links": len(links),
            "new_physical_records": len(new_records),
            "global_physical_records_after_field": len(existing_records) + len(new_records),
            "global_links_after_field": len(existing_links) + len(links),
        },
        "metadata_only": True,
        "manual_review_required": True,
        "abstract_or_fulltext_persisted": False,
        "evidence_promotion": False,
        "source_freeze_sha256": sha256(field_dir / "source-freeze.json"),
        "outputs": {},
        "decision": "STEP09_FIELD_ADMITTED_METADATA_ONLY; MANUAL_REVIEW_REQUIRED; PHYSICAL_RECORDS_DEDUPED_GLOBALLY",
    }
    operation = {
        "schema": "task172-step09-field-operation-v1",
        "iteration": 172,
        "step": "09",
        "field_code": field,
        "field_label": packet["field_label"],
        "formal_parent_head": parent_head,
        "taxonomy": TAXONOMY,
        "corpus_identity": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"],
        "admission_status": "METADATA_ADMITTED_MANUAL_REVIEW_REQUIRED",
        "coverage_status": "READY_FOR_MANUAL_REVIEW",
        "counts": receipt["counts"],
        "source_freeze_sha256": receipt["source_freeze_sha256"],
        "content_boundary": admission["content_boundary"],
        "evidence_boundary": admission["evidence_boundary"],
        "decision": receipt["decision"],
    }
    write_json(repo_root / operation_rel, operation)

    report = f"# Task172 Step09 field {field}: {packet['field_label']}\n\n"
    report += f"- Formal parent freeze: `{parent_head}`\n- Discovery preparation parent: `{DISCOVERY_HEAD}`\n- UNESCO authority: 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines\n- Field disciplines: {len(targets)}\n- Selected metadata links: {len(links)}\n- New physical metadata records: {len(new_records)}\n- Global physical records after field: {len(existing_records) + len(new_records)}\n- Global links after field: {len(existing_links) + len(links)}\n\n"
    report += "## Boundary\n\nThis field is admitted only as `GENERAL_KNOWLEDGE_REFERENCE / SCHOLARLY_METADATA`. Provider responses were normalized to metadata hashes and identifiers; no abstract, full text, raw response, evidence, proof, or replication claim was persisted. Every selected row remains manual-review-required. A physical record is stored once globally; field/discipline links may point to it.\n\n"
    report += "## Explicit non-claims\n\nNo provider taxonomy equivalence, scientific relevance validation, external truth, canonical Foundation admission, epistemic acceptance, production readiness, Current promotion, Owner acceptance, Ready transition, merge, rebase, amend, squash, or force-push occurred.\n"
    report_path = repo_root / report_rel
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    committed_fields = sorted(existing_fields | {field}, key=lambda value: FIELDS.index(value))
    pending_fields = [value for value in FIELDS if value not in committed_fields]
    manifest = {
        "schema": "task172-step09-corpus-manifest-v1",
        "formal_write": True,
        "corpus_identity": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"],
        "taxonomy": TAXONOMY,
        "last_field_code": field,
        "last_field_parent_head": parent_head,
        "committed_fields": committed_fields,
        "pending_fields": pending_fields,
        "physical_record_count": len(existing_records) + len(new_records),
        "discipline_link_count": len(existing_links) + len(links),
        "same_physical_record_once": True,
        "metadata_only": True,
        "evidence_promotion": False,
        "policy_ref": str(POLICY_REL),
        "field_admission_refs": [str(DATA_REL / "fields" / value / "field-admission.json") for value in committed_fields],
        "operation_refs": [OPERATION_TEMPLATE.format(field=value) for value in committed_fields],
        "decision": "STEP09_PARTIAL_FIELD_WAVE_FROZEN; REMAINING_FIELDS_PENDING; METADATA_ONLY; MANUAL_REVIEW_REQUIRED",
    }
    write_json(repo_root / MANIFEST_REL, manifest)
    if not (repo_root / POLICY_REL).exists():
        write_json(repo_root / POLICY_REL, policy())

    outputs = {
        "field_admission": sha256(field_dir / "field-admission.json"),
        "source_freeze": sha256(field_dir / "source-freeze.json"),
        "operation": sha256(repo_root / operation_rel),
        "report": sha256(report_path),
        "manifest": sha256(repo_root / MANIFEST_REL),
        "physical_records": sha256(repo_root / LEDGER_REL),
        "discipline_links": sha256(repo_root / LINKS_REL),
    }
    receipt["outputs"] = outputs
    write_json(field_dir / "build-receipt.json", receipt)
    print(json.dumps({
        "field": field,
        "disciplines": len(targets),
        "selected_links": len(links),
        "new_physical_records": len(new_records),
        "global_physical_records": len(existing_records) + len(new_records),
        "global_links": len(existing_links) + len(links),
        "parent_head": parent_head,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
