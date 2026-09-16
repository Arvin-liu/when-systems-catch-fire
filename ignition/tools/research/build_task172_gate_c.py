#!/usr/bin/env python3
"""Build the policy-only Task172 Gate C scholarly-admission lock.

Gate C freezes admission semantics, provider roles, rights handling,
correction/retraction handling, conservative deduplication, and a synthetic
cross-domain policy pilot.  It deliberately admits no scholarly rows and
persists no abstract, full text, scan, or OCR content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.research.validate_task172_gate_r import validate as validate_gate_r
from tools.research.validate_task172_gate_t import validate as validate_gate_t


EXPECTED_SOURCE_HEAD = "998b5654248b41a8982d0674bf0368b400b65eec"
EXPECTED_GATE_R_HEAD = "6d704d570827bf8d6ebb65fb65bcdd236056b4d3"
COMMAND_SOURCE = {
    "repository": "Arvin-liu/1111",
    "ref": "b1fc45fb",
    "path": "agent-commands/IGNITION-20260913-176.md",
    "blob_sha": "98fd25bd1886cf8675992413d6c55d1e09b4502f",
}
BRANCH = "work/IGNITION-20260912-172-knowledge-routing-universal-corpus"
TAXONOMY = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
GATE_T_REL = Path("data/research/task172-gate-t-unesco-1988")
GATE_R_REL = Path("data/research/task172-gate-r-routing")
GATE_C_REL = Path("data/research/task172-gate-c-scholarly-admission")
OPERATION_REL = Path("data/operations/iterations/172/step05-scholarly-gate.json")
REPORT_REL = Path("reports/operations/ignition-172-20260913-step05-gate-c-scholarly.md")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def build(repo_root: Path, source_head: str) -> None:
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    if current_head != source_head:
        raise SystemExit(f"GATE_C_BUILD_REFUSED: current HEAD {current_head} != source head {source_head}")

    # Gate C is downstream of the already-confirmed Gate T and Gate R locks.
    validate_gate_t(repo_root)
    validate_gate_r(repo_root)
    gate_t = repo_root / GATE_T_REL
    gate_r = repo_root / GATE_R_REL
    out = repo_root / GATE_C_REL
    out.mkdir(parents=True, exist_ok=True)

    admission_policy = {
        "schema": "task172-gate-c-scholarly-admission-policy-v1",
        "authority": "policy lock only; it does not establish external scholarly truth or admit corpus rows",
        "corpus_identities": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"],
        "mode": "METADATA_ONLY",
        "admission_ceiling": {
            "stable_identifier_required": True,
            "accepted_identifiers": ["DOI", "PROVIDER_STABLE_ID"],
            "required_route_provenance": [
                "unesco_field_code",
                "unesco_discipline_code_or_explicitly_unresolved",
                "taxonomy_version",
                "query_or_seed",
                "provider_id",
                "fetched_at",
                "record_hash",
            ],
            "metadata_rows_admitted_in_gate_c": 0,
            "live_retrieval_in_gate_c": False,
            "abstract_persistence_by_default": False,
            "fulltext_persistence_by_default": False,
            "mass_formal_ingestion_authorized_in_gate_c": False,
        },
        "identity_rules": {
            "general_knowledge_reference": "bounded source navigation and bibliographic linkout; not evidence by presence",
            "scholarly_metadata": "metadata and provenance record only; not an empirical or proof conclusion",
            "provider_failure": "provider failure is not evidence that no literature exists",
            "unresolved_route": "retain unresolved route and manual review; do not coerce a field or discipline",
        },
        "taxonomy_authority": {
            "source": "1988 UNESCO primary document locked by Gate T",
            **TAXONOMY,
            "discrepancies_retained": {"skos_mirror_disciplines": 248, "local_inventory_disciplines": 250, "secondary_subdisciplines": 2183},
        },
        "promotion_boundary": {
            "metadata_is_not_evidence": True,
            "metadata_is_not_proof": True,
            "metadata_is_not_replication": True,
            "no_external_truth_claim": True,
            "manual_review_required_before_any_future_admission": True,
        },
    }

    provider_roles = {
        "schema": "task172-gate-c-provider-roles-v1",
        "authority": "provider roles are bounded retrieval/provenance capabilities, never evidence promotion",
        "roles": [
            {
                "provider_id": "OpenAlex",
                "role": "BROAD_METADATA_DISCOVERY",
                "allowed_uses": ["candidate discovery", "stable work identifiers", "concept and venue metadata", "broad recall probing"],
                "forbidden_uses": ["treating coverage as exhaustive", "treating a work record as evidence", "inferring no literature from a failed request"],
                "no_evidence_promotion": True,
            },
            {
                "provider_id": "Crossref",
                "role": "DOI_REGISTRATION_AND_UPDATE_PROVENANCE",
                "allowed_uses": ["DOI normalization", "registration metadata", "license and link metadata", "update and relation metadata"],
                "forbidden_uses": ["treating registration as peer review", "treating a DOI as proof of a claim", "assuming license scope from a missing field"],
                "no_evidence_promotion": True,
            },
            {
                "provider_id": "OpenAIRE",
                "role": "OPEN_RESEARCH_RELATION_DISCOVERY",
                "allowed_uses": ["research-product relations", "repository and project metadata", "open-access status as a discovery signal"],
                "forbidden_uses": ["treating OA status as a license grant", "treating relation metadata as evidence", "using provider coverage as a completeness claim"],
                "no_evidence_promotion": True,
            },
            {
                "provider_id": "PubMed E-utilities",
                "role": "BIOMEDICAL_INDEX_AND_CORRECTION_RELATIONS",
                "allowed_uses": ["biomedical index metadata", "publication type", "correction and retraction relations", "stable index identifiers"],
                "forbidden_uses": ["generalizing biomedical index coverage to all fields", "treating indexing as claim validation", "using an absent record as no-literature evidence"],
                "no_evidence_promotion": True,
            },
        ],
        "failure_semantics": "provider failure, timeout, quota, denial, or empty response produces a provider-health event and does not become a no-literature conclusion",
        "independence_rule": "one provider cannot silently substitute for another provider's identifier, rights, correction, or retraction role",
    }

    rights_policy = {
        "schema": "task172-gate-c-rights-policy-v1",
        "authority": "copyright and license boundary for metadata-only scholarly admission",
        "mode": "METADATA_ONLY",
        "metadata": {
            "factual_bibliographic_metadata_allowed": True,
            "stable_identifier_allowed": True,
            "provider_linkout_allowed": True,
            "abstract_persistence_default": False,
            "fulltext_persistence_default": False,
        },
        "content_rules": {
            "explicit_license_and_scope_required_for_content": True,
            "oa_status_is_not_a_license": True,
            "unknown_rights_block_abstract_and_fulltext": True,
            "metadata_rights_are_separate_from_content_rights": True,
            "publisher_page_linkout_does_not_grant_republication": True,
        },
        "operational_disposition": {
            "rights_unknown": "retain metadata only; block content persistence",
            "license_present_but_scope_unclear": "retain metadata only; manual rights review",
            "explicit_license_and_scope": "content remains outside Gate C and requires a later scoped admission decision",
        },
    }

    correction_policy = {
        "schema": "task172-gate-c-correction-retraction-policy-v1",
        "authority": "correction and retraction metadata changes record disposition; they never create positive evidence",
        "statuses": ["NOT_OBSERVED", "CORRECTED", "RETRACTED", "EXPRESSION_OF_CONCERN", "UPDATED", "UNKNOWN"],
        "default_status": "UNKNOWN",
        "rules": {
            "NOT_OBSERVED": "no provider relation observed; do not infer that no relation exists",
            "CORRECTED": "retain original metadata, link the correction, and flag the original for manual review",
            "RETRACTED": "retain provenance, quarantine or tombstone positive-use eligibility, and link the retraction notice",
            "EXPRESSION_OF_CONCERN": "retain provenance and block positive evidence use pending manual review",
            "UPDATED": "retain the prior version and link the update; do not silently overwrite historical metadata",
            "UNKNOWN": "rights and correction state are unresolved; no positive evidence promotion",
        },
        "admission_behavior": {
            "correction_or_retraction_relation": "metadata-only quarantine until reviewed",
            "original_record": "retained for audit and linked lineage",
            "positive_evidence": "never granted by correction or retraction metadata",
            "tombstone_policy": "tombstone or quarantine is reversible and preserves stable identifiers",
        },
    }

    dedupe_policy = {
        "schema": "task172-gate-c-conservative-dedupe-policy-v1",
        "authority": "deduplication is record identity hygiene, not evidence adjudication",
        "precedence": [
            "NORMALIZED_DOI",
            "PROVIDER_STABLE_ID_WITH_PROVIDER_NAMESPACE",
            "EXACT_NORMALIZED_TITLE_FIRST_AUTHOR_YEAR",
        ],
        "normalization": {
            "doi": "lowercase, trim URL/prefix punctuation, preserve the normalized DOI string",
            "provider_id": "retain provider namespace and exact stable identifier",
            "title": "Unicode normalize, lowercase, collapse whitespace and punctuation conservatively",
            "author": "use first author only for the third-level collision key",
            "year": "use the declared publication year; do not manufacture a year",
        },
        "collision_rules": {
            "same_normalized_doi": "merge identity references, preserve every provider provenance record",
            "same_provider_id": "merge only inside the provider namespace, preserve cross-provider distinctions",
            "same_title_author_year": "candidate duplicate only; require manual review before merge",
            "unresolved_collision": "retain records separately and mark the collision unresolved",
            "conflicting_metadata": "retain conflicting values with provenance; never choose silently",
        },
        "non_dedupe_claim": "a deduplicated bibliographic identity is not a validated conclusion and does not upgrade evidence maturity",
    }

    pilot = {
        "schema": "task172-gate-c-cross-domain-policy-pilot-v1",
        "authority": "synthetic policy simulation; no live retrieval and no corpus admission",
        "mode": "POLICY_SIMULATION_ONLY",
        "taxonomy": TAXONOMY,
        "domains": [
            {"domain_id": "natural_science", "sample_field_codes": ["21", "22", "23", "24", "25"], "target_per_domain": 5},
            {"domain_id": "engineering_medicine", "sample_field_codes": ["31", "32", "33"], "target_per_domain": 5},
            {"domain_id": "social_science", "sample_field_codes": ["51", "52", "53", "54", "55", "56", "57", "58", "59", "61", "63"], "target_per_domain": 5},
            {"domain_id": "humanities_law_arts_philosophy", "sample_field_codes": ["56", "57", "58", "62", "71", "72"], "target_per_domain": 5},
        ],
        "target_range_per_domain": [5, 12],
        "selection_slots": ["overview", "foundational", "recent", "method", "critical"],
        "field_sample_is_not_coverage_claim": True,
        "synthetic_cases": [
            {"case_id": "doi-less-provider-id", "input": "stable provider ID but no DOI", "expected": "metadata-only candidate; retain provider namespace; no content"},
            {"case_id": "correction-relation", "input": "provider reports CORRECTED", "expected": "retain original, link correction, manual review, no positive evidence"},
            {"case_id": "retraction-relation", "input": "provider reports RETRACTED", "expected": "quarantine or tombstone positive-use eligibility; retain lineage"},
            {"case_id": "rights-unknown", "input": "metadata present and rights unknown", "expected": "metadata only; block abstract and full text"},
            {"case_id": "doi-duplicate", "input": "two providers share one normalized DOI", "expected": "merge identity references; preserve provider provenance"},
            {"case_id": "title-collision", "input": "same normalized title but different author or year", "expected": "retain separately; unresolved collision; no silent merge"},
            {"case_id": "provider-failure", "input": "provider timeout or quota response", "expected": "record provider-health failure; do not infer no literature"},
            {"case_id": "quota-bias", "input": "one domain exhausts a provider quota", "expected": "do not downgrade or exclude the domain; use another declared provider or remain unresolved"},
        ],
        "live_retrieval": False,
        "metadata_rows_admitted": 0,
        "abstract_fulltext_persisted": False,
        "corpus_admission": False,
        "status": "POLICY_PILOT_PASS_NO_CORPUS_ADMISSION",
    }

    policy_values = {
        "admission_policy": admission_policy,
        "provider_roles": provider_roles,
        "rights_policy": rights_policy,
        "correction_retraction_policy": correction_policy,
        "dedupe_policy": dedupe_policy,
        "cross_domain_pilot": pilot,
    }
    policy_files = {
        key: out / filename
        for key, filename in {
            "admission_policy": "admission-policy.json",
            "provider_roles": "provider-roles.json",
            "rights_policy": "rights-policy.json",
            "correction_retraction_policy": "correction-retraction-policy.json",
            "dedupe_policy": "dedupe-policy.json",
            "cross_domain_pilot": "cross-domain-pilot.json",
        }.items()
    }
    for key, path in policy_files.items():
        write_json(path, policy_values[key])

    source_freeze = {
        "schema": "task172-gate-c-source-freeze-v1",
        "freeze_event": "SCAN_INPUT_FREEZE_REUSE",
        "direction_lock": "IGNITION-20260913-176",
        "command_source": COMMAND_SOURCE,
        "formal_pre_freeze": {"head": source_head, "pull_request": 218, "state": "OPEN + DRAFT + unmerged", "branch": BRANCH},
        "taxonomy_authority": {
            "source": "1988 UNESCO primary document locked by Gate T",
            **TAXONOMY,
            "gate_t_parse_sha256": sha256(gate_t / "primary-1988-parse.json"),
            "gate_t_ledger_sha256": sha256(gate_t / "discrepancy-ledger.json"),
        },
        "gate_r_precondition": {
            "source_exact_head": EXPECTED_GATE_R_HEAD,
            "routing_schema_sha256": sha256(gate_r / "routing-schema.json"),
            "controlled_vocabulary_sha256": sha256(gate_r / "controlled-vocabulary.json"),
            "precision_pilot_sha256": sha256(gate_r / "precision-pilot.json"),
            "hard_check_violations": 0,
            "manual_review_rows": 750,
        },
        "authority_inputs": {
            "gate_t_parse_sha256": sha256(gate_t / "primary-1988-parse.json"),
            "gate_t_ledger_sha256": sha256(gate_t / "discrepancy-ledger.json"),
            "gate_r_source_freeze_sha256": sha256(gate_r / "source-freeze.json"),
        },
        "policy_hashes": {key: sha256(path) for key, path in policy_files.items()},
        "scan_inputs": {
            "primary_pdf_persisted": False,
            "ocr_persisted": False,
            "live_scholarly_retrieval": False,
            "abstract_fulltext_persisted": False,
            "corpus_admission": False,
            "mass_formal_ingestion": False,
        },
        "decision": "GATE_C_POLICY_LOCK_ONLY; NO_CORPUS_ADMISSION; NO_MASS_FORMAL_INGESTION",
    }
    source_freeze_path = out / "source-freeze.json"
    write_json(source_freeze_path, source_freeze)

    report_path = repo_root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        f"""# IGNITION-172 Step05 — Gate C scholarly admission policy

