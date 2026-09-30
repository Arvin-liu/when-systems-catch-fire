#!/usr/bin/env python3
"""Create/check a byte manifest for Task229 preregistration sources."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE.parent
EXCLUDED = {"freeze-manifest.json"}
EXTERNAL = {
    "task228_manifest": ("ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/SHA256SUMS", "864c4b91dc12b7f3166d1f0101b8e4dc300551fd4e83f28bb9e1be96a0312538"),
    "task228_build_manifest": ("ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/build/candidate-build-manifest.json", "dc679675af1401a3b4c7c816bcded9e7485dbf49f109d3e08f757011f21eb484"),
    "task225_freeze_manifest": ("ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/freeze-manifest.json", "f6201ea25d3614af34ef05d36cc8f620a8c149902fcef8937d259445b0b302a8"),
    "task227_freeze_manifest": ("ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/freeze/freeze-manifest.json", "91a33c38f209b88644ef473c21a133463bf7839d1bd5afc9c1507b88d128b7ec"),
}
PATH_CLASSIFICATION = "ignition/data/foundation/repository-path-classification/classification-manifest.jsonl"
PARENT_SHA = "d82a52077df6d4e96e998ace3757f2fb343b4db5"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_entries():
    entries = []
    for path in sorted(PREREG.rglob("*")):
        if not path.is_file() or path.name in EXCLUDED:
            continue
        rel = path.relative_to(PREREG).as_posix()
        if rel.startswith("run/"):
            continue
        entries.append({"path": rel, "sha256": sha(path.read_bytes())})
    return entries


def expected_document():
    repo = PREREG.parents[3]
    external = {}
    for name, (rel, expected) in EXTERNAL.items():
        path = repo / rel
        if path.is_file():
            raw = path.read_bytes()
        elif name == "task225_freeze_manifest":
            raw = subprocess.run(
                ["git", "show", f"{PARENT_SHA}:{rel}"], cwd=repo,
                check=True, capture_output=True
            ).stdout
        else:
            raw = b""
        digest = sha(raw) if raw else None
        external[name] = {"path": rel, "sha256": digest, "expected_sha256": expected}
    classification_path = repo / PATH_CLASSIFICATION
    classification_sha = sha(classification_path.read_bytes()) if classification_path.is_file() else None
    external["formal_path_classification_manifest"] = {
        "path": PATH_CLASSIFICATION,
        "sha256": classification_sha,
        "expected_sha256": classification_sha,
    }
    return {
        "version": "task229-preregistration-freeze-r0",
        "task_branch": "work/IGNITION-20260929-229-transfer-interface-clean-r0",
        "required_parent_sha": PARENT_SHA,
        "external_anchors": external,
        "files": file_entries()
    }


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = PREREG / "freeze-manifest.json"
    expected = expected_document()
    if any(item["sha256"] != item["expected_sha256"] for item in expected["external_anchors"].values()):
        print("TASK229_FREEZE_MANIFEST=FAIL external anchor mismatch", file=sys.stderr)
        return 1
    if args.write:
        if path.exists():
            print("TASK229_FREEZE_MANIFEST=FAIL refusing to overwrite existing freeze", file=sys.stderr)
            return 1
        path.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        if not path.is_file():
            print("TASK229_FREEZE_MANIFEST=FAIL freeze manifest is missing", file=sys.stderr)
            return 1
        actual = json.loads(path.read_text(encoding="utf-8"))
        if actual != expected:
            print("TASK229_FREEZE_MANIFEST=FAIL preregistration bytes differ from freeze manifest", file=sys.stderr)
            return 1
    digest = sha(path.read_bytes()) if path.is_file() else ""
    print(f"TASK229_FREEZE_MANIFEST=PASS SHA256={digest}")
    print(f"TASK229_PREREG_FILES={len(expected['files'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
