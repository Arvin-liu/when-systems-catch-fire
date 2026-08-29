import copy
import unittest

from tools.operations.validate_ignition_interface_sync import (
    ADDITIONAL_LOCATORS,
    InterfaceSyncError,
    RECEIPT_PATH,
    REGISTRY_PATH,
    load_json,
    operation_method_surfaces,
    step11_introduction_commit,
    validate,
    validate_decision_contract,
    validate_preserved_digests,
    validate_semantics,
)


class IgnitionInterfaceSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = load_json(RECEIPT_PATH)
        cls.registry = load_json(REGISTRY_PATH)

    def test_repository_interface_sync_is_valid(self):
        report = validate()
        self.assertEqual(report["declared_surfaces"], 20)
        self.assertEqual(report["changed"], 12)
        self.assertEqual(report["no_change_with_reason"], 8)
        self.assertEqual(report["additional_surfaces"], 9)
        self.assertEqual(report["historical_rewrites"], 0)

    def test_every_registry_triggered_surface_has_exactly_one_decision(self):
        required = operation_method_surfaces(self.registry)
        actual = {item["surface_id"] for item in self.receipt["surface_decisions"]}
        self.assertEqual(actual, set(required))
        self.assertEqual(
            {item["locator"] for item in self.receipt["additional_surface_decisions"]},
            ADDITIONAL_LOCATORS,
        )

    def test_missing_registry_surface_fails_closed(self):
        broken = copy.deepcopy(self.receipt)
        broken["surface_decisions"].pop()
        with self.assertRaisesRegex(InterfaceSyncError, "SURFACE_DECISION_SET_MISMATCH"):
            validate_decision_contract(broken, self.registry)

    def test_disallowed_surface_decision_fails_closed(self):
        broken = copy.deepcopy(self.receipt)
        target = next(item for item in broken["surface_decisions"] if item["surface_id"] == "method.iteration")
        target["decision"] = "NOT_APPLICABLE"
        with self.assertRaisesRegex(InterfaceSyncError, "DECISION_NOT_ALLOWED:method.iteration"):
            validate_decision_contract(broken, self.registry)

    def test_operating_method_precedes_iteration_in_interface_semantics(self):
        validate_semantics(self.registry)
        surfaces = {item["surface_id"]: item for item in self.registry["surfaces"]}
        self.assertIn("method.operating", surfaces["method.iteration"]["derived_from"])

    def test_step11_no_change_digests_are_exact(self):
        validate_preserved_digests(
            self.receipt,
            revision=step11_introduction_commit(),
        )


if __name__ == "__main__":
    unittest.main()
