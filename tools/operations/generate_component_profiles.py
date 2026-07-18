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

def canonical(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
def safe_argv(argv):
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x or x.startswith("/") or "\\" in x or ".." in x or any(c in x for c in ";&|`$<>") for x in argv):
        raise ValueError("unsafe structured argv")

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
    validator = policy.get("validator_argv", policies["validator_argv"])
    common = {"component_id": cid, "authority": authority, "component_kind": kind,
              "execution_capability": capability, "execution_cwd": ".",
              "authoritative_inputs": inputs, "generated_outputs": outputs,
              "input_fingerprint_policy": {"kind": "sha256_sorted_file_set", "paths": inputs},
              "output_fingerprint_policy": {"kind": "sha256_declared_outputs", "target": outputs[0] if outputs else component["canonical_target"]},
              "validator_argv": validator, "validators": [validator],
              "trigger_dimensions": sorted({d for r in topology["relations"] if cid in {r["source"],r["target"]} for d in r["trigger_dimensions"]}), "cache_policy": {"mode":"identity_bound","local_only":True},
              "local_rebuild_allowed": capability == "automatic", "global_gate": capability in {"external_attestation","validation_only"},
              "full_rebuild_triggers": ["missing_profile","missing_validator","missing_fingerprint_policy","authority_change"],
              "rollback_policy": "restore_registered_outputs_or_emit_recovery_package",
              "rights_and_provenance_constraints": "repository authority and provenance boundary must remain explicit",
              "claim_ceiling": "repository execution evidence only; no truth or lifecycle upgrade"}
    if capability == "automatic":
        argv = policy.get("producer_argv")
        if not argv or not outputs: raise ValueError(f"automatic profile lacks explicit producer/outputs: {cid}")
        common.update(execution_kind="automatic", producer_argv=argv, producer=argv, freshness_validator_argv=validator)
    elif capability == "external_attestation":
        common.update(execution_kind="attestation", attestation_required=True)
    elif capability == "validation_only":
        common.update(execution_kind="validation_only", aggregate_sources=inputs)
    else:
        common.update(execution_kind="manual", manual_authored=True)
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
