from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_validation_invocation_deduplication as dedup  # noqa: E402


TREE = "1" * 40
RUNTIME = hashlib.sha256(b"runtime").hexdigest()
ENV = hashlib.sha256(b"environment").hexdigest()


def profile(profile_id: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "profile_id": profile_id,
        "argv": ["python3", "tools/validate_human_front_door.py"],
        "working_directory": ".",
        "source_tree_git_sha1": TREE,
        "runtime_fingerprint_sha256": RUNTIME,
        "environment_fingerprint_sha256": ENV,
        "result_contract_id": "exit-code-zero-only",
        "side_effect_class": "READ_ONLY_VALIDATION",
        "review_status": "SOURCE_REVIEWED_READ_ONLY",
        "evidence_ref": "review/front-door-source-r0",
    }
    row.update(overrides)
    return row


def document(profiles: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": "validation-invocation-dedup-input-r0",
        "evaluation_context": {
            "evaluation_id": "dedup-test-r0",
            "source_ref": "test-fixture",
            "analysis_purpose": "group identical read-only validation invocations",
        },
        "profiles": profiles,
    }


def run_analysis(profiles: list[dict[str, object]]) -> dict[str, object]:
    raw = json.dumps(document(profiles), sort_keys=True, separators=(",", ":")).encode()
    return dedup.analyze(raw)


class ValidationInvocationDedupTests(unittest.TestCase):
    def test_exact_read_only_profiles_form_reuse_candidate(self) -> None:
        result = run_analysis([profile("no_l7"), profile("no_truth_upgrade")])
        self.assertEqual(result["profiles_analyzed"], 2)
        self.assertEqual(result["invocation_group_count"], 1)
        self.assertEqual(result["potential_reuse_group_count"], 1)
        self.assertEqual(result["potential_duplicate_invocations"], 1)
        group = result["groups"][0]
        self.assertEqual(group["profile_ids"], ["no_l7", "no_truth_upgrade"])
        self.assertEqual(group["reuse_candidate_status"], "POTENTIAL_READ_ONLY_REUSE")
        self.assertFalse(result["non_claims"]["execution_authorized"])
        self.assertFalse(result["non_claims"]["commands_executed"])

    def test_argument_or_context_difference_splits_groups(self) -> None:
        result = run_analysis([
            profile("a"),
            profile("different-argv", argv=["python3", "tools/validate_human_front_door.py", "--strict"]),
            profile("different-env", environment_fingerprint_sha256=hashlib.sha256(b"other").hexdigest()),
            profile("different-tree", source_tree_git_sha1="2" * 40),
        ])
        self.assertEqual(result["invocation_group_count"], 4)
        self.assertEqual(result["potential_reuse_group_count"], 0)
        self.assertEqual(result["potential_duplicate_invocations"], 0)

    def test_effectful_or_unreviewed_duplicate_is_not_reusable(self) -> None:
        result = run_analysis([
            profile("a", side_effect_class="EFFECTFUL_OR_UNKNOWN"),
            profile("b", side_effect_class="EFFECTFUL_OR_UNKNOWN"),
        ])
        group = result["groups"][0]
        self.assertEqual(group["reuse_candidate_status"], "NOT_ESTABLISHED")
        self.assertIn("SIDE_EFFECT_OR_REVIEW_NOT_ESTABLISHED", group["non_eligibility_reasons"])
        self.assertEqual(result["potential_duplicate_invocations"], 0)

    def test_unreviewed_duplicate_is_not_reusable(self) -> None:
        result = run_analysis([
            profile("a", review_status="NOT_REVIEWED"),
            profile("b", review_status="NOT_REVIEWED"),
        ])
        self.assertEqual(result["groups"][0]["reuse_candidate_status"], "NOT_ESTABLISHED")

    def test_duplicate_profile_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(dedup.InvocationInputError, "duplicate profile_id"):
            run_analysis([profile("same"), profile("same")])

    def test_parent_directory_is_rejected(self) -> None:
        with self.assertRaisesRegex(dedup.InvocationInputError, "parent segments"):
            run_analysis([profile("unsafe", working_directory="../outside")])

    def test_malformed_source_tree_hash_is_rejected(self) -> None:
        with self.assertRaisesRegex(dedup.InvocationInputError, "invalid digest"):
            run_analysis([profile("bad-tree", source_tree_git_sha1="not-a-git-tree")])

    def test_input_over_limit_is_rejected_before_json_parsing(self) -> None:
        with self.assertRaisesRegex(dedup.InvocationInputError, "input exceeds"):
            dedup.analyze(b" " * (dedup.MAX_INPUT_BYTES + 1))

    def test_duplicate_json_keys_are_rejected(self) -> None:
        raw = b'{"schema_version":"validation-invocation-dedup-input-r0","schema_version":"x"}'
        with self.assertRaisesRegex(dedup.InvocationInputError, "duplicate JSON key"):
            dedup.analyze(raw)

    def test_unknown_result_contract_splits_profiles(self) -> None:
        result = run_analysis([
            profile("a"),
            profile("different-contract", result_contract_id="json-output-byte-equality"),
        ])
        self.assertEqual(result["invocation_group_count"], 2)
        self.assertEqual(result["potential_reuse_group_count"], 0)


if __name__ == "__main__":
    unittest.main()
