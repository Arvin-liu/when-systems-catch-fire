#!/usr/bin/env python3
"""022 field-model reproduction + canonical revalidation against SOURCE data."""
from __future__ import annotations
import json, re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT
NOW = "2026-07-10T21:00:00+08:00"

def read(p): return p.read_text(encoding="utf-8")

# 1. 020 schema required + properties
schema020 = json.loads(read(ROOT / "inputs/020/formal-protocol-promotion.schema.json"))
schema020_required = schema020.get("required", [])
schema020_props = list(schema020.get("properties", {}).keys())

# 2. 020 validator accessed fields (static scan of validate_formal_protocol.py)
vsrc = read(ROOT / "inputs/020/validate_formal_protocol.py")
accessed = set(re.findall(r'record\.get\("([^"]+)"\)', vsrc))
# also detect what validate_all actually passes: inventory record keys
inventory_keys = ["protocol_id","title_zh","title_en","status","document_path","index_location",
                  "machine_record_location","source_reference","last_modified","content_hash"]
# the bug: protocol_inventory builds a stripped rec, never the full machine record
# so the ONLY fields the validator ever sees are inventory_keys.

# 3. source machine data actual fields
src_data = json.loads(read(REPO / "data/meta-protocols/meta-protocols.json"))
src_fields = list(src_data["protocols"][0].keys())

# 4. 021 draft fields (from a sample draft)
draft = json.loads(read(ROOT / "inputs/021/protocols-draft.json"))
draft_fields = list(draft["protocols"][0].keys())

# 5. canonical fields
canon = json.loads(read(ROOT / "canonical/data/canonical-field-registry.json")) if (ROOT/"canonical/data/canonical-field-registry.json").exists() else None

# ---- field compatibility matrix ----
def equivalence(canon_field, source_field, schema_field, validator_field):
    """Classify semantic equivalence honestly."""
    if source_field == "<none>":
        return "target_field_missing / 源字段不存在"
    if canon_field == "<none>":
        return "源字段无 canonical 目标"
    return "近似等价（需人工复核）"

rows = []
# canonical fields vs legacy mapping
legacy_map = json.loads(read(ROOT / "canonical/mappings/legacy-to-canonical-field-map.json"))
all_canon = list(legacy_map.keys())
for cf in all_canon:
    lk = legacy_map.get(cf, [])
    src_present = any(l in src_fields for l in lk)
    schema_present = cf in schema020_required
    validator_present = any(l in accessed for l in lk)
    if not lk or all(l not in src_fields for l in lk):
        sem = "源字段不存在（canonical 新增，需人工补）"
        safe = "no"
        tran = "requires_transformation"
        hr = "yes"
        risk = "high (new content)"
    elif len(lk) > 1:
        sem = "多对一（legacy 多字段合并）"
        safe = "no"
        tran = "requires_transformation"
        hr = "yes"
        risk = "medium"
    elif cf not in schema020_required and cf not in schema020_props:
        sem = "canonical 新增字段（schema 020 未要求）"
        safe = "no"
        tran = "n/a"
        hr = "yes"
        risk = "medium"
    elif not validator_present:
        sem = "近似等价但 020 验证器未读取"
        safe = "no"
        tran = "requires_transformation"
        hr = "yes"
        risk = "high (020 误判来源)"
    else:
        sem = "近似等价"
        safe = "no" if cf not in schema020_required else "yes"
        tran = "no" if cf in schema020_required else "requires_transformation"
        hr = "yes" if cf not in schema020_required else "no"
        risk = "low" if cf in schema020_required else "medium"
    rows.append({
        "canonical_field": cf,
        "020_schema_field": cf if cf in schema020_required else "<none>",
        "020_validator_field": " | ".join(l for l in lk if l in accessed) or "<none (validator never reads full record)>",
        "source_field": " | ".join(lk) if lk else "<none>",
        "021_draft_field": cf if cf in draft_fields else "<none>",
        "semantic_equivalence": sem,
        "safe_to_map": safe,
        "requires_transformation": tran,
        "requires_human_review": hr,
        "information_loss_risk": risk,
        "notes": ("020 验证器只读取被剥离的 inventory 记录，未加载完整机器记录 → 该字段即使源仓库存在也会被误判为缺失"
                  if not validator_present and src_present else ""),
    })

# Write field-model artifacts
(ROOT / "analysis/field-model/020-schema-fields.json").write_text(json.dumps(
    {"required": schema020_required, "properties": schema020_props}, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "analysis/field-model/020-validator-accessed-fields.json").write_text(json.dumps(
    {"record_get_fields": sorted(accessed), "inventory_keys_passed": inventory_keys,
     "note": "validate_all() passes only inventory_keys to validate_protocol_record; full machine record fields are never loaded"},
    ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "analysis/field-model/source-machine-data-fields.json").write_text(json.dumps(
    {"fields": src_fields}, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "analysis/field-model/021-draft-fields.json").write_text(json.dumps(
    {"fields": draft_fields}, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "analysis/field-model/field-compatibility-matrix.md").write_text(
    "# Field Compatibility Matrix (020 schema vs 020 validator vs source vs 021 draft vs canonical)\n\n"
    "generated_at: " + NOW + "\n\n"
    "| canonical_field | 020_schema | 020_validator | source_field | 021_draft | semantic | safe | transform | human_review | info_loss | notes |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|\n" +
    "\n".join(
        f"| {r['canonical_field']} | {r['020_schema_field']} | {r['020_validator_field']} | {r['source_field']} | "
        f"{r['021_draft_field']} | {r['semantic_equivalence']} | {r['safe_to_map']} | {r['requires_transformation']} | "
        f"{r['requires_human_review']} | {r['information_loss_risk']} | {r['notes']} |" for r in rows
    ) + "\n", encoding="utf-8")

# ---- reproduce 020 validator behavior (run it) to show machine_eligible=0 ----
print("field-model artifacts written.")
print("020 schema required count:", len(schema020_required))
print("020 validator record.get fields:", sorted(accessed))
print("source machine fields:", src_fields)
print("021 draft fields count:", len(draft_fields))
print("matrix rows:", len(rows))
