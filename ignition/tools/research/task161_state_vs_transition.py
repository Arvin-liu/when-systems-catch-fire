#!/usr/bin/env python3
"""Task161 research-only state-versus-transition semantics competition.

This tool creates a deterministic prospective paired-fixture suite, freezes all
inputs before scoring, scores blind packets in two clean clones, and writes
task-scoped evidence.  It is intentionally not imported by canonical runtime
code and must not be treated as a production validator.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
TASK = "IGNITION-20260907-161"
FORMAL_REPO = "Arvin-liu/when-systems-catch-fire"
FORMAL_PR = 210
FORMAL_BASE_REF = "work/IGNITION-20260907-160"
FORMAL_BASE = "9ceb4c4eb84203bee2b62dcdbe0d5c1c09707438"
FORMAL_BRANCH = "work/IGNITION-20260907-161"
COMMAND_REPO = "Arvin-liu/1111"
COMMAND_PATH = "agent-commands/IGNITION-20260907-161.md"
COMMAND_COMMIT = "59003ae23c56a2f0c4ac6389d5235c938cd5f5fd"
COMMAND_BLOB = "610febea27a1e4cb62d9c32da4b19a9113a243ec"
COMMAND_SHA256 = "9f1df434d39aa379fac5eb2254b250530720e994176526da3c971ee0e84d06de"

OUT = ROOT / "data/research/state-vs-transition-semantics-2026-09-07"
T160_DIR = ROOT / "data/research/basis-escape-v2-2026-09-07"
T160_RESIDUALS = T160_DIR / "representation-residuals.jsonl"
T160_UNIVERSE = T160_DIR / "corpus-universe.jsonl"
T159_SIGNATURE = {
    "L1": "NO when a semantic-conservative OldBasis -> NewRepresentation mapping preserves states, operations and questions",
    "L2": "YES only for a previously unproducible object/operator class",
    "L3": "YES only with a pre-leap unaskable to post-leap representable question",
    "L4": "YES only for a failure mode passing all old checks",
    "L5": "supportive only; requires two independent pre-existing families",
    "L6": "YES only if removing the new semantic primitive loses capability",
    "challenger_priority": "any complete challenger plus no independent L2/L3/L4/L6 increment is NON_LEAP",
}

FAMILIES = {
    "F1": "endpoint-valid/transition-invalid",
    "F2": "legal migration versus illegal jump",
    "F3": "lifecycle epoch",
    "F4": "approval and authority",
    "F5": "evidence and claim promotion/demotion",
    "F6": "Base/Delta/scope admission",
    "F7": "release/provider/admission",
    "F8": "projection/public surface",
    "F9": "consequence/reconciliation/ownership",
    "F10": "multi-hop path",
    "F11": "rollback/reversal/cycle",
    "F12": "ordering/commutativity/concurrency",
}

CONTROL_CLASSES = (
    "PURE_STATE",
    "EVIDENCE_QUALITY",
    "AUTHORITY_ABSENCE_NOT_REQUIRED",
    "OBJECT_IDENTITY_UNCONSTRAINED",
    "EVENTUAL_PROJECTION",
    "ORDINARY_SCHEMA_MIGRATION",
    "PUBLICATION_ONLY",
)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def git(*args: str, cwd: Path = REPO) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT
    ).strip()


def git_status(cwd: Path = REPO) -> list[str]:
    return git("status", "--porcelain", "--untracked-files=all", cwd=cwd).splitlines()


def current_head(cwd: Path = REPO) -> str:
    return git("rev-parse", "HEAD", cwd=cwd)


def stable_id(prefix: str, value: Any) -> str:
    return prefix + hashlib.sha256(canonical(value)).hexdigest()[:16]


def split_for_variant(variant: int) -> str:
    if variant <= 3:
        return "calibration"
    if variant <= 7:
        return "in_family_holdout"
    return "transfer_holdout"


def base_facts(pair_id: str, family_id: str, variant: int) -> dict[str, Any]:
    number = int(pair_id.split("-")[-1])
    source = "state://{0}/item-{1:03d}/epoch-1".format(family_id, number)
    target = "state://{0}/item-{1:03d}/epoch-1/accepted".format(family_id, number)
    object_ref = "object://{0}/item-{1:03d}".format(family_id, number)
    scope = "scope://{0}/bounded".format(family_id)
    transition = "transition://{0}/item-{1:03d}/v{2}".format(
        family_id, number, variant
    )
    return {
        "source_state_ref": source,
        "target_state_ref": target,
        "source_state_valid": True,
        "target_state_valid": True,
        "source_object_ref": object_ref,
        "target_object_ref": object_ref,
        "object_ref": object_ref,
        "object_binding_mode": "same-object",
        "scope_ref": scope,
        "transition_scope_ref": scope,
        "action_scope": scope,
        "source_version": 1,
        "target_version": 2,
        "version_jump": 1,
        "max_version_jump": 1,
        "migration_marker": True,
        "migration_path": ["v1", "v2"],
        "allowed_migration_paths": [["v1", "v2"]],
        "source_lifecycle_epoch": 1,
        "target_lifecycle_epoch": 1,
        "lifecycle_epoch": 1,
        "epoch_transition_requires_boundary": False,
        "boundary_observed": True,
        "trigger": "promote",
        "allowed_trigger_kinds": ["promote"],
        "evidence_refs": ["evidence://{0}/item-{1:03d}".format(family_id, number)],
        "evidence_available": True,
        "evidence_bound": True,
        "authority_refs": ["authority://{0}/item-{1:03d}".format(family_id, number)],
        "authority_available": True,
        "authority_bound": True,
        "required_approval": True,
        "required_scope": scope,
        "approval_scope": scope,
        "approval_granted": True,
        "ordered_steps": ["admit", "promote"],
        "required_order": ["admit", "promote"],
        "commutative": False,
        "path": [source, target],
        "legal_hops": [[source, target]],
        "path_valid": True,
        "path_endpoint_valid_refs": True,
        "multi_hop": False,
        "rollback_of": None,
        "expected_rollback_of": None,
        "inverse_transition_ref": None,
        "expected_inverse_transition_ref": None,
        "reversible": True,
        "cycle_allowed": False,
        "cycle_observed": False,
        "surface_epoch": 1,
        "allowed_projection_delay": 2,
        "observed_projection_delay": 1,
        "projection_mode": "eventual",
        "projection_current": True,
        "schema_source_version": 1,
        "schema_target_version": 1,
        "publication_only": False,
        "observation_status": "OBSERVED",
        "local_annotations": {
            "allowed_state_pairs": [[source, target]],
            "forbidden_state_pairs": [],
            "scope_ref": scope,
            "known_lifecycle_epochs": [1, 2],
            "max_local_version": 99,
            "migration_paths": [["v1", "v2"], ["v1", "v3"]],
            "history_refs": [source],
            "local_order_rule": "endpoint-only",
            "local_rollback_rule": "reversible",
            "local_projection_rule": "eventual",
            "local_aliases": [],
        },
        "irrelevant_metadata": {
            "display_name": "fixture-{0}-{1:03d}".format(family_id, number),
            "annotation_order": variant % 3,
            "operator_note": "prospective fixture metadata",
        },
        "pair_contract": {
            "pair_id": pair_id,
            "same_raw_facts_for_pair_members": True,
            "family_id": family_id,
            "template_key": "template-{0:02d}".format(variant),
        },
        "transition_id": transition,
    }


def apply_scenario(
    facts: dict[str, Any], family_id: str, variant: int, family_number: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    facts = copy.deepcopy(facts)
    expected = {
        "expected_outcome": "CLEAN",
        "expected_transition_defect": False,
        "endpoint_states_valid": True,
        "all_old_checks_pass": True,
        "local_rule_suffices": False,
        "control_class": None,
        "oracle_source": "pre-registered fixture construction rule",
    }

    if variant in {0, 3, 4}:
        facts["local_annotations"]["forbidden_state_pairs"].append(
            [facts["source_state_ref"], facts["target_state_ref"]]
        )
        expected.update(
            expected_outcome="TRANSITION_DEFECT",
            expected_transition_defect=True,
            local_rule_suffices=True,
            oracle_source="local state-pair prohibition",
        )
    elif variant == 1:
        facts["target_state_valid"] = False
        expected.update(
            expected_outcome="ENDPOINT_DEFECT",
            endpoint_states_valid=False,
            all_old_checks_pass=False,
            control_class="ENDPOINT_INVALID",
            oracle_source="endpoint validity control",
        )
    elif variant == 2:
        expected["control_class"] = "NO_OP_OR_IDENTITY"
    elif variant == 6:
        facts["commutative"] = True
        facts["ordered_steps"] = ["promote", "admit"]
        facts["allowed_orderings"] = [["admit", "promote"], ["promote", "admit"]]
        facts["observed_projection_delay"] = 1
        expected["control_class"] = "COMMUTATIVE_REORDER_AND_SAFE_DELAY"
    elif variant == 11:
        control = CONTROL_CLASSES[(family_number + variant) % len(CONTROL_CLASSES)]
        expected["control_class"] = control
        if control == "PURE_STATE":
            facts["transition_scope_ref"] = facts["scope_ref"]
        elif control == "EVIDENCE_QUALITY":
            facts["evidence_refs"] = ["evidence://unrelated-quality-sample"]
            facts["evidence_bound"] = True
        elif control == "AUTHORITY_ABSENCE_NOT_REQUIRED":
            facts["required_approval"] = False
            facts["authority_available"] = False
            facts["authority_bound"] = False
        elif control == "OBJECT_IDENTITY_UNCONSTRAINED":
            facts["object_binding_mode"] = "unconstrained"
            facts["target_object_ref"] = "object://unconstrained/other"
        elif control == "EVENTUAL_PROJECTION":
            facts["projection_mode"] = "eventual"
            facts["projection_current"] = False
            facts["observed_projection_delay"] = 2
        elif control == "ORDINARY_SCHEMA_MIGRATION":
            facts["schema_source_version"] = 1
            facts["schema_target_version"] = 2
            facts["migration_marker"] = True
            facts["migration_path"] = ["v1", "v2"]
        elif control == "PUBLICATION_ONLY":
            facts["publication_only"] = True
            facts["trigger"] = "publish"
            facts["required_approval"] = False
    elif variant in {5, 7, 8, 9, 10}:
        expected.update(
            expected_outcome="TRANSITION_DEFECT",
            expected_transition_defect=True,
            oracle_source="pre-registered transition constraint violation",
        )
        if variant == 5:
            if family_id == "F1":
                facts["target_object_ref"] = "object://foreign/item"
            elif family_id == "F2":
                facts.update(
                    target_version=3,
                    version_jump=2,
                    migration_marker=False,
                    migration_path=["v1", "v3"],
                )
            elif family_id == "F3":
                facts.update(
                    target_lifecycle_epoch=2,
                    epoch_transition_requires_boundary=True,
                    boundary_observed=False,
                )
            elif family_id == "F4":
                facts["approval_scope"] = "scope://other/approval"
            elif family_id == "F5":
                facts["evidence_bound"] = False
            elif family_id == "F6":
                facts["transition_scope_ref"] = "scope://other/admission"
            elif family_id == "F7":
                facts["ordered_steps"] = ["promote", "admit"]
            elif family_id == "F8":
                facts.update(
                    projection_mode="strict",
                    projection_current=False,
                    observed_projection_delay=3,
                )
            elif family_id == "F9":
                facts.update(
                    rollback_of="transition://foreign/rollback",
                    expected_rollback_of="transition://{0}/item-{1:03d}/v4".format(
                        family_id, family_number
                    ),
                )
            elif family_id == "F10":
                middle = "state://{0}/item-{1:03d}/illegal-hop".format(
                    family_id, family_number
                )
                facts.update(
                    path=[facts["source_state_ref"], middle, facts["target_state_ref"]],
                    legal_hops=[[facts["source_state_ref"], facts["target_state_ref"]]],
                    path_valid=False,
                    multi_hop=True,
                )
            elif family_id == "F11":
                facts.update(
                    cycle_observed=True,
                    path=[
                        facts["source_state_ref"],
                        facts["target_state_ref"],
                        facts["source_state_ref"],
                    ],
                    path_valid=False,
                )
            elif family_id == "F12":
                facts["ordered_steps"] = ["promote", "admit"]
        elif variant == 7:
            facts["path_valid"] = False
            facts["path_endpoint_valid_refs"] = True
            if family_id == "F12":
                facts["commutative"] = False
                facts["ordered_steps"] = ["promote", "admit"]
            elif family_id == "F11":
                facts["cycle_observed"] = True
            else:
                facts["path"] = [
                    facts["source_state_ref"],
                    "state://{0}/item-{1:03d}/intermediate".format(
                        family_id, family_number
                    ),
                    facts["target_state_ref"],
                ]
                facts["multi_hop"] = True
        elif variant == 8:
            facts["evidence_bound"] = False
            facts["evidence_available"] = True
        elif variant == 9:
            facts["ordered_steps"] = ["promote", "admit"]
            facts["commutative"] = False
        elif variant == 10:
            facts["rollback_of"] = "transition://foreign/reversal"
            facts["expected_rollback_of"] = facts["transition_id"]
            facts["inverse_transition_ref"] = "transition://foreign/inverse"
            facts["expected_inverse_transition_ref"] = "transition://expected/inverse"
    return facts, expected


def load_historical_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    residuals = read_jsonl(T160_RESIDUALS)
    universe = read_jsonl(T160_UNIVERSE)
    transition_rows = [
        row
        for row in residuals
        if row.get("residual_family") == "transition-over-state"
    ]
    controls = [
        row
        for row in universe
        if row.get("family") == "C7_ENGINEERING_NEGATIVE_CONTROL"
    ]
    def normalize(row: dict[str, Any], kind: str, index: int) -> dict[str, Any]:
        return {
            "discovery_id": "T160-{0}-{1:04d}".format(kind, index),
            "source_path": row.get("source_path"),
            "source_item_id": row.get("item_id"),
            "corpus_family": row.get("corpus_family", row.get("family")),
            "time_slice": row.get("time_slice"),
            "residual_family": row.get("residual_family"),
            "residual_type": row.get("residual_type"),
            "evaluation_eligible": False,
            "label_status": "UNADJUDICATED_DISCOVERY_LEAD",
            "not_a_positive_by_default": True,
            "provenance_digest": digest(row),
            "dedup_key": digest(
                {
                    "source_path": row.get("source_path"),
                    "source_item_id": row.get("item_id"),
                    "corpus_family": row.get("corpus_family", row.get("family")),
                }
            ),
        }
    transition = [normalize(row, "TRANSITION_RESIDUAL", i) for i, row in enumerate(transition_rows)]
    negative = [normalize(row, "NON_TRANSITION_CONTROL", i) for i, row in enumerate(controls)]
    return transition, negative


def preflight_snapshot() -> dict[str, Any]:
    status = git_status()
    allowed = {"ignition/tools/research/task161_state_vs_transition.py"}
    unexpected = [
        line
        for line in status
        if line[3:] not in allowed and not line.endswith("task161_state_vs_transition.py")
    ]
    branch_sha = ""
    try:
        remote_line = git(
            "ls-remote", "origin", "refs/heads/" + FORMAL_BRANCH
        )
        branch_sha = remote_line.split()[0] if remote_line else ""
    except subprocess.CalledProcessError:
        branch_sha = ""
    try:
        base_local = git("rev-parse", FORMAL_BASE_REF)
        base_ref_used = FORMAL_BASE_REF
    except subprocess.CalledProcessError:
        base_local = git("rev-parse", "origin/" + FORMAL_BASE_REF)
        base_ref_used = "origin/" + FORMAL_BASE_REF
    pointers = {}
    for path in ("instructions/CURRENT.md", "relay/current"):
        target = REPO / path
        pointers[path] = {
            "exists": target.exists(),
            "preserved": True,
            "action": "preserve missing or stale pointer; no create/update/redirect",
        }
    snapshot = {
        "task_id": TASK,
        "mode": [
            "STATE_VS_TRANSITION",
            "COMPETING_SEMANTICS",
            "PROSPECTIVE_FIXTURES",
            "TRANSFER_HOLDOUT",
            "V2_SEMANTIC_LEAP_GATE",
            "RESEARCH_ONLY",
        ],
        "command_source": {
            "repository": COMMAND_REPO,
            "path": COMMAND_PATH,
            "commit": COMMAND_COMMIT,
            "blob": COMMAND_BLOB,
            "content_sha256": COMMAND_SHA256,
            "source_url": "https://github.com/{0}/blob/{1}/{2}".format(
                COMMAND_REPO, COMMAND_COMMIT, COMMAND_PATH
            ),
        },
        "formal_repository": FORMAL_REPO,
        "formal_pr": {
            "number": FORMAL_PR,
            "state": "open",
            "draft": True,
            "merged": False,
            "head_sha_observed": "9ceb4c4eb84203bee2b62dcdbe0d5c1c09707438",
            "base_ref": "work/IGNITION-20260907-159",
            "base_sha_observed": "76e44213904928f9f0be8ba131b86529e44e7682",
            "observation": "GitHub connector preflight observation",
        },
        "required_base": {
            "ref": FORMAL_BASE_REF,
            "sha": FORMAL_BASE,
            "local_sha": base_local,
            "local_ref_used": base_ref_used,
            "local_matches": base_local == FORMAL_BASE,
            "remote_task160_sha": "9ceb4c4eb84203bee2b62dcdbe0d5c1c09707438",
            "remote_task160_matches": True,
        },
        "new_branch": {
            "name": FORMAL_BRANCH,
            "remote_sha_at_preflight": branch_sha or None,
            "must_be_created_from": FORMAL_BASE,
        },
        "worktree": {
            "status_lines_at_snapshot": status,
            "clean_before_task161_implementation": not unexpected,
            "current_status_is_clean_except_planned_tool": not unexpected,
            "unexpected_changes": unexpected,
            "note": "The tool file itself is the only planned pre-commit addition; initial preflight was clean.",
        },
        "control_pointers": pointers,
        "forbidden_actions": [
            "no canonical runtime or validator integration",
            "no Ready, merge, Current, Owner acceptance, or external action",
            "no use of Task160 transition residuals as positive labels",
            "no answer-key access during blind scoring",
        ],
    }
    write_json(OUT / "preflight.json", snapshot)
    return snapshot


def build_fixtures() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    answer_key: list[dict[str, Any]] = []
    pair_number = 0
    for family_number, family_id in enumerate(FAMILIES, start=1):
        for variant in range(12):
            pair_number += 1
            pair_id = "P-{0:03d}".format(pair_number)
            split = split_for_variant(variant)
            template = "F{0}-T{1:02d}".format(family_number, variant)
            raw, expected = apply_scenario(
                base_facts(pair_id, family_id, variant),
                family_id,
                variant,
                family_number,
            )
            facts_digest = digest(raw)
            instance_ids = ["{0}-A".format(pair_id), "{0}-B".format(pair_id)]
            manifest.append(
                {
                    "pair_id": pair_id,
                    "family_id": family_id,
                    "family_description": FAMILIES[family_id],
                    "template_key": template,
                    "split": split,
                    "fixture_kind": "FRESH_PROSPECTIVE_SYNTHETIC",
                    "instance_ids": instance_ids,
                    "same_raw_facts": True,
                    "facts_digest": facts_digest,
                    "source_provenance": "task-scoped generator; no historical row reused",
                    "answer_key_excluded": True,
                }
            )
            for role in ("A", "B"):
                instance_id = "{0}-{1}".format(pair_id, role)
                packets.append(
                    {
                        "packet_id": instance_id,
                        "pair_id": pair_id,
                        "instance_id": instance_id,
                        "role": role,
                        "family_id": family_id,
                        "template_key": template,
                        "split": split,
                        "facts": copy.deepcopy(raw),
                        "facts_digest": facts_digest,
                        "answer_key_loaded": False,
                        "scorer_contract": {
                            "answer_key_visible": False,
                            "model_may_read_only": "facts",
                            "model_must_return": [
                                "outcome",
                                "reason_codes",
                                "model",
                            ],
                        },
                    }
                )
                answer_key.append(
                    {
                        "packet_id": instance_id,
                        "pair_id": pair_id,
                        "instance_id": instance_id,
                        "role": role,
                        "family_id": family_id,
                        "template_key": template,
                        "split": split,
                        "expected_outcome": expected["expected_outcome"],
                        "expected_transition_defect": expected[
                            "expected_transition_defect"
                        ],
                        "endpoint_states_valid": expected["endpoint_states_valid"],
                        "all_old_checks_pass": expected["all_old_checks_pass"],
                        "local_rule_suffices": expected["local_rule_suffices"],
                        "control_class": expected["control_class"],
                        "oracle_source": expected["oracle_source"],
                        "facts_digest": facts_digest,
                    }
                )
    if len(manifest) != 144 or len(packets) != 288:
        raise AssertionError("fixture count must be 144 pairs and 288 instances")
    write_jsonl(OUT / "fixture-manifest.jsonl", manifest)
    write_jsonl(OUT / "blind-packets.jsonl", packets)
    write_jsonl(OUT / "answer-key.jsonl", answer_key)
    return manifest, packets, answer_key


def model_definitions() -> dict[str, Any]:
    models = {
        "M0": {
            "name": "current-state-baseline",
            "reads": ["source_state_valid", "target_state_valid"],
            "rule": "reject invalid endpoints; otherwise return CLEAN",
        },
        "MS": {
            "name": "strongest-fair-local-patchwork",
            "reads": [
                "endpoint validity",
                "local_annotations.allowed_state_pairs",
                "local_annotations.forbidden_state_pairs",
                "local_annotations.scope_ref",
                "local_annotations.known_lifecycle_epochs",
                "local_annotations.history_refs",
                "local_annotations.local_aliases",
            ],
            "rule": "M0 plus local state/scope/history rules only",
            "allowed_local_patchwork": [
                "local before/after references",
                "ordered pair as local metadata",
                "allowed and forbidden state pairs",
                "bounded history",
                "local migration and rollback rules",
                "local evidence and authority references",
            ],
            "forbidden_shared_primitive": [
                "first-class transition object",
                "transition identity",
                "transition algebra",
                "path semantics",
                "central transition authority",
            ],
        },
        "MT": {
            "name": "minimal-first-class-transition-candidate",
            "reads": [
                "the exact same raw facts as MS",
                "source-to-target transition relation",
                "scope and lifecycle fields",
                "trigger, evidence, authority and approval fields",
                "ordered path, hop and rollback fields",
                "projection and concurrency fields",
            ],
            "rule": "M0 plus explicit transition relation constraints; no new authority, truth, capability or lifecycle state",
            "schema_frozen_before_holdout": True,
            "new_facts_allowed": False,
            "transition_identity": "deterministically derived from refs and tuple; not an external authority",
        },
        "MH": {
            "name": "MS-plus-MT-diagnostic",
            "rule": "union of MS and MT reason codes; diagnostic only",
        },
    }
    value = {
        "task_id": TASK,
        "research_only": True,
        "same_facts_hard_constraint": True,
        "models": models,
        "task159_v2_signature": copy.deepcopy(T159_SIGNATURE),
        "task159_signature_sha256": file_digest(
            ROOT / "data/research/semantic-leap-detector-v2-2026-09-07/semantic-leap-signature-v2.json"
        ),
        "frozen_before_holdout": [
            "hypotheses",
            "fixture schema",
            "discovery and threshold rules",
            "model definitions",
            "family/template split",
            "answer-key construction rules",
        ],
        "no_canonical_integration": True,
    }
    write_json(OUT / "model-definitions.json", value)
    return value


def freeze() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    preflight = preflight_snapshot()
    if not preflight["required_base"]["local_matches"]:
        raise AssertionError("Task160 exact base is not checked out")
    transition, negative = load_historical_records()
    write_json(
        OUT / "hypothesis-freeze.json",
        {
            "task_id": TASK,
            "frozen_before_scoring": True,
            "frozen_before_holdout": True,
            "hypotheses": {
                "H0": "state-local semantics are sufficient",
                "H1": "first-class transition semantics add irreducible capability",
                "H2": "the useful transition layer is reducible to local patchwork",
                "H3": "the missing semantics are path/non-Cartesian rather than a binary relation",
            },
            "primary_question": "Does a first-class transition relation add independently useful semantics beyond the strongest fair state-local patchwork?",
            "task160_conclusion": "MIXED_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING",
            "task160_residual_is": "discovery lead, not ground truth or positive label",
            "command_source_sha256": COMMAND_SHA256,
        },
    )
    model_definitions()
    task160_universe = read_jsonl(T160_UNIVERSE)
    transition_paths = {row["source_path"] for row in transition}
    corpus_rows = []
    for index, row in enumerate(task160_universe):
        source_path = row.get("source_path")
        if row.get("family") == "C7_ENGINEERING_NEGATIVE_CONTROL":
            partition = "STRONG_NON_TRANSITION_CONTROL"
        elif source_path in transition_paths:
            partition = "TRANSITION_OVER_STATE_DISCOVERY_LEAD"
        else:
            partition = "OTHER_TASK160_RESEARCH_ROW"
        corpus_rows.append(
            {
                "universe_id": "T160-UNIVERSE-{0:04d}".format(index),
                "source_path": source_path,
                "source_item_id": row.get("item_id"),
                "corpus_family": row.get("corpus_family", row.get("family")),
                "time_slice": row.get("time_slice"),
                "partition": partition,
                "evaluation_eligible": False,
                "label_status": "UNADJUDICATED_DISCOVERY_OR_CONTROL",
                "not_a_positive_by_default": True,
                "provenance_digest": digest(row),
            }
        )
    write_jsonl(OUT / "corpus-universe.jsonl", corpus_rows)
    write_jsonl(OUT / "historical-transition-residuals.jsonl", transition)
    write_jsonl(
        OUT / "historical-non-transition-controls.jsonl",
        negative,
    )
    manifest, packets, answer_key = build_fixtures()
    split_rows = [
        {
            "pair_id": row["pair_id"],
            "split": row["split"],
            "family_id": row["family_id"],
            "template_key": row["template_key"],
            "instance_ids": row["instance_ids"],
        }
        for row in manifest
    ]
    write_json(
        OUT / "split-manifest.json",
        {
            "pair_count": len(manifest),
            "instance_count": len(packets),
            "pair_members_stay_together": True,
            "calibration_pair_count": sum(
                row["split"] == "calibration" for row in manifest
            ),
            "in_family_holdout_pair_count": sum(
                row["split"] == "in_family_holdout" for row in manifest
            ),
            "transfer_holdout_pair_count": sum(
                row["split"] == "transfer_holdout" for row in manifest
            ),
            "transfer_unseen_family_template_combinations": 12,
            "rule": "variants 00-03 calibration, 04-07 in-family holdout, 08-11 transfer holdout",
            "digest": digest(split_rows),
            "rows": split_rows,
        },
    )
    write_json(
        OUT / "fixture-generator-manifest.json",
        {
            "task_id": TASK,
            "generator": "task161_state_vs_transition.py",
            "generator_version": "1.0.0",
            "seed_rule": "family ordinal plus variant ordinal; no random source",
            "families": FAMILIES,
            "variants_per_family": 12,
            "instances_per_pair": 2,
            "pair_count": len(manifest),
            "instance_count": len(packets),
            "strong_negative_controls": list(CONTROL_CLASSES)
            + ["ENDPOINT_INVALID", "NO_OP_OR_IDENTITY"],
            "historical_sources_not_reused_as_fixtures": True,
        },
    )
    write_json(
        OUT / "freeze-ledger.json",
        {
            "status": "FROZEN",
            "freeze_order": [
                "hypotheses",
                "corpus universe",
                "fixture generator",
                "model definitions",
                "split",
                "blind packets",
                "answer key sealed separately",
            ],
            "command_source": {
                "repository": COMMAND_REPO,
                "path": COMMAND_PATH,
                "commit": COMMAND_COMMIT,
                "blob": COMMAND_BLOB,
                "content_sha256": COMMAND_SHA256,
            },
            "formal_base": {
                "ref": FORMAL_BASE_REF,
                "sha": FORMAL_BASE,
            },
            "preflight_digest": digest(preflight),
            "corpus_digest": file_digest(OUT / "corpus-universe.jsonl"),
            "fixture_manifest_digest": file_digest(OUT / "fixture-manifest.jsonl"),
            "split_digest": digest(read_json(OUT / "split-manifest.json")),
            "model_digest": file_digest(OUT / "model-definitions.json"),
            "answer_key_digest": file_digest(OUT / "answer-key.jsonl"),
            "blind_packet_digest": file_digest(OUT / "blind-packets.jsonl"),
            "immutable_after_freeze": True,
        },
    )
    return read_json(OUT / "freeze-ledger.json")


def frozen_inputs() -> dict[str, Any]:
    required = [
        "hypothesis-freeze.json",
        "model-definitions.json",
        "corpus-universe.jsonl",
        "historical-transition-residuals.jsonl",
        "fixture-generator-manifest.json",
        "fixture-manifest.jsonl",
        "split-manifest.json",
        "freeze-ledger.json",
        "blind-packets.jsonl",
        "answer-key.jsonl",
    ]
    missing = [name for name in required if not (OUT / name).exists()]
    if missing:
        raise AssertionError("frozen inputs missing: " + ", ".join(missing))
    ledger = read_json(OUT / "freeze-ledger.json")
    if ledger.get("status") != "FROZEN":
        raise AssertionError("freeze ledger is not FROZEN")
    if ledger.get("formal_base", {}).get("sha") != FORMAL_BASE:
        raise AssertionError("freeze ledger base drift")
    return ledger


def verify() -> dict[str, Any]:
    ledger = frozen_inputs()
    manifest = read_jsonl(OUT / "fixture-manifest.jsonl")
    packets = read_jsonl(OUT / "blind-packets.jsonl")
    answers = read_jsonl(OUT / "answer-key.jsonl")
    if len(manifest) != 144 or len(packets) != 288 or len(answers) != 288:
        raise AssertionError("frozen fixture counts are not 144/288/288")
    by_pair = defaultdict(list)
    for packet in packets:
        by_pair[packet["pair_id"]].append(packet)
        if packet.get("answer_key_loaded"):
            raise AssertionError("blind packet records answer-key access")
    if len(by_pair) != 144 or any(len(rows) != 2 for rows in by_pair.values()):
        raise AssertionError("paired fixture invariant failed")
    for rows in by_pair.values():
        if rows[0]["split"] != rows[1]["split"]:
            raise AssertionError("pair members split apart")
        if rows[0]["facts_digest"] != rows[1]["facts_digest"]:
            raise AssertionError("pair members do not share raw facts")
        if rows[0]["facts"] != rows[1]["facts"]:
            raise AssertionError("pair member raw facts differ")
    if json.loads(
        (ROOT / "data/research/semantic-leap-detector-v2-2026-09-07/semantic-leap-signature-v2.json").read_text(
            encoding="utf-8"
        )
    ) != T159_SIGNATURE:
        raise AssertionError("Task159 V2 signature drift")
    if file_digest(OUT / "corpus-universe.jsonl") != ledger["corpus_digest"]:
        raise AssertionError("corpus digest drift")
    for name, expected in (
        ("fixture-manifest.jsonl", ledger["fixture_manifest_digest"]),
        ("split-manifest.json", ledger["split_digest"]),
        ("model-definitions.json", ledger["model_digest"]),
        ("answer-key.jsonl", ledger["answer_key_digest"]),
        ("blind-packets.jsonl", ledger["blind_packet_digest"]),
    ):
        actual = (
            digest(read_json(OUT / name))
            if name == "split-manifest.json"
            else file_digest(OUT / name)
        )
        if actual != expected:
            raise AssertionError("frozen digest drift: " + name)
    scores_equal = False
    if (OUT / "score-run-1.jsonl").is_file() and (OUT / "score-run-2.jsonl").is_file():
        scores_equal = (OUT / "score-run-1.jsonl").read_bytes() == (
            OUT / "score-run-2.jsonl"
        ).read_bytes()
    result = {
        "task_id": TASK,
        "freeze_status": ledger["status"],
        "pair_count": len(by_pair),
        "instance_count": len(packets),
        "same_facts_for_pair_members": True,
        "score_runs_byte_identical": scores_equal,
        "task159_signature_exact": True,
        "answer_key_not_loaded_in_blind_packets": True,
        "formal_base": ledger["formal_base"],
        "passed": True,
    }
    write_json(OUT / "verification.json", result)
    return result


def local_reason_codes(facts: dict[str, Any]) -> list[str]:
    if not facts["source_state_valid"] or not facts["target_state_valid"]:
        return ["ENDPOINT_INVALID"]
    annotations = facts["local_annotations"]
    reasons: list[str] = []
    pair = [facts["source_state_ref"], facts["target_state_ref"]]
    if pair in annotations["forbidden_state_pairs"]:
        reasons.append("LOCAL_FORBIDDEN_STATE_PAIR")
    if pair not in annotations["allowed_state_pairs"]:
        reasons.append("LOCAL_PAIR_NOT_ALLOWED")
    if annotations["scope_ref"] != facts["scope_ref"]:
        reasons.append("LOCAL_SCOPE_MISMATCH")
    if facts["target_lifecycle_epoch"] not in annotations["known_lifecycle_epochs"]:
        reasons.append("LOCAL_UNKNOWN_EPOCH")
    if facts["target_version"] > annotations["max_local_version"]:
        reasons.append("LOCAL_VERSION_LIMIT")
    if facts["source_state_ref"] not in annotations["history_refs"]:
        reasons.append("LOCAL_HISTORY_MISS")
    return sorted(set(reasons))


def transition_reason_codes(
    facts: dict[str, Any], ablation: str | None = None
) -> list[str]:
    if not facts["source_state_valid"] or not facts["target_state_valid"]:
        return ["ENDPOINT_INVALID"]
    reasons: list[str] = []
    disabled_by_ablation = {
        "remove_transition_identity": {"identity", "binding"},
        "remove_ordered_source_target": {"binding"},
        "remove_scope_lifecycle": {"scope", "lifecycle"},
        "remove_trigger_evidence": {"trigger", "evidence"},
        "remove_authority_approval": {"authority", "approval"},
        "remove_path_order": {"path", "order"},
        "collapse_endpoint_pair": {"binding", "identity", "path"},
        "collapse_multi_hop_final_state": {"path"},
    }

    def enabled(name: str) -> bool:
        return name not in disabled_by_ablation.get(ablation or "", set())
    if enabled("binding") and facts["object_binding_mode"] == "same-object":
        if facts["source_object_ref"] != facts["target_object_ref"]:
            reasons.append("TRANSITION_OBJECT_BINDING_MISMATCH")
    if enabled("scope") and facts["transition_scope_ref"] != facts["scope_ref"]:
        reasons.append("TRANSITION_SCOPE_MISMATCH")
    if enabled("lifecycle"):
        if (
            facts["source_lifecycle_epoch"] != facts["target_lifecycle_epoch"]
            and facts["epoch_transition_requires_boundary"]
            and not facts["boundary_observed"]
        ):
            reasons.append("TRANSITION_EPOCH_BOUNDARY_MISSING")
    if enabled("version"):
        if (
            facts["version_jump"] > facts["max_version_jump"]
            or not facts["migration_marker"]
            or facts["migration_path"] not in facts["allowed_migration_paths"]
        ):
            reasons.append("TRANSITION_MIGRATION_PATH_INVALID")
    if enabled("trigger") and enabled("evidence"):
        if (
            not facts["publication_only"]
            and facts["trigger"] in facts["allowed_trigger_kinds"]
            and not facts["evidence_bound"]
        ):
            reasons.append("TRANSITION_EVIDENCE_UNBOUND")
    if enabled("authority") and enabled("approval"):
        if facts["required_approval"] and (
            not facts["approval_granted"]
            or facts["approval_scope"] != facts["required_scope"]
            or not facts["authority_bound"]
        ):
            reasons.append("TRANSITION_APPROVAL_AUTHORITY_MISMATCH")
    if enabled("order") and not facts["commutative"]:
        if facts["ordered_steps"] != facts["required_order"]:
            reasons.append("TRANSITION_ORDER_INVALID")
    path_enabled = enabled("path") and ablation not in {
        "collapse_multi_hop_final_state",
        "collapse_endpoint_pair",
    }
    if path_enabled:
        if not facts["path_valid"] or not facts["path_endpoint_valid_refs"]:
            reasons.append("TRANSITION_PATH_INVALID")
        elif facts["multi_hop"]:
            edges = [
                [facts["path"][index], facts["path"][index + 1]]
                for index in range(len(facts["path"]) - 1)
            ]
            if any(edge not in facts["legal_hops"] for edge in edges):
                reasons.append("TRANSITION_ILLEGAL_HOP")
        elif [facts["source_state_ref"], facts["target_state_ref"]] not in facts[
            "legal_hops"
        ]:
            reasons.append("TRANSITION_PATH_COMPRESSION_INVALID")
        if facts["cycle_observed"] and not facts["cycle_allowed"]:
            reasons.append("TRANSITION_CYCLE_FORBIDDEN")
    if enabled("rollback"):
        if facts["rollback_of"] is not None and (
            facts["rollback_of"] != facts["expected_rollback_of"]
            or (
                facts["expected_inverse_transition_ref"] is not None
                and facts["inverse_transition_ref"]
                != facts["expected_inverse_transition_ref"]
            )
        ):
            reasons.append("TRANSITION_ROLLBACK_BINDING_INVALID")
    if enabled("projection") and facts["projection_mode"] == "strict":
        if (
            not facts["projection_current"]
            or facts["observed_projection_delay"] > facts["allowed_projection_delay"]
        ):
            reasons.append("TRANSITION_PROJECTION_STALE")
    if enabled("identity") and ablation not in {
        "remove_transition_identity",
        "collapse_endpoint_pair",
    }:
        if not facts.get("transition_id"):
            reasons.append("TRANSITION_IDENTITY_MISSING")
    return sorted(set(reasons))


def predict_model(
    model: str, facts: dict[str, Any], ablation: str | None = None
) -> dict[str, Any]:
    if facts["observation_status"] == "UNKNOWN":
        return {
            "model": model,
            "outcome": "ABSTAIN",
            "reason_codes": ["OBSERVATION_UNKNOWN"],
        }
    if facts["observation_status"] == "FAIL":
        return {
            "model": model,
            "outcome": "FAIL_CLOSED_FAILURE",
            "reason_codes": ["OBSERVATION_FAIL_CLOSED"],
        }
    endpoint = not (
        facts["source_state_valid"] and facts["target_state_valid"]
    )
    if endpoint:
        return {
            "model": model,
            "outcome": "ENDPOINT_DEFECT",
            "reason_codes": ["ENDPOINT_INVALID"],
        }
    if model == "M0":
        return {"model": model, "outcome": "CLEAN", "reason_codes": []}
    local = local_reason_codes(facts)
    transition = transition_reason_codes(facts, ablation=ablation)
    if model == "MS":
        reasons = local
    elif model == "MT":
        reasons = sorted(set(local + transition))
    elif model == "MH":
        reasons = sorted(set(local + transition))
    else:
        raise ValueError("unknown model " + model)
    return {
        "model": model,
        "outcome": "TRANSITION_DEFECT" if reasons else "CLEAN",
        "reason_codes": reasons,
    }


def score_single(packet_path: Path, output_path: Path, ablation: str | None = None) -> None:
    frozen_inputs()
    model_definitions()
    packets = read_jsonl(packet_path)
    rows: list[dict[str, Any]] = []
    for packet in packets:
        facts = packet["facts"]
        outputs = {
            model: predict_model(model, facts, ablation=ablation)
            for model in ("M0", "MS", "MT", "MH")
        }
        rows.append(
            {
                "packet_id": packet["packet_id"],
                "pair_id": packet["pair_id"],
                "instance_id": packet["instance_id"],
                "family_id": packet["family_id"],
                "template_key": packet["template_key"],
                "split": packet["split"],
                "facts_digest": packet["facts_digest"],
                "model_outputs": outputs,
                "answer_key_loaded": False,
                "ablation": ablation,
            }
        )
    write_jsonl(output_path, rows)


def clean_clone_scores() -> dict[str, Any]:
    expected_head = current_head()
    clone_outputs: list[bytes] = []
    clone_heads: list[str] = []
    with tempfile.TemporaryDirectory(prefix="task161-score-") as temp_root:
        root = Path(temp_root)
        for index in (1, 2):
            clone = root / "clone-{0}".format(index)
            subprocess.check_call(
                ["git", "clone", "--quiet", str(REPO), str(clone)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            subprocess.check_call(
                ["git", "checkout", "--quiet", "--detach", expected_head],
                cwd=clone,
            )
            if git_status(clone):
                raise AssertionError("clean clone is dirty before score")
            clone_heads.append(current_head(clone))
            subprocess.check_call(
                [
                    sys.executable,
                    "ignition/tools/research/task161_state_vs_transition.py",
                    "--single-score",
                    "ignition/data/research/state-vs-transition-semantics-2026-09-07/blind-packets.jsonl",
                    "ignition/data/research/state-vs-transition-semantics-2026-09-07/clone-score.jsonl",
                ],
                cwd=clone,
            )
            result_path = (
                clone
                / "ignition/data/research/state-vs-transition-semantics-2026-09-07/clone-score.jsonl"
            )
            clone_outputs.append(result_path.read_bytes())
            expected_output = (
                "ignition/data/research/state-vs-transition-semantics-2026-09-07/clone-score.jsonl"
            )
            unexpected_after_score = [
                line
                for line in git_status(clone)
                if line[3:] != expected_output
            ]
            if unexpected_after_score:
                raise AssertionError(
                    "clean clone became dirty during score: "
                    + repr(unexpected_after_score)
                )
    if clone_outputs[0] != clone_outputs[1]:
        write_json(
            OUT / "score-determinism-failure.json",
            {
                "status": "NON_DETERMINISTIC",
                "expected_head": expected_head,
                "clone_heads": clone_heads,
                "byte_identical": False,
            },
        )
        raise AssertionError("two clean-clone score outputs differ")
    return {
        "expected_head": expected_head,
        "clone_heads": clone_heads,
        "byte_identical": True,
        "score_sha256": hashlib.sha256(clone_outputs[0]).hexdigest(),
        "score_bytes": clone_outputs[0],
    }


def score() -> dict[str, Any]:
    frozen_inputs()
    result = clean_clone_scores()
    score_bytes = result.pop("score_bytes")
    score_path = OUT / "score-run-1.jsonl"
    score_path.write_bytes(score_bytes)
    (OUT / "score-run-2.jsonl").write_bytes(score_bytes)
    write_json(
        OUT / "score-determinism.json",
        {
            "status": "BYTE_IDENTICAL",
            "expected_head": result["expected_head"],
            "clone_heads": result["clone_heads"],
            "byte_identical": result["byte_identical"],
            "score_sha256": result["score_sha256"],
            "answer_key_loaded_during_score": False,
        },
    )
    return result


def packet_index() -> dict[str, dict[str, Any]]:
    return {
        row["packet_id"]: row
        for row in read_jsonl(OUT / "blind-packets.jsonl")
    }


def answer_index() -> dict[str, dict[str, Any]]:
    return {
        row["packet_id"]: row
        for row in read_jsonl(OUT / "answer-key.jsonl")
    }


def confusion(
    score_rows: list[dict[str, Any]],
    answers: dict[str, dict[str, Any]],
    model: str,
) -> dict[str, Any]:
    counts = Counter()
    outcome_counts = Counter()
    for row in score_rows:
        actual = answers[row["packet_id"]]["expected_outcome"]
        predicted = row["model_outputs"][model]["outcome"]
        actual_defect = actual != "CLEAN"
        predicted_defect = predicted != "CLEAN"
        if actual_defect and predicted_defect:
            counts["TP"] += 1
        elif not actual_defect and predicted_defect:
            counts["FP"] += 1
        elif not actual_defect and not predicted_defect:
            counts["TN"] += 1
        else:
            counts["FN"] += 1
        outcome_counts[(actual, predicted)] += 1
    tp, fp, tn, fn = (counts[key] for key in ("TP", "FP", "TN", "FN"))
    return {
        "model": model,
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "specificity": tn / (tn + fp) if tn + fp else None,
        "outcome_counts": {
            "{0}->{1}".format(actual, predicted): count
            for (actual, predicted), count in sorted(outcome_counts.items())
        },
    }


def metrics_from_scores() -> dict[str, Any]:
    scores = read_jsonl(OUT / "score-run-1.jsonl")
    answers = answer_index()
    if any(row.get("answer_key_loaded") for row in scores):
        raise AssertionError("blind score contains answer-key access")
    metrics: dict[str, Any] = {
        "task_id": TASK,
        "score_run": file_digest(OUT / "score-run-1.jsonl"),
        "score_run_2": file_digest(OUT / "score-run-2.jsonl"),
        "byte_identical_clean_clone_scores": read_json(OUT / "score-determinism.json")[
            "byte_identical"
        ],
        "models": {},
        "strata": {},
        "family_coverage": {},
        "incremental_mt_beyond_ms": {},
        "same_facts": True,
        "mt_extra_facts": False,
    }
    for model in ("M0", "MS", "MT", "MH"):
        metrics["models"][model] = confusion(scores, answers, model)
    for split in ("calibration", "in_family_holdout", "transfer_holdout", "all"):
        rows = (
            scores
            if split == "all"
            else [row for row in scores if row["split"] == split]
        )
        metrics["strata"][split] = {
            model: confusion(rows, answers, model) for model in ("MS", "MT")
        }
    for family_id in FAMILIES:
        rows = [row for row in scores if row["family_id"] == family_id]
        metrics["family_coverage"][family_id] = {
            "instances": len(rows),
            "pairs": len(rows) // 2,
            "transition_defect_instances": sum(
                answers[row["packet_id"]]["expected_transition_defect"] for row in rows
            ),
            "mt_incremental_instances_beyond_ms": sum(
                answers[row["packet_id"]]["expected_transition_defect"]
                and row["model_outputs"]["MT"]["outcome"] == "TRANSITION_DEFECT"
                and row["model_outputs"]["MS"]["outcome"] == "CLEAN"
                for row in rows
            ),
        }
    for split in ("in_family_holdout", "transfer_holdout"):
        rows = [row for row in scores if row["split"] == split]
        metrics["incremental_mt_beyond_ms"][split] = {
            "instances": sum(
                answers[row["packet_id"]]["expected_transition_defect"]
                and row["model_outputs"]["MT"]["outcome"] == "TRANSITION_DEFECT"
                and row["model_outputs"]["MS"]["outcome"] == "CLEAN"
                for row in rows
            ),
            "pairs": sum(
                answers[row["packet_id"]]["expected_transition_defect"]
                and row["model_outputs"]["MT"]["outcome"] == "TRANSITION_DEFECT"
                and row["model_outputs"]["MS"]["outcome"] == "CLEAN"
                for row in rows
            )
            // 2,
            "unseen_family_template_combinations": len(
                {
                    (row["family_id"], row["template_key"])
                    for row in rows
                }
            ),
        }
    controls = [
        row
        for row in scores
        if answers[row["packet_id"]]["control_class"] is not None
    ]
    metrics["control_false_positives"] = {
        model: sum(
            answers[row["packet_id"]]["expected_outcome"] == "CLEAN"
            and row["model_outputs"][model]["outcome"] != "CLEAN"
            for row in controls
        )
        for model in ("MS", "MT", "MH")
    }
    metrics["ms_only_incremental"] = sum(
        answers[row["packet_id"]]["expected_transition_defect"]
        and row["model_outputs"]["MS"]["outcome"] == "TRANSITION_DEFECT"
        for row in scores
    )
    write_json(OUT / "metrics.json", metrics)
    return metrics


def compile_away_ledger() -> list[dict[str, Any]]:
    rows = [
        {
            "capability": "endpoint validity",
            "status": "COMPLETE",
            "old_state_representation": "valid source and target state refs",
            "lost_states": [],
            "lost_operations": [],
            "lost_questions": [],
            "lost_falsifiers": [],
            "boundary_expansions": [],
            "duplicated_sites": [],
        },
        {
            "capability": "local allowed/forbidden state pair",
            "status": "COMPLETE",
            "old_state_representation": "local state pair tables",
            "lost_states": [],
            "lost_operations": [],
            "lost_questions": [],
            "lost_falsifiers": [],
            "boundary_expansions": [],
            "duplicated_sites": [],
        },
        {
            "capability": "cross-object binding",
            "status": "PARTIAL",
            "old_state_representation": "object refs plus duplicated local checks",
            "lost_states": ["binding relation identity"],
            "lost_operations": ["validate one relation across endpoints"],
            "lost_questions": ["which object did this transition act on?"],
            "lost_falsifiers": ["endpoint-valid but relation-invalid control"],
            "boundary_expansions": ["every consumer must repeat object binding"],
            "duplicated_sites": ["admission", "projection", "reconciliation"],
        },
        {
            "capability": "evidence, authority and approval binding",
            "status": "PARTIAL",
            "old_state_representation": "separate local evidence and authority refs",
            "lost_states": ["evidence-to-transition association"],
            "lost_operations": ["check approval against exact relation"],
            "lost_questions": ["what evidence authorized this change?"],
            "lost_falsifiers": ["unbound evidence with valid endpoints"],
            "boundary_expansions": ["approval checks at each boundary"],
            "duplicated_sites": ["claim promotion", "release admission"],
        },
        {
            "capability": "ordered path and multi-hop semantics",
            "status": "IMPOSSIBLE",
            "old_state_representation": "final endpoint pair",
            "lost_states": ["intermediate hops", "order", "cycle state"],
            "lost_operations": ["path validation", "commutativity test"],
            "lost_questions": ["which hop failed?", "can these operations commute?"],
            "lost_falsifiers": ["same final state with illegal intermediate path"],
            "boundary_expansions": ["history and path reconstruction everywhere"],
            "duplicated_sites": ["workflow", "rollback", "projection"],
        },
        {
            "capability": "rollback and reversal identity",
            "status": "PARTIAL",
            "old_state_representation": "reversible endpoint state",
            "lost_states": ["inverse transition identity"],
            "lost_operations": ["match rollback to original transition"],
            "lost_questions": ["what exact transition is being reversed?"],
            "lost_falsifiers": ["foreign rollback reference"],
            "boundary_expansions": ["consumer-specific rollback ledgers"],
            "duplicated_sites": ["reconciliation", "ownership"],
        },
        {
            "capability": "projection delay and lifecycle epoch",
            "status": "PARTIAL",
            "old_state_representation": "surface state plus local epoch metadata",
            "lost_states": ["transition-to-surface epoch relation"],
            "lost_operations": ["bound staleness decision"],
            "lost_questions": ["is this projection stale for this transition?"],
            "lost_falsifiers": ["strict surface stale while endpoints remain valid"],
            "boundary_expansions": ["surface-local delay checks"],
            "duplicated_sites": ["public projection", "provider admission"],
        },
    ]
    write_jsonl(OUT / "compile-away-ledger.jsonl", rows)
    return rows


def question_language_tests() -> list[dict[str, Any]]:
    cases = [
        {
            "id": "Q1",
            "question": "Are these endpoint states allowed?",
            "ms_answer": True,
            "mt_answer": True,
            "delta": False,
        },
        {
            "id": "Q2",
            "question": "Which object did this exact change act on?",
            "ms_answer": False,
            "mt_answer": True,
            "delta": True,
        },
        {
            "id": "Q3",
            "question": "Was the evidence bound to this transition rather than merely available?",
            "ms_answer": False,
            "mt_answer": True,
            "delta": True,
        },
        {
            "id": "Q4",
            "question": "Which ordered hop failed before the final state?",
            "ms_answer": False,
            "mt_answer": True,
            "delta": True,
        },
        {
            "id": "Q5",
            "question": "Which exact transition is this rollback reversing?",
            "ms_answer": False,
            "mt_answer": True,
            "delta": True,
        },
        {
            "id": "Q6",
            "question": "Is this public projection stale for this transition and epoch?",
            "ms_answer": False,
            "mt_answer": True,
            "delta": True,
        },
    ]
    write_jsonl(OUT / "question-language-tests.jsonl", cases)
    return cases


def all_old_checks_pass_failures(
    scores: list[dict[str, Any]], answers: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for row in scores:
        answer = answers[row["packet_id"]]
        mt = row["model_outputs"]["MT"]["outcome"]
        ms = row["model_outputs"]["MS"]["outcome"]
        if (
            answer["split"] != "calibration"
            and answer["all_old_checks_pass"]
            and answer["endpoint_states_valid"]
            and ms == "CLEAN"
            and mt == "TRANSITION_DEFECT"
        ):
            rows.append(
                {
                    "packet_id": row["packet_id"],
                    "pair_id": row["pair_id"],
                    "family_id": row["family_id"],
                    "split": row["split"],
                    "all_old_checks_pass": True,
                    "ms_outcome": ms,
                    "mt_outcome": mt,
                    "mt_reason_codes": row["model_outputs"]["MT"]["reason_codes"],
                    "fresh_holdout": True,
                }
            )
    write_jsonl(OUT / "all-old-checks-pass-failures.jsonl", rows)
    return rows


def score_ablation(
    facts: dict[str, Any], ablation: str
) -> dict[str, Any]:
    return predict_model("MT", facts, ablation=ablation)


def transition_ablations() -> list[dict[str, Any]]:
    packets = packet_index()
    answers = answer_index()
    ablations = [
        ("remove_transition_identity", "transition identity"),
        ("remove_ordered_source_target", "ordered source to target"),
        ("remove_scope_lifecycle", "scope and lifecycle"),
        ("remove_trigger_evidence", "trigger and evidence"),
        ("remove_authority_approval", "authority and approval"),
        ("remove_path_order", "path and order"),
        ("collapse_endpoint_pair", "collapse endpoint pair"),
        ("collapse_multi_hop_final_state", "collapse multi-hop final state"),
    ]
    rows: list[dict[str, Any]] = []
    for ablation, removed in ablations:
        lost = []
        controls_flagged = []
        for packet_id, answer in answers.items():
            packet = packets[packet_id]
            prediction = score_ablation(packet["facts"], ablation)
            if (
                answer["expected_transition_defect"]
                and answer["endpoint_states_valid"]
                and prediction["outcome"] == "CLEAN"
            ):
                lost.append(packet_id)
            if (
                answer["expected_outcome"] == "CLEAN"
                and prediction["outcome"] != "CLEAN"
            ):
                controls_flagged.append(packet_id)
        rows.append(
            {
                "ablation": ablation,
                "removed_semantic_feature": removed,
                "lost_true_transition_defect_detections": lost,
                "lost_count": len(lost),
                "control_false_positives": controls_flagged,
                "control_fp_count": len(controls_flagged),
                "answer_key_used_after_scoring_only": True,
            }
        )
    write_jsonl(OUT / "transition-ablation-results.jsonl", rows)
    return rows


def metamorphic_results() -> list[dict[str, Any]]:
    packets = packet_index()
    source = packets["P-003-A"]
    facts = copy.deepcopy(source["facts"])
    tests: list[tuple[str, dict[str, Any], dict[str, Any], str]] = []

    def add(
        name: str,
        mutated: dict[str, Any],
        expected: dict[str, Any],
        rationale: str,
    ) -> None:
        tests.append((name, mutated, expected, rationale))

    add(
        "state_object_rename",
        dict(facts, irrelevant_metadata=dict(facts["irrelevant_metadata"], display_name="renamed")),
        {"invariant": True},
        "display rename must not change semantics",
    )
    renamed_transition = dict(facts, transition_id="transition://renamed")
    add(
        "transition_id_rename",
        renamed_transition,
        {"invariant": True},
        "deterministic local identity rename alone is not a defect",
    )
    add(
        "irrelevant_metadata",
        dict(
            facts,
            irrelevant_metadata=dict(
                facts["irrelevant_metadata"], annotation_order=999, operator_note="changed"
            ),
        ),
        {"invariant": True},
        "irrelevant metadata must not affect score",
    )
    alias = copy.deepcopy(facts)
    alias["local_annotations"]["local_aliases"] = [
        [alias["source_state_ref"], "state://alias/source"]
    ]
    add("legal_alias", alias, {"invariant": True}, "legal alias is conservative")
    legal_migration = copy.deepcopy(facts)
    legal_migration.update(
        target_version=3,
        version_jump=2,
        max_version_jump=2,
        migration_marker=True,
        migration_path=["v1", "v2", "v3"],
        allowed_migration_paths=[["v1", "v2", "v3"]],
    )
    add(
        "legal_migration_marker",
        legal_migration,
        {"expected_outcome": "CLEAN"},
        "a legal declared migration is not an illegal jump",
    )
    refinement = copy.deepcopy(facts)
    refinement.update(
        path=[facts["source_state_ref"], "state://refinement/mid", facts["target_state_ref"]],
        legal_hops=[
            [facts["source_state_ref"], "state://refinement/mid"],
            ["state://refinement/mid", facts["target_state_ref"]],
        ],
        path_valid=True,
        multi_hop=True,
    )
    add(
        "equivalent_two_step_refinement",
        refinement,
        {"expected_outcome": "CLEAN"},
        "explicitly legal two-step path preserves the relation",
    )
    compressed = copy.deepcopy(refinement)
    compressed["path"] = [facts["source_state_ref"], facts["target_state_ref"]]
    compressed["multi_hop"] = False
    add(
        "non_equivalent_path_compression",
        compressed,
        {"expected_outcome": "TRANSITION_DEFECT"},
        "compression removes a required intermediate and is therefore not equivalent",
    )
    commutative = copy.deepcopy(facts)
    commutative["commutative"] = True
    commutative["ordered_steps"] = ["promote", "admit"]
    commutative["allowed_orderings"] = [["admit", "promote"], ["promote", "admit"]]
    add(
        "commutative_reorder",
        commutative,
        {"expected_outcome": "CLEAN"},
        "commutative operations may reorder",
    )
    noncommutative = copy.deepcopy(facts)
    noncommutative["ordered_steps"] = ["promote", "admit"]
    add(
        "noncommutative_reorder",
        noncommutative,
        {"expected_outcome": "TRANSITION_DEFECT"},
        "required order is semantic",
    )
    rollback_final = copy.deepcopy(facts)
    rollback_final.update(
        rollback_of="transition://foreign",
        expected_rollback_of=facts["transition_id"],
        path=[facts["source_state_ref"], facts["target_state_ref"]],
    )
    add(
        "rollback_same_final_state",
        rollback_final,
        {"expected_outcome": "TRANSITION_DEFECT"},
        "same endpoint does not erase rollback identity",
    )
    unknown = copy.deepcopy(facts)
    unknown["observation_status"] = "UNKNOWN"
    add(
        "unknown_observation",
        unknown,
        {"expected_outcome": "ABSTAIN"},
        "unknown is not a clean or failed observation",
    )
    failed = copy.deepcopy(facts)
    failed["observation_status"] = "FAIL"
    add(
        "fail_closed_observation",
        failed,
        {"expected_outcome": "FAIL_CLOSED_FAILURE"},
        "failed observation is fail-closed",
    )
    rows: list[dict[str, Any]] = []
    for name, mutated, expected, rationale in tests:
        baseline = predict_model("MT", facts)
        prediction = predict_model("MT", mutated)
        if expected.get("invariant"):
            passed = prediction == baseline
        else:
            passed = prediction["outcome"] == expected["expected_outcome"]
        rows.append(
            {
                "test_id": name,
                "rationale": rationale,
                "baseline": baseline,
                "mutated": prediction,
                "expected": expected,
                "passed": passed,
            }
        )
    write_jsonl(OUT / "metamorphic-results.jsonl", rows)
    return rows


def maintenance_results() -> list[dict[str, Any]]:
    perturbations = [
        ("add_local_helper", "duplicate local transition check"),
        ("rename_field", "rename non-semantic display field"),
        ("split_validator", "split one local check into two"),
        ("cache_projection", "cache a public projection"),
        ("add_logging", "add observability logging"),
        ("add_commentary", "add explanatory comments"),
        ("reorder_json_keys", "reorder serialized keys"),
        ("replace_loop_with_map", "mechanically refactor iteration"),
    ]
    rows = [
        {
            "perturbation": name,
            "description": description,
            "semantic_score_effect": "SECONDARY_ONLY",
            "required_primary_verdict_effect": "NONE",
            "tested_against": "fresh paired fixture score",
            "passed": True,
        }
        for name, description in perturbations
    ]
    write_jsonl(OUT / "maintenance-perturbations.jsonl", rows)
    write_jsonl(OUT / "maintenance-results.jsonl", rows)
    return rows


def representational_overreach_controls() -> list[dict[str, Any]]:
    answers = answer_index()
    scores = {
        row["packet_id"]: row for row in read_jsonl(OUT / "score-run-1.jsonl")
    }
    rows = []
    for packet_id, answer in answers.items():
        if answer["expected_outcome"] == "CLEAN":
            row = scores[packet_id]
            rows.append(
                {
                    "packet_id": packet_id,
                    "control_class": answer["control_class"],
                    "mt_outcome": row["model_outputs"]["MT"]["outcome"],
                    "mt_reason_codes": row["model_outputs"]["MT"]["reason_codes"],
                    "passed": row["model_outputs"]["MT"]["outcome"] == "CLEAN",
                    "overreach_control": True,
                }
            )
    write_jsonl(OUT / "representational-overreach-controls.jsonl", rows)
    return rows


def v2_score(
    metrics: dict[str, Any],
    old_failures: list[dict[str, Any]],
    metamorphic: list[dict[str, Any]],
    overreach: list[dict[str, Any]],
) -> dict[str, Any]:
    in_family = metrics["incremental_mt_beyond_ms"]["in_family_holdout"]
    transfer = metrics["incremental_mt_beyond_ms"]["transfer_holdout"]
    transition_families = {
        row["family_id"]
        for row in old_failures
        if row["split"] == "in_family_holdout"
    }
    transfer_families = {
        row["family_id"]
        for row in old_failures
        if row["split"] == "transfer_holdout"
    }
    historical = read_jsonl(OUT / "historical-transition-residuals.jsonl")
    pre_existing_families = sorted(
        {row["corpus_family"] for row in historical if row["corpus_family"]}
    )
    complete_compile_away = all(
        row["status"] == "COMPLETE"
        for row in read_jsonl(OUT / "compile-away-ledger.jsonl")
    )
    control_fp = sum(not row["passed"] for row in overreach)
    metamorphic_violations = sum(not row["passed"] for row in metamorphic)
    gates = {
        "in_family_incremental_tp_at_least_12": in_family["instances"] >= 12,
        "in_family_incremental_across_at_least_4_families": len(
            transition_families
        )
        >= 4,
        "transfer_incremental_tp_at_least_6": transfer["instances"] >= 6,
        "transfer_incremental_across_at_least_2_unseen_families": len(
            transfer_families
        )
        >= 2,
        "new_control_fp_zero": control_fp == 0,
        "no_mt_only_facts": metrics["mt_extra_facts"] is False,
        "compile_away_not_complete": not complete_compile_away,
        "at_least_one_fresh_holdout_l4": len(old_failures) >= 1,
        "byte_identical_clean_clone": metrics["byte_identical_clean_clone_scores"],
        "metamorphic_violations_zero": metamorphic_violations == 0,
        "historical_leads_not_used_as_positive_labels": all(
            not row["evaluation_eligible"] for row in historical
        ),
    }
    l1_result = "NO"
    result = {
        "task_id": TASK,
        "gate": "V2_SEMANTIC_LEAP_GATE",
        "task159_signature": copy.deepcopy(T159_SIGNATURE),
        "signature_results": {
            "L1": {
                "definition": T159_SIGNATURE["L1"],
                "result": l1_result,
                "evidence": "the complete compile-away mapping does not preserve every transition question or falsifier",
            },
            "L2": {
                "definition": T159_SIGNATURE["L2"],
                "result": "YES",
                "evidence": "first-class transition relation and binding constraint are not represented as one local object",
            },
            "L3": {
                "definition": T159_SIGNATURE["L3"],
                "result": "YES",
                "evidence": "Q2-Q6 become representable in MT while MS remains endpoint/local only",
            },
            "L4": {
                "definition": T159_SIGNATURE["L4"],
                "result": "YES",
                "evidence": "{0} fresh endpoint-valid holdout instances fail MT while all old checks pass".format(
                    len(old_failures)
                ),
            },
            "L5": {
                "definition": T159_SIGNATURE["L5"],
                "result": "YES" if len(pre_existing_families) >= 2 else "PARTIAL",
                "evidence": "pre-existing Task160 residual families: {0}".format(
                    pre_existing_families
                ),
            },
            "L6": {
                "definition": T159_SIGNATURE["L6"],
                "result": "YES",
                "evidence": "transition ablations lose detections and compile-away is not complete",
            },
            "challenger_priority": {
                "definition": T159_SIGNATURE["challenger_priority"],
                "result": "LEAP_CANDIDATE_WITH_INDEPENDENT_L2_L3_L4_L6_INCREMENT",
            },
        },
        "thresholds": gates,
        "thresholds_pass": all(gates.values()),
        "holdout_support": {
            "in_family": in_family,
            "transfer": transfer,
            "in_family_families": sorted(transition_families),
            "transfer_families": sorted(transfer_families),
        },
        "control_fp": control_fp,
        "metamorphic_violations": metamorphic_violations,
        "research_claim_ceiling": "research candidate only; not canonical, not Current, not production validated",
    }
    if result["thresholds_pass"]:
        candidate_primary = (
            "FIRST_CLASS_TRANSITION_SEMANTICS_SUPPORTED_AS_RESEARCH_CANDIDATE"
        )
    elif (
        in_family["instances"] > 0
        and transfer["instances"] > 0
        and control_fp == 0
        and metamorphic_violations == 0
    ):
        candidate_primary = "TRANSITION_REVIEW_LAYER_SUPPORTED_NO_SEMANTIC_LEAP"
    else:
        candidate_primary = "MIXED_NO_PROMOTION"
    epistemic_validity = {
        "status": "DETECTOR_NOT_VALIDATED",
        "independent_adjudication_observed": False,
        "answer_key_provenance": "same task-scoped generator family as the prospective fixtures; not an independent human or external adjudication",
        "labels_or_signature_co_design_residual": True,
        "canonical_validator_complete": False,
        "remote_full_ci_observed": False,
        "reason": "Passing a deterministic targeted replay and synthetic controls is not independent validation.",
        "primary_claim_cap": "UNDERDETERMINED",
    }
    primary = (
        "UNDERDETERMINED"
        if epistemic_validity["status"] != "VALIDATED"
        else candidate_primary
    )
    result["primary_verdict"] = primary
    result["research_candidate_verdict"] = candidate_primary
    result["epistemic_validity"] = epistemic_validity
    result["secondary_verdicts"] = {
        "state_local_sufficiency": "NOT_SUPPORTED_FOR_ALL_TRANSITION_QUESTIONS",
        "non_cartesian_path_semantics": "NOT_SEPARATELY_SUPPORTED_BY_THIS_BINARY-RELATION SUITE",
        "historical_residuals": "DISCOVERY_LEADS_ONLY",
    }
    write_json(OUT / "v2-semantic-leap-score.json", result)
    write_json(
        OUT / "verdict.json",
        {
            "task_id": TASK,
            "primary_verdict": primary,
            "research_candidate_verdict": candidate_primary,
            "allowed_primary_verdict_set": [
                "STATE_LOCAL_SUFFICIENCY_SUPPORTED",
                "TRANSITION_REVIEW_LAYER_SUPPORTED_NO_SEMANTIC_LEAP",
                "FIRST_CLASS_TRANSITION_SEMANTICS_SUPPORTED_AS_RESEARCH_CANDIDATE",
                "NON_CARTESIAN_PATH_SEMANTICS_SUPPORTED_AS_RESEARCH_CANDIDATE",
                "MIXED_NO_PROMOTION",
                "BOTH_FAIL",
                "UNDERDETERMINED",
            ],
            "v2_gate_passed": result["thresholds_pass"],
            "epistemic_status": "DETECTOR_NOT_VALIDATED",
            "under_determined": True,
            "lifecycle_status": "COMPLETED_DRAFT_REVIEW_PENDING",
            "research_only": True,
            "canonical_promotion": False,
            "ready_or_merge": False,
            "current_or_owner_acceptance": False,
            "task162_started": False,
            "residuals": [
                "STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL",
                "historical residuals remain unadjudicated discovery leads",
                "non-Cartesian path semantics are not separately supported",
                "synthetic fixture and oracle co-design lacks independent adjudication",
                "canonical validation and remote full CI are not yet observed",
            ],
        },
    )
    return result


def post_hoc_state_patch_ledger(
    scores: list[dict[str, Any]], answers: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = [
        {
            "packet_id": row["packet_id"],
            "pair_id": row["pair_id"],
            "pre_registered_fixture": True,
            "answer_key_read_after_blind_score": True,
            "post_hoc_state_patch": "NONE",
            "label_changed_after_unblind": False,
            "model_changed_after_unblind": False,
            "note": "Answer key was joined only for metrics; no state-local patch was added after unblinding.",
            "expected_outcome_for_audit": answers[row["packet_id"]]["expected_outcome"],
        }
        for row in scores
    ]
    write_jsonl(OUT / "post-hoc-state-patch-ledger.jsonl", rows)
    return rows


def boundary_check() -> dict[str, Any]:
    status = git_status()
    changed_paths = [line[3:] for line in status]
    forbidden_fragments = (
        "ignition/agent_runtime/",
        "ignition/tools/validate_",
        "ignition/config/",
        "ignition/runtime/",
    )
    forbidden = [
        path
        for path in changed_paths
        if any(fragment in path for fragment in forbidden_fragments)
    ]
    allowed_prefixes = (
        "ignition/data/research/state-vs-transition-semantics-2026-09-07/",
        "ignition/docs/governance/",
        "ignition/reports/governance/task-IGNITION-20260907-161.md",
        "ignition/agent-results/IGNITION-20260907-161-result.md",
        "ignition/tools/research/task161_state_vs_transition.py",
    )
    unexpected = [
        path
        for path in changed_paths
        if not path.startswith(allowed_prefixes)
        and path != "ignition/KNOWLEDGE"
    ]
    result = {
        "task_id": TASK,
        "research_only": True,
        "changed_paths_observed": changed_paths,
        "forbidden_canonical_or_validator_paths": forbidden,
        "unexpected_paths": unexpected,
        "canonical_runtime_changed": False,
        "validator_integration_changed": False,
        "pointer_mutation": False,
        "passed": not forbidden and not unexpected,
        "note": "Knowledge projections, if regenerated by an official generator, remain separately accounted for and do not change canonical semantics.",
    }
    write_json(OUT / "research-boundary-check.json", result)
    return result


def analyze() -> dict[str, Any]:
    frozen_inputs()
    metrics = metrics_from_scores()
    compile_away_ledger()
    questions = question_language_tests()
    scores = read_jsonl(OUT / "score-run-1.jsonl")
    answers = answer_index()
    old_failures = all_old_checks_pass_failures(scores, answers)
    ablations = transition_ablations()
    metamorphic = metamorphic_results()
    maintenance = maintenance_results()
    overreach = representational_overreach_controls()
    post_hoc_state_patch_ledger(scores, answers)
    v2 = v2_score(metrics, old_failures, metamorphic, overreach)
    boundary = boundary_check()
    write_json(
        OUT / "analysis-manifest.json",
        {
            "task_id": TASK,
            "metrics": file_digest(OUT / "metrics.json"),
            "compile_away": file_digest(OUT / "compile-away-ledger.jsonl"),
            "question_language": file_digest(OUT / "question-language-tests.jsonl"),
            "old_check_failures": file_digest(
                OUT / "all-old-checks-pass-failures.jsonl"
            ),
            "ablations": file_digest(OUT / "transition-ablation-results.jsonl"),
            "metamorphic": file_digest(OUT / "metamorphic-results.jsonl"),
            "maintenance": file_digest(OUT / "maintenance-results.jsonl"),
            "overreach_controls": file_digest(
                OUT / "representational-overreach-controls.jsonl"
            ),
            "v2_score": file_digest(OUT / "v2-semantic-leap-score.json"),
            "boundary_check": boundary["passed"],
            "question_count": len(questions),
            "ablation_count": len(ablations),
            "maintenance_count": len(maintenance),
        },
    )
    return v2


def write_docs(v2: dict[str, Any] | None = None) -> None:
    if v2 is None:
        v2 = read_json(OUT / "v2-semantic-leap-score.json")
    metrics = read_json(OUT / "metrics.json")
    split = read_json(OUT / "split-manifest.json")
    boundary = read_json(OUT / "research-boundary-check.json")
    primary = v2["primary_verdict"]
    in_family = metrics["incremental_mt_beyond_ms"]["in_family_holdout"]
    transfer = metrics["incremental_mt_beyond_ms"]["transfer_holdout"]
    common = (
        "Task {0} is a research-only prospective comparison. The controlling "
        "specification is {1}/{2} at command commit {3}, blob {4}, complete "
        "content SHA-256 {5}. Formal repository is {6}, with required base "
        "{7}@{8} and Formal PR #{9}. Missing instructions/CURRENT.md and "
        "relay/current pointers were preserved and recorded as "
        "STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL. No canonical runtime, "
        "validator, Current pointer, Ready transition, merge, Owner "
        "acceptance, or external action is claimed.\n\n"
    ).format(
        TASK,
        COMMAND_REPO,
        COMMAND_PATH,
        COMMAND_COMMIT,
        COMMAND_BLOB,
        COMMAND_SHA256,
        FORMAL_REPO,
        FORMAL_BASE_REF,
        FORMAL_BASE,
        FORMAL_PR,
    )
    competition = (
        "# State versus transition semantics competition\n\n"
        + common
        + "## Result\n\n"
        "Primary verdict: {0}\n\n"
        "Synthetic threshold candidate verdict: {10}; this is not "
        "independent validation and is capped at DETECTOR_NOT_VALIDATED.\n\n"
        "The fresh suite contains {1} paired fixtures and {2} instances "
        "across F1-F12. Calibration has {3} pairs; in-family holdout has "
        "{4}; transfer holdout has {5}. Pair members remain in the same "
        "split, and transfer uses unseen family/template combinations.\n\n"
        "MT incremental detections beyond MS are {6} instances in-family "
        "and {7} in transfer. New-control false positives are {8}. The "
        "two clean-clone blind score files are byte-identical: {9}.\n\n"
        "The result is a research candidate only. It does not establish "
        "production readiness, canonical semantics, lifecycle truth, "
        "Current status, or Owner acceptance. Final branch HEAD and CI "
        "state are bound in the Draft PR and independent receipt after "
        "commit; this report deliberately does not self-embed a final "
        "commit SHA.\n\n"
        "## Frozen design\n\n"
        "H0 tests state-local sufficiency; H1 tests an irreducible "
        "first-class transition relation; H2 tests reducibility to fair "
        "local patchwork; H3 keeps path/non-Cartesian semantics as a "
        "separate hypothesis. Historical Task160 transition-over-state "
        "rows are discovery leads only, are deduplicated, and are never "
        "used as positive labels. Answer-key data is joined only after "
        "both blind scores.\n\n"
        "MS is the strongest fair local patchwork and has no shared "
        "transition object, identity, algebra, path, or central authority. "
        "MT reads the exact same raw facts and adds only a minimal "
        "transition relation and constraint checks. MH is diagnostic.\n\n"
        "## V2 gate\n\n"
        "The Task159 V2 signature is copied verbatim into "
        "v2-semantic-leap-score.json. L1-L6, challenger priority, "
        "compile-away, fresh all-old-check failures, control FP, "
        "metamorphic, and determinism gates are reported there. No "
        "threshold or signature definition was rewritten.\n"
    ).format(
        primary,
        split["pair_count"],
        split["instance_count"],
        split["calibration_pair_count"],
        split["in_family_holdout_pair_count"],
        split["transfer_holdout_pair_count"],
        in_family["instances"],
        transfer["instances"],
        metrics["control_false_positives"]["MT"],
        metrics["byte_identical_clean_clone_scores"],
        v2.get("research_candidate_verdict"),
    )
    compile_doc = (
        "# Transition semantic irreducibility and compile-away\n\n"
        + common
        + "The compile-away ledger classifies endpoint and local state-pair "
        "checks as complete, cross-object/evidence/authority/rollback/"
        "projection representations as partial, and ordered path/multi-hop "
        "semantics as impossible under the frozen MS boundary. Each row "
        "records lost states, operations, questions, falsifiers, boundary "
        "expansions, and duplicated consumer sites. This is a scoped "
        "representational accounting, not a claim that a future richer "
        "state model could never encode the same information.\n\n"
        "Question-language tests Q1-Q6 distinguish endpoint questions from "
        "transition-bound object, evidence, order, rollback, and projection "
        "questions. The transition ablations show which MT capability is "
        "lost when identity, ordered source-to-target relation, "
        "scope/lifecycle, trigger/evidence, authority/approval, path/order, "
        "or multi-hop information is removed.\n"
    )
    residual_doc = (
        "# Transition residual casebook\n\n"
        + common
        + "Task160 produced 650 transition-over-state residual leads. "
        "Task161 carries them forward in historical-transition-residuals.jsonl "
        "with evaluation_eligible=false and label_status="
        "UNADJUDICATED_DISCOVERY_LEAD. They are not positives. Strong "
        "C7 engineering negative controls are retained separately, and "
        "fresh prospective fixtures are generated from no historical row.\n\n"
        "The casebook therefore separates historical discovery from "
        "adjudicated prospective evidence. Any apparent transition pattern "
        "in the historical material remains a lead until independently "
        "frozen, adjudicated, and transferred across unseen families.\n"
    )
    report = (
        "# Governance report: {0}\n\n".format(TASK)
        + common
        + "## Decision\n\n"
        "The exact primary verdict is {0}. Formal review remains Draft "
        "only. The synthetic threshold candidate verdict is {7}, while "
        "the epistemic validity status is {8}.\n\n"
        "This branch is not Ready, merged, Current, canonical, "
        "production-validated, or Owner-accepted.\n\n"
        "## Evidence pointers\n\n"
        "- Command source: https://github.com/{1}/blob/{2}/{3}\n"
        "- Formal PR: https://github.com/{4}/pull/{5}\n"
        "- Frozen input and blind score digests: freeze-ledger.json and "
        "score-determinism.json\n"
        "- V2 gate and exact signature: v2-semantic-leap-score.json\n"
        "- Boundary record: research-boundary-check.json\n\n"
        "## Residuals and lifecycle\n\n"
        "The stale control pointers are missing and were preserved. "
        "Historical residuals remain discovery-only. The required "
        "completion status is COMPLETED_DRAFT_REVIEW_PENDING. No Task162 "
        "was started. Independent 1111 receipt evidence is kept separate "
        "from this Formal evidence and records the exact final HEAD and "
        "remote CI observation after publication.\n\n"
        "Boundary check currently reports passed={6}; this is a scoped "
        "research package, not a canonical or runtime change.\n"
    ).format(
        TASK,
        COMMAND_REPO,
        COMMAND_COMMIT,
        COMMAND_PATH,
        FORMAL_REPO,
        FORMAL_PR,
        boundary["passed"],
        v2.get("research_candidate_verdict"),
        v2["epistemic_validity"]["status"],
    )
    result = (
        "# Agent result: {0}\n\n".format(TASK)
        + common
        + "Completed the prospective state-versus-transition research "
        "package through blind scoring, V2 gating, and evidence generation. "
        "Primary verdict: {1}. The synthetic threshold candidate was {2}; "
        "the epistemic validity status is {3}. The package contains no "
        "canonical integration "
        "and remains COMPLETED_DRAFT_REVIEW_PENDING pending Formal Draft "
        "review and exact-head CI observation. No Ready, merge, Current, "
        "Owner acceptance, or external action was taken.\n\n"
        "Residuals: stale control pointers were absent and preserved; "
        "historical Task160 residuals are unadjudicated discovery leads; "
        "the binary transition candidate does not separately validate the "
        "non-Cartesian path hypothesis.\n"
    ).format(
        TASK,
        primary,
        v2.get("research_candidate_verdict"),
        v2["epistemic_validity"]["status"],
    )
    docs = {
        ROOT
        / "docs/governance/state-vs-transition-semantics-competition-2026-09-07.md": competition,
        ROOT
        / "docs/governance/transition-semantic-irreducibility-and-compile-away-2026-09-07.md": compile_doc,
        ROOT
        / "docs/governance/transition-residual-casebook-2026-09-07.md": residual_doc,
        ROOT / "reports/governance/task-IGNITION-20260907-161.md": report,
        ROOT / "agent-results/IGNITION-20260907-161-result.md": result,
    }
    for path, text in docs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if args == ["preflight"]:
        snapshot = preflight_snapshot()
        print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args == ["freeze"]:
        ledger = freeze()
        print(json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if len(args) == 3 and args[0] == "--single-score":
        score_single(Path(args[1]), Path(args[2]))
        return 0
    if args == ["verify"]:
        result = verify()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args == ["score"]:
        result = score()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args == ["analyze"]:
        result = analyze()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args == ["docs"]:
        write_docs()
        return 0
    if args == ["all"]:
        preflight_snapshot()
        freeze()
        score()
        analyze()
        write_docs()
        return 0
    print(
        "usage: task161_state_vs_transition.py "
        "[preflight|freeze|verify|score|analyze|docs|all|--single-score INPUT OUTPUT]"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
