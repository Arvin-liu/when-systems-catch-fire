#!/usr/bin/env python3
"""Extract which fields the 020 validator actually reads (static analysis).
Outputs JSON for the field-compatibility matrix. Read-only."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path("/Users/zhiyuan/Documents/Codex/2026-07-10/ignition-20260709-022")

def main():
    vsrc = (ROOT / "inputs/020/validate_formal_protocol.py").read_text(encoding="utf-8")
    gets = sorted(set(re.findall(r'record\.get\("([^"]+)"\)', vsrc)))
    # simulate validate_all: it builds inventory rec with only these keys
    inventory_keys = ["protocol_id", "title_zh", "title_en", "status", "document_path",
                      "index_location", "machine_record_location", "source_reference",
                      "last_modified", "content_hash"]
    out = {
        "validator_record_get_fields": gets,
        "inventory_keys_passed_to_validator": inventory_keys,
        "bug_note": "validate_all() passes only inventory_keys; the full machine record "
                    "(definition/dimension/role_in_P_meta/relation_to_Psi0/examples/boundaries/"
                    "risks/basic_meaning/source_files) is never loaded, so every record.get() "
                    "for those fields returns None and yields false FAIL/PENDING.",
        "fields_that_would_pass_if_full_record_loaded": [
            "definition (G05)", "dimension (G06/G09)", "role_in_P_meta (G08/G16)",
            "relation_to_Psi0 (G14/G15)", "examples (G07/G11)", "boundaries (G10/G22)",
            "risks (G10/G22)", "basic_meaning (G12)", "source_files (G13/G24)", "formal_expression (S05)",
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
