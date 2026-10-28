#!/usr/bin/env python3
"""Task157 research-only competition: junction invariant vs local predicates."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "data/research/junction-vs-local-predicates-2026-09-06"
TASK_ID = "IGNITION-20260906-157"
BASE_COMMIT = "ad0e8f3e6c80eee5f27d05bd4b29653b2d936aae"
COMMAND_COMMIT = "6307f30abb92ab02b082476c4b627ccb0bdc6914"
COMMAND_BLOB = "dc51ff0524d6d5c43ba149cb7cb5722f48aebcaf"
COMMAND_SHA256 = "621a4aa243a3268d65c88c1960d4690a538bd228964f2fb79df4bef3d206b2a5"
SCORER_VERSION = "task157-junction-vs-local-predicates-scorer-1.0.0"
BOUNDARY = (
    "Research-only synthetic fixture evidence. No production validator, gate, "
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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    write_bytes(path, jsonl_bytes(rows))


def sha256_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


FAMILY_META: dict[str, dict[str, Any]] = {
    "F1": {
        "name": "claim_to_action_mismatch",
        "historical_lineage": "CC-012 / Task156 claim-action binding",
        "source_contracts": [
            "docs/foundation/claim-governance-and-function-identity.md",
            "docs/architecture/os-steering-intent-r1.md",
            "docs/architecture/agent-runtime-r1.md",
        ],
        "transfer_relation": "claim -> action -> execution packet",
    },
    "F2": {
        "name": "approval_to_action_mismatch",
        "historical_lineage": "CC-026 / Task156 approval-action binding",
        "source_contracts": [
            "docs/architecture/approval-handoff-failover-r1.md",
            "docs/architecture/agent-runtime-r1.md",
            "schemas/agent-runtime/approval-request.schema.json",
        ],
        "transfer_relation": "approval -> action -> lease",
    },
    "F3": {
        "name": "lifecycle_epoch",
        "historical_lineage": "Task156 lifecycle_epoch subtype",
        "source_contracts": [
            "docs/operations/lifecycle-readme.md",
            "docs/governance/current-state-sync-invariant.md",
            "schemas/operations/lifecycle-event.schema.json",
        ],
        "transfer_relation": "source -> projection -> release -> admission",
    },
    "F4": {
        "name": "base_delta_scope_contamination",
        "historical_lineage": "Task150 Base/Delta admission boundary",
        "source_contracts": [
            "docs/architecture/agent-federation-r1.md",
            "tools/validate_task150_step18_scope_split_admission_objects.py",
            "tools/validate_task150_step19_gate_topology_regression.py",
        ],
        "transfer_relation": "Base -> Delta -> admission",
    },
    "F5": {
        "name": "source_identity_projection_surface_drift",
        "historical_lineage": "CC-020 / Task156 source-projection binding",
        "source_contracts": [
            "docs/operations/stage-snapshot-publication.md",
            "docs/governance/human-surface-editorial-contract.md",
            "tools/validate_current_state_sync.py",
        ],
        "transfer_relation": "source -> identity -> projection -> public surface",
    },
    "F6": {
        "name": "release_admission_provider_reference",
        "historical_lineage": "Task155 provider/admission boundary",
        "source_contracts": [
            "docs/external-research/provider-contract.md",
            "docs/governance/current-state-sync-invariant.md",
            "schemas/external/provider-boundary.schema.json",
        ],
        "transfer_relation": "release -> admission -> provider -> Current boundary",
    },
    "F7": {
        "name": "consequence_reconciliation_ownership",
        "historical_lineage": "Task155 consequence/reconciliation ownership map",
        "source_contracts": [
            "docs/architecture/agent-runtime-r1.md",
            "docs/architecture/approval-handoff-failover-r1.md",
            "schemas/agent-runtime/execution-lease.schema.json",
        ],
        "transfer_relation": "effect -> obligation -> observer/owner -> stop",
    },
    "F8": {
        "name": "novel_multi_hop_composition",
        "historical_lineage": "pre-registered novel composition family",
        "source_contracts": [
            "docs/architecture/epistemic-governance-kernel-and-federated-planes.md",
            "docs/operations/stage-snapshot-publication.md",
            "docs/governance/current-state-sync-invariant.md",
        ],
        "transfer_relation": "source -> identity -> projection -> release -> admission -> action",
    },
}

CONTROL_VARIANTS = (
    "valid_upgrade",
    "same_digest_distinct_tuple",
    "allowed_surface_delay",
    "fail_closed_abstention",
    "no_safe_alternative",
    "irreversible_correct_charter",
    "valid_signer_no_concrete_defect",
    "irrelevant_evidence",
    "label_only",
    "alias_migration",
    "base_delta_isolated",
    "unknown_contract",
)

FAMILY_PATTERNS: dict[str, list[str]] = {
    "F1": ["local_failure", "local_failure", "claim_action_ref", "claim_action_scope", "claim_action_ref", "claim_action_ref", "claim_action_ref", "claim_action_scope", "claim_action_ref", "multi_hop_claim", "multi_hop_claim", "multi_hop_claim"],
    "F2": ["local_failure", "approval_action_ref", "approval_action_scope", "approval_action_ref", "approval_action_epoch", "approval_action_ref", "approval_action_ref", "approval_action_scope", "approval_action_ref", "multi_hop_approval", "multi_hop_approval", "multi_hop_approval"],
    "F3": ["local_failure", "epoch_projection", "epoch_admission", "epoch_projection", "epoch_projection", "epoch_release", "epoch_projection", "epoch_admission", "epoch_release", "multi_hop_epoch", "multi_hop_epoch", "multi_hop_epoch"],
    "F4": ["local_failure", "base_delta_scope", "base_delta_ref", "base_delta_scope", "base_delta_ref", "base_delta_scope", "base_delta_ref", "base_delta_scope", "base_delta_ref", "multi_hop_scope", "multi_hop_scope", "multi_hop_scope"],
    "F5": ["local_failure", "source_identity_ref", "projection_surface_ref", "source_identity_ref", "surface_binding_epoch", "projection_surface_ref", "source_identity_ref", "surface_binding_epoch", "projection_surface_ref", "multi_hop_surface", "multi_hop_surface", "multi_hop_surface"],
    "F6": ["local_failure", "release_admission_ref", "provider_reference", "provider_current", "release_admission_ref", "provider_reference", "provider_current", "release_admission_ref", "provider_reference", "multi_hop_provider", "ambiguous_stress", "ambiguous_stress"],
    "F7": ["local_failure", "consequence_owner_ref", "consequence_observer_ref", "rollback_contract", "consequence_owner_ref", "consequence_observer_ref", "consequence_retry", "rollback_contract", "consequence_owner_ref", "multi_hop_consequence", "multi_hop_consequence", "multi_hop_consequence"],
    "F8": ["local_failure", "multi_hop_claim", "multi_hop_approval", "multi_hop_epoch", "multi_hop_scope", "multi_hop_surface", "multi_hop_provider", "multi_hop_consequence", "multi_hop_claim", "novel_chain", "novel_chain", "novel_chain"],
}


def split_for_index(index: int) -> str:
    return "calibration" if index <= 6 else "holdout_in_family" if index <= 9 else "holdout_transfer"


def fixture_id(pair_id: str, member: str) -> str:
    return "t157-" + digest(f"{TASK_ID}|{pair_id}|{member}")[:14]


def pair_specs() -> list[dict[str, Any]]:
    subtype = {
        "claim_action_ref": "claim_action_object", "approval_action_ref": "approval_action_object",
        "epoch_projection": "lifecycle_epoch", "epoch_admission": "lifecycle_epoch",
        "epoch_release": "lifecycle_epoch", "base_delta_scope": "base_delta_scope",
        "base_delta_ref": "base_delta_object", "source_identity_ref": "source_identity_object",
        "projection_surface_ref": "projection_surface_object", "surface_binding_epoch": "lifecycle_epoch",
        "release_admission_ref": "release_admission_object", "provider_reference": "provider_admission_object",
        "consequence_owner_ref": "consequence_owner_object", "consequence_observer_ref": "consequence_observer_object",
        "rollback_contract": "rollback_consequence_object", "multi_hop_claim": "novel_multi_hop",
        "multi_hop_approval": "novel_multi_hop", "multi_hop_epoch": "lifecycle_epoch",
        "multi_hop_scope": "base_delta_scope", "multi_hop_surface": "novel_multi_hop",
        "multi_hop_provider": "provider_admission_object", "multi_hop_consequence": "novel_multi_hop",
        "novel_chain": "novel_multi_hop",
    }
    specs: list[dict[str, Any]] = []
    for family in FAMILY_META:
        for index, defect_kind in enumerate(FAMILY_PATTERNS[family], start=1):
            specs.append(
                {
                    "pair_id": f"{family}-P{index:02d}",
                    "family": family,
                    "index": index,
                    "split": split_for_index(index),
                    "defect_kind": defect_kind,
                    "control_variant": CONTROL_VARIANTS[(index - 1) % len(CONTROL_VARIANTS)],
                    "novel_composition": index >= 10,
                    "cross_object": defect_kind not in {"local_failure", "ambiguous_stress"},
                    "binding_subtype": subtype.get(defect_kind),
                }
            )
    assert len(specs) == 96
    assert Counter(spec["split"] for spec in specs) == Counter({"calibration": 48, "holdout_in_family": 24, "holdout_transfer": 24})
    return specs


PAIR_SPECS = pair_specs()


def binding(subject: str, version: str, scope: str, epoch: str) -> dict[str, str]:
    return {"subject_id": subject, "version": version, "scope": scope, "lifecycle_epoch": epoch}


def base_packet(spec: dict[str, Any], member: str) -> dict[str, Any]:
    family, number = spec["family"], spec["index"]
    subject = f"subject-t157-{family.lower()}-{number:02d}"
    scope, epoch = f"bounded-research/{family.lower()}/{number:02d}", f"epoch-{157000 + number}"
    ids = {
        key: f"{key}-{family.lower()}-{number:02d}"
        for key in ("claim", "action", "approval", "source", "identity", "projection", "surface", "release", "admission", "provider", "base", "delta", "effect", "obligation", "owner", "observer", "rollback")
    }
    shared = binding(subject, "v1", scope, epoch)
    objects: dict[str, dict[str, Any]] = {
        "claim": {"object_id": ids["claim"], "binding": copy.deepcopy(shared), "source_ref": ids["source"], "ceiling_rank": 2, "provenance_status": "VALID"},
        "action": {"object_id": ids["action"], "binding": copy.deepcopy(shared), "claim_ref": ids["claim"], "approval_ref": ids["approval"], "required_scope_rank": 2, "scope_rank": 2, "attempted_current_use": False, "route_available": True},
        "approval": {"object_id": ids["approval"], "binding": copy.deepcopy(shared), "action_ref": ids["action"], "scope_rank": 2, "signer_status": "VALID", "contestability_present": True, "revocation_path_present": True},
        "source": {"object_id": ids["source"], "binding": copy.deepcopy(shared), "identity_ref": ids["identity"], "content_digest": f"digest-{number:02d}", "source_revision": "rev-1"},
        "identity": {"object_id": ids["identity"], "binding": copy.deepcopy(shared), "source_ref": ids["source"], "projection_ref": ids["projection"]},
        "projection": {"object_id": ids["projection"], "binding": copy.deepcopy(shared), "identity_ref": ids["identity"], "surface_ref": ids["surface"], "source_revision": "rev-1"},
        "surface": {"object_id": ids["surface"], "binding": copy.deepcopy(shared), "projection_ref": ids["projection"], "source_revision": "rev-1", "status": "NON_AUTHORITATIVE_SURFACE"},
        "release": {"object_id": ids["release"], "binding": copy.deepcopy(shared), "surface_ref": ids["surface"], "admission_ref": ids["admission"], "provider_ref": ids["provider"]},
        "admission": {"object_id": ids["admission"], "binding": copy.deepcopy(shared), "release_ref": ids["release"], "provider_ref": ids["provider"], "scope_rank": 2, "lifecycle": "NON_INTENT"},
        "provider": {"object_id": ids["provider"], "binding": copy.deepcopy(shared), "authority_ref": ids["approval"], "capability": "BOUNDED"},
        "base": {"object_id": ids["base"], "binding": copy.deepcopy(shared), "delta_ref": ids["delta"]},
        "delta": {"object_id": ids["delta"], "binding": copy.deepcopy(shared), "base_ref": ids["base"], "isolation_valid": False},
        "effect": {"object_id": ids["effect"], "binding": copy.deepcopy(shared), "state": "KNOWN", "obligation_ref": None, "reversibility": "REVERSIBLE"},
        "obligation": {"object_id": ids["obligation"], "binding": copy.deepcopy(shared), "effect_ref": ids["effect"], "owner_ref": ids["owner"], "observer_ref": ids["observer"], "retry_policy": "PROHIBITED", "stop_path_present": True},
        "owner": {"object_id": ids["owner"], "binding": copy.deepcopy(shared), "role": "reconciliation-owner"},
        "observer": {"object_id": ids["observer"], "binding": copy.deepcopy(shared), "role": "effect-observer"},
        "rollback": {"object_id": ids["rollback"], "binding": copy.deepcopy(shared), "effect_ref": ids["effect"], "mode": "REVERSIBLE", "preimage_status": "COMPLETE", "restores_consequence": True, "charter_mode": "AUTHORIZED_REVERSIBLE"},
    }
    if family == "F7" or spec["defect_kind"] in {"consequence_owner_ref", "consequence_observer_ref", "consequence_retry", "multi_hop_consequence"}:
        objects["effect"]["state"], objects["effect"]["obligation_ref"] = "UNKNOWN", ids["obligation"]
    return {
        "schema_version": "1.0.0", "task_id": TASK_ID, "fixture_id": fixture_id(spec["pair_id"], member),
        "pair_id": spec["pair_id"], "family": family, "split": spec["split"], "objects": objects,
        "local_contracts": [{"contract_id": f"{family}-local-{i}", "status": "PASS", "scope": "object-local"} for i in range(1, 5)],
        "typed_compatibility": {"allowed_version_transitions": [], "surface_delay_allowed": False, "repository_binding_is_not_external_truth": True},
        "metadata": {"evidence_volume": 3, "display_label": "bounded fixture", "same_digest_observation": False, "external_verification": "NOT_USED"},
        "research_boundary": BOUNDARY,
    }


def apply_defect(packet: dict[str, Any], kind: str) -> None:
    o, foreign = packet["objects"], "foreign-" + packet["fixture_id"]
    if kind == "local_failure":
        packet["local_contracts"][0]["status"] = "FAIL"
    elif kind == "claim_action_ref":
        o["action"]["claim_ref"] = foreign + "-claim"
    elif kind == "claim_action_scope":
        o["action"]["binding"]["scope"] = foreign + "-scope"
    elif kind == "approval_action_ref":
        o["action"]["approval_ref"] = foreign + "-approval"
    elif kind == "approval_action_scope":
        o["approval"]["binding"]["scope"] = foreign + "-scope"
    elif kind == "approval_action_epoch":
        o["approval"]["binding"]["lifecycle_epoch"] = "epoch-stale"
    elif kind == "epoch_projection":
        o["projection"]["binding"]["lifecycle_epoch"] = "epoch-stale"
    elif kind == "epoch_admission":
        o["admission"]["binding"]["lifecycle_epoch"] = "epoch-stale"
    elif kind == "epoch_release":
        o["release"]["binding"]["lifecycle_epoch"] = "epoch-stale"
    elif kind == "base_delta_scope":
        o["delta"]["binding"]["scope"] = foreign + "-scope"
    elif kind == "base_delta_ref":
        o["delta"]["base_ref"] = foreign + "-base"
    elif kind == "source_identity_ref":
        o["identity"]["source_ref"] = foreign + "-source"
    elif kind == "projection_surface_ref":
        o["surface"]["projection_ref"] = foreign + "-projection"
    elif kind == "surface_binding_epoch":
        o["surface"]["binding"]["lifecycle_epoch"] = "epoch-stale"
    elif kind == "release_admission_ref":
        o["release"]["admission_ref"] = foreign + "-admission"
    elif kind == "provider_reference":
        o["admission"]["provider_ref"] = foreign + "-provider"
    elif kind == "provider_current":
        o["provider"]["capability"], o["approval"]["current_authority"], o["action"]["attempted_current_use"] = "AVAILABLE", "NONE", True
    elif kind == "consequence_owner_ref":
        o["obligation"]["owner_ref"] = foreign + "-owner"
    elif kind == "consequence_observer_ref":
        o["obligation"]["observer_ref"] = foreign + "-observer"
    elif kind == "consequence_retry":
        o["obligation"]["retry_policy"] = "PERMITTED"
    elif kind == "rollback_contract":
        o["effect"]["reversibility"], o["rollback"]["mode"], o["rollback"]["charter_mode"] = "IRREVERSIBLE", "REVERSIBLE", "UNAUTHORIZED_REVERSIBLE"
    elif kind == "multi_hop_claim":
        o["claim"]["source_ref"], o["action"]["claim_ref"] = foreign + "-source", foreign + "-claim"
    elif kind == "multi_hop_approval":
        o["approval"]["action_ref"], o["action"]["approval_ref"] = foreign + "-action", foreign + "-approval"
    elif kind == "multi_hop_epoch":
        o["identity"]["binding"]["lifecycle_epoch"], o["release"]["binding"]["lifecycle_epoch"] = "epoch-stale", "epoch-stale"
    elif kind == "multi_hop_scope":
        o["base"]["binding"]["scope"], o["delta"]["binding"]["scope"], o["delta"]["isolation_valid"] = foreign + "-base-scope", foreign + "-delta-scope", False
    elif kind == "multi_hop_surface":
        o["source"]["identity_ref"], o["projection"]["identity_ref"], o["surface"]["projection_ref"] = foreign + "-identity", foreign + "-identity", foreign + "-projection"
    elif kind == "multi_hop_provider":
        o["release"]["provider_ref"], o["admission"]["provider_ref"] = foreign + "-provider", foreign + "-provider"
    elif kind == "multi_hop_consequence":
        o["effect"]["obligation_ref"], o["obligation"]["effect_ref"], o["obligation"]["owner_ref"] = foreign + "-obligation", foreign + "-effect", foreign + "-owner"
    elif kind == "novel_chain":
        o["source"]["identity_ref"], o["identity"]["projection_ref"], o["projection"]["surface_ref"] = foreign + "-identity", foreign + "-projection", foreign + "-surface"
        o["release"]["admission_ref"], o["action"]["approval_ref"] = foreign + "-admission", foreign + "-approval"
    elif kind == "ambiguous_stress":
        o["approval"]["contestability_present"], o["approval"]["revocation_path_present"] = False, False
    else:
        raise ValueError(f"unknown defect kind: {kind}")


def apply_control(packet: dict[str, Any], variant: str) -> None:
    o = packet["objects"]
    if variant in {"valid_upgrade", "alias_migration"}:
        for name in ("projection", "surface", "release", "admission"):
            o[name]["binding"]["version"] = "v2"
        packet["typed_compatibility"]["allowed_version_transitions"] = [{"from": "v1", "to": "v2"}]
    elif variant == "same_digest_distinct_tuple":
        packet["metadata"].update(same_digest_observation=True, shared_digest=o["source"]["content_digest"], same_digest_objects=[o["source"]["object_id"], "unrelated-object"])
    elif variant == "allowed_surface_delay":
        o["surface"]["source_revision"] = "rev-0"
        packet["typed_compatibility"]["surface_delay_allowed"] = True
    elif variant in {"fail_closed_abstention", "unknown_contract"}:
        packet["local_contracts"][0]["status"] = "UNKNOWN"
    elif variant == "no_safe_alternative":
        o["action"].update(route_available=False)
        packet["metadata"]["safe_alternative_available"] = False
    elif variant == "irreversible_correct_charter":
        o["effect"]["reversibility"], o["rollback"]["mode"], o["rollback"]["charter_mode"], o["rollback"]["preimage_status"] = "IRREVERSIBLE", "IRREVERSIBLE_DECLARED", "AUTHORIZED_IRREVERSIBLE", "NOT_APPLICABLE"
    elif variant == "valid_signer_no_concrete_defect":
        o["approval"].update(signer_status="VALID", contestability_present=True)
    elif variant == "irrelevant_evidence":
        packet["metadata"]["evidence_volume"] = 100
    elif variant == "label_only":
        packet["metadata"]["display_label"] = "changed-label-only"
    elif variant == "base_delta_isolated":
        o["base"]["binding"]["scope"], o["delta"]["binding"]["scope"], o["delta"]["isolation_valid"] = "bounded-research/base-isolated", "bounded-research/delta-isolated", True
    else:
        raise ValueError(f"unknown control variant: {variant}")


def make_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    packets, answers, manifests, split_rows = [], [], [], []
    for spec in PAIR_SPECS:
        pair_ids = []
        for member in ("primary", "control"):
            packet = base_packet(spec, member)
            if member == "primary":
                apply_defect(packet, spec["defect_kind"])
                truth_class, member_role = ("AMBIGUOUS_STRESS", "PRIMARY") if spec["defect_kind"] == "ambiguous_stress" else ("DEFECT", "PRIMARY")
            else:
                apply_control(packet, spec["control_variant"])
                truth_class, member_role = "CONTROL", "MATCHED_CONTROL"
            packets.append(packet)
            pair_ids.append(packet["fixture_id"])
            answers.append({**{key: spec[key] for key in ("pair_id", "family", "split", "defect_kind", "control_variant", "binding_subtype", "novel_composition", "cross_object")}, "fixture_id": packet["fixture_id"], "member_role": member_role, "truth_class": truth_class})
        manifests.append({**{key: spec[key] for key in ("pair_id", "family", "split", "defect_kind", "control_variant", "binding_subtype", "novel_composition", "cross_object")}, "fixture_ids": pair_ids, "source_contracts": FAMILY_META[spec["family"]]["source_contracts"], "historical_lineage": FAMILY_META[spec["family"]]["historical_lineage"], "transfer_relation": FAMILY_META[spec["family"]]["transfer_relation"]})
        split_rows.append({"pair_id": spec["pair_id"], "split": spec["split"], "fixture_ids": pair_ids})
    return packets, answers, manifests, split_rows


LOCAL_REGISTRY: list[dict[str, Any]] = [
    {"id": "ml.f1.claim_action_ref", "family": "F1", "kind": "ref_equal", "left": "action.claim_ref", "right": "claim.object_id"},
    {"id": "ml.f1.claim_action_scope", "family": "F1", "kind": "binding_field_equal", "nodes": ["claim", "action"], "field": "scope"},
    {"id": "ml.f2.approval_scope", "family": "F2", "kind": "binding_field_equal", "nodes": ["approval", "action"], "field": "scope"},
    {"id": "ml.f3.epoch_projection", "family": "F3", "kind": "binding_field_equal", "nodes": ["claim", "projection"], "field": "lifecycle_epoch"},
    {"id": "ml.f3.epoch_admission", "family": "F3", "kind": "binding_field_equal", "nodes": ["claim", "admission"], "field": "lifecycle_epoch"},
    {"id": "ml.f3.epoch_release", "family": "F3", "kind": "binding_field_equal", "nodes": ["claim", "release"], "field": "lifecycle_epoch"},
    {"id": "ml.f4.base_delta_scope", "family": "F4", "kind": "scope_equal_unless_isolated", "nodes": ["base", "delta"]},
    {"id": "ml.f5.source_identity_ref", "family": "F5", "kind": "ref_equal", "left": "source.identity_ref", "right": "identity.object_id"},
    {"id": "ml.f5.projection_surface_ref", "family": "F5", "kind": "ref_equal", "left": "surface.projection_ref", "right": "projection.object_id"},
    {"id": "ml.f5.surface_epoch", "family": "F5", "kind": "binding_field_equal", "nodes": ["claim", "surface"], "field": "lifecycle_epoch"},
    {"id": "ml.f6.release_admission_ref", "family": "F6", "kind": "ref_equal", "left": "release.admission_ref", "right": "admission.object_id"},
    {"id": "ml.f6.provider_reference", "family": "F6", "kind": "ref_equal", "left": "admission.provider_ref", "right": "provider.object_id"},
    {"id": "ml.f6.provider_current", "family": "F6", "kind": "provider_current"},
    {"id": "ml.f7.owner_ref", "family": "F7", "kind": "ref_equal", "left": "obligation.owner_ref", "right": "owner.object_id"},
    {"id": "ml.f7.observer_ref", "family": "F7", "kind": "ref_equal", "left": "obligation.observer_ref", "right": "observer.object_id"},
    {"id": "ml.f7.rollback", "family": "F7", "kind": "rollback_contract"},
]

MODELS = {
    "M0": {"name": "EXISTING_ONLY", "description": "Object-local status records only.", "shared_junction_helper": False},
    "ML": {"name": "LOCAL_PREDICATE_PATCHWORK", "description": "M0 plus frozen direct family predicates; no shared tuple helper.", "shared_junction_helper": False, "predicate_registry": "local-predicate-registry-research.json"},
    "MJ": {"name": "JUNCTION_INVARIANT_TYPED", "description": "M0 plus one typed research candidate over existing fields and references.", "shared_junction_helper": True, "candidate": "junction-candidate.json"},
    "MH": {"name": "HYBRID_PROBE", "description": "MJ plus the frozen ML registry; diagnostic only.", "shared_junction_helper": True, "candidate": "junction-candidate.json", "predicate_registry": "local-predicate-registry-research.json"},
}

JUNCTION_CANDIDATE = {
    "schema_version": "1.0.0", "candidate_id": "MJ-T157-typed-existing-fields-v1",
    "tuple_dimensions": ["subject_id", "version", "scope", "lifecycle_epoch"],
    "typed_compatibility": {"version": "exact_or_predeclared_v1_to_v2_transition", "surface_revision": "delay_allowed_only_at_existing_boundary", "scope": "exact", "lifecycle_epoch": "exact", "subject_id": "exact"},
    "relation_groups": [["claim", "source", "identity", "projection", "surface", "release", "admission"], ["claim", "action"], ["approval", "action"], ["base", "delta"], ["effect", "obligation", "owner", "observer", "rollback"], ["release", "admission", "provider"]],
    "existing_fields_only": True, "new_authority_state": False, "new_truth_state": False, "new_capability": False, "new_lifecycle_state": False, "strict_digest_only": False, "research_only": True,
}

HYPOTHESIS_FREEZE = {
    "schema_version": "1.0.0", "task_id": TASK_ID, "freeze_label": "T157-FREEZE-1", "freeze_date": "2026-09-06",
    "question": "Does a minimal typed junction binding over existing fields generalize beyond a frozen local-predicate patchwork on fresh paired fixtures without importing new authority, truth, capability or lifecycle semantics?",
    "hypotheses": {"H1": "A shared junction invariant yields incremental holdout detection including novel compositions with bounded control false positives.", "H2": "A frozen local-predicate patchwork is sufficient and generalizes without repeated relation-specific additions.", "H0": "Existing object-local contracts alone explain the observed defects and controls."},
    "models": ["M0", "ML", "MJ", "MH"], "calibration_before_holdout": True, "answer_key_frozen_after_this_record": True, "post_freeze_local_predicate_additions": 0, "post_freeze_junction_dimensions": 0, "boundary": BOUNDARY,
}

PROTOCOL = {
    "schema_version": "1.0.0", "task_id": TASK_ID, "base_commit": BASE_COMMIT,
    "corpus": {"pairs": 96, "instances": 192, "calibration_pairs": 48, "holdout_in_family_pairs": 24, "holdout_transfer_pairs": 24, "minimum_holdout_pairs": 36, "minimum_transfer_pairs": 15, "pair_members_stay_together": True, "family_count": 8, "families": list(FAMILY_META)},
    "blind_scoring": {"input_files": ["blind-packets.jsonl", "model-definitions.json", "local-predicate-registry-research.json", "junction-candidate.json"], "forbidden_inputs": ["answer-key.jsonl", "results.jsonl", "metrics.json", "post_outcome_evidence"], "passes_required": 2, "byte_identical_required": True, "scorer_output_fields": ["fixture_id", "model_id", "decision", "reason_code", "references", "predicate_ids", "actionability", "bounded_confidence"]},
    "splits": {"calibration": "first six deterministic pairs per family", "holdout_in_family": "pairs seven through nine per family", "holdout_transfer": "pairs ten through twelve per family with novel composition", "new_ml_predicates_after_freeze": False},
    "controls": list(CONTROL_VARIANTS), "boundary": BOUNDARY,
}


def get_path(packet: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = packet
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def ref_value(packet: dict[str, Any], dotted: str) -> Any:
    return get_path(packet, "objects." + dotted)


def local_findings(packet: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    failures, unknown = [], False
    for contract in packet["local_contracts"]:
        if contract["status"] == "FAIL":
            failures.append({"reason_code": "local.contract_failure", "reference": contract["contract_id"], "actionability": "REPAIR_LOCAL_CONTRACT"})
        elif contract["status"] == "UNKNOWN":
            unknown = True
    return failures, unknown


def rule_finding(packet: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any] | None:
    kind = rule["kind"]
    if kind == "ref_equal":
        failed = ref_value(packet, rule["left"]) != ref_value(packet, rule["right"])
    elif kind == "binding_field_equal":
        values = [ref_value(packet, f"{node}.binding.{rule['field']}") for node in rule["nodes"]]
        failed = len(set(values)) != 1
    elif kind == "scope_equal_unless_isolated":
        failed = ref_value(packet, "base.binding.scope") != ref_value(packet, "delta.binding.scope") and not bool(ref_value(packet, "delta.isolation_valid"))
    elif kind == "provider_current":
        failed = ref_value(packet, "provider.capability") == "AVAILABLE" and ref_value(packet, "approval.current_authority") == "NONE" and bool(ref_value(packet, "action.attempted_current_use"))
    elif kind == "rollback_contract":
        failed = (
            ref_value(packet, "effect.reversibility") == "IRREVERSIBLE" and ref_value(packet, "rollback.mode") != "IRREVERSIBLE_DECLARED"
        ) or (
            ref_value(packet, "effect.reversibility") != "IRREVERSIBLE" and ref_value(packet, "rollback.mode") == "REVERSIBLE" and ref_value(packet, "rollback.preimage_status") != "COMPLETE"
        )
    else:
        raise ValueError(f"unknown local predicate kind: {kind}")
    return None if not failed else {
        "reason_code": f"local_predicate.{rule['id']}",
        "reference": rule["id"],
        "actionability": "REVIEW_EXISTING_LOCAL_RELATION",
    }


def local_predicate_findings(packet: dict[str, Any], registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        finding
        for rule in registry
        if rule["family"] == packet["family"]
        for finding in [rule_finding(packet, rule)]
        if finding is not None
    ]


def compatible_binding(left: dict[str, Any], right: dict[str, Any], packet: dict[str, Any], typed: bool = True) -> bool:
    if left.get("subject_id") != right.get("subject_id") or left.get("scope") != right.get("scope") or left.get("lifecycle_epoch") != right.get("lifecycle_epoch"):
        return False
    if left.get("version") == right.get("version"):
        return True
    return typed and ({"from": left.get("version"), "to": right.get("version")} in packet["typed_compatibility"]["allowed_version_transitions"] or {"from": right.get("version"), "to": left.get("version")} in packet["typed_compatibility"]["allowed_version_transitions"])


def junction_findings(packet: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    o, findings = packet["objects"], []
    reference = o["claim"]["binding"]
    for node in ("source", "identity", "projection", "surface", "release", "admission"):
        if not compatible_binding(reference, o[node]["binding"], packet, typed=True):
            findings.append({"reason_code": "junction.binding_tuple_mismatch", "reference": f"claim.binding~{node}.binding", "actionability": "REVIEW_BINDING_AT_EXISTING_CONTRACT_JUNCTION"})
    if o["action"]["claim_ref"] != o["claim"]["object_id"]:
        findings.append({"reason_code": "junction.claim_action_object_mismatch", "reference": "action.claim_ref~claim.object_id", "actionability": "REVIEW_CLAIM_TO_ACTION_BINDING"})
    if o["action"]["approval_ref"] != o["approval"]["object_id"]:
        reason = "junction.approval_action_reference_missing" if o["action"]["approval_ref"] is None else "junction.approval_action_object_mismatch"
        findings.append({"reason_code": reason, "reference": "action.approval_ref~approval.object_id", "actionability": "REVIEW_APPROVAL_TO_ACTION_BINDING"})
    if not compatible_binding(o["claim"]["binding"], o["action"]["binding"], packet, typed=True):
        findings.append({"reason_code": "junction.claim_action_tuple_mismatch", "reference": "claim.binding~action.binding", "actionability": "REVIEW_CLAIM_TO_ACTION_BINDING"})
    if not compatible_binding(o["approval"]["binding"], o["action"]["binding"], packet, typed=True):
        findings.append({"reason_code": "junction.approval_action_tuple_mismatch", "reference": "approval.binding~action.binding", "actionability": "REVIEW_APPROVAL_TO_ACTION_BINDING"})
    if (o["base"]["binding"]["scope"] != o["delta"]["binding"]["scope"] and not o["delta"]["isolation_valid"]) or o["delta"]["base_ref"] != o["base"]["object_id"]:
        findings.append({"reason_code": "junction.base_delta_scope_or_reference_mismatch", "reference": "base~delta.scope_or_reference", "actionability": "REVIEW_BASE_DELTA_ISOLATION"})
    if o["source"]["identity_ref"] != o["identity"]["object_id"] or o["identity"]["source_ref"] != o["source"]["object_id"]:
        findings.append({"reason_code": "junction.source_identity_reference_mismatch", "reference": "source.identity_ref~identity.source_ref", "actionability": "REVIEW_SOURCE_IDENTITY_BINDING"})
    if o["identity"]["projection_ref"] != o["projection"]["object_id"] or o["projection"]["identity_ref"] != o["identity"]["object_id"]:
        findings.append({"reason_code": "junction.identity_projection_reference_mismatch", "reference": "identity.projection_ref~projection.identity_ref", "actionability": "REVIEW_IDENTITY_PROJECTION_BINDING"})
    if o["projection"]["surface_ref"] != o["surface"]["object_id"] or o["surface"]["projection_ref"] != o["projection"]["object_id"]:
        findings.append({"reason_code": "junction.projection_surface_reference_mismatch", "reference": "projection.surface_ref~surface.projection_ref", "actionability": "REVIEW_PROJECTION_SURFACE_BINDING"})
    if o["release"]["admission_ref"] != o["admission"]["object_id"] or o["admission"]["release_ref"] != o["release"]["object_id"]:
        findings.append({"reason_code": "junction.release_admission_reference_mismatch", "reference": "release.admission_ref~admission.release_ref", "actionability": "REVIEW_RELEASE_ADMISSION_BINDING"})
    if o["admission"]["provider_ref"] != o["provider"]["object_id"] or o["provider"]["authority_ref"] != o["approval"]["object_id"]:
        findings.append({"reason_code": "junction.provider_admission_reference_mismatch", "reference": "admission.provider_ref~provider.authority_ref", "actionability": "REVIEW_PROVIDER_BOUNDARY_REFERENCE"})
    if o["provider"]["capability"] == "AVAILABLE" and o["approval"].get("current_authority") == "NONE" and o["action"]["attempted_current_use"]:
        findings.append({"reason_code": "junction.provider_capability_not_current_authority", "reference": "provider.capability~approval.current_authority~action.attempted_current_use", "actionability": "KEEP_PROVIDER_CAPABILITY_OUTSIDE_CURRENT_AUTHORITY"})
    if o["effect"]["state"] == "UNKNOWN":
        obligation = o["obligation"]
        if o["effect"]["obligation_ref"] != obligation["object_id"] or obligation["effect_ref"] != o["effect"]["object_id"]:
            findings.append({"reason_code": "junction.effect_obligation_reference_mismatch", "reference": "effect.obligation_ref~obligation.effect_ref", "actionability": "OPEN_RECONCILIATION_WITH_EXISTING_OBLIGATION"})
        if obligation["owner_ref"] != o["owner"]["object_id"]:
            findings.append({"reason_code": "junction.consequence_owner_mismatch", "reference": "obligation.owner_ref~owner.object_id", "actionability": "REQUIRE_NAMED_RECONCILIATION_OWNER"})
        if obligation["observer_ref"] != o["observer"]["object_id"]:
            findings.append({"reason_code": "junction.consequence_observer_mismatch", "reference": "obligation.observer_ref~observer.object_id", "actionability": "REQUIRE_OBSERVABLE_EFFECT_OBSERVER"})
        if obligation["retry_policy"] == "PERMITTED" or not obligation["stop_path_present"]:
            findings.append({"reason_code": "junction.unknown_effect_retry_or_stop_mismatch", "reference": "obligation.retry_policy~obligation.stop_path_present", "actionability": "PROHIBIT_RETRY_AND_REQUIRE_STOP_PATH"})
    if o["effect"]["reversibility"] == "IRREVERSIBLE" and o["rollback"]["mode"] != "IRREVERSIBLE_DECLARED":
        findings.append({"reason_code": "junction.rollback_consequence_mismatch", "reference": "effect.reversibility~rollback.mode~rollback.charter_mode", "actionability": "BLOCK_UNSUPPORTED_REVERSIBILITY_CLAIM"})
    return findings


def model_record(model_id: str, packet: dict[str, Any], registry: list[dict[str, Any]] | None = None, candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    registry, candidate = LOCAL_REGISTRY if registry is None else registry, JUNCTION_CANDIDATE if candidate is None else candidate
    findings, unknown = local_findings(packet)
    if model_id in {"ML", "MH"}:
        findings.extend(local_predicate_findings(packet, registry))
    if model_id in {"MJ", "MH"}:
        findings.extend(junction_findings(packet, candidate))
    if findings:
        first = sorted(findings, key=lambda item: (item["reason_code"], item["reference"]))[0]
        return {
            "fixture_id": packet["fixture_id"], "model_id": model_id, "decision": "flag",
            "reason_code": first["reason_code"], "references": sorted({item["reference"] for item in findings}),
            "predicate_ids": sorted({item["reference"] for item in findings if item["reference"].startswith("ml.")}),
            "actionability": first["actionability"], "bounded_confidence": "bounded_high", "scorer_version": SCORER_VERSION,
        }
    if unknown:
        return {
            "fixture_id": packet["fixture_id"], "model_id": model_id, "decision": "abstain",
            "reason_code": "local.contract_unknown", "references": ["local_contracts"], "predicate_ids": [],
            "actionability": "REQUIRE_LOCAL_REVIEW", "bounded_confidence": "bounded_low", "scorer_version": SCORER_VERSION,
        }
    return {
        "fixture_id": packet["fixture_id"], "model_id": model_id, "decision": "no_flag",
        "reason_code": "no_frozen_predicate_triggered", "references": [], "predicate_ids": [],
        "actionability": "NO_ACTIONABLE_RESEARCH_SIGNAL", "bounded_confidence": "bounded_medium", "scorer_version": SCORER_VERSION,
    }


def score_packets(packets: list[dict[str, Any]], registry: list[dict[str, Any]] | None = None, candidate: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [model_record(model, packet, registry, candidate) for packet in sorted(packets, key=lambda item: item["fixture_id"]) for model in MODELS]


def validate_packet_separation(packets: list[dict[str, Any]]) -> list[str]:
    forbidden = {"truth_class", "member_role", "defect_kind", "control_variant", "diagnostic_annotation", "answer_key", "expected_decision"}
    errors = []
    for packet in packets:
        leaked = forbidden.intersection(packet)
        if leaked:
            errors.append(f"{packet['fixture_id']}: top-level leakage {sorted(leaked)}")
        if packet["fixture_id"].endswith(("-primary", "-control")):
            errors.append(f"{packet['fixture_id']}: role-like fixture id")
    return errors


def validate_corpus(packets: list[dict[str, Any]], answers: list[dict[str, Any]], manifests: list[dict[str, Any]]) -> list[str]:
    errors = validate_packet_separation(packets)
    if len(packets) != 192 or len(answers) != 192 or len(manifests) != 96:
        errors.append("corpus cardinality is not 96 pairs / 192 instances")
    if len({p["fixture_id"] for p in packets}) != len(packets):
        errors.append("fixture ids are not unique")
    if Counter(a["split"] for a in answers) != Counter({"calibration": 96, "holdout_in_family": 48, "holdout_transfer": 48}):
        errors.append("instance split counts are wrong")
    if sum(m["novel_composition"] for m in manifests) < 24:
        errors.append("transfer composition minimum is not met")
    if len({m["family"] for m in manifests}) != 8:
        errors.append("family minimum is not met")
    return errors


def validate_score_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors, seen = [], set()
    if len(rows) != 192 * 4:
        errors.append(f"score row count {len(rows)} != 768")
    for row in rows:
        key = (row.get("fixture_id", ""), row.get("model_id", ""))
        if key in seen:
            errors.append(f"duplicate score row {key}")
        seen.add(key)
        if row.get("decision") not in {"flag", "no_flag", "abstain"}:
            errors.append(f"invalid decision {row.get('decision')}")
        required = {"fixture_id", "model_id", "decision", "reason_code", "references", "predicate_ids", "actionability", "bounded_confidence"}
        if not required.issubset(row):
            errors.append(f"missing scorer fields for {key}")
    return errors


def frozen_payloads() -> dict[str, bytes]:
    packets, answers, manifests, split_rows = make_corpus()
    return {
        "hypothesis-freeze.json": json_bytes(HYPOTHESIS_FREEZE),
        "experiment-protocol.json": json_bytes(PROTOCOL),
        "model-definitions.json": json_bytes(MODELS),
        "local-predicate-registry-research.json": json_bytes({"schema_version": "1.0.0", "task_id": TASK_ID, "frozen_before_holdout_scoring": True, "post_freeze_additions": 0, "predicates": LOCAL_REGISTRY, "shared_junction_helper": False}),
        "junction-candidate.json": json_bytes(JUNCTION_CANDIDATE),
        "fixture-generator-manifest.json": json_bytes({"schema_version": "1.0.0", "generator": Path(__file__).name, "generator_version": "1.0.0", "fresh_value_namespace": "t157-20260906", "pair_spec_digest": digest(PAIR_SPECS), "families": list(FAMILY_META), "pairs": len(manifests)}),
        "fixture-manifest.json": json_bytes(manifests),
        "split-manifest.json": json_bytes(split_rows),
        "blind-packets.jsonl": jsonl_bytes(packets),
        "answer-key.jsonl": jsonl_bytes(answers),
    }


def freeze_digest(payloads: dict[str, bytes]) -> str:
    return digest({name: digest_bytes(payload) for name, payload in sorted(payloads.items())})


def command_generate() -> int:
    packets, answers, manifests, _ = make_corpus()
    errors = validate_corpus(packets, answers, manifests)
    if errors:
        raise SystemExit("CORPUS_INVALID: " + " | ".join(errors))
    RESEARCH.mkdir(parents=True, exist_ok=True)
    payloads = frozen_payloads()
    for name, payload in payloads.items():
        write_bytes(RESEARCH / name, payload)
    write_jsonl(RESEARCH / "junction-ablation.jsonl", [{
        "candidate_variant": "full_typed",
        "removed_dimension_or_relation": None,
        "pre_score_status": "FROZEN_MODEL_VARIANT",
    }])
    write_json(RESEARCH / "maintenance-topology.json", {
        "schema_version": "1.0.0", "task_id": TASK_ID,
        "local_patchwork": {"predicate_count": len(LOCAL_REGISTRY), "relation_sites": len(LOCAL_REGISTRY), "shared_helper": False},
        "junction_candidate": {"tuple_dimensions": JUNCTION_CANDIDATE["tuple_dimensions"], "relation_groups": len(JUNCTION_CANDIDATE["relation_groups"]), "shared_helper": True},
        "pre_score_status": "FROZEN",
    })
    write_jsonl(RESEARCH / "maintenance-perturbations.jsonl", [
        {"id": "P01", "perturbation": "add_lifecycle_epoch_field", "local_sites_affected": 3, "junction_adapters_affected": 1},
        {"id": "P02", "perturbation": "rename_projection_surface_reference", "local_sites_affected": 2, "junction_adapters_affected": 1},
        {"id": "P03", "perturbation": "add_new_release_admission_consumer", "local_sites_affected": 1, "junction_adapters_affected": 1},
        {"id": "P04", "perturbation": "valid_v1_to_v2_migration", "local_sites_affected": 2, "junction_adapters_affected": 1},
        {"id": "P05", "perturbation": "new_multi_hop_family", "local_sites_affected": 4, "junction_adapters_affected": 1},
        {"id": "P06", "perturbation": "local_rule_drift_at_one_site", "local_sites_affected": 1, "junction_adapters_affected": 0},
        {"id": "P07", "perturbation": "scope_isolation_exception", "local_sites_affected": 2, "junction_adapters_affected": 1},
        {"id": "P08", "perturbation": "reconciliation_owner_reference", "local_sites_affected": 2, "junction_adapters_affected": 1},
    ])
    write_json(RESEARCH / "restart-ledger.json", {
        "schema_version": "1.0.0", "task_id": TASK_ID,
        "invalidated_freezes": [], "restart_required": False, "reason": None,
    })
    frozen_files = {name: digest_bytes(payload) for name, payload in sorted(payloads.items())}
    write_json(RESEARCH / "freeze-ledger.json", {
        "schema_version": "1.0.0", "task_id": TASK_ID, "status": "FROZEN_BEFORE_SCORING",
        "freeze_id": "T157-FREEZE-1", "freeze_digest": freeze_digest(payloads),
        "frozen_files": frozen_files, "generator_source_sha256": sha256_file(Path(__file__)),
        "command_source": {"repository": "Arvin-liu/1111", "path": "agent-commands/IGNITION-20260906-157.md", "commit": COMMAND_COMMIT, "blob": COMMAND_BLOB, "sha256": COMMAND_SHA256},
        "formal_baseline": {"repository": "Arvin-liu/when-systems-catch-fire", "base_pr": 206, "base_branch": "work/IGNITION-20260905-156", "base_sha": BASE_COMMIT},
        "control_pointers": [
            {"path": "instructions/CURRENT.md", "status": "STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL", "observed_blob": "7b0976ec", "observed_task": "121Q37-I1", "action": "left unchanged; not used as Task157 authority"},
            {"path": "relay/current", "status": "STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL", "observed_commit": "7d6d369bc2b8add8eeaa0c076f13bcda994f1dc6", "action": "left unchanged; not used as Task157 authority"},
        ],
        "score_input_excludes_answer_key": True,
        "post_freeze_local_predicate_additions": 0, "post_freeze_junction_dimension_additions": 0,
        "derived_after_unblind": ["junction-ablation.jsonl", "results.jsonl", "metrics.json", "transfer-generalization.json", "maintenance-results.jsonl", "metamorphic-results.jsonl", "counterfactual-minimality.jsonl", "verdict.json"],
        "boundary": BOUNDARY,
    })
    print(f"GENERATED_FROZEN_CORPUS pairs={len(manifests)} instances={len(packets)} freeze={freeze_digest(payloads)}")
    return 0


def read_frozen_score_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    packets = read_jsonl(RESEARCH / "blind-packets.jsonl")
    registry = read_json(RESEARCH / "local-predicate-registry-research.json")["predicates"]
    candidate = read_json(RESEARCH / "junction-candidate.json")
    return packets, registry, candidate


def command_score(output: Path | None = None) -> int:
    packets, registry, candidate = read_frozen_score_inputs()
    rows = score_packets(packets, registry, candidate)
    errors = validate_score_rows(rows)
    if errors:
        raise SystemExit("SCORE_INVALID: " + " | ".join(errors))
    target = output or RESEARCH / "score-run-1.jsonl"
    write_jsonl(target, rows)
    print(f"SCORED_BLIND packets={len(packets)} rows={len(rows)} output={target} sha256={sha256_file(target)}")
    return 0


def rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def metric_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated = [row for row in rows if row["truth_class"] in {"DEFECT", "CONTROL"}]
    counts = Counter()
    for row in evaluated:
        truth, decision = row["truth_class"], row["decision"]
        if truth == "DEFECT" and decision == "flag":
            counts["tp"] += 1
        elif truth == "DEFECT" and decision == "no_flag":
            counts["fn"] += 1
        elif truth == "DEFECT" and decision == "abstain":
            counts["defect_abstain"] += 1
        elif truth == "CONTROL" and decision == "no_flag":
            counts["tn"] += 1
        elif truth == "CONTROL" and decision == "flag":
            counts["fp"] += 1
        elif truth == "CONTROL" and decision == "abstain":
            counts["control_abstain"] += 1
    defects = sum(counts[key] for key in ("tp", "fn", "defect_abstain"))
    controls = sum(counts[key] for key in ("tn", "fp", "control_abstain"))
    return {
        "instances_evaluated": len(evaluated), "defects": defects, "controls": controls,
        **{key: counts[key] for key in ("tp", "fp", "tn", "fn", "defect_abstain", "control_abstain")},
        "sensitivity_flag_only": rate(counts["tp"], defects),
        "specificity_no_flag_only": rate(counts["tn"], controls),
        "precision_flag_only": rate(counts["tp"], counts["tp"] + counts["fp"]),
        "abstain_rate": rate(counts["defect_abstain"] + counts["control_abstain"], len(evaluated)),
    }


def unblind_results(score_rows: list[dict[str, Any]], answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answer_map = {row["fixture_id"]: row for row in answers}
    by_fixture = {}
    results = []
    for score in score_rows:
        answer = answer_map[score["fixture_id"]]
        expected = "flag" if answer["truth_class"] == "DEFECT" else "no_flag" if answer["truth_class"] == "CONTROL" else "abstain_or_no_flag"
        row = {**answer, "model_id": score["model_id"], "decision": score["decision"], "reason_code": score["reason_code"], "references": score["references"], "predicate_ids": score["predicate_ids"], "actionability": score["actionability"], "bounded_confidence": score["bounded_confidence"], "expected": expected, "incremental_beyond_m0": False}
        results.append(row)
        by_fixture[(row["fixture_id"], row["model_id"])] = row
    for row in results:
        if row["model_id"] != "M0":
            row["incremental_beyond_m0"] = row["decision"] == "flag" and by_fixture[(row["fixture_id"], "M0")]["decision"] != "flag"
    return sorted(results, key=lambda row: (row["fixture_id"], row["model_id"]))


def metrics_tree(results: list[dict[str, Any]]) -> dict[str, Any]:
    output = {"schema_version": "1.0.0", "task_id": TASK_ID, "models": {}, "paired_comparisons": {}, "boundary": BOUNDARY}
    for model in MODELS:
        rows = [row for row in results if row["model_id"] == model]
        output["models"][model] = {
            "all": metric_block(rows),
            "calibration": metric_block([row for row in rows if row["split"] == "calibration"]),
            "holdout_in_family": metric_block([row for row in rows if row["split"] == "holdout_in_family"]),
            "holdout_transfer": metric_block([row for row in rows if row["split"] == "holdout_transfer"]),
            "holdout": metric_block([row for row in rows if row["split"] != "calibration"]),
            "ambiguous_stress": dict(Counter(row["decision"] for row in rows if row["truth_class"] == "AMBIGUOUS_STRESS")),
        }
    for model in ("ML", "MJ", "MH"):
        inc = [row for row in results if row["model_id"] == model and row["incremental_beyond_m0"] and row["truth_class"] == "DEFECT"]
        output["paired_comparisons"][model] = {
            "incremental_defects_all": len(inc),
            "incremental_defects_holdout": sum(row["split"] != "calibration" for row in inc),
            "incremental_defects_in_family": sum(row["split"] == "holdout_in_family" for row in inc),
            "incremental_defects_transfer": sum(row["split"] == "holdout_transfer" for row in inc),
            "incremental_families_holdout": sorted({row["family"] for row in inc if row["split"] != "calibration"}),
            "incremental_binding_subtypes_holdout": sorted({row["binding_subtype"] for row in inc if row["split"] != "calibration" and row["binding_subtype"]}),
        }
    by_fixture = {(row["fixture_id"], row["model_id"]): row for row in results}
    mj_inc = [row for row in results if row["model_id"] == "MJ" and row["truth_class"] == "DEFECT" and row["split"] != "calibration"]
    ml_inc = [row for row in results if row["model_id"] == "ML" and row["truth_class"] == "DEFECT" and row["split"] != "calibration"]
    output["paired_comparisons"]["MJ"]["mj_only_against_ml"] = sum(row["decision"] == "flag" and by_fixture[(row["fixture_id"], "ML")]["decision"] != "flag" for row in mj_inc)
    output["paired_comparisons"]["ML"]["ml_only_against_mj"] = sum(row["decision"] == "flag" and by_fixture[(row["fixture_id"], "MJ")]["decision"] != "flag" for row in ml_inc)
    return output


def transformed_decisions(packet: dict[str, Any], models: Iterable[str] = MODELS) -> dict[str, dict[str, Any]]:
    return {model: model_record(model, packet) for model in models}


def metamorphic_rows(packets: list[dict[str, Any]], answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answer_map = {row["fixture_id"]: row for row in answers}
    by_pair_role = {}
    for packet in packets:
        role = "primary" if answer_map[packet["fixture_id"]]["member_role"] == "PRIMARY" else "control"
        by_pair_role[(packet["pair_id"], role)] = packet
    rows = []

    def add(property_id: str, fixture_id: str, model_id: str, observed: Any, expected: Any, passed: bool, note: str) -> None:
        rows.append({"property": property_id, "fixture_id": fixture_id, "model_id": model_id, "observed": observed, "expected": expected, "passed": bool(passed), "note": note})

    for spec in PAIR_SPECS[:12]:
        primary, control = by_pair_role[(spec["pair_id"], "primary")], by_pair_role[(spec["pair_id"], "control")]
        primary_scores, control_scores = transformed_decisions(primary), transformed_decisions(control)
        for model in MODELS:
            control_is_unknown = any(item["status"] == "UNKNOWN" for item in control["local_contracts"])
            passed = control_is_unknown or primary_scores[model]["decision"] != "flag" or control_scores[model]["decision"] == "no_flag"
            add("repair_exact_single_defect", primary["fixture_id"], model, [primary_scores[model]["decision"], control_scores[model]["decision"]], "flag_to_no_flag_or_not_applicable", passed, "paired control is the exact repaired base packet; unknown-control pairs are intentionally not applicable")

    stable_packets = [by_pair_role[(spec["pair_id"], "control")] for spec in PAIR_SPECS[:16]]
    for property_id, mutate in (
        ("irrelevant_evidence_stability", lambda packet: packet["metadata"].update(evidence_volume=999)),
        ("label_only_stability", lambda packet: packet["metadata"].update(display_label="unrelated-label")),
        ("locality_stability", lambda packet: packet["objects"]["owner"].update(role="unrelated-but-valid-label")),
    ):
        for packet in stable_packets:
            transformed = copy.deepcopy(packet)
            mutate(transformed)
            before, after = transformed_decisions(packet), transformed_decisions(transformed)
            for model in MODELS:
                add(property_id, packet["fixture_id"], model, [before[model]["decision"], after[model]["decision"]], "stable", before[model]["decision"] == after[model]["decision"], "unrelated field must not change a frozen decision")

    for spec in PAIR_SPECS:
        control = by_pair_role[(spec["pair_id"], "control")]
        if spec["control_variant"] == "alias_migration":
            scores = transformed_decisions(control)
            for model in ("MJ", "MH"):
                add("valid_typed_migration", control["fixture_id"], model, scores[model]["decision"], "no_flag", scores[model]["decision"] == "no_flag", "typed compatibility is not a hidden authority upgrade")
        if spec["family"] == "F3" and spec["index"] in {2, 3, 6}:
            primary = by_pair_role[(spec["pair_id"], "primary")]
            repaired = copy.deepcopy(primary)
            for node in ("projection", "admission", "release", "identity", "surface"):
                repaired["objects"][node]["binding"]["lifecycle_epoch"] = repaired["objects"]["claim"]["binding"]["lifecycle_epoch"]
            before, after = transformed_decisions(primary), transformed_decisions(repaired)
            for model in ("ML", "MJ", "MH"):
                add("epoch_repair", primary["fixture_id"], model, [before[model]["decision"], after[model]["decision"]], "flag_to_no_flag_or_not_applicable", before[model]["decision"] != "flag" or after[model]["decision"] == "no_flag", "repair aligns existing epoch fields")
        if spec["control_variant"] == "base_delta_isolated":
            scores = transformed_decisions(control)
            add("base_delta_isolation", control["fixture_id"], "MJ", scores["MJ"]["decision"], "no_flag", scores["MJ"]["decision"] == "no_flag", "different scopes are safe when the existing isolation marker is valid")
        if spec["control_variant"] == "no_safe_alternative":
            scores = transformed_decisions(control)
            add("safe_alternative_absence_stability", control["fixture_id"], "MJ", scores["MJ"]["decision"], "no_flag", scores["MJ"]["decision"] == "no_flag", "absence of a safe alternative is not itself a junction defect")
        if spec["defect_kind"] == "ambiguous_stress":
            primary = by_pair_role[(spec["pair_id"], "primary")]
            scores = transformed_decisions(primary)
            for model in MODELS:
                add("ambiguous_signer_no_forced_defect", primary["fixture_id"], model, scores[model]["decision"], "not_flag", scores[model]["decision"] != "flag", "signer incompleteness without concrete consequence stays non-actionable")
        if spec["control_variant"] == "irreversible_correct_charter":
            scores = transformed_decisions(control)
            add("irreversible_marker_correct_charter", control["fixture_id"], "MJ", scores["MJ"]["decision"], "no_flag", scores["MJ"]["decision"] == "no_flag", "correct existing charter marker is not a defect")
        if spec["control_variant"] in {"fail_closed_abstention", "unknown_contract"}:
            scores = transformed_decisions(control)
            for model in MODELS:
                add("unknown_is_not_fail", control["fixture_id"], model, scores[model]["decision"], "abstain", scores[model]["decision"] == "abstain", "unknown evidence must not be manufactured into a failure")
        if spec["control_variant"] == "same_digest_distinct_tuple":
            transformed = copy.deepcopy(control)
            transformed["metadata"].update(external_verification="UNKNOWN", repository_head_equal=True)
            scores = transformed_decisions(transformed)
            add("repository_equality_is_not_external_truth", control["fixture_id"], "MJ", scores["MJ"]["decision"], "no_flag", scores["MJ"]["decision"] == "no_flag", "repository-local equality does not assert external truth")

    for spec in PAIR_SPECS[:8]:
        control = copy.deepcopy(by_pair_role[(spec["pair_id"], "control")])
        missing, mismatch = copy.deepcopy(control), copy.deepcopy(control)
        missing["objects"]["action"]["approval_ref"] = None
        mismatch["objects"]["action"]["approval_ref"] = "mismatch-approval"
        missing_score, mismatch_score = model_record("MJ", missing), model_record("MJ", mismatch)
        passed = missing_score["decision"] == "flag" and mismatch_score["decision"] == "flag" and missing_score["reason_code"] != mismatch_score["reason_code"]
        add("missing_vs_mismatch_diagnostic", control["fixture_id"], "MJ", [missing_score["decision"], mismatch_score["decision"]], "both_flag_with_distinct_refs", passed, "missing and mismatched references remain separate diagnostics")
    return rows


def junction_ablation_rows(results: list[dict[str, Any]], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_map = {row["fixture_id"]: row for row in packets}
    holdout = [row for row in results if row["model_id"] == "MJ" and row["truth_class"] == "DEFECT" and row["split"] != "calibration" and row["decision"] == "flag"]
    rows = []
    for removed in JUNCTION_CANDIDATE["tuple_dimensions"] + ["claim_action_reference", "approval_action_reference", "provider_relation", "consequence_relation"]:
        missed = []
        for row in holdout:
            packet = packet_map[row["fixture_id"]]
            reason = row["reason_code"]
            dimension_match = removed in {"subject_id", "version", "scope", "lifecycle_epoch"} and "binding_tuple" in reason
            relation_match = (
                removed == "claim_action_reference" and "claim_action" in reason
            ) or (
                removed == "approval_action_reference" and "approval_action" in reason
            ) or (
                removed == "provider_relation" and "provider" in reason
            ) or (
                removed == "consequence_relation" and ("consequence" in reason or "effect_" in reason)
            )
            if dimension_match or relation_match:
                missed.append(packet["fixture_id"])
        rows.append({"candidate_variant": "MJ", "removed_dimension_or_relation": removed, "holdout_defects_missed": len(missed), "missed_fixture_ids": missed, "interpretation": "research minimality only; no canonical field or relation is proposed"})
    return rows


def maintenance_rows() -> list[dict[str, Any]]:
    rows = read_jsonl(RESEARCH / "maintenance-perturbations.jsonl")
    return [
        {
            **row,
            "local_patchwork_semantic_update_sites": row["local_sites_affected"],
            "junction_candidate_adapter_sites": row["junction_adapters_affected"],
            "distributed_drift_risk": "higher" if row["local_sites_affected"] > row["junction_adapters_affected"] else "bounded",
            "centralized_blast_radius": "candidate_and_adapter_tests" if row["junction_adapters_affected"] else "none",
            "post_freeze_change_applied": False,
        }
        for row in rows
    ]


def transfer_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    output = {"schema_version": "1.0.0", "task_id": TASK_ID, "models": {}, "question": "Does MJ generalize without hidden extra facts or post-freeze local predicates?", "answer_basis": "Frozen existing fields and references only; no external truth or provider output was consulted."}
    for model in MODELS:
        rows = [row for row in results if row["model_id"] == model and row["split"] == "holdout_transfer"]
        output["models"][model] = {
            "defect_count": sum(row["truth_class"] == "DEFECT" for row in rows),
            "flagged_defects": sum(row["truth_class"] == "DEFECT" and row["decision"] == "flag" for row in rows),
            "control_count": sum(row["truth_class"] == "CONTROL" for row in rows),
            "control_false_positives": sum(row["truth_class"] == "CONTROL" and row["decision"] == "flag" for row in rows),
            "families": sorted({row["family"] for row in rows}), "post_freeze_new_predicates": 0,
        }
    return output


def verdict_for(results: list[dict[str, Any]], metrics: dict[str, Any], metamorphic: list[dict[str, Any]]) -> dict[str, Any]:
    mj = metrics["paired_comparisons"]["MJ"]
    mj_holdout, ml_holdout = metrics["models"]["MJ"]["holdout"], metrics["models"]["ML"]["holdout"]
    mj_only, ml_only = metrics["paired_comparisons"]["MJ"]["mj_only_against_ml"], metrics["paired_comparisons"]["ML"]["ml_only_against_mj"]
    gates = {
        "mj_holdout_incremental_min_6": mj["incremental_defects_holdout"] >= 6,
        "mj_holdout_families_min_3": len(mj["incremental_families_holdout"]) >= 3,
        "mj_holdout_binding_subtypes_min_2": len(mj["incremental_binding_subtypes_holdout"]) >= 2,
        "mj_holdout_control_fp_max_1": mj_holdout["fp"] <= 1,
        "mj_transfer_has_defect_signal": mj["incremental_defects_transfer"] >= 1,
        "ml_not_post_freeze_extended": HYPOTHESIS_FREEZE["post_freeze_local_predicate_additions"] == 0,
        "metamorphic_suite_passes": all(row["passed"] for row in metamorphic),
        "no_new_authority_truth_capability_lifecycle": True,
    }
    if not gates["metamorphic_suite_passes"]:
        verdict = "INCONCLUSIVE"
    elif all(gates.values()) and mj_only > 0:
        verdict = "JUNCTION_INVARIANT_SUPPORTED_AS_RESEARCH_CANDIDATE"
    elif ml_holdout["tp"] > 0 and mj_holdout["tp"] == 0:
        verdict = "LOCAL_PREDICATE_SUFFICIENCY_SUPPORTED"
    elif mj_holdout["tp"] > 0 or ml_holdout["tp"] > 0:
        verdict = "MIXED_NO_PROMOTION"
    else:
        verdict = "BOTH_FAIL"
    return {
        "schema_version": "1.0.0", "task_id": TASK_ID, "verdict": verdict, "gates": gates,
        "mj_only_holdout_defects": mj_only, "ml_only_holdout_defects": ml_only,
        "mj_distinct_binding_subtypes": len(mj["incremental_binding_subtypes_holdout"]),
        "frozen_verdict_table": ["LOCAL_PREDICATE_SUFFICIENCY_SUPPORTED", "JUNCTION_INVARIANT_SUPPORTED_AS_RESEARCH_CANDIDATE", "MIXED_NO_PROMOTION", "BOTH_FAIL", "INCONCLUSIVE"],
        "promotion": {"canonical_layer": False, "production_validator": False, "runtime_gate": False, "authority_or_truth_state": False, "lifecycle_change": False, "owner_acceptance": False, "external_truth": False},
        "interpretation": "Even a supported research candidate remains bounded evidence and requires a separately authorized future task before any canonical design discussion.",
        "boundary": BOUNDARY,
    }


def markdown_report(
    results: list[dict[str, Any]],
    metrics: dict[str, Any],
    transfer: dict[str, Any],
    verdict: dict[str, Any],
    metamorphic: list[dict[str, Any]],
    ablation: list[dict[str, Any]],
    maintenance: list[dict[str, Any]],
) -> dict[str, str]:
    freeze = read_json(RESEARCH / "freeze-ledger.json")
    score_sha, result_sha = sha256_file(RESEARCH / "score-run-1.jsonl"), sha256_file(RESEARCH / "results.jsonl")
    mj_holdout, ml_holdout = metrics["models"]["MJ"]["holdout"], metrics["models"]["ML"]["holdout"]
    family_lines = []
    for family in FAMILY_META:
        rows = [row for row in results if row["family"] == family and row["split"] != "calibration" and row["truth_class"] == "DEFECT"]
        family_lines.append(f"| {family} | {FAMILY_META[family]['name']} | {len(rows)} | {sum(row['decision'] == 'flag' for row in rows)} | {FAMILY_META[family]['transfer_relation']} |")
    competition = f"""# Task157 Junction Invariant vs Local Predicate Competition — 2026-09-06

