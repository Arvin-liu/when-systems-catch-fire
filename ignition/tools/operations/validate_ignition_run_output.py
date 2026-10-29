#!/usr/bin/env python3
"""Validate the unified Ignition machine/audit output and render its concise human profile."""

from __future__ import annotations

import argparse
import copy
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
CONTRACT_PATH = ROOT / "data/operations/ignition-run-output-contract-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/ignition-run-output-r1.schema.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
PLAYBOOKS_PATH = "ignition/data/operations/ignition-operation-playbooks-r1.json"
FUNCTION_REGISTRY_PATH = ROOT / "data/foundation/function-assets/identity-cards.jsonl"
NONFUNCTION_REGISTRY_PATH = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"
FUNCTION_AUTHORITY = "ignition/data/foundation/function-assets/identity-cards.jsonl"
NONFUNCTION_AUTHORITY = "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/unified-output-r1.json"

SEMANTIC_FIELDS = (
    ("REQUEST", "/request"),
    ("RUN_MODE", "/run_mode"),
    ("OPERATION_PATH", "/operation_path"),
    ("CURRENT_REF", "/current_ref"),
    ("INPUT_OBJECT / PROVENANCE", "/input_object_provenance"),
    ("INPUT_DERIVED_FINDINGS", "/input_derived_findings"),
    ("EXISTING_CANONICAL_MATCHES", "/existing_canonical_matches"),
    ("COLLISION_RELATIONS", "/collision_relations"),
    ("CANDIDATE_DELTAS", "/candidate_deltas"),
    ("CONTRADICTIONS / GAPS", "/contradictions_gaps"),
    ("EVIDENCE / SOURCES", "/evidence_sources"),
    ("UNCERTAINTY", "/uncertainty"),
    ("CLAIM_CEILING", "/claim_ceiling"),
    ("RESULT", "/result"),
    ("STOP_REASON / OPTIONAL_NEXT_ACTION", "/stop"),
)
BOUNDARY_GUARDS = (
    "INPUT_DERIVED_IS_NOT_IGNITION_DISCOVERY",
    "CANDIDATE_IS_NOT_CANONICAL_ASSET",
    "REPOSITORY_MATCH_IS_NOT_EXTERNAL_TRUTH",
    "AGENT_CONSENSUS_IS_NOT_EVIDENCE",
    "IMPLEMENTATION_COMPLETE_IS_NOT_EPISTEMIC_ACCEPTANCE",
    "HISTORICAL_MEMORY_IS_NOT_CURRENT_REGISTRY",
)
LIFECYCLE_STAGES = (
    "ACCEPT_REQUEST",
    "FREEZE_CURRENT",
    "CLASSIFY_MODE",
    "CLASSIFY_INPUT_OBJECT",
    "RESOLVE_OPERATION",
    "CHECK_CAPABILITY_STATUS",
    "BUILD_MINIMAL_READ_PLAN",
    "NORMALIZE_INPUT_AND_PROVENANCE",
    "EXECUTE_OPERATION",
    "CANONICAL_COLLISION / EVIDENCE CHECK",
    "ADVERSARIAL_REVIEW",
    "APPLY_CLAIM_CEILING",
    "RENDER_RESULT",
    "STOP / HANDOFF",
)
MATCH_REQUIRED_RELATIONS = {"DUPLICATE_OF", "EXTENSION_OF", "COMBINATION_OF", "CONFLICT_WITH", "CANDIDATE_NEW"}
EVIDENCE_EFFECTS = {
    "CURRENT_REPOSITORY_AUTHORITY": "REPOSITORY_IDENTITY_OR_POLICY_ONLY",
    "INPUT_SOURCE": "SOURCE_PROVENANCE_ONLY",
    "EXTERNAL_PRIMARY_SOURCE": "EXTERNAL_EVIDENCE_WITH_DECLARED_SCOPE",
    "EXTERNAL_SECONDARY_SOURCE": "EXTERNAL_EVIDENCE_WITH_DECLARED_SCOPE",
    "VALIDATOR_OUTPUT": "VALIDATION_ONLY",
    "HUMAN_REVIEW": "HUMAN_REVIEW_WITH_DECLARED_SCOPE",
    "CURRENT_EPISTEMIC_AUTHORITY": "EPISTEMIC_DECISION_WITH_DECLARED_SCOPE",
    "HISTORICAL_RETRIEVAL_HINT": "NONE",
}


