#!/usr/bin/env python3
"""Build the Task172 Step08 metadata-only UNESCO/provider pilot.

The live provider worker runs outside Formal and discards provider bodies.
This builder freezes the sanitized candidate source, derives the crosswalk and
dedupe ledger, and writes one reproducible metadata-admission packet.  It does
not persist abstracts/full text, promote evidence, or claim provider-taxonomy
equivalence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.research.validate_task172_gate_c import validate as validate_gate_c
from tools.research.validate_task172_gate_r import validate as validate_gate_r
from tools.research.validate_task172_gate_t import validate as validate_gate_t


EXPECTED_PARENT_HEAD = "36a1ed4c0e5b91598b5a4fada4bec1539ccc106b"
BRANCH = "work/IGNITION-20260912-172-knowledge-routing-universal-corpus"
PR_NUMBER = 218
COMMAND_SOURCES = [
    {"repository": "Arvin-liu/1111", "ref": "b7c27fab", "path": "agent-commands/IGNITION-20260912-172.md"},
    {"repository": "Arvin-liu/1111", "ref": "ebc75f9c", "path": "agent-commands/IGNITION-20260913-175.md"},
    {"repository": "Arvin-liu/1111", "ref": "b1fc45fb", "path": "agent-commands/IGNITION-20260913-176.md", "blob_sha": "98fd25bd1886cf8675992413d6c55d1e09b4502f"},
]
TAXONOMY = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
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
ALLOWED_PROVIDERS = ["OpenAlex", "Crossref", "OpenAIRE", "PubMed E-utilities"]
BAN_KEYS = {"abstract", "abstracts", "description", "fulltext", "full_text", "full-text", "raw_response", "response_body"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def assert_no_banned_keys(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert str(key).lower() not in BAN_KEYS, f"forbidden content key at {path}.{key}"
            assert_no_banned_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_banned_keys(child, f"{path}[{index}]")


def build_targets(repo_root: Path) -> list[dict]:
    parse = json.loads((repo_root / "data/research/task172-gate-t-unesco-1988/primary-1988-parse.json").read_text(encoding="utf-8"))
    field_labels = {row["code"]: row["label"] for row in parse["hierarchy"]["fields"]}
    by_field: dict[str, list[dict]] = defaultdict(list)
    for row in parse["discipline_records"]:
        by_field[row["parent_field_code"]].append(row)
    targets = []
    for field_code in sorted(by_field):
        row = by_field[field_code][0]
        targets.append({
            "field_code": field_code,
            "field_label": field_labels[field_code],
            "discipline_code": row["code"],
            "discipline_label": row["label"],
            "query_terms": [row["label"]],
            "mapping_type": "QUERY_SEED_ONLY_NO_DIRECT_PROVIDER_EQUIVALENCE",
            "confidence": None,
            "primary_evidence": {
                "source_document_id": row["source_document_id"],
                "source_page": row["source_page"],
                "source_text_anchor": row["source_text_anchor"],
            },
        })
    assert len(targets) == TAXONOMY["fields"]
    return targets


def dedupe_key(candidate: dict) -> str:
    doi = str(candidate.get("doi") or "").strip().lower()
    if doi:
        return "NORMALIZED_DOI:" + doi
    provider = str(candidate.get("provider") or "").strip()
    provider_id = str(candidate.get("provider_record_id") or candidate.get("stable_identifier", {}).get("value") or "").strip()
    if provider_id:
        return "PROVIDER_STABLE_ID:" + provider + ":" + provider_id
    title = " ".join(str(candidate.get("title") or "").lower().split())
    authors = candidate.get("authors") or []
    first_author = str(authors[0] if authors else "").lower().strip()
    year = str(candidate.get("publication_year") or "")
    return "TITLE_AUTHOR_YEAR:" + hashlib.sha256(canonical([title, first_author, year]).encode("utf-8")).hexdigest()


def build(repo_root: Path, source_head: str, source_input: Path | None, request_input: Path | None) -> None:
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    if source_input is not None and current_head != source_head:
        raise SystemExit(f"TASK172_STEP08_BUILD_REFUSED: current HEAD {current_head} != frozen parent {source_head}")
    validate_gate_t(repo_root)
    validate_gate_r(repo_root)
    validate_gate_c(repo_root)

    out = repo_root / DATA_REL
    out.mkdir(parents=True, exist_ok=True)
    targets = build_targets(repo_root)
    target_by_code = {row["discipline_code"]: row for row in targets}
    target_by_field = {row["field_code"]: row for row in targets}

    source_path = repo_root / SOURCE_REL
    if source_input is not None:
        source_rows = read_jsonl(source_input)
        source_rows = sorted(source_rows, key=lambda row: (str(row.get("unesco_field_code")), str(row.get("provider")), str(row.get("candidate_id"))))
        write_jsonl(source_path, source_rows)
    else:
        source_rows = read_jsonl(source_path)
    assert source_rows or source_path.exists(), "Step08 sanitized source candidates are missing"
    for row in source_rows:
        assert row.get("provider") in ALLOWED_PROVIDERS, f"unknown provider: {row.get('provider')}"
        discipline = str(row.get("unesco_discipline_code"))
        assert discipline in target_by_code, f"candidate is outside the 24-discipline pilot target set: {discipline}"
        assert row.get("unesco_field_code") == target_by_code[discipline]["field_code"], f"candidate field mismatch: {row.get('candidate_id')}"
        assert row.get("metadata_only") is True, f"candidate is not metadata-only: {row.get('candidate_id')}"
        assert_no_banned_keys(row, f"candidate:{row.get('candidate_id')}")
        assert row.get("stable_identifier", {}).get("value"), f"candidate has no stable identifier: {row.get('candidate_id')}"

    if request_input is not None:
        request_receipt = json.loads(request_input.read_text(encoding="utf-8"))
        write_json(repo_root / REQUEST_REL, request_receipt)
    else:
        request_receipt = json.loads((repo_root / REQUEST_REL).read_text(encoding="utf-8"))
    assert request_receipt.get("source_exact_head") == source_head, "provider receipt source head drift"
    assert request_receipt.get("raw_response_persistence") is False, "raw provider response persisted"
    assert request_receipt.get("abstract_or_fulltext_persistence") is False, "content persistence boundary drift"
    assert request_receipt.get("provider_failure_is_not_no_literature") is True, "provider failure semantics missing"

    target_packet = {
        "schema": "task172-step08-target-disciplines-v1",
        "authority": "Gate T primary 1988 UNESCO parse; one four-digit seed per each of 24 fields",
        "source_exact_head": source_head,
        "taxonomy": TAXONOMY,
        "targets": targets,
        "discrepancy_policy": "245 primary disciplines remain authoritative; 248 mirror, 250 local inventory and 2183 historical secondary counts remain labeled discrepancies",
    }
    write_json(repo_root / TARGET_REL, target_packet)

    admission_rows = []
    for sequence, candidate in enumerate(source_rows, start=1):
        target = target_by_code[str(candidate["unesco_discipline_code"])]
        source_fingerprint = hashlib.sha256(canonical(candidate).encode("utf-8")).hexdigest()
        admission_rows.append({
            "record_id": f"UNESCO172-STEP08-{sequence:04d}",
            "corpus_identity": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"],
            "admission_status": "METADATA_ADMITTED_MANUAL_REVIEW_REQUIRED",
            "unesco_route": {
                "field_code": target["field_code"],
                "discipline_code": target["discipline_code"],
                "discipline_label": target["discipline_label"],
                "mapping_type": target["mapping_type"],
                "confidence": None,
                "query_terms": target["query_terms"],
            },
            "bibliographic": {
                "stable_identifier": candidate["stable_identifier"],
                "doi": candidate.get("doi"),
                "title": candidate.get("title"),
                "authors": candidate.get("authors", []),
                "institutions": candidate.get("institutions", []),
                "publication_year": candidate.get("publication_year"),
                "publication_date": candidate.get("publication_date"),
                "venue": candidate.get("venue"),
                "work_type": candidate.get("work_type"),
            },
            "provider_signals": {
                "provider": candidate["provider"],
                "provider_record_id": candidate.get("provider_record_id"),
                "peer_review_signal": candidate.get("peer_review_signal"),
                "open_access_signal": candidate.get("open_access_signal", {}),
                "license_signals": candidate.get("license_signals", []),
                "correction_retraction_status": candidate.get("correction_retraction_status", "UNKNOWN"),
                "update_relation_types": candidate.get("update_relation_types", []),
            },
            "source_provenance": {
                "source_url": candidate.get("source_url"),
                "source_query": candidate.get("source_query"),
                "source_response_sha256": candidate.get("source_response_sha256"),
                "fetched_at": request_receipt.get("retrieved_at"),
                "source_fingerprint": source_fingerprint,
            },
            "routing": {
                "tags": [f"UNESCO_FIELD:{target['field_code']}", f"UNESCO_DISCIPLINE:{target['discipline_code']}", "GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA", "METADATA_ONLY", "MANUAL_REVIEW_REQUIRED"],
                "slot": "UNASSIGNED_PENDING_MANUAL_REVIEW",
                "slot_reason": "No content or scientific relevance adjudication performed in Step08 pilot",
                "cross_source_state": "PROVIDER_RECORD_ONLY",
            },
            "content_boundary": {"metadata_only": True, "non_metadata_content_count": 0, "content_persistence": "DISABLED"},
            "evidence_boundary": {"evidence_promotion": False, "proof_promotion": False, "replication_promotion": False},
            "fingerprint": dedupe_key(candidate),
        })
    admission_rows.sort(key=lambda row: row["record_id"])
    write_jsonl(repo_root / ADMISSION_REL, admission_rows)

    groups: dict[str, list[str]] = defaultdict(list)
    for row in admission_rows:
        groups[row["fingerprint"]].append(row["record_id"])
    dedupe_rows = []
    for key in sorted(groups):
        records = groups[key]
        mechanism = key.split(":", 1)[0]
        dedupe_rows.append({
            "dedupe_key": key,
            "mechanism": mechanism,
            "record_ids": records,
            "decision": "IDENTITY_LINK_BY_NORMALIZED_DOI_PROVIDER_PROVENANCE_PRESERVED" if mechanism == "NORMALIZED_DOI" else "RETAIN_PROVIDER_SCOPED_RECORDS_UNRESOLVED_FOR_MANUAL_REVIEW",
            "merge_evidence": "identity hygiene only; no scientific or content equivalence asserted",
        })
    write_jsonl(repo_root / DEDUPE_REL, dedupe_rows)

    records_by_discipline: dict[str, list[dict]] = defaultdict(list)
    for row in admission_rows:
        records_by_discipline[row["unesco_route"]["discipline_code"]].append(row)
    counts_by_provider = dict(request_receipt.get("candidate_count_by_provider", {}))
    crosswalk_rows = []
    for target in targets:
        records = records_by_discipline.get(target["discipline_code"], [])
        provider_counts = {provider: sum(1 for row in records if row["provider_signals"]["provider"] == provider) for provider in ALLOWED_PROVIDERS}
        attempted = ["OpenAlex", "Crossref", "OpenAIRE"] + (["PubMed E-utilities"] if target["field_code"] == "32" else [])
        crosswalk_rows.append({
            "field_code": target["field_code"],
            "field_label": target["field_label"],
            "unesco_discipline_code": target["discipline_code"],
            "unesco_discipline_label": target["discipline_label"],
            "mapping_type": target["mapping_type"],
            "confidence": None,
            "query_terms": target["query_terms"],
            "primary_evidence": target["primary_evidence"],
            "providers_attempted": attempted,
            "provider_candidate_counts": provider_counts,
            "candidate_record_ids": [row["record_id"] for row in records],
            "provider_taxonomy_ids": [],
            "manual_review_required": True,
            "coverage_interpretation": "query attempt and candidate availability only; not completeness and not a provider-to-UNESCO equivalence",
        })
    crosswalk = {
        "schema": "task172-step08-unesco-modern-index-crosswalk-pilot-v1",
        "authority": "UNESCO codes/labels come only from Gate T primary parse; provider indexes are retrieval signals",
        "source_exact_head": source_head,
        "taxonomy": TAXONOMY,
        "pilot_scope": {"target_fields": len(targets), "target_disciplines": len(targets), "records": len(admission_rows), "metadata_only": True, "manual_review_required": True},
        "provider_candidate_counts": counts_by_provider,
        "no_direct_mapping_rule": True,
        "rows": crosswalk_rows,
        "decision": "STEP08_PILOT_PASS_FOR_METADATA_PIPELINE; NO_DIRECT_PROVIDER_EQUIVALENCE; NO_SCIENTIFIC_EVIDENCE_PROMOTION",
    }
    write_json(repo_root / CROSSWALK_REL, crosswalk)

    freeze = {
        "schema": "task172-step08-source-freeze-v1",
        "freeze_event": "SCAN_AND_PROVIDER_INPUT_FREEZE",
        "direction_locks": ["IGNITION-20260913-175", "IGNITION-20260913-176", "IGNITION-20260912-172"],
        "command_sources": COMMAND_SOURCES,
        "formal_pre_freeze": {"head": source_head, "branch": BRANCH, "pull_request": PR_NUMBER, "state": "OPEN + DRAFT + unmerged"},
        "taxonomy_authority": {"source": "1988 UNESCO primary document locked by Gate T", **TAXONOMY, "gate_t_parse_sha256": sha256(repo_root / "data/research/task172-gate-t-unesco-1988/primary-1988-parse.json"), "gate_t_ledger_sha256": sha256(repo_root / "data/research/task172-gate-t-unesco-1988/discrepancy-ledger.json")},
        "gate_r_precondition": {"source_exact_head": "6d704d570827bf8d6ebb65fb65bcdd236056b4d3", "precision_pilot_rows": 750, "hard_check_violations": 0},
        "gate_c_precondition": {"policy_receipt_sha256": sha256(repo_root / "data/research/task172-gate-c-scholarly-admission/build-receipt.json"), "policy_only": True, "exact_head_ci_required_before_this_step": True},
        "provider_input": {"request_receipt_sha256": sha256(repo_root / REQUEST_REL), "source_candidates_sha256": sha256(source_path), "raw_response_persistence": False, "abstract_or_fulltext_persistence": False, "provider_failure_is_not_no_literature": True},
        "derived_outputs": {"target_disciplines": sha256(repo_root / TARGET_REL), "metadata_admission": sha256(repo_root / ADMISSION_REL), "crosswalk": sha256(repo_root / CROSSWALK_REL), "dedupe": sha256(repo_root / DEDUPE_REL)},
        "decision": "STEP08_SOURCE_AND_DERIVED_CLOSURE_FROZEN; METADATA_ONLY; NO_PROVIDER_TAXONOMY_EQUIVALENCE; NO_EVIDENCE_PROMOTION",
    }
    write_json(repo_root / FREEZE_REL, freeze)

    report_path = repo_root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        f"""# IGNITION-172 Step08 — UNESCO/provider metadata pilot

