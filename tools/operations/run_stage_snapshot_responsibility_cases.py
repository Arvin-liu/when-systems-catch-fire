#!/usr/bin/env python3
"""Run stable, instance-level responsibility actor acceptance evidence."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from stage_snapshot_contract import (
    ContractError,
    README,
    REGISTRY,
    REQUEST_SCHEMA,
    SCHEMA,
    load,
    readme_with_projection,
    render_projection,
    schema_errors,
    validate_materialized_projection,
    validate_registry,
    validate_request,
)


ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests/stage_snapshot_responsibility_actor_cases.json"


def positive_request(cases: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_version": "1.1.0",
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


def rejected(call: Callable[[], None]) -> tuple[bool, str | None]:
    try:
        call()
    except (ContractError, AssertionError) as exc:
        return True, str(exc)
    return False, None


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

    def a09(registry: dict[str, Any]) -> None:
        registry["snapshots"].append(copy.deepcopy(item(registry)))

    def a11(registry: dict[str, Any]) -> None:
        item(registry)["lifecycle_state"] = "REJECTED"
        item(registry)["outcome"] = "SUCCESS"

    def a12() -> None:
        instance = copy.deepcopy(base)
        item(instance)["homepage"]["summary"] = "drifted public text"
        validate_materialized_projection(instance, readme, projection_doc)

    def a13(registry: dict[str, Any]) -> None:
        item(registry)["publication_status"] = "SUPERSEDED_SNAPSHOT"
        item(registry)["source"]["snapshot_record_merged_to_main"] = True

    def a16() -> None:
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
        ("A09", registry_call(a09)),
        ("A10", registry_call(lambda r: item(r).__setitem__("known_limitations_and_blockers", []))),
        ("A11", registry_call(a11)),
        ("A12", a12),
        ("A13", registry_call(a13)),
        ("A14a", registry_call(lambda r: item(r).__setitem__("summary", item(r)["summary"] + " ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"))),
        ("A14b", registry_call(lambda r: item(r).__setitem__("summary", item(r)["summary"] + " /Users/private/raw.txt"))),
        ("A15a", registry_call(lambda r: item(r)["responsibility"].__setitem__("founder_responsibility_inferred", True))),
        ("A15b", registry_call(lambda r: item(r)["responsibility"].__setitem__("upstream_responsibility_inferred", True))),
        ("A15c", registry_call(lambda r: item(r)["responsibility"]["responsible_actor"].__setitem__("name", "Codex Agent"))),
        ("A15d", registry_call(lambda r: item(r)["responsibility"]["responsible_actor"].__setitem__("name", "automated publication workflow"))),
        ("A16", a16),
        ("A17", registry_call(lambda r: item(r)["source"].__setitem__("snapshot_record_merged_to_main", True))),
        ("A18", registry_call(lambda r: item(r).__setitem__("affects_formal_capability", True))),
    ]


def main() -> int:
    cases = load(CASES)
    base_registry = load(REGISTRY)
    registry_schema = load(SCHEMA)
    request_schema = load(REQUEST_SCHEMA)
    results: list[dict[str, Any]] = []
    legacy_results: list[dict[str, Any]] = []

    for case_id, call in legacy_attack_calls(base_registry, cases):
        did_reject, error = rejected(call)
        legacy_results.append({
            "id": case_id, "expected": "REJECT",
            "runtime_result": "REJECT" if did_reject else "ACCEPT",
            "pass": did_reject, "error": error,
        })

    for case in cases["attack_cases"]:
        for field in ("responsible_actor", "publisher_actor"):
            instance = copy.deepcopy(base_registry)
            instance["snapshots"][0]["responsibility"][field]["name"] = case["name"]
            schema_result = "REJECT" if schema_errors(instance, registry_schema) else "ACCEPT"
            did_reject, error = rejected(lambda instance=instance: validate_registry(instance))
            results.append({
                "id": f"{case['id']}.registry.{field}",
                "expected": "REJECT", "schema_result": schema_result,
                "runtime_result": "REJECT" if did_reject else "ACCEPT",
                "pass": did_reject, "error": error,
            })
        for field in ("responsible_actor", "proposed_publisher_actor"):
            instance = positive_request(cases)
            instance["responsibility"][field]["name"] = case["name"]
            schema_result = "REJECT" if schema_errors(instance, request_schema) else "ACCEPT"
            did_reject, error = rejected(lambda instance=instance: validate_request(instance))
            results.append({
                "id": f"{case['id']}.request.{field}",
                "expected": "REJECT", "schema_result": schema_result,
                "runtime_result": "REJECT" if did_reject else "ACCEPT",
                "pass": did_reject, "error": error,
            })

    for case in cases["positive_cases"]:
        instance = copy.deepcopy(base_registry)
        instance["snapshots"][0]["responsibility"]["responsible_actor"] = copy.deepcopy(case["actor"])
        schema_result = "ACCEPT" if not schema_errors(instance, registry_schema) else "REJECT"
        accepted = True
        error = None
        try:
            validate_registry(instance)
        except (ContractError, AssertionError) as exc:
            accepted, error = False, str(exc)
        results.append({
            "id": case["id"], "expected": "ACCEPT", "schema_result": schema_result,
            "runtime_result": "ACCEPT" if accepted else "REJECT",
            "pass": accepted and schema_result == "ACCEPT", "error": error,
        })

    base_result = validate_registry(copy.deepcopy(base_registry))
    results.append({
        "id": "P15c-EXECUTION-AGENT-AND-WORKFLOW-RECORDED",
        "expected": "ACCEPT", "schema_result": "ACCEPT",
        "runtime_result": "ACCEPT" if base_result["status"] == "PASS" else "REJECT",
        "pass": base_result["status"] == "PASS", "error": None,
    })

    passed = all(result["pass"] for result in results + legacy_results)
    payload = {
        "fixture": str(CASES.relative_to(ROOT)),
        "gate": "stage_snapshot_responsibility_actor",
        "status": "PASS" if passed else "FAIL",
        "case_count": len(results),
        "results": results,
        "legacy_attack_matrix": {
            "status": "PASS" if all(result["pass"] for result in legacy_results) else "FAIL",
            "passed": sum(bool(result["pass"]) for result in legacy_results),
            "total": len(legacy_results),
            "results": legacy_results,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
