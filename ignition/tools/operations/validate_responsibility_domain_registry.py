#!/usr/bin/env python3
"""Fail-closed validation for the candidate responsibility-domain registry."""

from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import zlib
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
SOURCE_SNAPSHOT_PATH = IGNITION_ROOT / "data/operations/responsibility-domain-registry-r1-source-snapshot.json.gz"
SOURCE_SNAPSHOT_MAX_COMPRESSED_BYTES = 1_000_000
SOURCE_SNAPSHOT_MAX_UNCOMPRESSED_BYTES = 2_000_000

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
OWNER_ACCEPTANCE_URL = "https://github.com/Arvin-liu/1111/issues/164#issuecomment-7093080490"
OWNER_RELATION_ACCEPTANCE_SOURCE = "owner_relation_status_7094188476"
OWNER_RELATION_ACCEPTANCE_COMMENT = 7094188476
OWNER_RELATION_ACCEPTANCE_URL = "https://github.com/Arvin-liu/1111/issues/164#issuecomment-7094188476"
OWNER_REPOSITORY = "Arvin-liu/1111"
OWNER_ISSUE_NUMBER = 164
OWNER_LOGIN = "Arvin-liu"
OWNER_COMMENT_BODY_SHA256 = "5869ee1b404e1337beaf623528be9689f59a9bcbd7ceccd5b697729870e24f8e"
OWNER_RELATION_COMMENT_BODY_SHA256 = "4165e25ad668f358dc87c367bfb8197af423dcf6f86688ce8a45f734b3cf227c"
OWNER_DECISION_SUMMARY = (
    "Accepts the open unbounded responsibility-domain set, preserves exact R/O/G definitions, "
    "accepts the four named new domain definitions and responsibility boundaries, and accepts "
    "the Q14 architecture attribution principle; it does not authorize Validation Map migration."
)
OWNER_RELATION_DECISION_SUMMARY = (
    "The record states that only Q14 decision_support_mapping primary and G shared_interface "
    "component relations are Owner accepted; all other candidate component relations remain proposed."
)
OWNER_ACCEPTANCE_SCOPE = (
    "Accepts the open domain model, exact R/O/G definitions, four named new domain boundaries, "
    "and the Q14 architecture attribution principle. The specific accepted component relation "
    "statuses are separately bound to #164 comment 7094188476."
)
OWNER_RELATION_ACCEPTANCE_SCOPE = (
    "Records the exact two Owner-accepted component relations: q14 decision_support_mapping primary "
    "and q14 G shared_interface; no other component relations are owner_accepted."
)
OWNER_ACCEPTED_DOMAIN_IDS = frozenset(
    {
        "R",
        "O",
        "G",
        "agent_execution_coordination",
        "formal_repository_change_coordination",
        "bounded_function_execution",
        "decision_support_mapping",
    }
)
OWNER_ACCEPTED_DOMAIN_FINGERPRINTS = {
    "agent_execution_coordination": "6b57b9fc22582cea88afb218ea10b77f49b0b70baf3965ceef9d51838988a392",
    "formal_repository_change_coordination": "63ee7eb2163d3b3f8f1f55d84e0d8621f30b593428dddc37d726fae954873710",
    "bounded_function_execution": "8c8013595601a088ee57c7e01efc5a5781db5b3153402a86c92441054d0e61e4",
    "decision_support_mapping": "606682b90ec216c3c5ce8e3e93390e06c33273d4e9d844b6117f2470a433c827",
}
OWNER_ACCEPTED_DOMAIN_SOURCE_POINTERS = {
    "agent_execution_coordination": "/domains/3",
    "formal_repository_change_coordination": "/domains/4",
    "bounded_function_execution": "/domains/5",
    "decision_support_mapping": "/domains/6",
}
OWNER_ACCEPTED_DOMAIN_FINGERPRINT_FIELDS = [
    "domain_id",
    "name_zh",
    "definition",
    "responsibility_boundary.included",
    "responsibility_boundary.excluded",
]
OWNER_ACCEPTED_RELATIONS = {
    ("q14", "decision_support_mapping", "primary"),
    ("q14", "G", "shared_interface"),
}
OWNER_ACCEPTED_EXTERNAL_INTERFACES: tuple[dict[str, Any], ...] = ()
CANDIDATE_CLAIM_CEILING = {
    "candidate_status": "CANDIDATE_NOT_EFFECTIVE",
    "formal_main_current": False,
    "formal_merge_authorized": False,
    "other_component_relationships_owner_accepted": False,
    "validation_map_routes_authorized": False,
    "execution_authorized": False,
    "review_authorized": False,
    "publication_authorized": False,
    "external_action_authorized": False,
}
Q14_MATURITY_DESCRIPTION = (
    "Manually curated, source-marked, versioned map projection; snapshot freshness and actual "
    "external decision benefit are unverified; it is not a mature automated decision engine."
)
OWNER_Q14_MATURITY_CONSTRAINT = {
    "constraint_id": "q14_maturity_claim_ceiling_7093080490",
    "source_acceptance_record_id": OWNER_ACCEPTANCE_SOURCE,
    "source_repository": OWNER_REPOSITORY,
    "source_issue_number": OWNER_ISSUE_NUMBER,
    "source_comment_id": OWNER_ACCEPTANCE_COMMENT,
    "source_author_login": OWNER_LOGIN,
    "source_content_sha256": OWNER_COMMENT_BODY_SHA256,
    "target_component_id": "q14",
    "target_domain_id": "decision_support_mapping",
    "maturity_claims": {
        "maturity_class": "manual_curated_source_marked_versioned_map_projection",
        "snapshot_freshness": "unverified",
        "external_actual_decision_benefit": "unverified",
        "mature_automated_decision_engine": False,
    },
}
Q14_SHARED_INTERFACE_ENDPOINTS = frozenset({"G", "decision_support_mapping"})
PINNED_OWNER_ACCEPTED_INTERACTION_TUPLES: frozenset[
    tuple[str, str, str, tuple[str, ...], str]
] = frozenset()

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