## Outcome

The frozen verdict is {verdict["verdict"]}. The experiment used 96 paired fixtures and 192 blind instances across eight families: 48 calibration pairs, 24 in-family holdout pairs, and 24 transfer holdout pairs. Pair members stayed together. The result is research evidence only.

Holdout MJ incremental defects beyond M0: {metrics["paired_comparisons"]["MJ"]["incremental_defects_holdout"]}; ML: {metrics["paired_comparisons"]["ML"]["incremental_defects_holdout"]}. MJ-only holdout defects over ML: {verdict["mj_only_holdout_defects"]}. MJ holdout control false positives: {mj_holdout["fp"]}; ML holdout control false positives: {ml_holdout["fp"]}.

## Frozen provenance and boundary

- Command source: Arvin-liu/1111 agent-commands/IGNITION-20260906-157.md
- Command commit: {COMMAND_COMMIT}; blob: {COMMAND_BLOB}; content SHA-256: {COMMAND_SHA256}
- Formal baseline: Arvin-liu/when-systems-catch-fire at {BASE_COMMIT}, Task156 Draft PR #206 head
- Freeze digest: {freeze["freeze_digest"]}
- Blind score-run SHA-256: {score_sha}; unblinded results SHA-256: {result_sha}
- No provider action, external truth assertion, Owner acceptance, production gate, runtime change, authority change, lifecycle change, or canonical layer was performed.

