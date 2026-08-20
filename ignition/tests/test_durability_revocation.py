from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.revocation import CapabilityGrant, RevocationDispatcher, RevocationError, RevocationStore


class DurabilityRevocationTests(unittest.TestCase):
    def _grant(self, effect: str = "EXTERNAL_SIDE_EFFECT", expiry: float = 200.0) -> CapabilityGrant:
        return CapabilityGrant("grant-1", "principal-a", "ns-a", "repo.write", effect, expiry, "principal-owner", "a" * 64)

    def test_queued_action_is_not_started_after_revoke_and_event_replays(self) -> None:
        with tempfile.TemporaryDirectory(prefix="revocation-") as temp:
            store = RevocationStore(Path(temp) / "revocations.jsonl")
            store.register(self._grant(), occurred_at=100.0)
            dispatcher = RevocationDispatcher(store)
            admission = dispatcher.admit_future("action-1", "grant-1", now=110.0)
            self.assertEqual(admission.state, "ADMITTED_QUEUED")
            cancelled = dispatcher.revoke_in_flight(admission)
            self.assertEqual(cancelled.state, "CANCEL_BEFORE_START")
            self.assertFalse(cancelled.started)
            self.assertFalse(store.is_admissible("grant-1", now=111.0))
            self.assertEqual(store.replayed_state()["grant-1"]["status"], "REVOKED")
            self.assertEqual(len(store.events()), 2)

    def test_in_flight_effect_class_is_honest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="revocation-") as temp:
            store = RevocationStore(Path(temp) / "revocations.jsonl")
            store.register(self._grant("READ_ONLY"), occurred_at=100.0)
            read = RevocationDispatcher(store).revoke_in_flight(RevocationDispatcher(store).admit_future("action-read", "grant-1", now=110.0).__class__("action-read", "grant-1", "READ_ONLY", "ADMITTED_QUEUED", True))
            self.assertEqual(read.state, "CANCEL")
            self.assertFalse(read.external_effect_retracted)

            store2 = RevocationStore(Path(temp) / "revocations-unknown.jsonl")
            store2.register(self._grant("UNKNOWN_SIDE_EFFECT"), occurred_at=100.0)
            dispatcher = RevocationDispatcher(store2)
            in_flight = dispatcher.admit_future("action-unknown", "grant-1", now=110.0)
            in_flight = type(in_flight)(in_flight.action_id, in_flight.grant_id, in_flight.effect_class, in_flight.state, True)
            self.assertEqual(dispatcher.revoke_in_flight(in_flight).state, "DRAIN_AND_RECONCILE")

    def test_stale_lease_and_duplicate_revoke_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="revocation-") as temp:
            store = RevocationStore(Path(temp) / "revocations.jsonl")
            store.register(self._grant(expiry=10.0), occurred_at=1.0)
            self.assertEqual(RevocationDispatcher(store).admit_future("action-stale", "grant-1", now=10.0).state, "REJECTED_REVOKED_OR_EXPIRED")
            store.revoke("grant-1", occurred_at=11.0)
            with self.assertRaises(RevocationError):
                store.revoke("grant-1", occurred_at=12.0)

    def test_health_degradation_never_expands_permissions(self) -> None:
        result = RevocationDispatcher.health_degradation_decision(degraded_executor="executor-a", substitute_capabilities=("network.send",))
        self.assertEqual(result["status"], "DRAIN_ONLY")
        self.assertEqual(result["substitute_capabilities"], [])


if __name__ == "__main__":
    unittest.main()
