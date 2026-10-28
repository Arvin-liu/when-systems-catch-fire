#!/usr/bin/env python3
"""Annotated terminal-tag validator (task 108 and task-111 recovery).

Validates an annotated terminal tag used for iteration attestation. The tag must:

  * follow ``ignition/iterations/<n>/terminal-r1`` or the narrowly governed
    ``ignition/iterations/<n>/terminal-r1-recovery-<positive integer>`` form;
  * be an ANNOTATED tag (a tag object exists), never a lightweight tag;
  * point to the declared terminalization merge commit;
  * carry a message binding task_number, task_id, terminal_state,
    core_receipt_sha256 and attestation_mode;
  * declare a core_receipt_sha256 that matches the immutable TERMINAL_EVIDENCE_CORE.json.

Any deviation FAILS CLOSED. This module is importable so unit tests can feed
synthetic and broken tags.
"""
from __future__ import annotations

import hashlib
import re
import sys
from typing import Dict, List, Optional

import lifecycle_events as le

TERMINAL_TAG_RE = re.compile(r"^ignition/iterations/(\d+)/terminal-r1$")
RECOVERY_TAG_RE = re.compile(
    r"^ignition/iterations/(\d+)/terminal-r1-recovery-([1-9]\d*)$"
)

# The original task-111 tag has no core receipt.  Recovery validation uses a
# non-empty sentinel when replaying the ordinary validator so that the old tag
# must remain invalid without inventing a digest for it.
ORIGINAL_TAG_CORE_UNAVAILABLE = "ORIGINAL_TAG_CORE_UNAVAILABLE"

REQUIRED_MESSAGE_FIELDS = (
    "task_number",
    "task_id",
    "terminal_state",
    "core_receipt_sha256",
    "attestation_mode",
)

RECOVERY_MESSAGE_FIELDS = (
    "recovery_of_tag",
    "recovery_of_tag_object_sha",
    "recovery_of_tag_target",
    "recovery_reason",
    "recovery_authorization_control_commit",
)


def message_field(message: str, field: str) -> Optional[str]:
    """Return the exact ``field: value`` binding from an annotated message."""
    prefix = f"{field}:"
    for line in message.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def tag_object_sha(tag_name: str) -> Optional[str]:
    return le.annotated_tag_object_sha(tag_name)


def validate_tag(
    tag_name: str,
    *,
    expected_task_number: int,
    expected_target: str,
    expected_core_sha256: str,
    expected_attestation_mode: str,
    core_evidence_bytes: Optional[bytes] = None,
) -> List[str]:
    """Return a list of problems (empty == valid). Fail-closed."""
    problems: List[str] = []
    m = TERMINAL_TAG_RE.match(tag_name)
    if not m:
        return [f"tag {tag_name!r} does not match ignition/iterations/<n>/terminal-r1"]
    if int(m.group(1)) != expected_task_number:
        problems.append(f"tag number {m.group(1)} != expected task {expected_task_number}")

    if not le.ref_exists(f"refs/tags/{tag_name}"):
        return [f"terminal tag {tag_name} not present in repository"]

    obj = tag_object_sha(tag_name)
    if obj is None:
        return [f"terminal tag {tag_name} is lightweight, not annotated (reject: force-move or wrong type)"]

    if not le.tag_points_to(tag_name, expected_target):
        actual = le._git("rev-parse", f"{tag_name}^{{}}")
        problems.append(f"terminal tag does not point to {expected_target} (actual {actual})")

    msg = le.tag_message(tag_name) or ""
    for field in REQUIRED_MESSAGE_FIELDS:
        if message_field(msg, field) is None:
            problems.append(f"terminal tag message missing required field {field}")

    if message_field(msg, "core_receipt_sha256") != expected_core_sha256:
        problems.append("terminal tag message does not bind declared core_receipt_sha256")

    if expected_attestation_mode and message_field(msg, "attestation_mode") != expected_attestation_mode:
        problems.append(f"terminal tag message missing attestation_mode {expected_attestation_mode}")

    # Cross-check the core evidence bytes if supplied.
    if core_evidence_bytes is not None:
        actual = hashlib.sha256(core_evidence_bytes).hexdigest()
        if actual != expected_core_sha256:
            problems.append(f"core evidence digest mismatch computed={actual} declared={expected_core_sha256}")

    return problems


