#!/usr/bin/env python3
"""Generate complete execution profiles from the canonical component registry.

The output is derived: this program and the compact policy file are its only
profile authority.  It intentionally contains no component-count constant.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/operations/project-components.json"
POLICIES = ROOT / "data/operations/component-execution-profile-policies.json"
TOPOLOGY = ROOT / "data/operations/change-propagation-topology.json"
OUTPUT = ROOT / "data/operations/component-execution-profiles.json"
LOCAL_VALIDATOR_CONTRACTS = {
    "foundation_data": [("python3", "tools/foundation/validate_foundation.py")],
    "no_l7": [("python3", "tools/validate_human_front_door.py")],
    "no_totality_proof": [("python3", "tools/validate_human_front_door.py")],
    "no_truth_upgrade": [("python3", "tools/validate_human_front_door.py")],
    "pages_pipeline": [("python3", "-m", "unittest", "tests.test_pages_deploy_gate", "tests.test_tracked_symlink_gate")],
    "propagation_calculator": [("python3", "-m", "unittest", "tests.test_change_propagation", "tests.test_diff_coverage_gate")],
    "system_map": [("python3", "tools/generate_interactive_system_map.py", "--check")],
    "system_map_projection": [("python3", "tools/generate_interactive_system_map.py", "--check")],
}

def canonical(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
def safe_argv(argv):
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x or x.startswith("/") or "\\" in x or ".." in x or any(c in x for c in ";&|`$<>") for x in argv):
        raise ValueError("unsafe structured argv")

def validate_local_validator(cid, argv):
    safe_argv(argv)
    if tuple(argv) not in LOCAL_VALIDATOR_CONTRACTS.get(cid, []):
        raise ValueError(f"incomplete or component-inappropriate validator for {cid}: {argv}")
    if argv[:2] == ["python3", "tools/validate_protocol_canonical.py"]:
        raise ValueError(f"placeholder canonical validator is forbidden for {cid}")
    if argv[0] == "python3" and len(argv) >= 2 and argv[1].endswith(".py"):
        if not (ROOT / argv[1]).is_file():
            raise ValueError(f"validator script does not exist for {cid}: {argv[1]}")
    elif argv[:3] == ["python3", "-m", "unittest"]:
        if len(argv) < 4:
            raise ValueError(f"unittest validator lacks targets for {cid}")
    else:
        raise ValueError(f"unsupported local validator contract for {cid}: {argv}")

def profile(component, policies, topology):
    authority = component["authority"]
    cid = component["component_id"]
    paths = component["path_patterns"]
    policy = policies.get("component_policies", {}).get(cid, {})
    capability = policy.get("execution_capability")
    if capability is None:
        if authority == "external": capability = "external_attestation"
        elif component["component_type"] in {"virtual", "interpretation_boundary"}: capability = "validation_only"
        else: capability = "manual"
    if capability not in {"automatic", "validation_only", "manual", "external_attestation"}:
        raise ValueError(f"invalid execution capability for {cid}: {capability}")
    kind = {"automatic":"generated", "external_attestation":"external", "validation_only":"virtual", "manual":"authored"}[capability]
    inputs = policy.get("authoritative_inputs", paths)
    outputs = policy.get("generated_outputs", [])
    validation_capability = policy.get("validation_capability")
    if validation_capability is None:
        validation_capability = {"automatic":"local_automatic_validation", "validation_only":"local_validation_only", "manual":"manual_review", "external_attestation":"external_attestation"}[capability]
    expected_validation = {"automatic":"local_automatic_validation", "validation_only":"local_validation_only", "manual":"manual_review", "external_attestation":"external_attestation"}[capability]
    if validation_capability != expected_validation:
        raise ValueError(f"execution/validation capability conflict for {cid}: {capability}/{validation_capability}")
    common = {"component_id": cid, "authority": authority, "component_kind": kind,
              "execution_capability": capability, "validation_capability": validation_capability, "execution_cwd": ".",
              "authoritative_inputs": inputs, "generated_outputs": outputs,
              "input_fingerprint_policy": {"kind": "sha256_sorted_file_set", "paths": inputs},
              "output_fingerprint_policy": {"kind": "sha256_declared_outputs", "target": outputs[0] if outputs else component["canonical_target"]},
              "trigger_dimensions": sorted({d for r in topology["relations"] if cid in {r["source"],r["target"]} for d in r["trigger_dimensions"]}), "cache_policy": {"mode":"identity_bound","local_only":True},
              "local_rebuild_allowed": capability == "automatic", "global_gate": capability in {"external_attestation","validation_only"},
              "full_rebuild_triggers": ["missing_profile","missing_validator","missing_fingerprint_policy","authority_change"],
              "rollback_policy": "restore_registered_outputs_or_emit_recovery_package",
              "rights_and_provenance_constraints": "repository authority and provenance boundary must remain explicit",
              "claim_ceiling": "repository execution evidence only; no truth or lifecycle upgrade"}
    if capability == "automatic":
        validator = policy.get("validator_argv")
        if not validator: raise ValueError(f"automatic profile lacks explicit validator: {cid}")
        validate_local_validator(cid, validator)
        argv = policy.get("producer_argv")
        if not argv or not outputs: raise ValueError(f"automatic profile lacks explicit producer/outputs: {cid}")
        common.update(execution_kind="automatic", producer_argv=argv, producer=argv, validator_argv=validator, validators=[validator], freshness_validator_argv=validator)
    elif capability == "external_attestation":
        if "validator_argv" in policy: raise ValueError(f"external profile cannot declare local validator: {cid}")
        common.update(execution_kind="attestation", attestation_required=True, validation_authority=policies["external_validation_authority"])
    elif capability == "validation_only":
        validator = policy.get("validator_argv")
        if not validator: raise ValueError(f"validation-only profile lacks explicit validator: {cid}")
        validate_local_validator(cid, validator)
        common.update(execution_kind="validation_only", aggregate_sources=inputs, validator_argv=validator, validators=[validator])
    else:
        if "validator_argv" in policy: raise ValueError(f"manual profile cannot declare local validator: {cid}")
        common.update(execution_kind="manual", manual_authored=True, validation_authority=policies["manual_validation_authority"])
    for key in ("validator_argv", "producer_argv", "freshness_validator_argv"):
        if key in common: safe_argv(common[key])
    return common

def build():
    registry = json.loads(REGISTRY.read_text())
    policies = json.loads(POLICIES.read_text())
    topology = json.loads(TOPOLOGY.read_text())
    profiles = [profile(c, policies, topology) for c in sorted(registry["components"], key=lambda x: x["component_id"])]
    return {"schema_version":"1.0.0", "derived_from": {"registry_sha256": hashlib.sha256(REGISTRY.read_bytes()).hexdigest(), "policy_sha256": hashlib.sha256(POLICIES.read_bytes()).hexdigest(), "topology_sha256": hashlib.sha256(TOPOLOGY.read_bytes()).hexdigest()}, "profiles": profiles}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--check", action="store_true"); args=p.parse_args()
    payload=canonical(build())
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != payload: raise SystemExit("generated profiles are stale")
    else: OUTPUT.write_text(payload)
if __name__ == "__main__": main()