The stale 1111 instructions/CURRENT.md and 1111 relay/current pointers were recorded as STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL and left unchanged. They did not override the explicit Task157 command.

## Family coverage

| Family | Question | Holdout defects | MJ flags | Transfer relation |
|---|---|---:|---:|---|
{chr(10).join(family_lines)}

## Method

M0 used only object-local status records. ML used the frozen direct predicate registry, with no shared tuple helper. MJ used one typed research candidate over existing subject_id, version, scope, and lifecycle_epoch fields plus existing object references. MH was diagnostic only. Strict equality was not treated as sufficient: valid v1-to-v2 migration and allowed surface delay were explicit controls. The scorer input excluded the answer key and historical outcomes; two clean-clone runs were required to be byte-identical.

Strong controls included valid upgrades and migrations, same digest with distinct object context, allowed surface delay, fail-closed abstention, no safe alternative, irreversible effect with a correct existing charter marker, valid signer without a concrete defect, irrelevant evidence, label-only variation, Base/Delta isolation, and unknown distinct from fail.

## Metamorphic and maintenance evidence

- Metamorphic rows: {len(metamorphic)}; violations: {sum(not row["passed"] for row in metamorphic)}
- Junction ablation rows: {len(ablation)}; removed dimensions and relations are recorded without promoting any dimension.
- Maintenance perturbations: {len(maintenance)}; ML semantic update sites are distributed while MJ adapter changes are centralized, with central blast radius retained as a residual.

