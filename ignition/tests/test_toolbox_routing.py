from __future__ import annotations

import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


def profile(task_id: str, inputs: list[str], outputs: list[str], *, allowed_network_hosts: list[str] | None = None) -> dict:
    result = {
        "task_id": task_id,
        "current_ref": "refs/heads/main@483658e2ff57ad553c3fda762ed855a8bd93ebbe",
        "input_types": inputs,
        "required_outputs": outputs,
        "allowed_execution_modes": ["READ_ONLY_RUN"],
    }
    if allowed_network_hosts is not None:
        result["allowed_network_hosts"] = allowed_network_hosts
    return result


class AdaptiveToolRouteTests(unittest.TestCase):
    def test_candidate_path_escape_is_rejected(self) -> None:
        self.assertFalse(planner.route_source_path_is_safe("ignition/../outside.py"))
        self.assertFalse(planner.route_source_path_is_safe("ignition/tools/../../outside.py"))

    def test_simple_task_selects_one_matching_registered_operation(self) -> None:
        result = planner.plan_tool_route(profile(
            "simple-current-read", ["Current state query"], ["Current identity snapshot"],
        ))
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in result["selected_tools"]], ["ignition.recover_current_state"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["current_ref_binding"], "CALLER_SUPPLIED_NOT_RESOLVED_BY_THIS_PLANNER")

    def test_evidence_task_expands_to_complementary_operations(self) -> None:
        result = planner.plan_tool_route(profile(
            "claim-and-source", ["claim", "source record", "claim-to-source relation"],
            ["claim-governance findings", "provenance validation report"],
        ))
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual(
            {row["tool_id"] for row in result["selected_tools"]},
            {"knowledge.validate_claim", "knowledge.validate_evidence_link"},
        )
        self.assertEqual(result["cost_estimate"]["status"], "UNKNOWN")
        self.assertIn("GREEDY_NOT_PROVEN_GLOBAL_OPTIMUM", result["selection_rule"])

    def test_experimental_tool_is_excluded_until_explicitly_allowlisted(self) -> None:
        task = profile("cluster-source-brief", ["article cluster ID"], ["source-backed cluster member brief"])
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(task, include_experimental_tool_ids=["knowledge.cluster_source_brief"])
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(included["selected_tools"][0]["kind"], "EXPERIMENTAL_OPTIONAL_TOOL")
        self.assertFalse(included["execution_authorized"])
        self.assertEqual(included["source_refs"]["current_registry_git_blob_sha1"], "21fe1bfcdb0d9762edd60339aca14f1040393fc7")

    def test_batch_identity_resolution_is_excluded_until_explicitly_allowlisted(self) -> None:
        task = profile(
            "batch-current-identity-resolution",
            ["JSON stdin object with an ordered nonempty array of exact reference strings"],
            ["input-ordered canonical identity resolution rows", "authority and resolver SHA-256 receipt"],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["foundation.batch_resolve_current_asset_references"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["foundation.batch_resolve_current_asset_references"],
        )
        self.assertFalse(included["execution_authorized"])

    def test_pack_catalog_inspector_is_excluded_until_explicitly_allowlisted(self) -> None:
        task = profile(
            "declared-pack-capability-inspection",
            ["Pack metadata list request"],
            ["declared Pack metadata", "declared capability route list", "manifest and source-tree SHA-256 references"],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["runtime.inspect_declared_pack_catalog"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["runtime.inspect_declared_pack_catalog"],
        )
        self.assertFalse(included["execution_authorized"])

    def test_current_asset_record_reader_is_excluded_until_explicitly_allowlisted(self) -> None:
        task = profile(
            "read-full-current-foundation-record",
            ["JSON stdin object containing exactly one exact canonical_id string"],
            [
                "complete Current function-identity card or non-function claim record",
                "verified record digest and hashes of both registry snapshots",
            ],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["foundation.read_current_asset_card"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["foundation.read_current_asset_card"],
        )
        self.assertFalse(included["execution_authorized"])

    def test_bounded_function_os_runner_is_excluded_until_explicitly_allowlisted(self) -> None:
        task = profile(
            "bounded-symbolic-function-execution",
            ["UTF-8 JSON stdin object containing exactly one bounded FunctionSpec object and one exact input-value object"],
            ["N1-N7 execution status and single declared output when successful"],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["function_os.run_bounded_symbolic_spec"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["function_os.run_bounded_symbolic_spec"],
        )
        self.assertFalse(included["execution_authorized"])

    def test_archify_ir_exporter_is_excluded_until_explicitly_allowlisted(self) -> None:
        task = profile(
            "canonical-architecture-typed-ir-export",
            ["UTF-8 JSON stdin object containing exactly one formal_revision lowercase commit-SHA string"],
            ["typed Archify-shaped derived visualization IR with component, connection, and boundary counts"],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["visualization.build_archify_derived_ir"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["visualization.build_archify_derived_ir"],
        )
        self.assertFalse(included["execution_authorized"])

    def test_network_candidate_requires_both_tool_allowlist_and_exact_host_allowance(self) -> None:
        task = profile(
            "live-crossref-metadata-comparison",
            ["UTF-8 JSON stdin object with one to ten unique DOI, expected-title, expected-year records"],
            ["input-ordered Crossref metadata comparison rows", "per-response SHA-256 and explicit HTTP or network outcome summary"],
        )
        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["allowed_network_hosts"], [])
        self.assertEqual(default["network_authority_binding"], "NO_NETWORK_HOSTS_ALLOWED")

        allowlisted_without_host = planner.plan_tool_route(
            task, include_experimental_tool_ids=["research.verify_crossref_metadata"],
        )
        self.assertEqual(allowlisted_without_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": "research.verify_crossref_metadata", "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            allowlisted_without_host["rejected_candidates"],
        )

        permitted_host = planner.plan_tool_route(
            profile(
                "live-crossref-metadata-comparison",
                task["input_types"], task["required_outputs"],
                allowed_network_hosts=["api.crossref.org"],
            ),
            include_experimental_tool_ids=["research.verify_crossref_metadata"],
        )
        self.assertEqual(permitted_host["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted_host["selected_tools"]], ["research.verify_crossref_metadata"])
        self.assertEqual(permitted_host["selected_tools"][0]["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertEqual(permitted_host["network_authority_binding"], "CALLER_SUPPLIED_NOT_AUTHORITY_VERIFIED_BY_THIS_PLANNER")
        self.assertFalse(permitted_host["execution_authorized"])

    def test_network_route_rejects_wildcards_urls_and_ports(self) -> None:
        task = profile("invalid-network-route", ["x"], ["y"], allowed_network_hosts=["*.crossref.org"])
        with self.assertRaises(planner.RunPlanningError):
            planner.plan_tool_route(task)
        for invalid in ("https://api.crossref.org", "api.crossref.org:443", "127.0.0.1"):
            with self.subTest(invalid=invalid), self.assertRaises(planner.RunPlanningError):
                planner.plan_tool_route(profile("invalid-host", ["x"], ["y"], allowed_network_hosts=[invalid]))
        too_many = [f"host-{index}.example.org" for index in range(planner.MAX_NETWORK_HOSTS + 1)]
        with self.assertRaisesRegex(planner.RunPlanningError, "no more than"):
            planner.plan_tool_route(profile("too-many-hosts", ["x"], ["y"], allowed_network_hosts=too_many))

    def test_evidence_program_validator_stays_out_of_router_without_git_metadata_path_support(self) -> None:
        task = profile(
            "fixed-evidence-program-validation",
            ["fixed checked-out ignition/evidence-program snapshot plus containing checkout Git metadata for read-only ancestry checks"],
            ["compact validator status, check count, failure count, and bounded failure details"],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["research.validate_evidence_program_snapshot"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "INCOMPLETE")
        self.assertEqual(included["selected_tools"], [])
        self.assertIn(
            {"tool_id": "research.validate_evidence_program_snapshot", "reason": "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"},
            included["rejected_candidates"],
        )

    def test_unknown_experimental_allowlist_id_is_reported(self) -> None:
        result = planner.plan_tool_route(
            profile("unknown-opt-in", ["article cluster ID"], ["source-backed cluster member brief"]),
            include_experimental_tool_ids=["knowledge.not_a_real_tool"],
        )
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": "knowledge.not_a_real_tool", "reason": "UNKNOWN_EXPERIMENTAL_ALLOWLIST_ID"},
            result["rejected_candidates"],
        )

    def test_stale_candidate_registry_pin_fails_closed(self) -> None:
        registry_bytes = planner.REGISTRY_PATH.read_bytes()
        registry = json.loads(registry_bytes.decode("utf-8"))
        candidates = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        candidates["source_registry_blob_sha1"] = "0" * 40
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "registry.json"
            candidates_path = Path(tmp) / "candidates.json"
            registry_path.write_bytes(registry_bytes)
            candidates_path.write_text(json.dumps(candidates), encoding="utf-8")
            with patch.object(planner, "REGISTRY_PATH", registry_path), patch.object(planner, "EXPERIMENTAL_TOOL_CARDS_PATH", candidates_path):
                with self.assertRaisesRegex(planner.RunPlanningError, "stale"):
                    planner.plan_tool_route(
                        profile("stale-card-catalog", ["article cluster ID"], ["source-backed cluster member brief"]),
                        include_experimental_tool_ids=["knowledge.cluster_source_brief"],
                    )

    def test_read_only_network_route_rejects_host_without_explicit_allowance(self) -> None:
        registry_bytes = planner.REGISTRY_PATH.read_bytes()
        candidates = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        candidates["candidates"][0]["permissions"]["network"] = True
        candidates["candidates"][0]["permissions"]["network_hosts"] = ["example.org"]
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "registry.json"
            candidates_path = Path(tmp) / "candidates.json"
            registry_path.write_bytes(registry_bytes)
            candidates_path.write_text(json.dumps(candidates), encoding="utf-8")
            with patch.object(planner, "REGISTRY_PATH", registry_path), patch.object(planner, "EXPERIMENTAL_TOOL_CARDS_PATH", candidates_path):
                result = planner.plan_tool_route(
                    profile("readonly-network-negative-control", ["article cluster ID"], ["source-backed cluster member brief"]),
                    include_experimental_tool_ids=["knowledge.cluster_source_brief"],
                )
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": "knowledge.cluster_source_brief", "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            result["rejected_candidates"],
        )

    def test_route_expands_without_a_fixed_tool_count(self) -> None:
        result = planner.plan_tool_route(profile(
            "three-output-task",
            ["claim", "source record", "claim-to-source relation", "Current state query"],
            ["claim-governance findings", "provenance validation report", "Current identity snapshot"],
        ))
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual(len(result["selected_tools"]), 3)

    def test_owner_deferred_external_operation_never_routes(self) -> None:
        result = planner.plan_tool_route({
            "task_id": "external-action-stop",
            "current_ref": "refs/heads/main@483658e2ff57ad553c3fda762ed855a8bd93ebbe",
            "input_types": ["explicit Owner external-action request", "executor admission evidence"],
            "required_outputs": ["bounded execution receipt if separately authorized and validated"],
            "allowed_execution_modes": ["EXTERNAL_ACTION_RUN"],
        })
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["selected_tools"], [])
        self.assertIn("NOT_CURRENT_CALLABLE", {row["reason"] for row in result["rejected_candidates"]})

    def test_missing_contract_output_is_reported_not_guessed(self) -> None:
        result = planner.plan_tool_route(profile("unknown-output", ["claim"], ["unregistered output"]))
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["unmet_outputs"], ["unregistered output"])
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
