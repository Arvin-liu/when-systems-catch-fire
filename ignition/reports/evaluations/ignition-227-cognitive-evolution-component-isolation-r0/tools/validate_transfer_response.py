#!/usr/bin/env python3
"""Validate one immutable Task227 Component-A successor response."""
from __future__ import annotations
import argparse, json
from pathlib import Path

FIELDS={"primary_action","additional_actions","reported_value","preserved_m0_rule","fallback","scope_statement","rationale"}
def validate(path:Path):
    try:data=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:raise ValueError(f"invalid JSON: {exc}")
    if not isinstance(data,dict) or set(data)!={"responses"}:raise ValueError("top-level response must contain exactly responses")
    rows=data["responses"]
    if not isinstance(rows,dict) or set(rows)!={"A","B","C"}:raise ValueError("responses must contain exactly A, B, C")
    for case,row in rows.items():
        if not isinstance(row,dict) or set(row)!=FIELDS:raise ValueError(f"{case} fields differ from frozen response schema")
        for key in ("primary_action","scope_statement","rationale"):
            if not isinstance(row[key],str) or not row[key].strip():raise ValueError(f"{case}.{key} must be nonempty string")
        if not isinstance(row["additional_actions"],list) or any(not isinstance(x,str) or not x.strip() for x in row["additional_actions"]):raise ValueError(f"{case}.additional_actions invalid")
        if row["reported_value"] is not None and (not isinstance(row["reported_value"],(int,float,str)) or isinstance(row["reported_value"],bool)):raise ValueError(f"{case}.reported_value invalid")
        for key in ("preserved_m0_rule","fallback"):
            if row[key] is not None and not isinstance(row[key],str):raise ValueError(f"{case}.{key} must be string or null")
    return data

def main():
    ap=argparse.ArgumentParser();ap.add_argument("response",type=Path);args=ap.parse_args()
    try:validate(args.response)
    except ValueError as exc:
        print(f"TASK227_TRANSFER_RESPONSE_INVALID={exc}")
        raise SystemExit(1)
    print("TASK227_TRANSFER_RESPONSE_VALID=PASS")

if __name__=="__main__":main()