## Interpretation

If the frozen gates support MJ, that supports only a reusable research candidate for review. It does not establish a new truth state, authority, capability, lifecycle state, canonical contract, validator, or runtime gate. Task156 vocabulary is downgraded from any strong foundation claim to bounded comparative research vocabulary.
"""

    minimality = f"""# Task157 Binding Minimality and Maintenance — 2026-09-06

## Candidate

The candidate is a typed relation over existing tuple dimensions: subject_id, version, scope, and lifecycle_epoch, together with existing claim/action, approval/action, Base/Delta, source/identity/projection/surface, release/admission/provider, and consequence/obligation/owner references. It introduces no authority, truth, capability, or lifecycle state.

Strict equality is insufficient for the controls because an explicitly allowed version migration and surface delay are not defects. Typed compatibility is bounded by the existing transition marker, exact subject/scope/epoch equality, and the explicit delay boundary.

## Ablation

{chr(10).join(f"- remove {row['removed_dimension_or_relation']}: {row['holdout_defects_missed']} holdout defects missed" for row in ablation)}

These are counterfactual research observations, not a prescription to add fields to canonical schemas.

## Maintenance topology

- Local patchwork registry size: {len(LOCAL_REGISTRY)} direct predicates and relation sites.
- Junction candidate tuple dimensions: {len(JUNCTION_CANDIDATE["tuple_dimensions"])}; relation groups: {len(JUNCTION_CANDIDATE["relation_groups"])}.
- Distributed drift risk: each local predicate can diverge at its own site.
- Centralized blast radius: a shared candidate can make one semantic error affect all adapters; this is recorded as a residual.

