#!/usr/bin/env python3
"""Fail-closed validation for the candidate responsibility-domain registry."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[2]
REPO_ROOT = IGNITION_ROOT.parent
REGISTRY_PATH = IGNITION_ROOT / "data/operations/responsibility-domain-registry-r1.json"
SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/responsibility-domain-registry-r1.schema.json"

FORMAL_MAIN = "509d49e0b26216ce5443d5c3677aed6c4da4ef4b"
PR275_HEAD = "b188dbab54677484aaf914a134064903b8902a43"
IDENTITY_AUDIT_COMMIT = "f34438c1739a0023e25a2ede2adb8462772707e1"
PRIOR_CANDIDATE_COMMIT = "a30ac9ce110820252523e16019827bdaa941c802"
MAIN_COMPONENTS_PATH = "ignition/data/operations/project-components.json"
MATRIX_PATH = "ignition/data/operations/component-domain-responsibilities-r1.json"
IDENTITY_AUDIT_PATH = "ignition/docs/architecture/rog/component-identity-audit-r0.1.md"
PRIOR_CANDIDATE_PATH = "ignition/docs/architecture/rog/component-domain-registry-candidate-r0.json"
VALIDATION_MAP_PATH = "ignition/data/operations/component-validation-map-r1.json"

OWNER_ACCEPTANCE_SOURCE = "owner_architecture_ruling_7093080490"
OWNER_ACCEPTANCE_COMMENT = 7093080490
OWNER_ACCEPTED_RELATIONS = {
    ("q14", "decision_support_mapping", "primary"),
    ("q14", "G", "shared_interface"),
}

FIXED_SOURCE_ANCHORS = {
    "formal_main_component_registry": (
        FORMAL_MAIN,
        MAIN_COMPONENTS_PATH,
        "a008b89b05efea82967c0fb0bb0ba70574bcff8f",
    ),
    "draft_responsibility_matrix_r1": (
        PR275_HEAD,
        MATRIX_PATH,
        "a2b4f8d0f51e2f72a369749d7bd15f2d3c700e84",
    ),
    "identity_audit_r0_1": (
        IDENTITY_AUDIT_COMMIT,
        IDENTITY_AUDIT_PATH,
        "038daa26a974436eaad4405ea33c05f8dc77edf9",
    ),
    "previous_registry_candidate_a30": (
        PRIOR_CANDIDATE_COMMIT,
        PRIOR_CANDIDATE_PATH,
        "f6c614f2aa0d7fb39d73c6ecf7e3cd486733b7f7",
    ),
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{path}"],
        stderr=subprocess.STDOUT,
    )


@lru_cache(maxsize=None)
def _git_blob_sha1(commit: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", f"{commit}:{path}"],
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def _json_pointer_get(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError("JSON Pointer must be empty or start with '/'")
    current = document
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not part.isdecimal():
                raise KeyError(part)
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(part)
    return current


def _source_maps(document: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    return (
        {row["source_id"]: row for row in document["sources"]},
        {row["record_id"]: row for row in document["owner_acceptance_records"]},
    )


def _validate_source_catalog(document: dict[str, Any], errors: list[str], verify_sources: bool) -> None:
    source_ids = [row["source_id"] for row in document["sources"]]
    if len(source_ids) != len(set(source_ids)):
        errors.append("sources contains duplicate source_id values")
    sources = {row["source_id"]: row for row in document["sources"]}

    for source_id, (commit, path, sha1) in FIXED_SOURCE_ANCHORS.items():
        source = sources.get(source_id)
        if source is None:
            errors.append(f"pinned source is missing: {source_id}")
            continue
        if (source.get("commit"), source.get("path"), source.get("blob_sha1")) != (commit, path, sha1):
            errors.append(f"pinned source anchor drifted: {source_id}")

    for source in document["sources"]:
        source_id = source["source_id"]
        if source["source_kind"] == "git_commit":
            if source.get("commit") is None or source.get("path") is None:
                errors.append(f"git source lacks a commit/path: {source_id}")
                continue
            if verify_sources:
                try:
                    actual = _git_blob_sha1(source["commit"], source["path"])
                except (subprocess.CalledProcessError, OSError) as exc:
                    errors.append(f"git source cannot be resolved for {source_id}: {exc}")
                else:
                    if actual != source.get("blob_sha1"):
                        errors.append(f"git source blob SHA-1 mismatch for {source_id}")
        elif source["source_kind"] == "github_issue_comment":
            if source.get("comment_id") is None or not source.get("url", "").endswith(
                f"issuecomment-{source.get('comment_id')}"
            ):
                errors.append(f"issue-comment source has a mismatched URL/id: {source_id}")


def _resolve_evidence_ref(
    ref: dict[str, Any],
    source_id: str | None,
    commit: str | None,
    sources: dict[str, dict[str, Any]],
    errors: list[str],
    verify_sources: bool,
    location: str,
) -> None:
    effective_source_id = ref.get("source_id", source_id)
    if not effective_source_id or effective_source_id not in sources:
        errors.append(f"{location}: missing or unknown source_id {effective_source_id!r}")
        return
    source = sources[effective_source_id]
    source_kind = source["source_kind"]
    effective_commit = ref.get("commit", commit or source.get("commit"))

    if source_kind == "github_issue_comment":
        if ref.get("comment_id", source.get("comment_id")) != source.get("comment_id"):
            errors.append(f"{location}: issue-comment evidence id does not match source catalog")
        if ref.get("url", source.get("url")) != source.get("url"):
            errors.append(f"{location}: issue-comment evidence URL does not match source catalog")
    else:
        if effective_commit != source.get("commit"):
            errors.append(f"{location}: evidence commit does not match source catalog")
        path = ref.get("path", source.get("path"))
        if not path or path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"{location}: evidence path is absent or unsafe")
        elif verify_sources:
            try:
                raw = _git_blob(effective_commit, path)
                actual_blob = _git_blob_sha1(effective_commit, path)
            except (subprocess.CalledProcessError, OSError) as exc:
                errors.append(f"{location}: evidence artifact cannot be resolved ({path}): {exc}")
                raw = b""
                actual_blob = None
            if ref.get("blob_sha1") and actual_blob != ref["blob_sha1"]:
                errors.append(f"{location}: evidence blob SHA-1 mismatch ({path})")
            if ref.get("json_pointer") is not None:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                    _json_pointer_get(parsed, ref["json_pointer"])
                except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
                    errors.append(f"{location}: dangling JSON Pointer {ref['json_pointer']!r} in {path}: {exc}")
            if ref.get("evidence_key"):
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append(f"{location}: evidence key points to non-text artifact {path}")
                else:
                    if ref["evidence_key"] not in text:
                        errors.append(f"{location}: evidence key {ref['evidence_key']} is absent from {path}")
        if verify_sources and ref.get("evidence_target_path"):
            target = ref["evidence_target_path"]
            try:
                target_blob = _git_blob_sha1(effective_commit, target)
            except (subprocess.CalledProcessError, OSError) as exc:
                errors.append(f"{location}: evidence target cannot be resolved ({target}): {exc}")
            else:
                if ref.get("evidence_target_blob_sha1") and target_blob != ref["evidence_target_blob_sha1"]:
                    errors.append(f"{location}: evidence target blob SHA-1 mismatch ({target})")

    nested = ref.get("evidence_refs", [])
    if isinstance(nested, list):
        for index, child in enumerate(nested):
            _resolve_evidence_ref(
                child,
                effective_source_id,
                effective_commit,
                sources,
                errors,
                verify_sources,
                f"{location}.evidence_refs[{index}]",
            )


def _resolve_all_evidence(document: dict[str, Any], errors: list[str], verify_sources: bool) -> None:
    sources, _ = _source_maps(document)
    groups = [
        ("domains", document["domains"]),
        ("component_identity_snapshot", document["component_identity_snapshot"]),
        ("component_relationship_decisions", document["component_relationship_decisions"]),
        ("inter_domain_interactions", document["inter_domain_interactions"]),
        ("external_consumer_interfaces", document["external_consumer_interfaces"]),
        ("validation_domain_associations", document["validation_domain_associations"]),
    ]
    for section, records in groups:
        for index, record in enumerate(records):
            refs = record.get("evidence_refs")
            if refs is None and section == "component_identity_snapshot":
                refs = [record["source_ref"]]
            for ref_index, ref in enumerate(refs or []):
                _resolve_evidence_ref(
                    ref,
                    None,
                    None,
                    sources,
                    errors,
                    verify_sources,
                    f"{section}[{index}].evidence_refs[{ref_index}]",
                )
            if section == "validation_domain_associations":
                _resolve_evidence_ref(
                    record["migration_authorization_ref"],
                    None,
                    None,
                    sources,
                    errors,
                    verify_sources,
                    f"{section}[{index}].migration_authorization_ref",
                )


def _validate_domain_labels(document: dict[str, Any], errors: list[str]) -> None:
    domain_ids = [row["domain_id"] for row in document["domains"]]
    if len(domain_ids) != len(set(domain_ids)):
        errors.append("domains contains duplicate domain_id values")
    seen: dict[str, str] = {}
    for domain in document["domains"]:
        labels = [domain["domain_id"], domain["name_zh"], *domain.get("aliases", [])]
        local_labels = set()
        for label in labels:
            folded = label.strip().casefold()
            if not folded:
                errors.append(f"domain {domain['domain_id']} has an empty ID/name/alias")
                continue
            if folded in local_labels:
                errors.append(f"domain {domain['domain_id']} repeats a case-folded identity label: {label}")
            local_labels.add(folded)
            previous = seen.get(folded)
            if previous is not None and previous != domain["domain_id"]:
                errors.append(
                    f"domain identity name/alias collision after case-folding: {label!r} "
                    f"({previous} vs {domain['domain_id']})"
                )
            else:
                seen[folded] = domain["domain_id"]


def _validate_snapshots(document: dict[str, Any], errors: list[str], verify_sources: bool) -> tuple[set[str], dict[str, dict[str, Any]]]:
    domains_by_id = {row["domain_id"]: row for row in document["domains"]}
    domain_ids = set(domains_by_id)
    matrix_snapshot = document["source_matrix_snapshot"]
    if matrix_snapshot["source_id"] != "draft_responsibility_matrix_r1":
        errors.append("source_matrix_snapshot does not bind the pinned #275 matrix source")
    if matrix_snapshot["commit"] != PR275_HEAD or matrix_snapshot["path"] != MATRIX_PATH:
        errors.append("source_matrix_snapshot commit/path drifted")
    matrix_source = next(
        (row for row in document["sources"] if row["source_id"] == matrix_snapshot["source_id"]),
        None,
    )
    if matrix_source is None or matrix_snapshot["blob_sha1"] != matrix_source.get("blob_sha1"):
        errors.append("source_matrix_snapshot blob does not match its catalogued source")
    if matrix_snapshot["document"].get("source_commit") != FORMAL_MAIN:
        errors.append("#275 matrix's declared source_commit no longer matches pinned Formal main")
    if verify_sources:
        try:
            matrix_blob = _git_blob(matrix_snapshot["commit"], matrix_snapshot["path"])
            source_matrix_document = json.loads(matrix_blob.decode("utf-8"))
        except (subprocess.CalledProcessError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"pinned #275 source matrix cannot be loaded: {exc}")
        else:
            if matrix_snapshot["document"] != source_matrix_document:
                errors.append("embedded #275 matrix snapshot differs from its exact source commit")

    matrix = matrix_snapshot["document"]
    matrix_rows = matrix.get("components", [])
    matrix_ids = [row.get("component_id") for row in matrix_rows]
    if len(matrix_ids) != len(set(matrix_ids)):
        errors.append("source matrix snapshot contains duplicate component IDs")
    matrix_by_id = {row["component_id"]: row for row in matrix_rows}
    component_rows = document["component_identity_snapshot"]
    component_ids = [row["component_id"] for row in component_rows]
    if len(component_ids) != len(set(component_ids)):
        errors.append("component identity snapshot contains duplicate component IDs")
    if set(component_ids) != set(matrix_ids):
        errors.append("component identity snapshot and #275 source matrix cover different component IDs")

    main_by_id: dict[str, dict[str, Any]] = {}
    if verify_sources:
        try:
            main = json.loads(_git_blob(FORMAL_MAIN, MAIN_COMPONENTS_PATH).decode("utf-8"))
            main_rows = main["components"]
            main_by_id = {row["component_id"]: row for row in main_rows}
        except (subprocess.CalledProcessError, OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            errors.append(f"pinned Formal main component registry cannot be loaded: {exc}")

    if main_by_id and set(main_by_id) != set(component_ids):
        errors.append("component identity snapshot does not match the pinned Formal main component IDs")
    for index, identity in enumerate(component_rows):
        cid = identity["component_id"]
        expected_pointer = f"/components/{index}"
        source_ref = identity["source_ref"]
        if (
            source_ref.get("source_id") != "formal_main_component_registry"
            or source_ref.get("commit") != FORMAL_MAIN
            or source_ref.get("path") != MAIN_COMPONENTS_PATH
            or source_ref.get("json_pointer") != expected_pointer
        ):
            errors.append(f"component identity {cid} is not bound to its exact main registry row")
        raw_matrix_row = matrix_by_id.get(cid)
        if raw_matrix_row and raw_matrix_row.get("canonical_target") != identity["canonical_target"]:
            errors.append(f"#275 canonical_target differs from Formal main for {cid}")
        source_component = main_by_id.get(cid)
        if source_component and any(
            identity[field] != source_component.get(source_field)
            for field, source_field in (
                ("canonical_target", "canonical_target"),
                ("component_type", "component_type"),
                ("lifecycle", "lifecycle"),
            )
        ):
            errors.append(f"component identity snapshot changed protected main metadata for {cid}")

    matrix_definitions = matrix.get("domain_definitions", {})
    for domain_id in ("R", "O", "G"):
        if domain_id not in domains_by_id or domains_by_id[domain_id]["definition"] != matrix_definitions.get(domain_id):
            errors.append(f"the #275 exact {domain_id} definition was not preserved")

    return domain_ids, matrix_by_id


def _validate_acceptance(document: dict[str, Any], errors: list[str], domain_ids: set[str]) -> None:
    sources, acceptance_records = _source_maps(document)
    if len(acceptance_records) != len(document["owner_acceptance_records"]):
        errors.append("owner_acceptance_records contains duplicate record_id values")
    for record_id, record in acceptance_records.items():
        source = sources.get(record["source_id"])
        if source is None or source["source_kind"] != "github_issue_comment":
            errors.append(f"Owner acceptance record {record_id} is not linked to an issue comment source")
            continue
        if (record["comment_id"], record["url"]) != (source.get("comment_id"), source.get("url")):
            errors.append(f"Owner acceptance record {record_id} comment does not match its source catalog entry")
        if len(record["accepted_domain_ids"]) != len(set(record["accepted_domain_ids"])):
            errors.append(f"Owner acceptance record {record_id} has duplicate domain IDs")
        if len(record["accepted_component_relations"]) != len(
            {(row["component_id"], row["domain_id"], row["relationship_type"]) for row in record["accepted_component_relations"]}
        ):
            errors.append(f"Owner acceptance record {record_id} has duplicate component relations")
        if any(domain_id not in domain_ids for domain_id in record["accepted_domain_ids"]):
            errors.append(f"Owner acceptance record {record_id} names an unknown domain")

    for domain in document["domains"]:
        record_id = domain.get("owner_acceptance_record_id")
        if domain["domain_status"] == "owner_accepted":
            record = acceptance_records.get(record_id)
            if record is None or domain["domain_id"] not in record["accepted_domain_ids"]:
                errors.append(f"owner-accepted domain lacks its matching acceptance record: {domain['domain_id']}")
            if not any(ref.get("source_id") == (record or {}).get("source_id") for ref in domain.get("evidence_refs", [])):
                errors.append(f"owner-accepted domain lacks a direct acceptance evidence ref: {domain['domain_id']}")
        elif record_id is not None:
            errors.append(f"non-accepted domain has an Owner acceptance record: {domain['domain_id']}")

    accepted_rows: set[tuple[str, str, str]] = set()
    for record in document["owner_acceptance_records"]:
        accepted_rows.update(
            (row["component_id"], row["domain_id"], row["relationship_type"])
            for row in record["accepted_component_relations"]
        )
    if accepted_rows != OWNER_ACCEPTED_RELATIONS:
        errors.append("the current Owner ruling's accepted component relation scope must remain exactly Q14 primary + G shared_interface")
    current_source = sources.get(OWNER_ACCEPTANCE_SOURCE)
    if (
        current_source is None
        or current_source.get("comment_id") != OWNER_ACCEPTANCE_COMMENT
        or current_source.get("url") != "https://github.com/Arvin-liu/1111/issues/164#issuecomment-7093080490"
    ):
        errors.append("the accepted Q14 relationship rule is not bound to the exact Owner comment")


def _validate_relationships(
    document: dict[str, Any], errors: list[str], domain_ids: set[str], matrix_by_id: dict[str, dict[str, Any]]
) -> None:
    decisions = document["component_relationship_decisions"]
    identities = {row["component_id"] for row in document["component_identity_snapshot"]}
    decision_ids = [row["decision_id"] for row in decisions]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("component_relationship_decisions contains duplicate decision_id values")

    logical_keys: list[tuple[Any, ...]] = []
    source_declared: set[tuple[str, str, str]] = set()
    declared_source_rows: set[tuple[str, str, str]] = set()
    by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_source_id = "previous_registry_candidate_a30"

    for index, row in enumerate(decisions):
        cid = row["component_id"]
        if cid not in identities:
            errors.append(f"relationship decision references an unknown component: {cid}")
            continue
        source_row = matrix_by_id.get(cid)
        if source_row is None:
            errors.append(f"relationship decision has no #275 source row: {cid}")
            continue
        by_component[cid].append(row)
        if (
            row["source_matrix_status_at_275_head"] != source_row["classification_status"]
            or row["source_matrix_primary_domain_at_275_head"] != source_row["primary_responsibility_domain"]
        ):
            errors.append(f"relationship decision rewrites #275 status/primary for {cid}")

        relation = row["relationship_type"]
        domain_id = row["domain_id"]
        status = row["decision_status"]
        if status == "unresolved":
            if domain_id is not None or relation is not None or row["interface_domain_ids"]:
                errors.append(f"unresolved relationship must not name a domain/type: {cid}")
            if row["origin"] != "candidate_review_unassigned":
                errors.append(f"unresolved relationship has an invalid origin: {cid}")
            logical_keys.append((cid, None, None))
            continue

        if domain_id not in domain_ids:
            errors.append(f"relationship decision references an unknown domain: {domain_id}")
            continue
        logical_keys.append((cid, domain_id, relation))
        if relation == "shared_interface":
            interface_domains = row["interface_domain_ids"]
            if not interface_domains or domain_id not in interface_domains or not set(interface_domains) <= domain_ids:
                errors.append(f"shared-interface relation has invalid interface endpoints: {cid} -> {domain_id}")
        elif row["interface_domain_ids"]:
            errors.append(f"non-interface relationship declares interface endpoints: {cid} -> {domain_id}")

        if status == "source_declared":
            source_declared.add((cid, domain_id, relation))
            origin = row["origin"]
            if origin == "source_matrix_primary_classification":
                if relation != "primary" or domain_id != source_row.get("primary_responsibility_domain"):
                    errors.append(f"source-declared primary does not match the matrix for {cid}")
                else:
                    declared_source_rows.add((cid, domain_id, relation))
            elif origin == "source_matrix_participating_domain":
                participants = source_row.get("participating_domains", [])
                if relation != "participating" or domain_id not in participants or domain_id == source_row.get("primary_responsibility_domain"):
                    errors.append(f"source-declared participant does not match the matrix for {cid}")
                else:
                    declared_source_rows.add((cid, domain_id, relation))
            elif origin == "source_matrix_cross_domain_interface":
                matching = [
                    interface for interface in source_row.get("cross_domain_interfaces", [])
                    if interface.get("to_domain") == domain_id
                ]
                if relation != "shared_interface" or not matching:
                    errors.append(f"source-declared interface does not match the matrix for {cid}")
                elif not any(
                    set(row["interface_domain_ids"]) == {item.get("from_domain"), item.get("to_domain")}
                    for item in matching
                ):
                    errors.append(f"source-declared interface endpoints do not match the matrix for {cid}")
                else:
                    declared_source_rows.add((cid, domain_id, relation))
            else:
                errors.append(f"unknown source-declared relation origin: {origin}")
            if row.get("owner_acceptance_record_id") is not None:
                errors.append(f"source-declared relation was promoted to an Owner record: {cid}")
        elif status in {"proposed", "owner_accepted"}:
            if row["origin"] != "candidate_review_proposal":
                errors.append(f"candidate relation has an unexpected origin: {cid}")
            if not any(
                ref.get("source_id") == candidate_source_id
                and ref.get("path") == PRIOR_CANDIDATE_PATH
                and isinstance(ref.get("json_pointer"), str)
                and ref["json_pointer"].startswith("/component_mappings/")
                for ref in row["evidence_refs"]
            ):
                errors.append(f"candidate relation lacks its prior-candidate source pointer: {cid} -> {domain_id}")
            if status == "owner_accepted":
                key = (cid, domain_id, relation)
                if key not in OWNER_ACCEPTED_RELATIONS:
                    errors.append(f"unaccepted candidate relation was promoted to owner_accepted: {key}")
                if row.get("owner_acceptance_record_id") != OWNER_ACCEPTANCE_SOURCE:
                    errors.append(f"owner-accepted relation is not linked to the exact Owner ruling: {key}")
                if not any(ref.get("source_id") == OWNER_ACCEPTANCE_SOURCE for ref in row["evidence_refs"]):
                    errors.append(f"owner-accepted relation lacks its acceptance evidence ref: {key}")
            elif row.get("owner_acceptance_record_id") is not None:
                errors.append(f"proposed relation has an Owner acceptance record: {cid} -> {domain_id}")
        else:
            errors.append(f"unknown relationship decision status: {status}")

    if len(logical_keys) != len(set(logical_keys)):
        errors.append("duplicate logical component/domain/relationship decisions found")
    for cid in identities:
        if cid not in by_component:
            errors.append(f"component has no relationship assessment, including unresolved: {cid}")

    expected_source_rows: set[tuple[str, str, str]] = set()
    for cid, source_row in matrix_by_id.items():
        primary = source_row.get("primary_responsibility_domain")
        if primary is not None:
            expected_source_rows.add((cid, primary, "primary"))
        for participant in source_row.get("participating_domains", []):
            if participant != primary:
                expected_source_rows.add((cid, participant, "participating"))
        for interface in source_row.get("cross_domain_interfaces", []):
            expected_source_rows.add((cid, interface["to_domain"], "shared_interface"))
    if source_declared != expected_source_rows or declared_source_rows != expected_source_rows:
        errors.append("source_declared relationships do not exactly preserve #275 primary/participant/interface declarations")

    for row in decisions:
        if row["decision_status"] == "unresolved" and row["source_matrix_status_at_275_head"] != "UNRESOLVED":
            errors.append(f"unresolved candidate outcome conflicts with a classified #275 source row: {row['component_id']}")


def _validation_route_rows(errors: list[str], verify_sources: bool) -> dict[str, dict[str, Any]]:
    try:
        if verify_sources:
            route_document = json.loads(_git_blob(FORMAL_MAIN, VALIDATION_MAP_PATH).decode("utf-8"))
        else:
            route_document = _load_json(IGNITION_ROOT / "data/operations/component-validation-map-r1.json")
    except (subprocess.CalledProcessError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"pinned Validation Map cannot be resolved for association checks: {exc}")
        return {}
    return {row["component_id"]: row for row in route_document.get("components", [])}


def _validate_route_separation(document: dict[str, Any], errors: list[str], domain_ids: set[str], verify_sources: bool) -> None:
    route_rows = _validation_route_rows(errors, verify_sources)
    seen: set[tuple[str, str, str, str]] = set()
    sources, _ = _source_maps(document)
    for association in document["validation_domain_associations"]:
        component_id = association["component_id"]
        responsibility_domain_id = association["responsibility_domain_id"]
        validation_domain_id = association["validation_domain_id"]
        validation_target_id = association["validation_target_id"]
        if component_id not in route_rows:
            errors.append(f"route crosswalk names a component absent from the current Validation Map: {component_id}")
            continue
        if responsibility_domain_id not in domain_ids:
            errors.append(f"route crosswalk names an unknown responsibility domain: {responsibility_domain_id}")
        row = route_rows[component_id]
        if validation_domain_id not in row.get("domains", []):
            errors.append(f"route crosswalk domain is not declared for {component_id}: {validation_domain_id}")
        if validation_target_id not in row.get("validation_targets", []):
            errors.append(f"route crosswalk target is not declared for {component_id}: {validation_target_id}")
        key = (component_id, responsibility_domain_id, validation_domain_id, validation_target_id)
        if key in seen:
            errors.append(f"duplicate validation-domain association: {key}")
        seen.add(key)

        authorization_ref = association["migration_authorization_ref"]
        auth_source = sources.get(authorization_ref.get("source_id"))
        if (
            auth_source is None
            or auth_source.get("source_kind") != "github_issue_comment"
            or auth_source.get("availability") != "explicit_separate_validation_migration_authorization"
        ):
            errors.append("route crosswalk lacks a separate explicit Owner migration-authorization source")
        elif auth_source.get("comment_id") == OWNER_ACCEPTANCE_COMMENT:
            errors.append("the current architecture ruling does not authorize Validation Map migration")


def derive_domain_views(
    registry: dict[str, Any], decision_statuses: set[str] | None = None
) -> dict[str, dict[str, list[str]]]:
    """Derive overlapping component views from explicit relation decisions."""
    allowed = (
        {"source_declared", "proposed", "owner_accepted"}
        if decision_statuses is None
        else decision_statuses
    )
    result: dict[str, dict[str, set[str]]] = {
        domain["domain_id"]: {
            "core_components": set(),
            "participating_components": set(),
            "interfaces": set(),
        }
        for domain in registry["domains"]
    }
    for row in registry["component_relationship_decisions"]:
        if row["decision_status"] not in allowed or row["relationship_type"] is None:
            continue
        domain_id = row["domain_id"]
        if domain_id not in result:
            continue
        relation = row["relationship_type"]
        if relation == "primary":
            result[domain_id]["core_components"].add(row["component_id"])
        elif relation == "participating":
            result[domain_id]["participating_components"].add(row["component_id"])
        elif relation == "shared_interface":
            endpoints = row.get("interface_domain_ids") or [domain_id]
            for endpoint in endpoints:
                if endpoint in result:
                    result[endpoint]["interfaces"].add(row["component_id"])
    return {
        domain_id: {view: sorted(component_ids) for view, component_ids in views.items()}
        for domain_id, views in result.items()
    }


def validate(
    document: dict[str, Any] | None = None, *, verify_sources: bool = True
) -> list[str]:
    document = document if document is not None else _load_json(REGISTRY_PATH)
    schema = _load_json(SCHEMA_PATH)
    errors = [
        f"{list(error.absolute_path)}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(document)
    ]
    if errors:
        return errors

    _validate_source_catalog(document, errors, verify_sources)
    _validate_domain_labels(document, errors)
    domain_ids, matrix_by_id = _validate_snapshots(document, errors, verify_sources)
    _validate_acceptance(document, errors, domain_ids)
    _resolve_all_evidence(document, errors, verify_sources)
    _validate_relationships(document, errors, domain_ids, matrix_by_id)

    for index, interaction in enumerate(document["inter_domain_interactions"]):
        if interaction["from_domain_id"] not in domain_ids or interaction["to_domain_id"] not in domain_ids:
            errors.append(f"inter_domain_interactions[{index}] references an unknown responsibility domain")
        if any(component_id not in matrix_by_id for component_id in interaction["component_ids"]):
            errors.append(f"inter_domain_interactions[{index}] references an unknown component")
        if interaction["interaction_status"] == "owner_accepted":
            if not (
                interaction["from_domain_id"] == "G"
                and interaction["to_domain_id"] == "decision_support_mapping"
                and "q14" in interaction["component_ids"]
                and interaction.get("owner_acceptance_record_id") == OWNER_ACCEPTANCE_SOURCE
            ):
                errors.append(f"unaccepted inter-domain interaction was promoted: {index}")
        elif interaction.get("owner_acceptance_record_id") is not None:
            errors.append(f"proposed inter-domain interaction has an Owner acceptance record: {index}")

    for index, interface in enumerate(document["external_consumer_interfaces"]):
        if interface["source_domain_id"] not in domain_ids:
            errors.append(f"external_consumer_interfaces[{index}] references an unknown source domain")
        if any(component_id not in matrix_by_id for component_id in interface["component_ids"]):
            errors.append(f"external_consumer_interfaces[{index}] references an unknown component")
        if "to_domain_id" in interface:
            errors.append(f"external consumer {interface['external_consumer_id']} must not invent a target domain")

    _validate_route_separation(document, errors, domain_ids, verify_sources)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    if not args.check:
        return 2
    errors = validate()
    if errors:
        print("RESPONSIBILITY_DOMAIN_REGISTRY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    registry = _load_json(REGISTRY_PATH)
    statuses = Counter(row["decision_status"] for row in registry["component_relationship_decisions"])
    print(
        "RESPONSIBILITY_DOMAIN_REGISTRY_OK "
        f"domains={len(registry['domains'])} components={len(registry['component_identity_snapshot'])} "
        f"source_declared={statuses['source_declared']} proposed={statuses['proposed']} "
        f"owner_accepted={statuses['owner_accepted']} unresolved={statuses['unresolved']} "
        f"validation_associations={len(registry['validation_domain_associations'])} candidate_only=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