class IgnitionRunOutputError(ValueError):
    """Raised when an output cannot satisfy the unified contract."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _pointer_get(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise KeyError(pointer)
    value = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


@lru_cache(maxsize=1)
def _operation_map() -> dict[str, dict[str, Any]]:
    return {row["operation_id"]: row for row in load_json(REGISTRY_PATH)["operations"]}


@lru_cache(maxsize=1)
def _canonical_maps() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    function_rows = load_jsonl(FUNCTION_REGISTRY_PATH)
    claim_rows = load_jsonl(NONFUNCTION_REGISTRY_PATH)
    return (
        {row["canonical_id"]: row for row in function_rows},
        {row["canonical_id"]: row for row in claim_rows},
    )


def validate_contract(contract: dict[str, Any] | None = None) -> list[str]:
    document = contract if contract is not None else load_json(CONTRACT_PATH)
    errors: list[str] = []
    if document.get("contract_id") != "IGNITION_RUN_OUTPUT_CONTRACT_R1":
        errors.append("contract id is missing or changed")
    if document.get("canonical_source_path") != "ignition/data/operations/ignition-run-output-contract-r1.json":
        errors.append("canonical contract path is missing or changed")
    if document.get("instance_schema_path") != "ignition/schemas/operations/ignition-run-output-r1.schema.json":
        errors.append("instance schema path is missing or changed")
    lifecycle = document.get("lifecycle", {})
    if lifecycle.get("task_id") != "IGNITION-20260829-148":
        errors.append("output contract lifecycle task_id is not Task148")
    if lifecycle.get("status") == "CURRENT":
        if lifecycle.get("current_on_main") is not True:
            errors.append("Current output contract must set current_on_main=true")
    elif lifecycle.get("status") != "TASK148_CANDIDATE_BRANCH" or lifecycle.get("current_on_main") is not False:
        errors.append("output contract lifecycle is neither a synchronized Current state nor a valid candidate state")
    actual_semantics = [
        (row.get("semantic_id"), row.get("json_pointer"))
        for row in document.get("semantic_fields", [])
        if isinstance(row, dict)
    ]
    if actual_semantics != list(SEMANTIC_FIELDS):
        errors.append("the fifteen required semantic fields or their canonical JSON pointers changed")
    actual_guards = [row.get("guard_id") for row in document.get("boundary_guards", []) if isinstance(row, dict)]
    if actual_guards != list(BOUNDARY_GUARDS):
        errors.append("the six anti-confusion guards are missing, duplicated or reordered")
    profiles = document.get("profiles", {})
    if profiles.get("machine_audit", {}).get("profile_id") != "MACHINE_AUDIT":
        errors.append("machine/audit profile is missing")
    human = profiles.get("human_default", {})
    if human.get("profile_id") != "HUMAN_DEFAULT" or human.get("machine_audit_recovery_required") is not True:
        errors.append("human default profile must preserve machine/audit recovery")
    return errors


def _schema_errors(output: dict[str, Any]) -> list[str]:
    return [
        f"{error.json_path}: {error.message}"
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(output)
    ]


def validate_output(output: dict[str, Any]) -> list[str]:
    errors = validate_contract()
    errors.extend(_schema_errors(output))

    evidence_rows = output.get("evidence_sources", [])
    if isinstance(evidence_rows, list):
        for row in evidence_rows:
            if isinstance(row, dict) and row.get("source_kind") in {"AGENT_CONSENSUS", "MODEL_MEMORY"}:
                errors.append("Agent consensus or model memory cannot be entered as evidence")
    if errors:
        return errors

    for semantic_id, pointer in SEMANTIC_FIELDS:
        try:
            _pointer_get(output, pointer)
        except (KeyError, IndexError, TypeError, ValueError):
            errors.append(f"{semantic_id}: machine/audit semantic is not recoverable at {pointer}")

    attestations = output["boundary_attestations"]
    if list(attestations) != list(BOUNDARY_GUARDS) or not all(attestations.values()):
        errors.append("boundary attestations must preserve all six canonical anti-confusion guards")

    operation_path = output["operation_path"]
    operation_id = operation_path["operation_id"]
    operation = _operation_map().get(operation_id)
    if operation is None:
        if operation_path["registry_status"] != "UNREGISTERED" or operation_path["decision"] != "STOP":
            errors.append(f"{operation_id}: an unregistered operation must stop as UNREGISTERED")
        if operation_path["playbook_source"] is not None:
            errors.append(f"{operation_id}: an unregistered operation cannot load a callable playbook")
    else:
        if operation_path["registry_status"] != operation["current_status"]:
            errors.append(f"{operation_id}: output registry status differs from the Current capability registry")
        callable_operation = (
            operation["current_status"] in {"CURRENT", "CURRENT_BOUNDED"}
            and operation["ai_callability"] in {"PUBLIC", "PUBLIC_BOUNDED"}
        )
        if callable_operation and operation_path["playbook_source"] != PLAYBOOKS_PATH:
            errors.append(f"{operation_id}: callable output path must bind the registry-derived playbook index")
        if not callable_operation:
            if operation_path["decision"] != "STOP":
                errors.append(f"{operation_id}: a non-callable status entry must stop")
            if operation_path["playbook_source"] is not None:
                errors.append(f"{operation_id}: a non-callable status entry cannot load a playbook")
        if operation_path["decision"] in {"PROCEED", "PROCEED_BOUNDED"}:
            if output["run_mode"] != operation["default_execution_mode"]:
                errors.append(f"{operation_id}: proceeded run mode differs from the registry default")
            expected_decision = "PROCEED_BOUNDED" if operation["current_status"] == "CURRENT_BOUNDED" else "PROCEED"
            if operation_path["decision"] != expected_decision:
                errors.append(f"{operation_id}: proceed decision differs from registry status")

    stages = operation_path["lifecycle_stages_completed"]
    positions = [LIFECYCLE_STAGES.index(stage) for stage in stages]
    if positions != sorted(positions):
        errors.append("completed lifecycle stages are not in canonical order")
    if output["result"]["status"] in {"COMPLETED", "COMPLETED_BOUNDED"} and stages != list(LIFECYCLE_STAGES):
        errors.append("a completed output must record all fourteen lifecycle stages")
    if stages[-1] != "STOP / HANDOFF":
        errors.append("every final output must record STOP / HANDOFF")

    current_ref = output["current_ref"]
    if current_ref["exact_head"] and current_ref["commit_sha"] is None:
        errors.append("an exact Current head requires a commit SHA")
    if not current_ref["exact_head"] and not current_ref["limitations"]:
        errors.append("a non-exact Current observation requires an explicit limitation")
    if output["input_object_provenance"]["boundary_status"] == "UNRESOLVED" and output["result"]["status"] != "STOPPED":
        errors.append("an unresolved request/object boundary must stop")

    object_ids = [row["object_id"] for row in output["input_object_provenance"]["objects"]]
    finding_ids = [row["finding_id"] for row in output["input_derived_findings"]]
    match_ids = [row["match_id"] for row in output["existing_canonical_matches"]]
    relation_ids = [row["relation_id"] for row in output["collision_relations"]]
    candidate_ids = [row["candidate_id"] for row in output["candidate_deltas"]]
    gap_ids = [row["item_id"] for row in output["contradictions_gaps"]]
    source_ids = [row["source_id"] for row in output["evidence_sources"]]
    uncertainty_ids = [row["uncertainty_id"] for row in output["uncertainty"]]
    for label, values in (
        ("input object", object_ids),
        ("input-derived finding", finding_ids),
        ("canonical match", match_ids),
        ("collision relation", relation_ids),
        ("candidate delta", candidate_ids),
        ("contradiction/gap", gap_ids),
        ("evidence source", source_ids),
        ("uncertainty", uncertainty_ids),
    ):
        duplicates = _duplicates(values)
        if duplicates:
            errors.append(f"duplicate {label} IDs: {duplicates}")

    object_id_set = set(object_ids)
    finding_id_set = set(finding_ids)
    match_id_set = set(match_ids)
    relation_id_set = set(relation_ids)
    source_id_set = set(source_ids)
    for finding in output["input_derived_findings"]:
        unknown = sorted(set(finding["input_object_ids"]) - object_id_set)
        if unknown:
            errors.append(f"{finding['finding_id']}: unknown input object IDs {unknown}")

    functions, claims = _canonical_maps()
    for match in output["existing_canonical_matches"]:
        is_function = match["registry_kind"] == "FUNCTION_ASSET"
        records = functions if is_function else claims
        expected_path = FUNCTION_AUTHORITY if is_function else NONFUNCTION_AUTHORITY
        if match["authority_path"] != expected_path:
            errors.append(f"{match['match_id']}: historical or wrong registry cannot establish Current identity")
        record = records.get(match["canonical_id"])
        if record is None:
            errors.append(f"{match['match_id']}: canonical ID is absent from the Current registry")
            continue
        title = record["title"] if is_function else record["canonical_title"]
        for field, expected in (
            ("canonical_title", title),
            ("record_sha256", record["record_sha256"]),
            ("final_disposition", record["final_disposition"]),
            ("claim_ceiling", record["claim_ceiling"]),
        ):
            if match[field] != expected:
                errors.append(f"{match['match_id']}: {field} differs from the Current canonical record")

    for relation in output["collision_relations"]:
        unknown_findings = sorted(set(relation["input_finding_ids"]) - finding_id_set)
        unknown_matches = sorted(set(relation["canonical_match_ids"]) - match_id_set)
        unknown_sources = sorted(set(relation["evidence_source_ids"]) - source_id_set)
        if unknown_findings:
            errors.append(f"{relation['relation_id']}: unknown input-derived findings {unknown_findings}")
        if unknown_matches:
            errors.append(f"{relation['relation_id']}: unknown canonical matches {unknown_matches}")
        if unknown_sources:
            errors.append(f"{relation['relation_id']}: unknown evidence sources {unknown_sources}")
        if relation["relation_type"] in MATCH_REQUIRED_RELATIONS and not relation["canonical_match_ids"]:
            errors.append(f"{relation['relation_id']}: {relation['relation_type']} requires canonical collision evidence")

    source_statements = {_normalize_text(row["statement"]) for row in output["input_derived_findings"]}
    for candidate in output["candidate_deltas"]:
        unknown_findings = sorted(set(candidate["derived_from_input_finding_ids"]) - finding_id_set)
        unknown_matches = sorted(set(candidate["canonical_match_ids"]) - match_id_set)
        unknown_relations = sorted(set(candidate["relation_ids"]) - relation_id_set)
        if unknown_findings:
            errors.append(f"{candidate['candidate_id']}: unknown input-derived findings {unknown_findings}")
        if unknown_matches:
            errors.append(f"{candidate['candidate_id']}: unknown canonical matches {unknown_matches}")
        if unknown_relations:
            errors.append(f"{candidate['candidate_id']}: unknown collision relations {unknown_relations}")
        if _normalize_text(candidate["statement"]) in source_statements:
            errors.append(f"{candidate['candidate_id']}: input-explicit content cannot be relabelled as a candidate delta")

    known_refs = (
        finding_id_set
        | match_id_set
        | relation_id_set
        | set(candidate_ids)
        | set(gap_ids)
        | source_id_set
        | set(uncertainty_ids)
    )
    for item in output["contradictions_gaps"]:
        unknown = sorted(set(item["basis_refs"]) - known_refs)
        if unknown:
            errors.append(f"{item['item_id']}: unknown basis references {unknown}")
    for source in output["evidence_sources"]:
        expected_effect = EVIDENCE_EFFECTS[source["source_kind"]]
        if source["authority_effect"] != expected_effect:
            errors.append(f"{source['source_id']}: evidence authority effect differs from source kind")
        unknown = sorted(set(source["supports_refs"]) - known_refs)
        if unknown:
            errors.append(f"{source['source_id']}: unknown supported references {unknown}")
        if source["source_kind"] == "HISTORICAL_RETRIEVAL_HINT" and set(source["supports_refs"]) & match_id_set:
            errors.append(f"{source['source_id']}: historical material cannot support a Current canonical match")

    result = output["result"]
    acceptance = result["epistemic_acceptance_authority"]
    accepted = result["epistemic_status"] == "ACCEPTED_BY_SEPARATE_CURRENT_AUTHORITY"
    if accepted and acceptance is None:
        errors.append("epistemic acceptance requires a separately identified Current authority")
    if not accepted and acceptance is not None:
        errors.append("epistemic acceptance authority cannot appear without an accepted epistemic status")
    if acceptance is not None:
        source = next((row for row in output["evidence_sources"] if row["source_id"] == acceptance["authority_source_id"]), None)
        if source is None or source["source_kind"] != "CURRENT_EPISTEMIC_AUTHORITY":
            errors.append("epistemic acceptance authority must reference CURRENT_EPISTEMIC_AUTHORITY evidence")

    return errors


def render_human(output: dict[str, Any]) -> str:
    errors = validate_output(output)
    if errors:
        raise IgnitionRunOutputError("; ".join(errors))
    result = output["result"]
    operation = output["operation_path"]
    lines = [
        result["summary"],
        "",
        f"Operation: `{operation['operation_id']}` ({operation['registry_status']}, `{output['run_mode']}`).",
    ]
    if output["collision_relations"]:
        lines.extend(["", "Key relations:"])
        lines.extend(f"- {row['statement']} (`{row['relation_type']}`)" for row in output["collision_relations"])
    if output["candidate_deltas"]:
        lines.extend(["", "Candidate deltas (not canonical assets):"])
        lines.extend(f"- {row['statement']}" for row in output["candidate_deltas"])
    if output["contradictions_gaps"]:
        lines.extend(["", "Contradictions / gaps:"])
        lines.extend(f"- {row['statement']} (`{row['resolution_status']}`)" for row in output["contradictions_gaps"])
    if output["uncertainty"]:
        lines.extend(["", "Uncertainty:"])
        lines.extend(f"- {row['statement']} Consequence: {row['consequence']}" for row in output["uncertainty"])
    lines.extend([
        "",
        f"Claim ceiling: {output['claim_ceiling']}",
        f"Stop reason: `{output['stop']['stop_reason']}`",
    ])
    if output["stop"]["optional_next_action"]:
        lines.append(f"Optional next action: {output['stop']['optional_next_action']}")
    lines.append(
        f"Audit recovery: machine profile `{output['run_id']}` under `IGNITION_RUN_OUTPUT_CONTRACT_R1`."
    )
    return "\n".join(lines).rstrip() + "\n"


def _pointer_parent(document: Any, pointer: str) -> tuple[Any, str]:
    if not pointer.startswith("/"):
        raise IgnitionRunOutputError(f"fixture mutation pointer must start with /: {pointer}")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]
    value = document
    for part in parts[:-1]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value, parts[-1]


def apply_fixture_mutations(base: dict[str, Any], mutations: list[dict[str, Any]]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for mutation in mutations:
        parent, key = _pointer_parent(result, mutation["path"])
        operation = mutation["op"]
        if operation == "set":
            if isinstance(parent, list):
                parent[int(key)] = copy.deepcopy(mutation["value"])
            else:
                parent[key] = copy.deepcopy(mutation["value"])
        elif operation == "delete":
            if isinstance(parent, list):
                del parent[int(key)]
            else:
                del parent[key]
        elif operation == "append":
            target = parent[int(key)] if isinstance(parent, list) else parent[key]
            if not isinstance(target, list):
                raise IgnitionRunOutputError(f"append target is not a list: {mutation['path']}")
            target.append(copy.deepcopy(mutation["value"]))
        else:
            raise IgnitionRunOutputError(f"unsupported fixture mutation operation: {operation}")
    return result


def validate_fixtures(document: dict[str, Any] | None = None) -> list[str]:
    fixtures = document if document is not None else load_json(FIXTURE_PATH)
    base = fixtures.get("base_output") if isinstance(fixtures, dict) else None
    cases = fixtures.get("cases", []) if isinstance(fixtures, dict) else []
    if not isinstance(base, dict) or not isinstance(cases, list) or not cases:
        return ["unified output fixtures require a base_output and nonempty cases"]
    errors: list[str] = []
    case_ids: list[str] = []
    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str):
            errors.append("every unified output fixture must have a case_id")
            continue
        case_ids.append(case_id)
        try:
            output = apply_fixture_mutations(base, case.get("mutations", []))
            actual_errors = validate_output(output)
        except (KeyError, TypeError, IgnitionRunOutputError) as exc:
            actual_errors = [str(exc)]
        expected_valid = case.get("expected_valid")
        if expected_valid is True and actual_errors:
            errors.append(f"{case_id}: expected valid, got {actual_errors}")
        elif expected_valid is False:
            if not actual_errors:
                errors.append(f"{case_id}: expected invalid, got valid")
            for text in case.get("expected_error_contains", []):
                if not any(text in error for error in actual_errors):
                    errors.append(f"{case_id}: expected error containing {text!r}, got {actual_errors}")
    if len(case_ids) != len(set(case_ids)):
        errors.append("unified output fixture case IDs must be unique")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate_fixtures()
    if errors:
        print("IGNITION_RUN_OUTPUT_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    fixtures = load_json(FIXTURE_PATH)
    _ = render_human(fixtures["base_output"])
    print(
        "IGNITION_RUN_OUTPUT_OK "
        f"semantics={len(SEMANTIC_FIELDS)} guards={len(BOUNDARY_GUARDS)} fixtures={len(fixtures['cases'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
