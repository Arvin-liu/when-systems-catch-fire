#!/usr/bin/env python3
"""Deterministic publication and integration gate for Task 114."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
PUB = ROOT / "data/operations/iterations/114/publication"
MANIFEST = PUB / "PUBLICATION_MANIFEST.json"
FREEZE = PUB / "CANDIDATE_FREEZE.json"
REGISTRY = ROOT / "data/publication/zhiyuan-writing-showcase.json"

TASK_ID = "IGNITION-LANGUAGE-THOUGHT-LOGIC-CROSS-LAYER-PLANE-REPRESENTATIVE-LANGUAGE-PILOT-AND-CURRENT-WORK-REPAIR-R1-20260802"
ARMY_PATH = "docs/publication/works/when-an-army-believes-its-own-back.md"
EMPEROR_PATH = "docs/publication/works/when-an-emperor-manufactures-heaven.md"
METHOD_PATH = "docs/publication/zhiyuan-writing-method.md"
FINAL_HASHES = {
    ARMY_PATH: "520a4b2043dacbd876b2831c257e62d126378a8e916c4beeb5365867f7f7025d",
    EMPEROR_PATH: "d7f9df5cc8d4e1eaf4ffd906856e6e6c363d5bb8a32225f7737a62ce3147e0a5",
    METHOD_PATH: "615b049dca357f4c00e3baeb38a3edd649a3bfadfa3a292928ab8d9ed8867e4d",
}
HISTORICAL_HASHES = {
    ARMY_PATH: "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b",
    EMPEROR_PATH: "8d9fe3752e602041c8effb12f39bb2188c60a74843be4285d9181969e314a2e4",
}
FROZEN_HASHES = {
    ARMY_PATH: "2575c6c20922b434cde18514aed9fc3cd68a8df7514378354b2f8f46af7636f0",
    EMPEROR_PATH: "d397dcb1dff1da39d0340c110b4e655c32fe9b9ce58e99f6b4904ca602bcb7ac",
    METHOD_PATH: "fd23ebd2cb7ad988e31a5e6c38612711fdb1bbda81718a5f74d1381c7985ebab",
}
ROLE_REVIEWS = {
    "LANGUAGE_COGNITION_AND_TYPOLOGY_REVIEW.md": "PASS_WITH_BOUNDED_CLAIMS",
    "CROSS_LAYER_ARCHITECTURE_REVIEW.md": "PASS_NO_L7_NO_TRUTH_UPGRADE",
    "NATIVE_CHINESE_REVIEW.md": "PASS_AFTER_SUBSTANTIVE_REWRITE",
    "LITERARY_ANTI_HOMOGENIZATION_AND_COPYRIGHT_REVIEW.md": "PASS_WITH_REQUIRED_PRESERVATIONS",
}


def fail(message: str) -> None:
    raise SystemExit(f"TASK114_PUBLICATION_VALIDATION_FAILED: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def text(path: Path) -> str:
    require(path.is_file(), f"missing file: {path.relative_to(ROOT)}")
    value = path.read_text(encoding="utf-8")
    require(bool(value.strip()), f"empty file: {path.relative_to(ROOT)}")
    return value


def load(path: Path) -> dict:
    return json.loads(text(path))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    # Import after ROOT is known so the validator uses the checkout under test.
    from tools.language_thought.validate_language_thought import validate_repository

    manifest = load(MANIFEST)
    freeze = load(FREEZE)
    registry = load(REGISTRY)
    plane_report = validate_repository(ROOT)

    require(manifest.get("task_id") == TASK_ID, "publication manifest task identity mismatch")
    require(manifest.get("review_state") == "FOUR_ROLE_REVIEW_COMPLETE_SUBSTANTIVE_REWRITE_COMPLETE", "four-role review is not complete")
    require(plane_report["status"] == "PASS", f"language-thought plane failed: {plane_report['errors']}")
    require(plane_report["dimensions"] == 12 and plane_report["profiles"] == 4, "dimension/profile count mismatch")
    require(plane_report["fixtures"] == 26, "fixture count mismatch")
    metrics = plane_report["fixture_metrics"]
    require(metrics["false_positive"] == 0 and metrics["false_negative"] == 0, "fixture gate has false positives or false negatives")
    require(metrics["unsupported"] >= 1, "unsupported human-judgment category disappeared")

    frozen = {item["path"]: item["candidate_sha256"] for item in freeze.get("candidates", [])}
    require(frozen == FROZEN_HASHES, "candidate freeze does not bind the exact three review inputs")
    for path, expected in FINAL_HASHES.items():
        actual = sha256(ROOT / path)
        require(actual == expected, f"current artifact hash mismatch: {path}: {actual}")
        require(actual != FROZEN_HASHES[path], f"artifact was not substantively revised after review: {path}")

    army = text(ROOT / ARMY_PATH)
    emperor = text(ROOT / EMPEROR_PATH)
    method = text(ROOT / METHOD_PATH)
    for forbidden in (
        "战局已经变成什么样",
        "证据不再只是被动摆在行动之前",
        "再让这些解释返回统治",
        "它们飞得并不需要先知道自己将被怎样解释",
    ):
        require(forbidden not in army + emperor, f"reviewed thought-organization defect remains: {forbidden}")
    for required in (
        "谁在退，谁还站着",
        "行动以前，人们通常先找证据，再作判断",
    ):
        require(required in army, f"army substantive rewrite missing: {required}")
    for required in (
        "鹤只是从宫门上空飞过。人们后来怎样解释这一幕，是另一回事。",
        "宫廷再把解释送回皇权",
    ):
        require(required in emperor, f"emperor substantive rewrite missing: {required}")
    for required in (
        "Version: `0.5.0` current",
        "事件先行”是一种诊断动作",
        "不提交大型版权语料",
        "不能证明自然度或文学质量",
    ):
        require(required in method, f"method 0.5.0 boundary missing: {required}")

    dispositions = text(PUB / "REVIEW_DISPOSITION_MATRIX.md")
    for filename, terminal_disposition in ROLE_REVIEWS.items():
        review = text(PUB / filename)
        require("审查结论" in review, f"review conclusion missing: {filename}")
        require(terminal_disposition in dispositions, f"role disposition missing: {terminal_disposition}")
    for name in (
        "NON_CHINESE_PROFILE_SOURCE_REVIEW.md",
        "FINAL_REVISION_MAP.md",
        "PUBLICATION_MANIFEST.json",
    ):
        text(PUB / name)

    items = {item["work_path"]: item for item in registry.get("items", [])}
    for path in (ARMY_PATH, EMPEROR_PATH):
        item = items.get(path)
        require(item is not None, f"current machine shelf missing {path}")
        require(item.get("accepted_text_sha256") == HISTORICAL_HASHES[path], f"historical acceptance overwritten: {path}")
        require(item.get("current_revision_sha256") == FINAL_HASHES[path], f"current revision not bound: {path}")
        require(item.get("current_method_version") == "0.5.0", f"current method version missing: {path}")
        require(item.get("revision_lineage", {}).get("preserves_historical_acceptance") is True, f"lineage boundary missing: {path}")

    shelf = text(ROOT / "PUBLICATIONS/README.md")
    root_readme = text(ROOT / "README.md")
    for basename in ("when-an-army-believes-its-own-back.md", "when-an-emperor-manufactures-heaven.md"):
        require(basename in shelf, f"publication shelf missing current work: {basename}")
    require("PUBLICATIONS/README.md" in root_readme, "root does not reach publication shelf in one click")
    require("language-thought-logic-plane.md" in root_readme, "root does not expose the cross-layer plane")

    topology = load(ROOT / "data/operations/change-propagation-topology.json")
    relation = next((item for item in topology.get("relations", []) if item.get("relation_id") == "map_language_thought_zhiyuan"), None)
    require(relation is not None and relation.get("relation_class") == "synchronization_requires", "plane-to-method relation is not a synchronization obligation")
    system_map = load(ROOT / "data/architecture/interactive-system-map.json")
    node_ids = {node.get("id") for node in system_map.get("nodes", [])}
    require("language_thought_plane" in node_ids, "system map lacks language-thought plane")
    require("l7" not in {str(item).lower() for item in node_ids}, "system map introduced L7")
    require(system_map.get("map_version") == "0.5.0", "current map version is not 0.5.0")

    lifecycle = [json.loads(line) for line in text(ROOT / "data/operations/lifecycle-events.jsonl").splitlines() if line.strip()]
    task_events = [event for event in lifecycle if event.get("task_number") == 114]
    candidates = [event for event in task_events if event.get("event_type") == "ITERATION_CANDIDATE"]
    terminals = [event for event in task_events if event.get("event_type") == "TERMINALIZATION_PROJECTION"]
    require(len(candidates) == 1, "Task 114 must have exactly one content candidate event")
    state = candidates[0].get("lifecycle_state")
    require(state in {"READY_FOR_CONTENT_MERGE", "CONTENT_MERGED_AWAITING_TERMINALIZATION"}, "Task 114 content candidate lifecycle record mismatch")
    if state == "READY_FOR_CONTENT_MERGE":
        require(candidates[0].get("formal_content_pr_number") is None and candidates[0].get("exact_reviewed_content_head") is None, "pre-merge candidate asserts future PR identity")
    else:
        require(isinstance(candidates[0].get("formal_content_pr_number"), int), "merged candidate lacks content PR")
        require(isinstance(candidates[0].get("exact_reviewed_content_head"), str), "merged candidate lacks exact reviewed head")
    require(len(terminals) <= 1, "Task 114 has duplicate terminal projections")
    if terminals:
        require(terminals[0].get("lifecycle_state") == "TERMINAL_SUCCESS", "Task 114 terminal projection is not TERMINAL_SUCCESS")

    ci = text(ROOT / ".github/workflows/foundation-validation.yml")
    require("Validate Language-Thought Logic Plane" in ci and "tests.test_language_thought_plane" in ci, "formal CI does not run the plane gate")
    require(text(ROOT / "reports/operations/114-language-thought-project-audit.md").count("25 条") == 1, "project audit summary missing exact finding count")
    require(not (ROOT / "data/operations/iterations/115").exists(), "Task 115 iteration directory exists")
    require(not any(ROOT.glob("**/*task115*")), "Task 115 artifact exists")

    print(json.dumps({
        "status": "PASS",
        "task": 114,
        "architecture": "ORTHOGONAL_PLANE_ACROSS_L0_L6_NOT_L7",
        "dimensions": plane_report["dimensions"],
        "profiles": plane_report["profiles"],
        "fixtures": plane_report["fixtures"],
        "fixture_metrics": metrics,
        "audit": {"population": 14, "findings": 25},
        "reviews": 4,
        "works": {ARMY_PATH: FINAL_HASHES[ARMY_PATH], EMPEROR_PATH: FINAL_HASHES[EMPEROR_PATH]},
        "method": {"version": "0.5.0", "sha256": FINAL_HASHES[METHOD_PATH]},
        "task115": "ABSENT",
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
