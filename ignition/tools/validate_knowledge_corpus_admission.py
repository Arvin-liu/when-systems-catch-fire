#!/usr/bin/env python3
"""Validate the shared Knowledge Corpus Admission Policy and its projections."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.foundation.knowledge_corpus_admission import admission_for_path, load_policy


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    policy = load_policy()
    required_classes = {
        "KNOWLEDGE_SOURCE_ELIGIBLE",
        "KNOWLEDGE_SOURCE_EXPLICIT_ONLY",
        "PLATFORM_CODE_EXCLUDED",
        "GENERATED_PROJECTION_EXCLUDED",
        "HISTORICAL_PROVENANCE_ONLY",
    }
    if set(policy.get("classes", {})) != required_classes:
        raise SystemExit("admission policy class vocabulary drift")
    assertions = {
        "runtime": admission_for_path("agent_runtime/r1_runtime.py").classification == "PLATFORM_CODE_EXCLUDED" and not admission_for_path("agent_runtime/r1_runtime.py").auto_discovery,
        "kernel": admission_for_path("agent_kernel/contracts.py").classification == "PLATFORM_CODE_EXCLUDED" and not admission_for_path("agent_kernel/contracts.py").auto_discovery,
        "tests": admission_for_path("tests/test_agent_runtime_r1.py").classification == "PLATFORM_CODE_EXCLUDED" and not admission_for_path("tests/test_agent_runtime_r1.py").auto_discovery,
        "schemas": admission_for_path("schemas/agent-runtime/r1-run-state.schema.json").classification == "PLATFORM_CODE_EXCLUDED" and not admission_for_path("schemas/agent-runtime/r1-run-state.schema.json").auto_discovery,
        "explicit_docs": admission_for_path("docs/architecture/agent-runtime-r1.md").explicit and admission_for_path("docs/architecture/agent-runtime-r1.md").auto_discovery,
        "historical": admission_for_path("reports/operations/old-audit.md").classification == "HISTORICAL_PROVENANCE_ONLY" and admission_for_path("reports/operations/old-audit.md").provenance_only,
    }
    if not all(assertions.values()):
        raise SystemExit("admission policy path assertions failed: " + json.dumps(assertions, sort_keys=True))
    for path in (
        ROOT / "data/foundation/function-assets/census.jsonl",
        ROOT / "data/foundation/function-assets/identity-cards.jsonl",
        ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl",
    ):
        for row in rows(path):
            sources = row.get("source_evidence", {}).get("occurrence_paths", []) or [item.get("path", "") for item in row.get("source_anchors", [])]
            if sources and all(admission_for_path(source).classification == "PLATFORM_CODE_EXCLUDED" for source in sources):
                raise SystemExit(f"platform-only row remains in current projection: {path.name}:{row.get('stable_id') or row.get('canonical_id')}")
    print(json.dumps({"status": "PASS", "policy_id": policy["policy_id"], "classes": sorted(required_classes)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