def validate_recovery_tag(
    tag_name: str,
    *,
    expected_task_number: int,
    expected_task_id: str,
    expected_target: str,
    expected_core_sha256: str,
    expected_attestation_mode: str,
    recovery_of_tag: str,
    recovery_of_tag_object_sha: str,
    recovery_of_tag_target: str,
    recovery_reason: str,
    recovery_authorization_control_commit: str,
    expected_recovery_index: int = 1,
    original_expected_core_sha256: str = ORIGINAL_TAG_CORE_UNAVAILABLE,
    core_evidence_bytes: Optional[bytes] = None,
) -> List[str]:
    """Validate the exact task-111 recovery-attestation contract.

    A recovery tag is never accepted merely because its own message is
    complete.  The original tag must still exist, remain annotated at the
    declared object and target, and still fail the ordinary validator.  This
    keeps the invalid original tag as immutable incident evidence while making
    the recovery tag the only possible terminal authority.
    """
    problems: List[str] = []
    match = RECOVERY_TAG_RE.fullmatch(tag_name)
    if not match:
        return [
            f"tag {tag_name!r} does not match "
            "ignition/iterations/<n>/terminal-r1-recovery-<positive integer>"
        ]
    if int(match.group(1)) != expected_task_number:
        problems.append(
            f"tag number {match.group(1)} != expected task {expected_task_number}"
        )
    if int(match.group(2)) != expected_recovery_index:
        problems.append(
            f"recovery tag index {match.group(2)} != expected {expected_recovery_index}"
        )

    if not le.ref_exists(f"refs/tags/{tag_name}"):
        return [f"recovery tag {tag_name} not present in repository"]

    obj = tag_object_sha(tag_name)
    if obj is None:
        problems.append(
            f"recovery tag {tag_name} is lightweight, not annotated "
            "(reject: force-move or wrong type)"
        )
    if not le.tag_points_to(tag_name, expected_target):
        actual = le._git("rev-parse", f"{tag_name}^{{}}")
        problems.append(
            f"recovery tag does not point to {expected_target} (actual {actual})"
        )

    msg = le.tag_message(tag_name) or ""
    for field in REQUIRED_MESSAGE_FIELDS + RECOVERY_MESSAGE_FIELDS:
        if message_field(msg, field) is None:
            problems.append(f"recovery tag message missing required field {field}")

    expected_fields = {
        "task_number": str(expected_task_number),
        "task_id": expected_task_id,
        "terminal_state": "TERMINAL_SUCCESS",
        "core_receipt_sha256": expected_core_sha256,
        "attestation_mode": expected_attestation_mode,
        "recovery_of_tag": recovery_of_tag,
        "recovery_of_tag_object_sha": recovery_of_tag_object_sha,
        "recovery_of_tag_target": recovery_of_tag_target,
        "recovery_reason": recovery_reason,
        "recovery_authorization_control_commit": recovery_authorization_control_commit,
    }
    for field, expected in expected_fields.items():
        actual = message_field(msg, field)
        if actual is not None and actual != expected:
            problems.append(
                f"recovery tag message field {field} mismatch "
                f"declared={actual} expected={expected}"
            )

    if core_evidence_bytes is not None:
        actual = hashlib.sha256(core_evidence_bytes).hexdigest()
        if actual != expected_core_sha256:
            problems.append(
                f"core evidence digest mismatch computed={actual} "
                f"declared={expected_core_sha256}"
            )

    # Preserve the original tag and independently replay the ordinary
    # validator.  A moved, deleted, lightweight, or newly-valid old tag is a
    # recovery failure, not an acceptable cleanup.
    if not le.ref_exists(f"refs/tags/{recovery_of_tag}"):
        problems.append(f"recovery original tag {recovery_of_tag} not present")
    else:
        original_obj = tag_object_sha(recovery_of_tag)
        if original_obj != recovery_of_tag_object_sha:
            problems.append(
                "recovery original tag object sha mismatch "
                f"declared={recovery_of_tag_object_sha} actual={original_obj}"
            )
        if not le.tag_points_to(recovery_of_tag, recovery_of_tag_target):
            actual_target = le._git("rev-parse", f"{recovery_of_tag}^{{}}")
            problems.append(
                "recovery original tag target mismatch "
                f"declared={recovery_of_tag_target} actual={actual_target}"
            )
        original_problems = validate_tag(
            recovery_of_tag,
            expected_task_number=expected_task_number,
            expected_target=recovery_of_tag_target,
            expected_core_sha256=original_expected_core_sha256,
            expected_attestation_mode="ORIGINAL_TERMINATION",
        )
        if not original_problems:
            problems.append(
                "recovery original tag unexpectedly passes ordinary validator"
            )

    # Only one recovery tag may exist for a task.  A second tag, even if it is
    # otherwise valid, creates competing terminal authority and fails closed.
    recovery_tags = le.recovery_tag_names(expected_task_number)
    if recovery_tags and recovery_tags != [tag_name]:
        problems.append(
            "duplicate/conflicting recovery tags: " + ", ".join(recovery_tags)
        )

    return problems


def main() -> int:
    import argparse
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag")
    ap.add_argument("--task-number", type=int)
    ap.add_argument("--target")
    ap.add_argument("--core-sha256")
    ap.add_argument("--attestation-mode")
    ap.add_argument("--core-file", default=None)
    args = ap.parse_args()
    if not all([args.tag, args.task_number, args.target, args.core_sha256, args.attestation_mode]):
        print("missing arguments", file=sys.stderr)
        return 2
    core_bytes = None
    if args.core_file:
        with open(args.core_file, "rb") as fh:
            core_bytes = fh.read()
    problems = validate_tag(
        args.tag,
        expected_task_number=args.task_number,
        expected_target=args.target,
        expected_core_sha256=args.core_sha256,
        expected_attestation_mode=args.attestation_mode,
        core_evidence_bytes=core_bytes,
    )
    if problems:
        for p in problems:
            print(f"TAG_INVALID: {p}", file=sys.stderr)
        return 1
    print(f"TAG_OK {args.tag} -> {args.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
