#!/usr/bin/env python3
"""Migrate a legacy protocol record (ignition source OR 021 draft) to canonical.
Read-only transformation; writes a migrated copy to outputs, never touches source."""
from __future__ import annotations
import json, sys, datetime, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from canonical_registry import load_legacy_map

NOW = "2026-07-10T21:10:00+08:00"

def migrate(raw: dict, source_label: str) -> dict:
    legacy_map = load_legacy_map()
    out: dict[str, object] = {}
    notes = []
    for cf, lks in legacy_map.items():
        val = None
        for lk in lks:
            cur = raw
            ok = True
            for part in lk.split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    ok = False
                    break
            if ok and cur not in (None, "", [], {}):
                val = cur
                if cf not in raw:
                    notes.append(f"{cf}: from legacy {lk}")
                break
        out[cf] = val
    out["version_metadata"] = {
        "schema": "protocol-canonical.schema.json",
        "migrated_at": NOW,
        "source_label": source_label,
        "migration_notes": notes,
    }
    out["provenance"] = {
        "generated_by": "migrate_legacy_protocol_record",
        "generated_at": NOW,
        "source_record_keys": sorted(raw.keys()),
        "mapping_notes": notes,
        "is_draft_derived": raw.get("draft_status") == "candidate_draft",
    }
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--source-label", default="legacy")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    raw = json.loads(Path(a.input).read_text(encoding="utf-8"))
    recs = raw["protocols"] if isinstance(raw, dict) and "protocols" in raw else raw
    migrated = [migrate(r, a.source_label) for r in recs]
    Path(a.output).write_text(json.dumps(migrated if isinstance(raw, list) else {"protocols": migrated},
                                         ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"migrated {len(migrated)} records -> {a.output}")

if __name__ == "__main__":
    raise SystemExit(main())
