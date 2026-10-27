from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import validate_ignition_operation_playbooks as validator  # noqa: E402
import plan_ignition_operation_run as operation_planner  # noqa: E402


class IgnitionOperationPlaybooksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.playbooks = validator.load_json(validator.PLAYBOOKS_PATH)
        self.registry = validator.load_json(validator.REGISTRY_PATH)
        self.candidate_cards = operation_planner.load_json(operation_planner.EXPERIMENTAL_TOOL_CARDS_PATH)["candidates"]

    def route_profile(self, card, *, input_type=None, output=None, allowed_network_hosts=None):
        permissions = card["permissions"]
        return {
            "task_id": "noaa-gas-toolbox-routing-test",
            "current_ref": "3f5f359650dcba6943e389dffe446afecc33b953",
            "input_types": [input_type or card["accepted_input_types"][0]],
            "required_outputs": [output or card["output_types"][0]],
            "allowed_execution_modes": [card["execution_mode"]],
            "allowed_network_hosts": (
                allowed_network_hosts
                if allowed_network_hosts is not None
                else permissions.get("network_hosts", [])
            ),
        }

    def test_current_playbooks_and_generated_view_pass(self) -> None:
        self.assertEqual(validator.validate(copy.deepcopy(self.playbooks)), [])
        self.assertEqual(len(self.playbooks["playbooks"]), 16)
        self.assertEqual(len(self.playbooks["excluded_status_only"]), 4)
        self.assertEqual(len(self.playbooks["category_audit"]), 11)

    def test_callable_registry_coverage_is_exact(self) -> None:
        operations = {row["operation_id"]: row for row in self.registry["operations"]}
        expected = sorted(
            operation_id
            for operation_id, row in operations.items()
            if row["current_status"] in validator.CALLABLE_STATUSES
            and row["ai_callability"] in validator.CALLABLE_AI
        )
        actual = [row["operation_id"] for row in self.playbooks["playbooks"]]
        self.assertEqual(actual, expected)
        self.assertNotIn("external.live_invocation", actual)
        self.assertNotIn("executor.reference_conformance", actual)

    def test_missing_callable_playbook_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        candidate["playbooks"] = candidate["playbooks"][1:]
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("callable playbook coverage mismatch" in error for error in errors))

    def test_status_only_operation_cannot_receive_playbook(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        extra = copy.deepcopy(candidate["playbooks"][0])
        extra["operation_id"] = "external.live_invocation"
        candidate["playbooks"].append(extra)
        candidate["playbooks"].sort(key=lambda row: row["operation_id"])
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("callable playbook coverage mismatch" in error for error in errors))
        self.assertTrue(any("non-callable operation" in error for error in errors))

    def test_category_cannot_reference_unknown_operation(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        candidate["category_audit"][0]["operation_ids"].append("knowledge.imagined_retrieval")
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("unknown operation IDs" in error for error in errors))

    def test_covered_current_requires_current_operation(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        row = next(item for item in candidate["category_audit"] if item["category_id"] == "translation_language_thought")
        row["coverage_status"] = "COVERED_CURRENT"
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("COVERED_CURRENT requires a CURRENT operation" in error for error in errors))

    def test_human_view_projects_required_playbook_fields(self) -> None:
        rendered = validator.render_markdown(self.playbooks, self.registry)
        self.assertEqual(rendered, validator.HUMAN_VIEW_PATH.read_text(encoding="utf-8"))
        self.assertEqual(rendered.count("### `"), 16)
        for heading in (
            "用户常见意图：",
            "输入（registry-derived）：",
            "最小 Current read set：",
            "执行步骤：",
            "必须检查的 authority：",
            "允许的最大输出：",
            "Stop conditions：",
            "不得做什么：",
        ):
            self.assertEqual(rendered.count(heading), 16)
        self.assertEqual(rendered.count("ignition/data/operations/ignition-run-output-contract-r1.json"), 16)

    def test_authored_playbooks_do_not_duplicate_registry_fields(self) -> None:
        allowed = {
            "operation_id",
            "common_natural_language_intents",
            "execution_steps",
            "stop_conditions",
            "prohibitions",
        }
        self.assertTrue(all(set(row) == allowed for row in self.playbooks["playbooks"]))

    def test_experimental_tools_are_default_off_and_never_authorize_execution(self) -> None:
        for card in self.candidate_cards:
            with self.subTest(tool_id=card["tool_id"]):
                profile = self.route_profile(card)
                plan = operation_planner.plan_tool_route(profile)
                self.assertNotEqual(plan["decision"], "COMPLETE")
                self.assertNotIn(card["tool_id"], [row["tool_id"] for row in plan["selected_tools"]])
                self.assertIn(
                    {"tool_id": card["tool_id"], "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
                    plan["rejected_candidates"],
                )
                self.assertFalse(plan["execution_authorized"])

    def test_existing_planner_cli_proposes_candidate_only_after_explicit_opt_in(self) -> None:
        card = next(row for row in self.candidate_cards if row["tool_id"] == "research.pair_noaa_co2_ch4_growth_by_year")
        profile = self.route_profile(card)
        cli = [sys.executable, str(IGNITION_ROOT / "tools/operations/plan_ignition_operation_run.py"), "--route-request"]
        default = subprocess.run(
            cli,
            input=json.dumps(profile),
            text=True,
            capture_output=True,
            cwd=IGNITION_ROOT,
            check=False,
        )
        self.assertEqual(default.returncode, 2)
        default_plan = json.loads(default.stdout)
        self.assertEqual(default_plan["selected_tools"], [])
        opted_in = subprocess.run(
            cli + ["--allow-experimental", card["tool_id"]],
            input=json.dumps(profile),
            text=True,
            capture_output=True,
            cwd=IGNITION_ROOT,
            check=False,
        )
        self.assertEqual(opted_in.returncode, 0, opted_in.stderr)
        opted_in_plan = json.loads(opted_in.stdout)
        self.assertEqual(opted_in_plan["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted_in_plan["selected_tools"]], [card["tool_id"]])
        self.assertFalse(opted_in_plan["execution_authorized"])

    def test_real_route_experiment_receipt_binds_router_catalog_and_offline_replay(self) -> None:
        receipt_path = IGNITION_ROOT / "data/operations/toolbox-noaa-gas-adaptive-routing-real-task-experiment-r0.json"
        receipt = operation_planner.load_json(receipt_path)
        bindings = receipt["bindings"]
        self.assertEqual(receipt["schema_version"], "ignition-toolbox-route-experiment-r0")
        self.assertEqual(bindings["candidate_count"], 9)
        self.assertEqual(
            bindings["planner_git_blob_sha1"],
            operation_planner.git_blob_sha1((IGNITION_ROOT / "tools/operations/plan_ignition_operation_run.py").read_bytes()),
        )
        self.assertEqual(
            bindings["candidate_catalog_git_blob_sha1"],
            operation_planner.git_blob_sha1((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_bytes()),
        )
        self.assertEqual(
            bindings["current_operation_registry_git_blob_sha1"],
            operation_planner.git_blob_sha1((IGNITION_ROOT / "data/operations/ignition-operation-capability-registry-r1.json").read_bytes()),
        )
        trials = receipt["route_trials"]
        self.assertEqual(trials["default_no_experimental_opt_in"]["decision"], "INCOMPLETE")
        self.assertEqual(trials["default_no_experimental_opt_in"]["selected_tool_ids"], [])
        self.assertEqual(trials["sufficient_pairer_only"]["selected_tool_ids"], ["research.pair_noaa_co2_ch4_growth_by_year"])
        self.assertEqual(trials["all_nine_allowlisted_with_exact_noaa_host"]["selected_tool_ids"], ["research.pair_noaa_co2_ch4_growth_by_year"])
        self.assertEqual(
            trials["unneeded_co2_comparator_skipped"]["skipped_candidates"],
            [{"tool_id": "research.compare_noaa_co2_source_surfaces", "reason": "NO_REQUIRED_OUTPUT_MATCH"}],
        )
        self.assertEqual(
            trials["co2_comparator_supplemented_for_extra_required_output"]["selected_tool_ids"],
            ["research.pair_noaa_co2_ch4_growth_by_year", "research.compare_noaa_co2_source_surfaces"],
        )
        self.assertTrue(all(not trial["execution_authorized"] for trial in trials.values()))
        self.assertTrue(all(trial["cost_estimate"]["status"] == "UNKNOWN" for trial in trials.values()))

        replay = receipt["actual_selected_tool_replay"]
        input_bytes = (IGNITION_ROOT / "data/operations/toolbox-noaa-co2-ch4-growth-pair-n2o-extension-real-task-input-r1.json").read_bytes()
        expected_output = (IGNITION_ROOT / "data/operations/toolbox-noaa-co2-ch4-growth-pair-n2o-extension-real-task-output-r1.json").read_bytes()
        self.assertEqual(replay["input_sha256"], hashlib.sha256(input_bytes).hexdigest())
        self.assertEqual(replay["expected_output_sha256"], hashlib.sha256(expected_output).hexdigest())
        self.assertEqual(replay["actual_output_sha256"], replay["expected_output_sha256"])
        self.assertTrue(replay["all_replays_byte_identical_to_captured_output"])
        self.assertEqual(replay["invocations"], 1)
        self.assertEqual(replay["network_calls"], 0)
        self.assertEqual(replay["cash_cost"], "UNKNOWN")

    def test_explicit_opt_in_routes_each_candidate_under_its_declared_bounds(self) -> None:
        for card in self.candidate_cards:
            with self.subTest(tool_id=card["tool_id"]):
                profile = self.route_profile(card)
                plan = operation_planner.plan_tool_route(
                    profile,
                    include_experimental_tool_ids=[card["tool_id"]],
                )
                self.assertEqual(plan["decision"], "COMPLETE")
                self.assertEqual([row["tool_id"] for row in plan["selected_tools"]], [card["tool_id"]])
                selected = plan["selected_tools"][0]
                self.assertEqual(selected["permissions"], card["permissions"])
                self.assertFalse(plan["execution_authorized"])
                self.assertFalse(selected["explicit_owner_authorization_required"])

    def test_minimal_pairing_route_ignores_redundant_allowlisted_tools(self) -> None:
        card = next(row for row in self.candidate_cards if row["tool_id"] == "research.pair_noaa_co2_ch4_growth_by_year")
        r1_output = card["output_types"][2]
        r1_input = card["accepted_input_types"][1]
        profile = self.route_profile(card, input_type=r1_input, output=r1_output)
        all_ids = [row["tool_id"] for row in self.candidate_cards]
        baseline = operation_planner.plan_tool_route(profile)
        sufficient = operation_planner.plan_tool_route(profile, include_experimental_tool_ids=[card["tool_id"]])
        broad_host_profile = copy.deepcopy(profile)
        broad_host_profile["allowed_network_hosts"] = ["gml.noaa.gov"]
        redundant = operation_planner.plan_tool_route(broad_host_profile, include_experimental_tool_ids=all_ids)
        self.assertEqual(baseline["decision"], "INCOMPLETE")
        self.assertEqual(baseline["selected_tools"], [])
        self.assertEqual(sufficient["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in sufficient["selected_tools"]], [card["tool_id"]])
        self.assertEqual(redundant["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in redundant["selected_tools"]], [card["tool_id"]])
        self.assertEqual(
            ({row["tool_id"] for row in redundant["rejected_candidates"]}
             | {row["tool_id"] for row in redundant["skipped_candidates"]})
            & set(all_ids),
            set(all_ids) - {card["tool_id"]},
        )
        self.assertTrue(all(
            row["reason"] == "NO_INPUT_TYPE_MATCH"
            for row in redundant["rejected_candidates"]
            if row["tool_id"] in set(all_ids) - {card["tool_id"]}
        ))
        self.assertFalse(sufficient["execution_authorized"])
        self.assertEqual(sufficient["cost_estimate"]["status"], "UNKNOWN")

    def test_available_tool_is_skipped_when_its_unique_output_is_unneeded(self) -> None:
        pairer = next(row for row in self.candidate_cards if row["tool_id"] == "research.pair_noaa_co2_ch4_growth_by_year")
        co2_compare = next(row for row in self.candidate_cards if row["tool_id"] == "research.compare_noaa_co2_source_surfaces")
        profile = self.route_profile(
            pairer,
            input_type=pairer["accepted_input_types"][1],
            output=pairer["output_types"][2],
            allowed_network_hosts=co2_compare["permissions"]["network_hosts"],
        )
        profile["input_types"].append(co2_compare["accepted_input_types"][0])
        plan = operation_planner.plan_tool_route(
            profile,
            include_experimental_tool_ids=[pairer["tool_id"], co2_compare["tool_id"]],
        )
        self.assertEqual(plan["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in plan["selected_tools"]], [pairer["tool_id"]])
        self.assertEqual(
            plan["skipped_candidates"],
            [{"tool_id": co2_compare["tool_id"], "reason": "NO_REQUIRED_OUTPUT_MATCH"}],
        )

    def test_additional_source_surface_detail_is_supplemented_only_when_required(self) -> None:
        pairer = next(row for row in self.candidate_cards if row["tool_id"] == "research.pair_noaa_co2_ch4_growth_by_year")
        co2_compare = next(row for row in self.candidate_cards if row["tool_id"] == "research.compare_noaa_co2_source_surfaces")
        pairer_output = pairer["output_types"][2]
        detailed_co2_output = co2_compare["output_types"][0]
        profile = self.route_profile(
            pairer,
            input_type=pairer["accepted_input_types"][1],
            output=pairer_output,
            allowed_network_hosts=co2_compare["permissions"]["network_hosts"],
        )
        profile["input_types"].append(co2_compare["accepted_input_types"][0])
        profile["required_outputs"].append(detailed_co2_output)
        pairer_only = operation_planner.plan_tool_route(
            profile,
            include_experimental_tool_ids=[pairer["tool_id"]],
        )
        supplemented = operation_planner.plan_tool_route(
            profile,
            include_experimental_tool_ids=[pairer["tool_id"], co2_compare["tool_id"]],
        )
        self.assertEqual(pairer_only["decision"], "INCOMPLETE")
        self.assertEqual(pairer_only["unmet_outputs"], [detailed_co2_output])
        self.assertEqual(supplemented["decision"], "COMPLETE")
        self.assertEqual(
            [row["tool_id"] for row in supplemented["selected_tools"]],
            [pairer["tool_id"], co2_compare["tool_id"]],
        )
        self.assertEqual(supplemented["skipped_candidates"], [])
        self.assertFalse(supplemented["execution_authorized"])

    def test_network_candidates_require_exact_caller_allowed_hosts(self) -> None:
        for card in self.candidate_cards:
            if not card["permissions"]["network"]:
                continue
            with self.subTest(tool_id=card["tool_id"]):
                profile = self.route_profile(card, allowed_network_hosts=[])
                rejected = operation_planner.plan_tool_route(
                    profile,
                    include_experimental_tool_ids=[card["tool_id"]],
                )
                self.assertNotEqual(rejected["decision"], "COMPLETE")
                self.assertIn(
                    {"tool_id": card["tool_id"], "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
                    rejected["rejected_candidates"],
                )
                profile["allowed_network_hosts"] = card["permissions"]["network_hosts"]
                allowed = operation_planner.plan_tool_route(
                    profile,
                    include_experimental_tool_ids=[card["tool_id"]],
                )
                self.assertEqual(allowed["decision"], "COMPLETE")
                self.assertEqual(allowed["allowed_network_hosts"], card["permissions"]["network_hosts"])
                self.assertFalse(allowed["execution_authorized"])

    def test_network_host_allowlist_rejects_wildcards_urls_ports_and_ip_literals(self) -> None:
        card = next(row for row in self.candidate_cards if row["permissions"]["network"])
        for host in ("*.noaa.gov", "https://gml.noaa.gov", "gml.noaa.gov:443", "127.0.0.1"):
            with self.subTest(host=host):
                profile = self.route_profile(card, allowed_network_hosts=[host])
                with self.assertRaises(operation_planner.RunPlanningError):
                    operation_planner.plan_tool_route(
                        profile,
                        include_experimental_tool_ids=[card["tool_id"]],
                    )

    def test_species_mismatch_does_not_route_n2o_lookup(self) -> None:
        n2o = next(row for row in self.candidate_cards if row["tool_id"] == "research.lookup_noaa_global_n2o_annual_growth")
        co2 = next(row for row in self.candidate_cards if row["tool_id"] == "research.lookup_noaa_global_co2_annual_growth")
        profile = self.route_profile(
            n2o,
            input_type=co2["accepted_input_types"][0],
            allowed_network_hosts=n2o["permissions"]["network_hosts"],
        )
        plan = operation_planner.plan_tool_route(profile, include_experimental_tool_ids=[n2o["tool_id"]])
        self.assertNotEqual(plan["decision"], "COMPLETE")
        self.assertNotIn(n2o["tool_id"], [row["tool_id"] for row in plan["selected_tools"]])
        self.assertIn(
            {"tool_id": n2o["tool_id"], "reason": "NO_INPUT_TYPE_MATCH"},
            plan["rejected_candidates"],
        )


if __name__ == "__main__":
    unittest.main()
