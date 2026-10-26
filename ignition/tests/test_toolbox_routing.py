from __future__ import annotations

import hashlib
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

    def test_cluster_source_brief_c007_route_is_minimal_explicit_and_not_execution(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "knowledge.cluster_source_brief")
        task = profile("C007-source-brief-route-c1-01", card["accepted_input_types"], card["output_types"])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-cluster-source-brief-c1-evidence-r0.json").read_text(encoding="utf-8")
        )

        default = planner.plan_tool_route(task)
        opted_in = planner.plan_tool_route(task, include_experimental_tool_ids=[card["tool_id"]])
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(opted_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted_in["selected_tools"]], [card["tool_id"]])
        self.assertFalse(opted_in["execution_authorized"])
        self.assertFalse(opted_in["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opted_in["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(evidence["routing"]["default_off"]["decision"], default["decision"])
        self.assertEqual(evidence["routing"]["explicit_allowlist"]["decision"], opted_in["decision"])
        self.assertEqual(evidence["routing"]["explicit_allowlist"]["selected_tool_ids"], [card["tool_id"]])
        self.assertFalse(evidence["routing"]["explicit_allowlist"]["execution_authorized"])
        self.assertRegex(evidence["routing"]["source_refs"]["experimental_candidate_catalog_git_blob_sha1"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            opted_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )

    def test_raw_evidence_navigator_is_default_off_and_requires_explicit_allowlist(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "knowledge.navigate_raw_evidence")
        task = profile("local-raw-evidence-navigation", card["accepted_input_types"], card["output_types"])

        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["knowledge.navigate_raw_evidence"],
        )

        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["knowledge.navigate_raw_evidence"],
        )
        self.assertFalse(included["execution_authorized"])
        self.assertFalse(included["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(included["selected_tools"][0]["permissions"]["write_paths"], [])

    def test_context_packet_assembler_is_default_off_and_requires_explicit_allowlist(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "knowledge.assemble_context_packet")
        task = profile("context-packet-local-boundary-smoke", card["accepted_input_types"], card["output_types"])

        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["knowledge.assemble_context_packet"],
        )

        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(excluded["selected_tools"], [])
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["knowledge.assemble_context_packet"],
        )
        self.assertFalse(included["execution_authorized"])
        self.assertFalse(included["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(included["selected_tools"][0]["permissions"]["write_paths"], [])

    def test_reusable_context_preflight_is_default_off_and_requires_explicit_allowlist(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "knowledge.preflight_reusable_context"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("cross-task-derived-context-preflight", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        allowlisted = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn({"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"}, default["rejected_candidates"])
        self.assertEqual(allowlisted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in allowlisted["selected_tools"]], [tool_id])
        self.assertFalse(allowlisted["execution_authorized"])
        self.assertFalse(allowlisted["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(allowlisted["selected_tools"][0]["permissions"]["write_paths"], [])

        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-reusable-context-preflight-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["tool_id"], tool_id)
        for trial in evidence["route_trials"]:
            replay = planner.plan_tool_route(
                evidence["route_profile"],
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(replay["decision"], trial["decision"])
            self.assertEqual([row["tool_id"] for row in replay["selected_tools"]], trial["selected_tool_ids"])
            self.assertFalse(replay["execution_authorized"])
            self.assertEqual(trial["router_provider_calls"], 0)
            self.assertFalse(trial["candidate_invoked"])

    def test_context_packet_variant_comparator_is_default_off_and_selects_only_after_allowlisting(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "maintenance.compare_context_packet_variants"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("matched-context-packet-structural-variant-comparison", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        allowlisted = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-context-packet-variant-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn({"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"}, default["rejected_candidates"])
        self.assertEqual(allowlisted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in allowlisted["selected_tools"]], [tool_id])
        self.assertFalse(allowlisted["execution_authorized"])
        self.assertFalse(allowlisted["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(allowlisted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(evidence["default_route_result"]["decision"], "INCOMPLETE")
        self.assertEqual(evidence["route_result"]["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in evidence["route_result"]["selected_tools"]], [tool_id])
        self.assertFalse(evidence["execution_authorized"])
        self.assertEqual(
            evidence["route_result"]["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            evidence["candidate_catalog_git_blob_sha1"],
        )

    def test_audit_finding_comparator_is_default_off_and_only_proposed_for_exact_review_pair(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "maintenance.compare_audit_findings"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("same-target-audit-finding-comparison-route-experiment", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        opted = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-audit-finding-comparator-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn({"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"}, default["rejected_candidates"])
        self.assertEqual(opted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted["selected_tools"]], [tool_id])
        self.assertFalse(opted["execution_authorized"])
        self.assertFalse(opted["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(evidence["routes"]["default_off"]["decision"], "INCOMPLETE")
        self.assertEqual(evidence["routes"]["explicit_allowlist"]["decision"], "COMPLETE")
        self.assertEqual(evidence["routes"]["explicit_allowlist"]["selected_tool_ids"], [tool_id])
        self.assertFalse(evidence["routes"]["explicit_allowlist"]["execution_authorized"])
        self.assertEqual(
            evidence["routes"]["explicit_allowlist"]["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            evidence["candidate_catalog_refresh"]["current_candidate_catalog_git_blob_sha1"],
        )

    def test_agent_episode_binding_preflight_is_default_off_and_opt_in_is_not_execution(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "collaboration.validate_agent_episode_binding"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile(
            "agent-episode-binding-declaration-preflight",
            card["accepted_input_types"],
            card["output_types"],
        )

        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])

        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(excluded["selected_tools"], [])
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in included["selected_tools"]], [tool_id])
        self.assertFalse(included["execution_authorized"])
        self.assertFalse(included["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(included["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(included["selected_tools"][0]["permissions"]["read_paths"], [
            "ignition/schemas/operations/toolbox-agent-episode-binding-r0.schema.json",
        ])

    def test_cognitive_migration_editorial_proposal_is_opt_in_and_read_only(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "writing.preflight_cognitive_migration_revision")
        task = profile("cognitive-migration-editorial-proposal", card["accepted_input_types"], [card["output_types"][1]])
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["writing.preflight_cognitive_migration_revision"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["writing.preflight_cognitive_migration_revision"],
        )
        self.assertFalse(included["execution_authorized"])
        self.assertFalse(included["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(included["selected_tools"][0]["permissions"]["write_paths"], [])

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

    def test_actions_step_timeline_summary_is_off_by_default_and_opt_in(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "maintenance.summarize_actions_step_timeline")
        task = profile(
            "summarize-actions-run-job-and-step-intervals",
            card["accepted_input_types"],
            [card["output_types"][0]],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["maintenance.summarize_actions_step_timeline"],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(excluded["selected_tools"], [])
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["maintenance.summarize_actions_step_timeline"],
        )
        self.assertFalse(included["execution_authorized"])
        self.assertFalse(included["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(included["selected_tools"][0]["permissions"]["write_paths"], [])

    def test_actions_repeated_step_sequence_is_off_by_default_and_uses_batch_specific_tool(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "maintenance.compare_actions_repeated_step_sequences")
        task = profile(
            "compare-one-pr-actions-history",
            card["accepted_input_types"],
            card["output_types"],
        )
        excluded = planner.plan_tool_route(task)
        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=[
                "maintenance.compare_actions_repeated_step_sequences",
                "maintenance.summarize_actions_step_timeline",
            ],
        )
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(excluded["selected_tools"], [])
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["maintenance.compare_actions_repeated_step_sequences"],
        )
        self.assertIn(
            {"tool_id": "maintenance.summarize_actions_step_timeline", "reason": "NO_INPUT_TYPE_MATCH"},
            included["rejected_candidates"],
        )
        self.assertFalse(included["execution_authorized"])
        self.assertFalse(included["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(included["selected_tools"][0]["permissions"]["write_paths"], [])

    def test_network_candidate_requires_both_tool_allowlist_and_exact_host_allowance(self) -> None:
        task = profile(
            "live-crossref-metadata-comparison",
            ["UTF-8 JSON stdin object with one to ten unique DOI, expected-title, expected-year records"],
            [
                "input-ordered Crossref metadata comparison rows",
                "per-response SHA-256 and explicit HTTP or network outcome summary",
                "bounded update-to, updated-by, and typed relation identifier projections with reported/omitted counts and truncation state",
            ],
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

    def test_crossref_reference_projection_is_opt_in_and_ignores_unneeded_providers(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        cards = {
            item["tool_id"]: item
            for item in catalog["candidates"]
            if item["tool_id"] in {
                "research.verify_crossref_metadata",
                "research.lookup_openalex_work_metadata",
                "research.audit_pubmed_updates_from_doi",
            }
        }
        crossref_id = "research.verify_crossref_metadata"
        crossref = cards[crossref_id]
        required_references = crossref["output_types"][-1]
        all_input_types = list(dict.fromkeys(
            value
            for tool_id in cards
            for value in cards[tool_id]["accepted_input_types"]
        ))
        task = profile(
            "crossref-deposited-reference-projection",
            all_input_types,
            [required_references],
        )

        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": crossref_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )

        no_host = planner.plan_tool_route(task, include_experimental_tool_ids=[crossref_id])
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": crossref_id, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        minimum = planner.plan_tool_route(
            profile(
                task["task_id"],
                task["input_types"],
                task["required_outputs"],
                allowed_network_hosts=["api.crossref.org"],
            ),
            include_experimental_tool_ids=[crossref_id],
        )
        self.assertEqual(minimum["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in minimum["selected_tools"]], [crossref_id])
        self.assertEqual(minimum["selected_tools"][0]["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertFalse(minimum["execution_authorized"])

        expanded_options = planner.plan_tool_route(
            profile(
                task["task_id"],
                task["input_types"],
                task["required_outputs"],
                allowed_network_hosts=["api.crossref.org"],
            ),
            include_experimental_tool_ids=list(cards),
        )
        self.assertEqual(expanded_options["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in expanded_options["selected_tools"]], [crossref_id])
        for tool_id in set(cards) - {crossref_id}:
            self.assertIn(
                {"tool_id": tool_id, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
                expanded_options["rejected_candidates"],
            )
        self.assertFalse(expanded_options["execution_authorized"])

    def test_crossref_reference_metadata_comparator_is_default_off_and_requires_exact_host(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "research.compare_crossref_reference_metadata"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile(
            "selected-crossref-reference-doi-metadata-comparison",
            card["accepted_input_types"],
            card["output_types"],
        )

        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )

        allowlisted_without_host = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        self.assertEqual(allowlisted_without_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": tool_id, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            allowlisted_without_host["rejected_candidates"],
        )

        permitted = planner.plan_tool_route(
            profile(
                task["task_id"],
                task["input_types"],
                task["required_outputs"],
                allowed_network_hosts=["api.crossref.org"],
            ),
            include_experimental_tool_ids=[tool_id],
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], [tool_id])
        self.assertEqual(permitted["selected_tools"][0]["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertFalse(permitted["execution_authorized"])

        expanded = planner.plan_tool_route(
            profile(
                task["task_id"],
                task["input_types"],
                task["required_outputs"],
                allowed_network_hosts=["api.crossref.org"],
            ),
            include_experimental_tool_ids=[
                tool_id,
                "research.verify_crossref_metadata",
                "research.lookup_openalex_work_metadata",
                "research.compare_publication_metadata_snapshots",
            ],
        )
        self.assertEqual([row["tool_id"] for row in expanded["selected_tools"]], [tool_id])
        self.assertFalse(expanded["execution_authorized"])

        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-crossref-reference-metadata-comparison-route-evidence-r1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["routes"]["default_off"]["decision"], default["decision"])
        self.assertEqual(evidence["routes"]["tool_allowlist_without_host"]["decision"], allowlisted_without_host["decision"])
        self.assertEqual(evidence["routes"]["exact_host_minimum"]["decision"], permitted["decision"])
        self.assertEqual(evidence["routes"]["exact_host_minimum"]["selected_tool_ids"], [tool_id])
        self.assertEqual(evidence["routes"]["expanded_allowlist"]["selected_tool_ids"], [tool_id])
        self.assertFalse(evidence["execution_authorized"])
        # The receipt remains pinned to the catalog version it actually used; later optional-card admissions do not rewrite history.
        self.assertRegex(evidence["candidate_catalog_git_blob_sha1"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            evidence["candidate_catalog_git_blob_sha1"],
            evidence["catalog_replay"]["candidate_catalog_git_blob_sha1"],
        )

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
        cluster_brief = next(
            item for item in candidates["candidates"]
            if item["tool_id"] == "knowledge.cluster_source_brief"
        )
        cluster_brief["permissions"]["network"] = True
        cluster_brief["permissions"]["network_hosts"] = ["example.org"]
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

    def test_pubmed_identifier_lookup_is_opt_in_and_complements_crossref(self) -> None:
        pubmed_input = "JSON stdin object with one to ten unique bare DOI identifiers"
        crossref_input = "UTF-8 JSON stdin object with one to ten unique DOI, expected-title, expected-year records"
        task = profile(
            "doi-index-identifiers",
            [pubmed_input],
            ["input-ordered PubMed/PMC identifier resolution rows", "per-response SHA-256 and explicit HTTP or network outcome summary"],
        )
        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(
            task, include_experimental_tool_ids=["research.resolve_pubmed_identifiers"],
        )
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": "research.resolve_pubmed_identifiers", "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        pubmed_route = planner.plan_tool_route(
            profile("doi-index-identifiers", [pubmed_input], task["required_outputs"], allowed_network_hosts=["pmc.ncbi.nlm.nih.gov"]),
            include_experimental_tool_ids=["research.resolve_pubmed_identifiers", "runtime.inspect_declared_pack_catalog"],
        )
        self.assertEqual(pubmed_route["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in pubmed_route["selected_tools"]], ["research.resolve_pubmed_identifiers"])
        self.assertIn(
            {"tool_id": "runtime.inspect_declared_pack_catalog", "reason": "NO_INPUT_TYPE_MATCH"},
            pubmed_route["rejected_candidates"],
        )
        self.assertFalse(pubmed_route["execution_authorized"])

        combined = planner.plan_tool_route(
            profile(
                "crossref-plus-pubmed-identifiers",
                [crossref_input, pubmed_input],
                [
                    "input-ordered Crossref metadata comparison rows",
                    "input-ordered PubMed/PMC identifier resolution rows",
                ],
                allowed_network_hosts=["api.crossref.org", "pmc.ncbi.nlm.nih.gov"],
            ),
            include_experimental_tool_ids=["research.resolve_pubmed_identifiers", "research.verify_crossref_metadata"],
        )
        self.assertEqual(combined["decision"], "COMPLETE")
        self.assertEqual(
            {row["tool_id"] for row in combined["selected_tools"]},
            {"research.resolve_pubmed_identifiers", "research.verify_crossref_metadata"},
        )
        self.assertFalse(combined["execution_authorized"])
        self.assertEqual(combined["network_authority_binding"], "CALLER_SUPPLIED_NOT_AUTHORITY_VERIFIED_BY_THIS_PLANNER")

    def test_openalex_work_metadata_lookup_is_opt_in_and_complements_crossref(self) -> None:
        openalex_input = "JSON stdin object with one to five unique bare DOI identifiers"
        openalex_outputs = [
            "input-ordered OpenAlex Work ID and selected bibliographic metadata rows including the provider-reported is_retracted signal",
            "OpenAlex-reported open-access summary, best OA location, and up to 25 sanitized location records per matched Work; provider count and truncation state remain explicit",
            "per-request response SHA-256, HTTP status, and public API usage fields",
        ]
        task = profile("openalex-work-metadata", [openalex_input], openalex_outputs)
        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(
            task, include_experimental_tool_ids=["research.lookup_openalex_work_metadata"],
        )
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": "research.lookup_openalex_work_metadata", "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        permitted = planner.plan_tool_route(
            profile("openalex-work-metadata", [openalex_input], openalex_outputs, allowed_network_hosts=["api.openalex.org"]),
            include_experimental_tool_ids=["research.lookup_openalex_work_metadata"],
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], ["research.lookup_openalex_work_metadata"])
        self.assertEqual(permitted["selected_tools"][0]["permissions"]["network_hosts"], ["api.openalex.org"])
        self.assertFalse(permitted["execution_authorized"])

        crossref_input = "UTF-8 JSON stdin object with one to ten unique DOI, expected-title, expected-year records"
        crossref_output = "input-ordered Crossref metadata comparison rows"
        paired = planner.plan_tool_route(
            profile(
                "crossref-and-openalex-doi-task",
                [crossref_input, openalex_input],
                [crossref_output] + openalex_outputs,
                allowed_network_hosts=["api.crossref.org", "api.openalex.org"],
            ),
            include_experimental_tool_ids=["research.verify_crossref_metadata", "research.lookup_openalex_work_metadata"],
        )
        self.assertEqual(paired["decision"], "COMPLETE")
        self.assertEqual(
            {row["tool_id"] for row in paired["selected_tools"]},
            {"research.verify_crossref_metadata", "research.lookup_openalex_work_metadata"},
        )
        self.assertFalse(paired["execution_authorized"])
        self.assertEqual(paired["cost_estimate"]["status"], "UNKNOWN")

    def test_arxiv_metadata_lookup_requires_candidate_and_exact_host_allowlists(self) -> None:
        arxiv_input = "UTF-8 JSON stdin object with exactly one modern arXiv ID (YYMM.NNNN[N], optionally vN)"
        arxiv_outputs = [
            "Provider-reported arXiv entry ID/version, title, author names, dates, categories, journal reference, and DOI when present",
            "One request URL, retrieval timestamp, response SHA-256, byte count, and claim-ceiling receipt",
        ]
        task = profile("arxiv-id-metadata", [arxiv_input], arxiv_outputs)
        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(
            task, include_experimental_tool_ids=["research.lookup_arxiv_paper_metadata"],
        )
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": "research.lookup_arxiv_paper_metadata", "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        permitted = planner.plan_tool_route(
            profile("arxiv-id-metadata", [arxiv_input], arxiv_outputs, allowed_network_hosts=["export.arxiv.org"]),
            include_experimental_tool_ids=["research.lookup_arxiv_paper_metadata"],
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], ["research.lookup_arxiv_paper_metadata"])
        self.assertEqual(permitted["selected_tools"][0]["permissions"]["network_hosts"], ["export.arxiv.org"])
        self.assertFalse(permitted["execution_authorized"])

    def test_arxiv_query_search_is_default_off_and_requires_exact_host_allowlist(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "research.search_arxiv_query")
        task = profile("arxiv-public-topic-search", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(task, include_experimental_tool_ids=[card["tool_id"]])
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": card["tool_id"], "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        competitors = [
            "research.search_pubmed_query",
            "research.search_europe_pmc_query",
            "research.lookup_arxiv_paper_metadata",
            card["tool_id"],
        ]
        permitted = planner.plan_tool_route(
            profile(
                "arxiv-public-topic-search",
                card["accepted_input_types"],
                card["output_types"],
                allowed_network_hosts=["export.arxiv.org"],
            ),
            include_experimental_tool_ids=competitors,
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], [card["tool_id"]])
        self.assertEqual(permitted["selected_tools"][0]["permissions"]["network_hosts"], ["export.arxiv.org"])
        self.assertFalse(permitted["execution_authorized"])

    def test_openalex_query_search_is_default_off_and_selects_only_for_its_required_outputs(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        tool_id = "research.search_openalex_query"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("openalex-public-topic-search", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": tool_id, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        exact_host = planner.plan_tool_route(
            profile(
                "openalex-public-topic-search",
                card["accepted_input_types"],
                card["output_types"],
                allowed_network_hosts=["api.openalex.org"],
            ),
            include_experimental_tool_ids=[tool_id],
        )
        self.assertEqual(exact_host["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in exact_host["selected_tools"]], [tool_id])
        self.assertEqual(exact_host["selected_tools"][0]["permissions"]["network_hosts"], ["api.openalex.org"])
        self.assertEqual(exact_host["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertFalse(exact_host["selected_tools"][0]["permissions"]["secrets"])
        self.assertFalse(exact_host["selected_tools"][0]["permissions"]["billing"])
        self.assertFalse(exact_host["selected_tools"][0]["permissions"]["external_actions"])
        self.assertFalse(exact_host["execution_authorized"])

        redundant_options = planner.plan_tool_route(
            profile(
                "openalex-public-topic-search",
                card["accepted_input_types"],
                card["output_types"],
                allowed_network_hosts=["api.openalex.org", "export.arxiv.org", "www.ebi.ac.uk"],
            ),
            include_experimental_tool_ids=[
                tool_id,
                "research.search_arxiv_query",
                "research.search_europe_pmc_query",
            ],
        )
        self.assertEqual(redundant_options["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in redundant_options["selected_tools"]], [tool_id])
        self.assertFalse(redundant_options["execution_authorized"])

        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-openalex-query-search-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        for trial in evidence["route_trials"]:
            route_profile = dict(evidence["route_profile"])
            if trial["allowed_network_hosts"]:
                route_profile["allowed_network_hosts"] = trial["allowed_network_hosts"]
            replay = planner.plan_tool_route(
                route_profile,
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(replay["decision"], trial["decision"])
            self.assertEqual([row["tool_id"] for row in replay["selected_tools"]], trial["selected_tool_ids"])
            self.assertFalse(replay["execution_authorized"])

    def test_crossref_query_search_is_default_off_and_selects_only_for_crossref_outputs(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        tool_id = "research.search_crossref_query"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("crossref-public-topic-search", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": tool_id, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        exact_host = planner.plan_tool_route(
            profile(
                "crossref-public-topic-search",
                card["accepted_input_types"],
                card["output_types"],
                allowed_network_hosts=["api.crossref.org"],
            ),
            include_experimental_tool_ids=[tool_id],
        )
        self.assertEqual(exact_host["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in exact_host["selected_tools"]], [tool_id])
        self.assertEqual(exact_host["selected_tools"][0]["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertEqual(exact_host["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertFalse(exact_host["selected_tools"][0]["permissions"]["secrets"])
        self.assertFalse(exact_host["selected_tools"][0]["permissions"]["billing"])
        self.assertFalse(exact_host["selected_tools"][0]["permissions"]["external_actions"])
        self.assertFalse(exact_host["execution_authorized"])

        redundant_options = planner.plan_tool_route(
            profile(
                "crossref-public-topic-search",
                card["accepted_input_types"],
                card["output_types"],
                allowed_network_hosts=["api.crossref.org", "api.openalex.org", "export.arxiv.org", "www.ebi.ac.uk"],
            ),
            include_experimental_tool_ids=[
                tool_id,
                "research.search_openalex_query",
                "research.search_arxiv_query",
                "research.search_europe_pmc_query",
            ],
        )
        self.assertEqual(redundant_options["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in redundant_options["selected_tools"]], [tool_id])
        self.assertFalse(redundant_options["execution_authorized"])

        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-crossref-query-search-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        for trial in evidence["route_trials"]:
            route_profile = dict(evidence["route_profile"])
            if trial["allowed_network_hosts"]:
                route_profile["allowed_network_hosts"] = trial["allowed_network_hosts"]
            replay = planner.plan_tool_route(
                route_profile,
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(replay["decision"], trial["decision"])
            self.assertEqual([row["tool_id"] for row in replay["selected_tools"]], trial["selected_tool_ids"])
            self.assertFalse(replay["execution_authorized"])

    def test_noaa_ch4_growth_lookup_is_default_off_and_requires_exact_host_allowance(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "research.lookup_noaa_global_ch4_annual_growth")
        task = profile("noaa-ch4-annual-growth", card["accepted_input_types"], card["output_types"])
        excluded = planner.plan_tool_route(task)
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(excluded["selected_tools"], [])

        missing_host = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=[card["tool_id"]],
        )
        self.assertEqual(missing_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": card["tool_id"], "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            missing_host["rejected_candidates"],
        )

        permitted = planner.plan_tool_route(
            profile("noaa-ch4-annual-growth", card["accepted_input_types"], card["output_types"], allowed_network_hosts=["gml.noaa.gov"]),
            include_experimental_tool_ids=[card["tool_id"]],
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], [card["tool_id"]])
        self.assertEqual(permitted["selected_tools"][0]["permissions"]["network_hosts"], ["gml.noaa.gov"])
        self.assertFalse(permitted["execution_authorized"])

    def test_noaa_co2_growth_is_complementary_default_off_and_needs_exact_host(self) -> None:
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "research.lookup_noaa_global_co2_annual_growth")
        ch4 = next(row for row in catalog["candidates"] if row["tool_id"] == "research.lookup_noaa_global_ch4_annual_growth")
        task = profile("noaa-co2-annual-growth", card["accepted_input_types"], card["output_types"])

        excluded = planner.plan_tool_route(task)
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(excluded["selected_tools"], [])

        ch4_only = planner.plan_tool_route(
            profile("noaa-co2-annual-growth", card["accepted_input_types"], card["output_types"], allowed_network_hosts=["gml.noaa.gov"]),
            include_experimental_tool_ids=[ch4["tool_id"]],
        )
        self.assertEqual(ch4_only["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": ch4["tool_id"], "reason": "NO_INPUT_TYPE_MATCH"},
            ch4_only["rejected_candidates"],
        )

        missing_host = planner.plan_tool_route(task, include_experimental_tool_ids=[card["tool_id"]])
        self.assertEqual(missing_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": card["tool_id"], "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            missing_host["rejected_candidates"],
        )

        permitted = planner.plan_tool_route(
            profile("noaa-co2-annual-growth", card["accepted_input_types"], card["output_types"], allowed_network_hosts=["gml.noaa.gov"]),
            include_experimental_tool_ids=[card["tool_id"]],
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], [card["tool_id"]])
        self.assertEqual(permitted["selected_tools"][0]["permissions"]["network_hosts"], ["gml.noaa.gov"])
        self.assertFalse(permitted["execution_authorized"])

    def test_real_doi_task_expands_to_two_required_outputs_and_skips_redundant_candidates(self) -> None:
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-real-task-route-evidence-r0.json").read_text(encoding="utf-8")
        )
        route = evidence["route_profile"]
        task = profile(
            evidence["task"]["task_id"],
            route["input_types"],
            route["required_outputs"],
            allowed_network_hosts=route["allowed_network_hosts"],
        )
        redundant = next(row for row in evidence["route_trials"] if row["scenario"] == "redundant_options")
        result = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=redundant["include_experimental_tool_ids"],
        )
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual(
            {row["tool_id"] for row in result["selected_tools"]},
            {"research.resolve_pubmed_identifiers", "research.verify_crossref_metadata"},
        )
        actual_rejections = {row["tool_id"]: row["reason"] for row in result["rejected_candidates"]}
        for rejection in redundant["rejected_candidates"]:
            self.assertEqual(actual_rejections[rejection["tool_id"]], rejection["reason"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["cost_estimate"]["status"], "UNKNOWN")

    def test_pubmed_update_links_are_separate_opt_in_capability(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "research.inspect_pubmed_update_links")
        pmid_input = card["accepted_input_types"][0]
        outputs = card["output_types"]
        task = profile("pubmed-record-updates", [pmid_input], outputs)
        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(task, include_experimental_tool_ids=["research.inspect_pubmed_update_links"])
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": "research.inspect_pubmed_update_links", "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        permitted = planner.plan_tool_route(
            profile("pubmed-record-updates", [pmid_input], outputs, allowed_network_hosts=["eutils.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov"]),
            include_experimental_tool_ids=["research.inspect_pubmed_update_links", "research.resolve_pubmed_identifiers"],
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], ["research.inspect_pubmed_update_links"])
        self.assertFalse(permitted["execution_authorized"])
        self.assertIn(
            {"tool_id": "research.resolve_pubmed_identifiers", "reason": "NO_INPUT_TYPE_MATCH"},
            permitted["rejected_candidates"],
        )
        self.assertFalse(permitted["execution_authorized"])

    def test_europe_pmc_query_search_is_default_off_and_minimally_sufficient(self) -> None:
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-europe-pmc-query-search-evidence-r0.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            evidence["route_profile"]["candidate_catalog_git_blob_sha1"],
            evidence["candidate_catalog_refresh"]["current_candidate_catalog_git_blob_sha1"],
        )
        route = evidence["route_profile"]
        task = profile(
            evidence["task"]["task_id"],
            route["input_types"],
            route["required_outputs"],
            allowed_network_hosts=route["allowed_network_hosts"],
        )
        for trial in evidence["route_trials"]:
            trial_task = profile(
                task["task_id"],
                task["input_types"],
                task["required_outputs"],
                allowed_network_hosts=trial["allowed_network_hosts"],
            )
            result = planner.plan_tool_route(
                trial_task,
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(result["decision"], trial["expected_decision"], trial["scenario"])
            self.assertEqual(
                [row["tool_id"] for row in result["selected_tools"]],
                trial["expected_selected_tool_ids"],
                trial["scenario"],
            )
            self.assertEqual(result["execution_authorized"], trial["expected_execution_authorized"], trial["scenario"])
            for rejected in trial["expected_rejections"]:
                self.assertIn(rejected, result["rejected_candidates"], trial["scenario"])
            if trial["scenario"] == "explicit_minimal_route_with_redundant_identifier_tool":
                self.assertEqual(
                    result["network_authority_binding"],
                    "CALLER_SUPPLIED_NOT_AUTHORITY_VERIFIED_BY_THIS_PLANNER",
                )
                self.assertEqual(result["cost_estimate"]["status"], "UNKNOWN")

    def test_europe_pmc_fulltext_locator_is_default_off_and_specialized(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "research.resolve_europe_pmc_fulltext_locations")
        self.assertIn("DOI, PMID, or PMCID", card["accepted_input_types"][0])
        task = profile("exact-typed-identifier-europe-pmc-fulltext-locations", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])

        no_host = planner.plan_tool_route(task, include_experimental_tool_ids=[card["tool_id"]])
        self.assertEqual(no_host["decision"], "INCOMPLETE")
        self.assertIn(
            {"tool_id": card["tool_id"], "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            no_host["rejected_candidates"],
        )

        permitted = planner.plan_tool_route(
            profile(
                task["task_id"], task["input_types"], task["required_outputs"],
                allowed_network_hosts=["www.ebi.ac.uk"],
            ),
            include_experimental_tool_ids=[card["tool_id"], "research.search_europe_pmc_query"],
        )
        self.assertEqual(permitted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in permitted["selected_tools"]], [card["tool_id"]])
        self.assertIn(
            {"tool_id": "research.search_europe_pmc_query", "reason": "NO_INPUT_TYPE_MATCH"},
            permitted["rejected_candidates"],
        )
        self.assertFalse(permitted["execution_authorized"])
        self.assertEqual(permitted["cost_estimate"]["status"], "UNKNOWN")

    def test_g1_goal_intake_preflight_is_opt_in_and_never_authorizes(self) -> None:
        task = profile(
            "offline-g1-goal-proposal-preflight",
            ["UTF-8 JSON stdin object with one closed ResearchEpisodeRequest envelope (maximum 1,000,000 bytes)"],
            [
                "machine-readable preflight status, structural outcome, and reason-coded findings for the supplied proposal bytes",
                "exact raw input SHA-256 and bounded Intent/Goal/parent/Completion Contract projection",
                "explicit non-authentication and no-write/no-activation/no-completion/no-dispatch flags plus wrapper-source SHA-256",
            ],
        )
        excluded = planner.plan_tool_route(task)
        self.assertEqual(excluded["decision"], "INCOMPLETE")
        self.assertEqual(excluded["selected_tools"], [])
        self.assertIn(
            {"tool_id": "research.preflight_g1_goal_intake", "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            excluded["rejected_candidates"],
        )

        included = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=["research.preflight_g1_goal_intake"],
        )
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in included["selected_tools"]],
            ["research.preflight_g1_goal_intake"],
        )
        permissions = included["selected_tools"][0]["permissions"]
        self.assertEqual(permissions["write_paths"], [])
        self.assertFalse(permissions["network"])
        self.assertFalse(permissions["secrets"])
        self.assertFalse(permissions["external_actions"])
        self.assertFalse(included["execution_authorized"])

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

    def test_receiver_handoff_preflight_is_default_off_and_opt_in_is_a_proposal(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "collaboration.preflight_receiver_handoff"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile(
            "receiver-handoff-source-binding-preflight",
            card["accepted_input_types"],
            card["output_types"],
        )

        default = planner.plan_tool_route(task)
        opt_in = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(opt_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opt_in["selected_tools"]], [tool_id])
        self.assertEqual(opt_in["selected_tools"][0]["kind"], "EXPERIMENTAL_OPTIONAL_TOOL")
        self.assertFalse(opt_in["execution_authorized"])
        self.assertEqual(opt_in["cost_estimate"]["status"], "UNKNOWN")
        self.assertEqual(
            opt_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )

    def test_handoff_artifact_byte_checker_is_default_off_and_uses_only_explicit_allowlist(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "collaboration.verify_handoff_artifact_files"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("handoff-artifact-local-digest-check", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        opt_in = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        receipt = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-handoff-artifact-byte-check-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(opt_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opt_in["selected_tools"]], [tool_id])
        self.assertFalse(opt_in["execution_authorized"])
        self.assertFalse(opt_in["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opt_in["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertFalse(receipt["default_route_result"]["execution_authorized"])
        self.assertEqual(receipt["default_route_result"]["decision"], "INCOMPLETE")
        self.assertEqual(receipt["route_result"]["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in receipt["route_result"]["selected_tools"]], [tool_id])
        self.assertFalse(receipt["route_result"]["execution_authorized"])
        self.assertEqual(
            receipt["route_result"]["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            receipt["candidate_catalog_refresh"]["current_git_blob_sha1"],
        )
        self.assertEqual(
            opt_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )
        self.assertNotEqual(
            receipt["candidate_catalog_refresh"]["current_git_blob_sha1"],
            opt_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
        )

    def test_cross_source_metadata_comparator_is_default_off_and_opt_in(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "research.compare_publication_metadata_snapshots"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile(
            "compare-collected-crossref-openalex-title-year",
            card["accepted_input_types"],
            card["output_types"],
        )

        default = planner.plan_tool_route(task)
        opt_in = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        receipt = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-publication-metadata-cross-source-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(opt_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opt_in["selected_tools"]], [tool_id])
        self.assertEqual(opt_in["allowed_network_hosts"], [])
        self.assertFalse(opt_in["execution_authorized"])
        self.assertFalse(opt_in["selected_tools"][0]["permissions"]["network"])
        comparison = receipt["comparison_stage"]
        self.assertEqual(comparison["default_route_result"]["decision"], "INCOMPLETE")
        self.assertEqual(comparison["route_result"]["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in comparison["route_result"]["selected_tools"]], [tool_id])
        self.assertFalse(comparison["route_result"]["execution_authorized"])
        self.assertEqual(
            comparison["route_result"]["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            receipt["candidate_catalog_git_blob_sha1"],
        )
        self.assertEqual(
            opt_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )
        self.assertNotEqual(
            receipt["candidate_catalog_git_blob_sha1"],
            opt_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
        )
        retrieval = receipt["source_retrieval_stage"]
        self.assertEqual(retrieval["route_trials"]["default_light"]["decision"], "INCOMPLETE")
        self.assertEqual(
            set(retrieval["route_trials"]["minimum_sufficient_pair"]["selected_tool_ids"]),
            {"research.verify_crossref_metadata", "research.lookup_openalex_work_metadata"},
        )
        self.assertEqual(
            retrieval["route_trials"]["minimum_sufficient_pair"]["allowed_network_hosts"],
            ["api.crossref.org", "api.openalex.org"],
        )
        self.assertEqual(
            retrieval["route_trials"]["extra_provider_options_same_permission_context"]["selected_tool_ids"],
            retrieval["route_trials"]["minimum_sufficient_pair"]["selected_tool_ids"],
        )
        self.assertFalse(retrieval["route_result"]["execution_authorized"])

    def test_portable_research_episode_preflight_is_default_off_and_allowlist_does_not_execute(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "collaboration.validate_portable_research_episode"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("portable-research-episode-manifest-preflight", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        opted = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(opted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted["selected_tools"]], [tool_id])
        self.assertFalse(opted["execution_authorized"])
        self.assertFalse(opted["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(evidence["default_route_result"]["decision"], "INCOMPLETE")
        self.assertEqual(evidence["allowlisted_route_result"]["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in evidence["allowlisted_route_result"]["selected_tools"]], [tool_id])
        self.assertFalse(evidence["allowlisted_route_result"]["execution_authorized"])
        self.assertEqual(
            evidence["allowlisted_route_result"]["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            evidence["candidate_catalog_git_blob_sha1"],
        )
        self.assertEqual(
            opted["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )
        self.assertNotEqual(
            evidence["candidate_catalog_git_blob_sha1"],
            opted["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
        )

    def test_producer_consumer_semantic_preflight_is_default_off_and_minimally_routed(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "maintenance.preflight_producer_consumer_semantics"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("producer-consumer-static-pattern-preflight", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        opted = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-producer-consumer-semantic-route-evidence-r0.json").read_text(encoding="utf-8")
        )
        trials = {row["scenario"]: row for row in evidence["route_trials"]}

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(opted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted["selected_tools"]], [tool_id])
        self.assertFalse(opted["execution_authorized"])
        self.assertFalse(opted["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(trials["default_light"]["decision"], "INCOMPLETE")
        self.assertEqual(trials["explicit_candidate"]["decision"], "COMPLETE")
        self.assertEqual(trials["explicit_candidate"]["selected_tool_ids"], [tool_id])
        self.assertFalse(trials["explicit_candidate"]["explicit_invocation_authorized"])
        self.assertEqual(trials["candidate_with_adjacent_options"]["selected_tool_ids"], [tool_id])
        self.assertEqual(
            {row["reason"] for row in trials["candidate_with_adjacent_options"]["relevant_rejections"]},
            {"NO_INPUT_TYPE_MATCH"},
        )
        current_candidate_hash = planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes())
        self.assertEqual(opted["source_refs"]["experimental_candidate_catalog_git_blob_sha1"], current_candidate_hash)
        # This pre-addition receipt remains bound to its historical candidate catalog snapshot.
        self.assertEqual(evidence["candidate_binding"]["candidate_cards_git_blob_sha1"], "01eb6ebeec0b55c5a1416ad557ea524182ca71e4")
        self.assertNotEqual(current_candidate_hash, evidence["candidate_binding"]["candidate_cards_git_blob_sha1"])

    def test_pubmed_doi_update_composition_is_default_off_and_routes_only_with_both_hosts(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "research.audit_pubmed_updates_from_doi"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("pubmed-doi-update-audit", card["accepted_input_types"], card["output_types"])

        default = planner.plan_tool_route(task)
        missing_host = planner.plan_tool_route(
            {**task, "allowed_network_hosts": ["pmc.ncbi.nlm.nih.gov"]},
            include_experimental_tool_ids=[tool_id],
        )
        opted = planner.plan_tool_route(
            {**task, "allowed_network_hosts": ["pmc.ncbi.nlm.nih.gov", "eutils.ncbi.nlm.nih.gov"]},
            include_experimental_tool_ids=[
                tool_id,
                "research.resolve_pubmed_identifiers",
                "research.inspect_pubmed_update_links",
            ],
        )

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn({"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"}, default["rejected_candidates"])
        self.assertEqual(missing_host["decision"], "INCOMPLETE")
        self.assertIn({"tool_id": tool_id, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"}, missing_host["rejected_candidates"])
        self.assertEqual(opted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted["selected_tools"]], [tool_id])
        self.assertFalse(opted["execution_authorized"])
        self.assertEqual(opted["selected_tools"][0]["permissions"]["network_hosts"], ["pmc.ncbi.nlm.nih.gov", "eutils.ncbi.nlm.nih.gov"])
        self.assertEqual(opted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(
            opted["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )

    def test_pubmed_doi_update_route_evidence_r2_replays_for_both_specialized_scopes(self) -> None:
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-pubmed-doi-update-route-evidence-r2.json").read_text(encoding="utf-8")
        )
        # Historical route evidence keeps its original catalog binding; the trials below are replayed against today's catalog.
        self.assertRegex(evidence["catalog_replay"]["candidate_catalog_git_blob_sha1"], r"^[0-9a-f]{40}$")
        self.assertTrue(evidence["catalog_replay"]["all_expected_decisions_reproduced"])
        self.assertEqual(evidence["summary"]["execution_authorized"], False)
        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                result = planner.plan_tool_route(
                    trial["task_profile"],
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                self.assertEqual(result["decision"], trial["expected_decision"])
                self.assertEqual(
                    [row["tool_id"] for row in result["selected_tools"]],
                    trial["expected_selected_tool_ids"],
                )
                self.assertFalse(result["execution_authorized"])

    def test_grounded_ideation_is_default_off_and_selects_only_on_explicit_allowlist(self) -> None:
        tool_id = "research.preflight_grounded_ideation"
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        route_profile = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-grounded-ideation-preflight-route-profile-r0.json")
            .read_text(encoding="utf-8")
        )
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-grounded-ideation-preflight-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(route_profile["input_types"], card["accepted_input_types"])
        self.assertEqual(route_profile["required_outputs"], card["output_types"])
        fingerprint_fields = (
            "tool_id", "version", "accepted_input_types", "output_types", "execution_mode",
            "explicit_owner_authorization_required", "permissions", "router_selectable_by_default",
            "router_conditions", "claim_ceiling",
        )
        fingerprint_doc = {key: card[key] for key in fingerprint_fields}
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(evidence["tool_id"], tool_id)
        self.assertEqual(evidence["routing_contract_sha256"], fingerprint)

        default = planner.plan_tool_route(route_profile)
        included = planner.plan_tool_route(route_profile, include_experimental_tool_ids=[tool_id])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(included["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in included["selected_tools"]], [tool_id])
        self.assertFalse(included["execution_authorized"])
        self.assertFalse(included["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(included["selected_tools"][0]["permissions"]["write_paths"], [])
        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                replay = planner.plan_tool_route(
                    route_profile,
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                self.assertEqual(replay["decision"], trial["decision"])
                self.assertEqual([row["tool_id"] for row in replay["selected_tools"]], trial["selected_tool_ids"])
                self.assertEqual(replay["unmet_outputs"], trial["unmet_outputs"])
                self.assertFalse(replay["execution_authorized"])
                self.assertEqual(trial["router_provider_calls"], 0)
                self.assertFalse(trial["candidate_invoked"])

    def test_declared_permission_delta_is_default_off_and_proposes_only_on_allowlist(self) -> None:
        tool_id = "governance.preflight_declared_permission_delta"
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        route_profile = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-declared-permission-delta-route-profile-r0.json")
            .read_text(encoding="utf-8")
        )
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-declared-permission-delta-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(route_profile["input_types"], card["accepted_input_types"])
        self.assertEqual(route_profile["required_outputs"], card["output_types"])
        fingerprint_fields = (
            "tool_id", "version", "accepted_input_types", "output_types", "execution_mode",
            "explicit_owner_authorization_required", "permissions", "router_selectable_by_default",
            "router_conditions", "claim_ceiling",
        )
        fingerprint_doc = {key: card[key] for key in fingerprint_fields}
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(evidence["tool_id"], tool_id)
        self.assertEqual(evidence["route_profile_sha256"], hashlib.sha256(
            (IGNITION_ROOT / "data/operations/toolbox-declared-permission-delta-route-profile-r0.json")
            .read_bytes()
        ).hexdigest())
        self.assertEqual(evidence["routing_contract_sha256"], fingerprint)

        default = planner.plan_tool_route(route_profile)
        allowlisted = planner.plan_tool_route(route_profile, include_experimental_tool_ids=[tool_id])
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(allowlisted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in allowlisted["selected_tools"]], [tool_id])
        self.assertFalse(allowlisted["execution_authorized"])
        self.assertEqual(allowlisted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertFalse(allowlisted["selected_tools"][0]["permissions"]["network"])
        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                replay = planner.plan_tool_route(
                    route_profile,
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                self.assertEqual(replay["decision"], trial["decision"])
                self.assertEqual([row["tool_id"] for row in replay["selected_tools"]], trial["selected_tool_ids"])
                self.assertEqual(replay["unmet_outputs"], trial["unmet_outputs"])
                self.assertFalse(replay["execution_authorized"])
                self.assertEqual(trial["router_provider_calls"], 0)
                self.assertFalse(trial["candidate_invoked"])

    def test_offline_source_snapshot_binding_is_default_off_and_routes_only_when_allowlisted(self) -> None:
        tool_id = "research.bind_offline_source_snapshot_run"
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("offline-frozen-source-binding", card["accepted_input_types"], card["output_types"])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-offline-source-snapshot-binding-route-evidence-r1.json")
            .read_text(encoding="utf-8")
        )

        default = planner.plan_tool_route(task)
        allowlisted = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(allowlisted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in allowlisted["selected_tools"]], [tool_id])
        self.assertFalse(allowlisted["execution_authorized"])
        self.assertFalse(allowlisted["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(allowlisted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertRegex(evidence["catalog_replay"]["candidate_catalog_git_blob_sha1"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            evidence["catalog_replay"]["candidate_catalog_git_blob_sha1"],
            evidence["candidate_catalog_git_blob_sha1"],
        )
        self.assertTrue(evidence["catalog_replay"]["all_expected_decisions_reproduced"])
        self.assertEqual(evidence["summary"]["execution_authorized"], False)
        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                result = planner.plan_tool_route(
                    trial["task_profile"],
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                self.assertEqual(result["decision"], trial["expected_decision"])
                self.assertEqual(
                    [row["tool_id"] for row in result["selected_tools"]],
                    trial["expected_selected_tool_ids"],
                )
                self.assertFalse(result["execution_authorized"])

    def test_offline_source_snapshot_run_verifier_is_default_off_and_allowlist_only(self) -> None:
        tool_id = "research.verify_offline_source_snapshot_run"
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = profile("offline-e37-run-receipt-verification", card["accepted_input_types"], card["output_types"])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-offline-source-snapshot-run-verifier-route-evidence-r1.json")
            .read_text(encoding="utf-8")
        )

        default = planner.plan_tool_route(task)
        allowlisted = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn(
            {"tool_id": tool_id, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )
        self.assertEqual(allowlisted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in allowlisted["selected_tools"]], [tool_id])
        self.assertFalse(allowlisted["execution_authorized"])
        self.assertFalse(allowlisted["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(allowlisted["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertRegex(evidence["catalog_replay"]["candidate_catalog_git_blob_sha1"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            evidence["catalog_replay"]["candidate_catalog_git_blob_sha1"],
            evidence["candidate_catalog_git_blob_sha1"],
        )
        self.assertTrue(evidence["catalog_replay"]["all_expected_decisions_reproduced"])
        self.assertFalse(evidence["summary"]["execution_authorized"])
        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                result = planner.plan_tool_route(
                    trial["task_profile"],
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                self.assertEqual(result["decision"], trial["expected_decision"])
                self.assertEqual(
                    [row["tool_id"] for row in result["selected_tools"]],
                    trial["expected_selected_tool_ids"],
                )
                self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
