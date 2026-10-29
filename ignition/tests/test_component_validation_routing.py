from __future__ import annotations

import copy
import io
import json
import sys
import subprocess
import tempfile
import unittest
from types import ModuleType
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.operations.compute_change_propagation import load_json  # noqa: E402
from tools.operations.route_component_validation import (  # noqa: E402
    FULL_REGRESSION_PATHS,
    MAP_PATH,
    MAP_SCHEMA_PATH,
    REGISTRY_PATH,
    TOPOLOGY_PATH,
    RoutingBlocked,
    _module_file,
    _validate_checkout_binding,
    plan_paths,
    validate_validation_map,
)
from tools.operations.run_component_validation_targets import (  # noqa: E402
    _run_suite,
    collect_registered_test_ids,
    run_commands,
    run_modules,
    run_plan,
)


class ComponentValidationRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_json(REGISTRY_PATH)
        cls.topology = load_json(TOPOLOGY_PATH)
        cls.validation_map = load_json(MAP_PATH)
        cls.schema = load_json(MAP_SCHEMA_PATH)

    def plan(self, paths, **kwargs):
        registry = kwargs.pop("registry", copy.deepcopy(self.registry))
        topology = kwargs.pop("topology", copy.deepcopy(self.topology))
        validation_map = kwargs.pop("validation_map", copy.deepcopy(self.validation_map))
        schema = kwargs.pop("schema", self.schema)
        verify_target_files = kwargs.pop("verify_target_files", False)
        return plan_paths(
            paths,
            registry=registry,
            topology=topology,
            validation_map=validation_map,
            schema=schema,
            verify_target_files=verify_target_files,
            **kwargs,
        )

    def test_openalex_change_selects_research_slot_and_its_real_consumer_tests(self):
        result = self.plan(["scripts/external-research/openalex_client.py"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["R"])
        self.assertEqual(result["seed_components"], ["openalex_adapter_r1"])
        self.assertIn("research_workflow_slot", result["affected_component_closure"])
        self.assertIn("openalex_adapter_consumed_by_research_workflow_slot", result["traversed_relations"])
        self.assertEqual(result["selected_target_ids"], ["r_research_slot_consumers"])
        self.assertEqual(result["path_component_evidence"][0]["components"][0]["component_id"], "openalex_adapter_r1")

    def test_crossref_verifier_change_selects_the_live_research_cli_consumer(self):
        result = self.plan(["evidence-program/tools/run_crossref_verification.py"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["R"])
        self.assertEqual(result["seed_components"], ["crossref_verifier_r1"])
        self.assertIn("research_workflow_slot", result["affected_component_closure"])
        self.assertIn(
            "crossref_verifier_consumed_by_research_workflow_slot",
            result["traversed_relations"],
        )
        self.assertEqual(result["selected_target_ids"], ["r_research_slot_consumers"])

    def test_research_slot_change_routes_to_r_consumers(self):
        result = self.plan(["research_workflow/slot.py"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["R"])
        self.assertEqual(result["selected_target_ids"], ["r_research_slot_consumers"])

    def test_o_only_change_selects_output_consumers(self):
        result = self.plan(["data/governance/knowledge-experience/manifest.json"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["O"])
        self.assertEqual(result["selected_target_ids"], ["o_human_result_consumers"])

    def test_ai_usage_guide_routes_to_its_registered_o_component(self):
        result = self.plan(["ignition/docs/AI-USAGE.md"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["O"])
        self.assertEqual(result["seed_components"], ["ai_guide"])
        self.assertEqual(result["selected_target_ids"], ["o_human_result_consumers"])

    def test_human_usage_guide_routes_to_operating_method_consumers(self):
        result = self.plan(["ignition/docs/USAGE.md"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["G"])
        self.assertEqual(result["seed_components"], ["usage"])
        self.assertEqual(result["selected_target_ids"], ["g_operating_method_consumers"])

    def test_foundation_only_change_requires_full_regression_and_actual_consumer_targets(self):
        result = self.plan(["data/foundation/README.md"])
        self.assertEqual(result["mode"], "FULL")
        self.assertEqual(result["seed_components"], ["foundation"])
        self.assertEqual(
            result["selected_target_ids"],
            [
                "g_current_state_consumers",
                "g_epistemic_boundary_consumers",
                "g_federation_boundary_consumers",
                "g_foundation_argument_consumers",
                "g_foundation_formal_consumers",
                "g_human_front_door_consumers",
                "g_publication_consumers",
                "g_repository_path_consumers",
                "o_human_result_consumers",
            ],
        )
        self.assertEqual(result["domains"], ["G", "O", "R"])
        self.assertTrue(any(
            reason == {"kind": "component_requires_full_regression", "component_id": "foundation"}
            for reason in result["full_regression_reasons"]
        ))

    def test_g_only_change_selects_governance_controls(self):
        result = self.plan(["data/governance/history-remediation-register.json"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["G"])
        self.assertEqual(result["selected_target_ids"], ["g_history_remediation_contract"])

    def test_actual_cross_domain_consumer_closure_runs_only_affected_targets(self):
        result = self.plan(["tests/fixtures/ignition-operating-method/homepage-ai-first-r1.json"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["G", "O"])
        self.assertEqual(
            result["seed_components"],
            ["ignition_operating_method", "propagation_calculator"],
        )
        self.assertTrue({"sync", "readme", "human_knowledge_surfaces"}.issubset(
            set(result["affected_component_closure"])
        ))
        self.assertEqual(
            set(result["selected_target_ids"]),
            {
                "g_component_release_controls",
                "g_human_front_door_consumers",
                "g_operating_method_consumers",
                "g_repository_path_consumers",
                "o_human_result_consumers",
            },
        )
        self.assertEqual(result["full_regression_reasons"], [])
        self.assertEqual(
            {edge["relation_id"] for edge in result["cross_domain_impact"]["traversed_cross_domain_relations"]},
            {"sync_requires_readme", "human_results_depend_on_readme"},
        )

    def test_independent_multidomain_changes_select_each_direct_component_target(self):
        result = self.plan([
            "scripts/external-research/openalex_client.py",
            "data/governance/knowledge-experience/manifest.json",
        ])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["O", "R"])
        self.assertEqual(result["selected_target_ids"], ["o_human_result_consumers", "r_research_slot_consumers"])
        self.assertEqual(result["cross_domain_impact"]["direct_seed_domains"], ["O", "R"])
        self.assertEqual(result["cross_domain_impact"]["traversed_cross_domain_relations"], [])
        self.assertEqual(result["full_regression_reasons"], [])

    def test_cochanged_research_consumer_test_requires_full_regression(self):
        result = self.plan([
            "research_workflow/slot.py",
            "research_workflow/test_pluggable_slot.py",
        ])
        self.assertEqual(result["mode"], "FULL")
        self.assertEqual(result["selected_target_ids"], ["r_research_slot_consumers"])
        reason = next(x for x in result["full_regression_reasons"] if x["kind"] == "validation_target_changed")
        self.assertEqual(reason["paths"], ["research_workflow/test_pluggable_slot.py"])

    def test_registered_consumer_test_alone_routes_to_full_without_unknown_path(self):
        result = self.plan(["research_workflow/test_research_workflow.py"])
        self.assertEqual(result["mode"], "FULL")
        self.assertEqual(result["seed_components"], [])
        self.assertEqual(result["selected_target_ids"], ["r_research_slot_consumers"])
        self.assertEqual(result["changed_validation_test_targets"], ["r_research_slot_consumers"])
        self.assertEqual(result["domains"], ["R"])

    def test_cochanged_governance_consumer_test_requires_full_regression(self):
        result = self.plan([
            "data/governance/history-remediation-register.json",
            "tests/test_history_remediation_contract.py",
        ])
        self.assertEqual(result["mode"], "FULL")
        self.assertIn("g_history_remediation_contract", result["selected_target_ids"])
        reason = next(x for x in result["full_regression_reasons"] if x["kind"] == "validation_target_changed")
        self.assertEqual(reason["paths"], ["tests/test_history_remediation_contract.py"])

    def test_shared_formal_layers_require_full_regression_and_their_consumers(self):
        examples = {
            "data/foundation/formal-objects.jsonl": "g_foundation_formal_consumers",
            "data/foundation/arguments.jsonl": "g_foundation_argument_consumers",
            "docs/math-foundation/claims.md": "g_foundation_formal_consumers",
        }
        for path, target_id in examples.items():
            with self.subTest(path=path):
                result = self.plan([path])
                self.assertEqual(result["mode"], "FULL")
                self.assertEqual(result["domains"], ["G", "O", "R"])
                self.assertIn(target_id, result["selected_target_ids"])

    def test_path_evidence_names_the_registered_overlap_authority(self):
        result = self.plan(["data/foundation/formal-objects.jsonl"])
        item = result["path_component_evidence"][0]
        self.assertIn("authorized_overlap", item)
        self.assertEqual(item["authorized_overlap"]["authority_source"], "FOUNDATION.md")
        self.assertIn("formal-objects.jsonl", item["path"])

    def test_q33_era_resolver_evidence_routes_to_existing_arr_consumers(self):
        result = self.plan([
            "evidence/adaptive-relational-runtime-r2-q33-era-resolver-repair-r1/CI_FAILURE_REPRODUCTION.md"
        ])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["seed_components"], ["arr"])
        self.assertIn("g_repository_path_consumers", result["selected_target_ids"])
        self.assertIn("g_arr_runtime", result["selected_target_ids"])

    def test_unmapped_path_is_not_hidden_by_an_independent_full_trigger(self):
        with self.assertRaisesRegex(RoutingBlocked, "unmapped_path"):
            self.plan([".github/workflows/foundation-validation.yml", "tools/unregistered-output.py"])

    def test_router_authority_change_requires_full_regression(self):
        path = "tools/operations/route_component_validation.py"
        self.assertIn(path, FULL_REGRESSION_PATHS)
        result = self.plan([path])
        self.assertEqual(result["mode"], "FULL")
        self.assertIn("component_validation_router", result["affected_component_closure"])

    def test_shared_workflow_change_requires_full_regression(self):
        result = self.plan([".github/workflows/foundation-validation.yml"])
        self.assertEqual(result["mode"], "FULL")
        self.assertTrue(any(x["kind"] == "validation_authority_changed" for x in result["full_regression_reasons"]))

    def test_unknown_path_blocks_instead_of_running_zero_targets(self):
        with self.assertRaisesRegex(RoutingBlocked, "unmapped_path"):
            self.plan(["tools/unregistered-output.py"])

    def test_empty_diff_blocks_instead_of_becoming_green(self):
        with self.assertRaisesRegex(RoutingBlocked, "empty Git diff"):
            self.plan([])

    def test_unknown_transitive_consumer_blocks(self):
        topology = copy.deepcopy(self.topology)
        topology["relations"].append({
            "relation_id": "research_slot_to_unmapped_consumer_fixture",
            "source": "research_workflow_slot",
            "target": "l1",
            "relation_class": "lifecycle_depends_on",
            "relation_domain": "repository_dependency",
            "trigger_dimensions": [],
            "trigger_classifications": [],
            "propagation_mode": "required_assessment",
            "required_evaluation": True,
            "creates_sync_obligation": False,
            "map_visible": False,
            "label": "negative fixture for unresolved consumer ownership",
            "declaration_source": "test fixture only",
            "claim_ceiling": "negative fixture",
            "residue": [],
        })
        with self.assertRaisesRegex(RoutingBlocked, "lack reviewed R/O/G ownership or targets"):
            self.plan(["research_workflow/slot.py"], topology=topology)

    def test_cycle_in_declared_consumer_closure_blocks(self):
        topology = copy.deepcopy(self.topology)
        topology["relations"].append({
            "relation_id": "research_slot_back_to_openalex_fixture",
            "source": "research_workflow_slot",
            "target": "openalex_adapter_r1",
            "relation_class": "lifecycle_depends_on",
            "relation_domain": "repository_dependency",
            "trigger_dimensions": [],
            "trigger_classifications": [],
            "propagation_mode": "required_assessment",
            "required_evaluation": True,
            "creates_sync_obligation": False,
            "map_visible": False,
            "label": "negative fixture for a dependency cycle",
            "declaration_source": "test fixture only",
            "claim_ceiling": "negative fixture",
            "residue": [],
        })
        with self.assertRaisesRegex(RoutingBlocked, "cycle requiring adjudication"):
            self.plan(["scripts/external-research/openalex_client.py"], topology=topology)

    def test_duplicate_topology_relation_ids_block(self):
        topology = copy.deepcopy(self.topology)
        topology["relations"].append(copy.deepcopy(topology["relations"][0]))
        with self.assertRaisesRegex(RoutingBlocked, "duplicate topology relation ID"):
            self.plan(["scripts/external-research/openalex_client.py"], topology=topology)

    def test_substantive_causal_candidate_is_not_promoted_to_ci_edge(self):
        topology = copy.deepcopy(self.topology)
        topology["relations"].append({
            "relation_id": "candidate_only_openalex_to_output_fixture",
            "source": "openalex_adapter_r1",
            "target": "human_knowledge_surfaces",
            "relation_class": "mechanism_hypothesis",
            "relation_domain": "substantive_causal_candidate",
            "trigger_dimensions": [],
            "trigger_classifications": [],
            "propagation_mode": "informational_only",
            "required_evaluation": False,
            "creates_sync_obligation": False,
            "map_visible": False,
            "label": "negative fixture for an unverified causal hypothesis",
            "declaration_source": "test fixture only",
            "claim_ceiling": "negative fixture",
            "residue": [],
        })
        result = self.plan(["scripts/external-research/openalex_client.py"], topology=topology)
        self.assertNotIn("human_knowledge_surfaces", result["affected_component_closure"])
        self.assertIn("candidate_only_openalex_to_output_fixture", result["excluded_substantive_causal_candidates"])
        self.assertEqual(result["domains"], ["R"])

    def test_unrelated_seed_dimensions_do_not_activate_an_r_consumer_edge(self):
        topology = copy.deepcopy(self.topology)
        topology["relations"].append({
            "relation_id": "unrelated_governance_edge_from_r_fixture",
            "source": "openalex_adapter_r1",
            "target": "human_knowledge_surfaces",
            "relation_class": "projects",
            "relation_domain": "repository_dependency",
            "trigger_dimensions": ["governance"],
            "trigger_classifications": ["GOVERNANCE_CHANGE"],
            "propagation_mode": "automatic",
            "required_evaluation": True,
            "creates_sync_obligation": False,
            "map_visible": False,
            "label": "negative control: another domain's global triggers must not leak into R",
            "declaration_source": "test fixture only",
            "claim_ceiling": "negative fixture",
            "residue": [],
        })
        result = self.plan(["scripts/external-research/openalex_client.py"], topology=topology)
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["domains"], ["R"])
        self.assertNotIn("human_knowledge_surfaces", result["affected_component_closure"])
        excluded = {item["relation_id"]: item for item in result["excluded_relations_by_effect"]}
        self.assertEqual(excluded["unrelated_governance_edge_from_r_fixture"]["missing_dimensions"], ["governance"])
        self.assertEqual(excluded["unrelated_governance_edge_from_r_fixture"]["missing_classifications"], ["GOVERNANCE_CHANGE"])

    def test_missing_target_assignment_blocks(self):
        validation_map = copy.deepcopy(self.validation_map)
        slot = next(x for x in validation_map["components"] if x["component_id"] == "research_workflow_slot")
        slot["validation_targets"] = []
        with self.assertRaisesRegex(RoutingBlocked, "lacks validation targets"):
            self.plan(["research_workflow/slot.py"], validation_map=validation_map)

    def test_missing_selected_target_files_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RoutingBlocked, "missing module files"):
                self.plan(
                    ["scripts/external-research/openalex_client.py"],
                    verify_target_files=True,
                    repo_root=Path(temporary),
                )

    def test_declared_roots_resolve_G_and_R_modules_from_the_checkout(self):
        checkout = ROOT.parent
        self.assertEqual(
            _module_file(checkout, "tests.test_component_validation_routing", ["ignition"]),
            checkout / "ignition/tests/test_component_validation_routing.py",
        )
        with tempfile.TemporaryDirectory() as temporary:
            research_checkout = Path(temporary)
            package = research_checkout / "research_workflow"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            research_test = package / "test_research_workflow.py"
            research_test.write_text("import unittest\n", encoding="utf-8")
            self.assertEqual(
                _module_file(research_checkout, "research_workflow.test_research_workflow", ["research_workflow"]),
                research_test.resolve(),
            )

    def test_duplicate_module_locations_block_instead_of_shadowing(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary)
            for relative in ["tests/test_consumer.py", "ignition/tests/test_consumer.py"]:
                target = checkout / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("import unittest\n", encoding="utf-8")
            with self.assertRaisesRegex(RoutingBlocked, "multiple checkout files"):
                _module_file(checkout, "tests.test_consumer", ["ignition"])

    def test_module_leaf_symlink_blocks_before_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            checkout = parent / "checkout"
            checkout.mkdir()
            outside = parent / "outside.py"
            outside.write_text("raise RuntimeError('outside module executed')\n", encoding="utf-8")
            package = checkout / "research_workflow"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "test_consumer.py").symlink_to(outside)
            with self.assertRaisesRegex(RoutingBlocked, "traverses a symlink"):
                _module_file(checkout, "research_workflow.test_consumer")

    def test_parent_package_symlink_blocks_before_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            checkout = parent / "checkout"
            checkout.mkdir()
            outside = parent / "outside_tests"
            outside.mkdir()
            (outside / "test_consumer.py").write_text("import unittest\n", encoding="utf-8")
            (checkout / "tests").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RoutingBlocked, "traverses a symlink"):
                _module_file(checkout, "tests.test_consumer")

    def test_ignored_untracked_module_is_not_authorized_by_exact_HEAD(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary)

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(checkout), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git("init", "-q")
            git("config", "user.name", "Validation Fixture")
            git("config", "user.email", "fixture@example.invalid")
            (checkout / ".gitignore").write_text("ignition/tests/ghost.py\n", encoding="utf-8")
            tracked = checkout / "ignition/tests"
            tracked.mkdir(parents=True)
            (tracked / "present.py").write_text("import unittest\n", encoding="utf-8")
            git("add", ".gitignore", "ignition/tests/present.py")
            git("commit", "-m", "fixture tree")
            head = git("rev-parse", "HEAD")
            ghost = tracked / "ghost.py"
            ghost.write_text("raise RuntimeError('ignored module executed')\n", encoding="utf-8")
            self.assertEqual(git("status", "--porcelain", "--untracked-files=all"), "")
            with self.assertRaisesRegex(RoutingBlocked, "not one regular file in validation commit"):
                _module_file(checkout, "tests.ghost", ["ignition"], validation_sha=head)

    def test_registered_command_symlink_blocks_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            checkout = parent / "checkout"
            script_parent = checkout / "ignition/tools/governance"
            script_parent.mkdir(parents=True)
            marker = parent / "external-command-ran"
            outside = parent / "command.py"
            outside.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n", encoding="utf-8")
            (script_parent / "run_self_correction.py").symlink_to(outside)
            with self.assertRaisesRegex(RoutingBlocked, "traverses a symlink"):
                run_commands(["run_self_correction_check"], repo_root=checkout)
            self.assertFalse(marker.exists())

    def test_noncanonical_wildcard_path_is_not_silently_matched(self):
        with self.assertRaisesRegex(RoutingBlocked, "unmapped_path"):
            self.plan(["research_workflow_extra/slot.py"])

    def test_skip_fails_the_target_run(self):
        class SkippedCase(unittest.TestCase):
            @unittest.skip("negative control")
            def test_skipped(self):
                pass

        result = _run_suite(
            unittest.defaultTestLoader.loadTestsFromTestCase(SkippedCase),
            ["fixture.SkippedCase"],
            stream=io.StringIO(),
        )
        self.assertEqual(result["tests_run"], 1)
        self.assertEqual(result["tests_executed"], 0)
        self.assertEqual(result["skipped"], 1)
        self.assertFalse(result["successful"])
        self.assertEqual(result["skip_evidence"][0]["reason"], "negative control")
        self.assertEqual(result["status"], "NO_EXECUTED_TESTS")

    def test_recorded_skip_keeps_target_incomplete_despite_other_passing_tests(self):
        class MixedCase(unittest.TestCase):
            @unittest.skip("platform condition is not present")
            def test_platform_condition(self):
                pass

            def test_executed_control(self):
                self.assertTrue(True)

        result = _run_suite(
            unittest.defaultTestLoader.loadTestsFromTestCase(MixedCase),
            ["fixture.MixedCase"],
            stream=io.StringIO(),
        )
        self.assertEqual(result["tests_run"], 2)
        self.assertEqual(result["tests_executed"], 1)
        self.assertEqual(result["skipped"], 1)
        self.assertFalse(result["successful"])
        self.assertEqual(result["status"], "INCOMPLETE_WITH_RECORDED_SKIPS")

    def test_expected_failure_does_not_count_as_component_validation_pass(self):
        class ExpectedFailureCase(unittest.TestCase):
            @unittest.expectedFailure
            def test_known_failure(self):
                self.fail("negative control")

            def test_passing_control(self):
                self.assertTrue(True)

        result = _run_suite(
            unittest.defaultTestLoader.loadTestsFromTestCase(ExpectedFailureCase),
            ["fixture.ExpectedFailureCase"],
            stream=io.StringIO(),
        )
        self.assertEqual(len(result["expected_failures"]), 1)
        self.assertTrue(result["expected_failures"][0].endswith("ExpectedFailureCase.test_known_failure"))
        self.assertFalse(result["successful"])
        self.assertEqual(result["status"], "INCOMPLETE_WITH_EXPECTED_FAILURES")

    def test_legacy_script_style_import_root_loads_research_consumer_modules(self):
        with tempfile.TemporaryDirectory() as temp:
            repo_root = Path(temp)
            package = repo_root / "research_workflow"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "cli.py").write_text("VALUE = 41\n", encoding="utf-8")
            consumer_source = "\n".join([
                "import cli",
                "import unittest",
                "class ConsumerTest(unittest.TestCase):",
                "    def test_script_style_import(self):",
                "        self.assertEqual(cli.VALUE, 41)",
                "",
            ])
            (package / "test_consumer.py").write_text(consumer_source, encoding="utf-8")
            previous_package = sys.modules.get("research_workflow")
            stale_package = ModuleType("research_workflow")
            stale_package.__path__ = []
            sys.modules["research_workflow"] = stale_package
            try:
                result = run_modules(
                    ["research_workflow.test_consumer"],
                    repo_root=repo_root,
                    import_roots=["research_workflow"],
                    verbosity=0,
                )
                self.assertIs(sys.modules.get("research_workflow"), stale_package)
            finally:
                if previous_package is None:
                    sys.modules.pop("research_workflow", None)
                else:
                    sys.modules["research_workflow"] = previous_package
        self.assertEqual(result["tests_executed"], 1)
        self.assertEqual(result["failures"], 0)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertTrue(result["successful"])

    def test_nested_ignition_import_roots_load_pr259_consumer_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            repo_root = Path(temp)
            package = repo_root / "ignition/research_workflow"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "cli.py").write_text("VALUE = 43\n", encoding="utf-8")
            consumer_source = "\n".join([
                "import cli",
                "import unittest",
                "class ConsumerTest(unittest.TestCase):",
                "    def test_script_style_import(self):",
                "        self.assertEqual(cli.VALUE, 43)",
                "",
            ])
            (package / "test_nested_consumer.py").write_text(consumer_source, encoding="utf-8")
            for module_name in [
                name for name in sys.modules
                if name == "cli" or name == "research_workflow" or name.startswith("research_workflow.")
            ]:
                sys.modules.pop(module_name, None)
            result = run_modules(
                ["research_workflow.test_nested_consumer"],
                repo_root=repo_root,
                import_roots=["ignition", "ignition/research_workflow"],
                verbosity=0,
            )
        self.assertEqual(result["tests_executed"], 1)
        self.assertEqual(result["failures"], 0)
        self.assertEqual(result["errors"], 0)
        self.assertTrue(result["successful"])

    def test_declared_import_roots_precede_repository_root_for_indirect_imports(self):
        with tempfile.TemporaryDirectory() as temp:
            repo_root = Path(temp)
            ignition_tools = repo_root / "ignition/tools"
            root_tools = repo_root / "tools"
            test_dir = repo_root / "ignition/tests"
            ignition_tools.mkdir(parents=True)
            root_tools.mkdir(parents=True)
            test_dir.mkdir(parents=True)
            (ignition_tools / "__init__.py").write_text("", encoding="utf-8")
            (root_tools / "__init__.py").write_text("", encoding="utf-8")
            (ignition_tools / "probe.py").write_text("VALUE = 'declared-root'\n", encoding="utf-8")
            (root_tools / "probe.py").write_text("VALUE = 'repository-root'\n", encoding="utf-8")
            (test_dir / "test_indirect_import.py").write_text(
                "import unittest\n"
                "from tools.probe import VALUE\n"
                "class ImportRootTest(unittest.TestCase):\n"
                "    def test_declared_root_wins(self):\n"
                "        self.assertEqual(VALUE, 'declared-root')\n",
                encoding="utf-8",
            )
            prefixes = ("ignition", "tools")
            previous_modules = {
                name: module for name, module in sys.modules.items()
                if any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)
            }
            for name in previous_modules:
                sys.modules.pop(name, None)
            try:
                test_ids = collect_registered_test_ids(
                    ["ignition.tests.test_indirect_import"],
                    repo_root=repo_root,
                    import_roots=["ignition"],
                )
                for name in list(sys.modules):
                    if name == "tools" or name.startswith("tools."):
                        sys.modules.pop(name, None)
                result = run_modules(
                    ["ignition.tests.test_indirect_import"],
                    repo_root=repo_root,
                    import_roots=["ignition"],
                    verbosity=0,
                )
            finally:
                for name in list(sys.modules):
                    if any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes):
                        sys.modules.pop(name, None)
                sys.modules.update(previous_modules)
        self.assertEqual(
            test_ids,
            ["ignition.tests.test_indirect_import.ImportRootTest.test_declared_root_wins"],
        )
        self.assertEqual(result["tests_executed"], 1)
        self.assertEqual(result["failures"], 0)
        self.assertEqual(result["errors"], 0)
        self.assertTrue(result["successful"])

    def test_plan_hash_tampering_blocks_target_execution(self):
        plan = self.plan(["data/governance/history-remediation-register.json"])
        plan["selected_target_ids"] = []
        with self.assertRaisesRegex(RoutingBlocked, "plan hash"):
            run_plan(plan)

    def test_target_runner_requires_exact_source_commits_even_with_rehashed_plan(self):
        import hashlib

        plan = self.plan(["data/governance/history-remediation-register.json"])
        plan["source"] = {"base_sha": "0" * 40, "head_sha": "1" * 40, "validation_sha": "1" * 40}
        unhashed = dict(plan)
        unhashed.pop("plan_sha256", None)
        plan["plan_sha256"] = hashlib.sha256(
            json.dumps(unhashed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        with self.assertRaisesRegex(RoutingBlocked, "rev-parse --verify failed|does not resolve|exact Git"):
            run_plan(plan)

    def test_checkout_binding_accepts_exact_pr_merge_and_rejects_wrong_parent_or_dirty_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git("init", "-q")
            git("config", "user.name", "Validation Fixture")
            git("config", "user.email", "fixture@example.invalid")
            (repo / "state.txt").write_text("base\n", encoding="utf-8")
            git("add", "state.txt")
            git("commit", "-m", "base")
            base = git("rev-parse", "HEAD")
            default_branch = git("branch", "--show-current")
            git("checkout", "-b", "candidate")
            (repo / "state.txt").write_text("candidate\n", encoding="utf-8")
            git("commit", "-am", "candidate")
            head = git("rev-parse", "HEAD")
            git("checkout", "-b", "validation", default_branch)
            git("merge", "--no-ff", "--no-edit", "candidate")
            validation = git("rev-parse", "HEAD")

            self.assertEqual(_validate_checkout_binding(repo, base, head, validation), (base, head, validation))
            with self.assertRaisesRegex(RoutingBlocked, "declared base and head parents"):
                _validate_checkout_binding(repo, head, base, validation)

            (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(RoutingBlocked, "untracked changes"):
                _validate_checkout_binding(repo, base, head, validation)

    def test_exact_validation_commit_with_escaping_tracked_symlink_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "repo"
            repo.mkdir()
            outside = parent / "outside.py"
            outside.write_text("print('outside')\n", encoding="utf-8")

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git("init", "-q")
            git("config", "user.name", "Validation Fixture")
            git("config", "user.email", "fixture@example.invalid")
            (repo / "state.txt").write_text("candidate\n", encoding="utf-8")
            (repo / "escaped.py").symlink_to("../outside.py")
            git("add", "state.txt", "escaped.py")
            git("commit", "-m", "fixture with escaping symlink")
            head = git("rev-parse", "HEAD")
            with self.assertRaisesRegex(RoutingBlocked, "tracked symlinks that escape"):
                _validate_checkout_binding(repo, head, head, head)

    def test_map_target_must_exist_and_match_component_domain(self):
        broken_map = copy.deepcopy(self.validation_map)
        target = next(x for x in broken_map["targets"] if x["target_id"] == "g_component_release_controls")
        target["domain"] = "O"
        with self.assertRaisesRegex(RoutingBlocked, "outside component"):
            validate_validation_map(self.registry, self.topology, broken_map, self.schema)


if __name__ == "__main__":
    unittest.main()