def _git_blob_oid(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _git_blob_if_available(commit: str, path: str) -> bytes | None:
    env = os.environ.copy()
    env["GIT_NO_LAZY_FETCH"] = "1"
    commit_result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-e", commit],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if commit_result.returncode != 0:
        return None
    blob_result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{commit}:{path}"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if blob_result.returncode != 0:
        return None
    return _git_blob(commit, path)


@lru_cache(maxsize=None)
def _pinned_source_blob(source_id: str, snapshot_path: str) -> bytes:
    anchor = FIXED_SOURCE_ANCHORS.get(source_id)
    if anchor is None or source_id not in {"identity_audit_r0_1", "previous_registry_candidate_a30"}:
        raise ValueError(f"source is not eligible for the pinned provenance snapshot: {source_id}")
    try:
        snapshot_file = Path(snapshot_path)
        if snapshot_file.is_symlink() or not snapshot_file.is_file():
            raise ValueError("pinned source snapshot must be a regular file")
        if snapshot_file.stat().st_size > SOURCE_SNAPSHOT_MAX_COMPRESSED_BYTES:
            raise ValueError("pinned source snapshot exceeds its compressed size limit")
        with gzip.open(snapshot_file, "rb") as stream:
            manifest_bytes = stream.read(SOURCE_SNAPSHOT_MAX_UNCOMPRESSED_BYTES + 1)
            if (
                len(manifest_bytes) > SOURCE_SNAPSHOT_MAX_UNCOMPRESSED_BYTES
                or stream.read(1)
            ):
                raise ValueError("pinned source snapshot exceeds its uncompressed size limit")
        payload = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, EOFError, UnicodeDecodeError, json.JSONDecodeError, zlib.error) as exc:
        raise ValueError(f"pinned source snapshot cannot be loaded: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"format", "sources"}
        or payload.get("format") != "responsibility-domain-registry-r1-source-snapshot-v1"
    ):
        raise ValueError("pinned source snapshot format is invalid")
    sources = payload.get("sources")
    if not isinstance(sources, dict) or set(sources) != {"identity_audit_r0_1", "previous_registry_candidate_a30"}:
        raise ValueError("pinned source snapshot has an unexpected source set")
    entry = sources.get(source_id)
    if not isinstance(entry, dict) or set(entry) != {"commit", "path", "blob_sha1", "content_base64"}:
        raise ValueError(f"pinned source snapshot entry is invalid: {source_id}")
    if (entry.get("commit"), entry.get("path"), entry.get("blob_sha1")) != anchor:
        raise ValueError(f"pinned source snapshot provenance differs from the fixed anchor: {source_id}")
    try:
        content = base64.b64decode(entry["content_base64"], validate=True)
    except (TypeError, ValueError, binascii.Error) as exc:
        raise ValueError(f"pinned source snapshot content encoding is invalid: {source_id}") from exc
    if _git_blob_oid(content) != anchor[2]:
        raise ValueError(f"pinned source snapshot Git blob SHA-1 mismatch: {source_id}")
    git_content = _git_blob_if_available(anchor[0], anchor[1])
    if git_content is not None and git_content != content:
        raise ValueError(f"pinned source snapshot differs from the source commit blob: {source_id}")
    return content


def _source_blob(source_id: str, commit: str, path: str) -> bytes:
    if source_id in {"identity_audit_r0_1", "previous_registry_candidate_a30"}:
        anchor = FIXED_SOURCE_ANCHORS[source_id]
        if (commit, path) != anchor[:2]:
            raise ValueError(f"source snapshot does not cover a different commit/path: {source_id}")
        return _pinned_source_blob(source_id, str(SOURCE_SNAPSHOT_PATH))
    return _git_blob(commit, path)


