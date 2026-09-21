#!/usr/bin/env python3
"""Validate Task198 Step02 case/provenance/manifest byte bindings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "cases" / "case-manifest.json"
DIGEST_PATH = ROOT / "cases" / "case-manifest.sha256"

FORBIDDEN_FACTS_MARKERS = (
    "facts_only",
    "method_trace",
    "broken_method_trace",
    "evaluator",
    "expected label",
    "expected disposition",
    "candidate_ref",
    "selected_candidate_ref",
    "source-bound",
    "method history",
    "inherited method",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["task_id"] == "IGNITION-20260921-198"
    assert manifest["case_count"] == 3
    assert [case["case_id"] for case in manifest["cases"]] == [
        "REPL-CASE-01",
        "REPL-CASE-02",
        "REPL-CASE-03",
    ]
    assert len({case["source_path"] for case in manifest["cases"]}) == 3
    assert len({case["provenance_path"] for case in manifest["cases"]}) == 3

    for case in manifest["cases"]:
        source = ROOT / case["source_path"]
        provenance_path = ROOT / case["provenance_path"]
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        assert source.is_file()
        assert provenance_path.is_file()
        assert sha256(source) == case["source_sha256"]
        assert sha256(provenance_path) == case["provenance_sha256"]
        assert provenance["case_id"] == case["case_id"]
        assert provenance["source_sha256"] == case["source_sha256"]
        assert provenance["synthetic"] is True
        assert provenance["personal_data"] is False
        assert provenance["external_knowledge_required"] is False
        facts = source.read_text(encoding="utf-8").lower()
        assert not any(marker in facts for marker in FORBIDDEN_FACTS_MARKERS)
        assert "http://" not in facts and "https://" not in facts

    digest_line = DIGEST_PATH.read_text(encoding="utf-8").strip().split()
    assert digest_line[1] == "cases/case-manifest.json"
    assert digest_line[0] == sha256(MANIFEST_PATH)
    print("TASK198_STEP02_CASE_MANIFEST_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
