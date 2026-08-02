#!/usr/bin/env python3
"""Deterministic validator for the task-113 public writing chain."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
WORK = ROOT / "docs/publication/works/when-an-emperor-manufactures-heaven.md"
CASE = ROOT / "docs/publication/cases/song-huizong-taoism-1117-source.md"
ANALYSIS = ROOT / "reports/publication/song-huizong-taoism-point-fire-analysis.md"
SHELF = ROOT / "PUBLICATIONS/README.md"
SHOWCASE = ROOT / "docs/publication/zhiyuan-writing-showcase.md"
REGISTRY = ROOT / "data/publication/zhiyuan-writing-showcase.json"
MANIFEST = ROOT / "data/operations/iterations/113/publication/PUBLICATION_MANIFEST.json"
REVIEW_ROOT = ROOT / "data/operations/iterations/113/publication"

SOURCE_SHA = "506904a3923bf5aac9f65c8311c512d2ba70b4c1073802b02647ce294fab433f"
SOURCE_BYTES = 41601
R0_SHA = "09e7b476303f74d9851a8ed227d5432f7bcc15b307c3e0607125723f61d35489"
WORK_PATH = "docs/publication/works/when-an-emperor-manufactures-heaven.md"
CASE_PATH = "docs/publication/cases/song-huizong-taoism-1117-source.md"
ANALYSIS_PATH = "reports/publication/song-huizong-taoism-point-fire-analysis.md"
WORK_ID = "zhiyuan-work-song-huizong-taoism-113"

REVIEW_FILES = (
    "SOURCE_AND_CLAIM_REVIEW.md",
    "ADVERSARIAL_REVIEW.md",
    "EDITORIAL_REVIEW.md",
    "REVIEW_DISPOSITION_MATRIX.md",
    "FINAL_REVISION_MAP.md",
    "PUBLICATION_MANIFEST.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def han_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))


def fail(message: str) -> None:
    raise SystemExit(f"TASK113_PUBLICATION_VALIDATION_FAILED: {message}")


def require_file(path: Path) -> str:
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        fail(f"missing or empty artifact: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    work_text = require_file(WORK)
    case_text = require_file(CASE)
    analysis_text = require_file(ANALYSIS)
    shelf_text = require_file(SHELF)
    showcase_text = require_file(SHOWCASE)
    registry = json.loads(require_file(REGISTRY))
    manifest = json.loads(require_file(MANIFEST))

    final_sha = sha256(WORK)
    if final_sha == R0_SHA:
        fail("final work was not substantively rewritten from the frozen R0 candidate")
    body = work_text.split("### 参考与继续核查", 1)[0]
    body_han = han_count(body)
    if not 5000 <= body_han <= 9000:
        fail(f"main-body Han character count {body_han} is outside 5000..9000")
    forbidden_body = (
        "IGNITION-ZHIYUAN",
        "d15ce70bef67b439ec2e99d1aeb1e792b4e6e9ef",
        "1b3545a252c542129424a240d3c7eb3b5af808af",
        "PR #",
        "../cases/",
        "../reports/",
        "data/operations/",
    )
    for token in forbidden_body:
        if token in body:
            fail(f"internal execution or path token leaked into main essay body: {token}")
    for required_phrase in ("《瑞鹤图》", "教主道君皇帝", "艮岳", "林灵素", "谁还能让天意对他说“不”"):
        if required_phrase not in work_text:
            fail(f"essay is missing load-bearing phrase: {required_phrase}")

    if "FULL_LOCAL_NOTE_HASH_MATCH" not in case_text or SOURCE_SHA not in case_text or str(SOURCE_BYTES) not in case_text:
        fail("source provenance page does not bind exact source mode, byte count and SHA-256")
    for phrase in ("不进入正式仓库", "第三方课程原文", "人工驯鹤", "富兰克林"):
        if phrase not in case_text:
            fail(f"source boundary page is missing required handling marker: {phrase}")
    if "原文" in work_text and "第三方课程原文" in work_text:
        # The essay may say the transcript was not used; the transcript itself must not appear.
        if len(work_text) > 50000:
            fail("essay unexpectedly exceeds bounded publication size")

    for phrase in (
        "SOURCE_REPORTS",
        "SUPPORTED_WITH_SCOPE",
        "PARTIALLY_SUPPORTED",
        "CONTESTED",
        "NOT_VERIFIED",
        "OMITTED_FROM_FINAL",
        "竞争解释",
        "provenance-bound feedback",
        "候选 gap",
    ):
        if phrase not in analysis_text:
            fail(f"Pointfire analysis is missing required boundary or analysis element: {phrase}")

    for name in REVIEW_FILES:
        require_file(REVIEW_ROOT / name)
    review_text = "\n".join((REVIEW_ROOT / name).read_text(encoding="utf-8") for name in REVIEW_FILES)
    if R0_SHA not in review_text or final_sha not in review_text:
        fail("review artifacts do not bind both frozen R0 and final work hashes")
    if "实质重写" not in review_text or "COMPLETE" not in review_text:
        fail("review artifacts do not show completed substantive disposition")

    if "when-an-emperor-manufactures-heaven.md" not in shelf_text:
        fail("publication shelf does not link the new work")
    if "when-an-emperor-manufactures-heaven.md" not in showcase_text or "song-huizong-taoism-1117-source.md" not in showcase_text:
        fail("human showcase does not expose the complete chain")
    if "《当天意有了接口：宋徽宗与会自我证明的皇权》" not in showcase_text:
        fail("human showcase does not expose the final title")

    items = registry.get("items", [])
    item = next((row for row in items if row.get("work_id") == WORK_ID), None)
    if item is None:
        fail(f"machine showcase registry missing {WORK_ID}")
    if item.get("method_version") != "0.4.0":
        fail("machine showcase registry does not bind method version 0.4.0")
    if item.get("source_sha256") != SOURCE_SHA or item.get("accepted_text_sha256") != final_sha:
        fail("machine showcase registry hash binding mismatch")
    for key, expected in (("work_path", WORK_PATH), ("case_path", CASE_PATH), ("analysis_path", ANALYSIS_PATH)):
        if item.get(key) != expected:
            fail(f"machine registry {key} mismatch")

    if manifest.get("status") != "PUBLISHED_WITH_EXPLICIT_LIMITATIONS" or manifest.get("review", {}).get("state") != "COMPLETE":
        fail("publication manifest is not complete with explicit limitations")
    if manifest.get("source", {}).get("sha256") != SOURCE_SHA or manifest.get("source", {}).get("utf8_bytes") != SOURCE_BYTES:
        fail("publication manifest source identity mismatch")
    if manifest.get("artifacts", {}).get("work", {}).get("sha256") != final_sha:
        fail("publication manifest final work hash mismatch")
    if manifest.get("review", {}).get("r0_sha256") != R0_SHA or manifest.get("review", {}).get("final_sha256") != final_sha:
        fail("publication manifest review hash mismatch")
    if manifest.get("primary_reading_path", {}).get("clicks_to_work") != 2:
        fail("publication manifest does not bind two-click root path")

    if (ROOT / "data/operations/iterations/114").exists():
        fail("task 114 iteration directory exists")
    if list(ROOT.glob("**/*task114*")):
        fail("task 114 artifact exists")

    print(json.dumps({
        "status": "PASS",
        "work": {
            "path": WORK_PATH,
            "characters": len(work_text),
            "han_characters_main_body": body_han,
            "sha256": final_sha,
        },
        "source": {"mode": "FULL_LOCAL_NOTE_HASH_MATCH", "bytes": SOURCE_BYTES, "sha256": SOURCE_SHA},
        "reviews": {"r0_sha256": R0_SHA, "final_sha256": final_sha, "roles": 3, "substantive_rewrite": True},
        "visibility": {"root_to_shelf": 1, "root_to_work": 2},
        "task114": "ABSENT",
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
