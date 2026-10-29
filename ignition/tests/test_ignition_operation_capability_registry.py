from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
from validate_ignition_operation_capability_registry import REGISTRY_PATH, load_json, validate  # noqa: E402


class IgnitionOperationCapabilityRegistryR1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_json(REGISTRY_PATH)

    def test_current_registry_passes(self) -> None:
        self.assertEqual(validate(copy.deepcopy(self.registry)), [])

    def test_current_lifecycle_requires_merge_and_current_flags(self) -> None:
        candidate = copy.deepcopy(self.registry)
        candidate["registry_lifecycle"]["current_on_main"] = False
        self.assertTrue(any("merged_to_main=true and current_on_main=true" in error for error in validate(candidate)))

    def test_duplicate_operation_id_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.registry)
        candidate["operations"].append(copy.deepcopy(candidate["operations"][0]))
        candidate["coverage"]["operation_count"] += 1
        self.assertTrue(any("operation ids must be unique" in error for error in validate(candidate)))

    def test_missing_pack_capability_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.registry)
        candidate["operations"] = [
            row for row in candidate["operations"]
            if row["operation_id"] != "knowledge.read_foundation"
        ]
        candidate["coverage"]["operation_count"] -= 1
        self.assertTrue(any("Pack capability coverage mismatch" in error for error in validate(candidate)))

    def test_owner_deferred_live_action_cannot_be_downgraded(self) -> None:
        candidate = copy.deepcopy(self.registry)
        live = next(row for row in candidate["operations"] if row["operation_id"] == "external.live_invocation")
        live["current_status"] = "CURRENT"
        self.assertTrue(any("external.live_invocation must remain OWNER_DEFERRED" in error for error in validate(candidate)))

    def test_read_only_operation_cannot_mutate_repository(self) -> None:
        candidate = copy.deepcopy(self.registry)
        current = next(row for row in candidate["operations"] if row["operation_id"] == "ignition.recover_current_state")
        current["repository_mutation_permission"] = "EXPLICIT_USER_OR_OWNER_AUTHORIZATION_AND_ITERATION_METHOD"
        self.assertTrue(any("READ_ONLY_RUN cannot permit repository mutation" in error for error in validate(candidate)))

    def test_missing_authoritative_source_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.registry)
        current = next(row for row in candidate["operations"] if row["operation_id"] == "ignition.recover_current_state")
        current["authoritative_sources"][0]["path"] = "ignition/data/operations/does-not-exist.json"
        self.assertTrue(any("authoritative source missing" in error for error in validate(candidate)))

    def test_object_collision_must_read_both_canonical_registries(self) -> None:
        candidate = copy.deepcopy(self.registry)
        collision = next(row for row in candidate["operations"] if row["operation_id"] == "knowledge.collide_object")
        collision["required_current_reads"].remove(
            "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
        )
        self.assertTrue(any("both Current canonical registries" in error for error in validate(candidate)))

    def test_object_collision_cannot_authorize_side_effects(self) -> None:
        candidate = copy.deepcopy(self.registry)
        collision = next(row for row in candidate["operations"] if row["operation_id"] == "knowledge.collide_object")
        collision["repository_mutation_permission"] = "EXPLICIT_USER_OR_OWNER_AUTHORIZATION_AND_ITERATION_METHOD"
        self.assertTrue(any("READ_ONLY_RUN cannot permit repository mutation" in error for error in validate(candidate)))

    def test_current_resolver_must_read_both_canonical_registries(self) -> None:
        candidate = copy.deepcopy(self.registry)
        resolver = next(
            row for row in candidate["operations"]
            if row["operation_id"] == "foundation.resolve_current_asset"
        )
        resolver["authoritative_sources"] = [
            source for source in resolver["authoritative_sources"]
            if source["path"] != "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
        ]
        resolver["required_current_reads"].remove(
            "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
        )
        errors = validate(candidate)
        self.assertTrue(any("both Current canonical registries" in error for error in errors))
        self.assertTrue(any("must read both Current canonical registries" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
