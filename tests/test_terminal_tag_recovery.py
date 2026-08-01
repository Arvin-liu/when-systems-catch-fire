#!/usr/bin/env python3
"""Adversarial fixtures for the immutable task-111 terminal-tag recovery path."""
from __future__ import annotations

import hashlib
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "propagation"))

import lifecycle_events as le  # noqa: E402
import tag_validator as tv  # noqa: E402


TASK = 111
TASK_ID = "IGNITION-FAILURE-CASE-EVIDENCE-GATE-AND-REAL-DEFECT-REPRODUCTION-PILOT-R1-20260801"
OLD_TAG = "ignition/iterations/111/terminal-r1"
RECOVERY_TAG = "ignition/iterations/111/terminal-r1-recovery-1"
RECOVERY_TAG_2 = "ignition/iterations/111/terminal-r1-recovery-2"
OLD_OBJECT = "91de7433db0cef4800bb64a59b703a6305bc30ce"
TARGET = "9b15d359c54694d851c38df6ab3c7ae42544a51b"
CONTROL = "8b0cb1fca95d0bd7cc690727dac6591f87808aba"
REASON = "MISSING_REQUIRED_MACHINE_BINDINGS_IN_IMMUTABLE_ORIGINAL_TAG_MESSAGE"
CORE_BYTES = b'{"schema_version":"recovery-test"}\n'
CORE_SHA = hashlib.sha256(CORE_BYTES).hexdigest()


def recovery_message(core_sha: str = CORE_SHA) -> str:
    return (
        f"task_number: {TASK}\n"
        f"task_id: {TASK_ID}\n"
        "terminal_state: TERMINAL_SUCCESS\n"
        f"core_receipt_sha256: {core_sha}\n"
        "attestation_mode: RECOVERY_AFTER_INVALID_TERMINAL_TAG\n"
        f"recovery_of_tag: {OLD_TAG}\n"
        f"recovery_of_tag_object_sha: {OLD_OBJECT}\n"
        f"recovery_of_tag_target: {TARGET}\n"
        f"recovery_reason: {REASON}\n"
        f"recovery_authorization_control_commit: {CONTROL}\n"
    )


class RecoveryValidatorHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.refs = {f"refs/tags/{OLD_TAG}", f"refs/tags/{RECOVERY_TAG}"}
        self.objects = {OLD_TAG: OLD_OBJECT, RECOVERY_TAG: "recovery-object"}
        self.targets = {OLD_TAG: TARGET, RECOVERY_TAG: TARGET}
        self.messages = {
            OLD_TAG: "111 terminal-r1: evidence-gated apple case adjudication and regression gate established\n",
            RECOVERY_TAG: recovery_message(),
        }
        self.patches = mock.patch.multiple(
            le,
            ref_exists=mock.Mock(side_effect=lambda ref: ref in self.refs),
            annotated_tag_object_sha=mock.Mock(side_effect=lambda tag: self.objects.get(tag)),
            tag_points_to=mock.Mock(side_effect=lambda tag, target: self.targets.get(tag) == target),
            tag_message=mock.Mock(side_effect=lambda tag: self.messages.get(tag)),
            recovery_tag_names=mock.Mock(return_value=[RECOVERY_TAG]),
            _git=mock.Mock(side_effect=self.fake_git),
        )
        self.patches.start()
        self.addCleanup(self.patches.stop)

    def fake_git(self, *args: str):
        if args and args[0] == "rev-parse" and len(args) > 1:
            tag = args[1].removesuffix("^{}")
            return self.targets.get(tag)
        return None

    def validate(self, tag_name: str = RECOVERY_TAG, **overrides):
        values = {
            "expected_task_number": TASK,
            "expected_task_id": TASK_ID,
            "expected_target": TARGET,
            "expected_core_sha256": CORE_SHA,
            "expected_attestation_mode": "RECOVERY_AFTER_INVALID_TERMINAL_TAG",
            "recovery_of_tag": OLD_TAG,
            "recovery_of_tag_object_sha": OLD_OBJECT,
            "recovery_of_tag_target": TARGET,
            "recovery_reason": REASON,
            "recovery_authorization_control_commit": CONTROL,
            "core_evidence_bytes": CORE_BYTES,
        }
        values.update(overrides)
        return tv.validate_recovery_tag(tag_name, **values)

    def test_current_invalid_original_rejected_by_ordinary_validator(self):
        problems = tv.validate_tag(
            OLD_TAG,
            expected_task_number=TASK,
            expected_target=TARGET,
            expected_core_sha256=tv.ORIGINAL_TAG_CORE_UNAVAILABLE,
            expected_attestation_mode="ORIGINAL_TERMINATION",
        )
        self.assertEqual(
            problems,
            [
                "terminal tag message missing required field task_number",
                "terminal tag message missing required field task_id",
                "terminal tag message missing required field terminal_state",
                "terminal tag message missing required field core_receipt_sha256",
                "terminal tag message missing required field attestation_mode",
                "terminal tag message does not bind declared core_receipt_sha256",
                "terminal tag message missing attestation_mode ORIGINAL_TERMINATION",
            ],
        )

    def test_attempted_original_tag_movement_rejected(self):
        self.targets[OLD_TAG] = "0" * 40
        problems = self.validate()
        self.assertTrue(any("original tag target mismatch" in p for p in problems))

    def test_recovery_without_original_tag_rejected(self):
        self.refs.remove(f"refs/tags/{OLD_TAG}")
        problems = self.validate()
        self.assertTrue(any("original tag" in p and "not present" in p for p in problems))

    def test_wrong_original_object_sha_rejected(self):
        problems = self.validate(recovery_of_tag_object_sha="1" * 40)
        self.assertTrue(any("original tag object sha mismatch" in p for p in problems))

    def test_wrong_original_target_rejected(self):
        problems = self.validate(recovery_of_tag_target="2" * 40)
        self.assertTrue(any("original tag target mismatch" in p for p in problems))

    def test_wrong_recovery_index_rejected(self):
        self.objects[RECOVERY_TAG_2] = "recovery-object-2"
        self.targets[RECOVERY_TAG_2] = TARGET
        self.messages[RECOVERY_TAG_2] = recovery_message()
        self.refs.add(f"refs/tags/{RECOVERY_TAG_2}")
        le.recovery_tag_names.return_value = [RECOVERY_TAG_2]
        problems = self.validate(RECOVERY_TAG_2)
        self.assertTrue(any("recovery tag index" in p for p in problems))

    def test_missing_recovery_specific_field_rejected(self):
        self.messages[RECOVERY_TAG] = recovery_message().replace(
            f"recovery_reason: {REASON}\n", ""
        )
        problems = self.validate()
        self.assertTrue(any("missing required field recovery_reason" in p for p in problems))

    def test_recovery_tag_wrong_target_rejected(self):
        self.targets[RECOVERY_TAG] = "3" * 40
        problems = self.validate()
        self.assertTrue(any("recovery tag does not point" in p for p in problems))

    def test_recovery_tag_core_digest_mismatch_rejected(self):
        problems = self.validate(expected_core_sha256="4" * 64)
        self.assertTrue(any("core evidence digest mismatch" in p for p in problems))

    def test_duplicate_conflicting_recovery_tags_rejected(self):
        le.recovery_tag_names.return_value = [RECOVERY_TAG, RECOVERY_TAG_2]
        problems = self.validate()
        self.assertTrue(any("duplicate/conflicting recovery tags" in p for p in problems))

    def test_lightweight_recovery_tag_rejected(self):
        self.objects[RECOVERY_TAG] = None
        problems = self.validate()
        self.assertTrue(any("lightweight" in p for p in problems))

    def test_exact_authorized_recovery_chain_passes(self):
        self.assertEqual(self.validate(), [])

    def test_old_tag_alone_never_resolves_terminal_success(self):
        candidate = {
            "task_number": TASK,
            "event_type": "ITERATION_CANDIDATE",
            "lifecycle_state": "CONTENT_MERGED_AWAITING_TERMINALIZATION",
            "formal_content_pr_number": 174,
            "exact_reviewed_content_head": "3c086e070998670aa88c7a9bb31481b27e17d59e",
        }
        projection = {
            "task_number": TASK,
            "event_type": "TERMINALIZATION_PROJECTION",
            "content_pr_number": 174,
            "content_merge_commit": TARGET,
            "terminal_tag_name": OLD_TAG,
            "terminal_state": "TERMINAL_SUCCESS",
        }
        result = le.resolve_task([candidate, projection], TASK, git_available=False)
        self.assertNotEqual(result["resolved_state"], "TERMINAL_SUCCESS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
