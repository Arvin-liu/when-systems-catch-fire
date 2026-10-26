from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/operations/build_toolbox_identity_cards.py"
SPEC = importlib.util.spec_from_file_location("toolbox_identity_cards", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ToolboxIdentityCardTests(unittest.TestCase):
    def test_cluster_source_brief_c1_records_implementation_comparator_and_safe_scope(self) -> None:
        document = TOOL.build_cards()
        card = next(item for item in document["cards"] if item["tool_id"] == "knowledge.cluster_source_brief")
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-cluster-source-brief-c1-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(evidence["disposition"]["relationship"], "COEXIST_BY_INVOCATION_SCOPE")
        self.assertTrue(evidence["paired_comparison"]["stdout_byte_identical"])
        self.assertEqual(
            card["comparison_evidence"]["compared_implementation_refs"],
            ["ignition/tools/extract_cluster_source_brief.py"],
        )
        self.assertIn(
            "implementation refs: ignition/tools/extract_cluster_source_brief.py",
            TOOL.render_human(document),
        )
        self.assertIn("toolbox-cluster-source-brief-c1-evidence-r0.json", " ".join(card["comparison_evidence"]["evidence_refs"]))
        self.assertEqual(card["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "ACTIVE")
        self.assertTrue(card["unique_remaining_use_cases"])
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["network"])

    def test_crossref_c1_keeps_uncertainty_after_limited_record_comparison(self) -> None:
        document = TOOL.build_cards()
        card = next(
            item for item in document["cards"]
            if item["tool_id"] == "research.verify_crossref_metadata"
        )
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-crossref-task103-comparison-c1-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(evidence["schema_version"], "ignition.toolbox-c1-crossref-task103-comparison-evidence-r0")
        self.assertTrue(evidence["paired_result"]["all_fields_equal"])
        self.assertEqual(evidence["candidate"]["response_sha256"], evidence["reference_implementation"]["response_sha256"])
        self.assertEqual(evidence["disposition"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(evidence["reference_implementation"]["identity"].split(";")[1].strip(), "source script, not a registered toolbox tool identity")
        self.assertEqual(card["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(
            card["comparison_evidence"]["compared_tool_ids"],
            ["research.lookup_openalex_work_metadata", "research.inspect_pubmed_update_links"],
        )
        self.assertIn(
            "ignition/data/operations/toolbox-crossref-references-real-task-evidence-r0.json",
            card["comparison_evidence"]["evidence_refs"],
        )
        self.assertIn(
            "ignition/data/operations/toolbox-crossref-references-route-evidence-r0.json",
            card["comparison_evidence"]["evidence_refs"],
        )
        self.assertEqual(card["replacement_candidates"], [])
        self.assertTrue(card["unique_remaining_use_cases"])
        self.assertIn("Crossref reference citation metadata", card["unique_remaining_use_cases"][0])
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "ACTIVE")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["network_hosts"], ["api.crossref.org"])

    def test_raw_evidence_navigator_card_keeps_scope_and_comparison_uncertainty(self) -> None:
        document = TOOL.build_cards()
        card = next(
            item for item in document["cards"]
            if item["tool_id"] == "knowledge.navigate_raw_evidence"
        )

        self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["read_paths"], ["ignition/"])
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["network"])
        self.assertFalse(card["permissions"]["secrets"])
        self.assertFalse(card["permissions"]["billing"])
        self.assertFalse(card["permissions"]["external_actions"])
        self.assertEqual(card["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "COMPARISON_UNKNOWN")
        self.assertIn("sufficiency_decision is always NOT_EVALUATED", " ".join(card["output_types"]))

    def test_context_packet_card_keeps_structural_only_boundary_and_route_receipt(self) -> None:
        document = TOOL.build_cards()
        card = next(
            item for item in document["cards"]
            if item["tool_id"] == "knowledge.assemble_context_packet"
        )

        self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertEqual(card["version"], "0.1.0")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["read_paths"], ["ignition/"])
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["network"])
        self.assertFalse(card["permissions"]["secrets"])
        self.assertFalse(card["permissions"]["billing"])
        self.assertFalse(card["permissions"]["external_actions"])
        self.assertEqual(card["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "COMPARISON_UNKNOWN")
        self.assertIn("does not redact", " ".join(card["counterindicated_when"]).lower())
        self.assertIn("NOT_EVALUATED", " ".join(card["output_types"]))
        route = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-context-packet-route-evidence-r0.json").read_text(encoding="utf-8")
        )
        self.assertEqual(route["route_result"]["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in route["route_result"]["selected_tools"]],
            [card["tool_id"]],
        )
        self.assertFalse(route["execution_authorized"])
        self.assertFalse(route["route_result"]["execution_authorized"])

    def test_context_packet_variant_comparator_card_keeps_c1_scope_and_real_tool_limits(self) -> None:
        document = TOOL.build_cards()
        tool_id = "maintenance.compare_context_packet_variants"
        card = next(item for item in document["cards"] if item["tool_id"] == tool_id)
        c1 = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-context-packet-variant-c1-evidence-r0.json").read_text(encoding="utf-8")
        )
        real_task = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-context-packet-variant-real-task-r0.json").read_text(encoding="utf-8")
        )
        route = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-context-packet-variant-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(card["evidence_level"], "REAL_TOOL_TEST")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["read_paths"], [])
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["network"])
        self.assertFalse(card["permissions"]["secrets"])
        self.assertFalse(card["permissions"]["billing"])
        self.assertFalse(card["permissions"]["external_actions"])
        self.assertEqual(card["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(card["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(card["replacement_candidates"], [])
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertEqual(c1["decision"]["replacement_candidates"], [])
        self.assertEqual(real_task["task_outcome"].split(";")[0], "NOT_ASSESSED")
        self.assertNotIn("context_excerpt", json.dumps(real_task))
        self.assertEqual(route["default_route_result"]["decision"], "INCOMPLETE")
        self.assertEqual(route["route_result"]["decision"], "COMPLETE")
        self.assertFalse(route["execution_authorized"])

    def test_audit_finding_comparator_card_preserves_c1_scope_and_non_independence_boundary(self) -> None:
        document = TOOL.build_cards()
        tool_id = "maintenance.compare_audit_findings"
        card = next(item for item in document["cards"] if item["tool_id"] == tool_id)
        c1 = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-audit-finding-comparator-c1-evidence-r0.json").read_text(encoding="utf-8")
        )
        real_task = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-audit-finding-comparator-real-task-r0.json").read_text(encoding="utf-8")
        )
        route = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-audit-finding-comparator-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertEqual(card["version"], "0.1.0")
        self.assertEqual(card["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["read_paths"], [])
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["network"])
        self.assertFalse(card["permissions"]["secrets"])
        self.assertFalse(card["permissions"]["billing"])
        self.assertFalse(card["permissions"]["external_actions"])
        self.assertEqual(card["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(card["replacement_candidates"], [])
        self.assertEqual(card["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertFalse(real_task["reviewer_independence_established"])
        self.assertEqual(real_task["summary"]["shared"], 1)
        self.assertEqual(real_task["summary"]["second_review_only"], 1)
        self.assertEqual(c1["disposition"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(route["routes"]["default_off"]["decision"], "INCOMPLETE")
        self.assertEqual(route["routes"]["explicit_allowlist"]["decision"], "COMPLETE")
        self.assertFalse(route["routes"]["explicit_allowlist"]["execution_authorized"])

    def test_handoff_artifact_byte_checker_card_preserves_c1_specialization_and_bounds(self) -> None:
        document = TOOL.build_cards()
        card = next(
            item for item in document["cards"]
            if item["tool_id"] == "collaboration.verify_handoff_artifact_files"
        )

        self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertEqual(card["version"], "0.1.0")
        self.assertEqual(card["evidence_level"], "SYNTHETIC_ONLY")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["read_paths"], ["ignition/"])
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["network"])
        self.assertFalse(card["permissions"]["secrets"])
        self.assertFalse(card["permissions"]["billing"])
        self.assertFalse(card["permissions"]["external_actions"])
        self.assertEqual(card["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(card["replacement_candidates"], [])
        self.assertTrue(card["unique_remaining_use_cases"])
        self.assertEqual(card["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(
            set(card["comparison_evidence"]["compared_tool_ids"]),
            {"collaboration.preflight_receiver_handoff", "knowledge.assemble_context_packet"},
        )
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertIn("no file contents", " ".join(card["output_types"]).lower())
        route = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-handoff-artifact-byte-check-route-evidence-r0.json").read_text(encoding="utf-8")
        )
        self.assertEqual(route["default_route_result"]["decision"], "INCOMPLETE")
        self.assertEqual(route["route_result"]["decision"], "COMPLETE")
        self.assertFalse(route["route_result"]["execution_authorized"])

    def test_portable_research_episode_card_keeps_c1_uncertainty_and_nonexecution_boundary(self) -> None:
        document = TOOL.build_cards()
        tool_id = "collaboration.validate_portable_research_episode"
        card = next(item for item in document["cards"] if item["tool_id"] == tool_id)
        c1 = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-c1-comparison-r0.json").read_text(encoding="utf-8")
        )
        real_task = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-real-task-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertEqual(card["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(card["replacement_candidates"], [])
        self.assertEqual(card["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["network"])
        self.assertFalse(card["permissions"]["secrets"])
        self.assertFalse(card["permissions"]["billing"])
        self.assertFalse(card["permissions"]["external_actions"])
        self.assertIn("does not authenticate", card["claim_ceiling"])
        self.assertEqual(c1["c1_disposition"]["comparison_status"], "COMPARISON_UNKNOWN")
        self.assertEqual(real_task["invocation"]["result"]["status"], "EPISODE_MANIFEST_CONSISTENT")
        self.assertFalse(real_task["invocation"]["result"]["execution_authorized"])
        self.assertFalse(real_task["invocation"]["result"]["import_performed"])
        self.assertFalse(real_task["invocation"]["result"]["artifact_bytes_verified"])
        route = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-route-evidence-r0.json").read_text(encoding="utf-8")
        )
        self.assertEqual(route["default_route_result"]["selected_tools"], [])
        self.assertEqual([row["tool_id"] for row in route["allowlisted_route_result"]["selected_tools"]], [tool_id])
        self.assertFalse(route["allowlisted_route_result"]["execution_authorized"])

    def test_producer_consumer_semantic_card_keeps_scope_c1_and_read_only_boundary(self) -> None:
        document = TOOL.build_cards()
        tool_id = "maintenance.preflight_producer_consumer_semantics"
        card = next(item for item in document["cards"] if item["tool_id"] == tool_id)
        c1 = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-producer-consumer-semantic-c1-evidence-r0.json").read_text(encoding="utf-8")
        )
        real_task = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-producer-consumer-semantic-real-task-r0.json").read_text(encoding="utf-8")
        )
        route = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-producer-consumer-semantic-route-evidence-r0.json").read_text(encoding="utf-8")
        )

        self.assertEqual(card["card_kind"], "OPTIONAL_EXPERIMENTAL_TOOL")
        self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertEqual(card["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["permissions"]["read_paths"], ["ignition/schemas/operations/toolbox-producer-consumer-semantic-input-r0.schema.json"])
        self.assertEqual(card["permissions"]["write_paths"], [])
        for permission in ("network", "secrets", "billing", "external_actions"):
            self.assertFalse(card["permissions"][permission])
        self.assertEqual(card["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(card["replacement_candidates"], [])
        self.assertEqual(card["unique_remaining_use_cases"], [])
        self.assertEqual(card["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(set(card["comparison_evidence"]["compared_tool_ids"]), {
            "collaboration.validate_agent_episode_binding",
            "collaboration.verify_handoff_artifact_files",
        })
        self.assertEqual(c1["c1_disposition"]["comparison_status"], "COMPARISON_UNKNOWN")
        self.assertEqual(real_task["invocation"]["contract_status"], "STATIC_REQUIRED_PATTERN_MISMATCH")
        self.assertEqual(real_task["invocation"]["check_statuses"], {"m2": "PRESENT", "p2": "MALFORMED_OR_REORDERED"})
        self.assertEqual(real_task["invocation"]["p2_field_statuses"]["focused_repair_checker_pass"], "ABSENT")
        self.assertFalse(real_task["invocation"]["claim_flags"]["consumer_code_executed"])
        self.assertFalse(real_task["invocation"]["claim_flags"]["execution_authorized"])
        trials = {row["scenario"]: row for row in route["route_trials"]}
        self.assertEqual(trials["default_light"]["selected_tool_ids"], [])
        self.assertEqual(trials["explicit_candidate"]["selected_tool_ids"], [tool_id])
        self.assertEqual(trials["candidate_with_adjacent_options"]["selected_tool_ids"], [tool_id])
        self.assertEqual(
            card["source_refs"],
            [ref for ref in card["source_refs"] if ref["path"].startswith("ignition/")],
        )

    def test_projection_keeps_current_registry_and_candidate_tools_separate(self) -> None:
        document = TOOL.build_cards()
        candidate_document = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8")
        )
        expected_candidate_count = len(candidate_document["candidates"])
        self.assertEqual(document["current_registry"]["operation_count"], 20)
        self.assertEqual(document["candidate_cards"]["candidate_count"], expected_candidate_count)
        self.assertEqual(document["card_count"], 20 + expected_candidate_count)
        current = [card for card in document["cards"] if card["card_kind"] == "CURRENT_OPERATION_REGISTRY_PROJECTION"]
        candidates = [card for card in document["cards"] if card["card_kind"] == "OPTIONAL_EXPERIMENTAL_TOOL"]
        self.assertEqual(len(current), 20)
        self.assertTrue(all(card["availability"] == "REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE" for card in current))
        self.assertTrue(all(card["router_selectable_by_default"] is False for card in candidates))
        for card in current + candidates:
            self.assertIn("replacement_candidates", card)
            self.assertIn("unique_remaining_use_cases", card)
            self.assertIn("comparison_evidence", card)
            self.assertIn("deprecation_or_retirement_status", card)
            self.assertIn("migration_and_rollback", card)
            self.assertTrue(card["migration_and_rollback"]["migration_notes"])
            self.assertTrue(card["migration_and_rollback"]["rollback_steps"])
        crossref = next(card for card in candidates if card["tool_id"] == "research.verify_crossref_metadata")
        pubmed = next(card for card in candidates if card["tool_id"] == "research.resolve_pubmed_identifiers")
        pubmed_search = next(card for card in candidates if card["tool_id"] == "research.search_pubmed_query")
        openalex = next(card for card in candidates if card["tool_id"] == "research.lookup_openalex_work_metadata")
        noaa = next(card for card in candidates if card["tool_id"] == "research.lookup_noaa_global_ch4_annual_growth")
        noaa_co2 = next(card for card in candidates if card["tool_id"] == "research.lookup_noaa_global_co2_annual_growth")
        updates = next(card for card in candidates if card["tool_id"] == "research.inspect_pubmed_update_links")
        pubmed_composition = next(card for card in candidates if card["tool_id"] == "research.audit_pubmed_updates_from_doi")
        editorial = next(card for card in candidates if card["tool_id"] == "writing.preflight_cognitive_migration_revision")
        europe_pmc = next(card for card in candidates if card["tool_id"] == "research.search_europe_pmc_query")
        europe_pmc_fulltext = next(card for card in candidates if card["tool_id"] == "research.resolve_europe_pmc_fulltext_locations")
        self.assertEqual({card["tool_id"] for card in candidates if card["permissions"]["network"]}, {crossref["tool_id"], "research.compare_crossref_reference_metadata", pubmed["tool_id"], pubmed_search["tool_id"], openalex["tool_id"], updates["tool_id"], pubmed_composition["tool_id"], "research.lookup_arxiv_paper_metadata", "research.search_arxiv_query", noaa["tool_id"], noaa_co2["tool_id"], europe_pmc["tool_id"], europe_pmc_fulltext["tool_id"]})
        self.assertEqual(crossref["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertEqual(pubmed["permissions"]["network_hosts"], ["pmc.ncbi.nlm.nih.gov"])
        self.assertEqual(openalex["permissions"]["network_hosts"], ["api.openalex.org"])
        self.assertEqual(updates["permissions"]["network_hosts"], ["eutils.ncbi.nlm.nih.gov"])
        self.assertEqual(pubmed_search["permissions"]["network_hosts"], ["eutils.ncbi.nlm.nih.gov"])
        self.assertEqual(europe_pmc["permissions"]["network_hosts"], ["www.ebi.ac.uk"])
        self.assertEqual(europe_pmc_fulltext["permissions"]["network_hosts"], ["www.ebi.ac.uk"])
        self.assertFalse(europe_pmc_fulltext["router_selectable_by_default"])
        self.assertEqual(europe_pmc_fulltext["replacement_candidates"], [])
        self.assertEqual(europe_pmc_fulltext["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertIn("fullTextUrlList", " ".join(europe_pmc_fulltext["output_types"]))
        self.assertEqual(europe_pmc["evidence_level"], "REAL_TOOL_TEST")
        self.assertFalse(europe_pmc["router_selectable_by_default"])
        self.assertFalse(pubmed_search["router_selectable_by_default"])
        self.assertEqual(pubmed_search["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertEqual(pubmed_search["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(pubmed_search["comparison_evidence"]["compared_tool_ids"], [europe_pmc["tool_id"]])
        self.assertEqual(pubmed_search["replacement_candidates"], [])
        self.assertTrue(pubmed_search["unique_remaining_use_cases"])
        self.assertIn("ncbi.nlm.nih.gov/About/disclaimer.html", pubmed_search["license"])
        self.assertIn("ncbi.nlm.nih.gov/home/about/policies/", pubmed_search["license"])
        self.assertNotIn("europepmc.org/RestfulWebService", pubmed_search["license"])
        pubmed_doc = (IGNITION_ROOT / "docs/operations/toolbox-pubmed-query-search.md").read_text(encoding="utf-8")
        self.assertIn("NCBI Disclaimer and Copyright notice", pubmed_doc)
        self.assertIn("ncbi.nlm.nih.gov/About/disclaimer.html", pubmed_doc)
        self.assertIn("ncbi.nlm.nih.gov/home/about/policies/", pubmed_doc)
        pubmed_real_task = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-pubmed-query-search-real-task-r0.json").read_text(encoding="utf-8")
        )
        pubmed_c1 = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-pubmed-query-search-c1-evidence-r0.json").read_text(encoding="utf-8")
        )
        self.assertFalse(pubmed_real_task["permission_and_privacy"]["contact_email_value_retained"])
        self.assertNotRegex(json.dumps(pubmed_real_task), r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
        self.assertTrue(pubmed_c1["comparison_design"]["identical_timestamp"])
        self.assertEqual(pubmed_c1["observations"]["shared_exact_pmid_count"], 0)
        self.assertEqual(pubmed_c1["disposition"]["status"], "COEXIST_SPECIALIZED")
        self.assertTrue(any("high-volume or concurrent requests" in item.lower() for item in pubmed_search["counterindicated_when"]))
        self.assertEqual(pubmed_search["permissions"]["write_paths"], [])
        self.assertFalse(pubmed_search["permissions"]["secrets"])
        self.assertFalse(pubmed_search["permissions"]["billing"])
        self.assertFalse(pubmed_search["permissions"]["external_actions"])
        self.assertIn("--allow-public-network", europe_pmc["entrypoint"])
        self.assertEqual(
            europe_pmc["comparison_evidence"]["compared_tool_ids"],
            [
                "research.verify_crossref_metadata",
                "research.lookup_openalex_work_metadata",
                "research.resolve_pubmed_identifiers",
                "research.inspect_pubmed_update_links",
                "research.lookup_arxiv_paper_metadata",
                "research.compare_publication_metadata_snapshots",
                "knowledge.cluster_source_brief",
                "knowledge.navigate_raw_evidence",
            ],
        )
        self.assertEqual(europe_pmc["replacement_candidates"], [])
        self.assertEqual(europe_pmc["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertEqual(crossref["permission_mode"], "READ_ONLY_FIXED_HOST_NETWORK_QUERY")
        self.assertIn("--allow-public-network", crossref["entrypoint"])
        self.assertFalse(crossref["router_selectable_by_default"])
        self.assertEqual(crossref["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertIn(
            {
                "path": "ignition/data/operations/toolbox-real-task-route-evidence-r0.json",
                "role": "REAL_TASK_ROUTE_AND_OUTCOME_EVIDENCE",
            },
            crossref["source_refs"],
        )
        self.assertEqual(crossref["estimated_cost"]["status"], "UNKNOWN")
        self.assertIn("article full text", " ".join(crossref["not_for"]))
        reference_comparator = next(card for card in candidates if card["tool_id"] == "research.compare_crossref_reference_metadata")
        self.assertEqual(reference_comparator["version"], "0.2.0")
        self.assertFalse(reference_comparator["router_selectable_by_default"])
        self.assertEqual(reference_comparator["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertTrue(reference_comparator["permissions"]["network"])
        self.assertEqual(reference_comparator["permissions"]["write_paths"], [])
        self.assertFalse(reference_comparator["permissions"]["secrets"])
        self.assertFalse(reference_comparator["permissions"]["billing"])
        self.assertFalse(reference_comparator["permissions"]["external_actions"])
        self.assertIn("--allow-public-network", reference_comparator["entrypoint"])
        self.assertEqual(reference_comparator["replacement_candidates"], [])
        self.assertEqual(reference_comparator["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertIn("Differences do not prove incorrect citations", reference_comparator["claim_ceiling"])
        self.assertIn("verify_source_link", " ".join(reference_comparator["accepted_input_types"]))
        self.assertIn("source Work", " ".join(reference_comparator["output_types"]))
        self.assertIn(
            "ignition/schemas/operations/toolbox-crossref-reference-metadata-comparison-input-r1.schema.json",
            {item["path"] for item in reference_comparator["source_refs"]},
        )
        self.assertIn("source Work request", " ".join(reference_comparator["side_effects"]))
        self.assertIn("research.verify_crossref_metadata", {item["tool_id"] for item in reference_comparator["alternatives"]})
        self.assertEqual(pubmed["permission_mode"], "READ_ONLY_FIXED_HOST_NETWORK_QUERY")
        self.assertEqual(pubmed["version"], "0.1.1")
        self.assertIn("--allow-public-network", pubmed["entrypoint"])
        self.assertEqual(pubmed["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertIn(
            {
                "path": "ignition/data/operations/toolbox-real-task-route-evidence-r0.json",
                "role": "REAL_TASK_ROUTE_AND_OUTCOME_EVIDENCE",
            },
            pubmed["source_refs"],
        )
        self.assertEqual(pubmed["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(pubmed["dependencies"], [])
        self.assertIn("scientific truth", pubmed["claim_ceiling"])
        self.assertEqual(openalex["permission_mode"], "READ_ONLY_FIXED_HOST_NETWORK_QUERY")
        self.assertIn("--allow-public-network", openalex["entrypoint"])
        self.assertEqual(openalex["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertEqual(openalex["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(openalex["dependencies"], [])
        self.assertFalse(openalex["router_selectable_by_default"])
        self.assertFalse(openalex["permissions"]["billing"])
        self.assertIn("is_retracted", " ".join(openalex["output_types"]))
        self.assertIn("scientific truth", openalex["claim_ceiling"])
        self.assertEqual(openalex["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(openalex["replacement_candidates"], [])
        self.assertTrue(openalex["unique_remaining_use_cases"])
        self.assertEqual(noaa["permissions"]["network_hosts"], ["gml.noaa.gov"])
        self.assertEqual(noaa["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(noaa["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(noaa["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertIn(
            {
                "path": "ignition/data/operations/toolbox-noaa-ch4-annual-growth-live-task-evidence-r0.json",
                "role": "REAL_BOUNDED_NOAA_TASK_OUTCOME_WITH_NO_RAW_RESPONSE_RETENTION",
            },
            noaa["source_refs"],
        )
        self.assertIn("--allow-public-network", noaa["entrypoint"])
        self.assertFalse(noaa["router_selectable_by_default"])
        self.assertEqual(noaa["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(set(noaa["comparison_evidence"]["compared_tool_ids"]), {"research.verify_crossref_metadata", "research.lookup_openalex_work_metadata", "research.lookup_noaa_global_co2_annual_growth"})
        self.assertEqual(noaa["replacement_candidates"], [])
        self.assertEqual(noaa["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertTrue(noaa["unique_remaining_use_cases"])
        self.assertIn("emissions", noaa["claim_ceiling"].lower())
        self.assertEqual(noaa_co2["permissions"]["network_hosts"], ["gml.noaa.gov"])
        self.assertEqual(noaa_co2["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(noaa_co2["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(noaa_co2["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(noaa_co2["dependencies"], [])
        self.assertIn("--allow-public-network", noaa_co2["entrypoint"])
        self.assertFalse(noaa_co2["router_selectable_by_default"])
        self.assertEqual(noaa_co2["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertIn(noaa["tool_id"], noaa_co2["comparison_evidence"]["compared_tool_ids"])
        self.assertIn("CO2", " ".join(noaa_co2["unique_remaining_use_cases"]))
        self.assertIn("emissions", noaa_co2["claim_ceiling"].lower())
        source_review = json.loads((IGNITION_ROOT / "data/operations/toolbox-noaa-co2-source-review-r0.json").read_text(encoding="utf-8"))
        self.assertEqual(source_review["candidate_tool_execution"]["tool_id"], noaa_co2["tool_id"])
        self.assertFalse(source_review["candidate_tool_execution"]["network_call_made_by_candidate"])
        self.assertEqual(source_review["observed_difference"]["disposition"], "UNRECONCILED_SOURCE_SURFACE_DIFFERENCE")
        co2_route = json.loads((IGNITION_ROOT / "data/operations/toolbox-noaa-co2-annual-growth-route-evidence-r0.json").read_text(encoding="utf-8"))
        self.assertEqual(co2_route["route_result"]["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in co2_route["route_result"]["selected_tools"]], [noaa_co2["tool_id"]])
        self.assertFalse(co2_route["execution_authorized"])
        self.assertFalse(co2_route["network_call_made"])
        self.assertEqual(
            co2_route["route_result"]["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            co2_route["candidate_catalog_git_blob_sha1"],
        )
        self.assertEqual(updates["permission_mode"], "READ_ONLY_FIXED_HOST_NETWORK_QUERY")
        self.assertIn("--allow-public-network", updates["entrypoint"])
        self.assertEqual(updates["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertEqual(updates["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(updates["dependencies"], [])
        self.assertEqual(updates["version"], "0.2.0")
        self.assertIn(
            "JSON stdin object with one to ten unique numeric PubMed IDs (PMIDs); optional expected_doi is accepted only for exactly one PMID and must be a bare DOI.",
            updates["accepted_input_types"],
        )
        self.assertTrue(any(ref["path"] == "ignition/schemas/operations/pubmed-update-link-inspection-input-r0.schema.json" for ref in updates["source_refs"]))
        self.assertIn("absence claim", updates["claim_ceiling"])
        self.assertEqual(updates["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertTrue(updates["unique_remaining_use_cases"])
        self.assertIn("ignition/data/operations/toolbox-pubmed-doi-update-c1-evidence-r1.json", [ref["path"] for ref in updates["source_refs"]])
        self.assertEqual(pubmed_composition["permissions"]["network_hosts"], ["pmc.ncbi.nlm.nih.gov", "eutils.ncbi.nlm.nih.gov"])
        self.assertEqual(pubmed_composition["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(pubmed_composition["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertEqual(pubmed_composition["version"], "0.2.0")
        self.assertFalse(pubmed_composition["router_selectable_by_default"])
        self.assertEqual(pubmed_composition["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(set(pubmed_composition["comparison_evidence"]["compared_tool_ids"]), {pubmed["tool_id"], updates["tool_id"]})
        self.assertEqual(pubmed_composition["replacement_candidates"], [])
        self.assertTrue(pubmed_composition["unique_remaining_use_cases"])
        self.assertEqual(editorial["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(editorial["evidence_level"], "REAL_TOOL_TEST")
        self.assertFalse(editorial["permissions"]["network"])
        self.assertEqual(editorial["permissions"]["write_paths"], [])
        self.assertFalse(editorial["router_selectable_by_default"])
        self.assertIn("publication readiness", editorial["claim_ceiling"])
        self.assertEqual(editorial["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(set(editorial["comparison_evidence"]["compared_tool_ids"]), {"writing.apply_editorial_method", "writing.validate_publication_surface"})
        self.assertEqual(editorial["replacement_candidates"], [])
        self.assertEqual(editorial["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertTrue(editorial["unique_remaining_use_cases"])
        batch = next(card for card in candidates if card["tool_id"] == "foundation.batch_resolve_current_asset_references")
        offline_snapshot_binding = next(
            card for card in candidates if card["tool_id"] == "research.bind_offline_source_snapshot_run"
        )
        offline_snapshot_verifier = next(
            card for card in candidates if card["tool_id"] == "research.verify_offline_source_snapshot_run"
        )
        specialized_tool_ids = {
            editorial["tool_id"],
            "maintenance.summarize_actions_step_timeline",
            "maintenance.compare_actions_repeated_step_sequences",
            "research.lookup_arxiv_paper_metadata",
            "research.search_arxiv_query",
            openalex["tool_id"],
            noaa["tool_id"],
            noaa_co2["tool_id"],
            batch["tool_id"],
            "collaboration.verify_handoff_artifact_files",
            "research.compare_publication_metadata_snapshots",
            pubmed["tool_id"],
            updates["tool_id"],
            pubmed_composition["tool_id"],
            "maintenance.attribute_actions_validation_evidence",
            "maintenance.inspect_exact_head_check_observations",
            "research.search_europe_pmc_query",
            "research.resolve_europe_pmc_fulltext_locations",
            "research.search_pubmed_query",
            "maintenance.compare_context_packet_variants",
            "maintenance.compare_audit_findings",
            "maintenance.summarize_actions_interval_union",
            offline_snapshot_binding["tool_id"],
            offline_snapshot_verifier["tool_id"],
        }
        self.assertTrue(all(card["comparison_evidence"]["status"] == "COMPARISON_UNKNOWN" for card in candidates if card["tool_id"] not in specialized_tool_ids))
        self.assertTrue(all(card["comparison_evidence"]["status"] == "COMPARISON_UNKNOWN" for card in current))
        self.assertTrue(all(card["permissions"]["write_paths"] == [] for card in candidates))
        self.assertTrue(all(card["dependencies"] or card["tool_id"] in {pubmed["tool_id"], pubmed_search["tool_id"], openalex["tool_id"], updates["tool_id"], "maintenance.summarize_actions_step_timeline", "research.lookup_arxiv_paper_metadata", "research.search_arxiv_query", noaa["tool_id"], noaa_co2["tool_id"], "knowledge.assemble_context_packet", "research.compare_publication_metadata_snapshots", "research.search_europe_pmc_query", "research.resolve_europe_pmc_fulltext_locations", "maintenance.compare_context_packet_variants", "maintenance.compare_audit_findings", "knowledge.preflight_reusable_context", "maintenance.inspect_exact_head_check_observations", "maintenance.summarize_execution_candidate_pareto_frontier", "maintenance.summarize_component_path_residue"} for card in candidates))
        self.assertTrue(all(card["source_refs_with_hashes"] for card in candidates))
        self.assertTrue(all(card["explicit_owner_authorization_required"] is False for card in candidates))
        self.assertEqual(batch["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(batch["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertIn("Python >=3.9 standard library", batch["runtime_dependencies"])
        self.assertIn("ambiguous", " ".join(batch["counterindicated_when"]).lower())
        self.assertTrue(any("legacy-mappings.jsonl" in path for path in batch["dependencies"]))
        self.assertEqual(batch["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(batch["comparison_evidence"]["compared_tool_ids"], ["foundation.resolve_current_asset"])
        self.assertEqual(batch["replacement_candidates"], [])
        self.assertTrue(batch["unique_remaining_use_cases"])
        self.assertEqual(offline_snapshot_binding["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(offline_snapshot_binding["execution_mode"], "READ_ONLY_RUN")
        self.assertFalse(offline_snapshot_binding["permissions"]["network"])
        self.assertFalse(offline_snapshot_binding["router_selectable_by_default"])
        self.assertEqual(offline_snapshot_binding["replacement_candidates"], [])
        self.assertTrue(offline_snapshot_binding["unique_remaining_use_cases"])
        self.assertEqual(offline_snapshot_verifier["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(
            offline_snapshot_verifier["comparison_evidence"]["compared_tool_ids"],
            ["collaboration.verify_handoff_artifact_files"],
        )
        self.assertEqual(offline_snapshot_verifier["execution_mode"], "READ_ONLY_RUN")
        self.assertFalse(offline_snapshot_verifier["permissions"]["network"])
        self.assertEqual(offline_snapshot_verifier["permissions"]["write_paths"], [])
        self.assertFalse(offline_snapshot_verifier["router_selectable_by_default"])
        self.assertEqual(offline_snapshot_verifier["replacement_candidates"], [])
        self.assertTrue(offline_snapshot_verifier["unique_remaining_use_cases"])
        self.assertEqual(offline_snapshot_verifier["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertEqual(batch["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        pack_catalog = next(card for card in candidates if card["tool_id"] == "runtime.inspect_declared_pack_catalog")
        self.assertEqual(pack_catalog["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(pack_catalog["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(pack_catalog["permissions"]["network"])
        self.assertEqual(pack_catalog["permissions"]["write_paths"], [])
        self.assertIn("no Pack module is loaded", pack_catalog["claim_ceiling"])
        self.assertIn("ignition/packs/", pack_catalog["dependencies"])
        reader = next(card for card in candidates if card["tool_id"] == "foundation.read_current_asset_card")
        self.assertEqual(reader["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(reader["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertEqual(reader["permissions"]["write_paths"], [])
        self.assertIn("both identity registries source-hashed", reader["claim_ceiling"])
        function_os = next(card for card in candidates if card["tool_id"] == "function_os.run_bounded_symbolic_spec")
        self.assertEqual(function_os["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(function_os["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(function_os["permissions"]["write_paths"], [])
        self.assertFalse(function_os["permissions"]["network"])
        self.assertIn("security isolation", function_os["claim_ceiling"])
        self.assertIn("isolated security sandbox", " ".join(function_os["not_for"]))
        archify = next(card for card in candidates if card["tool_id"] == "visualization.build_archify_derived_ir")
        self.assertEqual(archify["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(archify["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(archify["permissions"]["write_paths"], [])
        self.assertFalse(archify["permissions"]["network"])
        self.assertIn("unresolved caller-supplied revision", archify["claim_ceiling"])
        evidence = next(card for card in candidates if card["tool_id"] == "research.validate_evidence_program_snapshot")
        self.assertEqual(evidence["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(evidence["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(evidence["permissions"]["write_paths"], [])
        self.assertFalse(evidence["permissions"]["network"])
        self.assertIn("no source authenticity", evidence["claim_ceiling"])
        self.assertEqual(evidence["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(evidence["comparison_evidence"]["compared_tool_ids"], [])
        self.assertIn(
            "ignition/data/operations/toolbox-c1-evidence-program-validator-comparison-r0.json",
            evidence["comparison_evidence"]["evidence_refs"],
        )
        self.assertEqual(evidence["deprecation_or_retirement_status"]["status"], "COMPARISON_UNKNOWN")
        comparison = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-c1-evidence-program-validator-comparison-r0.json").read_text(encoding="utf-8")
        )
        self.assertTrue(comparison["comparison"]["same_validator_source_bytes"])
        self.assertTrue(comparison["comparison"]["outcome_parity_observed"])
        self.assertEqual(comparison["paired_invocations"][0]["check_count"], 499)
        self.assertEqual(comparison["paired_invocations"][1]["failure_count"], 0)
        timeline = next(card for card in candidates if card["tool_id"] == "maintenance.summarize_actions_step_timeline")
        self.assertEqual(timeline["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(timeline["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(timeline["permissions"]["write_paths"], [])
        self.assertFalse(timeline["permissions"]["network"])
        self.assertFalse(timeline["permissions"]["secrets"])
        self.assertFalse(timeline["permissions"]["billing"])
        self.assertFalse(timeline["permissions"]["external_actions"])
        self.assertIn("NOT_BILLABLE_MINUTES", timeline["claim_ceiling"])
        self.assertEqual(timeline["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(timeline["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertEqual(timeline["comparison_evidence"]["compared_tool_ids"], ["maintenance.compare_actions_repeated_step_sequences"])
        self.assertFalse(timeline["router_selectable_by_default"])
        actions_history = next(card for card in candidates if card["tool_id"] == "maintenance.compare_actions_repeated_step_sequences")
        self.assertEqual(actions_history["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(actions_history["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(actions_history["router_selectable_by_default"])
        self.assertFalse(actions_history["permissions"]["network"])
        self.assertEqual(actions_history["permissions"]["write_paths"], [])
        self.assertEqual(actions_history["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(actions_history["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(actions_history["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertEqual(actions_history["comparison_evidence"]["compared_tool_ids"], ["maintenance.summarize_actions_step_timeline"])
        self.assertEqual(actions_history["replacement_candidates"], [])
        self.assertTrue(actions_history["unique_remaining_use_cases"])
        self.assertIn("causal waste attribution", actions_history["claim_ceiling"])
        arxiv = next(card for card in candidates if card["tool_id"] == "research.lookup_arxiv_paper_metadata")
        self.assertEqual(arxiv["execution_mode"], "READ_ONLY_RUN")
        self.assertTrue(arxiv["permissions"]["network"])
        self.assertEqual(arxiv["permissions"]["network_hosts"], ["export.arxiv.org"])
        self.assertFalse(arxiv["router_selectable_by_default"])
        self.assertFalse(arxiv["permissions"]["secrets"])
        self.assertFalse(arxiv["permissions"]["billing"])
        self.assertFalse(arxiv["permissions"]["external_actions"])
        self.assertEqual(arxiv["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(arxiv["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertTrue(arxiv["unique_remaining_use_cases"])
        self.assertIn("does not authenticate", arxiv["claim_ceiling"])
        planner_card = next(card for card in candidates if card["tool_id"] == "ignition.adaptive_toolbox_route_planner")
        self.assertIn("allowed_network_hosts", " ".join(planner_card["accepted_input_types"]))
        self.assertIn("authorization", planner_card["claim_ceiling"])

    def test_candidate_catalog_schema_and_source_pin_are_valid(self) -> None:
        validator_path = IGNITION_ROOT / "tools/operations/validate_toolbox_candidates.py"
        validator_spec = importlib.util.spec_from_file_location("validate_toolbox_candidates", validator_path)
        validator = importlib.util.module_from_spec(validator_spec)
        assert validator_spec.loader is not None
        validator_spec.loader.exec_module(validator)
        self.assertEqual(validator.validate(), [])

    def test_legacy_candidate_without_c1_fields_defaults_to_unknown(self) -> None:
        validator_path = IGNITION_ROOT / "tools/operations/validate_toolbox_candidates.py"
        validator_spec = importlib.util.spec_from_file_location("validate_toolbox_candidates_legacy", validator_path)
        validator = importlib.util.module_from_spec(validator_spec)
        assert validator_spec.loader is not None
        validator_spec.loader.exec_module(validator)
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        legacy = catalog["candidates"][0]
        legacy_id = legacy["tool_id"]
        for field in ("replacement_candidates", "unique_remaining_use_cases", "comparison_evidence", "deprecation_or_retirement_status", "migration_and_rollback"):
            legacy.pop(field, None)
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate_catalog = Path(temp_dir) / "legacy-candidate-cards.json"
            candidate_catalog.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            with patch.object(validator, "CATALOG", candidate_catalog):
                self.assertEqual(validator.validate(), [])
            with patch.object(TOOL, "CANDIDATES_PATH", candidate_catalog):
                document = TOOL.build_cards()
        projected = next(card for card in document["cards"] if card["tool_id"] == legacy_id)
        self.assertEqual(projected["replacement_candidates"], [])
        self.assertEqual(projected["unique_remaining_use_cases"], [])
        self.assertEqual(projected["comparison_evidence"]["status"], "COMPARISON_UNKNOWN")
        self.assertEqual(projected["deprecation_or_retirement_status"]["status"], "COMPARISON_UNKNOWN")
        self.assertTrue(projected["migration_and_rollback"]["rollback_steps"])

    def test_unknown_comparison_cannot_authorize_retirement(self) -> None:
        validator_path = IGNITION_ROOT / "tools/operations/validate_toolbox_candidates.py"
        validator_spec = importlib.util.spec_from_file_location("validate_toolbox_candidates_retirement", validator_path)
        validator = importlib.util.module_from_spec(validator_spec)
        assert validator_spec.loader is not None
        validator_spec.loader.exec_module(validator)
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        catalog["candidates"][0]["deprecation_or_retirement_status"]["status"] = "DEPRECATED"
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate_catalog = Path(temp_dir) / "candidate-cards.json"
            candidate_catalog.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            with patch.object(validator, "CATALOG", candidate_catalog):
                errors = validator.validate()
        self.assertTrue(any("unknown comparison cannot support deprecation or removal" in error for error in errors))

    def test_candidate_schema_rejects_dependency_path_traversal(self) -> None:
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-candidate-cards-r0.schema.json").read_text(encoding="utf-8"))
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        catalog["candidates"][0]["dependencies"].append("ignition/../../outside.py")
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))

    def test_network_candidate_requires_a_bounded_exact_host(self) -> None:
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-candidate-cards-r0.schema.json").read_text(encoding="utf-8"))
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        crossref = next(row for row in catalog["candidates"] if row["tool_id"] == "research.verify_crossref_metadata")
        crossref["permissions"].pop("network_hosts")
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))
        crossref["permissions"]["network_hosts"] = ["*.crossref.org"]
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))
        crossref["permissions"]["network_hosts"] = ["127.0.0.1"]
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))
        crossref["permissions"]["network_hosts"] = [f"host-{index}.example.org" for index in range(17)]
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))


if __name__ == "__main__":
    unittest.main()