Gate C is a policy lock downstream of Gate T and Gate R at Formal head `{source_head}`. It freezes scholarly-admission semantics, provider roles, rights handling, correction/retraction handling, conservative deduplication, and a synthetic cross-domain pilot. It does not establish external scholarly truth.

- Taxonomy authority: the locked 1988 UNESCO primary document, with 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines.
- Gate R precondition: the bounded routing schema and 750-row precision pilot remain manual-review-only and are not promoted into evidence or corpus truth.
- Admission mode: `METADATA_ONLY`; accepted identifiers are DOI or namespaced provider-stable IDs.
- Provider roles: OpenAlex for broad metadata discovery, Crossref for DOI/update provenance, OpenAIRE for open-research relations, and PubMed E-utilities for biomedical index/correction relations. None is an evidence-promotion channel.
- Rights: factual metadata and linkouts may be retained; unknown rights block abstract/full-text persistence; open-access status is not itself a license.
- Corrections/retractions: original records remain linked and auditable; corrected, retracted, expression-of-concern, updated, and unknown states never create positive evidence.
- Deduplication: normalized DOI, then namespaced provider ID, then conservative title/first-author/year candidate matching; unresolved collisions remain separate.
- Cross-domain pilot: four domain buckets, target 5 per domain with an allowed range of 5–12, synthetic policy cases only.
- Live scholarly retrieval, metadata-row admission, abstract/full-text persistence, and mass Formal ingestion: disabled (`0` / `false`).

