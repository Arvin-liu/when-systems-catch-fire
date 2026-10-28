from __future__ import annotations

import json
from pathlib import Path


def project_summary(fabric: dict) -> dict:
    return {
        "fabric_id": fabric["fabric_id"],
        "as_of_commit": fabric["as_of_commit"],
        "events": len(fabric.get("events", [])),
        "states": len(fabric.get("states", [])),
        "relations": len(fabric.get("relations", [])),
        "relation_classes": sorted({r["relation_class"] for r in fabric.get("relations", [])}),
        "scale_domains": sorted({e["scale_domain"] for e in fabric.get("events", [])} | {s["scale_domain"] for s in fabric.get("states", [])}),
        "residue_count": len(fabric.get("unmapped_residue", [])),
        "claim_ceiling": fabric["claim_ceiling"],
    }


def project_file(path: Path) -> dict:
    return project_summary(json.loads(path.read_text(encoding="utf-8")))

