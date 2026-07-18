#!/usr/bin/env python3
"""Fail-closed validator for Q32I plans, execution records, caches, and recovery."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.operations.run_incremental_execution import profile_identity

REGISTRY = ROOT / "data/operations/project-components.json"
TOPOLOGY = ROOT / "data/operations/change-propagation-topology.json"
PROFILES = ROOT / "data/operations/component-execution-profiles.json"
PLAN_HASH_SENTINEL = "<bound-to-canonical-plan-hash>"
ALLOWED_DECISIONS = {
    "REBUILD",
    "REVALIDATE",
    "SYNC_METADATA",
    "NO_CHANGE_WITH_PROOF",
    "FULL_REBUILD_REQUIRED",
}
META_PATHS = {
    "data/operations/project-components.json",
    "data/operations/change-propagation-topology.json",
    "data/operations/component-execution-profiles.json",
    "data/operations/component-execution-profile-policies.json",
    "tools/operations/generate_component_profiles.py",
    "tools/operations/plan_incremental_execution.py",
    "tools/operations/run_incremental_execution.py",
    "tools/operations/validate_incremental_execution.py",
    "schemas/operations/project-components.schema.json",
    "schemas/operations/change-propagation-topology.schema.json",
    "schemas/operations/component-execution-profile.schema.json",
    "schemas/operations/incremental-execution-plan.schema.json",
    "schemas/operations/non-impact-proof.schema.json",
}


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str | None:
    return digest_bytes(path.read_bytes()) if path.is_file() else None


def canonical_plan_bytes(plan: dict[str, Any]) -> bytes:
    """Canonical hash payload; proof bindings are normalized to avoid recursion."""
    payload = copy.deepcopy(plan)
    payload.pop("plan_hash", None)
    for decision in payload.get("component_decisions", []):
        proof = decision.get("non_impact_proof")
        if isinstance(proof, dict) and "plan_hash" in proof:
            proof["plan_hash"] = PLAN_HASH_SENTINEL
    return canonical(payload).encode("utf-8")


def compute_plan_hash(plan: dict[str, Any]) -> str:
    return digest_bytes(canonical_plan_bytes(plan))


def authority_fingerprint(registry_path: Path, topology_path: Path, profiles_path: Path) -> str:
    identity = {
        "component_registry_digest": digest_file(registry_path),
        "propagation_topology_digest": digest_file(topology_path),
        "profile_registry_digest": digest_file(profiles_path),
    }
    return digest_bytes(canonical(identity).encode("utf-8"))


def validate_repo_path(raw: object, root: Path) -> Path:
    if not isinstance(raw, str) or not raw or raw.startswith("/") or "\\" in raw:
        raise ValueError(f"unsafe repository path: {raw!r}")
    if len(raw) > 1 and raw[1] == ":":
        raise ValueError(f"Windows path rejected: {raw}")
    parts = PurePosixPath(raw).parts
    if "." in parts or ".." in parts:
        raise ValueError(f"non-canonical path rejected: {raw}")
    resolved = (root / raw).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"path escapes repository: {raw}")
    return resolved


def registered_path(raw: str, patterns: list[str]) -> bool:
    return any(raw == pattern or (pattern.endswith("/") and raw.startswith(pattern)) for pattern in patterns)


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "reason": self.reason}


class Collector:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def add(self, code: str, path: str, reason: str) -> None:
        self.issues.append(Issue(code, path, reason))

    def safe_path(self, raw: object, path: str, root: Path) -> Path | None:
        try:
            return validate_repo_path(raw, root)
        except ValueError as exc:
            self.add("E_UNSAFE_PATH", path, str(exc))
            return None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_profiles(
    c: Collector,
    registry: dict[str, Any],
    profiles: dict[str, Any],
    root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    component_list = registry.get("components", [])
    profile_list = profiles.get("profiles", [])
    component_ids = [x.get("component_id") for x in component_list if isinstance(x, dict)]
    profile_ids = [x.get("component_id") for x in profile_list if isinstance(x, dict)]
    if len(component_ids) != len(set(component_ids)):
        c.add("E_REGISTRY_DUPLICATE_COMPONENT", "registry.components", "component_id values must be unique")
    if len(profile_ids) != len(set(profile_ids)):
        c.add("E_PROFILE_DUPLICATE_COMPONENT", "profiles.profiles", "component_id values must be unique")
    known, covered = set(component_ids), set(profile_ids)
    if known - covered:
        c.add("E_PROFILE_MISSING_COMPONENT", "profiles.profiles", f"missing profiles: {sorted(known-covered)}")
    if covered - known:
        c.add("E_PROFILE_UNKNOWN_COMPONENT", "profiles.profiles", f"unknown profiles: {sorted(covered-known)}")
    by_component = {x["component_id"]: x for x in component_list if isinstance(x, dict) and isinstance(x.get("component_id"), str)}
    by_profile = {x["component_id"]: x for x in profile_list if isinstance(x, dict) and isinstance(x.get("component_id"), str)}
    for index, component in enumerate(component_list):
        for pindex, raw in enumerate(component.get("path_patterns", [])):
            c.safe_path(raw, f"registry.components[{index}].path_patterns[{pindex}]", root)
    for index, profile in enumerate(profile_list):
        cid = profile.get("component_id")
        input_policy = profile.get("input_fingerprint_policy")
        output_policy = profile.get("output_fingerprint_policy")
        if not isinstance(input_policy, dict) or not input_policy.get("kind") or not isinstance(input_policy.get("paths"), list):
            c.add(
                "E_PROFILE_FINGERPRINT_POLICY",
                f"profiles.profiles[{index}].input_fingerprint_policy",
                "explicit input fingerprint policy with kind and paths is required",
            )
        if not isinstance(output_policy, dict) or not output_policy.get("kind") or not isinstance(output_policy.get("target"), str):
            c.add(
                "E_PROFILE_FINGERPRINT_POLICY",
                f"profiles.profiles[{index}].output_fingerprint_policy",
                "explicit output fingerprint policy with kind and target is required",
            )
        for field in ("authoritative_inputs", "generated_outputs"):
            for pindex, raw in enumerate(profile.get(field, [])):
                c.safe_path(raw, f"profiles.profiles[{index}].{field}[{pindex}]", root)
        patterns = by_component.get(cid, {}).get("path_patterns", [])
        for pindex, raw in enumerate(profile.get("generated_outputs", [])):
            if isinstance(raw, str) and not registered_path(raw, patterns):
                c.add(
                    "E_UNREGISTERED_OUTPUT",
                    f"profiles.profiles[{index}].generated_outputs[{pindex}]",
                    f"output {raw!r} is not registered to component {cid!r}",
                )
        kind = profile.get("execution_capability", profile.get("execution_kind"))
        if kind in {"manual", "external_attestation", "attestation", "validation_only"} and profile.get("producer_argv"):
            c.add("E_EXECUTION_BOUNDARY", f"profiles.profiles[{index}].producer_argv", f"{kind} profile cannot have a producer")
    return by_component, by_profile


def _validate_plan(
    c: Collector,
    plan: dict[str, Any],
    by_component: dict[str, dict[str, Any]],
    authority: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    decisions = plan.get("component_decisions")
    if not isinstance(decisions, list):
        c.add("E_PLAN_DECISIONS_TYPE", "plan.component_decisions", "must be an array")
        return {}, []
    ids = [x.get("component_id") for x in decisions if isinstance(x, dict)]
    if len(ids) != len(set(ids)):
        c.add("E_PLAN_DUPLICATE_DECISION", "plan.component_decisions", "each component must have exactly one decision")
    known, decided = set(by_component), set(ids)
    if known - decided:
        c.add("E_PLAN_MISSING_DECISION", "plan.component_decisions", f"missing decisions: {sorted(known-decided)}")
    if decided - known:
        c.add("E_PLAN_UNKNOWN_COMPONENT", "plan.component_decisions", f"unknown decisions: {sorted(decided-known)}")
    by_decision = {x["component_id"]: x for x in decisions if isinstance(x, dict) and isinstance(x.get("component_id"), str)}
    affected = plan.get("q32_affected_component_closure", [])
    if not isinstance(affected, list) or any(x not in known for x in affected):
        c.add("E_AFFECTED_CLOSURE", "plan.q32_affected_component_closure", "closure must contain only registered components")
        affected = []
    if len(affected) != len(set(affected)):
        c.add("E_AFFECTED_CLOSURE", "plan.q32_affected_component_closure", "closure must not contain duplicates")
    required_proof_fields = {
        "component_id", "basis", "unchanged_authoritative_input_fingerprints",
        "unchanged_dependency_fingerprints", "traversed_declared_relations",
        "excluded_declared_relations", "excluded_trigger_dimensions", "proof_method",
        "plan_hash", "authority_fingerprint", "expiry_or_recheck_condition", "claim_ceiling",
    }
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            c.add("E_PLAN_DECISION_TYPE", f"plan.component_decisions[{index}]", "must be an object")
            continue
        cid, choice = decision.get("component_id"), decision.get("decision")
        if choice not in ALLOWED_DECISIONS:
            c.add("E_DECISION_VALUE", f"plan.component_decisions[{index}].decision", f"unsupported decision: {choice!r}")
        if cid in affected and choice == "NO_CHANGE_WITH_PROOF":
            c.add("E_AFFECTED_NO_CHANGE", f"plan.component_decisions[{index}]", "affected component cannot be NO_CHANGE_WITH_PROOF")
        proof = decision.get("non_impact_proof")
        if choice != "NO_CHANGE_WITH_PROOF":
            if proof is not None:
                c.add("E_UNEXPECTED_PROOF", f"plan.component_decisions[{index}].non_impact_proof", "proof is only allowed for NO_CHANGE_WITH_PROOF")
            continue
        if not isinstance(proof, dict):
            c.add("E_PROOF_REQUIRED", f"plan.component_decisions[{index}].non_impact_proof", "complete proof is required")
            continue
        missing = sorted(required_proof_fields - set(proof))
        if missing:
            c.add("E_PROOF_INCOMPLETE", f"plan.component_decisions[{index}].non_impact_proof", f"missing fields: {missing}")
        if proof.get("component_id") != cid:
            c.add("E_PROOF_COMPONENT_BINDING", f"plan.component_decisions[{index}].non_impact_proof.component_id", "proof component binding mismatch")
        if proof.get("plan_hash") != plan.get("plan_hash"):
            c.add("E_PROOF_PLAN_HASH_BINDING", f"plan.component_decisions[{index}].non_impact_proof.plan_hash", "proof is not bound to the plan hash")
        if proof.get("authority_fingerprint") != authority:
            c.add("E_PROOF_AUTHORITY_BINDING", f"plan.component_decisions[{index}].non_impact_proof.authority_fingerprint", "proof authority fingerprint mismatch")
        if not proof.get("expiry_or_recheck_condition"):
            c.add("E_PROOF_RECHECK_CONDITION", f"plan.component_decisions[{index}].non_impact_proof.expiry_or_recheck_condition", "recheck condition is required")
    expected_hash = compute_plan_hash(plan)
    if plan.get("plan_hash") != expected_hash:
        c.add("E_PLAN_HASH_MISMATCH", "plan.plan_hash", f"expected {expected_hash}")
    residue = plan.get("unresolved_residue", [])
    full_reasons = plan.get("full_rebuild_reasons", [])
    if residue and not full_reasons:
        c.add("E_UNRESOLVED_NOT_FAIL_CLOSED", "plan.unresolved_residue", "unresolved paths require a full rebuild reason")
    seeds = plan.get("normalized_change_seeds", [])
    all_patterns = [pattern for component in by_component.values() for pattern in component.get("path_patterns", [])]
    unknown_seeds = [
        seed for seed in seeds
        if isinstance(seed, str) and seed not in META_PATHS and not registered_path(seed, all_patterns)
    ]
    if unknown_seeds and not full_reasons:
        c.add("E_UNKNOWN_PATH_NOT_FAIL_CLOSED", "plan.normalized_change_seeds", f"unknown paths require full rebuild: {unknown_seeds}")
    meta_changed = any(seed in META_PATHS for seed in seeds if isinstance(seed, str))
    require_full = bool(residue or full_reasons or meta_changed or unknown_seeds)
    if meta_changed and not full_reasons:
        c.add("E_META_CHANGE_NOT_FAIL_CLOSED", "plan.normalized_change_seeds", "meta-structure changes require full rebuild")
    if require_full and any(x.get("decision") != "FULL_REBUILD_REQUIRED" for x in decisions if isinstance(x, dict)):
        c.add("E_FULL_REBUILD_DOWNGRADED", "plan.component_decisions", "fail-closed plan must assign FULL_REBUILD_REQUIRED to every component")
    expected_order = [x.get("component_id") for x in decisions if isinstance(x, dict) and x.get("decision") == "REBUILD"]
    order = plan.get("execution_order", [])
    if not isinstance(order, list) or order != expected_order or len(order) != len(set(order)):
        c.add("E_EXECUTION_ORDER", "plan.execution_order", f"expected exact REBUILD order {expected_order}")
        order = [] if not isinstance(order, list) else order
    return by_decision, order


def _validate_execution(
    c: Collector,
    execution: dict[str, Any],
    plan: dict[str, Any],
    order: list[str],
    by_profile: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    records = execution.get("records")
    if not isinstance(records, list):
        c.add("E_EXECUTION_RECORDS_TYPE", "execution.records", "must be an array")
        return
    record_ids = [x.get("component_id") for x in records if isinstance(x, dict)]
    if len(record_ids) != len(set(record_ids)):
        c.add("E_EXECUTION_ORDER", "execution.records", "execution records contain duplicates")
    failed_indexes = [i for i, x in enumerate(records) if isinstance(x, dict) and x.get("end_status") == "failed"]
    if failed_indexes:
        expected = order[: failed_indexes[0] + 1]
        if failed_indexes != [len(records) - 1]:
            c.add("E_EXECUTION_CONTINUED_AFTER_FAILURE", "execution.records", "first failure must stop execution")
    else:
        expected = order
    if record_ids != expected:
        c.add("E_EXECUTION_ORDER", "execution.records", f"expected records {expected}, got {record_ids}")
    if execution.get("ok") is True and failed_indexes:
        c.add("E_EXECUTION_FALSE_SUCCESS", "execution.ok", "failed execution cannot report success")
    required = {
        "component_id", "argv", "cwd", "start_status", "end_status", "stdout", "stderr",
        "return_code", "before_input_fingerprints", "before_output_fingerprints",
        "after_output_fingerprints", "validator_result", "cache_decision", "rollback_status",
    }
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            c.add("E_EXECUTION_RECORD_TYPE", f"execution.records[{index}]", "must be an object")
            continue
        missing = sorted(required - set(record))
        if missing:
            c.add("E_EXECUTION_RECORD_INCOMPLETE", f"execution.records[{index}]", f"missing fields: {missing}")
        cid = record.get("component_id")
        profile = by_profile.get(cid, {})
        if record.get("argv") != profile.get("producer_argv"):
            c.add("E_EXECUTION_COMMAND_IDENTITY", f"execution.records[{index}].argv", "recorded command must exactly match the registered producer argv")
        if record.get("cwd") != ".":
            c.add("E_EXECUTION_CWD", f"execution.records[{index}].cwd", "execution cwd must be the repository root")
        capability = profile.get("execution_capability", profile.get("execution_kind"))
        if capability == "manual" and record.get("end_status") not in {"manual-boundary", "dry-run"}:
            c.add("E_EXECUTION_BOUNDARY", f"execution.records[{index}].end_status", "manual component boundary was crossed")
        if capability in {"external_attestation", "attestation"} and record.get("end_status") not in {"attestation-required", "dry-run"}:
            c.add("E_EXECUTION_BOUNDARY", f"execution.records[{index}].end_status", "external attestation boundary was crossed")
        allowed_outputs = set(profile.get("generated_outputs", []))
        for field in ("before_input_fingerprints", "before_output_fingerprints", "after_output_fingerprints"):
            values = record.get(field, {})
            if not isinstance(values, dict):
                c.add("E_EXECUTION_FINGERPRINT_TYPE", f"execution.records[{index}].{field}", "must be an object")
                continue
            for raw in values:
                c.safe_path(raw, f"execution.records[{index}].{field}.{raw}", root)
                if field != "before_input_fingerprints" and raw not in allowed_outputs:
                    c.add("E_UNREGISTERED_OUTPUT", f"execution.records[{index}].{field}.{raw}", "execution fingerprint references unregistered output")
    if failed_indexes:
        failed = records[failed_indexes[0]]
        if failed.get("rollback_status") not in {"restored", "recovery-package-required"}:
            c.add("E_ROLLBACK_INCOMPLETE", f"execution.records[{failed_indexes[0]}].rollback_status", "failure requires completed rollback or recovery package")
        if not execution.get("recovery_package"):
            c.add("E_RECOVERY_REFERENCE_MISSING", "execution.recovery_package", "failed execution must reference a recovery package")
    if execution.get("plan_hash") not in {None, plan.get("plan_hash")}:
        c.add("E_EXECUTION_PLAN_BINDING", "execution.plan_hash", "execution is bound to another plan")


def _validate_cache(
    c: Collector,
    cache: dict[str, Any],
    plan: dict[str, Any],
    profiles: dict[str, Any],
    root: Path,
    profiles_path: Path,
) -> None:
    payload = copy.deepcopy(cache)
    integrity = payload.pop("integrity_digest", None)
    if integrity != digest_bytes(canonical(payload).encode("utf-8")):
        c.add("E_CACHE_INTEGRITY", "cache.integrity_digest", "cache payload digest mismatch")
    try:
        expected_identity = profile_identity(profiles_path, profiles, root, plan)
    except (KeyError, TypeError, ValueError) as exc:
        expected_identity = None
        c.add("E_CACHE_IDENTITY_INPUT", "cache.identity", f"cannot compute cache identity: {exc}")
    if cache.get("identity") != expected_identity:
        c.add("E_CACHE_IDENTITY", "cache.identity", "cache identity does not match profile, registry, topology, producer, validator, fingerprints, and plan")
    by_profile = {p.get("component_id"): p for p in profiles.get("profiles", []) if isinstance(p, dict)}
    for index, record in enumerate(cache.get("records", [])):
        if not isinstance(record, dict):
            c.add("E_CACHE_RECORD_TYPE", f"cache.records[{index}]", "cache record must be an object")
            continue
        expected_argv = by_profile.get(record.get("component_id"), {}).get("producer_argv")
        if record.get("argv") != expected_argv:
            c.add("E_CACHE_COMMAND_IDENTITY", f"cache.records[{index}].argv", "cached command must exactly match the registered producer argv")
    for raw in cache.get("output_fingerprints", {}):
        c.safe_path(raw, f"cache.output_fingerprints.{raw}", root)


def _validate_recovery(
    c: Collector,
    recovery: dict[str, Any],
    plan: dict[str, Any],
    root: Path,
    recovery_base: Path | None = None,
) -> None:
    required = {
        "plan_hash", "component_identity", "failed_action", "original_fingerprints",
        "current_fingerprints", "sha256", "restored_files", "unrecovered_files",
        "restore_steps", "records", "integrity_digest",
    }
    missing = sorted(required - set(recovery))
    if missing:
        c.add("E_RECOVERY_INCOMPLETE", "recovery", f"missing fields: {missing}")
    payload = copy.deepcopy(recovery)
    integrity = payload.pop("integrity_digest", None)
    if integrity != digest_bytes(canonical(payload).encode("utf-8")):
        c.add("E_RECOVERY_INTEGRITY", "recovery.integrity_digest", "recovery payload digest mismatch")
    if recovery.get("plan_hash") != plan.get("plan_hash"):
        c.add("E_RECOVERY_PLAN_BINDING", "recovery.plan_hash", "recovery package is bound to another plan")
    if not isinstance(recovery.get("failed_action"), dict):
        c.add("E_RECOVERY_FAILED_ACTION", "recovery.failed_action", "failed action record is required")
    records = recovery.get("records", [])
    record_ids = [record.get("component_id") for record in records if isinstance(record, dict)]
    if recovery.get("component_identity") != record_ids:
        c.add("E_RECOVERY_COMPONENT_IDENTITY", "recovery.component_identity", "component identity must exactly match recovery record order")
    failed_action = recovery.get("failed_action")
    if isinstance(failed_action, dict) and (
        failed_action.get("end_status") != "failed"
        or failed_action.get("component_id") not in record_ids
    ):
        c.add("E_RECOVERY_FAILED_ACTION", "recovery.failed_action", "failed action must identify a failed recovery record")
    if not recovery.get("restore_steps"):
        c.add("E_RECOVERY_INCOMPLETE", "recovery.restore_steps", "restore steps are required")
    for field in ("original_fingerprints", "current_fingerprints"):
        for raw in recovery.get(field, {}):
            c.safe_path(raw, f"recovery.{field}.{raw}", root)
    for raw in recovery.get("restored_files", []) + recovery.get("unrecovered_files", []):
        c.safe_path(raw, f"recovery.files.{raw}", root)
    for raw in recovery.get("sha256", {}):
        if not isinstance(raw, str) or not raw.startswith("backups/"):
            c.add("E_RECOVERY_BACKUP_PATH", f"recovery.sha256.{raw}", "backup digest key must start with backups/")
        else:
            c.safe_path(raw.removeprefix("backups/"), f"recovery.sha256.{raw}", root)
            if recovery_base is not None:
                backup = recovery_base / raw
                if not backup.is_file() or digest_file(backup) != recovery["sha256"][raw]:
                    c.add("E_RECOVERY_BACKUP_INTEGRITY", f"recovery.sha256.{raw}", "backup is missing or its digest is incorrect")


def validate_incremental_execution(
    plan: dict[str, Any],
    *,
    execution: dict[str, Any] | None = None,
    cache: dict[str, Any] | None = None,
    recovery: dict[str, Any] | None = None,
    recovery_base: Path | None = None,
    root: Path = ROOT,
    registry_path: Path | None = None,
    topology_path: Path | None = None,
    profiles_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    registry_path = registry_path or root / "data/operations/project-components.json"
    topology_path = topology_path or root / "data/operations/change-propagation-topology.json"
    profiles_path = profiles_path or root / "data/operations/component-execution-profiles.json"
    registry, profiles = _load_json(registry_path), _load_json(profiles_path)
    c = Collector()
    by_component, by_profile = _validate_profiles(c, registry, profiles, root)
    authority = authority_fingerprint(registry_path, topology_path, profiles_path)
    _, order = _validate_plan(c, plan, by_component, authority)
    lifecycle_values = [plan.get(key) for key in ("lifecycle_status", "candidate_status", "publication_status")]
    if any(isinstance(value, str) and value.strip().lower() in {"accepted", "merged", "current"} for value in lifecycle_values):
        c.add("E_LIFECYCLE_ESCALATION", "plan.lifecycle", "candidate validation cannot claim Accepted, Merged, or Current")
    candidate_basis = plan.get("candidate_basis")
    if isinstance(candidate_basis, str) and re.search(r"(?:current|candidate)\s*head|head\s*(?:itself|self)", candidate_basis, re.IGNORECASE):
        c.add("E_SELF_REFERENTIAL_AUTHORITY", "plan.candidate_basis", "candidate cannot use its current HEAD as its own authority")
    scope_assets = plan.get("scope_assets", [])
    if not isinstance(scope_assets, list):
        c.add("E_SCOPE_CONTAMINATION", "plan.scope_assets", "scope assets must be an array")
    else:
        unauthorized = [
            value for value in scope_assets
            if isinstance(value, str) and (
                re.search(r"(^|[/_.-])(lab|shadow)([/_.-]|$)", value, re.IGNORECASE)
                or re.search(r"(^|[/_.-])(phase[-_ ]?d4|phase[-_ ]?e)([/_.-]|$)", value, re.IGNORECASE)
            )
        ]
        if unauthorized:
            c.add("E_SCOPE_CONTAMINATION", "plan.scope_assets", f"unauthorized D3 assets: {unauthorized}")
    if execution is not None:
        _validate_execution(c, execution, plan, order, by_profile, root)
    if cache is not None:
        _validate_cache(c, cache, plan, profiles, root, profiles_path)
    if recovery is not None:
        _validate_recovery(c, recovery, plan, root, recovery_base)
    objects = ["registry", "profiles", "plan"]
    objects += [name for name, value in (("execution", execution), ("cache", cache), ("recovery", recovery)) if value is not None]
    return {
        "ok": not c.issues,
        "validator": "Q32I-D1-unified-incremental-validator",
        "checked_objects": objects,
        "error_count": len(c.issues),
        "errors": [x.as_dict() for x in c.issues],
        "summary": "PASS: unified incremental execution artifacts are valid" if not c.issues else f"FAIL: {len(c.issues)} validation error(s)",
    }


def _optional_document(path: Path | None, filename: str = "manifest.json") -> dict[str, Any] | None:
    if path is None:
        return None
    target = path / filename if path.is_dir() else path
    return _load_json(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--execution", type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_incremental_execution(
            _load_json(args.plan),
            execution=_optional_document(args.execution, "result.json"),
            cache=_optional_document(args.cache),
            recovery=_optional_document(args.recovery),
            recovery_base=args.recovery if args.recovery and args.recovery.is_dir() else None,
            root=args.root,
        )
    except Exception as exc:
        result = {
            "ok": False,
            "validator": "Q32I-D1-unified-incremental-validator",
            "checked_objects": [],
            "error_count": 1,
            "errors": [{"code": "E_VALIDATOR_EXCEPTION", "path": "$", "reason": f"{type(exc).__name__}: {exc}"}],
            "summary": "FAIL: validator exception",
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print(result["summary"], file=sys.stderr)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
