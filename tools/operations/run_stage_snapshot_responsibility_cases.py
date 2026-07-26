#!/usr/bin/env python3
"""Run stable, instance-level two-surface responsibility actor evidence."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

try:
    from tools.operations.stage_snapshot_contract import (
        ACTOR_REGISTRY, ContractError, README, REGISTRY, REQUEST_SCHEMA, SCHEMA, load,
        readme_with_projection, render_projection, schema_errors,
        require, resolve_actor, validate_actor_contract_sources, validate_actor_registry,
        validate_materialized_projection, validate_registry, validate_request,
    )
except ModuleNotFoundError:  # Direct script execution from tools/operations.
    from stage_snapshot_contract import (
        ACTOR_REGISTRY, ContractError, README, REGISTRY, REQUEST_SCHEMA, SCHEMA, load,
        readme_with_projection, render_projection, schema_errors,
        require, resolve_actor, validate_actor_contract_sources, validate_actor_registry,
        validate_materialized_projection, validate_registry, validate_request,
    )


ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests/stage_snapshot_responsibility_actor_cases.json"


def positive_request(cases: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_version": "1.2.0",
        "task_id": "ACTOR-GATE-EVIDENCE",
        "result_object": "stage snapshot responsibility actor gate",
        "source_head": "1" * 40,
        "evidence_entries": ["https://github.com/Arvin-liu/when-systems-catch-fire/pull/134"],
        "lifecycle_state": "CANDIDATE",
        "claim_ceiling": "Responsibility actor contract evidence only.",
        "homepage_summary": "Responsibility actor contract candidate awaits independent review.",
        "limitations_and_incomplete": ["The method candidate remains Draft and is not Current."],
        "responsibility": {
            "responsible_actor": copy.deepcopy(cases["positive_cases"][0]["actor"]),
            "proposed_publisher_actor": copy.deepcopy(cases["positive_cases"][1]["actor"]),
            "execution_agents": [{
                "name": "Codex Agent",
                "role": "Test execution tool, not final accountability",
                "evidence_reference": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/134",
            }],
            "automation_workflows": [{
                "name": "GitHub Actions",
                "role": "CI workflow, not final accountability",
                "evidence_reference": "https://github.com/Arvin-liu/when-systems-catch-fire/actions",
            }],
            "founder_responsibility_inferred": False,
            "upstream_responsibility_inferred": False,
        },
        "recommendation": "REVISE",
        "agent_claims_published_to_main": False,
    }


def legacy_free_text_actor(name: str) -> dict[str, Any]:
    """Model the rejected pre-R2 interface where a name could self-assert identity."""
    return {
        "type": "ORGANIZATION",
        "name": name,
        "stable_id": "org:unreviewed/free-text-claim",
        "role": "Claimed final accountability",
        "accountability_reference": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/134",
        "human_or_governance_contact": "https://github.com/Arvin-liu/when-systems-catch-fire/issues",
    }


def rejected(call: Callable[[], None]) -> tuple[bool, str | None]:
    try:
        call()
    except (ContractError, AssertionError) as exc:
        return True, str(exc)
    return False, None


def joint_case_pass(expected: str, schema_result: str, runtime_result: str) -> bool:
    """Both independent surfaces are verdict-bearing; disagreement always fails."""
    return schema_result == expected and runtime_result == expected


def evaluate_case(
    *, case_id: str, expected: str, instance: dict[str, Any], schema: dict[str, Any],
    runtime_call: Callable[[], None],
) -> dict[str, Any]:
    schema_result = "REJECT" if schema_errors(instance, schema) else "ACCEPT"
    did_reject, error = rejected(runtime_call)
    runtime_result = "REJECT" if did_reject else "ACCEPT"
    return {
        "id": case_id,
        "expected": expected,
        "schema_result": schema_result,
        "runtime_result": runtime_result,
        "pass": joint_case_pass(expected, schema_result, runtime_result),
        "error": error,
    }


def mutated_registry(base: dict[str, Any], mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    instance = copy.deepcopy(base)
    mutate(instance)
    return instance


def legacy_attack_calls(base: dict[str, Any], cases: dict[str, Any]) -> list[tuple[str, Callable[[], None]]]:
    item = lambda registry: registry["snapshots"][0]
    request = positive_request(cases)
    projection = render_projection(base)
    readme = readme_with_projection(README.read_text(encoding="utf-8"), projection)
    projection_doc = "# Recent Stage Results / 正在炼化\n\n" + projection.split("\n", 2)[2]

    def registry_call(mutate: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
        return lambda: validate_registry(mutated_registry(base, mutate))

    def duplicate(registry: dict[str, Any]) -> None:
        registry["snapshots"].append(copy.deepcopy(item(registry)))

    def disguised_rejection(registry: dict[str, Any]) -> None:
        item(registry)["lifecycle_state"] = "REJECTED"
        item(registry)["outcome"] = "SUCCESS"

    def drifted_projection() -> None:
        instance = copy.deepcopy(base)
        item(instance)["homepage"]["summary"] = "drifted public text"
        validate_materialized_projection(instance, readme, projection_doc)

    def superseded_without_successor(registry: dict[str, Any]) -> None:
        item(registry)["publication_status"] = "SUPERSEDED_SNAPSHOT"
        item(registry)["source"]["snapshot_record_merged_to_main"] = True

    def agent_claims_publication() -> None:
        instance = copy.deepcopy(request)
        instance["agent_claims_published_to_main"] = True
        validate_request(instance)

    return [
        ("A01", registry_call(lambda r: item(r).__setitem__("accepted", True))),
        ("A02", registry_call(lambda r: item(r).__setitem__("current", True))),
        ("A03", registry_call(lambda r: item(r).__setitem__("activated", True))),
        ("A04", registry_call(lambda r: item(r).__setitem__("affects_formal_capability", True))),
        ("A05", registry_call(lambda r: item(r)["source"].__setitem__("candidate_payload_merged_to_main", True))),
        ("A06", registry_call(lambda r: item(r)["source"].__setitem__("exact_head", "a" * 40))),
        ("A07a", registry_call(lambda r: item(r)["source"].__setitem__("pull_request_url", "https://github.com/other/repo/pull/130"))),
        ("A07b", registry_call(lambda r: item(r)["source"].__setitem__("branch", "wrong/source"))),
        ("A08", registry_call(lambda r: item(r)["evidence"]["entries"].remove(item(r)["evidence"]["relay_pull_request_url"]))),
        ("A09", registry_call(duplicate)),
        ("A10", registry_call(lambda r: item(r).__setitem__("known_limitations_and_blockers", []))),
        ("A11", registry_call(disguised_rejection)),
        ("A12", drifted_projection),
        ("A13", registry_call(superseded_without_successor)),
        ("A14a", registry_call(lambda r: item(r).__setitem__("summary", item(r)["summary"] + " ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"))),
        ("A14b", registry_call(lambda r: item(r).__setitem__("summary", item(r)["summary"] + " /Users/private/raw.txt"))),
        ("A15a", registry_call(lambda r: item(r)["responsibility"].__setitem__("founder_responsibility_inferred", True))),
        ("A15b", registry_call(lambda r: item(r)["responsibility"].__setitem__("upstream_responsibility_inferred", True))),
        ("A15c", registry_call(lambda r: item(r)["responsibility"].__setitem__("responsible_actor", legacy_free_text_actor("Codex Agent")))),
        ("A15d", registry_call(lambda r: item(r)["responsibility"].__setitem__("responsible_actor", legacy_free_text_actor("automated publication workflow")))),
        ("A16", agent_claims_publication),
        # A17 enforces the line-318 invariant (snapshot_record_merged_to_main must equal
        # the main-state of publication_status). Set the INCONSISTENT value for whatever the
        # current base publication_status is, so the attack stays valid regardless of base drift.
        # (The base is now PUBLISHED_SNAPSHOT with merged_to_main=True; flipping to a hard-coded
        # True would be a no-op on an already-valid state and stop exercising the invariant.)
        ("A17", registry_call(lambda r: item(r)["source"].__setitem__(
            "snapshot_record_merged_to_main",
            not (item(r)["publication_status"] in {"PUBLISHED_SNAPSHOT", "SUPERSEDED_SNAPSHOT", "WITHDRAWN_SNAPSHOT", "HISTORICAL_SNAPSHOT"}),
        ))),
        ("A18", registry_call(lambda r: item(r).__setitem__("affects_formal_capability", True))),
    ]


def attack_matrix(
    cases: list[dict[str, str]], base_registry: dict[str, Any], registry_schema: dict[str, Any],
    request_schema: dict[str, Any], all_cases: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        for field in ("responsible_actor", "publisher_actor"):
            instance = copy.deepcopy(base_registry)
            instance["snapshots"][0]["responsibility"][field] = legacy_free_text_actor(case["name"])
            rows.append(evaluate_case(
                case_id=f"{case['id']}.registry.{field}", expected="REJECT",
                instance=instance, schema=registry_schema,
                runtime_call=lambda instance=instance: validate_registry(instance),
            ))
        for field in ("responsible_actor", "proposed_publisher_actor"):
            instance = positive_request(all_cases)
            instance["responsibility"][field] = legacy_free_text_actor(case["name"])
            rows.append(evaluate_case(
                case_id=f"{case['id']}.request.{field}", expected="REJECT",
                instance=instance, schema=request_schema,
                runtime_call=lambda instance=instance: validate_request(instance),
            ))
    return rows


def positive_matrix(
    cases: dict[str, Any], base_registry: dict[str, Any], registry_schema: dict[str, Any],
    request_schema: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases["positive_cases"]:
        for field in ("responsible_actor", "publisher_actor"):
            instance = copy.deepcopy(base_registry)
            instance["snapshots"][0]["responsibility"][field] = copy.deepcopy(case["actor"])
            rows.append(evaluate_case(
                case_id=f"{case['id']}.registry.{field}", expected="ACCEPT",
                instance=instance, schema=registry_schema,
                runtime_call=lambda instance=instance: validate_registry(instance),
            ))
        for field in ("responsible_actor", "proposed_publisher_actor"):
            instance = positive_request(cases)
            instance["responsibility"][field] = copy.deepcopy(case["actor"])
            rows.append(evaluate_case(
                case_id=f"{case['id']}.request.{field}", expected="ACCEPT",
                instance=instance, schema=request_schema,
                runtime_call=lambda instance=instance: validate_request(instance),
            ))

    registry_instance = copy.deepcopy(base_registry)
    rows.append(evaluate_case(
        case_id="P15c.registry.technical-records-with-accountable-ref", expected="ACCEPT",
        instance=registry_instance, schema=registry_schema,
        runtime_call=lambda: validate_registry(registry_instance),
    ))
    request_instance = positive_request(cases)
    rows.append(evaluate_case(
        case_id="P15c.request.technical-records-with-accountable-ref", expected="ACCEPT",
        instance=request_instance, schema=request_schema,
        runtime_call=lambda: validate_request(request_instance),
    ))
    return rows


def summarize(rows: list[dict[str, Any]], expected: str) -> dict[str, Any]:
    schema_match = sum(row["schema_result"] == expected for row in rows)
    runtime_match = sum(row["runtime_result"] == expected for row in rows)
    joint = sum(bool(row["pass"]) for row in rows)
    return {
        "expected": expected,
        "total": len(rows),
        "schema_matches": schema_match,
        "runtime_matches": runtime_match,
        "joint_passes": joint,
        "status": "PASS" if joint == len(rows) else "FAIL",
    }


def mutation_probe_calls(
    cases: dict[str, Any], base_registry: dict[str, Any],
    registry_schema: dict[str, Any], request_schema: dict[str, Any],
) -> list[tuple[str, Callable[[], None]]]:
    actor_registry = load(ACTOR_REGISTRY)

    def gate_schema_ignored() -> None:
        require(joint_case_pass("REJECT", "ACCEPT", "REJECT"), "joint gate blocked a Schema-ignored mutation")

    def gate_runtime_ignored() -> None:
        require(joint_case_pass("REJECT", "REJECT", "ACCEPT"), "joint gate blocked a runtime-ignored mutation")

    def arbitrary_actor_ref() -> None:
        instance = copy.deepcopy(base_registry)
        instance["snapshots"][0]["responsibility"]["responsible_actor"]["actor_ref"] = "org:arbitrary/self-asserted"
        validate_registry(instance)

    def registry_resolution_bypass() -> None:
        resolve_actor({"actor_ref": "org:missing/unresolved"}, "mutation probe")

    def non_accountable_type() -> None:
        instance = copy.deepcopy(actor_registry)
        instance["actors"][1]["type"] = "AGENT"
        validate_actor_registry(instance)

    def technical_agent_as_final() -> None:
        instance = copy.deepcopy(base_registry)
        instance["snapshots"][0]["responsibility"]["responsible_actor"] = legacy_free_text_actor("Codex Agent")
        validate_registry(instance)

    def delete_registry_field(field: str) -> Callable[[], None]:
        def call() -> None:
            instance = copy.deepcopy(actor_registry)
            instance["actors"][1].pop(field)
            validate_actor_registry(instance)
        return call

    def nonexistent_actor_id() -> None:
        instance = copy.deepcopy(base_registry)
        instance["snapshots"][0]["responsibility"]["responsible_actor"] = {"actor_ref": "org:does-not-exist"}
        validate_registry(instance)

    def retired_actor() -> None:
        instance = copy.deepcopy(actor_registry)
        actor = instance["actors"][1]
        actor["status"] = "RETIRED"
        actor["retired_at"] = "2026-07-26T01:00:00+08:00"
        actor["history"].append({
            "record_id": "ACTOR-ORG-IGNITION-GOVERNANCE-002",
            "changed_at": "2026-07-26T01:00:00+08:00",
            "change_type": "RETIRED",
            "supersedes_record_id": "ACTOR-ORG-IGNITION-GOVERNANCE-001",
            "reason": "Mutation probe retirement.",
            "source_reference": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/135",
        })
        validate_registry(copy.deepcopy(base_registry), actor_registry=instance)

    def silent_actor_change() -> None:
        instance = copy.deepcopy(base_registry)
        original = instance["snapshots"][0]
        original["snapshot_id"] = "STAGE-MUTATION-ACTOR-001"
        original["relationships"]["successors"] = ["STAGE-MUTATION-ACTOR-002"]
        successor = copy.deepcopy(original)
        successor["snapshot_id"] = "STAGE-MUTATION-ACTOR-002"
        successor["relationships"] = {"predecessors": [original["snapshot_id"]], "successors": [], "supersedes": [], "superseded_by": []}
        successor["responsibility"]["responsible_actor"] = copy.deepcopy(cases["positive_cases"][0]["actor"])
        successor["responsibility"]["responsibility_record"]["record_id"] = "RESP-MUTATION-ACTOR-002"
        successor["responsibility"]["responsibility_record"]["supersedes_record_id"] = None
        instance["snapshots"] = [original, successor]
        validate_registry(instance)

    def schema_sets_differ() -> None:
        instance = copy.deepcopy(request_schema)
        instance["$defs"]["accountableActorRef"]["properties"]["actor_ref"]["enum"].pop()
        validate_actor_contract_sources(request_schema=instance)

    def generated_enum_stale() -> None:
        instance = copy.deepcopy(registry_schema)
        instance["$defs"]["accountableActorRef"]["properties"]["actor_ref"]["enum"].append("org:stale/generated")
        validate_actor_contract_sources(registry_schema=instance)

    def old_case_sensitive_enum_bypass() -> None:
        instance = copy.deepcopy(base_registry)
        instance["snapshots"][0]["responsibility"]["responsible_actor"] = legacy_free_text_actor("  cOdEx   aGeNt  ")
        validate_registry(instance)

    return [
        ("M01-RUNNER-IGNORES-SCHEMA", gate_schema_ignored),
        ("M02-RUNNER-IGNORES-RUNTIME", gate_runtime_ignored),
        ("M03-ACTOR-REF-ARBITRARY-STRING", arbitrary_actor_ref),
        ("M04-ACTOR-REGISTRY-RESOLUTION-SKIPPED", registry_resolution_bypass),
        ("M05-NON-ACCOUNTABLE-TYPE-IN-REGISTRY", non_accountable_type),
        ("M06-TECHNICAL-AGENT-COPIED-TO-FINAL", technical_agent_as_final),
        ("M07-GOVERNANCE-CONTACT-DELETED", delete_registry_field("human_or_governance_contact")),
        ("M08-ACCOUNTABILITY-BASIS-DELETED", delete_registry_field("accountability_reference")),
        ("M09-NONEXISTENT-ACTOR-ID", nonexistent_actor_id),
        ("M10-RETIRED-ACTOR-USED", retired_actor),
        ("M11-SILENT-RESPONSIBILITY-CHANGE", silent_actor_change),
        ("M12-SCHEMA-RUNTIME-ACTOR-SETS-DIFFER", schema_sets_differ),
        ("M13-GENERATED-ACTOR-ENUM-STALE", generated_enum_stale),
        ("M14-OLD-CASE-SENSITIVE-NOT-ENUM-BYPASS", old_case_sensitive_enum_bypass),
    ]


def main() -> int:
    cases = load(CASES)
    base_registry = load(REGISTRY)
    registry_schema = load(SCHEMA)
    request_schema = load(REQUEST_SCHEMA)

    legacy_results: list[dict[str, Any]] = []
    for case_id, call in legacy_attack_calls(base_registry, cases):
        did_reject, error = rejected(call)
        legacy_results.append({
            "id": case_id, "expected": "REJECT",
            "runtime_result": "REJECT" if did_reject else "ACCEPT",
            "pass": did_reject, "error": error,
        })

    existing_rows = attack_matrix(cases["attack_cases"], base_registry, registry_schema, request_schema, cases)
    new_rows = attack_matrix(cases["new_automation_variant_cases"], base_registry, registry_schema, request_schema, cases)
    positive_rows = positive_matrix(cases, base_registry, registry_schema, request_schema)
    mutation_results: list[dict[str, Any]] = []
    for mutation_id, call in mutation_probe_calls(cases, base_registry, registry_schema, request_schema):
        did_block, error = rejected(call)
        mutation_results.append({
            "id": mutation_id, "expected": "BLOCKED",
            "result": "BLOCKED" if did_block else "NOT_BLOCKED",
            "pass": did_block, "error": error,
        })

    passed = all(row["pass"] for row in existing_rows + new_rows + positive_rows + legacy_results + mutation_results)
    payload = {
        "fixture": str(CASES.relative_to(ROOT)),
        "gate": "stage_snapshot_responsibility_actor_two_surface",
        "verdict_rule": {
            "attack_pass": "schema_result == REJECT AND runtime_result == REJECT",
            "positive_pass": "schema_result == ACCEPT AND runtime_result == ACCEPT",
            "surface_disagreement": "FAIL",
        },
        "status": "PASS" if passed else "FAIL",
        "existing_attack_matrix": {**summarize(existing_rows, "REJECT"), "results": existing_rows},
        "new_automation_variant_matrix": {**summarize(new_rows, "REJECT"), "results": new_rows},
        "positive_matrix": {**summarize(positive_rows, "ACCEPT"), "results": positive_rows},
        "mutation_matrix": {
            "status": "PASS" if all(row["pass"] for row in mutation_results) else "FAIL",
            "blocked": sum(bool(row["pass"]) for row in mutation_results),
            "total": len(mutation_results),
            "results": mutation_results,
        },
        "legacy_attack_matrix": {
            "status": "PASS" if all(row["pass"] for row in legacy_results) else "FAIL",
            "passed": sum(bool(row["pass"]) for row in legacy_results),
            "total": len(legacy_results),
            "results": legacy_results,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
