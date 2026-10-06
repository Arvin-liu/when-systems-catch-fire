from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from egress_broker import EgressBroker
from sandbox_profile import render_profile, verify_profile, verify_profile_against_broker


class SandboxProfileTests(unittest.TestCase):
    def test_profile_is_single_loopback_port(self) -> None:
        self.assertEqual(
            render_profile(43210),
            '(version 1)\n(allow default)\n(deny network-outbound)\n'
            '(allow network-outbound (remote ip "localhost:43210"))\n',
        )

    @unittest.skipUnless(os.uname().sysname == "Darwin", "Seatbelt validation requires macOS")
    def test_kernel_profile_and_actual_deny_first_broker(self) -> None:
        work_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="profile-check-", dir=work_root) as temp:
            directory = Path(temp)
            os.chmod(directory, 0o700)
            profile = directory / "sandbox.sb"
            event_log = directory / "broker-events.jsonl"
            broker = EgressBroker(event_log=event_log)
            broker.start()
            try:
                result = verify_profile_against_broker(profile, broker.address)
            finally:
                broker.stop()

            self.assertEqual(result["returncode"], 0, result)
            self.assertTrue(result["child_result"]["approved_loopback_reached_broker"])
            self.assertTrue(result["child_result"]["broker_denied_probe_host"])
            self.assertTrue(result["child_result"]["other_loopback_denied"])
            self.assertTrue(result["child_result"]["direct_external_denied"])
            self.assertFalse(result["unapproved_loopback_listener_accepted"])
            events = [json.loads(line) for line in event_log.read_text().splitlines()]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["host"], "stage02.local-probe.invalid")
            self.assertEqual(events[0]["decision"], "blocked")
            self.assertEqual(events[0]["reason"], "not_allowlisted")
            self.assertNotIn("upstream_ip", events[0])


if __name__ == "__main__":
    unittest.main()