This logical step follows Gate T, Gate R and the Gate C policy/provider lock. The frozen parent is `{source_head}` on the existing Task172 branch and Draft PR #{PR_NUMBER}.

- Gate T authority: the 1988 UNESCO primary parse, 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines. The 248 mirror, 250 local inventory and 2183 historical secondary counts remain discrepancy values, not silent substitutes.
- Pilot scope: one Gate T four-digit discipline seed from each of the 24 fields; provider requests were bounded to OpenAlex, Crossref and OpenAIRE, with PubMed E-utilities only for the medical field.
- Crosswalk status: `QUERY_SEED_ONLY_NO_DIRECT_PROVIDER_EQUIVALENCE`; provider taxonomy identifiers are not copied into UNESCO identity, and every target remains manual-review-required.
- Results: {len(admission_rows)} sanitized metadata candidates admitted as `GENERAL_KNOWLEDGE_REFERENCE` / `SCHOLARLY_METADATA`; no content body was persisted, no scientific relevance was adjudicated, and no evidence/proof/replication promotion occurred.
- Dedupe: normalized DOI first, then namespaced provider ID, retaining provider provenance and unresolved collisions.
- Failure semantics: provider errors or empty results are provider-health events and are not no-literature conclusions.

Decision: `STEP08_PILOT_PASS_FOR_METADATA_PIPELINE; NO_DIRECT_PROVIDER_EQUIVALENCE; NO_SCIENTIFIC_EVIDENCE_PROMOTION`. The 24-field Formal ingestion lanes may now prepare under the one-field/one-commit gate, subject to exact-head CI and the unchanged Draft/open lifecycle ceiling.
""",
        encoding="utf-8",
    )

    operation = {
        "schema": "task172-step08-scholarly-pilot-v1",
        "step": "Task172 Step08 / UNESCO-modern-index metadata pilot",
        "command_sources": COMMAND_SOURCES,
        "source_exact_head": source_head,
        "taxonomy": TAXONOMY,
        "gate_t": {"primary_parse_sha256": sha256(repo_root / "data/research/task172-gate-t-unesco-1988/primary-1988-parse.json"), "discrepancy_ledger_sha256": sha256(repo_root / "data/research/task172-gate-t-unesco-1988/discrepancy-ledger.json")},
        "gate_r": {"source_exact_head": "6d704d570827bf8d6ebb65fb65bcdd236056b4d3", "precision_pilot_rows": 750, "hard_check_violations": 0},
        "gate_c": {"policy_receipt_sha256": sha256(repo_root / "data/research/task172-gate-c-scholarly-admission/build-receipt.json"), "policy_only": True},
        "pilot": {"target_fields": len(targets), "target_disciplines": len(targets), "metadata_candidates": len(source_rows), "metadata_admitted": len(admission_rows), "manual_review_required": len(admission_rows), "provider_candidate_counts": counts_by_provider, "no_direct_provider_equivalence": True, "evidence_promotion": False, "content_persistence": False},
        "source_freeze_sha256": sha256(repo_root / FREEZE_REL),
        "crosswalk_sha256": sha256(repo_root / CROSSWALK_REL),
        "dedupe_sha256": sha256(repo_root / DEDUPE_REL),
        "report_sha256": sha256(report_path),
        "decision": "STEP08_PILOT_PASS_FOR_METADATA_PIPELINE; NO_DIRECT_PROVIDER_EQUIVALENCE; NO_SCIENTIFIC_EVIDENCE_PROMOTION",
    }
    write_json(repo_root / OPERATION_REL, operation)

    outputs = {key: sha256(repo_root / rel) for key, rel in {"source_candidates": SOURCE_REL, "provider_request_receipt": REQUEST_REL, "target_disciplines": TARGET_REL, "metadata_admission": ADMISSION_REL, "crosswalk": CROSSWALK_REL, "dedupe": DEDUPE_REL, "source_freeze": FREEZE_REL, "operation": OPERATION_REL, "report": REPORT_REL}.items()}
    receipt = {
        "schema": "task172-step08-build-receipt-v1",
        "source_exact_head": source_head,
        "command_sources": COMMAND_SOURCES,
        "taxonomy": TAXONOMY,
        "counts": {"target_fields": len(targets), "target_disciplines": len(targets), "source_candidates": len(source_rows), "metadata_admitted": len(admission_rows), "manual_review_required": len(admission_rows), "dedupe_clusters": len(dedupe_rows)},
        "outputs": outputs,
        "raw_response_persistence": False,
        "content_persistence": False,
        "evidence_promotion": False,
        "no_direct_provider_equivalence": True,
        "provider_failure_is_not_no_literature": True,
        "deterministic_derived_closure": True,
        "decision": "STEP08_PILOT_PASS_FOR_METADATA_PIPELINE; NO_DIRECT_PROVIDER_EQUIVALENCE; NO_SCIENTIFIC_EVIDENCE_PROMOTION",
    }
    write_json(repo_root / RECEIPT_REL, receipt)
    print(f"TASK172_STEP08_PILOT_BUILT head={source_head} targets={len(targets)} candidates={len(source_rows)} admitted={len(admission_rows)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-head", default=EXPECTED_PARENT_HEAD)
    parser.add_argument("--source-input", type=Path)
    parser.add_argument("--request-input", type=Path)
    args = parser.parse_args()
    build(args.repo_root.resolve(), args.source_head, args.source_input.resolve() if args.source_input else None, args.request_input.resolve() if args.request_input else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
