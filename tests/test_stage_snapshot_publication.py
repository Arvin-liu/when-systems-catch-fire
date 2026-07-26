import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tools.operations.stage_snapshot_contract import (
    ContractError,
    README,
    REGISTRY,
    REQUEST_SCHEMA,
    SCHEMA,
    load,
    readme_with_projection,
    render_projection,
    validate_materialized_projection,
    validate_registry,
    validate_request,
)


class StageSnapshotPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load(REGISTRY)
        cls.schema = load(SCHEMA)
        cls.request_schema = load(REQUEST_SCHEMA)

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

    def test_registry_and_standard_schema_positive_instance(self):
        errors = list(Draft202012Validator(self.schema, format_checker=FormatChecker()).iter_errors(self.base))
        self.assertEqual(errors, [])
        self.assertEqual(validate_registry(self.registry())["status"], "PASS")

    def test_standard_schema_negative_instance(self):
        registry = self.registry()
        del self.item(registry)["claim_ceiling"]
        self.assertRejected(registry, "schema failure")

    def test_request_schema_positive_and_negative_instances(self):
        request = {
            "request_version": "1.0.0", "task_id": "TASK", "result_object": "artifact",
            "source_head": "1" * 40, "evidence_entries": ["https://github.com/a/b/pull/1"],
            "lifecycle_state": "CANDIDATE", "claim_ceiling": "artifact only",
            "homepage_summary": "candidate result", "limitations_and_incomplete": ["review pending"],
            "responsibility": {"executor": "agent", "proposed_publisher": "project", "responsible_organization": "project", "founder_responsibility_inferred": False, "upstream_responsibility_inferred": False},
            "recommendation": "PUBLISH", "agent_claims_published_to_main": False,
        }
        validate_request(request)
        request["agent_claims_published_to_main"] = True
        with self.assertRaisesRegex(ContractError, "request schema failure"):
            validate_request(request)

    def test_published_snapshot_is_orthogonal_to_accepted_current_activated(self):
        registry = self.registry()
        item = self.item(registry)
        item["publication_status"] = "PUBLISHED_SNAPSHOT"
        item["source"]["snapshot_record_merged_to_main"] = True
        self.assertFalse(item["accepted"] or item["current"] or item["activated"])
        self.assertEqual(validate_registry(registry)["status"], "PASS")

    def test_publication_state_and_main_record_flag_are_bidirectionally_bound(self):
        registry = self.registry()
        self.item(registry)["source"]["snapshot_record_merged_to_main"] = True
        self.assertRejected(registry, "Main snapshot flag conflicts")
        registry = self.registry()
        self.item(registry)["publication_status"] = "HISTORICAL_SNAPSHOT"
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
        facts["Arvin-liu/when-systems-catch-fire#130"]["head"] = "b" * 40
        with self.assertRaisesRegex(ContractError, "live source HEAD drift"):
            validate_registry(registry, facts)

    def test_revision_supersession_and_withdrawal_demo(self):
        registry = self.registry(); original = self.item(registry)
        original["snapshot_id"] = "STAGE-DEMO-REVISION-001"
        original["publication_status"] = "SUPERSEDED_SNAPSHOT"
        original["source"]["snapshot_record_merged_to_main"] = True
        original["relationships"]["successors"] = ["STAGE-DEMO-REVISION-002"]
        original["relationships"]["superseded_by"] = ["STAGE-DEMO-REVISION-002"]
        successor = copy.deepcopy(original)
        successor["snapshot_id"] = "STAGE-DEMO-REVISION-002"
        successor["publication_status"] = "PUBLISHED_SNAPSHOT"
        successor["relationships"] = {"predecessors": [original["snapshot_id"]], "successors": ["STAGE-DEMO-WITHDRAWN-003"], "supersedes": [original["snapshot_id"]], "superseded_by": []}
        withdrawn = copy.deepcopy(successor)
        withdrawn["snapshot_id"] = "STAGE-DEMO-WITHDRAWN-003"
        withdrawn["publication_status"] = "WITHDRAWN_SNAPSHOT"
        withdrawn["lifecycle_state"] = "WITHDRAWN"
        withdrawn["outcome"] = "WITHDRAWN"
        withdrawn["homepage"]["summary"] = "撤回：演示阶段快照可失败关闭。"
        withdrawn["relationships"] = {"predecessors": [successor["snapshot_id"]], "successors": [], "supersedes": [], "superseded_by": []}
        registry["snapshots"] = [original, successor, withdrawn]
        self.assertEqual(validate_registry(registry)["snapshot_count"], 3)


if __name__ == "__main__":
    unittest.main()
