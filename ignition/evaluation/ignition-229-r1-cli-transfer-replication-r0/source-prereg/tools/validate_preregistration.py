#!/usr/bin/env python3
"""Fail-closed mechanical validation for the frozen Task229 preregistration."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import pathlib
import re
import subprocess
import sys

try:
    import jsonschema
except ImportError as exc:
    raise SystemExit("TASK229_PREREGISTRATION=FAIL jsonschema is unavailable") from exc


HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE.parent
REPO = PREREG.parents[3]
POLICY_DIR = pathlib.Path("ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/policies")
INPUT_ROOT = pathlib.Path("ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families")
EXPECTED_POLICIES = {
    "POLICY_F01_A": "db786b0d68c8955cc1354c325aaa528bcc2e88915e75dc593fa3e9475b5c2410",
    "POLICY_F01_B": "f64bc598c3d37309a7519c8e19976d3f439c9e1715484fea3d9ed8e6788d93f5",
    "POLICY_F02_A": "e4fd07ae2f96bd31ddf9422de43d403e80aebd264fb0b1ca0be618598fc3744c",
    "POLICY_F02_B": "ac66d15487b8ae93b7353ab07ddb4230eb49b643370da92750db68b2a5ec371c",
    "POLICY_F03_A": "17a338279f13bbe716bc21cdbc90a7592a21b7024cb18b601f9dcb9b6ddbc4a9",
    "POLICY_F03_B": "d248c7809edc0fd739c226100179d1e56d5294db92148831efac8fda16d53841",
}
EXPECTED_INPUTS = {
    "FAMILY01/m0.md": "4cce89f12f278559f45ac0d3bbb6dae049e72dc059866bb1fb039ab74aaa5a0a",
    "FAMILY01/revision-evidence-e1.md": "8c4d4123055732d8e68a13eaa0dcb9fbae3cddb07afef66e7dbb3699ea761ca0",
    "FAMILY02/m0.md": "bc64a52ae85320c22221021aa57f3dee526d4355a5c37f45477f1e329737dc69",
    "FAMILY02/revision-evidence-e1.md": "f7adf3efbc59f07b5df3ef80552d96981c0112a71cdc324fe71d8e17988072ea",
    "FAMILY03/m0.md": "691b63e6ff4324acc23a09a35114df3fbb75668d39de3d8283386f30b110331a",
    "FAMILY03/revision-evidence-e1.md": "fba2eef834fa1ae9b43665ecbaa15a2bf8690f840cc0a56483701a8e7601c5ff",
}
REQUIRED_FILES = {
    "README.md", "protocol.md", "session-prompt-template.md", "response-schema.json",
    "analysis-input-schema.json", "blind-evaluation-schema.json", "blind-key-schema.json",
    "outcome-rule.json", "condition-manifest.json", "session-order.json",
    "evaluator-rubric.md", "sanitization-procedure.md", "missingness-retry-rules.md",
    "target-opening-gate.md", "claim-ceiling.md", "tools/validate_preregistration.py",
    "tools/freeze_manifest.py", "tools/target_opening_gate.py", "tools/recompute.py",
}


def fail(message: str):
    raise SystemExit(f"TASK229_PREREGISTRATION=FAIL {message}")


def load(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {path.relative_to(PREREG)}: {exc}")


def sha(path: pathlib.Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    missing = sorted(rel for rel in REQUIRED_FILES if not (PREREG / rel).is_file())
    if missing:
        fail("missing preregistration files: " + ", ".join(missing))

    manifest = load(PREREG / "condition-manifest.json")
    order = load(PREREG / "session-order.json")
    outcome = load(PREREG / "outcome-rule.json")
    if manifest.get("version") != "task229-condition-manifest-r0":
        fail("condition manifest version mismatch")
    if len(manifest.get("lineages", [])) != 6:
        fail("condition manifest must contain six fixed lineages")
    if manifest.get("conditions") != ["M0_ONLY", "M0_PLUS_E1", "REFERENCE_M1"]:
        fail("condition set or order differs from preregistration")

    seen_sessions = []
    validator_path = REPO / "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/tools/validate_policy.py"
    for lineage in manifest["lineages"]:
        policy_id = lineage["policy_id"]
        expected_policy = EXPECTED_POLICIES.get(policy_id)
        if expected_policy is None or lineage.get("policy_sha256") != expected_policy:
            fail(f"unexpected policy binding for {policy_id}")
        policy_path = REPO / lineage["policy_path"]
        if not policy_path.is_file() or sha(policy_path) != expected_policy:
            fail(f"policy byte hash mismatch for {policy_id}")
        policy = load(policy_path)
        if policy.get("policy_id") != policy_id:
            fail(f"policy ID mismatch for {policy_id}")
        check = subprocess.run([sys.executable, str(validator_path), str(policy_path)], capture_output=True, text=True)
        if check.returncode != 0 or "TASK228_POLICY_VALID=PASS" not in check.stdout:
            fail(f"Task228 validator failed for {policy_id}: {check.stdout.strip()} {check.stderr.strip()}")

        expected_family = lineage["family"]
        for kind, field, path_field in (("M0", "m0_sha256", "m0_path"), ("E1", "e1_sha256", "e1_path")):
            source = REPO / lineage[path_field]
            rel = f"{expected_family}/{source.name}"
            expected_sha = EXPECTED_INPUTS.get(rel)
            if expected_sha is None or lineage.get(field) != expected_sha or not source.is_file() or sha(source) != expected_sha:
                fail(f"frozen {kind} source hash mismatch for {expected_family}")

        conditions = lineage.get("conditions", [])
        if [item.get("condition") for item in conditions] != manifest["conditions"]:
            fail(f"condition entries missing or reordered for {lineage.get('lineage_id')}")
        if len(conditions) != 3:
            fail("every lineage must have exactly three sessions")
        for item in conditions:
            seen_sessions.append(item.get("session_id"))
            if item.get("family") != expected_family or item.get("m0_sha256") != lineage["m0_sha256"]:
                fail(f"condition family/M0 mismatch for {item.get('session_id')}")
            if item.get("condition") == "M0_ONLY" and any(key in item for key in ("e1_path", "policy_path", "policy_id")):
                fail("M0_ONLY condition must not bind E1 or a policy")
            if item.get("condition") == "M0_PLUS_E1" and (item.get("e1_sha256") != lineage["e1_sha256"] or item.get("policy_path")):
                fail("M0_PLUS_E1 must bind E1 and no reference policy")
            if item.get("condition") == "REFERENCE_M1" and (item.get("policy_id") != policy_id or item.get("policy_sha256") != expected_policy or item.get("e1_path")):
                fail("REFERENCE_M1 must bind only its exact policy and M0")
    if len(seen_sessions) != 18 or len(set(seen_sessions)) != 18:
        fail("session IDs must be 18 unique values")

    try:
        seed = bytes.fromhex(order["seed_hex"])
        if hashlib.sha256(seed).hexdigest() != order["seed_sha256"]:
            fail("session-order seed digest mismatch")
        computed = sorted(seen_sessions, key=lambda sid: (hashlib.sha256(seed + b"\0" + sid.encode("utf-8")).hexdigest(), sid))
        if order.get("order") != computed or len(order.get("order", [])) != 18:
            fail("deterministic session order mismatch")
    except (ValueError, KeyError, TypeError) as exc:
        fail(f"invalid session-order seed: {exc}")

    if outcome.get("version") != "TASK229_TRANSFER_ONLY_R0":
        fail("outcome rule version mismatch")
    prompt = (PREREG / "session-prompt-template.md").read_text(encoding="utf-8")
    prohibited = (
        "Task225", "Task227", "condition-manifest.json", "blind-evaluation-schema.json",
        "criteria.md", "target-index", "POLICY_F01", "POLICY_F02", "POLICY_F03",
        "M0_ONLY", "M0_PLUS_E1", "REFERENCE_M1", "L01", "L02", "L03", "L04", "L05", "L06",
        "fbfbbf5d", "e1569206", "9a508fc1", "6c66a1ff"
    )
    found = [token for token in prohibited if token in prompt]
    if found:
        fail("successor prompt leaks coordinator/target/evaluator identifiers: " + ", ".join(found))
    placeholders = re.findall(r"\{\{[A-Z0-9_]+\}\}", prompt)
    if set(placeholders) != {"{{METHOD_MATERIAL}}", "{{CASE_A}}", "{{CASE_B}}", "{{CASE_C}}", "{{RESPONSE_SCHEMA}}"}:
        fail("successor prompt placeholders differ from the frozen interface")

    # No experimental or target-derived data is allowed in the preregistration subtree before freeze.
    forbidden_dirs = {"raw", "raw-sessions", "outputs", "evaluations", "targets", "cases"}
    for path in PREREG.rglob("*"):
        if path.is_dir() and path.name in forbidden_dirs and path.name != "tests":
            fail(f"pre-freeze output/target directory exists: {path.relative_to(PREREG)}")
        if path.is_file() and path.relative_to(PREREG).parts[0] == "run":
            fail("pre-freeze runtime receipt/output exists")

    for name in ("response-schema.json", "analysis-input-schema.json", "blind-evaluation-schema.json", "blind-key-schema.json"):
        jsonschema.Draft202012Validator.check_schema(load(PREREG / name))
    try:
        version = importlib.metadata.version("jsonschema")
    except importlib.metadata.PackageNotFoundError:
        fail("jsonschema distribution metadata unavailable")
    if version != "4.25.1":
        fail(f"analysis validator version changed from 4.25.1 to {version}")

    print("TASK229_POLICY_HASHES=6/6")
    print("TASK229_POLICY_VALIDATOR=6/6")
    print("TASK229_M0_E1_HASHES=6/6")
    print("TASK229_SESSION_BINDING=18/18")
    print(f"TASK229_SESSION_ORDER=DETERMINISTIC seed_sha256={order['seed_sha256']}")
    print(f"TASK229_SCHEMA_CHECK=PASS jsonschema={version}")
    print("TASK229_PROMPT_TARGET_AND_EVALUATOR_LEAKAGE=NONE")
    print("TASK229_PREREGISTRATION=PASS")


if __name__ == "__main__":
    main()
