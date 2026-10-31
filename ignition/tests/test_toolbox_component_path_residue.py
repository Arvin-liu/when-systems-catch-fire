from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.toolbox_component_path_residue import (
    MAX_PATHS,
    InputError,
    summarize_residue,
)


class ComponentPathResidueTests(unittest.TestCase):
    def summarize(self, paths: list[str]) -> dict:
        raw = json.dumps(
            {
                "schema_version": "component-path-residue-input-r0",
                "residues": [
                    {"type": "unmapped_path", "path": path,
                     "message": "Changed path has no canonical component mapping."}
                    for path in paths
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return summarize_residue(
            json.loads(raw),
            input_bytes=raw,
            source_bytes=b"fixed-tool-source-for-unit-test",
        )

    def test_groups_directory_and_repeated_tool_filename_prefixes(self) -> None:
        result = self.summarize([
            "tools/toolbox_demo_sampler.py",
            "tests/test_toolbox_demo_sampler.py",
            "data/operations/toolbox-demo-sampler-route-evidence-r0.json",
            "data/operations/toolbox-demo-sampler-c1-evidence-r0.json",
            "docs/operations/toolbox-demo-sampler.md",
            "TOOLBOX.md",
        ])
        self.assertEqual(result["summary"]["path_count"], 6)
        self.assertEqual(result["summary"]["directory_group_count"], 5)
        self.assertEqual(result["summary"]["repeated_filename_family_count"], 1)
        self.assertEqual(result["summary"]["paths_in_repeated_filename_families"], 5)
        self.assertEqual(
            result["repeated_filename_families"][0]["family_prefix"],
            "toolbox-demo-sampler",
        )
        self.assertEqual(result["mapping_authority"]["component_ids_suggested"], [])
        self.assertTrue(result["mapping_authority"]["human_mapping_decision_required"])

    def test_unrelated_names_do_not_form_a_generic_toolbox_cohort(self) -> None:
        result = self.summarize([
            "data/operations/toolbox-alpha-route-evidence-r0.json",
            "data/operations/toolbox-beta-route-evidence-r0.json",
            "data/operations/toolbox-gamma-route-evidence-r0.json",
        ])
        self.assertEqual(result["repeated_filename_families"], [])
        self.assertEqual(result["summary"]["uncohorted_path_count"], 3)

    def test_input_digest_binds_exact_supplied_bytes(self) -> None:
        raw = b'{"schema_version":"component-path-residue-input-r0","residues":[{"path":"x/a.txt","type":"unmapped_path"}]}'
        result = summarize_residue(
            json.loads(raw),
            input_bytes=raw,
            source_bytes=b"source",
        )
        self.assertEqual(result["input_sha256"], hashlib.sha256(raw).hexdigest())

    def test_only_unmapped_path_rows_are_accepted(self) -> None:
        envelope = {
            "schema_version": "component-path-residue-input-r0",
            "residues": [{"type": "ambiguous_path_mapping", "path": "x/a.py"}],
        }
        with self.assertRaisesRegex(InputError, "only unmapped_path"):
            summarize_residue(envelope, input_bytes=b"{}", source_bytes=b"")

    def test_duplicate_paths_are_rejected(self) -> None:
        with self.assertRaisesRegex(InputError, "duplicate residue path"):
            self.summarize(["tools/a.py", "tools/a.py"])

    def test_parent_traversal_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputError, "normalized"):
            self.summarize(["tools/../secret.txt"])

    def test_absolute_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputError, "repository-relative"):
            self.summarize(["/etc/passwd"])

    def test_backslash_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputError, "repository-relative"):
            self.summarize(["tools\\script.py"])

    def test_empty_or_oversized_path_list_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputError, "1 to 5000"):
            summarize_residue(
                {"schema_version": "component-path-residue-input-r0", "residues": []},
                input_bytes=b"{}",
                source_bytes=b"",
            )
        too_many = [
            {"type": "unmapped_path", "path": f"files/{i:05}.txt"}
            for i in range(MAX_PATHS + 1)
        ]
        with self.assertRaisesRegex(InputError, "1 to 5000"):
            summarize_residue(
                {"schema_version": "component-path-residue-input-r0", "residues": too_many},
                input_bytes=b"{}",
                source_bytes=b"",
            )

    def test_noncanonical_empty_segments_are_rejected(self) -> None:
        with self.assertRaisesRegex(InputError, "normalized"):
            self.summarize(["tools//script.py"])

    def test_family_suffixes_are_conservative(self) -> None:
        result = self.summarize([
            "tools/toolbox_actions_step_timeline.py",
            "data/operations/toolbox-actions-step-timeline-route-evidence-r0.json",
            "docs/operations/toolbox-actions-step-timeline.md",
        ])
        self.assertEqual(result["repeated_filename_families"][0]["family_prefix"],
                         "toolbox-actions-step-timeline")

    def test_exact_formal_residue_task_is_schema_valid_and_replayable(self) -> None:
        ignition_root = Path(__file__).resolve().parents[1]
        input_path = ignition_root / "data/operations/toolbox-component-path-residue-real-task-input-r0.json"
        output_path = ignition_root / "data/operations/toolbox-component-path-residue-real-task-output-r0.json"
        input_schema_path = ignition_root / "schemas/operations/toolbox-component-path-residue-input-r0.schema.json"
        output_schema_path = ignition_root / "schemas/operations/toolbox-component-path-residue-output-r0.schema.json"
        source_path = ignition_root / "tools/toolbox_component_path_residue.py"

        raw = input_path.read_bytes()
        envelope = json.loads(raw)
        output = json.loads(output_path.read_text(encoding="utf-8"))
        result = summarize_residue(envelope, input_bytes=raw, source_bytes=source_path.read_bytes())
        input_schema = json.loads(input_schema_path.read_text(encoding="utf-8"))
        output_schema = json.loads(output_schema_path.read_text(encoding="utf-8"))

        self.assertEqual(list(Draft202012Validator(input_schema).iter_errors(envelope)), [])
        self.assertEqual(list(Draft202012Validator(output_schema).iter_errors(output)), [])
        self.assertEqual(result, output)
        self.assertEqual(output["summary"]["path_count"], 235)
        self.assertEqual(output["summary"]["directory_group_count"], 9)
        self.assertEqual(output["summary"]["repeated_filename_family_count"], 44)
        self.assertEqual(output["summary"]["paths_in_repeated_filename_families"], 164)
        self.assertEqual(output["summary"]["uncohorted_path_count"], 71)
        self.assertEqual(output["mapping_authority"]["component_ids_suggested"], [])
        self.assertEqual(output["mapping_authority"]["path_patterns_suggested"], [])
        self.assertFalse(output["mapping_authority"]["canonical_registry_modified"])


if __name__ == "__main__":
    unittest.main()
