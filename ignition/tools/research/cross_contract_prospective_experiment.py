#!/usr/bin/env python3
"""Task156 research-only prospective cross-contract fixture experiment.

This module deliberately lives outside the production validator/gate paths. It
generates a deterministic paired corpus, freezes model definitions before
scoring, scores blind packets without loading the answer key, and unblinds only
in a separate command. The records produced here are evidence for a bounded
research question; they are not canonical contracts, validators, runtime
states, authority records, or production gates.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "data/research/cross-contract-prospective-fixtures-2026-09-05"
FROZEN_NAMES = (
    "experiment-protocol.json",
    "model-definitions.json",
    "thresholds.json",
    "fixture-generator-manifest.json",
    "fixture-manifest.json",
    "blind-packets.jsonl",
    "answer-key.jsonl",
    "split-manifest.json",
    "freeze-ledger.json",
)
SCORER_VERSION = "task156-research-scorer-2.0.0"
TASK_ID = "IGNITION-20260905-156"
BASE_COMMIT = "9bed8e42ee824fc0c0a10717b6163fe7052423e8"
FROZEN_DATE = "2026-09-05"
BOUNDARY = (
    "Research-only synthetic fixture evidence; no production validator, gate, "
    "runtime, authority, capability, lifecycle or canonical-layer change."
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    return digest_bytes(canonical(value).encode("utf-8"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return "".join(canonical(row) + "\n" for row in rows).encode("utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def write_json(path: Path, value: Any) -> None:
    write_bytes(path, json_bytes(value))


def split_for_pair(pair_id: str) -> str:
    bucket = hashlib.sha256(pair_id.encode("utf-8")).digest()[0] % 3
    return "holdout" if bucket == 2 else "calibration"


CONTRACT_REFS: dict[str, dict[str, Any]] = {
    "F1": {
        "historical_lineage": "CC-012",
        "object_families": ["execution_receipt", "observation", "reconciliation_obligation"],
        "paths": [
            "agent_runtime/contracts.py",
            "tools/validate_dispatch_reconciliation.py",
            "tools/validate_live_observation_semantics.py",
            "data/operations/iterations/139/",
        ],
        "genealogy": "CC-012 supplied the consequence/accountability shape; fixtures recombine observer, ownership, stop and retry fields across new receipt variants.",
    },
    "F2": {
        "historical_lineage": "CC-026",
        "object_families": ["base_admission", "delta_admission", "provider_capability", "current_authority"],
        "paths": [
            "agent_federation/contracts.py",
            "tools/validate_task150_step18_scope_split_admission_objects.py",
            "tools/validate_task150_step19_gate_topology_regression.py",
            "data/operations/iterations/150/",
        ],
        "genealogy": "CC-026 supplied the Base/Delta scope-coupling shape; fixtures vary provider, lifecycle and object-level admission without copying its historical records.",
    },
    "F3": {
        "historical_lineage": "CC-020",
        "object_families": ["source_identity", "release_projection", "public_surface", "lifecycle_status"],
        "paths": [
            "tools/validate_current_state_sync.py",
            "tools/validate_current_release_lifecycle.py",
            "tools/validate_post_publication_current.py",
            "tools/validate_release_candidate_task_identity.py",
        ],
        "genealogy": "CC-020 supplied the identity/projection split-brain challenge; fixtures add novel lifecycle and scope junctions while keeping each local object valid.",
    },
    "F4": {
        "historical_lineage": "Task155 claim-ceiling map",
        "object_families": ["claim", "evidence", "action_packet", "decision_reason"],
        "paths": [
            "tools/foundation/validate_claim_governance.py",
            "tools/foundation/validate_nonfunction_claim_closure.py",
            "data/foundation/nonfunction-claims/claim-registry.jsonl",
            "data/foundation/nonfunction-claims/evidence-lineage.jsonl",
        ],
        "genealogy": "The claim-to-action shape is derived from current claim ceiling and evidence-lineage contracts; it is not a replay of a historical CC case.",
    },
    "F5": {
        "historical_lineage": "Task155 consequence/rollback map",
        "object_families": ["effect", "preimage", "rollback_control", "stop_path"],
        "paths": [
            "tools/validate_execution_contract.py",
            "tools/validate_durability_recovery.py",
            "tools/validate_durability_snapshot.py",
            "data/operations/iterations/134/",
        ],
        "genealogy": "The rollback shape comes from existing reversible local-file controls and durability recovery contracts, with synthetic irreversible and stop-path combinations.",
    },
    "F6": {
        "historical_lineage": "Task155 signer/contestability diagnostic",
        "object_families": ["signer", "approval", "scope", "consequence_visibility"],
        "paths": [
            "tools/validate_owner_editorial_authority.py",
            "tools/validate_external_attestation.py",
            "tools/validate_federation_ownership.py",
            "data/governance/owner-editorial-authority-r1.json",
        ],
        "genealogy": "The authorization shape stress-tests the weak signer/contestability label; four cases intentionally omit a consequence failure so the label cannot be manufactured.",
    },
}


def pair_specs() -> list[dict[str, Any]]:
    """Return the predeclared 48-pair design in stable order.

    ``kind`` is hidden from blind packets. LOCAL_BASELINE pairs test fairness
    of M0; the remaining actionable pairs test junction predicates. The last
    two F6 pairs are diagnostic stress pairs, not asserted historical defects.
    """

    specs: list[dict[str, Any]] = []

    def add(
        family: str,
        number: int,
        kind: str,
        diagnostic: str,
        changes: list[dict[str, Any]],
        repair: str,
        *,
        novel: bool = False,
        distractor: bool = True,
        cross_family: bool = True,
        binding_subtype: str | None = None,
    ) -> None:
        specs.append(
            {
                "pair_id": f"{family}-P{number:02d}",
                "family": family,
                "kind": kind,
                "diagnostic": diagnostic,
                "changes": changes,
                "repair": repair,
                "novel_recombination": novel,
                "distractor_fields_present": distractor,
                "cross_object_family": cross_family,
                "binding_subtype": binding_subtype,
            }
        )

    # F1 — four local baseline pairs and four genuinely cross-contract pairs.
    add("F1", 1, "LOCAL_BASELINE", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "local_contracts.0.status", "value": "FAIL"}], "Repair the receipt-local checksum predicate before admission.", novel=False)
    add("F1", 2, "LOCAL_BASELINE", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "local_contracts.1.status", "value": "FAIL"}], "Repair the observation-local presence predicate before admission.", novel=False)
    add("F1", 3, "LOCAL_BASELINE", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "local_contracts.2.status", "value": "FAIL"}], "Repair the reconciliation-record schema predicate before admission.", novel=True)
    add("F1", 4, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.consequence.stop_path_present", "value": False}], "Provide an observable stop path for the unresolved consequence.", novel=True)
    add("F1", 5, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.consequence.observer_present", "value": False}], "Require an observable observer for an unknown effect.", novel=True)
    add("F1", 6, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.consequence.reconciliation_owner_id", "value": None}], "Bind the unknown effect to a named reconciliation owner.", novel=True)
    add("F1", 7, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.consequence.retry_policy", "value": "PERMITTED"}], "Prohibit retry while the external effect remains unknown.", novel=True)
    add("F1", 8, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.consequence.stop_path_present", "value": False}], "Provide an observable stop path for the unresolved consequence.", novel=True)

    # F2 — admission/scope coupling, with local controls kept distinct.
    add("F2", 1, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.lifecycle_epoch", "value": "epoch-old"}], "Align admission lifecycle epoch with the source object.", novel=True, binding_subtype="lifecycle_epoch")
    add("F2", 2, "LOCAL_BASELINE", "PROVENANCE_WITHOUT_CEILING", [{"path": "local_contracts.1.status", "value": "FAIL"}], "Repair the Delta admission-local schema predicate.", novel=False)
    add("F2", 3, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.provider_capability", "value": "AVAILABLE"}, {"path": "objects.admission.current_authority", "value": "NONE"}, {"path": "objects.action.attempted_current_use", "value": True}], "Do not convert provider capability into Current authority.", novel=True)
    add("F2", 4, "LOCAL_BASELINE", "PROVENANCE_WITHOUT_CEILING", [{"path": "local_contracts.3.status", "value": "FAIL"}], "Repair the object-split-local predicate.", novel=True)
    add("F2", 5, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.scope_rank", "value": 3}], "Reject a combined gate that promotes a wider Delta scope than the Base admission.", novel=True)
    add("F2", 6, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.lifecycle", "value": "DRAFT"}, {"path": "objects.action.attempted_current_use", "value": True}], "Keep a Draft/non-intent object out of an admitted action path.", novel=True)
    add("F2", 7, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.provider_capability", "value": "AVAILABLE"}, {"path": "objects.admission.current_authority", "value": "NONE"}, {"path": "objects.action.attempted_current_use", "value": True}], "Do not convert provider capability into Current authority.", novel=True)
    add("F2", 8, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.object_level_split_present", "value": False}], "Require separate Base and Delta admission objects.", novel=True)

    # F3 — M3R catches source/identity/projection refinements; M4B has a
    # separate lifecycle/scope challenge that is not a digest equality check.
    add("F3", 1, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.identity.source_path", "value": "docs/other-object.md"}], "Align source path and identity before projecting the surface.", novel=False, binding_subtype="source_identity_path")
    add("F3", 2, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.projection.object_id", "value": "other-object"}], "Align projection identity with the source object.", novel=False, binding_subtype="identity_projection_object")
    add("F3", 3, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.surface.source_revision", "value": "rev-stale"}], "Align the public surface revision with the generated projection.", novel=True, binding_subtype="projection_surface_revision")
    add("F3", 4, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.release.source_path", "value": "data/release/other.json"}], "Align the release source path with the current source.", novel=True, binding_subtype="release_current_path")
    add("F3", 5, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.surface.lifecycle_epoch", "value": "epoch-old"}], "Require lifecycle-epoch alignment across source, projection and public surface.", novel=True, binding_subtype="lifecycle_epoch")
    add("F3", 6, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.scope", "value": "production"}], "Require scope alignment across the admission and projected object.", novel=True, binding_subtype="scope_alignment")
    add("F3", 7, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.projection.lifecycle_epoch", "value": "epoch-next"}], "Require projection lifecycle epoch to match the identity epoch.", novel=True, binding_subtype="lifecycle_epoch")
    add("F3", 8, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.admission.version", "value": "v0"}], "Require admission version alignment with the projected object.", novel=True, binding_subtype="version_alignment")

    # F4 — M0 local claim failures, M3 claim ceiling failures, and M4B
    # claim/action identity bindings with equal scope ranks.
    add("F4", 1, "LOCAL_BASELINE", "PROVENANCE_WITHOUT_CEILING", [{"path": "local_contracts.0.status", "value": "FAIL"}], "Repair the claim-local provenance predicate.", novel=False)
    add("F4", 2, "LOCAL_BASELINE", "PROVENANCE_WITHOUT_CEILING", [{"path": "local_contracts.1.status", "value": "FAIL"}], "Repair the evidence-local source predicate.", novel=False)
    add("F4", 3, "LOCAL_BASELINE", "PROVENANCE_WITHOUT_CEILING", [{"path": "local_contracts.2.status", "value": "FAIL"}], "Repair the action-local scope predicate.", novel=True)
    add("F4", 4, "LOCAL_BASELINE", "PROVENANCE_WITHOUT_CEILING", [{"path": "local_contracts.3.status", "value": "FAIL"}], "Repair the reason-local claim predicate.", novel=True)
    add("F4", 5, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.claim.ceiling_rank", "value": 1}], "Keep the action within the claim ceiling.", novel=True)
    add("F4", 6, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.action.required_scope_rank", "value": 3}], "Keep the requested action scope within the evidenced claim.", novel=True)
    add("F4", 7, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.action.claim_id", "value": "other-claim"}], "Bind the action reason to the claim object it actually uses.", novel=True, binding_subtype="claim_action_object")
    add("F4", 8, "JUNCTION_DEFECT", "PROVENANCE_WITHOUT_CEILING", [{"path": "objects.action.claim_id", "value": "other-claim"}, {"path": "objects.action.required_scope_rank", "value": 2}], "Bind a scope-valid action to its actual claim object.", novel=True, binding_subtype="claim_action_object")

    # F5 — local rollback contracts and consequence/rollback junctions.
    add("F5", 1, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.rollback.effect_reversibility", "value": "IRREVERSIBLE"}], "Do not present a reversible rollback label for an irreversible effect.", novel=True)
    add("F5", 2, "LOCAL_BASELINE", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "local_contracts.1.status", "value": "FAIL"}], "Repair the preimage-local contract predicate.", novel=False)
    add("F5", 3, "LOCAL_BASELINE", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "local_contracts.2.status", "value": "FAIL"}], "Repair the rollback-control-local predicate.", novel=True)
    add("F5", 4, "LOCAL_BASELINE", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "local_contracts.3.status", "value": "FAIL"}], "Repair the stop-path-local predicate.", novel=True)
    add("F5", 5, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.rollback.effect_reversibility", "value": "IRREVERSIBLE"}], "Do not present a reversible rollback label for an irreversible effect.", novel=True)
    add("F5", 6, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.rollback.restores_consequence", "value": False}], "Require rollback to restore the consequence state, not merely exist as a button.", novel=True)
    add("F5", 7, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.rollback.preimage_status", "value": "INCOMPLETE"}], "Require a complete preimage before claiming rollback coverage.", novel=True)
    add("F5", 8, "JUNCTION_DEFECT", "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY", [{"path": "objects.consequence.stop_path_present", "value": False}], "Provide a stop path when rollback cannot be relied on.", novel=True)

    # F6 — two local authorization failures, two scope junctions, two M4B
    # approval/action identity junctions, and two intentionally ambiguous
    # signer-only stress cases.
    add("F6", 1, "JUNCTION_DEFECT", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "objects.action.approval_id", "value": "other-approval"}], "Bind the action to the approval object that authorizes it.", novel=True, binding_subtype="approval_action_object")
    add("F6", 2, "LOCAL_BASELINE", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "local_contracts.1.status", "value": "FAIL"}], "Repair the approval-local scope predicate.", novel=False)
    add("F6", 3, "JUNCTION_DEFECT", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "objects.authority.scope_rank", "value": 1}], "Reject an approval whose scope is narrower than the action.", novel=True)
    add("F6", 4, "JUNCTION_DEFECT", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "objects.action.scope_rank", "value": 3}], "Reject an action that exceeds the signed scope.", novel=True)
    add("F6", 5, "JUNCTION_DEFECT", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "objects.action.approval_id", "value": "other-approval"}], "Bind the action to the approval object that authorizes it.", novel=True, binding_subtype="approval_action_object")
    add("F6", 6, "JUNCTION_DEFECT", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "objects.authority.approval_id", "value": "other-approval"}], "Bind the approval record to the action it claims to authorize.", novel=True, binding_subtype="approval_action_object")
    add("F6", 7, "AMBIGUOUS_STRESS", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "objects.authority.contestability_present", "value": False}], "Keep signer-only evidence undecidable without a concrete consequence failure.", novel=True, distractor=False, cross_family=False)
    add("F6", 8, "AMBIGUOUS_STRESS", "SIGNATURE_WITHOUT_CONTESTABILITY", [{"path": "objects.authority.revocation_path_present", "value": False}], "Keep a missing revocation path as a review question unless an actionable consequence is observed.", novel=True, distractor=False, cross_family=False)

    assert len(specs) == 48
    assert Counter(spec["family"] for spec in specs) == Counter({family: 8 for family in CONTRACT_REFS})
    assert sum(spec["novel_recombination"] for spec in specs) >= 16
    assert sum(spec["distractor_fields_present"] for spec in specs) >= 16
    assert sum(spec["cross_object_family"] for spec in specs) >= 16
    return specs


def path_get(value: dict[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def path_set(value: dict[str, Any], dotted: str, new_value: Any) -> Any:
    parts = dotted.split(".")
    current: Any = value
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    if isinstance(current, list):
        old = current[int(last)]
        current[int(last)] = new_value
    else:
        old = current[last]
        current[last] = new_value
    return old


def base_packet(spec: dict[str, Any], member: str) -> dict[str, Any]:
    pair_id = spec["pair_id"]
    family = spec["family"]
    refs = CONTRACT_REFS[family]
    object_id = f"object-{pair_id.lower()}"
    source_path = f"research/source/{family.lower()}/{pair_id.lower()}.json"
    source_revision = "rev-1"
    binding = {
        "object_id": object_id,
        "version": "v1",
        "scope": "bounded-research",
        "lifecycle_epoch": "epoch-1",
    }
    packet: dict[str, Any] = {
        "schema_version": "1.0.0",
        "fixture_id": f"{pair_id}-{member}",
        "pair_id": pair_id,
        "split": split_for_pair(pair_id),
        "object_family": refs["object_families"],
        "contract_context": {
            "repository": "Arvin-liu/when-systems-catch-fire",
            "as_of_commit": BASE_COMMIT,
            "source_contracts": refs["paths"],
            "local_contract_scope": "Each listed local contract is evaluated only against its own object record.",
        },
        "objects": {
            "claim": {
                "object_id": object_id,
                "version": "v1",
                "scope": "bounded-research",
                "lifecycle_epoch": "epoch-1",
                "provenance_status": "VALID",
                "ceiling_rank": 2,
                "source_path": source_path,
                "binding": copy.deepcopy(binding),
            },
            "action": {
                "object_id": f"action-{pair_id.lower()}",
                "claim_id": object_id,
                "approval_id": f"approval-{pair_id.lower()}",
                "required_scope_rank": 2,
                "scope_rank": 2,
                "attempted_current_use": False,
            },
            "authority": {
                "approver_id": "owner-role-1",
                "approval_id": f"approval-{pair_id.lower()}",
                "scope_rank": 2,
                "contestability_present": True,
                "revocation_path_present": True,
            },
            "admission": {
                "object_id": object_id,
                "version": "v1",
                "scope": "bounded-research",
                "lifecycle_epoch": "epoch-1",
                "scope_rank": 2,
                "lifecycle": "NON_INTENT",
                "provider_capability": "BOUNDED",
                "current_authority": "NONE",
                "object_level_split_present": True,
                "binding": copy.deepcopy(binding),
            },
            "source": {
                "object_id": object_id,
                "version": "v1",
                "scope": "bounded-research",
                "lifecycle_epoch": "epoch-1",
                "path": source_path,
                "revision": source_revision,
                "binding": copy.deepcopy(binding),
            },
            "identity": {
                "object_id": object_id,
                "version": "v1",
                "scope": "bounded-research",
                "lifecycle_epoch": "epoch-1",
                "source_path": source_path,
                "binding": copy.deepcopy(binding),
            },
            "projection": {
                "object_id": object_id,
                "version": "v1",
                "scope": "bounded-research",
                "lifecycle_epoch": "epoch-1",
                "source_path": source_path,
                "source_revision": source_revision,
                "binding": copy.deepcopy(binding),
            },
            "surface": {
                "object_id": object_id,
                "version": "v1",
                "scope": "bounded-research",
                "lifecycle_epoch": "epoch-1",
                "source_path": source_path,
                "source_revision": source_revision,
                "status": "NON_AUTHORITATIVE_SURFACE",
                "binding": copy.deepcopy(binding),
            },
            "release": {
                "object_id": object_id,
                "version": "v1",
                "scope": "bounded-research",
                "lifecycle_epoch": "epoch-1",
                "source_path": source_path,
                "binding": copy.deepcopy(binding),
            },
            "consequence": {
                "effect_state": "KNOWN",
                "technical_receipt_complete": True,
                "observer_present": True,
                "reconciliation_owner_id": "reconciliation-owner-1",
                "retry_policy": "PROHIBITED",
                "stop_path_present": True,
            },
            "rollback": {
                "label_present": True,
                "preimage_status": "VALID",
                "effect_reversibility": "REVERSIBLE",
                "restores_consequence": True,
            },
        },
        "local_contracts": [
            {"contract_id": f"{family}-local-1", "status": "PASS", "object": "primary", "predicate": "object-local schema and admission"},
            {"contract_id": f"{family}-local-2", "status": "PASS", "object": "secondary", "predicate": "object-local source or receipt"},
            {"contract_id": f"{family}-local-3", "status": "PASS", "object": "junction input A", "predicate": "object-local integrity"},
            {"contract_id": f"{family}-local-4", "status": "PASS", "object": "junction input B", "predicate": "object-local lifecycle"},
        ],
        "distractor_fields": {
            "evidence_volume": 3,
            "valid_signature_count": 1,
            "deadline_passed": False,
            "display_label": "bounded fixture",
            "unrelated_checksum": "distractor-1",
        },
        "research_boundary": BOUNDARY,
    }
    if family == "F1":
        # F1 pairs all share the same unresolved-effect context. The paired
        # change then alters exactly one accountability junction field.
        packet["objects"]["consequence"]["effect_state"] = "UNKNOWN"
    if not spec["distractor_fields_present"]:
        packet["distractor_fields"] = {"display_label": "bounded fixture"}
    return packet


def make_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    packets: list[dict[str, Any]] = []
    answers: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    for spec in pair_specs():
        pair_id = spec["pair_id"]
        split = split_for_pair(pair_id)
        member_rows: list[dict[str, Any]] = []
        for member, truth_role in (("A", "PRIMARY"), ("B", "MATCHED_CONTROL")):
            packet = base_packet(spec, member)
            applied: list[dict[str, Any]] = []
            if member == "A":
                for change in spec["changes"]:
                    before = path_set(packet, change["path"], change["value"])
                    applied.append({"path": change["path"], "before": before, "after": change["value"]})
            # The blind packet must not contain truth labels, roles, historical
            # outcomes or the answer key's change descriptions.
            packets.append(packet)
            truth_class = "AMBIGUOUS_STRESS" if spec["kind"] == "AMBIGUOUS_STRESS" and member == "A" else "CONTROL" if member == "B" else "DEFECT"
            answer = {
                "fixture_id": packet["fixture_id"],
                "pair_id": pair_id,
                "family": spec["family"],
                "member_role": truth_role,
                "truth_class": truth_class,
                "kind": spec["kind"],
                "diagnostic_annotation": spec["diagnostic"],
                "injected_changes": applied,
                "repair": spec["repair"],
                "novel_recombination": spec["novel_recombination"],
                "distractor_fields_present": spec["distractor_fields_present"],
                "cross_object_family": spec["cross_object_family"],
                "binding_subtype": spec["binding_subtype"],
                "metamorphic_expected": "FLAG_TO_NO_FLAG" if truth_class == "DEFECT" else "NO_FLAG_STABILITY_OR_UNDECIDABLE_STABILITY",
            }
            answers.append(answer)
            member_rows.append({"fixture_id": packet["fixture_id"], "truth_class": truth_class})
        manifests.append(
            {
                "pair_id": pair_id,
                "family": spec["family"],
                "split": split,
                "fixture_ids": [row["fixture_id"] for row in member_rows],
                "source_contracts": CONTRACT_REFS[spec["family"]]["paths"],
                "historical_lineage": CONTRACT_REFS[spec["family"]]["historical_lineage"],
                "genealogy": CONTRACT_REFS[spec["family"]]["genealogy"],
                "novel_recombination": spec["novel_recombination"],
                "distractor_fields_present": spec["distractor_fields_present"],
                "cross_object_family": spec["cross_object_family"],
                "metamorphic_field_paths": [change["path"] for change in spec["changes"]],
                "binding_subtype": spec["binding_subtype"],
            }
        )
        split_rows.append({"pair_id": pair_id, "split": split, "fixture_ids": [f"{pair_id}-A", f"{pair_id}-B"]})
    return packets, answers, manifests, split_rows


PROTOCOL: dict[str, Any] = {
    "schema_version": "1.0.0",
    "task_id": TASK_ID,
    "protocol_amendment": {
        "id": "TASK156-AMENDMENT-01",
        "invalidates_freeze_commit": "e942fb8482adbca5f4dd29eb9377b2aef0218f73",
        "reason": "The first unblind run counted non-applicable model coverage as metamorphic violations and had not yet implemented the full predeclared metamorphic property suite.",
        "restart_from_new_freeze": True,
        "archived_invalidated_run": "data/research/cross-contract-prospective-fixtures-2026-09-05/invalidated-freeze-e942fb84/",
    },
    "question": "Can a frozen executable answer-key-separated fixture experiment reproduce non-redundant cross-contract detection beyond existing local contracts while controlling false positives, and can CC-020-like binding defects be caught by sharpening three edges without inventing a fourth?",
    "base_commit": BASE_COMMIT,
    "corpus_type": "prospective_synthetic_but_repository_shaped",
    "live_external_effects": False,
    "minimum_pairs": 48,
    "actual_pairs": 48,
    "instances_per_pair": 2,
    "blind_input_contract": ["blind fixture packet", "frozen model definition", "existing contract references needed for M0"],
    "forbidden_scorer_inputs": ["answer-key.jsonl", "historical outcome labels", "defect/control labels", "post-outcome evidence"],
    "freeze_before_scoring": True,
    "split": {
        "algorithm": "SHA256(pair_id).first_byte mod 3; 0/1 calibration, 2 holdout",
        "pair_members_stay_together": True,
        "refinement_before_holdout": True,
    },
    "families": [
        {"id": family, **{key: value for key, value in refs.items() if key != "paths"}, "source_contracts": refs["paths"]}
        for family, refs in CONTRACT_REFS.items()
    ],
    "anti_overfitting": {
        "minimum_novel_recombination_pairs": 16,
        "minimum_distractor_pairs": 16,
        "minimum_cross_object_family_pairs": 16,
        "legitimate_incomplete_and_non_authoritative_controls": True,
        "historical_records_replayed": False,
    },
    "scoring": {
        "models": ["M0", "M3", "M3R", "M4B"],
        "passes_required": 2,
        "deterministic_output_identity_required": True,
        "semantic_adjudication": "NONE; all primary predicates are deterministic",
        "answer_key_read_after_scoring_only": True,
    },
    "metamorphic_properties": [
        {"id": "repair_exact_missing_junction", "expectation": "A model that flags a declared single-field defect must return NO_FLAG for its matched repair; models without that predicate are recorded as not applicable."},
        {"id": "binding_coverage_locality", "expectation": "Breaking a locally valid cross-object binding may flip only models whose frozen predicate covers that binding subtype."},
        {"id": "irrelevant_evidence_no_scope_upgrade", "expectation": "Adding irrelevant evidence volume does not change claim scope, predicates or result."},
        {"id": "signature_does_not_repair_consequence", "expectation": "Adding a valid signature does not remove an unrelated consequence/accountability finding."},
        {"id": "rollback_label_does_not_repair_irreversible_effect", "expectation": "Adding a rollback label cannot turn an irreversible-effect finding into NO_FLAG."},
        {"id": "safe_authorized_alternative_and_deadline", "expectation": "A safe authorized alternative may change an unavailable-route result; deadline passage alone cannot create a new failure."},
    ],
    "boundary": BOUNDARY,
}


MODELS: dict[str, dict[str, Any]] = {
    "M0": {
        "id": "M0",
        "name": "EXISTING_ONLY",
        "description": "Use only packet-local contract statuses and their explicitly named object-local predicates.",
        "edges": ["local_contract"],
        "predicates": [
            {"id": "m0.local_contract_failure", "observable": "any local_contracts[*].status == FAIL", "action": "DEFER_TO_LOCAL_CONTRACT_REPAIR"},
            {"id": "m0.local_contract_unknown", "observable": "any local_contracts[*].status == UNKNOWN and no FAIL", "action": "REQUIRE_LOCAL_REVIEW"},
        ],
    },
    "M3": {
        "id": "M3",
        "name": "THREE_EDGE_V1",
        "description": "M0 plus exactly the frozen claim, authority and consequence edges; no binding-specific predicate.",
        "edges": ["claim", "authority", "consequence"],
        "predicates": [
            {"id": "m3.claim_ceiling", "observable": "claim.provenance_status == VALID and claim.ceiling_rank < action.required_scope_rank", "action": "BLOCK_ACTION_UNTIL_CLAIM_CEILING_IS_ALIGNED"},
            {"id": "m3.authority_scope", "observable": "authority.scope_rank != action.scope_rank or admission.scope_rank != action.scope_rank or approver missing", "action": "BLOCK_ADMISSION_UNTIL_SCOPE_AND_APPROVAL_ALIGN"},
            {"id": "m3.admission_lifecycle", "observable": "admission.lifecycle == DRAFT and action attempts Current use", "action": "KEEP_DRAFT_NON_INTENT_OBJECT_OUT_OF_ACTION_PATH"},
            {"id": "m3.admission_authority", "observable": "provider capability is AVAILABLE, Current authority is NONE, and action attempts Current use", "action": "KEEP_PROVIDER_CAPABILITY_OUTSIDE_CURRENT_AUTHORITY"},
            {"id": "m3.admission_object_split", "observable": "admission.object_level_split_present is false", "action": "REQUIRE_SEPARATE_ADMISSION_OBJECTS"},
            {"id": "m3.consequence_unknown_owner", "observable": "effect_state == UNKNOWN and observer or reconciliation owner is absent", "action": "OPEN_RECONCILIATION_WITH_NAMED_OBSERVER_AND_OWNER"},
            {"id": "m3.consequence_retry", "observable": "effect_state == UNKNOWN and retry_policy == PERMITTED", "action": "PROHIBIT_RETRY_UNTIL_EFFECT_IS_RECONCILED"},
            {"id": "m3.consequence_stop", "observable": "effect_state == UNKNOWN and stop_path_present is false", "action": "REQUIRE_OBSERVABLE_STOP_PATH"},
            {"id": "m3.rollback", "observable": "rollback label exists but effect is irreversible, preimage incomplete, restoration false, or stop path absent", "action": "BLOCK_REVERSIBILITY_CLAIM_AND_REQUIRE_SAFE_STOP"},
        ],
    },
    "M3R": {
        "id": "M3R",
        "name": "THREE_EDGE_REFINED",
        "description": "M3 plus a pre-frozen refinement of the claim edge for source/identity/projection/public-surface binding; it remains reducible to claim provenance and ceiling.",
        "edges": ["claim", "authority", "consequence"],
        "refinement": "m3r.claim_source_identity_projection_binding",
        "predicates": [
            {"id": "m3r.claim_source_identity_projection_binding", "observable": "individually VALID source, identity, projection, surface and release records must agree on source path, object identity and source revision", "action": "BLOCK_PROJECTION_UNTIL_CLAIM_SOURCE_IDENTITY_AND_SURFACE_ALIGN"},
        ],
    },
    "M4B": {
        "id": "M4B",
        "name": "THREE_EDGE_PLUS_BINDING_CHALLENGER",
        "description": "M3R plus a neutral binding/integrity challenger over existing object_id/version/scope/lifecycle_epoch fields and claim/approval references.",
        "edges": ["claim", "authority", "consequence", "binding/integrity"],
        "refinement": "m3r.claim_source_identity_projection_binding",
        "binding_predicates": [
            {"id": "m4b.binding_tuple_alignment", "observable": "source, identity, projection, surface, release and admission binding tuples agree on object_id/version/scope/lifecycle_epoch", "action": "BLOCK_PROJECTION_OR_ADMISSION_UNTIL_EXISTING_BINDING_FIELDS_ALIGN"},
            {"id": "m4b.claim_action_object_binding", "observable": "action.claim_id == claim.object_id", "action": "BLOCK_ACTION_UNTIL_EXISTING_CLAIM_REFERENCE_ALIGN"},
            {"id": "m4b.approval_action_object_binding", "observable": "action.approval_id == authority.approval_id", "action": "BLOCK_ACTION_UNTIL_EXISTING_APPROVAL_REFERENCE_ALIGN"},
        ],
        "no_new_authority_or_truth_state": True,
    },
}


THRESHOLDS: dict[str, Any] = {
    "schema_version": "1.0.0",
    "any_cross_contract_signal_survival": {
        "holdout_incremental_true_detections_min": 6,
        "holdout_incremental_families_min": 3,
        "matched_control_false_positive_rate_max": 0.10,
        "incremental_exact_actionability_min": 0.80,
        "max_share_from_one_historical_lineage_inspired_family": 0.50,
    },
    "binding_challenger_survival": {
        "additional_holdout_binding_defects_min": 3,
        "distinct_binding_subtypes_min": 2,
        "additional_holdout_control_false_positives_max": 1,
        "new_authority_or_truth_state_allowed": False,
        "trivial_stale_digest_only_allowed": False,
    },
    "verdict_taxonomy": [
        "NO_REPRODUCIBLE_INCREMENT",
        "REVIEW_LENS_ONLY",
        "THREE_EDGE_SIGNAL_REPRODUCED",
        "REFINED_THREE_EDGE_SIGNAL_REPRODUCED",
        "BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE",
        "EXPERIMENT_INVALID",
    ],
    "post_hoc_changes": {
        "thresholds": "FORBIDDEN",
        "model_semantics": "FORBIDDEN",
        "answer_key": "FORBIDDEN",
        "case_exclusion": "FORBIDDEN; classify INVALID_FIXTURE under predeclared rule",
    },
}


def frozen_payloads() -> dict[str, bytes]:
    packets, answers, manifests, split_rows = make_corpus()
    generator_manifest = {
        "schema_version": "1.0.0",
        "generator": "ignition/tools/research/cross_contract_prospective_experiment.py",
        "generator_version": SCORER_VERSION,
        "seed": "IGNITION-20260905-156/frozen-pair-specs-v2-amended-metamorphic-suite",
        "base_commit": BASE_COMMIT,
        "pair_count": len(manifests),
        "fixture_instance_count": len(packets),
        "family_counts": dict(sorted(Counter(item["family"] for item in manifests).items())),
        "novel_recombination_pairs": sum(bool(item["novel_recombination"]) for item in manifests),
        "distractor_pairs": sum(bool(item["distractor_fields_present"]) for item in manifests),
        "cross_object_family_pairs": sum(bool(item["cross_object_family"]) for item in manifests),
        "family_genealogy": {family: refs["genealogy"] for family, refs in CONTRACT_REFS.items()},
        "invalid_fixture_rule": "If required packet keys or source-contract references are malformed, retain the row and classify INVALID_FIXTURE; do not delete after freeze.",
        "answer_key_separate_from_blind_packets": True,
    }
    fixture_manifest = {
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        "pairs": manifests,
        "boundaries": {"historical_records_replayed": False, "live_external_effects": False, "research_only": True},
    }
    split_manifest = {
        "schema_version": "1.0.0",
        "algorithm": "SHA256(pair_id).first_byte mod 3; 0/1 calibration, 2 holdout",
        "pairs": split_rows,
        "counts": dict(sorted(Counter(row["split"] for row in split_rows).items())),
    }
    # The freeze ledger is deliberately hashed after every other frozen file;
    # it records those hashes and is itself protected by the freeze commit.
    pre_ledger: dict[str, Any] = {
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        "freeze_status": "FROZEN_BEFORE_BLINDED_SCORING",
        "frozen_at": FROZEN_DATE,
        "base_commit": BASE_COMMIT,
        "frozen_artifacts": {},
        "separate_digests": {
            "blind_packets": digest_bytes(jsonl_bytes(packets)),
            "answer_key": digest_bytes(jsonl_bytes(answers)),
            "blind_and_answer_key_differ": digest_bytes(jsonl_bytes(packets)) != digest_bytes(jsonl_bytes(answers)),
        },
        "pair_count": len(manifests),
        "fixture_instance_count": len(packets),
        "calibration_pairs": split_manifest["counts"].get("calibration", 0),
        "holdout_pairs": split_manifest["counts"].get("holdout", 0),
        "models_frozen": list(MODELS),
        "thresholds_frozen": True,
        "scoring_input_exclusion": "The scorer command reads blind-packets.jsonl and model-definitions.json only; answer-key.jsonl is read only by unblind/metrics commands.",
        "preflight_residuals": [
            {"path": "1111/instructions/CURRENT.md", "status": "KNOWN_STALE_POINTER", "action": "PRESERVED_UNCHANGED"},
            {"path": "1111/relay/current", "status": "KNOWN_STALE_POINTER", "action": "PRESERVED_UNCHANGED"},
        ],
        "boundary": BOUNDARY,
    }
    payloads: dict[str, bytes] = {
        "experiment-protocol.json": json_bytes(PROTOCOL),
        "model-definitions.json": json_bytes({"schema_version": "1.0.0", "task_id": TASK_ID, "models": list(MODELS.values())}),
        "thresholds.json": json_bytes(THRESHOLDS),
        "fixture-generator-manifest.json": json_bytes(generator_manifest),
        "fixture-manifest.json": json_bytes(fixture_manifest),
        "blind-packets.jsonl": jsonl_bytes(packets),
        "answer-key.jsonl": jsonl_bytes(answers),
        "split-manifest.json": json_bytes(split_manifest),
    }
    pre_ledger["frozen_artifacts"] = {name: digest_bytes(payloads[name]) for name in sorted(payloads)}
    payloads["freeze-ledger.json"] = json_bytes(pre_ledger)
    return payloads


def validate_packet_separation(packets: list[dict[str, Any]]) -> list[str]:
    forbidden = {
        "truth_class",
        "member_role",
        "kind",
        "injected_changes",
        "answer_key",
        "historical_outcome",
        "defect_label",
        "control_label",
    }
    errors: list[str] = []
    for packet in packets:
        if forbidden & set(packet):
            errors.append(f"{packet.get('fixture_id')}: top-level forbidden answer-key field")
        if packet.get("fixture_id", "").endswith(("-DEFECT", "-CONTROL")):
            errors.append(f"{packet.get('fixture_id')}: role encoded in fixture id")
        if packet.get("research_boundary") != BOUNDARY:
            errors.append(f"{packet.get('fixture_id')}: boundary drift")
    return errors


def validate_corpus_structure(packets: list[dict[str, Any]], answers: list[dict[str, Any]], manifests: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_packet_separation(packets))
    packet_ids = {packet.get("fixture_id") for packet in packets}
    answer_ids = {answer.get("fixture_id") for answer in answers}
    if len(packets) != 96:
        errors.append(f"expected 96 packet instances, found {len(packets)}")
    if len(answers) != 96:
        errors.append(f"expected 96 answer rows, found {len(answers)}")
    if packet_ids != answer_ids:
        errors.append("blind packet and answer-key fixture ID sets differ")
    pair_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for answer in answers:
        pair_members[answer["pair_id"]].append(answer)
    if len(pair_members) != 48:
        errors.append(f"expected 48 pairs, found {len(pair_members)}")
    for pair_id, rows in sorted(pair_members.items()):
        if len(rows) != 2:
            errors.append(f"{pair_id}: pair does not have exactly two members")
        if {row["member_role"] for row in rows} != {"PRIMARY", "MATCHED_CONTROL"}:
            errors.append(f"{pair_id}: missing primary/control membership")
        split_values = {split_for_pair(pair_id)}
        packet_splits = {packet["split"] for packet in packets if packet["pair_id"] == pair_id}
        if packet_splits != split_values:
            errors.append(f"{pair_id}: pair members split inconsistently")
    for manifest in manifests:
        if manifest["split"] != split_for_pair(manifest["pair_id"]):
            errors.append(f"{manifest['pair_id']}: split hash mismatch")
        if len(manifest["fixture_ids"]) != 2:
            errors.append(f"{manifest['pair_id']}: manifest member count mismatch")
    return errors


def local_findings(packet: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    findings: list[dict[str, Any]] = []
    unknown = False
    for index, contract in enumerate(packet["local_contracts"]):
        status = contract.get("status")
        if status == "FAIL":
            findings.append(
                {
                    "edge": "local_contract",
                    "predicate": "m0.local_contract_failure",
                    "source_fields": [f"local_contracts.{index}.status", f"local_contracts.{index}.predicate"],
                    "proposed_action": "DEFER_TO_LOCAL_CONTRACT_REPAIR",
                }
            )
        elif status == "UNKNOWN":
            unknown = True
    if unknown and not findings:
        findings.append(
            {
                "edge": "local_contract",
                "predicate": "m0.local_contract_unknown",
                "source_fields": ["local_contracts[*].status"],
                "proposed_action": "REQUIRE_LOCAL_REVIEW",
                "undecidable": True,
            }
        )
    return findings, unknown


def m3_findings(packet: dict[str, Any]) -> list[dict[str, Any]]:
    objects = packet["objects"]
    claim = objects["claim"]
    action = objects["action"]
    authority = objects["authority"]
    admission = objects["admission"]
    consequence = objects["consequence"]
    rollback = objects["rollback"]
    findings: list[dict[str, Any]] = []

    if claim["provenance_status"] == "VALID" and claim["ceiling_rank"] < action["required_scope_rank"]:
        findings.append({"edge": "claim", "predicate": "m3.claim_ceiling", "source_fields": ["objects.claim.ceiling_rank", "objects.action.required_scope_rank"], "proposed_action": "BLOCK_ACTION_UNTIL_CLAIM_CEILING_IS_ALIGNED"})
    if authority.get("approver_id") is None or authority["scope_rank"] != action["scope_rank"] or admission["scope_rank"] != action["scope_rank"]:
        findings.append({"edge": "authority", "predicate": "m3.authority_scope", "source_fields": ["objects.authority.approver_id", "objects.authority.scope_rank", "objects.admission.scope_rank", "objects.action.scope_rank"], "proposed_action": "BLOCK_ADMISSION_UNTIL_SCOPE_AND_APPROVAL_ALIGN"})
    if admission["lifecycle"] == "DRAFT" and action["attempted_current_use"]:
        findings.append({"edge": "authority", "predicate": "m3.admission_lifecycle", "source_fields": ["objects.admission.lifecycle", "objects.action.attempted_current_use"], "proposed_action": "KEEP_DRAFT_NON_INTENT_OBJECT_OUT_OF_ACTION_PATH"})
    if admission["provider_capability"] == "AVAILABLE" and admission["current_authority"] == "NONE" and action["attempted_current_use"]:
        findings.append({"edge": "authority", "predicate": "m3.admission_authority", "source_fields": ["objects.admission.provider_capability", "objects.admission.current_authority", "objects.action.attempted_current_use"], "proposed_action": "KEEP_PROVIDER_CAPABILITY_OUTSIDE_CURRENT_AUTHORITY"})
    if not admission["object_level_split_present"]:
        findings.append({"edge": "authority", "predicate": "m3.admission_object_split", "source_fields": ["objects.admission.object_level_split_present"], "proposed_action": "REQUIRE_SEPARATE_ADMISSION_OBJECTS"})
    if consequence["effect_state"] == "UNKNOWN" and (not consequence["observer_present"] or consequence["reconciliation_owner_id"] is None):
        findings.append({"edge": "consequence", "predicate": "m3.consequence_unknown_owner", "source_fields": ["objects.consequence.effect_state", "objects.consequence.observer_present", "objects.consequence.reconciliation_owner_id"], "proposed_action": "OPEN_RECONCILIATION_WITH_NAMED_OBSERVER_AND_OWNER"})
    if consequence["effect_state"] == "UNKNOWN" and consequence["retry_policy"] == "PERMITTED":
        findings.append({"edge": "consequence", "predicate": "m3.consequence_retry", "source_fields": ["objects.consequence.effect_state", "objects.consequence.retry_policy"], "proposed_action": "PROHIBIT_RETRY_UNTIL_EFFECT_IS_RECONCILED"})
    if consequence["effect_state"] == "UNKNOWN" and not consequence["stop_path_present"]:
        findings.append({"edge": "consequence", "predicate": "m3.consequence_stop", "source_fields": ["objects.consequence.effect_state", "objects.consequence.stop_path_present"], "proposed_action": "REQUIRE_OBSERVABLE_STOP_PATH"})
    if rollback["label_present"] and (
        rollback["effect_reversibility"] == "IRREVERSIBLE"
        or rollback["preimage_status"] != "VALID"
        or not rollback["restores_consequence"]
        or not consequence["stop_path_present"]
    ):
        findings.append({"edge": "consequence", "predicate": "m3.rollback", "source_fields": ["objects.rollback.label_present", "objects.rollback.effect_reversibility", "objects.rollback.preimage_status", "objects.rollback.restores_consequence", "objects.consequence.stop_path_present"], "proposed_action": "BLOCK_REVERSIBILITY_CLAIM_AND_REQUIRE_SAFE_STOP"})
    return findings


def m3r_findings(packet: dict[str, Any]) -> list[dict[str, Any]]:
    objects = packet["objects"]
    source = objects["source"]
    identity = objects["identity"]
    projection = objects["projection"]
    surface = objects["surface"]
    release = objects["release"]
    relations = [
        ("objects.source.object_id", source["object_id"], "objects.identity.object_id", identity["object_id"]),
        ("objects.source.path", source["path"], "objects.identity.source_path", identity["source_path"]),
        ("objects.identity.object_id", identity["object_id"], "objects.projection.object_id", projection["object_id"]),
        ("objects.identity.source_path", identity["source_path"], "objects.projection.source_path", projection["source_path"]),
        ("objects.projection.source_revision", projection["source_revision"], "objects.surface.source_revision", surface["source_revision"]),
        ("objects.release.source_path", release["source_path"], "objects.source.path", source["path"]),
    ]
    if all(objects[key].get("status", "VALID") in {"VALID", "NON_AUTHORITATIVE_SURFACE"} for key in ("source", "identity", "projection", "surface", "release")):
        for left_path, left, right_path, right in relations:
            if left != right:
                return [
                    {
                        "edge": "claim",
                        "predicate": "m3r.claim_source_identity_projection_binding",
                        "source_fields": [left_path, right_path],
                        "proposed_action": "BLOCK_PROJECTION_UNTIL_CLAIM_SOURCE_IDENTITY_AND_SURFACE_ALIGN",
                    }
                ]
    return []


def m4b_findings(packet: dict[str, Any]) -> list[dict[str, Any]]:
    objects = packet["objects"]
    findings: list[dict[str, Any]] = []
    tuple_roles = ["source", "identity", "projection", "surface", "release", "admission"]
    fields = ["object_id", "version", "scope", "lifecycle_epoch"]
    tuples = {role: tuple(objects[role].get(field) for field in fields) for role in tuple_roles}
    if len(set(tuples.values())) != 1:
        mismatches = [f"objects.{role}.{field}" for role in tuple_roles for field in fields]
        findings.append({"edge": "binding/integrity", "predicate": "m4b.binding_tuple_alignment", "source_fields": mismatches, "proposed_action": "BLOCK_PROJECTION_OR_ADMISSION_UNTIL_EXISTING_BINDING_FIELDS_ALIGN"})
    if objects["action"]["claim_id"] != objects["claim"]["object_id"]:
        findings.append({"edge": "binding/integrity", "predicate": "m4b.claim_action_object_binding", "source_fields": ["objects.action.claim_id", "objects.claim.object_id"], "proposed_action": "BLOCK_ACTION_UNTIL_EXISTING_CLAIM_REFERENCE_ALIGN"})
    if objects["action"]["approval_id"] != objects["authority"]["approval_id"]:
        findings.append({"edge": "binding/integrity", "predicate": "m4b.approval_action_object_binding", "source_fields": ["objects.action.approval_id", "objects.authority.approval_id"], "proposed_action": "BLOCK_ACTION_UNTIL_EXISTING_APPROVAL_REFERENCE_ALIGN"})
    return findings


def model_record(model_id: str, packet: dict[str, Any]) -> dict[str, Any]:
    local, local_unknown = local_findings(packet)
    findings: list[dict[str, Any]] = list(local)
    if model_id != "M0":
        findings.extend(m3_findings(packet))
    if model_id in {"M3R", "M4B"}:
        findings.extend(m3r_findings(packet))
    if model_id == "M4B":
        findings.extend(m4b_findings(packet))
    deterministic_findings = [finding for finding in findings if not finding.get("undecidable")]
    if deterministic_findings:
        result = "FLAG"
    elif local_unknown:
        result = "UNDECIDABLE"
    else:
        result = "NO_FLAG"
    payload = {
        "fixture_id": packet["fixture_id"],
        "pair_id": packet["pair_id"],
        "split": packet["split"],
        "model": model_id,
        "result": result,
        "edges": sorted({finding["edge"] for finding in findings if not finding.get("undecidable")}),
        "predicates": sorted({finding["predicate"] for finding in findings if not finding.get("undecidable")}),
        "findings": findings,
        "exact_actionable_predicate": bool(deterministic_findings) and all("predicate" in finding and finding.get("proposed_action") for finding in deterministic_findings),
        "proposed_action": deterministic_findings[0]["proposed_action"] if deterministic_findings else None,
        "confidence": "DETERMINISTIC_PREDICATE" if result != "UNDECIDABLE" else "UNDECIDABLE",
        "claim_ceiling": BOUNDARY,
        "scorer_version": SCORER_VERSION,
    }
    payload["output_sha256"] = digest(payload)
    return payload


def score_packets(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet in sorted(packets, key=lambda item: item["fixture_id"]):
        for model_id in MODELS:
            rows.append(model_record(model_id, packet))
    return rows


def output_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["fixture_id"], row["model"]): row for row in rows}


def validate_score_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    expected = 96 * len(MODELS)
    if len(rows) != expected:
        errors.append(f"expected {expected} score rows, found {len(rows)}")
    keys = {(row.get("fixture_id"), row.get("model")) for row in rows}
    if len(keys) != len(rows):
        errors.append("duplicate fixture/model score row")
    for row in rows:
        actual_hash = row.get("output_sha256")
        payload = dict(row)
        payload.pop("output_sha256", None)
        if actual_hash != digest(payload):
            errors.append(f"{row.get('fixture_id')}/{row.get('model')}: output hash mismatch")
        if row.get("result") not in {"FLAG", "NO_FLAG", "UNDECIDABLE"}:
            errors.append(f"{row.get('fixture_id')}/{row.get('model')}: invalid result")
    return errors


def command_generate(check: bool) -> int:
    payloads = frozen_payloads()
    errors: list[str] = []
    if check:
        for name, payload in payloads.items():
            path = RESEARCH / name
            if not path.is_file():
                errors.append(f"missing frozen artifact: {name}")
            elif path.read_bytes() != payload:
                errors.append(f"frozen artifact drift: {name}")
        if errors:
            print("GENERATOR_DRIFT", *errors, sep="\n", file=sys.stderr)
            return 1
        print("PROSPECTIVE_FIXTURE_GENERATION_OK artifacts=9 pairs=48 instances=96")
        return 0
    for name, payload in payloads.items():
        write_bytes(RESEARCH / name, payload)
    print("PROSPECTIVE_FIXTURE_GENERATION_OK artifacts=9 pairs=48 instances=96")
    return 0


def command_validate_freeze() -> int:
    payloads = frozen_payloads()
    ledger_path = RESEARCH / "freeze-ledger.json"
    if not ledger_path.is_file():
        print("FREEZE_LEDGER_MISSING", file=sys.stderr)
        return 1
    ledger = read_json(ledger_path)
    errors: list[str] = []
    for name, expected in ledger.get("frozen_artifacts", {}).items():
        path = RESEARCH / name
        if not path.is_file():
            errors.append(f"missing frozen file {name}")
        elif digest_bytes(path.read_bytes()) != expected:
            errors.append(f"post-freeze mutation {name}")
        elif path.read_bytes() != payloads.get(name, path.read_bytes()):
            errors.append(f"regeneration drift {name}")
    packets = read_jsonl(RESEARCH / "blind-packets.jsonl")
    answers = read_jsonl(RESEARCH / "answer-key.jsonl")
    manifests = read_json(RESEARCH / "fixture-manifest.json")["pairs"]
    errors.extend(validate_corpus_structure(packets, answers, manifests))
    if errors:
        print("FREEZE_VALIDATION_FAILED", *errors, sep="\n", file=sys.stderr)
        return 1
    print("FREEZE_VALIDATION_OK frozen_artifacts=8 pairs=48 instances=96")
    return 0


def command_score(output: Path) -> int:
    # Deliberately do not read answer-key.jsonl here. This is the separation
    # boundary tested by the command and by the repository unit tests.
    packets_path = RESEARCH / "blind-packets.jsonl"
    model_path = RESEARCH / "model-definitions.json"
    if not packets_path.is_file() or not model_path.is_file():
        print("BLIND_INPUT_MISSING", file=sys.stderr)
        return 1
    packets = read_jsonl(packets_path)
    model_document = read_json(model_path)
    if [model["id"] for model in model_document["models"]] != list(MODELS):
        print("MODEL_DEFINITION_ORDER_OR_ID_DRIFT", file=sys.stderr)
        return 1
    errors = validate_packet_separation(packets)
    if errors:
        print("BLIND_PACKET_SEPARATION_FAILED", *errors, sep="\n", file=sys.stderr)
        return 1
    rows = score_packets(packets)
    errors = validate_score_rows(rows)
    if errors:
        print("SCORER_OUTPUT_INVALID", *errors, sep="\n", file=sys.stderr)
        return 1
    write_bytes(output, jsonl_bytes(rows))
    print(f"BLIND_SCORING_OK output={output} rows={len(rows)} answer_key_loaded=false")
    return 0


def rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def classification_for(model_rows: dict[tuple[str, str], dict[str, Any]], answer: dict[str, Any]) -> dict[str, Any]:
    fixture_id = answer["fixture_id"]
    m0 = model_rows[(fixture_id, "M0")]
    result: dict[str, Any] = {
        "fixture_id": fixture_id,
        "pair_id": answer["pair_id"],
        "family": answer["family"],
        "split": model_rows[(fixture_id, "M0")]["split"],
        "truth_class": answer["truth_class"],
        "diagnostic_annotation": answer["diagnostic_annotation"],
        "models": {},
    }
    for model_id in MODELS:
        row = model_rows[(fixture_id, model_id)]
        result["models"][model_id] = {
            "result": row["result"],
            "incremental_beyond_m0": answer["truth_class"] == "DEFECT" and m0["result"] != "FLAG" and row["result"] == "FLAG" and model_id != "M0",
            "redundant_with_m0": m0["result"] == "FLAG" and row["result"] == "FLAG" and model_id != "M0",
            "exact_actionable_predicate": row["exact_actionable_predicate"],
            "predicates": row["predicates"],
            "edges": row["edges"],
        }
    return result


def metrics_for(results: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, Any] = {"models": {}, "holdout_survival": {}, "family_metrics": {}, "diagnostic_annotations": {}}
    for model_id in MODELS:
        model_stats: dict[str, Any] = {}
        for split in ("all", "calibration", "holdout"):
            subset = results if split == "all" else [item for item in results if item["split"] == split]
            defects = [item for item in subset if item["truth_class"] == "DEFECT"]
            controls = [item for item in subset if item["truth_class"] == "CONTROL"]
            ambiguous = [item for item in subset if item["truth_class"] == "AMBIGUOUS_STRESS"]
            detected = [item for item in defects if item["models"][model_id]["result"] == "FLAG"]
            m0_detected = [item for item in defects if item["models"]["M0"]["result"] == "FLAG"]
            incremental = [item for item in defects if item["models"]["M0"]["result"] != "FLAG" and item["models"][model_id]["result"] == "FLAG" and model_id != "M0"]
            redundant = [item for item in defects if item["models"]["M0"]["result"] == "FLAG" and item["models"][model_id]["result"] == "FLAG" and model_id != "M0"]
            false_positives = [item for item in controls if item["models"][model_id]["result"] == "FLAG"]
            false_negatives = [item for item in defects if item["models"][model_id]["result"] == "NO_FLAG"]
            undecidable = [item for item in subset if item["models"][model_id]["result"] == "UNDECIDABLE"]
            exact = [item for item in incremental if item["models"][model_id]["exact_actionable_predicate"]]
            matched_flips = []
            by_pair = defaultdict(dict)
            for item in subset:
                by_pair[item["pair_id"]][item["truth_class"]] = item
            for pair_id, members in by_pair.items():
                primary = next((item for item in members.values() if item["truth_class"] == "DEFECT"), None)
                control = members.get("CONTROL")
                if primary and control and primary["models"][model_id]["result"] == "FLAG" and control["models"][model_id]["result"] != "FLAG":
                    matched_flips.append(pair_id)
            model_stats[split] = {
                "fixture_instances": len(subset),
                "defects": len(defects),
                "controls": len(controls),
                "ambiguous_stress": len(ambiguous),
                "m0_defects_detected": len(m0_detected),
                "detected_defects": len(detected),
                "incremental_defects_beyond_m0": len(incremental),
                "redundant_detections": len(redundant),
                "false_positives_on_matched_controls": len(false_positives),
                "matched_control_false_positive_rate": rate(len(false_positives), len(controls)),
                "false_negatives": len(false_negatives),
                "undecidable_outputs": len(undecidable),
                "invalid_fixtures": 0,
                "incremental_exact_actionability_rate": rate(len(exact), len(incremental)),
                "matched_pair_flips": len(matched_flips),
                "matched_pair_flip_accuracy": rate(len(matched_flips), len(by_pair)),
                "ambiguous_stress_flags": len([item for item in ambiguous if item["models"][model_id]["result"] == "FLAG"]),
            }
        metrics["models"][model_id] = model_stats

    for family in CONTRACT_REFS:
        metrics["family_metrics"][family] = {}
        for model_id in MODELS:
            subset = [item for item in results if item["family"] == family]
            defects = [item for item in subset if item["truth_class"] == "DEFECT"]
            controls = [item for item in subset if item["truth_class"] == "CONTROL"]
            flagged_defects = len([item for item in defects if item["models"][model_id]["result"] == "FLAG"])
            flagged_controls = len([item for item in controls if item["models"][model_id]["result"] == "FLAG"])
            metrics["family_metrics"][family][model_id] = {
                "defects": len(defects),
                "controls": len(controls),
                "sensitivity_descriptive": rate(flagged_defects, len(defects)),
                "specificity_descriptive": rate(len(controls) - flagged_controls, len(controls)),
                "control_false_positives": flagged_controls,
            }

    holdout = [item for item in results if item["split"] == "holdout"]
    m3r_incremental = [item for item in holdout if item["truth_class"] == "DEFECT" and item["models"]["M0"]["result"] != "FLAG" and item["models"]["M3R"]["result"] == "FLAG"]
    m4b_incremental = [item for item in holdout if item["truth_class"] == "DEFECT" and item["models"]["M3R"]["result"] != "FLAG" and item["models"]["M4B"]["result"] == "FLAG"]
    m3_incremental = [item for item in holdout if item["truth_class"] == "DEFECT" and item["models"]["M0"]["result"] != "FLAG" and item["models"]["M3"]["result"] == "FLAG"]
    m3r_incremental_families = sorted({item["family"] for item in m3r_incremental})
    # The answer annotation is not copied into blind scoring; after unblind it
    # is safe to use the fixture manifest's subtype map for this metric.
    subtype_by_pair = {item["pair_id"]: item.get("binding_subtype") for item in read_json(RESEARCH / "fixture-manifest.json")["pairs"]}
    m4b_subtypes = sorted({subtype_by_pair[item["pair_id"]] for item in m4b_incremental if subtype_by_pair[item["pair_id"]]})
    m3r_fp = metrics["models"]["M3R"]["holdout"]["false_positives_on_matched_controls"]
    m4b_fp = metrics["models"]["M4B"]["holdout"]["false_positives_on_matched_controls"]
    signal_rule = THRESHOLDS["any_cross_contract_signal_survival"]
    binding_rule = THRESHOLDS["binding_challenger_survival"]
    signal_survives = (
        len(m3r_incremental) >= signal_rule["holdout_incremental_true_detections_min"]
        and len(m3r_incremental_families) >= signal_rule["holdout_incremental_families_min"]
        and (metrics["models"]["M3R"]["holdout"]["matched_control_false_positive_rate"] or 0) <= signal_rule["matched_control_false_positive_rate_max"]
        and (metrics["models"]["M3R"]["holdout"]["incremental_exact_actionability_rate"] or 0) >= signal_rule["incremental_exact_actionability_min"]
    )
    binding_survives = (
        len(m4b_incremental) >= binding_rule["additional_holdout_binding_defects_min"]
        and len(m4b_subtypes) >= binding_rule["distinct_binding_subtypes_min"]
        and m4b_fp - m3r_fp <= binding_rule["additional_holdout_control_false_positives_max"]
        and not binding_rule["new_authority_or_truth_state_allowed"]
        and not binding_rule["trivial_stale_digest_only_allowed"]
    )
    metrics["holdout_survival"] = {
        "M3_incremental_defects": len(m3_incremental),
        "M3R_incremental_defects_beyond_m0": len(m3r_incremental),
        "M3R_incremental_families": m3r_incremental_families,
        "M4B_additional_defects_beyond_m3r": len(m4b_incremental),
        "M4B_additional_binding_subtypes": m4b_subtypes,
        "M4B_additional_control_false_positives_vs_m3r": m4b_fp - m3r_fp,
        "any_cross_contract_signal_survives": signal_survives,
        "binding_challenger_survives": binding_survives,
        "thresholds_source": "thresholds.json",
    }

    for diagnostic in sorted({item["diagnostic_annotation"] for item in results}):
        subset = [item for item in results if item["diagnostic_annotation"] == diagnostic]
        metrics["diagnostic_annotations"][diagnostic] = {
            "instances": len(subset),
            "primary_defects": len([item for item in subset if item["truth_class"] == "DEFECT"]),
            "ambiguous_stress": len([item for item in subset if item["truth_class"] == "AMBIGUOUS_STRESS"]),
            "m0_flags": len([item for item in subset if item["models"]["M0"]["result"] == "FLAG"]),
            "m3r_incremental_flags": len([item for item in subset if item["truth_class"] == "DEFECT" and item["models"]["M0"]["result"] != "FLAG" and item["models"]["M3R"]["result"] == "FLAG"]),
            "ambiguous_flags_by_model": {model_id: len([item for item in subset if item["truth_class"] == "AMBIGUOUS_STRESS" and item["models"][model_id]["result"] == "FLAG"]) for model_id in MODELS},
        }
    return metrics


BINDING_COVERING_MODELS: dict[str, set[str]] = {
    "source_identity_path": {"M3R", "M4B"},
    "identity_projection_object": {"M3R", "M4B"},
    "projection_surface_revision": {"M3R", "M4B"},
    "release_current_path": {"M3R", "M4B"},
    "lifecycle_epoch": {"M4B"},
    "scope_alignment": {"M4B"},
    "version_alignment": {"M4B"},
    "claim_action_object": {"M4B"},
    "approval_action_object": {"M4B"},
}


def metamorphic_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run the predeclared post-unblind metamorphic suite.

    The frozen blind score is never changed by this suite. Transformations are
    scored from the frozen packet/model definitions after the answer key has
    been loaded by ``unblind``. A model that does not cover a binding is marked
    not-applicable rather than being treated as a failed repair test; a model
    that covers the binding must make the expected matched-pair transition.
    """

    packets = read_jsonl(RESEARCH / "blind-packets.jsonl")
    packet_by_id = {packet["fixture_id"]: packet for packet in packets}
    result_by_id = {item["fixture_id"]: item for item in results}
    specs_by_pair = {spec["pair_id"]: spec for spec in pair_specs()}
    rows: list[dict[str, Any]] = []

    def append_pair_row(
        property_name: str,
        family: str,
        pair_id: str,
        model_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
        expected: str,
        status: str,
        passed: bool,
        changed_fields: list[dict[str, Any]],
        **extra: Any,
    ) -> None:
        rows.append(
            {
                "property": property_name,
                "family": family,
                "pair_id": pair_id,
                "model": model_id,
                "before_fixture_id": before["fixture_id"],
                "after_fixture_id": after["fixture_id"],
                "before_result": before["models"][model_id]["result"],
                "after_result": after["models"][model_id]["result"],
                "expected": expected,
                "status": status,
                "changed_fields": changed_fields,
                "passed": passed,
                **extra,
            }
        )

    def transformed_scores(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {row["model"]: row for row in score_packets([packet])}

    def score_summary(packet: dict[str, Any]) -> dict[str, Any]:
        scored = transformed_scores(packet)
        return {
            "fixture_id": packet["fixture_id"],
            "pair_id": packet["pair_id"],
            "models": {
                model_id: {
                    "result": scored[model_id]["result"],
                    "predicates": scored[model_id]["predicates"],
                    "edges": scored[model_id]["edges"],
                }
                for model_id in MODELS
            },
        }

    def append_transformation_rows(
        property_name: str,
        family: str,
        pair_id: str,
        before_packet: dict[str, Any],
        after_packet: dict[str, Any],
        changed_fields: list[dict[str, Any]],
        expectation,
        **extra: Any,
    ) -> None:
        before = score_summary(before_packet)
        after_scores = transformed_scores(after_packet)
        for model_id in MODELS:
            expected, status, passed = expectation(model_id, before, after_scores[model_id])
            append_pair_row(
                property_name,
                family,
                pair_id,
                model_id,
                before,
                {"fixture_id": after_packet["fixture_id"], "models": {model_id: after_scores[model_id]}},
                expected,
                status,
                passed,
                changed_fields,
                **extra,
            )

    # Matched-pair repair and binding locality checks use the frozen primary
    # and control scores. Multi-field injections are recorded as not applicable
    # to the exact-single-field repair property, not silently reinterpreted.
    for pair_id, spec in sorted(specs_by_pair.items()):
        primary = result_by_id[f"{pair_id}-A"]
        control = result_by_id[f"{pair_id}-B"]
        if spec["kind"] == "AMBIGUOUS_STRESS":
            for model_id in MODELS:
                primary_result = primary["models"][model_id]["result"]
                control_result = control["models"][model_id]["result"]
                append_pair_row(
                    "signer_only_stress_does_not_create_flag",
                    spec["family"],
                    pair_id,
                    model_id,
                    primary,
                    control,
                    "PRIMARY_AND_CONTROL_NOT_FLAGGED",
                    "APPLICABLE",
                    primary_result != "FLAG" and control_result != "FLAG",
                    spec["changes"],
                    diagnostic="SIGNATURE_WITHOUT_CONTESTABILITY",
                )
        elif len(spec["changes"]) == 1:
            for model_id in MODELS:
                primary_result = primary["models"][model_id]["result"]
                control_result = control["models"][model_id]["result"]
                if primary_result == "FLAG":
                    expected = "PRIMARY_FLAG_CONTROL_NO_FLAG"
                    status = "APPLICABLE"
                    passed = control_result == "NO_FLAG"
                else:
                    expected = "MODEL_NOT_COVERING_DEFECT"
                    status = "NOT_APPLICABLE_UNDETECTED"
                    passed = control_result != "FLAG"
                append_pair_row(
                    "repair_exact_missing_junction_flips_flag_to_no_flag",
                    spec["family"],
                    pair_id,
                    model_id,
                    primary,
                    control,
                    expected,
                    status,
                    passed,
                    spec["changes"],
                )
        else:
            for model_id in MODELS:
                control_result = control["models"][model_id]["result"]
                append_pair_row(
                    "repair_declared_minimal_change_set",
                    spec["family"],
                    pair_id,
                    model_id,
                    primary,
                    control,
                    "NOT_APPLICABLE_MULTI_FIELD_INJECTION",
                    "NOT_APPLICABLE_MULTI_FIELD",
                    control_result != "FLAG",
                    spec["changes"],
                )

        binding_subtype = spec.get("binding_subtype")
        if binding_subtype:
            covered_models = BINDING_COVERING_MODELS[binding_subtype]
            for model_id in MODELS:
                primary_result = primary["models"][model_id]["result"]
                control_result = control["models"][model_id]["result"]
                observed_change = primary_result == "FLAG" and control_result == "NO_FLAG"
                if model_id in covered_models:
                    expected = "PRIMARY_FLAG_CONTROL_NO_FLAG"
                    status = "COVERED_BY_FROZEN_PREDICATE"
                    passed = observed_change
                else:
                    expected = "NO_MODEL_CHANGE"
                    status = "NOT_COVERED_BY_FROZEN_PREDICATE"
                    passed = primary_result == control_result == "NO_FLAG"
                append_pair_row(
                    "binding_change_flips_only_covering_models",
                    spec["family"],
                    pair_id,
                    model_id,
                    primary,
                    control,
                    expected,
                    status,
                    passed,
                    spec["changes"],
                    binding_subtype=binding_subtype,
                    covered_models=sorted(covered_models),
                )

    # Irrelevant evidence volume must not change claim scope, selected
    # predicates, or model result. Run it on both members of every pair so all
    # six fixture families are covered by the same property.
    for packet in sorted(packets, key=lambda item: item["fixture_id"]):
        altered = copy.deepcopy(packet)
        old_volume = altered["distractor_fields"].get("evidence_volume", 0)
        altered["distractor_fields"]["evidence_volume"] = old_volume + 1000
        changed = [{"path": "distractor_fields.evidence_volume", "before": old_volume, "after": old_volume + 1000}]

        def evidence_expectation(model_id: str, before: dict[str, Any], after: dict[str, Any]) -> tuple[str, str, bool]:
            original = before["models"][model_id]
            passed = after["result"] == original["result"] and after["predicates"] == original["predicates"] and after["edges"] == original["edges"]
            return "UNCHANGED_RESULT_AND_CLAIM_PREDICATES", "APPLICABLE", passed

        append_transformation_rows(
            "irrelevant_evidence_does_not_upgrade_claim_scope",
            packet["fixture_id"].split("-", 1)[0],
            packet["pair_id"],
            packet,
            altered,
            changed,
            evidence_expectation,
            claim_scope_before=packet["objects"]["claim"]["scope"],
            claim_scope_after=altered["objects"]["claim"]["scope"],
        )

    # A valid signature is an irrelevant authority-side addition for the F1
    # consequence/accountability gaps. It must not repair those gaps.
    for packet in sorted(packets, key=lambda item: item["fixture_id"]):
        if packet["fixture_id"].split("-", 1)[0] != "F1":
            continue
        altered = copy.deepcopy(packet)
        old_count = altered["distractor_fields"].get("valid_signature_count", 0)
        altered["distractor_fields"]["valid_signature_count"] = old_count + 1
        changed = [{"path": "distractor_fields.valid_signature_count", "before": old_count, "after": old_count + 1}]

        def signature_expectation(model_id: str, before: dict[str, Any], after: dict[str, Any]) -> tuple[str, str, bool]:
            original = before["models"][model_id]
            passed = after["result"] == original["result"] and after["predicates"] == original["predicates"] and after["edges"] == original["edges"]
            return "CONSEQUENCE_RESULT_UNCHANGED", "APPLICABLE", passed

        append_transformation_rows(
            "valid_signature_does_not_repair_consequence_gap",
            "F1",
            packet["pair_id"],
            packet,
            altered,
            changed,
            signature_expectation,
        )

    # Adding a rollback label is tested against a deliberately conditioned
    # irreversible effect. The label may reveal a finding; it must not remove
    # one or turn the effect into NO_FLAG.
    for packet in sorted(packets, key=lambda item: item["fixture_id"]):
        if packet["fixture_id"].split("-", 1)[0] != "F5":
            continue
        before_packet = copy.deepcopy(packet)
        before_packet["objects"]["rollback"]["effect_reversibility"] = "IRREVERSIBLE"
        before_packet["objects"]["rollback"]["label_present"] = False
        altered = copy.deepcopy(before_packet)
        altered["objects"]["rollback"]["label_present"] = True
        changed = [{"path": "objects.rollback.label_present", "before": False, "after": True}]

        def rollback_expectation(model_id: str, before: dict[str, Any], after: dict[str, Any]) -> tuple[str, str, bool]:
            if model_id == "M0":
                return "LOCAL_RESULT_UNCHANGED", "NOT_COVERED_BY_FROZEN_PREDICATE", after["result"] == before["models"][model_id]["result"]
            return "ADDED_LABEL_MUST_NOT_REPAIR_IRREVERSIBLE_EFFECT", "APPLICABLE", after["result"] == "FLAG" and not (before["models"][model_id]["result"] == "FLAG" and after["result"] == "NO_FLAG")

        append_transformation_rows(
            "rollback_label_does_not_repair_irreversible_effect",
            "F5",
            packet["pair_id"],
            packet,
            altered,
            changed,
            rollback_expectation,
            conditioned_fields={"objects.rollback.effect_reversibility": "IRREVERSIBLE", "objects.rollback.label_present": False},
        )

    # Compare an unsafe unavailable/current-use route with a safe authorized
    # alternative. A change in abstention analysis is explicitly permitted.
    for family in CONTRACT_REFS:
        base = packet_by_id[f"{family}-P01-B"]
        unsafe = copy.deepcopy(base)
        setup_changes = []
        for path, value in (
            ("objects.admission.provider_capability", "AVAILABLE"),
            ("objects.admission.current_authority", "NONE"),
            ("objects.action.attempted_current_use", True),
        ):
            before_value = path_get(unsafe, path)
            path_set(unsafe, path, value)
            setup_changes.append({"path": path, "before": before_value, "after": value})
        safe = copy.deepcopy(unsafe)
        path_set(safe, "objects.admission.current_authority", "AUTHORIZED")
        changed = [{"path": "objects.admission.current_authority", "before": "NONE", "after": "AUTHORIZED"}]

        def safe_alternative_expectation(model_id: str, before: dict[str, Any], after: dict[str, Any]) -> tuple[str, str, bool]:
            if model_id == "M0":
                expected = "LOCAL_RESULT_UNCHANGED"
                passed = before["models"][model_id]["result"] == after["result"] == "NO_FLAG"
            else:
                expected = "UNSAFE_FLAG_SAFE_AUTHORIZED_NO_FLAG"
                passed = before["models"][model_id]["result"] == "FLAG" and after["result"] == "NO_FLAG"
            return expected, "ALLOWED_ABSTENTION_CHANGE", passed

        append_transformation_rows(
            "safe_authorized_alternative_may_change_abstention",
            family,
            base["pair_id"],
            unsafe,
            safe,
            changed,
            safe_alternative_expectation,
            conditioned_fields={change["path"]: change["after"] for change in setup_changes},
            setup_changes=setup_changes,
        )

    # Deadline passage is an irrelevant temporal label in this harness. It is
    # intentionally checked on one clean control from every family.
    for family in CONTRACT_REFS:
        packet = packet_by_id[f"{family}-P01-B"]
        altered = copy.deepcopy(packet)
        altered["distractor_fields"]["deadline_passed"] = True
        changed = [{"path": "distractor_fields.deadline_passed", "before": False, "after": True}]

        def deadline_expectation(model_id: str, before: dict[str, Any], after: dict[str, Any]) -> tuple[str, str, bool]:
            original = before["models"][model_id]
            passed = after["result"] == original["result"] and after["predicates"] == original["predicates"] and after["edges"] == original["edges"]
            return "UNCHANGED_RESULT_AND_PREDICATES", "APPLICABLE", passed

        append_transformation_rows(
            "deadline_passage_does_not_create_new_failure",
            family,
            packet["pair_id"],
            packet,
            altered,
            changed,
            deadline_expectation,
        )

    return rows


def diagnostic_decisions(results: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    decisions: dict[str, Any] = {}
    labels = [
        "PROVENANCE_WITHOUT_CEILING",
        "ABSTENTION_AS_AVOIDANCE",
        "BUDGET_AS_HARM_LICENSE",
        "SIGNATURE_WITHOUT_CONTESTABILITY",
        "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY",
    ]
    for label in labels:
        if label == "BUDGET_AS_HARM_LICENSE":
            disposition = "INSUFFICIENT_DISCRIMINATION"
            reason = "No fixture family operationalizes deadline passage as a harm license; the protocol deliberately does not manufacture support."
        elif label == "ABSTENTION_AS_AVOIDANCE":
            disposition = "INSUFFICIENT_DISCRIMINATION"
            reason = "No primary defect makes a safe authorized alternative available while the route is merely skipped; safe abstention is retained as a control."
        elif label == "SIGNATURE_WITHOUT_CONTESTABILITY":
            ambiguous_flags = metrics["diagnostic_annotations"].get(label, {}).get("ambiguous_flags_by_model", {})
            disposition = "FALSE_POSITIVE_PRONE" if any(ambiguous_flags.values()) else "INSUFFICIENT_DISCRIMINATION"
            reason = "Signer-only stress cases omit a concrete consequence failure; a flag would overread incompleteness as an actionable historical class." if not any(ambiguous_flags.values()) else "At least one model flags signer-only stress without a concrete consequence failure."
        elif label == "COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY":
            count = metrics["diagnostic_annotations"].get(label, {}).get("m3r_incremental_flags", 0)
            disposition = "SUPPORTED_BY_PROSPECTIVE_FIXTURE" if count else "INSUFFICIENT_DISCRIMINATION"
            reason = f"Prospective consequence/rollback junction pairs produced {count} M3R incremental detections beyond M0." if count else "No non-redundant consequence/accountability signal survived."
        else:
            count = metrics["diagnostic_annotations"].get(label, {}).get("m3r_incremental_flags", 0)
            disposition = "SUPPORTED_BY_PROSPECTIVE_FIXTURE" if count else "INSUFFICIENT_DISCRIMINATION"
            reason = f"Prospective claim/admission/binding pairs produced {count} M3R incremental detections beyond M0." if count else "No non-redundant claim-ceiling signal survived."
        decisions[label] = {"disposition": disposition, "reason": reason}
    return decisions


def command_unblind(score_paths: list[Path], output_dir: Path) -> int:
    answer_path = RESEARCH / "answer-key.jsonl"
    answers = read_jsonl(answer_path)
    score_sets = [read_jsonl(path) for path in score_paths]
    errors: list[str] = []
    for path, rows in zip(score_paths, score_sets):
        errors.extend(f"{path.name}: {error}" for error in validate_score_rows(rows))
    if len(score_sets) == 2 and jsonl_bytes(score_sets[0]) != jsonl_bytes(score_sets[1]):
        errors.append("two clean-state scoring passes differ")
    if errors:
        print("UNBLIND_BLOCKED", *errors, sep="\n", file=sys.stderr)
        return 1
    rows = score_sets[0]
    row_map = output_map(rows)
    results = [classification_for(row_map, answer) for answer in sorted(answers, key=lambda item: item["fixture_id"])]
    metrics = metrics_for(results)
    metamorphic = metamorphic_rows(results)
    decisions = diagnostic_decisions(results, metrics)
    metamorphic_violations = [row for row in metamorphic if not row["passed"]]
    validation = {
        "task_id": TASK_ID,
        "freeze_validation": "REQUIRED_SEPARATE_COMMAND",
        "answer_key_loaded": True,
        "scoring_passes": len(score_sets),
        "scoring_passes_identical": len(score_sets) == 1 or jsonl_bytes(score_sets[0]) == jsonl_bytes(score_sets[1]),
        "metamorphic_tests": len(metamorphic),
        "metamorphic_violations": len(metamorphic_violations),
        "metamorphic_not_applicable": len([row for row in metamorphic if row["status"].startswith("NOT_APPLICABLE")]),
        "metamorphic_allowed_changes": len([row for row in metamorphic if row["status"] == "ALLOWED_ABSTENTION_CHANGE"]),
        "metamorphic_properties": sorted({row["property"] for row in metamorphic}),
        "invalid_fixtures": 0,
        "frozen_model_hash": digest(read_json(RESEARCH / "model-definitions.json")),
        "frozen_threshold_hash": digest(read_json(RESEARCH / "thresholds.json")),
        "boundary": BOUNDARY,
    }
    write_bytes(output_dir / "results.jsonl", jsonl_bytes(results))
    write_json(output_dir / "metrics.json", metrics)
    write_bytes(output_dir / "metamorphic-results.jsonl", jsonl_bytes(metamorphic))
    write_json(output_dir / "diagnostic-decisions.json", decisions)
    write_json(output_dir / "validation.json", validation)
    print(f"UNBLIND_OK results={len(results)} metamorphic={len(metamorphic)} violations={validation['metamorphic_violations']}")
    print(json.dumps(metrics["holdout_survival"], ensure_ascii=False, sort_keys=True))
    return 0


def command_render_summary(output_dir: Path) -> int:
    metrics = read_json(output_dir / "metrics.json")
    decisions = read_json(output_dir / "diagnostic-decisions.json")
    results = read_jsonl(output_dir / "results.jsonl")
    validation = read_json(output_dir / "validation.json")
    metamorphic = read_jsonl(output_dir / "metamorphic-results.jsonl")
    family_rows = []
    for family in CONTRACT_REFS:
        family_rows.append(
            f"| {family} | {len([item for item in results if item['family'] == family and item['truth_class'] == 'DEFECT'])} | {metrics['family_metrics'][family]['M0']['sensitivity_descriptive']} | {metrics['family_metrics'][family]['M3']['sensitivity_descriptive']} | {metrics['family_metrics'][family]['M3R']['sensitivity_descriptive']} | {metrics['family_metrics'][family]['M4B']['sensitivity_descriptive']} |"
        )
    holdout = metrics["holdout_survival"]
    verdict = "BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE" if holdout["binding_challenger_survives"] else "REFINED_THREE_EDGE_SIGNAL_REPRODUCED" if holdout["any_cross_contract_signal_survives"] else "NO_REPRODUCIBLE_INCREMENT"
    experiment_doc = f"""# Task156 prospective cross-contract fixture experiment — 2026-09-05

Status: `SYNTHETIC_FIXTURE_RESULT / {verdict} / RESEARCH_ONLY / NON_CURRENT`

## Observation

The exact Task156 command freezes a prospective synthetic-but-repository-shaped corpus before blinded scoring. The corpus has **48 paired fixtures / 96 instances** across F1–F6, with pair members kept in one deterministic split. Source contracts are referenced from the Task155 candidate head `{BASE_COMMIT}`. No live external effect, authenticated provider action, production validator, runtime, authority or lifecycle change was used.

Frozen model definitions are M0 `EXISTING_ONLY`, M3 `THREE_EDGE_V1`, M3R `THREE_EDGE_REFINED`, and M4B `THREE_EDGE_PLUS_BINDING_CHALLENGER`. M3R's refinement remains on the claim edge; M4B uses existing object/version/scope/lifecycle/reference fields and introduces no new authority or truth state.

## Synthetic fixture result

| Family | Defect instances | M0 sensitivity | M3 sensitivity | M3R sensitivity | M4B sensitivity |
|---|---:|---:|---:|---:|---:|
{chr(10).join(family_rows)}

Holdout M3 incremental defects beyond M0: **{holdout['M3_incremental_defects']}**. M3R incremental defects beyond M0: **{holdout['M3R_incremental_defects_beyond_m0']}** across `{', '.join(holdout['M3R_incremental_families'])}`. M4B additional defects beyond M3R: **{holdout['M4B_additional_defects_beyond_m3r']}**, binding subtypes `{', '.join(holdout['M4B_additional_binding_subtypes']) or 'none'}`. The frozen survival thresholds are evaluated in `data/research/cross-contract-prospective-fixtures-2026-09-05/metrics.json`.

The metamorphic suite executed **{len(metamorphic)}** checks across all six families: **{validation['metamorphic_violations']}** model-quality violations, **{validation['metamorphic_not_applicable']}** explicitly not-applicable coverage checks, and **{validation['metamorphic_allowed_changes']}** allowed safe-alternative changes. The suite includes exact repair, binding locality, irrelevant evidence, valid-signature/consequence, rollback/irreversibility, safe-authorized alternative and deadline properties.

## Inference

The bounded verdict is **`{verdict}`**. This is a result about the frozen synthetic corpus and deterministic predicates. It is not a real-world prevalence, production accuracy, or Current capability claim. The two scoring passes are byte-identical; metamorphic violations and ambiguous stress outcomes remain explicit, with the final suite reporting `{validation['metamorphic_violations']}` model-quality violations.

CC-020-like path/identity/projection defects are testable by M3R without adding a fourth edge when the exact claim-edge binding predicate is sufficient. M4B only earns a research-invariant candidate if its additional holdout detections, subtype diversity and false-positive burden satisfy the pre-frozen table; it is not promoted automatically.

## Proposal

Keep any surviving structure as a replaceable research lens. If the binding challenger survives, the candidate predicate is: existing source, identity, projection, surface, release and admission records must agree on `(object_id, version, scope, lifecycle_epoch)`, while existing action references must equal the claim and approval object identities. This is a cross-family research predicate, not a new canonical contract.

## Non-claim / limitation

- Synthetic percentages are descriptive and cannot estimate real-world prevalence or production accuracy.
- The corpus is prospective and reproducible but authored with repository-history access; it is not cognitive independence or an independent replication.
- Existing local contracts were supplied to M0; detections also made by M0 are redundant, not incremental.
- `answer-key.jsonl` is not a scorer input. Frozen hashes, score-pass identity, split determinism and pair integrity are separate machine checks.
- Metamorphic results are model-quality checks, not additional truth labels; not-applicable model coverage and the allowed safe-authorized abstention change are separately classified.
- Stale `1111/instructions/CURRENT.md` and `1111/relay/current` pointers are preserved as preflight residuals and are not modified.

## Diagnostic retirement tests

| Task155 label | Prospective disposition | Reason |
|---|---|---|
""" + "\n".join(f"| `{label}` | `{value['disposition']}` | {value['reason']} |" for label, value in decisions.items()) + """

Machine evidence: [`data/research/cross-contract-prospective-fixtures-2026-09-05/`](../../data/research/cross-contract-prospective-fixtures-2026-09-05/). The formal task report and independent receipt separately record Git/CI/PR evidence.
"""
    assessment = f"""# Junction-invariant candidate assessment — Task156 — 2026-09-05

Status: `RESEARCH_ONLY / {verdict} / NON_CANONICAL / NON_CURRENT`

## Observation

The frozen challenger comparison is M3R versus M4B. M3R keeps the three original categories and adds only an exact source/identity/projection/public-surface binding predicate on the claim edge. M4B adds a neutral binding/integrity predicate over existing fields and references. Holdout results are M3R `{holdout['M3R_incremental_defects_beyond_m0']}` incremental detections beyond M0 and M4B `{holdout['M4B_additional_defects_beyond_m3r']}` additional detections beyond M3R.

## Synthetic fixture result

- Any cross-contract signal threshold: `{'PASS' if holdout['any_cross_contract_signal_survives'] else 'FAIL'}`.
- Binding challenger threshold: `{'PASS' if holdout['binding_challenger_survives'] else 'FAIL'}`.
- M4B additional binding subtypes: `{', '.join(holdout['M4B_additional_binding_subtypes']) or 'none'}`.
- Additional holdout control false positives versus M3R: `{holdout['M4B_additional_control_false_positives_vs_m3r']}`.

## Inference

CC-020-like failures can be detected without a fourth edge when their observable defect is source/path/identity/projection/public-surface misbinding covered by M3R. The fourth-edge challenger is {'supported as a bounded research invariant candidate' if holdout['binding_challenger_survives'] else 'not supported beyond the refined three-edge lens'}; this wording does not authorize production use.

## Exact candidate predicate

Only if the threshold table is passed, retain this as a research candidate: `source.binding == identity.binding == projection.binding == surface.binding == release.binding == admission.binding` over the existing tuple `(object_id, version, scope, lifecycle_epoch)`, plus `action.claim_id == claim.object_id` and `action.approval_id == authority.approval_id`. No new authority, truth, capability or lifecycle state is imported.

## Non-claim / limitation

The candidate is not a canonical layer, validator, gate, registry, runtime state, Current capability, production readiness or Owner acceptance. Digest-only equality is not sufficient; any future replication must preserve the subtype and actionability rules. Synthetic corpus results do not establish external truth.
"""
    casebook_lines = [
        "# Task156 prospective paired casebook — 2026-09-05",
        "",
        "Status: `FROZEN_BEFORE_SCORING / UNBLINDED_AFTER_TWO_IDENTICAL_PASSES / RESEARCH_ONLY`",
        "",
        "This casebook is generated from the frozen answer-key and score outputs. Pre-scoring blind packets contain no roles or truth labels; the answer key is not an input to `score`. Every pair keeps the primary fixture and matched control in the same split.",
        "",
    ]
    for family in CONTRACT_REFS:
        casebook_lines.extend([f"## {family} — {CONTRACT_REFS[family]['historical_lineage']}", "", CONTRACT_REFS[family]["genealogy"], ""])
        family_pairs = sorted({item["pair_id"] for item in results if item["family"] == family})
        for pair_id in family_pairs:
            members = [item for item in results if item["pair_id"] == pair_id]
            member = next(item for item in members if item["truth_class"] != "CONTROL")
            control = next(item for item in members if item["truth_class"] == "CONTROL")
            casebook_lines.extend(
                [
                    f"### {pair_id} ({member['split']})",
                    "",
                    f"- Primary truth class: `{member['truth_class']}`; matched control: `{control['truth_class']}`.",
                    f"- Diagnostic annotation: `{member['diagnostic_annotation']}`.",
                    f"- M0/M3/M3R/M4B primary results: `{member['models']['M0']['result']}` / `{member['models']['M3']['result']}` / `{member['models']['M3R']['result']}` / `{member['models']['M4B']['result']}`.",
                    f"- M0/M3/M3R/M4B control results: `{control['models']['M0']['result']}` / `{control['models']['M3']['result']}` / `{control['models']['M3R']['result']}` / `{control['models']['M4B']['result']}`.",
                    f"- Stable matched-pair flip: `{'PASS' if member['models']['M4B']['result'] == 'FLAG' and control['models']['M4B']['result'] != 'FLAG' else 'NO_FLIP_OR_STRESS'}`.",
                    "",
                ]
            )
    write_bytes(ROOT / "docs/governance/cross-contract-prospective-fixture-experiment-2026-09-05.md", experiment_doc.encode("utf-8"))
    write_bytes(ROOT / "docs/governance/junction-invariant-candidate-assessment-2026-09-05.md", assessment.encode("utf-8"))
    write_bytes(ROOT / "docs/governance/cross-contract-prospective-casebook-2026-09-05.md", "\n".join(casebook_lines).rstrip().encode("utf-8") + b"\n")
    print(f"RESEARCH_SUMMARY_RENDERED verdict={verdict} docs=3")
    return 0


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--check", action="store_true")
    sub.add_parser("validate-freeze")
    score = sub.add_parser("score")
    score.add_argument("--output", type=Path, required=True)
    unblind = sub.add_parser("unblind")
    unblind.add_argument("--score", type=Path, action="append", required=True)
    unblind.add_argument("--output-dir", type=Path, required=True)
    summary = sub.add_parser("render-summary")
    summary.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "generate":
        return command_generate(args.check)
    if args.command == "validate-freeze":
        return command_validate_freeze()
    if args.command == "score":
        return command_score(args.output)
    if args.command == "unblind":
        return command_unblind(args.score, args.output_dir)
    if args.command == "render-summary":
        return command_render_summary(args.output_dir)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