Decision: Gate C passes for the scholarly-admission policy and provider-role lock only. No scholarly corpus has been admitted, no external source has been adjudicated as truth, and no 24-field Formal ingestion is authorized until this step's own exact-head CI succeeds.
""",
        encoding="utf-8",
    )

    policy_hashes = {key: sha256(path) for key, path in policy_files.items()}
    operation = {
        "schema": "task172-step05-scholarly-gate-v1",
        "step": "Task172 Step05 / Gate C",
        "command_source": COMMAND_SOURCE,
        "source_exact_head": source_head,
        "taxonomy": TAXONOMY,
        "gate_t": {"primary_parse_sha256": sha256(gate_t / "primary-1988-parse.json"), "discrepancy_ledger_sha256": sha256(gate_t / "discrepancy-ledger.json")},
        "gate_r": {"source_exact_head": EXPECTED_GATE_R_HEAD, "precision_pilot_rows": 750, "hard_check_violations": 0, "manual_review_required": 750},
        "policy_hashes": policy_hashes,
        "source_freeze_sha256": sha256(source_freeze_path),
        "report_sha256": sha256(report_path),
        "pilot": {"domains": 4, "target_per_domain": 5, "target_range_per_domain": [5, 12], "synthetic_cases": 8, "live_retrieval": False, "metadata_rows_admitted": 0, "abstract_fulltext_persisted": False, "corpus_admission": False},
        "admission": {"corpus_identities": ["GENERAL_KNOWLEDGE_REFERENCE", "SCHOLARLY_METADATA"], "mode": "METADATA_ONLY", "mass_formal_ingestion_authorized": False},
        "decision": "GATE_C_PASS_FOR_SCHOLARLY_ADMISSION_POLICY_AND_PROVIDER_ROLES; METADATA_ONLY; NO_CORPUS_ADMISSION; 24_FIELD_FORMAL_INGESTION_MAY_BEGIN_AFTER_EXACT_HEAD_CI",
    }
    operation_path = repo_root / OPERATION_REL
    write_json(operation_path, operation)

    receipt = {
        "schema": "task172-gate-c-build-receipt-v1",
        "source_exact_head": source_head,
        "command_source": COMMAND_SOURCE,
        "taxonomy": TAXONOMY,
        "inputs": {"gate_t_parse": sha256(gate_t / "primary-1988-parse.json"), "gate_t_ledger": sha256(gate_t / "discrepancy-ledger.json"), "gate_r_source_freeze": sha256(gate_r / "source-freeze.json")},
        "outputs": {**{key: sha256(path) for key, path in policy_files.items()}, "source_freeze": sha256(source_freeze_path), "operation": sha256(operation_path), "report": sha256(report_path)},
        "counts": {"domains": 4, "target_per_domain": 5, "synthetic_cases": 8, "metadata_rows_admitted": 0},
        "scan_inputs": source_freeze["scan_inputs"],
        "live_retrieval": False,
        "corpus_admission": False,
        "abstract_fulltext_persisted": False,
        "mass_formal_ingestion": False,
        "deterministic": True,
        "decision": "GATE_C_POLICY_LOCK_ONLY; NO_CORPUS_ADMISSION; NO_MASS_FORMAL_INGESTION",
    }
    write_json(out / "build-receipt.json", receipt)
    print(f"TASK172_GATE_C_BUILT head={source_head} domains=4 synthetic_cases=8 metadata_rows_admitted=0 corpus_admission=false")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-head", default=EXPECTED_SOURCE_HEAD)
    args = parser.parse_args()
    build(args.repo_root.resolve(), args.source_head)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
