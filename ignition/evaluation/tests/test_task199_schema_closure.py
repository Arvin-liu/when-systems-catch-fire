from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

IGNITION_ROOT = Path(__file__).resolve().parents[2]
PACKET_ROOT = IGNITION_ROOT / "reports/evaluations/ignition-198-replicated-method-use-trial-r0"
sys.path.insert(0, str(PACKET_ROOT / "tools"))

import validate_step04_packets as packet_validator  # noqa: E402


class Task199SchemaClosureTests(unittest.TestCase):
    def test_all_frozen_packets_have_one_allowlisted_output_schema(self) -> None:
        for packet_name, spec in packet_validator.PACKET_SPECS.items():
            manifest = json.loads(
                (PACKET_ROOT / "packets" / packet_name / "packet-manifest.json").read_text(encoding="utf-8")
            )
            packet_validator.validate_packet_manifest(packet_name, spec, manifest)

    def test_deleting_actual_schema_row_is_rejected(self) -> None:
        packet_name = "facts-a"
        spec = packet_validator.PACKET_SPECS[packet_name]
        manifest = json.loads(
            (PACKET_ROOT / "packets" / packet_name / "packet-manifest.json").read_text(encoding="utf-8")
        )
        manifest["read_allowlist"] = [
            row
            for row in manifest["read_allowlist"]
            if row["path"] != packet_validator.OUTPUT_SCHEMA_PATH
        ]
        with self.assertRaises(AssertionError):
            packet_validator.validate_packet_manifest(packet_name, spec, manifest)

    def test_command_extra_input_cannot_substitute_for_missing_schema_row(self) -> None:
        packet_name = "facts-a"
        spec = packet_validator.PACKET_SPECS[packet_name]
        manifest = json.loads(
            (PACKET_ROOT / "packets" / packet_name / "packet-manifest.json").read_text(encoding="utf-8")
        )
        manifest["read_allowlist"] = [
            row
            for row in manifest["read_allowlist"]
            if row["path"] != packet_validator.OUTPUT_SCHEMA_PATH
        ]
        manifest["read_allowlist"].append(
            {
                "path": "agent-commands/experimental-schema-content.json",
                "sha256": "0" * 64,
                "role": "command",
            }
        )
        with self.assertRaises(AssertionError):
            packet_validator.validate_packet_manifest(packet_name, spec, manifest)

    def test_future_manifest_declares_control_metadata_boundary(self) -> None:
        manifest = json.loads(
            (PACKET_ROOT / "future-task-manifest.json").read_text(encoding="utf-8")
        )
        control = manifest["shared_contracts"]["packet_manifest_control_metadata"]
        self.assertEqual(control["read_class"], "CONTROL_METADATA")
        self.assertEqual(
            control["cognitive_input_reads"],
            "ONLY_FROM_VERIFIED_PACKET_READ_ALLOWLIST",
        )
        self.assertEqual(
            control["command_level_extra_input"],
            "PROHIBITED_AND_NOT_A_SUBSTITUTE_FOR_MISSING_PACKET_INPUT",
        )
        self.assertEqual(control["experimental_content_outside_packet"], "PROHIBITED")


if __name__ == "__main__":
    unittest.main()
