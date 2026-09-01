#!/usr/bin/env python3
"""Run the additional fail-closed gates required before Task149 Ready."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
BASE_SHA = "14c2595d796494286caf31378173fd9dd027edcf"
OWNER_RECORD_PATH = ROOT / "data/operations/iterations/149/task149-owner-adjudication-r1.json"
FINAL_REPORT_PATH = ROOT / "data/operations/iterations/149/final-report-external-capability-provider-adapter-spikes-r0.json"
CONTRACT_PATHS = [
    ROOT / "data/operations/iterations/149/provider-adapter-contract-r0.json",
    ROOT / "data/operations/iterations/149/provider-selection-authority-r0.json",
    ROOT / "data/operations/iterations/149/step01-provider-contract-boundary-r0.json",
]
CONTRACT_SCHEMA_PATHS = [
    ROOT / "schemas/operations/provider-adapter-contract-r0.schema.json",
    ROOT / "schemas/operations/provider-selection-authority-r0.schema.json",
    ROOT / "schemas/operations/provider-contract-boundary-r0.schema.json",
]
CURRENT_SURFACE_PATHS = [
    ROOT / "data/architecture/current-system-identity.json",
    ROOT / "data/architecture/current-facts.json",
    ROOT / "data/operations/current-snapshot-r1.json",
    ROOT / "data/operations/ignition-operation-capability-registry-r1.json",
    ROOT / "data/operations/ignition-operation-playbooks-r1.json",
]
FRONT_DOOR_PATHS = [
    ".github/README.md",
    "ignition/docs/USAGE.md",
    "ignition/docs/ai-assistant-usage-reference.md",
    "ignition/AI-START-HERE.md",
    "ignition/AI-HANDOFF.md",
    "ignition/llms.txt",
]
TASK149_IDS = {
    "NFC-98a78fb43c197995",
    "NFC-b69088986bec56f3",
    "NFC-3c5227edb0c17073",
    "NFC-b3c5c7948b976bda",
    "NFC-539e81e21c559678",
    "NFC-0e22bc9d70db50fa",
}
INVARIANTS = {
    "EXTERNAL_PROVIDER ≠ IGNITION_AUTHORITY",
    "PROVIDER_CAPABILITY ≠ PERMISSION",
    "PROVIDER_OUTPUT ≠ EXTERNAL_TRUTH",
    "PROVIDER_LOCAL_POLICY ≠ IGNITION_GLOBAL_POLICY",
    "ADAPTER_SPIKE_PASS ≠ CURRENT_CAPABILITY",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def command_output(args: list[str]) -> tuple[int, str]:
    result = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)
    return result.returncode, result.stdout + result.stderr


def gate_no_current_provider_activation(errors: list[str]) -> None:
    identity = load_json(ROOT / "data/architecture/current-system-identity.json")
    facts = load_json(ROOT / "data/architecture/current-facts.json")
    registry = load_json(ROOT / "data/operations/ignition-operation-capability-registry-r1.json")
    snapshot = load_json(ROOT / "data/operations/current-snapshot-r1.json")
    if identity.get("current_formal_task_id") != "IGNITION-20260829-148":
        errors.append("no_current_provider_activation: Current identity changed")
    if facts.get("current_formal_task_id") != "IGNITION-20260829-148":
        errors.append("no_current_provider_activation: Current facts changed")
    operations = registry.get("operations", [])
    if len(operations) != 19:
        errors.append(f"no_current_provider_activation: operation count is {len(operations)}, expected 19")
    for path, document in ((path, load_json(path)) for path in CURRENT_SURFACE_PATHS):
        names = [value.lower() for value in strings(document)]
        if any("archify" in value or "agent reach" in value for value in names):
            errors.append(f"no_current_provider_activation: provider name reached Current surface {path.relative_to(REPO_ROOT)}")
    owner = load_json(OWNER_RECORD_PATH)
    boundary = owner.get("authority_boundary", {})
    if boundary.get("current_provider_capability_added") is not False or boundary.get("current_operation_registry_changed") is not False:
        errors.append("no_current_provider_activation: Owner boundary widened")
    if snapshot.get("engineering_status", {}).get("current_state_status") != "CURRENT_WITH_OPEN_OBLIGATIONS":
        errors.append("no_current_provider_activation: Current snapshot status drifted")


def gate_no_provider_homepage_claim(errors: list[str]) -> None:
    code, output = command_output(["git", "diff", "--name-only", BASE_SHA, "HEAD", "--", *FRONT_DOOR_PATHS])
    if code != 0:
        errors.append(f"no_provider_homepage_claim: git diff failed: {output.strip()}")
    if output.strip():
        errors.append(f"no_provider_homepage_claim: front-door paths changed: {output.strip().replace(chr(10), ', ')}")
    forbidden = (
        "点火已支持 Archify",
        "点火已拥有全网能力",
        "点火支持 15 个平台",
        "Ignition supports Archify",
        "Ignition supports Agent Reach",
    )
    for relative in FRONT_DOOR_PATHS:
        path = REPO_ROOT / relative
        if not path.is_file():
            errors.append(f"no_provider_homepage_claim: missing front-door path {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        if any(phrase.lower() in text.lower() for phrase in forbidden):
            errors.append(f"no_provider_homepage_claim: forbidden claim in {relative}")
        if re.search(r"(?i)(current|default|supported|production).{0,80}(archify|agent reach)", text):
            errors.append(f"no_provider_homepage_claim: provider appears in a current/support claim in {relative}")


def gate_experimental_contract(errors: list[str]) -> None:
    for path in CONTRACT_PATHS:
        document = load_json(path)
        if document.get("research_scope") != "EXPERIMENTAL_PROVIDER_ADMISSION_RESEARCH_ONLY":
            errors.append(f"experimental_contract_not_runtime_authority: scope drifted in {path.name}")
        if document.get("runtime_interface_status") != "NOT_A_CURRENT_RUNTIME_PROVIDER_INTERFACE":
            errors.append(f"experimental_contract_not_runtime_authority: runtime status drifted in {path.name}")
    found_sets = [set(load_json(path).get("authority_invariants", [])) for path in (CONTRACT_PATHS[0], CONTRACT_PATHS[2])]
    if any(found != INVARIANTS for found in found_sets):
        errors.append("experimental_contract_not_runtime_authority: exact five invariants drifted")
    for path in CONTRACT_SCHEMA_PATHS:
        schema = load_json(path)
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        if "research_scope" not in required or "runtime_interface_status" not in required:
            errors.append(f"experimental_contract_not_runtime_authority: schema requirements missing in {path.name}")
        if properties.get("research_scope", {}).get("const") != "EXPERIMENTAL_PROVIDER_ADMISSION_RESEARCH_ONLY":
            errors.append(f"experimental_contract_not_runtime_authority: research const missing in {path.name}")
        if properties.get("runtime_interface_status", {}).get("const") != "NOT_A_CURRENT_RUNTIME_PROVIDER_INTERFACE":
            errors.append(f"experimental_contract_not_runtime_authority: runtime const missing in {path.name}")


def gate_no_authenticated_admission(errors: list[str]) -> None:
    owner = load_json(OWNER_RECORD_PATH)
    report = load_json(FINAL_REPORT_PATH)
    if owner.get("owner_decision", {}).get("agent_reach_authenticated", {}).get("decision") != "DEFER":
        errors.append("no_authenticated_admission: Owner decision is not DEFER")
    boundary = owner.get("authority_boundary", {})
    if boundary.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION" or boundary.get("authenticated_calls") != 0:
        errors.append("no_authenticated_admission: Owner boundary widened")
    authenticated = report.get("recommendations", {}).get("agent_reach_authenticated", {})
    if authenticated.get("authenticated_calls") != 0 or authenticated.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("no_authenticated_admission: historical report boundary widened")
    if owner.get("retained_evidence_and_residuals", {}).get("agent_reach_authenticated", {}).get("automatic_admission_queue") is not False:
        errors.append("no_authenticated_admission: automatic admission queue appeared")


def gate_live_external_invocation_unchanged(errors: list[str]) -> None:
    obligation = load_json(ROOT / "data/operations/open-obligation-registry-r1.json").get("obligations", [None])[0] or {}
    operation = next(
        item for item in load_json(ROOT / "data/operations/ignition-operation-capability-registry-r1.json").get("operations", [])
        if item.get("operation_id") == "external.live_invocation"
    )
    facts = load_json(ROOT / "data/architecture/current-facts.json")
    if obligation.get("obligation_id") != "LIVE_EXTERNAL_INVOCATION" or obligation.get("current_status") != "OPEN" or obligation.get("current_owner_plane") != "OWNER_DEFERRED":
        errors.append("live_external_invocation_unchanged: open obligation status changed")
    if obligation.get("owner_deferral", {}).get("no_automatic_resume") is not True:
        errors.append("live_external_invocation_unchanged: no-automatic-resume guard changed")
    if operation.get("current_status") != "OWNER_DEFERRED":
        errors.append("live_external_invocation_unchanged: operation admission status changed")
    open_obligations = facts.get("facts", {}).get("open_obligations", {})
    if open_obligations.get("open_obligation_ids") != ["LIVE_EXTERNAL_INVOCATION"]:
        errors.append("live_external_invocation_unchanged: Current facts open obligation changed")


def gate_nonfunction_materiality(errors: list[str]) -> None:
    closure = load_json(ROOT / "data/foundation/nonfunction-claims/closure-summary.json")
    if closure.get("canonical_claims") != 17859 or closure.get("explicit_quarantine_or_pending") != 4996:
        errors.append("nonfunction_claim_materiality_clean: closure counts drifted")
    ids = {json.loads(line)["canonical_id"] for line in (ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    if ids & TASK149_IDS:
        errors.append("nonfunction_claim_materiality_clean: Task149 operational IDs remain canonical")
    knowledge = load_json(ROOT / "data/governance/knowledge-experience/manifest.json")
    if knowledge.get("counts", {}).get("search_records") != 24421:
        errors.append("nonfunction_claim_materiality_clean: Knowledge search count drifted")
    owner = load_json(OWNER_RECORD_PATH)
    if owner.get("retained_evidence_and_residuals", {}).get("archify", {}).get("validation") != "PASS 9/9":
        errors.append("nonfunction_claim_materiality_clean: Archify PASS evidence missing")


def gate_exception(errors: list[str]) -> None:
    policy = (ROOT / "data/agent-federation/build-vs-integrate-policy-r1.json").read_text(encoding="utf-8")
    if "IGNITION-149-PROVIDER-ADAPTER-SPIKE" in policy:
        errors.append("no_draft_exception_survives_ready: expired exception remains in policy")
    if "HISTORICAL_OR_EXPERIMENTAL_PROVIDER_EVIDENCE_NO_RUNTIME_AUTHORITY" not in policy:
        errors.append("no_draft_exception_survives_ready: replacement exception missing")


def validate() -> list[str]:
    errors: list[str] = []
    gate_exception(errors)
    gate_no_current_provider_activation(errors)
    gate_no_provider_homepage_claim(errors)
    gate_experimental_contract(errors)
    gate_no_authenticated_admission(errors)
    gate_live_external_invocation_unchanged(errors)
    gate_nonfunction_materiality(errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_READY_GATES_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_READY_GATES_PASS no_current_provider_activation=PASS no_draft_exception_survives_ready=PASS experimental_contract_not_runtime_authority=PASS no_authenticated_admission=PASS no_provider_homepage_claim=PASS live_external_invocation_unchanged=PASS nonfunction_claim_materiality_clean=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