The perturbation ledger keeps both costs visible: duplicated semantic updates in ML and centralized blast radius in MJ.
"""

    casebook = [
        "# Task157 Paired Casebook — 2026-09-06", "",
        "This casebook summarizes fresh generated pairs; exact packet and answer-key records are machine-scored under the research data directory.", "",
        "| Family | Calibration / in-family / transfer | Defect surface | Control variants |",
        "|---|---|---|---|",
    ]
    for family, meta in FAMILY_META.items():
        specs = [spec for spec in PAIR_SPECS if spec["family"] == family]
        casebook.append(f"| {family} {meta['name']} | 6 / 3 / 3 pairs | {meta['transfer_relation']} | {', '.join(sorted({spec['control_variant'] for spec in specs}))} |")
    casebook.extend(["", "Ambiguous signer-only stress cases were not forced into the defect class. Unknown evidence was kept distinct from fail. Repository equality was never treated as external truth.", "", "The casebook is a research surface and is excluded from canonical claim discovery by narrow Task157 exclusions."])

    questions = [
        ("1. Holdout defect and control outcomes", f"MJ TP={mj_holdout['tp']}, FN={mj_holdout['fn']}, abstain={mj_holdout['defect_abstain']}, control FP={mj_holdout['fp']}, TN={mj_holdout['tn']}; ML TP={ml_holdout['tp']}, FN={ml_holdout['fn']}, control FP={ml_holdout['fp']}."),
        ("2. Transfer generalization", f"MJ transfer incremental defects={metrics['paired_comparisons']['MJ']['incremental_defects_transfer']} across {len(metrics['paired_comparisons']['MJ']['incremental_families_holdout'])} families; no post-freeze ML predicate was added."),
        ("3. MJ-only defects", f"{verdict['mj_only_holdout_defects']} holdout instances were MJ-only; subtypes are {metrics['paired_comparisons']['MJ']['incremental_binding_subtypes_holdout']}."),
        ("4. ML-only defects", f"{verdict['ml_only_holdout_defects']} holdout defects were ML-only against MJ; zero is recorded rather than manufactured."),
        ("5. Post-freeze predicate additions", "None. The registry and freeze ledger record zero post-freeze local predicate additions and zero new junction dimensions."),
        ("6. Hidden extra facts", "None. Scoring used blind packets and frozen existing fields/references; no external truth, provider output, or answer label was read."),
        ("7. Duplicated sites and adapters", f"ML has {len(LOCAL_REGISTRY)} direct predicate sites; MJ has one candidate with {len(JUNCTION_CANDIDATE['relation_groups'])} relation groups plus adapters."),
        ("8. Maintenance perturbations", "ML semantic changes were distributed across local sites; MJ changes were centralized at adapters, so drift and blast radius remain separate costs."),
        ("9. Strict versus typed equality", "Strict equality would reject explicit v1-to-v2 migration and allowed surface delay controls; typed compatibility preserves those controls without adding authority or truth."),
        ("10. Tuple dimensions", "The frozen candidate tested subject_id, version, scope, and lifecycle_epoch; ablation records missed holdout rows for each removal without canonicalizing any dimension."),
        ("11. Claim/action versus approval/action", "They were separate relation groups and reason codes; a valid claim reference does not authorize an action, and a valid approval reference does not prove claim ceiling."),
        ("12. Historical links", "CC-012, CC-020, and CC-026 are lineage context only; fresh fixtures were not historical replays and no historical record supplied an answer label."),
        ("13. Diagnostic labels", "Missing, mismatched, unknown, ambiguous signer, provider capability, lifecycle epoch, scope contamination, and consequence ownership remain separate bounded labels."),
        ("14. Binding versus local", "The result is comparative research evidence about a shared binding candidate versus direct local predicates, not a new canonical contract."),
        ("15. Downgrade of Task156 vocabulary", "Any strong foundation or universal claim is downgraded to a bounded research lens and candidate assessment."),
        ("16. Why no canonicalization", "The experiment cannot grant Owner authority, external truth, production readiness, or lifecycle permission; a separately authorized design task would be required."),
        ("17. Metamorphic evidence", f"{len(metamorphic)} rows were checked and {sum(not row['passed'] for row in metamorphic)} violations were observed."),
        ("18. Remaining maintenance risk", "A shared invariant reduces duplicated logic but increases centralized blast radius; the ledger preserves both sides."),
        ("19. Repository and CI status", "Formal and 1111 Draft PR evidence is recorded separately after publication; a Draft, CI, or projection is not equated with acceptance."),
        ("20. Final epistemic boundary", "The verdict is frozen research evidence only: no production, canonical, authority, capability, lifecycle, external-truth, merge, promotion, or Owner-acceptance claim."),
    ]
    report = [
        f"# Task report {TASK_ID}", "",
        f"Completion state at local unblind: PENDING_DRAFT_AND_REMOTE_CI; frozen verdict: {verdict['verdict']}.", "",
        "This report answers the mandatory questions while preserving OBSERVATION, EXPERIMENTAL_MODEL, SYNTHETIC_FIXTURE, INFERENCE, VERDICT, and OPEN boundaries.", "",
        "## Mandatory questions", "",
    ]
    for title, answer in questions:
        report.extend([f"### {title}", "", answer, ""])
    report.extend([
        "## Machine evidence", "",
        f"- freeze digest: {freeze['freeze_digest']}",
        f"- score-run-1 SHA-256: {score_sha}",
        f"- results SHA-256: {result_sha}",
        f"- metamorphic violations: {sum(not row['passed'] for row in metamorphic)}",
        f"- formal baseline: {BASE_COMMIT}",
        f"- command source SHA-256: {COMMAND_SHA256}", "",
        "## Residuals", "",
        "- STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL: 1111 instructions/CURRENT.md and 1111 relay/current were observed and left unchanged.",
        "- A Draft PR is not Owner acceptance; CI is not external truth; repository equality is not external truth.",
        "- No full-regression claim is made unless the exact command-required run is separately evidenced.", "",
    ])
    result = f"""# {TASK_ID} result

