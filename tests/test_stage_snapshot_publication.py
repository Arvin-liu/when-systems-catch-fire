import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tools.operations.stage_snapshot_contract import (
    ACTOR_REGISTRY,
    ACTOR_SCHEMA,
    ContractError,
    README,
    REGISTRY,
    REQUEST_SCHEMA,
    SCHEMA,
    load,
    readme_with_projection,
    render_projection,
    resolve_actor,
    validate_actor_contract_sources,
    validate_actor_registry,
    validate_materialized_projection,
    validate_registry,
    validate_request,
)
from tools.operations.run_stage_snapshot_responsibility_cases import joint_case_pass, legacy_free_text_actor

ACTOR_CASES = Path(__file__).parent / "stage_snapshot_responsibility_actor_cases.json"


class StageSnapshotPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load(REGISTRY)
        cls.schema = load(SCHEMA)
        cls.request_schema = load(REQUEST_SCHEMA)
        cls.actor_cases = load(ACTOR_CASES)
        cls.actor_registry = load(ACTOR_REGISTRY)
        cls.actor_schema = load(ACTOR_SCHEMA)

    def registry(self):
        return copy.deepcopy(self.base)

    def item(self, registry):
        return registry["snapshots"][0]

    def remote_facts(self, registry):
        item = self.item(registry)
        source, evidence, att = item["source"], item["evidence"], item["remote_attestation"]
        return {
            f"{source['repository']}#{source['pull_request']}": {
                "repository": source["repository"], "pull_request": source["pull_request"],
                "state": att["source_pr_state"], "draft": att["source_pr_draft"],
                "head": source["exact_head"], "branch": source["branch"],
            },
            f"{evidence['relay_repository']}#{evidence['relay_pull_request']}": {
                "repository": evidence["relay_repository"], "pull_request": evidence["relay_pull_request"],
                "state": att["relay_pr_state"], "draft": att["relay_pr_draft"],
                "head": evidence["relay_exact_head"], "branch": "relay-receipt",
            },
        }

    def assertRejected(self, registry, pattern, remote=False):
        with self.assertRaisesRegex((ContractError, AssertionError), pattern):
            validate_registry(registry, self.remote_facts(registry) if remote else None)

    def request(self):
        person = copy.deepcopy(self.actor_cases["positive_cases"][0]["actor"])
        organization = copy.deepcopy(self.actor_cases["positive_cases"][1]["actor"])
        return {
            "request_version": "1.2.0", "task_id": "TASK", "result_object": "artifact",
            "source_head": "1" * 40, "evidence_entries": ["https://github.com/a/b/pull/1"],
            "lifecycle_state": "CANDIDATE", "claim_ceiling": "artifact only",
            "homepage_summary": "candidate result", "limitations_and_incomplete": ["review pending"],
            "responsibility": {
                "responsible_actor": person,
                "proposed_publisher_actor": organization,
                "execution_agents": [{"name": "Codex Agent", "role": "evidence collection tool", "evidence_reference": "https://github.com/a/b/pull/1"}],
                "automation_workflows": [{"name": "GitHub Actions", "role": "validation automation", "evidence_reference": "https://github.com/a/b/actions"}],
                "founder_responsibility_inferred": False,
                "upstream_responsibility_inferred": False,
            },
            "recommendation": "PUBLISH", "agent_claims_published_to_main": False,
        }

    def test_registry_and_standard_schema_positive_instance(self):
        errors = list(Draft202012Validator(self.schema, format_checker=FormatChecker()).iter_errors(self.base))
        self.assertEqual(errors, [])
        self.assertEqual(validate_registry(self.registry())["status"], "PASS")

    def test_standard_schema_negative_instance(self):
        registry = self.registry()
        del self.item(registry)["claim_ceiling"]
        self.assertRejected(registry, "schema failure")

    def test_request_schema_positive_and_negative_instances(self):
        request = self.request()
        validate_request(request)
        request["agent_claims_published_to_main"] = True
        with self.assertRaisesRegex(ContractError, "request schema failure"):
            validate_request(request)

    def test_a15a_through_a15d_standard_schema_and_runtime_negative_instances(self):
        for case in (item for item in self.actor_cases["attack_cases"] if item["id"] in {"A15a", "A15b", "A15c", "A15d"}):
            for field in ("responsible_actor", "publisher_actor"):
                with self.subTest(case_id=case["id"], surface="registry", field=field):
                    registry = self.registry()
                    self.item(registry)["responsibility"][field] = legacy_free_text_actor(case["name"])
                    errors = list(Draft202012Validator(self.schema, format_checker=FormatChecker()).iter_errors(registry))
                    self.assertTrue(errors, f"{case['id']} must fail the standard registry schema")
                    self.assertRejected(registry, "schema failure|non-accountable")
            for field in ("responsible_actor", "proposed_publisher_actor"):
                with self.subTest(case_id=case["id"], surface="request", field=field):
                    request = self.request()
                    request["responsibility"][field] = legacy_free_text_actor(case["name"])
                    errors = list(Draft202012Validator(self.request_schema, format_checker=FormatChecker()).iter_errors(request))
                    self.assertTrue(errors, f"{case['id']} must fail the standard request schema")
                    with self.assertRaisesRegex(ContractError, "schema failure|non-accountable"):
                        validate_request(request)

    def test_stable_actor_attack_set_rejected_in_every_accountable_field(self):
        for case in self.actor_cases["attack_cases"]:
            for surface, fields in (("registry", ("responsible_actor", "publisher_actor")), ("request", ("responsible_actor", "proposed_publisher_actor"))):
                for field in fields:
                    with self.subTest(case_id=case["id"], surface=surface, field=field):
                        if surface == "registry":
                            instance = self.registry()
                            self.item(instance)["responsibility"][field] = legacy_free_text_actor(case["name"])
                            errors = list(Draft202012Validator(self.schema, format_checker=FormatChecker()).iter_errors(instance))
                            self.assertTrue(errors)
                            self.assertRejected(instance, "schema failure|actor_ref")
                        else:
                            instance = self.request()
                            instance["responsibility"][field] = legacy_free_text_actor(case["name"])
                            errors = list(Draft202012Validator(self.request_schema, format_checker=FormatChecker()).iter_errors(instance))
                            self.assertTrue(errors)
                            with self.assertRaisesRegex(ContractError, "schema failure|actor_ref"):
                                validate_request(instance)

    def test_new_automation_variants_rejected_on_all_four_positions(self):
        for case in self.actor_cases["new_automation_variant_cases"]:
            for field in ("responsible_actor", "publisher_actor"):
                registry = self.registry()
                self.item(registry)["responsibility"][field] = legacy_free_text_actor(case["name"])
                self.assertRejected(registry, "schema failure|actor_ref")
            for field in ("responsible_actor", "proposed_publisher_actor"):
                request = self.request()
                request["responsibility"][field] = legacy_free_text_actor(case["name"])
                with self.assertRaisesRegex(ContractError, "schema failure|actor_ref"):
                    validate_request(request)

    def test_positive_person_and_organization_are_each_accepted(self):
        for case in self.actor_cases["positive_cases"]:
            with self.subTest(case_id=case["id"]):
                registry = self.registry()
                self.item(registry)["responsibility"]["responsible_actor"] = copy.deepcopy(case["actor"])
                self.assertEqual(validate_registry(registry)["status"], "PASS")

    def test_execution_agent_and_workflow_are_recorded_without_substituting_accountability(self):
        registry = self.registry()
        responsibility = self.item(registry)["responsibility"]
        self.assertEqual(responsibility["execution_agents"][0]["name"], "Codex agents")
        self.assertEqual(responsibility["automation_workflows"][0]["name"], "GitHub Actions")
        self.assertEqual(validate_registry(registry)["status"], "PASS")
        projection = render_projection(registry)
        final_actor_line = next(line for line in projection.splitlines() if line.startswith("**最终责任主体：**"))
        self.assertNotIn("Codex", final_actor_line)
        self.assertNotIn("GitHub Actions", final_actor_line)
        self.assertIn("技术执行记录（非最终责任）", projection)

    def test_actor_absence_placeholders_and_legacy_free_text_are_rejected(self):
        registry = self.registry()
        del self.item(registry)["responsibility"]["responsible_actor"]
        self.assertRejected(registry, "schema failure")
        registry = self.registry()
        self.item(registry)["responsibility"]["responsible_actor"] = legacy_free_text_actor("maintainer")
        self.assertRejected(registry, "schema failure|actor_ref")
        registry = self.registry()
        self.item(registry)["responsibility"]["responsible_organization"] = "Codex Agent"
        self.assertRejected(registry, "schema failure")

    def test_actor_schema_mutations_fail_closed(self):
        mutations = (
            ("missing stable ID", lambda actor: actor.pop("actor_id")),
            ("wrong type prefix", lambda actor: actor.__setitem__("actor_id", "person:wrong-kind")),
            ("non-accountable type", lambda actor: actor.__setitem__("type", "AGENT")),
            ("technical actor name", lambda actor: actor.__setitem__("official_name", "Codex Agent")),
            ("missing role", lambda actor: actor.__setitem__("role", "")),
            ("missing accountability reference", lambda actor: actor.__setitem__("accountability_reference", "")),
            ("missing governance contact", lambda actor: actor.__setitem__("human_or_governance_contact", "unknown")),
        )
        for name, mutate in mutations:
            with self.subTest(mutation=name):
                actor_registry = copy.deepcopy(self.actor_registry)
                mutate(actor_registry["actors"][1])
                with self.assertRaisesRegex(ContractError, "schema failure|stable ID|non-accountable|traceable"):
                    validate_actor_registry(actor_registry)

    def test_reviewed_organization_name_may_contain_automation_without_becoming_free_text_authority(self):
        actor_registry = copy.deepcopy(self.actor_registry)
        actor_registry["actors"][1]["official_name"] = "Acme Automation Cooperative"
        actors = validate_actor_registry(actor_registry)
        self.assertEqual(actors["org:github/arvin-liu/when-systems-catch-fire"]["official_name"], "Acme Automation Cooperative")

    def test_actor_ref_is_positive_registry_identity_not_free_text(self):
        registry = self.registry()
        actor_ref = self.item(registry)["responsibility"]["responsible_actor"]
        actor = resolve_actor(actor_ref, "test")
        self.assertEqual(actor["type"], "ORGANIZATION")
        self.assertEqual(actor["official_name"], "Arvin-liu/when-systems-catch-fire project governance")
        actor_ref["name"] = "attacker-controlled display override"
        self.assertRejected(registry, "schema failure|only actor_ref")

    def test_nonexistent_removed_and_retired_actor_refs_fail_closed(self):
        registry = self.registry()
        self.item(registry)["responsibility"]["responsible_actor"]["actor_ref"] = "org:missing/actor"
        self.assertRejected(registry, "schema failure|does not resolve")

        actor_registry = copy.deepcopy(self.actor_registry)
        actor_registry["actors"].pop()
        with self.assertRaisesRegex(ContractError, "actor registry schema failure|actor_ref set drift"):
            validate_registry(self.registry(), actor_registry=actor_registry)

        actor_registry = copy.deepcopy(self.actor_registry)
        actor = actor_registry["actors"][1]
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
        with self.assertRaisesRegex(ContractError, "actor_ref set drift|retired"):
            validate_registry(self.registry(), actor_registry=actor_registry)

    def test_schema_runtime_actor_sets_and_generated_enums_cannot_drift(self):
        self.assertEqual(validate_actor_contract_sources()["status"], "PASS")
        request_schema = copy.deepcopy(self.request_schema)
        request_schema["$defs"]["accountableActorRef"]["properties"]["actor_ref"]["enum"].pop()
        with self.assertRaisesRegex(ContractError, "request schema actor_ref set drift|different actor_ref sets"):
            validate_actor_contract_sources(request_schema=request_schema)
        registry_schema = copy.deepcopy(self.schema)
        registry_schema["$defs"]["accountableActorRef"]["properties"]["actor_ref"]["enum"].append("org:stale/generated-entry")
        with self.assertRaisesRegex(ContractError, "registry schema actor_ref set drift"):
            validate_actor_contract_sources(registry_schema=registry_schema)

    def test_runner_joint_verdict_cannot_ignore_either_surface(self):
        self.assertTrue(joint_case_pass("REJECT", "REJECT", "REJECT"))
        self.assertFalse(joint_case_pass("REJECT", "ACCEPT", "REJECT"))
        self.assertFalse(joint_case_pass("REJECT", "REJECT", "ACCEPT"))
        self.assertTrue(joint_case_pass("ACCEPT", "ACCEPT", "ACCEPT"))
        self.assertFalse(joint_case_pass("ACCEPT", "REJECT", "ACCEPT"))
        self.assertFalse(joint_case_pass("ACCEPT", "ACCEPT", "REJECT"))

    def test_published_snapshot_is_orthogonal_to_accepted_current_activated(self):
        registry = self.registry()
        item = self.item(registry)
        item["publication_status"] = "PUBLISHED_SNAPSHOT"
        item["source"]["snapshot_record_merged_to_main"] = True
        self.assertFalse(item["accepted"] or item["current"] or item["activated"])
        self.assertEqual(validate_registry(registry)["status"], "PASS")

    def test_publication_state_and_main_record_flag_are_bidirectionally_bound(self):
        # The line-318 invariant: snapshot_record_merged_to_main must equal whether
        # publication_status is a Main snapshot state. Test BOTH directions of the
        # binding so the case stays valid regardless of the base registry's own state.
        # A snapshot record merged to Main is rejected for a non-Main publication status.
        registry = self.registry()
        item = self.item(registry)
        item["publication_status"] = "PR_VISIBLE"  # not a Main publication state
        item["source"]["snapshot_record_merged_to_main"] = True
        self.assertRejected(registry, "Main snapshot flag conflicts")
        # A Main publication status is rejected unless its snapshot record is merged to Main.
        registry = self.registry()
        item = self.item(registry)
        item["publication_status"] = "HISTORICAL_SNAPSHOT"  # a Main publication state
        item["source"]["snapshot_record_merged_to_main"] = False
        self.assertRejected(registry, "Main snapshot flag conflicts")

    def test_attack_false_current(self):
        registry = self.registry(); self.item(registry)["current"] = True
        self.assertRejected(registry, "Current cannot be true|inflated boolean")

    def test_attack_false_accepted(self):
        registry = self.registry(); self.item(registry)["accepted"] = True
        self.assertRejected(registry, "inflated boolean")

    def test_attack_source_head_drift(self):
        registry = self.registry(); self.item(registry)["source"]["exact_head"] = "a" * 40
        self.assertRejected(registry, "source HEAD drift")

    def test_attack_pr_missing_or_source_mismatch(self):
        registry = self.registry()
        facts = self.remote_facts(registry)
        facts.clear()
        with self.assertRaisesRegex(ContractError, "source PR does not exist"):
            validate_registry(registry, facts)
        registry = self.registry(); self.item(registry)["source"]["pull_request_url"] = "https://github.com/other/repo/pull/130"
        self.assertRejected(registry, "source PR URL/repository mismatch")

    def test_attack_1111_receipt_missing(self):
        registry = self.registry(); item = self.item(registry)
        item["evidence"]["entries"].remove(item["evidence"]["relay_pull_request_url"])
        self.assertRejected(registry, "1111 receipt entry missing")

    def test_attack_duplicate_snapshot_id(self):
        registry = self.registry(); registry["snapshots"].append(copy.deepcopy(self.item(registry)))
        self.assertRejected(registry, "duplicate snapshot ID")

    def test_attack_deleted_limitations_and_blockers(self):
        registry = self.registry(); self.item(registry)["known_limitations_and_blockers"] = []
        self.assertRejected(registry, "schema failure")

    def test_attack_candidate_registered_as_formal_capability(self):
        registry = self.registry(); self.item(registry)["affects_formal_capability"] = True
        self.assertRejected(registry, "formal capability|homepage visibility")

    def test_attack_privacy_or_secret_leak(self):
        registry = self.registry(); self.item(registry)["summary"] += " token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        self.assertRejected(registry, "secret-like")
        registry = self.registry(); self.item(registry)["summary"] += " /Users/private/raw.txt"
        self.assertRejected(registry, "private path")

    def test_attack_rejected_result_disguised_as_success(self):
        registry = self.registry(); item = self.item(registry)
        item["lifecycle_state"] = "REJECTED"; item["outcome"] = "REJECTED"
        item["homepage"]["summary"] = "All work succeeded"
        self.assertRejected(registry, "disguised as success")
        registry = self.registry(); item = self.item(registry)
        item["lifecycle_state"] = "REJECTED"; item["outcome"] = "SUCCESS"
        self.assertRejected(registry, "rejected lifecycle is disguised")

    def test_attack_homepage_semantically_claims_false_lifecycle_flags(self):
        for flag, claim in (
            ("current", "R5-A is Current"),
            ("accepted", "R5-A Accepted=true"),
            ("activated", "R5-A 已经激活"),
        ):
            registry = self.registry()
            self.item(registry)["homepage"]["summary"] = claim
            self.assertFalse(self.item(registry)[flag])
            self.assertRejected(registry, f"homepage falsely claims {flag}")

    def test_attack_homepage_text_diverges_from_registry(self):
        registry = self.registry()
        projection = render_projection(registry)
        readme = readme_with_projection(README.read_text(encoding="utf-8"), projection)
        projection_doc = "# Recent Stage Results / 正在炼化\n\n" + projection.split("\n", 2)[2]
        mutated = self.registry(); self.item(mutated)["homepage"]["summary"] = "drifted public text"
        with self.assertRaisesRegex(ContractError, "projection is stale"):
            validate_materialized_projection(mutated, readme, projection_doc)

    def test_attack_successor_omits_supersession_relation(self):
        registry = self.registry(); item = self.item(registry)
        item["publication_status"] = "SUPERSEDED_SNAPSHOT"
        item["source"]["snapshot_record_merged_to_main"] = True
        self.assertRejected(registry, "lacks successor relation")

    def test_attack_responsibility_shift_to_founder_or_upstream(self):
        for field in ("founder_responsibility_inferred", "upstream_responsibility_inferred"):
            registry = self.registry(); self.item(registry)["responsibility"][field] = True
            self.assertRejected(registry, "schema failure")

    def test_remote_identity_and_exact_head_binding(self):
        registry = self.registry()
        self.assertTrue(validate_registry(registry, self.remote_facts(registry))["remote_verified"])
        facts = self.remote_facts(registry)
        # Use the ACTUAL source PR key from the registry (no hard-coded PR number),
        # so the test tracks the live source PR across controlled syncs.
        source = self.item(registry)["source"]
        facts[f"{source['repository']}#{source['pull_request']}"]["head"] = "b" * 40
        with self.assertRaisesRegex(ContractError, "live source HEAD drift"):
            validate_registry(registry, facts)

    def test_revision_supersession_and_withdrawal_demo(self):
        registry = self.registry(); original = self.item(registry)
        original["snapshot_id"] = "STAGE-DEMO-REVISION-001"
        original["publication_status"] = "SUPERSEDED_SNAPSHOT"
        original["source"]["snapshot_record_merged_to_main"] = True
        original["relationships"]["successors"] = ["STAGE-DEMO-REVISION-002"]
        original["relationships"]["superseded_by"] = ["STAGE-DEMO-REVISION-002"]
        original["responsibility"]["responsibility_record"]["record_id"] = "RESP-DEMO-REVISION-001"
        successor = copy.deepcopy(original)
        successor["snapshot_id"] = "STAGE-DEMO-REVISION-002"
        successor["publication_status"] = "PUBLISHED_SNAPSHOT"
        successor["relationships"] = {"predecessors": [original["snapshot_id"]], "successors": ["STAGE-DEMO-WITHDRAWN-003"], "supersedes": [original["snapshot_id"]], "superseded_by": []}
        successor["responsibility"]["responsibility_record"]["record_id"] = "RESP-DEMO-REVISION-002"
        withdrawn = copy.deepcopy(successor)
        withdrawn["snapshot_id"] = "STAGE-DEMO-WITHDRAWN-003"
        withdrawn["publication_status"] = "WITHDRAWN_SNAPSHOT"
        withdrawn["lifecycle_state"] = "WITHDRAWN"
        withdrawn["outcome"] = "WITHDRAWN"
        withdrawn["homepage"]["summary"] = "撤回：演示阶段快照可失败关闭。"
        withdrawn["relationships"] = {"predecessors": [successor["snapshot_id"]], "successors": [], "supersedes": [], "superseded_by": []}
        withdrawn["responsibility"]["responsibility_record"]["record_id"] = "RESP-DEMO-WITHDRAWN-003"
        registry["snapshots"] = [original, successor, withdrawn]
        self.assertEqual(validate_registry(registry)["snapshot_count"], 3)

    def test_accountable_actor_change_requires_new_snapshot_revision_and_record(self):
        registry = self.registry()
        original = self.item(registry)
        original["snapshot_id"] = "STAGE-ACTOR-REVISION-001"
        original["relationships"]["successors"] = ["STAGE-ACTOR-REVISION-002"]
        successor = copy.deepcopy(original)
        successor["snapshot_id"] = "STAGE-ACTOR-REVISION-002"
        successor["relationships"] = {"predecessors": [original["snapshot_id"]], "successors": [], "supersedes": [], "superseded_by": []}
        successor["responsibility"]["responsible_actor"] = copy.deepcopy(self.actor_cases["positive_cases"][0]["actor"])
        successor["responsibility"]["responsibility_record"]["record_id"] = "RESP-ACTOR-REVISION-002"
        successor["responsibility"]["responsibility_record"]["supersedes_record_id"] = None
        registry["snapshots"] = [original, successor]
        self.assertRejected(registry, "changed without a new superseding responsibility record")
        successor["responsibility"]["responsibility_record"]["supersedes_record_id"] = original["responsibility"]["responsibility_record"]["record_id"]
        successor["responsibility"]["responsibility_record"]["change_reason"] = "Accountable actor changed in a new snapshot revision."
        self.assertEqual(validate_registry(registry)["snapshot_count"], 2)


if __name__ == "__main__":
    unittest.main()
