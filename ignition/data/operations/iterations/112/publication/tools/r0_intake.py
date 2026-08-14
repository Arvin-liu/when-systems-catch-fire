#!/usr/bin/env python3
"""Freeze the bounded, tracked delta of the isolated R0 repository."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path


R0 = Path("/Users/zhiyuan/WorkBuddy/Claw/ignition-publication-preproduction-r0")
DEST = Path("data/operations/iterations/112/publication/r0-original")
OUT = DEST.parent
BASE = "9b15d359c54694d851c38df6ab3c7ae42544a51b"
STAGE_SEVEN = "68302f968f109afc4b15988b46d3c99cc8c9fa33"
FINAL = "84fdcf68f2bd3fde8ed543b0ec6b51a538ea9597"


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=R0, text=True).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def char_counts(path: Path) -> dict[str, int]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"characters": 0, "lines": 0, "han_characters": 0}
    return {
        "characters": len(text),
        "lines": text.count("\n") + (1 if text else 0),
        "han_characters": sum("\u3400" <= c <= "\u9fff" for c in text),
    }


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    paths = subprocess.check_output(
        ["git", "-c", "core.quotePath=false", "diff", "--name-only", "-z", BASE, FINAL],
        cwd=R0,
    ).split(b"\0")
    tracked_delta = [p.decode("utf-8") for p in paths if p]
    if not tracked_delta:
        raise SystemExit("R0 tracked delta is empty")

    # Rebuild only this newly-created intake subtree; never touch the source R0 tree.
    for child in DEST.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for rel in tracked_delta:
        archive = subprocess.check_output(["git", "archive", FINAL, "--", rel], cwd=R0)
        with tarfile.open(fileobj=__import__("io").BytesIO(archive), mode="r:") as tf:
            tf.extractall(DEST)

    entries = []
    for rel in sorted(tracked_delta):
        path = DEST / rel
        data = path.read_bytes()
        entries.append(
            {
                "path": rel,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
                **char_counts(path),
            }
        )

    manifest = {
        "schema_version": "112.r0-file-manifest.v1",
        "intake_type": "BOUNDED_TRACKED_R0_DELTA",
        "source_repository": "Arvin-liu/when-systems-catch-fire",
        "source_workspace": str(R0),
        "baseline_commit": BASE,
        "stage_seven_commit": STAGE_SEVEN,
        "final_commit": FINAL,
        "tracked_delta_count": len(entries),
        "entries": entries,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (OUT / "R0_FILE_MANIFEST.json").write_bytes(manifest_bytes)

    source_lock = {
        "schema_version": "112.r0-source-lock.v1",
        "lock_status": "IMMUTABLE_INTAKE_LOCKED",
        "task_number": 112,
        "task_id": "IGNITION-RESEARCH-PUBLICATION-LAYER-HUNDRED-ITERATION-KNOWLEDGE-HARVEST-VOLUME-ONE-R1-20260802",
        "r0_workspace": str(R0),
        "r0_branch": run("git", "branch", "--show-current"),
        "r0_final_commit": FINAL,
        "r0_stage_seven_commit": STAGE_SEVEN,
        "fixed_source_baseline": BASE,
        "final_is_descendant_of_stage_seven": run("git", "merge-base", "--is-ancestor", STAGE_SEVEN, FINAL) == "",
        "r0_worktree_status": run("git", "status", "--porcelain=v1"),
        "source_fetch_url": "https://github.com/Arvin-liu/when-systems-catch-fire.git",
        "source_push_url": "DISABLED-LOCAL-ONLY",
        "r0_formal_remote_modified": False,
        "r0_1111_modified": False,
        "intake_root": "data/operations/iterations/112/publication/r0-original/",
        "manifest_path": "data/operations/iterations/112/publication/R0_FILE_MANIFEST.json",
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "source_manifest_sha256_at_r0_final": sha256_file(R0 / "SOURCE-MANIFEST.json"),
        "original_files_are_preserved_without_revision": True,
        "notes": [
            "Counts in the R0 SOURCE-MANIFEST remain intake claims until the independent audit is complete.",
            "The snapshot is the tracked delta from the fixed baseline, not a second copy of the formal repository.",
        ],
    }
    (OUT / "R0_SOURCE_LOCK.json").write_text(
        json.dumps(source_lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