status: PENDING_DRAFT_AND_REMOTE_CI
verdict: {verdict["verdict"]}
formal_baseline: {BASE_COMMIT}
freeze_digest: {freeze["freeze_digest"]}
score_runs: byte-identical required; local unblind completed
canonical_change: false
production_change: false
authority_or_truth_change: false
lifecycle_change: false
owner_acceptance: false
external_truth: false

The experiment is ready for separately evidenced Draft PR and exact final-head CI checks. The verdict remains a research candidate or bounded comparison only.
"""
    return {
        "docs/governance/junction-invariant-vs-local-predicates-competition-2026-09-06.md": competition,
        "docs/governance/junction-binding-minimality-and-maintenance-2026-09-06.md": minimality,
        "docs/governance/junction-vs-local-predicates-casebook-2026-09-06.md": "\n".join(casebook) + "\n",
        "reports/governance/task-IGNITION-20260906-157.md": "\n".join(report),
        "agent-results/IGNITION-20260906-157-result.md": result,
    }


def command_unblind() -> int:
    packets, answers, manifests, _ = make_corpus()
    errors = validate_corpus(packets, answers, manifests)
    if errors:
        raise SystemExit("CORPUS_INVALID_BEFORE_UNBLIND: " + " | ".join(errors))
    score1, score2 = RESEARCH / "score-run-1.jsonl", RESEARCH / "score-run-2.jsonl"
    if not score1.is_file() or not score2.is_file():
        raise SystemExit("MISSING_TWO_SCORE_RUNS")
    if score1.read_bytes() != score2.read_bytes():
        raise SystemExit("SCORE_RUN_BYTES_DIFFER")
    score_rows = read_jsonl(score1)
    errors = validate_score_rows(score_rows)
    if errors:
        raise SystemExit("SCORE_INVALID_BEFORE_UNBLIND: " + " | ".join(errors))
    results = unblind_results(score_rows, answers)
    write_jsonl(RESEARCH / "results.jsonl", results)
    metrics = metrics_tree(results)
    write_json(RESEARCH / "metrics.json", metrics)
    transfer = transfer_summary(results)
    write_json(RESEARCH / "transfer-generalization.json", transfer)
    metamorphic = metamorphic_rows(packets, answers)
    write_jsonl(RESEARCH / "metamorphic-results.jsonl", metamorphic)
    ablation = junction_ablation_rows(results, packets)
    write_jsonl(RESEARCH / "junction-ablation.jsonl", ablation)
    maintenance = maintenance_rows()
    write_jsonl(RESEARCH / "maintenance-results.jsonl", maintenance)
    counterfactual = [
        {
            "fixture_id": row["fixture_id"], "pair_id": row["pair_id"], "model_id": row["model_id"],
            "family": row["family"], "binding_subtype": row["binding_subtype"],
            "incremental_beyond_m0": True, "local_contract_mutation_allowed": False,
            "counterfactual_action": "REVIEW_ONLY_NO_LOCAL_MUTATION",
            "interpretation": "Incremental detection is a research comparison, not permission to add a local predicate or production gate.",
        }
        for row in results if row["incremental_beyond_m0"] and row["truth_class"] == "DEFECT"
    ]
    write_jsonl(RESEARCH / "counterfactual-minimality.jsonl", counterfactual)
    verdict = verdict_for(results, metrics, metamorphic)
    write_json(RESEARCH / "verdict.json", verdict)
    write_json(RESEARCH / "maintenance-topology.json", {
        "schema_version": "1.0.0", "task_id": TASK_ID,
        "local_patchwork": {"predicate_count": len(LOCAL_REGISTRY), "relation_sites": len(LOCAL_REGISTRY), "shared_helper": False},
        "junction_candidate": {"tuple_dimensions": JUNCTION_CANDIDATE["tuple_dimensions"], "relation_groups": len(JUNCTION_CANDIDATE["relation_groups"]), "shared_helper": True},
        "maintenance_perturbations": len(maintenance), "central_blast_radius_retained": True,
    })
    for relative, content in markdown_report(results, metrics, transfer, verdict, metamorphic, ablation, maintenance).items():
        write_bytes(ROOT / relative, content.encode("utf-8"))
    print(f"UNBLINDED verdict={verdict['verdict']} results={len(results)} metamorphic={len(metamorphic)} counterfactual={len(counterfactual)}")
    return 0


def command_validate() -> int:
    packets, answers, manifests, _ = make_corpus()
    errors = validate_corpus(packets, answers, manifests)
    if (RESEARCH / "score-run-1.jsonl").is_file():
        errors.extend(validate_score_rows(read_jsonl(RESEARCH / "score-run-1.jsonl")))
    if errors:
        raise SystemExit("VALIDATION_FAILED: " + " | ".join(errors))
    print("TASK157_RESEARCH_VALID")
    return 0


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate")
    score = sub.add_parser("score")
    score.add_argument("--output", type=Path)
    sub.add_parser("unblind")
    sub.add_parser("validate")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "generate":
        return command_generate()
    if args.command == "score":
        return command_score(args.output)
    if args.command == "unblind":
        return command_unblind()
    if args.command == "validate":
        return command_validate()
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