def _source_blob_sha1(source_id: str, commit: str, path: str) -> str:
    if source_id in {"identity_audit_r0_1", "previous_registry_candidate_a30"}:
        return _git_blob_oid(_source_blob(source_id, commit, path))
    return _git_blob_sha1(commit, path)


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


def _domain_fingerprint_payload(domain: dict[str, Any]) -> dict[str, Any]:
    boundary = domain["responsibility_boundary"]
    return {
        "domain_id": domain["domain_id"],
        "name_zh": domain["name_zh"],
        "definition": domain["definition"],
        "responsibility_boundary": {
            "included": boundary["included"],
            "excluded": boundary["excluded"],
        },
    }


def _domain_fingerprint_sha256(domain: dict[str, Any]) -> str:
    canonical = json.dumps(
        _domain_fingerprint_payload(domain),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _direct_component_ids(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    result = {
        value[key]
        for key in (
            "component_id",
            "source_component_id",
            "target_component_id",
            "from_component_id",
            "to_component_id",
            "source",
            "target",
        )
        if isinstance(value.get(key), str)
    }
    component_ids = value.get("component_ids")
    if isinstance(component_ids, list):
        result.update(item for item in component_ids if isinstance(item, str))
    return result


def _component_ids_from_pointer(document: Any, pointer: str) -> set[str]:
    if pointer == "":
        return _direct_component_ids(document)
    if not pointer.startswith("/"):
        raise ValueError("JSON Pointer must be empty or start with '/'")
    current = document
    ancestors = [current]
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
        ancestors.append(current)
    component_ids: set[str] = set()
    for ancestor in ancestors:
        component_ids.update(_direct_component_ids(ancestor))
    return component_ids


def _validate_identity_audit_subject(
    text: str,
    location: str,
    evidence_key: str,
    expected_component_ids: set[str],
    errors: list[str],
    evidence_location: str,
) -> None:
    item_match = re.search(r"\bitem\s+(\d+)\b", location)
    if item_match is None:
        errors.append(f"{evidence_location}: identity-audit evidence lacks a resolvable item number")
        return
    item_number = item_match.group(1)
    rows = []
    for line in text.splitlines():
        cells = line.split("|")
        if len(cells) < 3:
            continue
        first_cell = cells[1].strip()
        if re.match(rf"^{re.escape(item_number)}(?:\s|$)", first_cell):
            rows.append((line, first_cell))
    if len(rows) != 1:
        errors.append(f"{evidence_location}: identity-audit item {item_number} does not resolve to one row")
        return
    row, first_cell = rows[0]
    if evidence_key not in row:
        errors.append(f"{evidence_location}: evidence key {evidence_key} is absent from its identity-audit row")
    if not any(
        re.search(rf"(?<![A-Za-z0-9._-]){re.escape(component_id)}(?![A-Za-z0-9._-])", first_cell)
        for component_id in expected_component_ids
    ):
        errors.append(
            f"{evidence_location}: identity-audit item {item_number} does not identify any expected component"
        )


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
                    actual = _source_blob_sha1(source_id, source["commit"], source["path"])
                except (subprocess.CalledProcessError, OSError, ValueError) as exc:
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
    expected_component_ids: set[str] | None = None,
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
        else:
            need_component_subject = bool(expected_component_ids) and (
                ref.get("json_pointer") is not None or ref.get("evidence_key")
            )
            raw: bytes | None = None
            actual_blob: str | None = None
            if verify_sources or need_component_subject:
                try:
                    raw = _source_blob(effective_source_id, effective_commit, path)
                    if verify_sources:
                        actual_blob = _source_blob_sha1(effective_source_id, effective_commit, path)
                except (subprocess.CalledProcessError, OSError, ValueError) as exc:
                    errors.append(f"{location}: evidence artifact cannot be resolved ({path}): {exc}")
            if verify_sources and ref.get("blob_sha1") and actual_blob != ref["blob_sha1"]:
                errors.append(f"{location}: evidence blob SHA-1 mismatch ({path})")
            if raw is not None and ref.get("json_pointer") is not None:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                    _json_pointer_get(parsed, ref["json_pointer"])
                except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
                    errors.append(f"{location}: dangling JSON Pointer {ref['json_pointer']!r} in {path}: {exc}")
                else:
                    if expected_component_ids:
                        try:
                            target_component_ids = _component_ids_from_pointer(parsed, ref["json_pointer"])
                        except (KeyError, IndexError, ValueError) as exc:
                            errors.append(
                                f"{location}: cannot bind JSON Pointer {ref['json_pointer']!r} to a component: {exc}"
                            )
                        else:
                            if not target_component_ids.intersection(expected_component_ids):
                                errors.append(
                                    f"{location}: JSON Pointer {ref['json_pointer']!r} identifies components "
                                    f"{sorted(target_component_ids)!r}, expected one of {sorted(expected_component_ids)!r}"
                                )
            if raw is not None and ref.get("evidence_key"):
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append(f"{location}: evidence key points to non-text artifact {path}")
                else:
                    if ref["evidence_key"] not in text:
                        errors.append(f"{location}: evidence key {ref['evidence_key']} is absent from {path}")
                    elif expected_component_ids and not ref.get("json_pointer"):
                        if effective_source_id == "identity_audit_r0_1":
                            _validate_identity_audit_subject(
                                text,
                                ref.get("location", ""),
                                ref["evidence_key"],
                                expected_component_ids,
                                errors,
                                location,
                            )
                        else:
                            errors.append(
                                f"{location}: evidence key has no component-bound JSON Pointer or identity-audit row"
                            )
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
                expected_component_ids,
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
            expected_component_ids: set[str] | None = None
            if section in {"component_identity_snapshot", "component_relationship_decisions", "validation_domain_associations"}:
                expected_component_ids = {record["component_id"]}
            elif section in {"inter_domain_interactions", "external_consumer_interfaces"}:
                expected_component_ids = set(record["component_ids"])
            for ref_index, ref in enumerate(refs or []):
                _resolve_evidence_ref(
                    ref,
                    None,
                    None,
                    sources,
                    errors,
                    verify_sources,
                    f"{section}[{index}].evidence_refs[{ref_index}]",
                    expected_component_ids,
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
    for record_index, record in enumerate(document["owner_acceptance_records"]):
        for fingerprint_index, fingerprint in enumerate(record.get("accepted_domain_fingerprints", [])):
            _resolve_evidence_ref(
                fingerprint["source_ref"],
                None,
                None,
                sources,
                errors,
                verify_sources,
                f"owner_acceptance_records[{record_index}].accepted_domain_fingerprints[{fingerprint_index}].source_ref",
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
    if set(acceptance_records) != {OWNER_ACCEPTANCE_SOURCE, OWNER_RELATION_ACCEPTANCE_SOURCE}:
        errors.append("the R1 candidate must contain exactly the two currently pinned Owner decision records")

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

    current_source = sources.get(OWNER_ACCEPTANCE_SOURCE)
    source_anchor = {
        "source_kind": "github_issue_comment",
        "repository": OWNER_REPOSITORY,
        "comment_id": OWNER_ACCEPTANCE_COMMENT,
        "issue_number": OWNER_ISSUE_NUMBER,
        "url": OWNER_ACCEPTANCE_URL,
        "author_login": OWNER_LOGIN,
        "body_sha256": OWNER_COMMENT_BODY_SHA256,
        "decision_content_summary": OWNER_DECISION_SUMMARY,
    }
    if current_source is None or any(current_source.get(key) != value for key, value in source_anchor.items()):
        errors.append("Owner decision source identity/content hash/summary differs from the pinned #164 comment")

    relation_source = sources.get(OWNER_RELATION_ACCEPTANCE_SOURCE)
    relation_source_anchor = {
        "source_kind": "github_issue_comment",
        "repository": OWNER_REPOSITORY,
        "comment_id": OWNER_RELATION_ACCEPTANCE_COMMENT,
        "issue_number": OWNER_ISSUE_NUMBER,
        "url": OWNER_RELATION_ACCEPTANCE_URL,
        "author_login": OWNER_LOGIN,
        "body_sha256": OWNER_RELATION_COMMENT_BODY_SHA256,
        "decision_content_summary": OWNER_RELATION_DECISION_SUMMARY,
    }
    if relation_source is None or any(
        relation_source.get(key) != value for key, value in relation_source_anchor.items()
    ):
        errors.append("Owner relation-status source differs from the pinned #164 comment")

    record = acceptance_records.get(OWNER_ACCEPTANCE_SOURCE)
    if record is not None:
        if record.get("source_id") != OWNER_ACCEPTANCE_SOURCE:
            errors.append("Owner acceptance record is not bound to the pinned source ID")
        record_anchor = {
            "record_id": OWNER_ACCEPTANCE_SOURCE,
            "source_id": OWNER_ACCEPTANCE_SOURCE,
            "comment_id": OWNER_ACCEPTANCE_COMMENT,
            "url": OWNER_ACCEPTANCE_URL,
            "source_repository": OWNER_REPOSITORY,
            "source_issue_number": OWNER_ISSUE_NUMBER,
            "author_login": OWNER_LOGIN,
            "source_content_sha256": OWNER_COMMENT_BODY_SHA256,
            "decision_content_summary": OWNER_DECISION_SUMMARY,
            "scope": OWNER_ACCEPTANCE_SCOPE,
            "author": OWNER_LOGIN,
        }
        if any(record.get(key) != value for key, value in record_anchor.items()):
            errors.append("Owner acceptance record does not match the pinned decision source and scope")
        if (
            set(record.get("accepted_domain_ids", [])) != OWNER_ACCEPTED_DOMAIN_IDS
            or len(record.get("accepted_domain_ids", [])) != len(OWNER_ACCEPTED_DOMAIN_IDS)
        ):
            errors.append("Owner acceptance record domain IDs differ from the exact pinned accepted set")
        if record.get("accepted_component_relations"):
            errors.append("domain-acceptance record must not independently confer component-relation status")

        if record.get("accepted_external_interfaces") != list(OWNER_ACCEPTED_EXTERNAL_INTERFACES):
            errors.append("Owner decision does not authorize the declared external-interface acceptance scope")

        fingerprints = record.get("accepted_domain_fingerprints", [])
        fingerprint_by_id = {item["domain_id"]: item for item in fingerprints}
        if len(fingerprints) != len(fingerprint_by_id) or set(fingerprint_by_id) != set(OWNER_ACCEPTED_DOMAIN_FINGERPRINTS):
            errors.append("Owner acceptance record lacks the exact four pinned new-domain fingerprints")
        domains_by_id = {row["domain_id"]: row for row in document["domains"]}
        pinned_candidate_document: dict[str, Any] | None = None
        try:
            pinned_candidate_document = json.loads(
                _source_blob("previous_registry_candidate_a30", PRIOR_CANDIDATE_COMMIT, PRIOR_CANDIDATE_PATH).decode("utf-8")
            )
        except (subprocess.CalledProcessError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"pinned Owner-accepted definition source cannot be loaded: {exc}")
        for domain_id, expected_hash in OWNER_ACCEPTED_DOMAIN_FINGERPRINTS.items():
            fingerprint = fingerprint_by_id.get(domain_id)
            if fingerprint is None:
                continue
            expected_source_ref = {
                "source_id": "previous_registry_candidate_a30",
                "commit": PRIOR_CANDIDATE_COMMIT,
                "path": PRIOR_CANDIDATE_PATH,
                "json_pointer": OWNER_ACCEPTED_DOMAIN_SOURCE_POINTERS[domain_id],
                "blob_sha1": FIXED_SOURCE_ANCHORS["previous_registry_candidate_a30"][2],
            }
            if (
                fingerprint.get("fingerprint_fields") != OWNER_ACCEPTED_DOMAIN_FINGERPRINT_FIELDS
                or fingerprint.get("fingerprint_sha256") != expected_hash
                or fingerprint.get("source_ref") != expected_source_ref
            ):
                errors.append(f"Owner acceptance fingerprint/source binding was changed: {domain_id}")
            domain = domains_by_id.get(domain_id)
            if domain is None:
                errors.append(f"Owner-accepted domain is missing from the registry: {domain_id}")
            elif _domain_fingerprint_sha256(domain) != expected_hash:
                errors.append(f"Owner-accepted domain definition/boundary fingerprint mismatch: {domain_id}")

            if pinned_candidate_document is not None:
                try:
                    accepted_source_domain = _json_pointer_get(
                        pinned_candidate_document, OWNER_ACCEPTED_DOMAIN_SOURCE_POINTERS[domain_id]
                    )
                except (KeyError, IndexError, ValueError) as exc:
                    errors.append(f"pinned Owner-accepted definition source cannot resolve for {domain_id}: {exc}")
                else:
                    if (
                        accepted_source_domain.get("domain_id") != domain_id
                        or _domain_fingerprint_sha256(accepted_source_domain) != expected_hash
                    ):
                        errors.append(f"pinned prior-candidate definition does not match Owner acceptance: {domain_id}")

    relation_record = acceptance_records.get(OWNER_RELATION_ACCEPTANCE_SOURCE)
    if relation_record is not None:
        relation_record_anchor = {
            "record_id": OWNER_RELATION_ACCEPTANCE_SOURCE,
            "source_id": OWNER_RELATION_ACCEPTANCE_SOURCE,
            "comment_id": OWNER_RELATION_ACCEPTANCE_COMMENT,
            "url": OWNER_RELATION_ACCEPTANCE_URL,
            "source_repository": OWNER_REPOSITORY,
            "source_issue_number": OWNER_ISSUE_NUMBER,
            "author_login": OWNER_LOGIN,
            "source_content_sha256": OWNER_RELATION_COMMENT_BODY_SHA256,
            "decision_content_summary": OWNER_RELATION_DECISION_SUMMARY,
            "scope": OWNER_RELATION_ACCEPTANCE_SCOPE,
            "author": OWNER_LOGIN,
        }
        if any(relation_record.get(key) != value for key, value in relation_record_anchor.items()):
            errors.append("Owner relation acceptance record does not match its pinned source and scope")
        if relation_record.get("accepted_domain_ids") or relation_record.get("accepted_domain_fingerprints"):
            errors.append("relation-status record must not add or redefine accepted domain boundaries")
        relation_rows = {
            (row["component_id"], row["domain_id"], row["relationship_type"])
            for row in relation_record.get("accepted_component_relations", [])
        }
        if (
            relation_rows != OWNER_ACCEPTED_RELATIONS
            or len(relation_record.get("accepted_component_relations", [])) != len(OWNER_ACCEPTED_RELATIONS)
        ):
            errors.append("Owner relation-status record differs from the two pinned Q14 component relations")
        if relation_record.get("accepted_external_interfaces") != list(OWNER_ACCEPTED_EXTERNAL_INTERFACES):
            errors.append("relation-status record does not authorize external-consumer interfaces")

    for domain in document["domains"]:
        record_id = domain.get("owner_acceptance_record_id")
        if domain["domain_status"] == "owner_accepted":
            record = acceptance_records.get(record_id)
            if (
                record is None
                or domain["domain_id"] not in OWNER_ACCEPTED_DOMAIN_IDS
                or domain["domain_id"] not in record["accepted_domain_ids"]
                or record_id != OWNER_ACCEPTANCE_SOURCE
            ):
                errors.append(f"owner-accepted domain lacks its matching acceptance record: {domain['domain_id']}")
            if not any(ref.get("source_id") == (record or {}).get("source_id") for ref in domain.get("evidence_refs", [])):
                errors.append(f"owner-accepted domain lacks a direct acceptance evidence ref: {domain['domain_id']}")
        elif domain["domain_id"] in OWNER_ACCEPTED_DOMAIN_IDS:
            errors.append(f"pinned Owner-accepted domain was demoted: {domain['domain_id']}")
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
    if current_source is None:
        errors.append("the accepted Q14 relationship rule is not bound to the exact Owner comment")


def _validate_prior_candidate_pointer(
    row: dict[str, Any],
    ref: dict[str, Any],
    candidate_document: dict[str, Any],
    errors: list[str],
    location: str,
) -> None:
    pointer = ref.get("json_pointer")
    if not isinstance(pointer, str):
        errors.append(f"{location}: prior-candidate reference has no JSON Pointer")
        return
    try:
        target = _json_pointer_get(candidate_document, pointer)
        parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.strip("/").split("/")]
        if len(parts) < 2 or parts[0] != "component_mappings" or not parts[1].isdecimal():
            raise ValueError("pointer is outside a component mapping record")
        mapping = _json_pointer_get(candidate_document, f"/component_mappings/{parts[1]}")
    except (KeyError, IndexError, ValueError) as exc:
        errors.append(f"{location}: prior-candidate pointer does not resolve to a mapping record: {exc}")
        return

    component_id = row["component_id"]
    if not isinstance(mapping, dict) or mapping.get("component_id") != component_id:
        errors.append(f"{location}: prior-candidate mapping belongs to a different component")
        return

    if row["decision_status"] == "unresolved":
        if len(parts) != 2 or not isinstance(target, dict):
            errors.append(f"{location}: unresolved assessment must cite its exact prior-candidate component record")
        elif target.get("component_id") != component_id:
            errors.append(f"{location}: prior-candidate component record identity does not match")
        elif target.get("domain_relations"):
            errors.append(f"{location}: unresolved assessment points to a prior component with candidate relations")
        return

    if row["origin"] == "source_matrix_participating_domain":
        expected_pointer = f"/component_mappings/{parts[1]}/source_matrix_participating_domains_at_275_head"
        if pointer != expected_pointer:
            errors.append(f"{location}: source-declared participant does not cite the exact prior participant field")
        if not isinstance(target, list) or row["domain_id"] not in target:
            errors.append(f"{location}: prior-candidate participant field does not contain the declared domain")
        return

    if len(parts) != 4 or parts[2] != "domain_relations" or not parts[3].isdecimal():
        errors.append(f"{location}: relationship must cite an exact prior-candidate domain relation")
        return
    if not isinstance(target, dict) or (
        target.get("domain_id") != row["domain_id"]
        or target.get("relation") != row["relationship_type"]
    ):
        errors.append(f"{location}: prior-candidate domain relation does not match component/domain/type")


def _validate_relationships(
    document: dict[str, Any],
    errors: list[str],
    domain_ids: set[str],
    matrix_by_id: dict[str, dict[str, Any]],
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
    candidate_document: dict[str, Any] | None = None
    try:
        candidate_document = json.loads(
            _source_blob("previous_registry_candidate_a30", PRIOR_CANDIDATE_COMMIT, PRIOR_CANDIDATE_PATH).decode("utf-8")
        )
    except (subprocess.CalledProcessError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"pinned prior candidate cannot be loaded for relation pointer checks: {exc}")

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
            prior_refs = [ref for ref in row["evidence_refs"] if ref.get("source_id") == candidate_source_id]
            if not prior_refs:
                errors.append(f"unresolved assessment lacks its prior-candidate component pointer: {cid}")
            elif candidate_document is not None:
                for ref_index, ref in enumerate(prior_refs):
                    _validate_prior_candidate_pointer(
                        row,
                        ref,
                        candidate_document,
                        errors,
                        f"component_relationship_decisions[{index}].prior_candidate_refs[{ref_index}]",
                    )
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
            prior_refs = [
                ref
                for ref in row["evidence_refs"]
                if ref.get("source_id") == candidate_source_id
                and ref.get("path") == PRIOR_CANDIDATE_PATH
                and isinstance(ref.get("json_pointer"), str)
            ]
            if not prior_refs:
                errors.append(
                    f"candidate relation lacks its prior-candidate source pointer: {cid} -> {domain_id}"
                )
            elif candidate_document is not None:
                for ref_index, ref in enumerate(prior_refs):
                    _validate_prior_candidate_pointer(
                        row,
                        ref,
                        candidate_document,
                        errors,
                        f"component_relationship_decisions[{index}].prior_candidate_refs[{ref_index}]",
                    )
            if status == "owner_accepted":
                key = (cid, domain_id, relation)
                if key not in OWNER_ACCEPTED_RELATIONS:
                    errors.append(f"unaccepted candidate relation was promoted to owner_accepted: {key}")
                if row.get("owner_acceptance_record_id") != OWNER_RELATION_ACCEPTANCE_SOURCE:
                    errors.append(f"owner-accepted relation is not linked to the exact Owner ruling: {key}")
                if not any(ref.get("source_id") == OWNER_RELATION_ACCEPTANCE_SOURCE for ref in row["evidence_refs"]):
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


def _external_interface_binding(interface: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_domain_id": interface["source_domain_id"],
        "target_type": interface["target_type"],
        "external_consumer_id": interface["external_consumer_id"],
        "direction": interface["direction"],
        "interface_type": interface["interface_type"],
        "component_ids": interface["component_ids"],
        "interaction": interface["interaction"],
    }


def _validate_external_interfaces(
    document: dict[str, Any], errors: list[str], domain_ids: set[str], component_ids: set[str]
) -> None:
    acceptance_records = {row["record_id"]: row for row in document["owner_acceptance_records"]}
    accepted_observed: list[dict[str, Any]] = []
    for index, interface in enumerate(document["external_consumer_interfaces"]):
        consumer_id = interface["external_consumer_id"]
        record_id = interface.get("owner_acceptance_record_id")
        if interface["source_domain_id"] not in domain_ids:
            errors.append(f"external_consumer_interfaces[{index}] references an unknown source domain")
        if any(component_id not in component_ids for component_id in interface["component_ids"]):
            errors.append(f"external_consumer_interfaces[{index}] references an unknown component")
        if consumer_id in domain_ids:
            errors.append(f"external consumer {consumer_id} must use an external identity, not a domain_id")
        if interface.get("target_type") != "external_consumer":
            errors.append(f"external consumer {consumer_id} lacks the explicit external_consumer target type")
        if "to_domain_id" in interface:
            errors.append(f"external consumer {consumer_id} must not invent a target domain")

        if interface["interface_status"] == "owner_accepted":
            record = acceptance_records.get(record_id)
            if record is None:
                errors.append(f"owner-accepted external consumer {consumer_id} lacks its exact Owner acceptance record")
                continue
            binding = _external_interface_binding(interface)
            accepted_bindings = record.get("accepted_external_interfaces", [])
            if binding not in accepted_bindings:
                errors.append(
                    f"owner-accepted external consumer {consumer_id} does not match the accepted target/direction/type/components"
                )
            if not any(ref.get("source_id") == record["source_id"] for ref in interface["evidence_refs"]):
                errors.append(f"owner-accepted external consumer {consumer_id} lacks direct Owner evidence")
            accepted_observed.append(binding)
        elif record_id is not None:
            errors.append(f"non-accepted external consumer {consumer_id} has an Owner acceptance record")

    expected_bindings = [
        binding
        for record in document["owner_acceptance_records"]
        for binding in record.get("accepted_external_interfaces", [])
    ]
    if accepted_observed != expected_bindings:
        errors.append("accepted external-interface records and owner_accepted interfaces do not match exactly")


def _validate_claim_ceiling(document: dict[str, Any], errors: list[str]) -> None:
    if document.get("claim_ceiling") != CANDIDATE_CLAIM_CEILING:
        errors.append("claim_ceiling differs from the exact pinned candidate-state and authority boundary")


def _validate_q14_maturity_claims(document: dict[str, Any], errors: list[str]) -> None:
    if document.get("owner_claim_constraints") != [OWNER_Q14_MATURITY_CONSTRAINT]:
        errors.append("Q14 maturity claims are not bound to the exact Owner source constraint")

    domains = document.get("domains")
    if not isinstance(domains, list):
        errors.append("Q14 maturity claim target is missing from the domain list")
        return
    q14_domains = [
        row
        for row in domains
        if isinstance(row, dict) and row.get("domain_id") == "decision_support_mapping"
    ]
    if len(q14_domains) != 1 or q14_domains[0].get("maturity") != Q14_MATURITY_DESCRIPTION:
        errors.append("Q14 maturity description differs from the exact pinned Owner maturity ceiling")

    sources = document.get("sources")
    if not isinstance(sources, list):
        errors.append("Q14 maturity source is missing from the source catalog")
        return
    owner_sources = [
        row
        for row in sources
        if isinstance(row, dict) and row.get("source_id") == OWNER_ACCEPTANCE_SOURCE
    ]
    if len(owner_sources) != 1:
        errors.append("Q14 maturity constraint does not resolve to one pinned Owner source")
        return
    source = owner_sources[0]
    expected_source = {
        "source_kind": "github_issue_comment",
        "repository": OWNER_REPOSITORY,
        "issue_number": OWNER_ISSUE_NUMBER,
        "comment_id": OWNER_ACCEPTANCE_COMMENT,
        "url": OWNER_ACCEPTANCE_URL,
        "author_login": OWNER_LOGIN,
        "body_sha256": OWNER_COMMENT_BODY_SHA256,
    }
    if any(source.get(key) != value for key, value in expected_source.items()):
        errors.append("Q14 maturity constraint Owner source identity/content hash does not match the pinned ruling")


def _validate_q14_shared_interface_endpoints(document: dict[str, Any], errors: list[str]) -> None:
    decisions = document.get("component_relationship_decisions")
    if not isinstance(decisions, list):
        errors.append("the exact Q14 G shared-interface decision is missing")
        return
    rows = [
        row
        for row in decisions
        if isinstance(row, dict) and row.get("decision_id") == "q14::G::shared_interface"
    ]
    if len(rows) != 1:
        errors.append("the exact Q14 G shared-interface decision must appear exactly once")
        return
    row = rows[0]
    endpoints = row.get("interface_domain_ids")
    if (
        row.get("component_id") != "q14"
        or row.get("domain_id") != "G"
        or row.get("relationship_type") != "shared_interface"
        or not isinstance(endpoints, list)
        or len(endpoints) != 2
        or not all(isinstance(endpoint, str) for endpoint in endpoints)
        or set(endpoints) != Q14_SHARED_INTERFACE_ENDPOINTS
    ):
        errors.append("Q14 G shared_interface endpoints must be exactly {G, decision_support_mapping}")


def _validate_inter_domain_interaction_acceptance(document: dict[str, Any], errors: list[str]) -> None:
    interactions = document.get("inter_domain_interactions")
    if not isinstance(interactions, list):
        return
    for index, interaction in enumerate(interactions):
        if not isinstance(interaction, dict):
            continue
        if interaction.get("interaction_status") == "owner_accepted":
            components = interaction.get("component_ids")
            normalized_components = (
                tuple(sorted(components))
                if isinstance(components, list) and all(isinstance(item, str) for item in components)
                else ()
            )
            interaction_tuple = (
                interaction.get("from_domain_id"),
                interaction.get("to_domain_id"),
                interaction.get("interaction_type"),
                normalized_components,
                interaction.get("interaction"),
            )
            if interaction_tuple not in PINNED_OWNER_ACCEPTED_INTERACTION_TUPLES:
                errors.append(
                    "inter-domain interaction lacks a full-tuple Owner acceptance in the pinned sources: "
                    f"{index}"
                )
        elif interaction.get("owner_acceptance_record_id") is not None:
            errors.append(f"non-accepted inter-domain interaction has an Owner acceptance record: {index}")


def validate(
    document: dict[str, Any] | None = None, *, verify_sources: bool = True
) -> list[str]:
    document = document if document is not None else _load_json(REGISTRY_PATH)
    if not isinstance(document, dict):
        return ["registry document must be an object"]
    errors: list[str] = []
    _validate_claim_ceiling(document, errors)
    _validate_q14_maturity_claims(document, errors)
    _validate_q14_shared_interface_endpoints(document, errors)
    _validate_inter_domain_interaction_acceptance(document, errors)
    schema = _load_json(SCHEMA_PATH)
    errors.extend(
        f"{list(error.absolute_path)}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(document)
    )
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

    _validate_external_interfaces(
        document,
        errors,
        domain_ids,
        {row["component_id"] for row in document["component_identity_snapshot"]},
    )

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
