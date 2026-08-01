#!/usr/bin/env python3
"""Annotated terminal-tag validator (task 108, contract §4/§7/§12).

Validates an annotated terminal tag used for iteration attestation. The tag must:

  * follow ``ignition/iterations/<n>/terminal-r1``;
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

REQUIRED_MESSAGE_FIELDS = (
    "task_number",
    "task_id",
    "terminal_state",
    "core_receipt_sha256",
    "attestation_mode",
)


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
        if field not in msg:
            problems.append(f"terminal tag message missing required field {field}")

    if expected_core_sha256 not in msg:
        problems.append("terminal tag message does not bind declared core_receipt_sha256")

    if expected_attestation_mode and expected_attestation_mode not in msg:
        problems.append(f"terminal tag message missing attestation_mode {expected_attestation_mode}")

    # Cross-check the core evidence bytes if supplied.
    if core_evidence_bytes is not None:
        actual = hashlib.sha256(core_evidence_bytes).hexdigest()
        if actual != expected_core_sha256:
            problems.append(f"core evidence digest mismatch computed={actual} declared={expected_core_sha256}")

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
